"""
    HRPO-X: Hybrid Reasoning Research Prototype
    Single-file prototype exposing core utilities from hrpo_core_v2_2.py.
    """



# Import from root-level core module
import sys
from pathlib import Path

# Add parent directory to path to import hrpo_core_v2_2
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from hrpo_core_v2_2 import (
    HRPOConfig,
    adaptive_epsilon_schedule,
    importance_weighted_hrpo_loss,
    TaskAwareAdaptiveRminController,
    DistributionalGhostMode,
    PolicyHashManager,
)
from hrpo_paper_core import (
    PaperHRPOConfig,
    project_hidden_to_embedding,
    hybrid_gating_step,
    standardize_rewards,
    hrpo_loss,
)
from hrpo_paper_trainer import (
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

__version__ = "1.0.1"
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
