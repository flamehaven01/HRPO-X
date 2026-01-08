"""
HRPO-X Extensions Package - Validation Utilities
=================================================

This package contains validation utilities for production patches.
These are OPTIONAL helpers for development and debugging.

For actual extension implementations, see: hrpo_core_v2_2.py
"""

__version__ = "1.0.1"

# Note: Extension implementations (IS, adaptive_rmin, ghost_mode, hash_manager)
# are in hrpo_core_v2_2.py, not in separate files.
# This package only contains validation utilities.

from .validators import PatchValidator

__all__ = [
    'PatchValidator',
]
