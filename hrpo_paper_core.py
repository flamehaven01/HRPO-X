"""
HRPO-X Paper Alignment Core (Clean-room)
=======================================
Implements paper-aligned primitives based on hlr.txt notes.
No external code is copied or reused.
"""

from __future__ import annotations

import dataclasses
import typing

import torch
import torch.nn.functional as F


@dataclasses.dataclass
class PaperHRPOConfig:
    """Configuration for paper-aligned HRPO primitives."""

    tau: float = 1.0
    c: float = 8.0
    beta: float = 0.005
    eps: float = 1e-8


def project_hidden_to_embedding(
    logits: torch.Tensor,
    embedding_matrix: torch.Tensor,
    tau: float = 1.0,
    eps: float = 1e-8,
) -> typing.Tuple[torch.Tensor, torch.Tensor]:
    """
    Eq(3) projection: map logits to embedding space via normalized softmax.

    Args:
        logits: Head(h_hat_t), shape (..., vocab)
        embedding_matrix: W_e, shape (vocab, dim)
        tau: temperature
        eps: numerical stability for norm

    Returns:
        h_next: projected embedding, shape (..., dim)
        p_next: softmax distribution, shape (..., vocab)
    """
    p_next = F.softmax(logits / tau, dim=-1)
    p_norm = p_next / (p_next.norm(dim=-1, keepdim=True) + eps)
    h_next = p_norm @ embedding_matrix
    return h_next, p_next


def hybrid_gating_step(
    e_hat: torch.Tensor,
    h_proj: torch.Tensor,
    w_a: torch.Tensor,
    b_a: torch.Tensor,
    w_x: torch.Tensor,
    b_x: torch.Tensor,
    lambda_vec: torch.Tensor,
    c: float = 8.0,
    think_mask: typing.Optional[torch.Tensor] = None,
) -> typing.Tuple[torch.Tensor, typing.Dict[str, torch.Tensor]]:
    """
    Eq(4) hybrid gating step.

    Args:
        e_hat: sampled token embeddings, shape (..., dim)
        h_proj: projected hidden embeddings, shape (..., dim)
        w_a, b_a: gating weights for r_t
        w_x, b_x: gating weights for i_t
        lambda_vec: learnable vector Lambda, shape (dim,) or broadcastable
        c: scaling constant
        think_mask: optional boolean mask, shape (...) matching e_hat without last dim

    Returns:
        e_next: hybrid input embedding, shape (..., dim)
        gates: dict with r_t, i_t, a_t
    """
    r_t = torch.sigmoid(F.linear(e_hat, w_a, b_a))
    i_t = torch.sigmoid(F.linear(e_hat, w_x, b_x))
    a_t = torch.exp(-c * F.softplus(lambda_vec) * r_t)

    e_next = a_t * e_hat + (1.0 - a_t.pow(2)) * (i_t * h_proj)

    if think_mask is not None:
        mask = think_mask.unsqueeze(-1).to(e_next.dtype)
        e_next = mask * e_next + (1.0 - mask) * e_hat

    return e_next, {"r_t": r_t, "i_t": i_t, "a_t": a_t}


def standardize_rewards(rewards: torch.Tensor, eps: float = 1e-8) -> torch.Tensor:
    """
    Standardize rewards within a group.
    """
    mean = rewards.mean()
    std = rewards.std(unbiased=False)
    std = torch.clamp(std, min=eps)
    return (rewards - mean) / std


def hrpo_loss(
    logp: torch.Tensor,
    rewards: torch.Tensor,
    ref_logp: torch.Tensor,
    beta: float = 0.005,
    eps: float = 1e-8,
    token_mask: typing.Optional[torch.Tensor] = None,
) -> typing.Tuple[torch.Tensor, typing.Dict[str, float]]:
    """
    Eq(6) HRPO loss (on-policy, no ratio/IS).

    Args:
        logp: log probabilities from policy, shape (g, T)
        rewards: outcome rewards, shape (g,)
        ref_logp: reference log probabilities, shape (g, T)
        beta: KL coefficient
        eps: numerical stability
        token_mask: optional mask for valid tokens, shape (g, T)

    Returns:
        loss: scalar tensor
        metrics: dict of floats
    """
    advantages = standardize_rewards(rewards, eps=eps).unsqueeze(-1)
    advantages = advantages.expand_as(logp)

    if token_mask is not None:
        mask = token_mask.to(logp.dtype)
        denom = mask.sum().clamp_min(1.0)
        pg_term = (logp * advantages * mask).sum() / denom
        kl_term = ((logp - ref_logp) * mask).sum() / denom
    else:
        pg_term = (logp * advantages).mean()
        kl_term = (logp - ref_logp).mean()

    loss = -pg_term + beta * kl_term
    metrics = {
        "loss": float(loss.item()),
        "pg_loss": float((-pg_term).item()),
        "kl": float(kl_term.item()),
        "reward_mean": float(rewards.mean().item()),
        "reward_std": float(rewards.std(unbiased=False).item()),
        "beta": float(beta),
    }
    return loss, metrics
