#!/usr/bin/env python3
"""
Unit tests for the SettingsConfig class.

Tests the configurable settings system including command line arguments
and environment variables.
"""

import os
import tempfile
import shutil
import argparse
from pathlib import Path
from unittest import mock

import pytest

from core.settings.config import SettingsConfig, get_settings, initialize_settings_from_cli, get_settings_info


class TestSettingsConfig:
    """Test the SettingsConfig class functionality."""

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

    def test_singleton_pattern(self):
        """Test that SettingsConfig follows singleton pattern."""
        config1 = SettingsConfig.get_instance()
        config2 = SettingsConfig.get_instance()
        
        assert config1 is config2
        assert SettingsConfig._initialized is True

    def test_direct_instantiation_raises_error(self):
        """Test that direct instantiation after singleton raises error."""
        SettingsConfig.get_instance()  # Initialize singleton
        
        with pytest.raises(RuntimeError, match="SettingsConfig is a singleton"):
            SettingsConfig()

    def test_default_configuration(self):
        """Test default configuration with no arguments or environment vars."""
        config = SettingsConfig.get_instance()
        args = argparse.Namespace()
        config._configure_from_args(args)
        
        assert config.settings_dir is None
        assert config.settings_file is None
        assert config.is_portable is False
        assert config.is_temporary is False
        assert config.temp_dir is None

    def test_temp_settings_command_line(self):
        """Test temporary settings via command line argument."""
        config = SettingsConfig.get_instance()
        args = argparse.Namespace(temp_settings=True)
        config._configure_from_args(args)
        
        assert config.is_temporary is True
        assert config.temp_dir is not None
        assert config.temp_dir.exists()
        assert str(config.temp_dir).startswith('/tmp/viloapp_settings_')
        
        # Clean up temp directory
        if config.temp_dir.exists():
            shutil.rmtree(config.temp_dir)

    def test_temp_settings_environment_variable(self):
        """Test temporary settings via environment variable."""
        os.environ['VILOAPP_TEMP_SETTINGS'] = '1'
        
        config = SettingsConfig.get_instance()
        args = argparse.Namespace()
        config._configure_from_args(args)
        
        assert config.is_temporary is True
        assert config.temp_dir is not None
        assert config.temp_dir.exists()
        
        # Clean up temp directory
        if config.temp_dir.exists():
            shutil.rmtree(config.temp_dir)

    def test_portable_mode_command_line(self):
        """Test portable mode via command line argument."""
        config = SettingsConfig.get_instance()
        args = argparse.Namespace(portable=True)
        config._configure_from_args(args)
        
        assert config.is_portable is True
        assert config.settings_dir is not None
        assert config.settings_dir.name == 'settings'
        assert config.settings_dir.exists()
        
        # Clean up
        if config.settings_dir.exists():
            shutil.rmtree(config.settings_dir)

    def test_portable_mode_environment_variable(self):
        """Test portable mode via environment variable."""
        os.environ['VILOAPP_PORTABLE'] = '1'
        
        config = SettingsConfig.get_instance()
        args = argparse.Namespace()
        config._configure_from_args(args)
        
        assert config.is_portable is True
        assert config.settings_dir is not None
        assert config.settings_dir.name == 'settings'
        
        # Clean up
        if config.settings_dir.exists():
            shutil.rmtree(config.settings_dir)

    def test_custom_settings_file_command_line(self):
        """Test custom settings file via command line argument."""
        test_file = Path('/tmp/test_settings.ini')
        
        config = SettingsConfig.get_instance()
        args = argparse.Namespace(settings_file=test_file)
        config._configure_from_args(args)
        
        assert config.settings_file == test_file.resolve()
        assert config.settings_file.parent.exists()
        
        # Clean up
        if test_file.parent.exists() and test_file.parent != Path('/tmp'):
            shutil.rmtree(test_file.parent)

    def test_custom_settings_file_environment_variable(self):
        """Test custom settings file via environment variable."""
        test_file = '/tmp/env_test_settings.ini'
        os.environ['VILOAPP_SETTINGS_FILE'] = test_file
        
        config = SettingsConfig.get_instance()
        args = argparse.Namespace()
        config._configure_from_args(args)
        
        assert config.settings_file == Path(test_file).resolve()
        assert config.settings_file.parent.exists()

    def test_custom_settings_dir_command_line(self):
        """Test custom settings directory via command line argument."""
        test_dir = Path('/tmp/test_settings_dir')
        
        config = SettingsConfig.get_instance()
        args = argparse.Namespace(settings_dir=test_dir)
        config._configure_from_args(args)
        
        assert config.settings_dir == test_dir.resolve()
        assert config.settings_dir.exists()
        
        # Clean up
        if test_dir.exists():
            shutil.rmtree(test_dir)

    def test_custom_settings_dir_environment_variable(self):
        """Test custom settings directory via environment variable."""
        test_dir = '/tmp/env_test_settings_dir'
        os.environ['VILOAPP_SETTINGS_DIR'] = test_dir
        
        config = SettingsConfig.get_instance()
        args = argparse.Namespace()
        config._configure_from_args(args)
        
        assert config.settings_dir == Path(test_dir).resolve()
        assert config.settings_dir.exists()
        
        # Clean up
        if Path(test_dir).exists():
            shutil.rmtree(test_dir)

    def test_command_line_precedence_over_environment(self):
        """Test that command line arguments take precedence over environment variables."""
        # Set environment variables
        os.environ['VILOAPP_SETTINGS_DIR'] = '/tmp/env_dir'
        os.environ['VILOAPP_SETTINGS_FILE'] = '/tmp/env_file.ini'
        
        # Set command line arguments
        cli_dir = Path('/tmp/cli_dir')
        cli_file = Path('/tmp/cli_file.ini')
        
        config = SettingsConfig.get_instance()
        args = argparse.Namespace(settings_dir=cli_dir, settings_file=cli_file)
        config._configure_from_args(args)
        
        # Command line should take precedence, but settings_file wins over settings_dir
        assert config.settings_file == cli_file.resolve()
        assert config.settings_dir is None  # file takes precedence over directory
        
        # Clean up
        if cli_file.parent.exists() and cli_file.parent != Path('/tmp'):
            shutil.rmtree(cli_file.parent)

    def test_settings_file_precedence_over_directory(self):
        """Test that settings file takes precedence over settings directory."""
        test_dir = Path('/tmp/test_dir')
        test_file = Path('/tmp/test_file.ini')
        
        config = SettingsConfig.get_instance()
        args = argparse.Namespace(settings_dir=test_dir, settings_file=test_file)
        config._configure_from_args(args)
        
        # File should take precedence
        assert config.settings_file == test_file.resolve()
        assert config.settings_dir is None

    def test_reset_settings(self):
        """Test settings reset functionality."""
        with mock.patch.object(SettingsConfig, 'reset_all_settings') as mock_reset:
            config = SettingsConfig.get_instance()
            args = argparse.Namespace(reset_settings=True)
            config._configure_from_args(args)
            
            mock_reset.assert_called_once()

    def test_create_settings_temp_mode(self):
        """Test QSettings creation in temporary mode."""
        config = SettingsConfig.get_instance()
        config.is_temporary = True
        config.temp_dir = Path(tempfile.mkdtemp(prefix='viloapp_test_'))
        
        settings = config.create_settings("TestOrg", "TestApp")
        
        assert settings is not None
        assert str(config.temp_dir) in settings.fileName()
        
        # Clean up
        if config.temp_dir.exists():
            shutil.rmtree(config.temp_dir)

    def test_create_settings_custom_file(self):
        """Test QSettings creation with custom file."""
        test_file = Path('/tmp/test_custom.ini')
        
        config = SettingsConfig.get_instance()
        config.settings_file = test_file
        
        settings = config.create_settings("TestOrg", "TestApp")
        
        assert settings is not None
        assert str(test_file) == settings.fileName()

    def test_create_settings_custom_dir(self):
        """Test QSettings creation with custom directory."""
        test_dir = Path('/tmp/test_custom_dir')
        test_dir.mkdir(exist_ok=True)
        
        config = SettingsConfig.get_instance()
        config.settings_dir = test_dir
        
        settings = config.create_settings("TestOrg", "TestApp")
        
        assert settings is not None
        expected_file = test_dir / "TestOrg_TestApp.ini"
        assert str(expected_file) == settings.fileName()
        
        # Clean up
        if test_dir.exists():
            shutil.rmtree(test_dir)

    def test_get_settings_location_descriptions(self):
        """Test human-readable settings location descriptions."""
        config = SettingsConfig.get_instance()
        
        # Test temporary mode
        config.is_temporary = True
        config.temp_dir = Path('/tmp/test_temp')
        location = config.get_settings_location()
        assert "Temporary directory" in location
        assert str(config.temp_dir) in location
        
        # Reset and test custom file
        config.is_temporary = False
        config.temp_dir = None
        config.settings_file = Path('/tmp/test.ini')
        location = config.get_settings_location()
        assert "Custom file" in location
        assert str(config.settings_file) in location
        
        # Reset and test custom directory
        config.settings_file = None
        config.settings_dir = Path('/tmp/test_dir')
        location = config.get_settings_location()
        assert "Custom directory" in location
        assert str(config.settings_dir) in location

    def test_cleanup_temp_directory(self):
        """Test cleanup of temporary directory."""
        config = SettingsConfig.get_instance()
        config.is_temporary = True
        config.temp_dir = Path(tempfile.mkdtemp(prefix='viloapp_test_'))
        
        # Ensure directory exists
        assert config.temp_dir.exists()
        
        # Clean up
        config.cleanup()
        
        # Directory should be removed
        assert not config.temp_dir.exists()


class TestConvenienceFunctions:
    """Test the convenience functions for settings configuration."""

    def setup_method(self):
        """Set up test environment."""
        SettingsConfig._instance = None
        SettingsConfig._initialized = False

    def teardown_method(self):
        """Clean up test environment."""
        SettingsConfig._instance = None
        SettingsConfig._initialized = False

    def test_get_settings_function(self):
        """Test the get_settings convenience function."""
        config = SettingsConfig.get_instance()
        config.is_temporary = True
        config.temp_dir = Path(tempfile.mkdtemp(prefix='viloapp_test_'))
        
        settings = get_settings("TestOrg", "TestApp")
        
        assert settings is not None
        assert str(config.temp_dir) in settings.fileName()
        
        # Clean up
        if config.temp_dir.exists():
            shutil.rmtree(config.temp_dir)

    @mock.patch('sys.argv', ['main.py', '--temp-settings'])
    def test_initialize_settings_from_cli_function(self):
        """Test the initialize_settings_from_cli convenience function."""
        config = initialize_settings_from_cli()
        
        assert config is not None
        assert isinstance(config, SettingsConfig)
        assert config.is_temporary is True
        
        # Clean up
        if config.temp_dir and config.temp_dir.exists():
            shutil.rmtree(config.temp_dir)

    def test_get_settings_info_function(self):
        """Test the get_settings_info convenience function."""
        config = SettingsConfig.get_instance()
        config.is_portable = True
        config.settings_dir = Path('/tmp/test_portable')
        
        info = get_settings_info()
        
        assert isinstance(info, dict)
        assert 'location' in info
        assert 'is_portable' in info
        assert 'is_temporary' in info
        assert 'custom_dir' in info
        assert 'custom_file' in info
        
        assert info['is_portable'] is True
        assert info['is_temporary'] is False
        assert info['custom_dir'] == str(config.settings_dir)