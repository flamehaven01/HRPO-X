#!/usr/bin/env python3
"""
HRPO-X v1.0.1 Quick Setup and Verification (Research Prototype)
Run this script to verify installation and run basic tests.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys


def print_header(message: str) -> None:
    line = "=" * 60
    print(f"\n{line}")
    print(f"  {message}")
    print(f"{line}\n")


def run_command(cmd: str, description: str) -> bool:
    print(f"[>] {description}...")
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("[+] Success")
        return True
    except subprocess.CalledProcessError as exc:
        print(f"[-] Failed: {exc}")
        if exc.stdout:
            print(f"    stdout: {exc.stdout[:200]}")
        if exc.stderr:
            print(f"    stderr: {exc.stderr[:200]}")
        return False


def check_python_version() -> bool:
    """Verify Python 3.10+."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"[+] Python {version.major}.{version.minor}.{version.micro} OK")
        return True
    print(f"[-] Python {version.major}.{version.minor} < 3.10 (upgrade required)")
    return False


def main() -> int:
    print_header("HRPO-X v1.0.1 Setup & Verification (Prototype)")

    if not check_python_version():
        print("[!] Please upgrade to Python 3.10 or higher")
        return 1

    if not pathlib.Path("hrpox/core_v2_2.py").exists():
        print("[-] Error: Must run from HRPO-X root directory")
        return 1

    print("[+] Working directory verified")

    print_header("Setting up Python environment")

    if not pathlib.Path("venv").exists():
        run_command(f"{sys.executable} -m venv venv", "Creating virtual environment")
    else:
        print("[*] Virtual environment already exists")

    if sys.platform == "win32":
        pip_cmd = r"venv\Scripts\pip.exe"
        python_cmd = r"venv\Scripts\python.exe"
    else:
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"

    print_header("Installing dependencies")
    run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip")
    run_command(f"{pip_cmd} install -r requirements.txt", "Installing requirements")

    print_header("Running HRPO-X Core Demo")
    if run_command(f"{python_cmd} -m hrpox", "Testing core functionality"):
        print("[+] Core demo completed successfully")

    print_header("Running Test Suite")
    if run_command(f"{pip_cmd} install pytest pytest-cov", "Installing test dependencies"):
        run_command(f"{python_cmd} -m pytest tests/ -v", "Running unit tests")

    print_header("Setup Complete")

    print(
        """
[>] HRPO-X v1.0.1 is ready (prototype).

Quick Start Commands:

  # Activate environment (Linux/Mac)
  $ source venv/bin/activate

  # Activate environment (Windows)
  $ venv\\Scripts\\activate

  # Run core demo
  $ python -m hrpox

  # Run simple demo
  $ python examples/simple_demo.py

  # Run tests
  $ pytest tests/ -v

Documentation:
  - README.md
  - docs/ARCHITECTURE.md
  - docs/PAPER_TO_CODE_MAP.md
  - roadmap.md

For issues or questions, see: https://github.com/your-org/hrpo-x
"""
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
