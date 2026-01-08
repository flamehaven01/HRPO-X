"""
    HRPO-X: Hybrid Reasoning Research Prototype
    Package exports for prototype utilities and paper-aligned scaffolds.
    """
from .core_v2_2 import (
    HRPOConfig,
    adaptive_epsilon_schedule,
    importance_weighted_hrpo_loss,
    TaskAwareAdaptiveRminController,
    DistributionalGhostMode,
    PolicyHashManager,
)
from .paper_core import (
    PaperHRPOConfig,
    project_hidden_to_embedding,
    hybrid_gating_step,
    standardize_rewards,
    hrpo_loss,
)
from .paper_trainer import (
    PaperTrainerConfig,
    PromptSample,
    PromptDataset,
    ListPromptDataset,
    ToyPromptDataset,
    RewardEvaluator,
    ExactMatchRewardEvaluator,
    TargetTokenRewardEvaluator,
    CallableRewardEvaluator,
    RolloutBatch,
    RolloutBuffer,
    PaperHRPOTrainer,
    run_full_trainer_demo,
)

__version__ = "1.1.0"
__all__ = [
    "HRPOConfig",
    "adaptive_epsilon_schedule",
    "importance_weighted_hrpo_loss",
    "TaskAwareAdaptiveRminController",
    "DistributionalGhostMode",
    "PolicyHashManager",
    "PaperHRPOConfig",
    "project_hidden_to_embedding",
    "hybrid_gating_step",
    "standardize_rewards",
    "hrpo_loss",
    "PaperTrainerConfig",
    "PromptSample",
    "PromptDataset",
    "ListPromptDataset",
    "ToyPromptDataset",
    "RewardEvaluator",
    "ExactMatchRewardEvaluator",
    "TargetTokenRewardEvaluator",
    "CallableRewardEvaluator",
    "RolloutBatch",
    "RolloutBuffer",
    "PaperHRPOTrainer",
    "run_full_trainer_demo",
]
