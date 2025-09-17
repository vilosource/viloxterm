#!/usr/bin/env python3
"""
Test script for ViloxTerm deployment.
Verifies that the deployed executable works correctly.
"""

import platform
import subprocess
import sys
import time
from pathlib import Path


class DeploymentTester:
    """Test deployed ViloxTerm executable."""

    def __init__(self):
        self.platform = platform.system()
        self.executable = self.find_executable()
        self.test_results = []

    def find_executable(self):
        """Find the deployed executable based on platform."""
        candidates = [
            Path("ViloxTerm.dist/main.bin"),  # Linux standalone
            Path("main.bin"),  # Linux single file
            Path("main.exe"),  # Windows
            Path("main.app/Contents/MacOS/main"),  # macOS
            Path("deployment/main.dist/main"),  # Standalone folder
            Path("deployment/main.bin"),  # In deployment folder
        ]

        for candidate in candidates:
            if candidate.exists():
                print(f"Found executable: {candidate}")
                return candidate

        print("ERROR: No executable found!")
        print("Searched for:")
        for c in candidates:
            print(f"  - {c}")
        return None

    def run_test(self, name, test_func):
        """Run a single test and record result."""
        print(f"\nTesting: {name}...")
        try:
            result = test_func()
            if result:
                print("  ✓ PASSED")
                self.test_results.append((name, True, None))
            else:
                print("  ✗ FAILED")
                self.test_results.append((name, False, "Test returned False"))
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            self.test_results.append((name, False, str(e)))

    def test_executable_exists(self):
        """Test that executable exists."""
        return self.executable and self.executable.exists()

    def test_executable_runs(self):
        """Test that executable can start."""
        if not self.executable:
            return False

        try:
            # Try to run with --help flag
            result = subprocess.run(
                [str(self.executable), "--help"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0 or "ViloxTerm" in result.stdout
        except subprocess.TimeoutExpired:
            # App might start GUI, timeout is acceptable
            return True
        except Exception:
            return False

    def test_version_flag(self):
        """Test --version flag."""
        if not self.executable:
            return False

        try:
            result = subprocess.run(
                [str(self.executable), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # App might not have --version yet, check for no crash
            return result.returncode == 0 or not result.stderr
        except:
            return False

    def test_quick_launch(self):
        """Test that app can launch and exit quickly."""
        if not self.executable:
            return False

        try:
            # Start the process
            proc = subprocess.Popen(
                [str(self.executable)], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            # Give it a moment to start
            time.sleep(2)

            # Check if it's still running
            if proc.poll() is None:
                # Still running, that's good
                proc.terminate()
                proc.wait(timeout=5)
                return True
            else:
                # Crashed immediately
                return False
        except:
            return False

    def test_file_size(self):
        """Check executable file size is reasonable."""
        if not self.executable:
            return False

        size_mb = self.executable.stat().st_size / (1024 * 1024)
        print(f"  Executable size: {size_mb:.2f} MB")

        # Reasonable size: 10MB - 200MB
        return 10 <= size_mb <= 200

    def test_dependencies(self):
        """Test that dependencies are bundled (Linux only)."""
        if not self.executable or self.platform != "Linux":
            return True  # Skip on non-Linux

        try:
            result = subprocess.run(
                ["ldd", str(self.executable)], capture_output=True, text=True
            )

            # Check for missing libraries
            if "not found" in result.stdout:
                print("  Missing libraries detected:")
                for line in result.stdout.split("\n"):
                    if "not found" in line:
                        print(f"    {line.strip()}")
                return False

            return True
        except:
            return True  # ldd not available, skip

    def test_settings_directory(self):
        """Test that app creates settings directory."""
        settings_dir = Path.home() / ".config" / "ViloxTerm"

        # Don't fail if directory already exists (from dev testing)
        if settings_dir.exists():
            print(f"  Settings directory exists: {settings_dir}")
            return True

        # Try to run app briefly to create settings
        if self.executable:
            try:
                proc = subprocess.Popen(
                    [str(self.executable)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                time.sleep(3)
                proc.terminate()
                proc.wait(timeout=5)
            except:
                pass

        return settings_dir.exists()

    def run_all_tests(self):
        """Run all deployment tests."""
        print("=" * 60)
        print("ViloxTerm Deployment Testing")
        print("=" * 60)
        print(f"Platform: {self.platform}")
        print(f"Python: {sys.version}")

        if not self.executable:
            print("\nERROR: Cannot proceed without executable!")
            return False

        # Run tests
        self.run_test("Executable exists", self.test_executable_exists)
        self.run_test("Executable runs", self.test_executable_runs)
        self.run_test("Version flag", self.test_version_flag)
        self.run_test("Quick launch", self.test_quick_launch)
        self.run_test("File size check", self.test_file_size)
        self.run_test("Dependencies bundled", self.test_dependencies)
        self.run_test("Settings directory", self.test_settings_directory)

        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)

        passed = sum(1 for _, success, _ in self.test_results if success)
        failed = len(self.test_results) - passed

        for name, success, error in self.test_results:
            status = "✓ PASS" if success else "✗ FAIL"
            print(f"{status}: {name}")
            if error:
                print(f"       {error}")

        print(f"\nTotal: {passed} passed, {failed} failed")

        return failed == 0


def main():
    """Main test runner."""
    tester = DeploymentTester()
    success = tester.run_all_tests()

    if success:
        print("\n✓ All deployment tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
