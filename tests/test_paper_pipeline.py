import math

import torch

from hrpox.paper_pipeline import MiniHRPOTrainer, MiniPipelineConfig, run_mini_pipeline


def test_mini_pipeline_metrics_keys():
    metrics = run_mini_pipeline(steps=2)
    required = {
        "loss",
        "pg_loss",
        "kl",
        "reward_mean",
        "reward_std",
        "beta",
    }
    assert required.issubset(metrics.keys())
    for key in required:
        assert isinstance(metrics[key], float)
        assert math.isfinite(metrics[key])


def test_rollout_group_shapes():
    torch.manual_seed(0)
    cfg = MiniPipelineConfig(seq_len=6, group_size=3)
    trainer = MiniHRPOTrainer(cfg)
    batch = trainer.rollout_group()

    assert batch["logp"].shape == (cfg.group_size, cfg.seq_len)
    assert batch["ref_logp"].shape == (cfg.group_size, cfg.seq_len)
    assert batch["rewards"].shape == (cfg.group_size,)
    assert batch["token_mask"].shape == (cfg.group_size, cfg.seq_len)
    assert batch["token_mask"].dtype == torch.bool
