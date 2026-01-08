"""
HRPO-X Core Package - Validation Utilities
===========================================

This package contains validation utilities for numerical stability
and theoretical compliance checking. These are OPTIONAL helpers,
not core algorithm implementations.

For actual algorithm implementation, see: hrpox/core_v2_2.py
"""

__version__ = "1.1.0"
__author__ = "CLI C01"

# Note: Core algorithm (projection, gating, objective) is implemented
# in hrpox/core_v2_2.py, not in separate files.
# This package only contains validation utilities.

from .integrity import CoreIntegrityChecker
from .validators import EquationValidator

__all__ = [
    'CoreIntegrityChecker',
    'EquationValidator',
]
