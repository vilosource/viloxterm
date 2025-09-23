#!/usr/bin/env python3
"""
Quick validation script for CI/CD pipelines.

Simple wrapper around validate_app.py with sensible defaults.
Returns 0 on success, non-zero on failure.
"""

import subprocess
import sys

def main():
    """Run quick validation."""
    # Run validation with default settings
    result = subprocess.run(
        [sys.executable, "validate_app.py"],
        capture_output=False,  # Show output directly
        text=True
    )
    
    # Exit with same code as validator
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()