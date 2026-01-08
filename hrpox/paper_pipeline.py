"""
HRPO-X Paper Mini Pipeline (Clean-room)
=======================================
Minimal rollout + think span + reward standardization pipeline.
This is a demo-scale implementation for paper-alignment verification only.
"""

from __future__ import annotations

import dataclasses
import typing

import torch
import torch.nn as nn
import torch.nn.functional as F

from . import paper_core


@dataclasses.dataclass
class MiniPipelineConfig:
    vocab_size: int = 32
    embed_dim: int = 16
    seq_len: int = 8
    group_size: int = 4
    think_span: int = 5
    answer_span: int = 3
    temperature: float = 1.0
    target_token_id: int = 1


class ToyPolicy(nn.Module):
    """
    Minimal policy that maps an input embedding to logits.
    """

    def __init__(self, vocab_size: int, embed_dim: int):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.head = nn.Linear(embed_dim, vocab_size, bias=False)

    def embed(self, token_ids: torch.Tensor) -> torch.Tensor:
        return self.embedding(token_ids)

    def logits_from_embedding(self, emb: torch.Tensor) -> torch.Tensor:
        return self.head(emb)


class GatingModule(nn.Module):
    """
    Learnable gates for Eq(4).
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
        think_mask: typing.Optional[torch.Tensor] = None,
    ) -> typing.Tuple[torch.Tensor, typing.Dict[str, torch.Tensor]]:
        return paper_core.hybrid_gating_step(
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


class MiniHRPOTrainer:
    """
    Clean-room mini pipeline to demonstrate:
    - hybrid rollouts (tokens + projected hidden)
    - think span gating
    - group reward standardization + HRPO loss
    """

    def __init__(
        self,
        cfg: MiniPipelineConfig,
        paper_cfg: typing.Optional[paper_core.PaperHRPOConfig] = None,
    ):
        self.cfg = cfg
        self.paper_cfg = paper_cfg or paper_core.PaperHRPOConfig()
        self.policy = ToyPolicy(cfg.vocab_size, cfg.embed_dim)
        self.gates = GatingModule(cfg.embed_dim)
        self.ref_policy = ToyPolicy(cfg.vocab_size, cfg.embed_dim)
        self.ref_policy.load_state_dict(self.policy.state_dict())
        for p in self.ref_policy.parameters():
            p.requires_grad = False
        self.optim = torch.optim.Adam(list(self.policy.parameters()) + list(self.gates.parameters()), lr=1e-3)

    def _think_mask(self) -> torch.Tensor:
        mask = torch.zeros(self.cfg.seq_len, dtype=torch.bool)
        span = min(self.cfg.think_span, self.cfg.seq_len)
        mask[:span] = True
        return mask

    def rollout_group(self) -> typing.Dict[str, torch.Tensor]:
        g = self.cfg.group_size
        T = self.cfg.seq_len
        think_mask = self._think_mask()

        logp = torch.zeros(g, T)
        ref_logp = torch.zeros(g, T)
        tokens = torch.zeros(g, T, dtype=torch.long)

        for i in range(g):
            start_id = torch.tensor(0)
            e_in = self.policy.embed(start_id)
            e_in_ref = self.ref_policy.embed(start_id)

            for t in range(T):
                logits = self.policy.logits_from_embedding(e_in)
                probs = F.softmax(logits / self.cfg.temperature, dim=-1)
                token_id = torch.multinomial(probs, num_samples=1).squeeze(0)
                tokens[i, t] = token_id

                logp[i, t] = F.log_softmax(logits, dim=-1)[token_id]

                ref_logits = self.ref_policy.logits_from_embedding(e_in_ref)
                ref_logp[i, t] = F.log_softmax(ref_logits, dim=-1)[token_id]

                e_hat = self.policy.embed(token_id)
                h_proj, _ = paper_core.project_hidden_to_embedding(
                    logits.unsqueeze(0),
                    self.policy.embedding.weight,
                    tau=self.paper_cfg.tau,
                    eps=self.paper_cfg.eps,
                )
                h_proj = h_proj.squeeze(0)

                e_next, _ = self.gates(
                    e_hat,
                    h_proj,
                    c=self.paper_cfg.c,
                    think_mask=think_mask[t].unsqueeze(0),
                )
                e_in = e_next.squeeze(0)
                e_in_ref = self.ref_policy.embed(token_id)

        rewards = self._compute_rewards(tokens)
        token_mask = self._answer_mask()

        return {"logp": logp, "ref_logp": ref_logp, "rewards": rewards, "token_mask": token_mask}

    def _compute_rewards(self, tokens: torch.Tensor) -> torch.Tensor:
        T = self.cfg.seq_len
        span = min(self.cfg.answer_span, T)
        answer_tokens = tokens[:, -span:]
        hit = (answer_tokens == self.cfg.target_token_id).any(dim=-1)
        return hit.to(torch.float32)

    def _answer_mask(self) -> torch.Tensor:
        mask = torch.zeros(self.cfg.seq_len, dtype=torch.bool)
        span = min(self.cfg.answer_span, self.cfg.seq_len)
        mask[-span:] = True
        return mask.unsqueeze(0).expand(self.cfg.group_size, -1)

    def train_step(self) -> typing.Dict[str, float]:
        batch = self.rollout_group()
        loss, metrics = paper_core.hrpo_loss(
            batch["logp"],
            batch["rewards"],
            batch["ref_logp"],
            beta=self.paper_cfg.beta,
            eps=self.paper_cfg.eps,
            token_mask=batch["token_mask"],
        )
        self.optim.zero_grad()
        loss.backward()
        self.optim.step()
        return metrics


def run_mini_pipeline(steps: int = 3) -> typing.Dict[str, float]:
    torch.manual_seed(0)
    trainer = MiniHRPOTrainer(MiniPipelineConfig())
    metrics = {}
    for _ in range(steps):
        metrics = trainer.train_step()
    return metrics
