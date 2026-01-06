"""
HRPO-X: Hybrid Reasoning with Policy Optimization
Production-ready implementation of latent reasoning via RL
"""

from hrpox.__main__ import (
    HRPOConfig,
    adaptive_epsilon_schedule,
    importance_weighted_hrpo_loss,
    TaskAwareAdaptiveRminController,
    DistributionalGhostMode,
    PolicyHashManager,
)

__version__ = "1.0.1"
__all__ = [
    "HRPOConfig",
    "adaptive_epsilon_schedule",
    "importance_weighted_hrpo_loss",
    "TaskAwareAdaptiveRminController",
    "DistributionalGhostMode",
    "PolicyHashManager",
]
