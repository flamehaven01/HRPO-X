"""
HRPO-X: Hybrid Reasoning with Policy Optimization
Production-ready implementation of latent reasoning via RL
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

__version__ = "1.0.1"
__all__ = [
    "HRPOConfig",
    "adaptive_epsilon_schedule",
    "importance_weighted_hrpo_loss",
    "TaskAwareAdaptiveRminController",
    "DistributionalGhostMode",
    "PolicyHashManager",
]
