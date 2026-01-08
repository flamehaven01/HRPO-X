import torch

from hrpo_paper_core import (
    PaperHRPOConfig,
    project_hidden_to_embedding,
    hybrid_gating_step,
    hrpo_loss,
)


def test_projection_shape_and_norm():
    torch.manual_seed(0)
    batch = 2
    vocab = 5
    dim = 3
    logits = torch.randn(batch, vocab)
    embedding = torch.randn(vocab, dim)

    h_next, p_next = project_hidden_to_embedding(logits, embedding, tau=1.0)

    assert p_next.shape == (batch, vocab)
    assert h_next.shape == (batch, dim)
    # Softmax should sum to 1
    assert torch.allclose(p_next.sum(dim=-1), torch.ones(batch), atol=1e-6)


def test_gating_respects_think_mask():
    torch.manual_seed(0)
    batch = 2
    dim = 4
    e_hat = torch.randn(batch, dim)
    h_proj = torch.randn(batch, dim)
    w_a = torch.randn(dim, dim)
    b_a = torch.randn(dim)
    w_x = torch.randn(dim, dim)
    b_x = torch.randn(dim)
    lambda_vec = torch.randn(dim)

    think_mask = torch.tensor([False, False])
    e_next, _ = hybrid_gating_step(
        e_hat, h_proj, w_a, b_a, w_x, b_x, lambda_vec, c=8.0, think_mask=think_mask
    )

    assert torch.allclose(e_next, e_hat, atol=1e-6)


def test_hrpo_loss_no_ratio_standardized_rewards():
    # g=3 rollouts, T=2 tokens
    logp = torch.tensor([[0.0, -0.1], [0.2, -0.2], [-0.3, 0.1]])
    ref_logp = torch.zeros_like(logp)
    rewards = torch.tensor([0.0, 1.0, 2.0])

    loss, metrics = hrpo_loss(logp, rewards, ref_logp, beta=0.1, eps=1e-8)

    assert "kl" in metrics
    # KL term should be mean(logp - ref_logp)
    expected_kl = (logp - ref_logp).mean().item()
    assert abs(metrics["kl"] - expected_kl) < 1e-6
    # Loss should be finite
    assert torch.isfinite(loss)


def test_paper_config_defaults():
    cfg = PaperHRPOConfig()
    assert cfg.tau > 0
    assert cfg.c > 0
    assert cfg.beta >= 0
