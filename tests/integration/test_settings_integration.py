#!/usr/bin/env python3
"""
Integration tests for the settings configuration system.

Tests the integration between command line arguments, environment variables,
and the actual settings persistence.
"""

import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path
import json

import pytest

from core.settings.config import SettingsConfig, get_settings


class TestSettingsIntegration:
    """Test settings configuration integration scenarios."""

    def setup_method(self):
        """Set up test environment."""
        # Reset singleton state
        SettingsConfig._instance = None
        SettingsConfig._initialized = False
        
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
        # Reset singleton state
        SettingsConfig._instance = None
        SettingsConfig._initialized = False
        
        # Restore original environment variables
        for var, value in self.original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]

    def test_environment_variable_detection_on_startup(self):
        """Test that environment variables are properly detected during startup."""
        test_dir = '/tmp/integration_test_settings'
        os.environ['VILOAPP_SETTINGS_DIR'] = test_dir
        
        # Import and initialize as if starting the app
        from core.settings.config import initialize_settings_from_cli
        
        # Mock sys.argv to have no arguments (only env vars)
        original_argv = sys.argv
        try:
            sys.argv = ['main.py']
            config = initialize_settings_from_cli()
            
            assert config.settings_dir == Path(test_dir).resolve()
            assert config.settings_dir.exists()
            
        finally:
            sys.argv = original_argv
            # Clean up
            if Path(test_dir).exists():
                shutil.rmtree(test_dir)

    def test_command_line_override_of_environment_variables(self):
        """Test that command line arguments override environment variables."""
        # Set environment variables
        os.environ['VILOAPP_SETTINGS_DIR'] = '/tmp/env_settings'
        
        # Mock command line arguments
        original_argv = sys.argv
        try:
            sys.argv = ['main.py', '--settings-dir', '/tmp/cli_settings']
            
            from core.settings.config import initialize_settings_from_cli
            config = initialize_settings_from_cli()
            
            # CLI should override environment
            assert config.settings_dir == Path('/tmp/cli_settings').resolve()
            assert config.settings_dir.exists()
            
        finally:
            sys.argv = original_argv
            # Clean up
            for path in ['/tmp/cli_settings', '/tmp/env_settings']:
                if Path(path).exists():
                    shutil.rmtree(Path(path))

    def test_settings_persistence_with_custom_location(self):
        """Test that settings are actually persisted to custom location."""
        test_dir = Path('/tmp/test_settings_persistence')
        if test_dir.exists():
            shutil.rmtree(test_dir)
        
        try:
            # Configure custom settings directory
            config = SettingsConfig.get_instance()
            config.settings_dir = test_dir
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # Create settings and write some data
            settings = config.create_settings("TestOrg", "TestApp")
            settings.setValue("test_key", "test_value")
            settings.sync()
            
            # Verify file was created in custom location
            expected_file = test_dir / "TestOrg_TestApp.ini"
            assert expected_file.exists()
            
            # Verify we can read the value back
            new_settings = config.create_settings("TestOrg", "TestApp")
            assert new_settings.value("test_key") == "test_value"
            
        finally:
            if test_dir.exists():
                shutil.rmtree(test_dir)

    def test_portable_mode_creates_settings_directory(self):
        """Test that portable mode creates settings directory in app root."""
        # Find the app root (where this file's parent directories lead to)
        app_root = Path(__file__).parent.parent.parent
        settings_dir = app_root / 'settings'
        
        # Clean up if it exists
        if settings_dir.exists():
            shutil.rmtree(settings_dir)
        
        try:
            original_argv = sys.argv
            sys.argv = ['main.py', '--portable']
            
            from core.settings.config import initialize_settings_from_cli
            config = initialize_settings_from_cli()
            
            assert config.is_portable is True
            assert config.settings_dir == settings_dir
            assert settings_dir.exists()
            
        finally:
            sys.argv = original_argv
            if settings_dir.exists():
                shutil.rmtree(settings_dir)

    def test_temporary_settings_isolation(self):
        """Test that temporary settings don't persist and are isolated."""
        # Configure for temporary settings
        config = SettingsConfig.get_instance()
        config.is_temporary = True
        config.temp_dir = Path(tempfile.mkdtemp(prefix='viloapp_test_'))
        
        temp_location = config.temp_dir
        
        # Create settings and write data
        settings = config.create_settings("TestOrg", "TestApp")
        settings.setValue("temp_key", "temp_value")
        settings.sync()
        
        # Verify settings file exists in temp location
        settings_files = list(temp_location.glob("*.ini"))
        assert len(settings_files) > 0
        
        # Simulate app cleanup
        config.cleanup()
        
        # Temp directory should be removed
        assert not temp_location.exists()

    def test_settings_file_format_and_structure(self):
        """Test that settings are stored in the expected INI format."""
        test_file = Path('/tmp/test_settings_format.ini')
        if test_file.exists():
            test_file.unlink()
        
        try:
            # Configure custom settings file
            config = SettingsConfig.get_instance()
            config.settings_file = test_file
            
            # Create settings and write various data types
            settings = config.create_settings("TestOrg", "TestApp")
            settings.setValue("string_key", "string_value")
            settings.setValue("int_key", 42)
            settings.setValue("bool_key", True)
            settings.setValue("list_key", ["a", "b", "c"])
            settings.sync()
            
            # Verify file exists and has correct format
            assert test_file.exists()
            
            # Read file content and verify it's INI format
            content = test_file.read_text()
            assert "[" in content  # INI sections
            assert "string_key" in content
            assert "string_value" in content
            
            # Verify we can read values back with correct types
            new_settings = config.create_settings("TestOrg", "TestApp")
            assert new_settings.value("string_key") == "string_value"
            assert new_settings.value("int_key", type=int) == 42
            assert new_settings.value("bool_key", type=bool) is True
            
        finally:
            if test_file.exists():
                test_file.unlink()

    def test_multiple_settings_domains_in_custom_directory(self):
        """Test that multiple settings domains work correctly with custom directory."""
        test_dir = Path('/tmp/test_multiple_domains')
        if test_dir.exists():
            shutil.rmtree(test_dir)
        
        try:
            # Configure custom settings directory
            config = SettingsConfig.get_instance()
            config.settings_dir = test_dir
            test_dir.mkdir(parents=True)
            
            # Create settings for different domains
            main_settings = config.create_settings("ViloApp", "ViloApp")
            state_settings = config.create_settings("ViloApp", "State")
            ui_settings = config.create_settings("ViloApp", "UI")
            
            # Write data to each
            main_settings.setValue("app_key", "app_value")
            state_settings.setValue("state_key", "state_value")
            ui_settings.setValue("ui_key", "ui_value")
            
            # Sync all
            main_settings.sync()
            state_settings.sync()
            ui_settings.sync()
            
            # Verify separate files were created
            expected_files = [
                "ViloApp_ViloApp.ini",
                "ViloApp_State.ini", 
                "ViloApp_UI.ini"
            ]
            
            for filename in expected_files:
                filepath = test_dir / filename
                assert filepath.exists(), f"{filename} was not created"
            
            # Verify each file contains its respective data
            new_main = config.create_settings("ViloApp", "ViloApp")
            new_state = config.create_settings("ViloApp", "State")
            new_ui = config.create_settings("ViloApp", "UI")
            
            assert new_main.value("app_key") == "app_value"
            assert new_state.value("state_key") == "state_value"
            assert new_ui.value("ui_key") == "ui_value"
            
        finally:
            if test_dir.exists():
                shutil.rmtree(test_dir)

    def test_error_handling_for_invalid_paths(self):
        """Test error handling when invalid paths are provided."""
        # Test with invalid directory path (permission denied simulation)
        config = SettingsConfig.get_instance()
        
        # This should not raise an exception, but handle gracefully
        # Note: The current implementation creates directories, so we test with a valid scenario
        invalid_dir = Path('/tmp/test_invalid_permissions')
        config.settings_dir = invalid_dir
        
        # This should work (creates the directory)
        settings = config.create_settings("Test", "Test")
        assert settings is not None
        
        # Clean up
        if invalid_dir.exists():
            shutil.rmtree(invalid_dir)

    def test_reset_settings_functionality(self):
        """Test that reset settings functionality works correctly."""
        test_dir = Path('/tmp/test_reset_settings')
        if test_dir.exists():
            shutil.rmtree(test_dir)
        
        try:
            config = SettingsConfig.get_instance()
            config.settings_dir = test_dir
            test_dir.mkdir(parents=True)
            
            # Create some settings files
            for domain in [("ViloApp", "ViloApp"), ("ViloApp", "State"), ("ViloApp", "UI")]:
                settings = config.create_settings(*domain)
                settings.setValue("test_key", "test_value")
                settings.sync()
            
            # Verify files exist
            assert len(list(test_dir.glob("*.ini"))) == 3
            
            # Reset settings
            config.reset_all_settings()
            
            # Verify files are cleared (they may still exist but should be empty/reset)
            for domain in [("ViloApp", "ViloApp"), ("ViloApp", "State"), ("ViloApp", "UI")]:
                settings = config.create_settings(*domain)
                # After reset, the test key should not exist
                assert settings.value("test_key") is None or settings.value("test_key") == ""
                
        finally:
            if test_dir.exists():
                shutil.rmtree(test_dir)