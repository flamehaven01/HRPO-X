"""
HRPO-X CLI Entry Point
======================
Runs HRPO-X demos and system checks.
"""

import sys
from pathlib import Path

# Add parent directory to import hrpo_core_v2_2
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from hrpo_core_v2_2 import main as run_core_demo
import logging

logger = logging.getLogger("HRPO-X-CLI")

def main():
    """Run HRPO-X demo."""
    logger.info("Running HRPO-X demo from CLI...")
    run_core_demo()


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
