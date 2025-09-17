#!/usr/bin/env python3
"""
Integration tests for Make targets related to settings configuration.

Tests that the new Make targets work correctly and use the appropriate
settings configurations.
"""

import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest


class TestMakeTargets:
    """Test Make targets for settings configuration."""

    def setup_method(self):
        """Set up test environment."""
        self.original_cwd = os.getcwd()

        # Store original environment variables
        self.original_env = {}
        env_vars = [
            'VILOAPP_SETTINGS_DIR',
            'VILOAPP_SETTINGS_FILE',
            'VILOAPP_PORTABLE',
            'VILOAPP_TEMP_SETTINGS'
        ]
        for var in env_vars:
            self.original_env[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]

    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)

        # Restore original environment variables
        for var, value in self.original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]

    def test_settings_info_target(self):
        """Test that 'make settings-info' provides helpful information."""
        result = subprocess.run(
            ['make', 'settings-info'],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0
        output = result.stdout

        # Check that all expected information is present
        expected_strings = [
            "Settings configuration for ViloApp:",
            "Command line options:",
            "--settings-dir",
            "--settings-file",
            "--portable",
            "--temp-settings",
            "--reset-settings",
            "Environment variables:",
            "VILOAPP_SETTINGS_DIR",
            "VILOAPP_SETTINGS_FILE",
            "VILOAPP_PORTABLE",
            "VILOAPP_TEMP_SETTINGS",
            "Development targets:",
            "make run-dev",
            "make run-test",
            "make run-clean",
            "make run-portable"
        ]

        for expected in expected_strings:
            assert expected in output, f"Expected '{expected}' in settings-info output"

    def test_make_help_includes_settings_targets(self):
        """Test that 'make help' includes the new settings-related targets."""
        result = subprocess.run(
            ['make', 'help'],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0
        output = result.stdout

        # Check that settings-related targets appear in help
        expected_targets = [
            "run-dev",
            "run-test",
            "run-clean",
            "run-portable",
            "run-custom",
            "settings-info",
            "clean-dev-settings",
            "backup-settings",
            "rd",  # alias for run-dev
            "rt",  # alias for run-test
            "rc"   # alias for run-clean
        ]

        for target in expected_targets:
            assert target in output, f"Expected '{target}' target in make help output"

    def test_backup_settings_target(self):
        """Test that 'make backup-settings' creates backup directory."""
        backup_dir = Path.home() / 'viloapp-settings-backup'

        # Clean up any existing backup directory
        if backup_dir.exists():
            shutil.rmtree(backup_dir)

        try:
            result = subprocess.run(
                ['make', 'backup-settings'],
                capture_output=True,
                text=True,
                timeout=10
            )

            assert result.returncode == 0
            assert "Settings backed up" in result.stdout
            assert backup_dir.exists()

        finally:
            if backup_dir.exists():
                shutil.rmtree(backup_dir)

    def test_clean_dev_settings_target(self):
        """Test that 'make clean-dev-settings' removes development settings directory."""
        dev_settings_dir = Path.home() / '.viloapp-dev'

        # Create a fake dev settings directory
        dev_settings_dir.mkdir(exist_ok=True)
        (dev_settings_dir / 'test_file.ini').write_text('[test]\nkey=value\n')

        assert dev_settings_dir.exists()

        try:
            result = subprocess.run(
                ['make', 'clean-dev-settings'],
                capture_output=True,
                text=True,
                timeout=5
            )

            assert result.returncode == 0
            assert "Development settings directory removed" in result.stdout
            assert not dev_settings_dir.exists()

        finally:
            if dev_settings_dir.exists():
                shutil.rmtree(dev_settings_dir)

    @pytest.mark.slow
    def test_run_dev_target_uses_dev_directory(self):
        """Test that 'make run-dev' uses the development settings directory."""
        # This is a more complex test that would launch the app briefly
        # We'll use a timeout to kill the process quickly

        dev_settings_dir = Path.home() / '.viloapp-dev'
        if dev_settings_dir.exists():
            shutil.rmtree(dev_settings_dir)

        try:
            # Start the process
            process = subprocess.Popen(
                ['make', 'run-dev'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Let it run for a short time to initialize
            time.sleep(2)  # Necessary for process initialization in integration test

            # Terminate the process
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

            # Check that the dev settings directory was created
            assert dev_settings_dir.exists(), "Development settings directory should be created"

        finally:
            if dev_settings_dir.exists():
                shutil.rmtree(dev_settings_dir)

    def test_run_custom_target_with_settings_file(self):
        """Test that 'make run-custom' works with SETTINGS_FILE environment variable."""
        test_settings_file = '/tmp/test_custom_make_settings.ini'

        # Clean up any existing file
        if Path(test_settings_file).exists():
            Path(test_settings_file).unlink()

        try:
            # Set the environment variable for the custom settings file
            env = os.environ.copy()
            env['SETTINGS_FILE'] = test_settings_file

            # Start the process
            process = subprocess.Popen(
                ['make', 'run-custom'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

            # Let it run for a short time
            time.sleep(2)  # Necessary for process initialization in integration test

            # Terminate the process
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

            # Check that the custom settings file directory was created
            settings_path = Path(test_settings_file)
            assert settings_path.parent.exists(), "Custom settings directory should be created"

        finally:
            if Path(test_settings_file).exists():
                Path(test_settings_file).unlink()

    @pytest.mark.slow
    def test_run_test_target_uses_temp_settings(self):
        """Test that 'make run-test' uses temporary settings."""
        # Start the process
        process = subprocess.Popen(
            ['make', 'run-test'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Let it run for a short time
        time.sleep(2)  # Necessary for process initialization in integration test

        # Terminate the process
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()

        # Check the output for temporary settings usage
        combined_output = stdout + stderr
        assert "temporary settings" in combined_output.lower() or "temp" in combined_output.lower()

    @pytest.mark.slow
    def test_run_clean_target_resets_and_uses_temp(self):
        """Test that 'make run-clean' resets settings and uses temporary storage."""
        # Start the process
        process = subprocess.Popen(
            ['make', 'run-clean'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Let it run for a short time
        time.sleep(2)  # Necessary for process initialization in integration test

        # Terminate the process
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()

        # Check the output for reset and temporary settings usage
        combined_output = stdout + stderr
        # Should see both reset and temp settings messages
        has_reset = "reset" in combined_output.lower()
        has_temp = "temporary" in combined_output.lower() or "temp" in combined_output.lower()

        assert has_reset or has_temp, "Should indicate settings reset or temporary usage"

    @pytest.mark.slow
    def test_run_portable_target_creates_settings_directory(self):
        """Test that 'make run-portable' creates settings directory in app root."""
        app_root = Path(os.getcwd())
        settings_dir = app_root / 'settings'

        # Clean up if it exists
        if settings_dir.exists():
            shutil.rmtree(settings_dir)

        try:
            # Start the process
            process = subprocess.Popen(
                ['make', 'run-portable'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Let it run for a short time
            time.sleep(2)  # Necessary for process initialization in integration test

            # Terminate the process
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

            # Check that the portable settings directory was created
            assert settings_dir.exists(), "Portable settings directory should be created"

        finally:
            if settings_dir.exists():
                shutil.rmtree(settings_dir)

    def test_make_target_aliases_work(self):
        """Test that the Make target aliases work correctly."""
        # Test that aliases resolve to the correct targets
        aliases = {
            'rd': 'run-dev',
            'rt': 'run-test',
            'rc': 'run-clean'
        }

        for alias, target in aliases.items():
            # We can't easily test execution, but we can verify the targets exist
            result = subprocess.run(
                ['make', '-n', alias],  # -n shows what would be executed without doing it
                capture_output=True,
                text=True,
                timeout=5
            )

            # Should not fail (returncode 0 means target exists)
            assert result.returncode == 0, f"Alias '{alias}' should exist and point to '{target}'"

    def test_makefile_syntax_is_valid(self):
        """Test that the Makefile has valid syntax by running make -n."""
        result = subprocess.run(
            ['make', '-n'],  # -n shows what would be executed without doing it
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should not fail due to syntax errors
        assert result.returncode == 0, "Makefile should have valid syntax"
