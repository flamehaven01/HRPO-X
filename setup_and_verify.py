#!/usr/bin/env python3
"""
HRPO-X v2.2f Quick Setup and Verification
Run this script to verify installation and run basic tests
"""

import sys
import subprocess
import os
from pathlib import Path

def print_header(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}\n")

def run_command(cmd, description):
    print(f"[>] {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"[+] Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] Failed: {e}")
        if e.stdout:
            print(f"    stdout: {e.stdout[:200]}")
        if e.stderr:
            print(f"    stderr: {e.stderr[:200]}")
        return False

def check_python_version():
    """Verify Python 3.10+"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"[+] Python {version.major}.{version.minor}.{version.micro} OK")
        return True
    else:
        print(f"[-] Python {version.major}.{version.minor} < 3.10 (upgrade required)")
        return False

def main():
    print_header("HRPO-X v2.2f Setup & Verification")
    
    # Check Python version
    if not check_python_version():
        print("[!] Please upgrade to Python 3.10 or higher")
        return 1
    
    # Check if we're in the right directory
    if not Path("hrpo_core_v2_2.py").exists():
        print("[-] Error: Must run from HRPO-X root directory")
        return 1
    
    print("[+] Working directory verified")
    
    # Create virtual environment
    print_header("Setting up Python environment")
    
    if not Path("venv").exists():
        run_command(f"{sys.executable} -m venv venv", "Creating virtual environment")
    else:
        print("[*] Virtual environment already exists")
    
    # Determine activation command
    if sys.platform == "win32":
        pip_cmd = r"venv\Scripts\pip.exe"
        python_cmd = r"venv\Scripts\python.exe"
    else:
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
    
    # Install dependencies
    print_header("Installing dependencies")
    run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip")
    run_command(f"{pip_cmd} install -r requirements.txt", "Installing requirements")
    
    # Run core demo
    print_header("Running HRPO-X Core Demo")
    if run_command(f"{python_cmd} hrpo_core_v2_2.py", "Testing core functionality"):
        print("[+] Core demo completed successfully")
    
    # Run tests
    print_header("Running Test Suite")
    if run_command(f"{pip_cmd} install pytest pytest-cov", "Installing test dependencies"):
        run_command(f"{python_cmd} -m pytest tests/test_core.py -v", "Running unit tests")
    
    # Print summary
    print_header("Setup Complete!")
    
    print("""
[*] HRPO-X v2.2f is ready!

Quick Start Commands:
  
  # Activate environment (Linux/Mac)
  $ source venv/bin/activate
  
  # Activate environment (Windows)
  $ venv\\Scripts\\activate
  
  # Run core demo
  $ python hrpo_core_v2_2.py
  
  # Run tests
  $ pytest tests/ -v
  
  # Start training (single GPU)
  $ bash scripts/train.sh config/base_config.yaml
  
Documentation:
  - README.md - Overview and quick start
  - docs/ARCHITECTURE.md - System design
  - docs/EVIDENCE_TRAIL.md - Paper compliance verification
  
For issues or questions, see: https://github.com/your-org/hrpo-x
""")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
