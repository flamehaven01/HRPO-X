"""HRPO-X Extensions Package - Production Enhancements"""
__version__ = "1.0.0"

from .importance_sampling import importance_weighted_hrpo_loss, adaptive_epsilon_schedule
from .adaptive_rmin import TaskAwareAdaptiveRminController
from .ghost_mode import DistributionalGhostMode
from .hash_manager import PolicyHashManager

__all__ = [
    'importance_weighted_hrpo_loss',
    'adaptive_epsilon_schedule',
    'TaskAwareAdaptiveRminController',
    'DistributionalGhostMode',
    'PolicyHashManager',
]
