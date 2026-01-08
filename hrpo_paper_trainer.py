"""
HRPO-X Paper Trainer (Clean-room)
=================================
Full pipeline scaffold: rollout buffer, reward evaluation, and training loop.
This is a demo-scale implementation intended for paper alignment verification.
"""
from __future__ import annotations

import dataclasses
import typing

import torch
import torch.nn as nn
import torch.nn.functional as F

import hrpo_paper_core


@dataclasses.dataclass
class PromptSample:
    """
    One training sample containing a prompt and optional target answer tokens.
    """

    prompt_tokens: torch.Tensor
    answer_tokens: typing.Optional[torch.Tensor] = None
    metadata: typing.Optional[typing.Dict[str, str]] = None


class PromptDataset:
    """
    Minimal dataset interface for prompt samples.
    """

    def __iter__(self) -> typing.Iterable[PromptSample]:
        raise NotImplementedError


class ListPromptDataset(PromptDataset):
    """
    In-memory dataset for explicit prompt/answer pairs.
    """

    def __init__(self, samples: typing.Sequence[PromptSample]):
        self.samples = list(samples)

    def __iter__(self) -> typing.Iterable[PromptSample]:
        yield from self.samples


class ToyPromptDataset(PromptDataset):
    """
    Generates random prompts with a fixed answer token id.
    """

    def __init__(self, vocab_size: int, prompt_len: int, answer_len: int, count: int, target_token_id: int = 1):
        self.vocab_size = vocab_size
        self.prompt_len = prompt_len
        self.answer_len = answer_len
        self.count = count
        self.target_token_id = target_token_id

    def __iter__(self) -> typing.Iterable[PromptSample]:
        for _ in range(self.count):
            prompt = torch.randint(0, self.vocab_size, (self.prompt_len,))
            answer = torch.full((self.answer_len,), self.target_token_id, dtype=torch.long)
            yield PromptSample(prompt_tokens=prompt, answer_tokens=answer)


class RewardEvaluator:
    """
    Reward interface for HRPO rollouts.
    """

    def compute(self, tokens: torch.Tensor, sample: PromptSample, answer_span: int) -> torch.Tensor:
        raise NotImplementedError


class ExactMatchRewardEvaluator(RewardEvaluator):
    """
    Returns 1.0 if the generated answer span exactly matches the target tokens.
    """

    def compute(self, tokens: torch.Tensor, sample: PromptSample, answer_span: int) -> torch.Tensor:
        if sample.answer_tokens is None:
            return torch.zeros(tokens.size(0))
        span = min(answer_span, tokens.size(1), sample.answer_tokens.numel())
        generated = tokens[:, -span:]
        target = sample.answer_tokens[-span:].unsqueeze(0).expand_as(generated)
        match = (generated == target).all(dim=-1)
        return match.to(torch.float32)


class TargetTokenRewardEvaluator(RewardEvaluator):
    """
    Returns 1.0 if the target token appears in the answer span.
    """

    def __init__(self, target_token_id: int):
        self.target_token_id = target_token_id

    def compute(self, tokens: torch.Tensor, sample: PromptSample, answer_span: int) -> torch.Tensor:
        span = min(answer_span, tokens.size(1))
        answer_tokens = tokens[:, -span:]
        hit = (answer_tokens == self.target_token_id).any(dim=-1)
        return hit.to(torch.float32)


class CallableRewardEvaluator(RewardEvaluator):
    """
    Wraps a custom reward function.
    """

    def __init__(
        self, reward_fn: typing.Callable[[torch.Tensor, PromptSample, int], torch.Tensor]
    ):
        self.reward_fn = reward_fn

    def compute(self, tokens: torch.Tensor, sample: PromptSample, answer_span: int) -> torch.Tensor:
        return self.reward_fn(tokens, sample, answer_span)


@dataclasses.dataclass
class PaperTrainerConfig:
    vocab_size: int = 32
    embed_dim: int = 16
    prompt_len: int = 4
    seq_len: int = 8
    group_size: int = 4
    think_span: int = 5
    answer_span: int = 3
    temperature: float = 1.0
    lr: float = 1e-3


class ToyPolicy(nn.Module):
    """
    Minimal policy that maps embeddings to logits.
    """

    def __init__(self, vocab_size: int, embed_dim: int):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.head = nn.Linear(embed_dim, vocab_size, bias=False)

    def embed(self, token_ids: torch.Tensor) -> torch.Tensor:
        return self.embedding(token_ids)

    def logits_from_embedding(self, emb: torch.Tensor) -> torch.Tensor:
        return self.head(emb)


class PolicyAdapter:
    """
    Adapter for policies with embedding + head modules.
    """

    def __init__(self, policy: nn.Module, embedding_attr: str = "embedding", head_attr: str = "head"):
        self.policy = policy
        self.embedding = getattr(policy, embedding_attr)
        self.head = getattr(policy, head_attr)

    def embed(self, token_ids: torch.Tensor) -> torch.Tensor:
        return self.embedding(token_ids)

    def logits_from_embedding(self, emb: torch.Tensor) -> torch.Tensor:
        return self.head(emb)

    def parameters(self):
        return self.policy.parameters()


class PaperGatingModule(nn.Module):
    """
    Learnable gates for the hybrid gating step (Eq(4)).
    """

    def __init__(self, embed_dim: int):
        super().__init__()
        self.w_a = nn.Parameter(torch.randn(embed_dim, embed_dim) * 0.02)
        self.b_a = nn.Parameter(torch.zeros(embed_dim))
        self.w_x = nn.Parameter(torch.randn(embed_dim, embed_dim) * 0.02)
        self.b_x = nn.Parameter(torch.zeros(embed_dim))
        self.lambda_vec = nn.Parameter(torch.zeros(embed_dim))

    def forward(
        self,
        e_hat: torch.Tensor,
        h_proj: torch.Tensor,
        c: float,
        think_mask: typing.Optional[torch.Tensor],
    ) -> typing.Tuple[torch.Tensor, typing.Dict[str, torch.Tensor]]:
        return hrpo_paper_core.hybrid_gating_step(
            e_hat,
            h_proj,
            self.w_a,
            self.b_a,
            self.w_x,
            self.b_x,
            self.lambda_vec,
            c=c,
            think_mask=think_mask,
        )


@dataclasses.dataclass
class RolloutBatch:
    tokens: torch.Tensor
    logp: torch.Tensor
    ref_logp: torch.Tensor
    rewards: torch.Tensor
    token_mask: torch.Tensor


class RolloutBuffer:
    """
    Simple on-policy rollout buffer.
    """

    def __init__(self):
        self._batches: typing.List[RolloutBatch] = []

    def add(self, batch: RolloutBatch) -> None:
        self._batches.append(batch)

    def clear(self) -> None:
        self._batches.clear()

    def is_empty(self) -> bool:
        return len(self._batches) == 0

    def as_batch(self) -> RolloutBatch:
        if not self._batches:
            raise RuntimeError("RolloutBuffer is empty.")
        tokens = torch.cat([b.tokens for b in self._batches], dim=0)
        logp = torch.cat([b.logp for b in self._batches], dim=0)
        ref_logp = torch.cat([b.ref_logp for b in self._batches], dim=0)
        rewards = torch.cat([b.rewards for b in self._batches], dim=0)
        token_mask = torch.cat([b.token_mask for b in self._batches], dim=0)
        return RolloutBatch(tokens=tokens, logp=logp, ref_logp=ref_logp, rewards=rewards, token_mask=token_mask)

    def iter_batches(self) -> typing.Iterable[RolloutBatch]:
        return iter(self._batches)


class PaperHRPOTrainer:
    """
    Full trainer scaffold: rollouts, reward evaluation, and HRPO updates.
    """

    def __init__(
        self,
        cfg: PaperTrainerConfig,
        dataset: PromptDataset,
        reward_evaluator: RewardEvaluator,
        paper_cfg: typing.Optional[hrpo_paper_core.PaperHRPOConfig] = None,
        policy: typing.Optional[nn.Module] = None,
        ref_policy: typing.Optional[nn.Module] = None,
    ):
        self.cfg = cfg
        self.paper_cfg = paper_cfg or hrpo_paper_core.PaperHRPOConfig()
        self.dataset = dataset
        self.reward_evaluator = reward_evaluator
        self.policy = PolicyAdapter(policy or ToyPolicy(cfg.vocab_size, cfg.embed_dim))
        self.gates = PaperGatingModule(cfg.embed_dim)
        ref = ref_policy or ToyPolicy(cfg.vocab_size, cfg.embed_dim)
        ref.load_state_dict(self.policy.policy.state_dict())
        self.ref_policy = PolicyAdapter(ref)
        for p in self.ref_policy.parameters():
            p.requires_grad = False
        self.optim = torch.optim.Adam(list(self.policy.parameters()) + list(self.gates.parameters()), lr=cfg.lr)
        self.buffer = RolloutBuffer()

    def _prompt_embedding(self, prompt_tokens: torch.Tensor, policy: PolicyAdapter) -> torch.Tensor:
        emb = policy.embed(prompt_tokens)
        return emb.mean(dim=0)

    def _think_mask(self, t: int) -> torch.Tensor:
        return torch.tensor([t < self.cfg.think_span], dtype=torch.bool)

    def _answer_mask(self) -> torch.Tensor:
        mask = torch.zeros(self.cfg.seq_len, dtype=torch.bool)
        span = min(self.cfg.answer_span, self.cfg.seq_len)
        mask[-span:] = True
        return mask.unsqueeze(0).expand(self.cfg.group_size, -1)

    def _rollout_group(self, sample: PromptSample) -> RolloutBatch:
        g = self.cfg.group_size
        T = self.cfg.seq_len

        logp = torch.zeros(g, T)
        ref_logp = torch.zeros(g, T)
        tokens = torch.zeros(g, T, dtype=torch.long)

        prompt = sample.prompt_tokens
        e_prompt = self._prompt_embedding(prompt, self.policy)
        e_prompt_ref = self._prompt_embedding(prompt, self.ref_policy)

        for i in range(g):
            e_in = e_prompt.clone()
            e_in_ref = e_prompt_ref.clone()
            for t in range(T):
                logits = self.policy.logits_from_embedding(e_in)
                probs = F.softmax(logits / self.cfg.temperature, dim=-1)
                token_id = torch.multinomial(probs, num_samples=1).squeeze(0)
                tokens[i, t] = token_id
                logp[i, t] = F.log_softmax(logits, dim=-1)[token_id]

                ref_logits = self.ref_policy.logits_from_embedding(e_in_ref)
                ref_logp[i, t] = F.log_softmax(ref_logits, dim=-1)[token_id]

                e_hat = self.policy.embed(token_id)
                h_proj, _ = hrpo_paper_core.project_hidden_to_embedding(
                    logits.unsqueeze(0),
                    self.policy.embedding.weight,
                    tau=self.paper_cfg.tau,
                    eps=self.paper_cfg.eps,
                )
                h_proj = h_proj.squeeze(0)
                think_mask = self._think_mask(t)
                e_next, _ = self.gates(e_hat, h_proj, c=self.paper_cfg.c, think_mask=think_mask)
                e_in = e_next.squeeze(0)
                e_in_ref = self.ref_policy.embed(token_id)

        rewards = self.reward_evaluator.compute(tokens, sample, self.cfg.answer_span)
        token_mask = self._answer_mask()
        return RolloutBatch(tokens=tokens, logp=logp, ref_logp=ref_logp, rewards=rewards, token_mask=token_mask)

    def collect_rollouts(self) -> None:
        self.buffer.clear()
        for sample in self.dataset:
            batch = self._rollout_group(sample)
            self.buffer.add(batch)

    def train_step(self) -> typing.Dict[str, float]:
        if self.buffer.is_empty():
            self.collect_rollouts()
        losses: typing.List[torch.Tensor] = []
        metric_sums: typing.Dict[str, float] = {}
        batch_count = 0
        for batch in self.buffer.iter_batches():
            loss, metrics = hrpo_paper_core.hrpo_loss(
                batch.logp,
                batch.rewards,
                batch.ref_logp,
                beta=self.paper_cfg.beta,
                eps=self.paper_cfg.eps,
                token_mask=batch.token_mask,
            )
            losses.append(loss)
            for key, value in metrics.items():
                metric_sums[key] = metric_sums.get(key, 0.0) + float(value)
            batch_count += 1
        loss = torch.stack(losses).mean()
        self.optim.zero_grad()
        loss.backward()
        self.optim.step()
        metrics_avg = {key: value / max(batch_count, 1) for key, value in metric_sums.items()}
        metrics_avg["loss"] = float(loss.item())
        return metrics_avg


def run_full_trainer_demo(steps: int = 3) -> typing.Dict[str, float]:
    torch.manual_seed(0)
    cfg = PaperTrainerConfig()
    dataset = ToyPromptDataset(cfg.vocab_size, cfg.prompt_len, cfg.answer_span, count=2)
    reward = ExactMatchRewardEvaluator()
    trainer = PaperHRPOTrainer(cfg, dataset, reward)
    metrics: typing.Dict[str, float] = {}
    for _ in range(steps):
        metrics = trainer.train_step()
    return metrics
