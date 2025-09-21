"""Tests for CLI configuration."""

import pytest
import tempfile
import yaml
from pathlib import Path

from viloapp_cli.config import CLIConfig


class TestCLIConfig:
    """Test CLI configuration management."""

    def test_default_config_creation(self):
        """Test default configuration is created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test-config.yaml"
            config = CLIConfig(config_path)

            assert config_path.exists()
            assert config.get("development.default_port") == 8080
            assert config.get("development.hot_reload") is True

    def test_config_loading(self):
        """Test loading existing configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test-config.yaml"

            # Create config file
            config_data = {
                "plugins": {
                    "directory": "/custom/path",
                },
                "development": {
                    "default_port": 9000,
                }
            }

            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            # Load config
            config = CLIConfig(config_path)
            assert config.get("plugins.directory") == "/custom/path"
            assert config.get("development.default_port") == 9000

    def test_config_get_with_default(self):
        """Test getting configuration with default value."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test-config.yaml"
            config = CLIConfig(config_path)

            # Test existing key
            assert config.get("development.default_port") == 8080

            # Test non-existing key with default
            assert config.get("nonexistent.key", "default_value") == "default_value"

            # Test non-existing key without default
            assert config.get("nonexistent.key") is None

    def test_config_set(self):
        """Test setting configuration values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test-config.yaml"
            config = CLIConfig(config_path)

            # Set new value
            config.set("custom.setting", "test_value")
            assert config.get("custom.setting") == "test_value"

            # Verify it was saved to file
            config2 = CLIConfig(config_path)
            assert config2.get("custom.setting") == "test_value"

    def test_config_nested_keys(self):
        """Test nested configuration keys."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test-config.yaml"
            config = CLIConfig(config_path)

            # Set nested value
            config.set("level1.level2.level3", "deep_value")
            assert config.get("level1.level2.level3") == "deep_value"

            # Verify intermediate levels were created
            assert isinstance(config.get("level1"), dict)
            assert isinstance(config.get("level1.level2"), dict)

    def test_plugins_directory(self):
        """Test plugins directory path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test-config.yaml"
            config = CLIConfig(config_path)

            plugins_dir = config.get_plugins_directory()
            assert isinstance(plugins_dir, Path)

    def test_templates_directory(self):
        """Test templates directory path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test-config.yaml"
            config = CLIConfig(config_path)

            templates_dir = config.get_templates_directory()
            assert isinstance(templates_dir, Path)

    def test_ensure_directories(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test-config.yaml"

            # Set custom directories
            custom_plugins_dir = Path(temp_dir) / "custom-plugins"
            custom_templates_dir = Path(temp_dir) / "custom-templates"

            config_data = {
                "plugins": {
                    "directory": str(custom_plugins_dir),
                    "templates_directory": str(custom_templates_dir),
                }
            }

            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            config = CLIConfig(config_path)
            config.ensure_directories()

            assert custom_plugins_dir.exists()
            assert custom_templates_dir.exists()

    def test_invalid_config_file(self):
        """Test handling of invalid configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "invalid-config.yaml"

            # Create invalid YAML file
            config_path.write_text("invalid: yaml: content: [")

            # Should fall back to defaults without crashing
            config = CLIConfig(config_path)
            assert config.get("development.default_port") == 8080