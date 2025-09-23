#!/usr/bin/env python3
"""
Application validation tool for ViloxTerm.

This tool verifies that the application can start successfully without exceptions.
It monitors logs for success markers and failure patterns, with a configurable timeout.

Exit codes:
    0: Success - application started without exceptions
    1: Timeout - no startup marker within timeout period
    2: Exception detected during startup
    3: Process crashed or exited unexpectedly
"""

import sys
import subprocess
import time
import re
import threading
from pathlib import Path
import logging

# Configure logging for the validator itself
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class AppValidator:
    """Validates ViloxTerm application startup."""

    # Success indicators to look for in logs
    SUCCESS_MARKERS = [
        "=== APPLICATION STARTUP COMPLETE ===",
        "ViloxTerm is ready for use"
    ]

    # Failure indicators (regex patterns)
    FAILURE_PATTERNS = [
        r"AttributeError:",
        r"ImportError:",
        r"ModuleNotFoundError:",
        r"TypeError:",
        r"ValueError:",
        r"NameError:",
        r"KeyError:",
        r"CRITICAL.*failed",
        r"CRITICAL.*error",
        r"sys\.exit\([1-9]",  # Non-zero exit
    ]

    # Known non-critical exceptions to ignore
    NON_CRITICAL_PATTERNS = [
        r"PluginLoadError: Failed to load module for core-",  # Built-in plugin load errors
        r"Plugin .* already registered",  # Plugin registration warnings
        r"No fallback for setting",  # Setting warnings
    ]

    def __init__(self, timeout: float = 3.0, verbose: bool = False):
        """Initialize validator.

        Args:
            timeout: Maximum time to wait for startup success (seconds)
            verbose: Enable verbose output
        """
        self.timeout = timeout
        self.verbose = verbose
        self.log_file = Path.home() / ".local/share/ViloxTerm/logs/viloxterm.log"
        self.exception_buffer = []
        self.startup_complete = False
        self.exception_found = None
        self.process = None
        self._stop_monitoring = threading.Event()

    def monitor_logs(self, process: subprocess.Popen) -> None:
        """Monitor application output for success/failure indicators.

        Args:
            process: The application subprocess
        """
        try:
            for line in iter(process.stdout.readline, ''):
                if self._stop_monitoring.is_set():
                    break

                if not line:
                    continue

                line = line.strip()

                # Log verbose output if requested
                if self.verbose:
                    print(f"  LOG: {line}")

                # Check for success markers
                for marker in self.SUCCESS_MARKERS:
                    if marker in line:
                        self.startup_complete = True
                        logger.info(f"✅ Success marker detected: {marker}")
                        return

                # Check for failure patterns
                for pattern in self.FAILURE_PATTERNS:
                    if re.search(pattern, line):
                        # Check if it's a non-critical pattern we should ignore
                        is_non_critical = False
                        for non_critical in self.NON_CRITICAL_PATTERNS:
                            if re.search(non_critical, line):
                                is_non_critical = True
                                if self.verbose:
                                    print(f"  INFO: Ignoring non-critical: {line}")
                                break

                        if not is_non_critical:
                            self.exception_found = line
                            self.exception_buffer.append(line)
                            logger.error(f"❌ Exception pattern detected: {line}")

                            # Continue reading a few more lines for context
                            for _ in range(5):
                                try:
                                    extra_line = process.stdout.readline()
                                    if extra_line:
                                        self.exception_buffer.append(extra_line.strip())
                                except:
                                    break
                            return

                # Store recent lines for context
                if "ERROR" in line or "CRITICAL" in line or "WARNING" in line:
                    self.exception_buffer.append(line)
                    if len(self.exception_buffer) > 20:
                        self.exception_buffer.pop(0)

        except Exception as e:
            logger.error(f"Error monitoring logs: {e}")

    def run_application(self) -> subprocess.Popen:
        """Start the application with validation flag.

        Returns:
            The subprocess object
        """
        cmd = [
            sys.executable,
            "packages/viloapp/src/viloapp/main.py",
            "--validate-startup"
        ]

        if self.verbose:
            logger.info(f"Starting application: {' '.join(cmd)}")

        # Start the application
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        return process

    def validate(self) -> int:
        """Validate application startup.

        Returns:
            Exit code:
                0: Success - app started without exceptions
                1: Timeout - no startup marker within timeout
                2: Exception detected during startup
                3: Process crashed
        """
        logger.info("=" * 60)
        logger.info("ViloxTerm Application Validator")
        logger.info("=" * 60)
        logger.info(f"Timeout: {self.timeout} seconds")
        logger.info(f"Verbose: {self.verbose}")
        logger.info("")

        # Start the application
        logger.info("Starting application...")
        self.process = self.run_application()

        # Start monitoring thread
        monitor_thread = threading.Thread(
            target=self.monitor_logs,
            args=(self.process,),
            daemon=True
        )
        monitor_thread.start()

        # Wait for startup with timeout
        start_time = time.time()
        check_interval = 0.1  # Check every 100ms

        while time.time() - start_time < self.timeout:
            # Check if startup completed successfully
            if self.startup_complete:
                elapsed = time.time() - start_time
                logger.info(f"✅ Application started successfully in {elapsed:.2f} seconds")

                # Give it a moment to ensure clean shutdown
                time.sleep(0.2)

                # Terminate the process cleanly
                try:
                    self.process.terminate()
                    self.process.wait(timeout=1)
                except:
                    self.process.kill()

                return 0

            # Check if exception was found
            if self.exception_found:
                logger.error("❌ Exception detected during startup")
                logger.error("")
                logger.error("Exception details:")
                for line in self.exception_buffer:
                    logger.error(f"  {line}")

                # Terminate the process
                try:
                    self.process.terminate()
                    self.process.wait(timeout=1)
                except:
                    self.process.kill()

                return 2

            # Check if process crashed
            if self.process.poll() is not None:
                exit_code = self.process.returncode

                # Check if it was a clean validation exit
                if exit_code == 0 and self.startup_complete:
                    logger.info("✅ Application validated and exited cleanly")
                    return 0

                logger.error(f"❌ Process exited unexpectedly with code: {exit_code}")

                # Show any captured output
                if self.exception_buffer:
                    logger.error("")
                    logger.error("Last output:")
                    for line in self.exception_buffer[-10:]:
                        logger.error(f"  {line}")

                return 3

            # Wait before next check
            time.sleep(check_interval)

        # Timeout reached
        elapsed = time.time() - start_time
        logger.error(f"⏱️ Timeout: No startup marker seen within {elapsed:.2f} seconds")

        # Show recent output
        if self.exception_buffer:
            logger.error("")
            logger.error("Recent output:")
            for line in self.exception_buffer[-10:]:
                logger.error(f"  {line}")

        # Terminate the process
        self._stop_monitoring.set()
        try:
            self.process.terminate()
            self.process.wait(timeout=1)
        except:
            self.process.kill()

        return 1

    def cleanup(self):
        """Clean up resources."""
        self._stop_monitoring.set()
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=1)
            except:
                self.process.kill()


def main():
    """Main entry point for validation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate ViloxTerm application startup"
    )
    parser.add_argument(
        "-t", "--timeout",
        type=float,
        default=3.0,
        help="Timeout in seconds (default: 3.0)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Continuous monitoring mode (not implemented yet)"
    )

    args = parser.parse_args()

    if args.watch:
        logger.warning("Watch mode not yet implemented")
        # TODO: Implement continuous monitoring with file watchers

    # Create and run validator
    validator = AppValidator(timeout=args.timeout, verbose=args.verbose)

    try:
        exit_code = validator.validate()
    except KeyboardInterrupt:
        logger.warning("\nValidation interrupted by user")
        exit_code = 1
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        exit_code = 1
    finally:
        validator.cleanup()

    # Print summary
    logger.info("")
    logger.info("=" * 60)

    if exit_code == 0:
        logger.info("✅ VALIDATION PASSED")
        logger.info("Application starts successfully without exceptions")
    elif exit_code == 1:
        logger.info("❌ VALIDATION FAILED: TIMEOUT")
        logger.info("Application did not complete startup within timeout")
        logger.info("Check logs at: ~/.local/share/ViloxTerm/logs/viloxterm.log")
    elif exit_code == 2:
        logger.info("❌ VALIDATION FAILED: EXCEPTION")
        logger.info("Exception detected during application startup")
        logger.info("Check logs at: ~/.local/share/ViloxTerm/logs/viloxterm.log")
    elif exit_code == 3:
        logger.info("❌ VALIDATION FAILED: CRASH")
        logger.info("Application process crashed or exited unexpectedly")
        logger.info("Check logs at: ~/.local/share/ViloxTerm/logs/viloxterm.log")

    logger.info("=" * 60)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()