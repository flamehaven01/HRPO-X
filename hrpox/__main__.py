"""
HRPO-X CLI Entry Point
======================
Runs HRPO-X demos and system checks.
"""
import logging

from .core_v2_2 import main as run_core_demo

logger = logging.getLogger("HRPO-X-CLI")


def main() -> None:
    """Run HRPO-X demo."""
    logger.info("Running HRPO-X demo from CLI...")
    run_core_demo()


if __name__ == "__main__":
    main()
