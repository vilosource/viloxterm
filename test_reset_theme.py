#!/usr/bin/env python3
"""
Test script to verify --reset-theme functionality.
"""

import subprocess
import sys
from pathlib import Path


def test_reset_theme():
    """Test that --reset-theme switch resets theme to vscode-dark."""

    # Run app with --reset-theme and --test-mode (so it doesn't wait for UI)
    # Capture output to verify theme reset happened
    cmd = [
        sys.executable, "main.py",
        "--reset-theme",
        "--test-mode",
        "--no-confirm"
    ]

    print("Testing --reset-theme switch...")
    print(f"Command: {' '.join(cmd)}")

    try:
        # Run for a short time then kill
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(__file__).parent
        )

        # Let it run for 2 seconds then terminate
        try:
            stdout, stderr = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()

        # Check if theme reset messages appear in stderr (where logging goes)
        if "Theme reset requested" in stderr and "Theme reset to default: vscode-dark" in stderr:
            print("✅ SUCCESS: --reset-theme switch working correctly")
            print("   - Command line argument parsed")
            print("   - Theme service reset theme to vscode-dark")
            return True
        else:
            print("❌ FAILED: Expected theme reset messages not found")
            print("STDERR:", stderr[-500:])  # Last 500 chars
            return False

    except Exception as e:
        print(f"❌ ERROR: Failed to test --reset-theme: {e}")
        return False

if __name__ == "__main__":
    success = test_reset_theme()
    sys.exit(0 if success else 1)
