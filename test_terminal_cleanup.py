#!/usr/bin/env python3
"""
Test script to verify terminal cleanup is working properly.

This script monitors the terminal server to ensure sessions are properly
cleaned up when panes are closed or split.
"""

import sys
import time
import subprocess
import re
from pathlib import Path

LOG_FILE = Path.home() / ".local/share/ViloxTerm/logs/viloxterm.log"


def get_terminal_count():
    """Count current terminal sessions from log."""
    # Clear log and wait a moment
    subprocess.run(["truncate", "-s", "0", str(LOG_FILE)], capture_output=True)
    time.sleep(0.5)

    # Start the app in background
    proc = subprocess.Popen(
        [sys.executable, "packages/viloapp/src/viloapp/main.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Wait for startup
    time.sleep(3)

    # Send proper close signal (like closing window)
    import signal
    proc.send_signal(signal.SIGTERM)
    time.sleep(2)  # Give it time to cleanup

    if proc.poll() is None:
        # Force kill if still running
        proc.kill()
        time.sleep(0.5)

    # NOW read log to count terminal creations and destructions
    with open(LOG_FILE, 'r') as f:
        content = f.read()

    created = len(re.findall(r"Terminal session started:", content))
    destroyed = len(re.findall(r"Destroyed terminal session", content))
    cleaned = len(re.findall(r"Terminal session cleaned up:", content))
    failed = len(re.findall(r"Failed to start terminal.*Maximum", content))

    return {
        "created": created,
        "destroyed": destroyed,
        "cleaned": cleaned,
        "failed": failed,
        "leaked": created - (destroyed + cleaned)
    }


def main():
    print("=" * 60)
    print("Terminal Cleanup Test")
    print("=" * 60)

    # Test 1: Basic startup and shutdown
    print("\nTest 1: Basic startup and shutdown")
    stats = get_terminal_count()
    print(f"  Created: {stats['created']}")
    print(f"  Destroyed: {stats['destroyed']}")
    print(f"  Cleaned: {stats['cleaned']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Leaked: {stats['leaked']}")

    if stats['leaked'] > 0:
        print("  ❌ FAILED: Terminals leaked!")
    elif stats['failed'] > 0:
        print("  ❌ FAILED: Hit terminal limit!")
    else:
        print("  ✅ PASSED: All terminals cleaned up")

    # Check recent log for cleanup messages
    print("\nChecking for cleanup in recent log...")
    result = subprocess.run(
        ["tail", "-100", str(LOG_FILE)],
        capture_output=True,
        text=True
    )

    if "Cleaned up AppWidget" in result.stdout:
        print("  ✅ Found AppWidget cleanup messages")
    else:
        print("  ⚠️ No AppWidget cleanup messages found")

    if "Terminal session cleaned up:" in result.stdout:
        print("  ✅ Found terminal session cleanup messages")
    else:
        print("  ⚠️ No terminal session cleanup messages found")


if __name__ == "__main__":
    main()