"""Tests for migration tools."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from migration.settings_migrator import SettingsMigrator
from migration.backward_compatibility import ConfigurationMigrator, deprecated


class TestSettingsMigrator:
    """Test settings migration functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.old_settings_path = self.temp_dir / "old_settings.json"
        self.new_settings_path = self.temp_dir / "new_settings.json"

        self.migrator = SettingsMigrator()
        self.migrator.old_settings_path = self.old_settings_path
        self.migrator.new_settings_path = self.new_settings_path

    def test_needs_migration(self):
        """Test migration detection."""
        # No migration needed when old settings don't exist
        assert not self.migrator.needs_migration()

        # Create old settings
        old_settings = {"theme": "dark", "terminal_font": "monospace"}
        with open(self.old_settings_path, 'w') as f:
            json.dump(old_settings, f)

        # Should need migration now
        assert self.migrator.needs_migration()

        # Create new settings - should not need migration
        with open(self.new_settings_path, 'w') as f:
            json.dump({"version": "2.0"}, f)

        assert not self.migrator.needs_migration()

    def test_transform_settings(self):
        """Test settings transformation."""
        old_settings = {
            "theme": "dark",
            "window_width": 1200,
            "window_height": 800,
            "terminal_font": "monospace",
            "terminal_font_size": 14,
            "terminal_bg": "#000000",
            "editor_font": "courier",
            "tab_width": 2
        }

        new_settings = self.migrator._transform_settings(old_settings)

        assert new_settings["version"] == "2.0"
        assert new_settings["core"]["theme"] == "dark"
        assert new_settings["core"]["window"]["width"] == 1200
        assert new_settings["plugins"]["viloxterm"]["settings"]["font_family"] == "monospace"
        assert new_settings["plugins"]["viloxterm"]["settings"]["font_size"] == 14
        assert new_settings["plugins"]["viloedit"]["settings"]["tab_width"] == 2

    def test_migrate_settings(self):
        """Test complete settings migration."""
        # Create old settings
        old_settings = {
            "theme": "light",
            "terminal_font": "courier",
            "editor_font_size": 16
        }

        with open(self.old_settings_path, 'w') as f:
            json.dump(old_settings, f)

        # Perform migration
        result = self.migrator.migrate_settings()
        assert result is True

        # Check new settings were created
        assert self.new_settings_path.exists()

        with open(self.new_settings_path, 'r') as f:
            new_settings = json.load(f)

        assert new_settings["version"] == "2.0"
        assert new_settings["core"]["theme"] == "light"


class TestConfigurationMigrator:
    """Test configuration migration functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.migrator = ConfigurationMigrator()

    def test_migrate_config_key(self):
        """Test single key migration."""
        # Test mapped key
        result = self.migrator.migrate_config_key("terminal_font", "monospace")
        assert result == ("viloxterm.font_family", "monospace")

        # Test unmapped key
        result = self.migrator.migrate_config_key("unknown_key", "value")
        assert result is None

    def test_migrate_all_config(self):
        """Test complete configuration migration."""
        old_config = {
            "terminal_font": "monospace",
            "terminal_font_size": 12,
            "editor_font": "courier",
            "unknown_setting": "value"
        }

        new_config = self.migrator.migrate_all_config(old_config)

        # Check migrated keys
        assert new_config["viloxterm"]["font_family"] == "monospace"
        assert new_config["viloxterm"]["font_size"] == 12
        assert new_config["viloedit"]["font_family"] == "courier"

        # Check unmapped key is preserved
        assert new_config["unknown_setting"] == "value"

    def test_set_nested_key(self):
        """Test nested key setting."""
        config = {}
        self.migrator._set_nested_key(config, "plugin.setting.subsetting", "value")

        assert config["plugin"]["setting"]["subsetting"] == "value"


class TestBackwardCompatibility:
    """Test backward compatibility features."""

    def test_deprecated_decorator(self):
        """Test deprecated function decorator."""
        @deprecated("Use new_function instead")
        def old_function():
            return "old"

        with pytest.warns(UserWarning, match="old_function is deprecated"):
            result = old_function()
            assert result == "old"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])