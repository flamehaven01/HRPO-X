"""HRPO-X Core Package - Golden Artifact (Hash Locked)"""
__version__ = "1.0.0"
__author__ = "CLI C01"
__paper__ = "NeurIPS 2025"

from .projection import hrpo_projection
from .gating import hrpo_gating
from .objective import hrpo_objective

__all__ = [
    'hrpo_projection',
    'hrpo_gating',
    'hrpo_objective',
]
