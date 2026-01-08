import math

import torch

from hrpox.paper_trainer import (
    ExactMatchRewardEvaluator,
    PaperHRPOTrainer,
    PaperTrainerConfig,
    RolloutBatch,
    RolloutBuffer,
    ToyPromptDataset,
)


def test_rollout_buffer_concat():
    batch_1 = RolloutBatch(
        tokens=torch.zeros(1, 2, dtype=torch.long),
        logp=torch.zeros(1, 2),
        ref_logp=torch.zeros(1, 2),
        rewards=torch.zeros(1),
        token_mask=torch.ones(1, 2, dtype=torch.bool),
    )
    batch_2 = RolloutBatch(
        tokens=torch.ones(1, 2, dtype=torch.long),
        logp=torch.ones(1, 2),
        ref_logp=torch.ones(1, 2),
        rewards=torch.ones(1),
        token_mask=torch.ones(1, 2, dtype=torch.bool),
    )
    buffer = RolloutBuffer()
    buffer.add(batch_1)
    buffer.add(batch_2)
    merged = buffer.as_batch()

    assert merged.tokens.shape == (2, 2)
    assert merged.logp.shape == (2, 2)
    assert merged.ref_logp.shape == (2, 2)
    assert merged.rewards.shape == (2,)
    assert merged.token_mask.shape == (2, 2)


def test_trainer_train_step_metrics():
    torch.manual_seed(0)
    cfg = PaperTrainerConfig(seq_len=4, group_size=2, prompt_len=3, answer_span=2)
    dataset = ToyPromptDataset(cfg.vocab_size, cfg.prompt_len, cfg.answer_span, count=1)
    reward = ExactMatchRewardEvaluator()
    trainer = PaperHRPOTrainer(cfg, dataset, reward)
    metrics = trainer.train_step()

    required = {"loss", "pg_loss", "kl", "reward_mean", "reward_std", "beta"}
    assert required.issubset(metrics.keys())
    for key in required:
        assert isinstance(metrics[key], float)
        assert math.isfinite(metrics[key])
