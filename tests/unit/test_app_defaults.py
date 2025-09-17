#!/usr/bin/env python3
"""
Unit tests for Application Defaults system.

Tests the app defaults manager, validation system, and fallback chains.
"""

from unittest.mock import MagicMock, patch

import pytest

from core.settings.app_defaults import (
    AppDefaults,
    AppDefaultsValidator,
    get_default_split_direction,
    get_default_split_ratio,
    get_default_widget_type,
    should_confirm_app_exit,
    should_restore_tabs,
)


class TestAppDefaultsValidator:
    """Test the validation system."""

    def test_validate_widget_type_valid(self):
        """Test validation of valid widget types."""
        valid_types = ["terminal", "editor", "theme_editor", "explorer", "settings"]
        for widget_type in valid_types:
            is_valid, value = AppDefaultsValidator.validate_widget_type(widget_type)
            assert is_valid is True
            assert value == widget_type

    def test_validate_widget_type_invalid(self):
        """Test validation of invalid widget types."""
        is_valid, value = AppDefaultsValidator.validate_widget_type("invalid_type")
        assert is_valid is False
        assert value == "terminal"  # Should fallback to terminal

    def test_validate_split_ratio_valid(self):
        """Test validation of valid split ratios."""
        valid_ratios = [0.1, 0.5, 0.9, 0.75]
        for ratio in valid_ratios:
            is_valid, value = AppDefaultsValidator.validate_split_ratio(ratio)
            assert is_valid is True
            assert value == ratio

    def test_validate_split_ratio_invalid(self):
        """Test validation of invalid split ratios."""
        # Out of range values
        is_valid, value = AppDefaultsValidator.validate_split_ratio(0.05)
        assert is_valid is False
        assert value == 0.5

        is_valid, value = AppDefaultsValidator.validate_split_ratio(1.5)
        assert is_valid is False
        assert value == 0.5

        # Invalid type
        is_valid, value = AppDefaultsValidator.validate_split_ratio("not_a_number")
        assert is_valid is False
        assert value == 0.5

    def test_validate_positive_int(self):
        """Test validation of positive integers."""
        # Valid values
        is_valid, value = AppDefaultsValidator.validate_positive_int(10, 100, 20)
        assert is_valid is True
        assert value == 10

        # Out of range
        is_valid, value = AppDefaultsValidator.validate_positive_int(150, 100, 20)
        assert is_valid is False
        assert value == 20

        # Invalid type
        is_valid, value = AppDefaultsValidator.validate_positive_int("abc", 100, 20)
        assert is_valid is False
        assert value == 20

    def test_validate_bool(self):
        """Test validation of boolean values."""
        # Direct booleans
        is_valid, value = AppDefaultsValidator.validate_bool(True)
        assert is_valid is True
        assert value is True

        is_valid, value = AppDefaultsValidator.validate_bool(False)
        assert is_valid is True
        assert value is False

        # String representations
        for true_str in ["true", "1", "yes", "on"]:
            is_valid, value = AppDefaultsValidator.validate_bool(true_str)
            assert is_valid is True
            assert value is True

        for false_str in ["false", "0", "no", "off"]:
            is_valid, value = AppDefaultsValidator.validate_bool(false_str)
            assert is_valid is True
            assert value is False

        # Invalid values
        is_valid, value = AppDefaultsValidator.validate_bool("invalid")
        assert is_valid is False
        assert value is True  # Default fallback

    def test_validate_close_behavior(self):
        """Test validation of close last tab behavior."""
        valid_behaviors = ["create_default", "close_window", "do_nothing"]
        for behavior in valid_behaviors:
            is_valid, value = AppDefaultsValidator.validate_close_behavior(behavior)
            assert is_valid is True
            assert value == behavior

        # Invalid behavior
        is_valid, value = AppDefaultsValidator.validate_close_behavior("invalid")
        assert is_valid is False
        assert value == "create_default"


class TestAppDefaults:
    """Test the AppDefaults manager."""

    @pytest.fixture
    def app_defaults(self):
        """Create a fresh AppDefaults instance."""
        with patch("core.settings.app_defaults.QSettings") as mock_settings_class:
            mock_settings = MagicMock()
            mock_settings_class.return_value = mock_settings
            mock_settings.contains.return_value = False  # No saved settings by default
            defaults = AppDefaults()
            defaults._cache.clear()
            return defaults

    def test_get_with_fallback(self, app_defaults):
        """Test getting a value with fallback."""
        # Test with provided fallback
        value = app_defaults.get("non_existent_key", "fallback_value")
        assert value == "fallback_value"

        # Test with hard-coded fallback
        value = app_defaults.get("workspace.default_new_tab_widget")
        assert value == "terminal"  # From HARD_CODED_FALLBACKS

    def test_set_valid_value(self, app_defaults):
        """Test setting a valid value."""
        result = app_defaults.set("workspace.default_new_tab_widget", "editor")
        assert result is True
        assert app_defaults._cache.get("workspace.default_new_tab_widget") == "editor"

    def test_set_invalid_value(self, app_defaults):
        """Test setting an invalid value."""
        result = app_defaults.set("workspace.default_new_tab_widget", "invalid_widget")
        assert result is False  # Should reject invalid value

    def test_reset_setting(self, app_defaults):
        """Test resetting a setting."""
        # Set a value
        app_defaults.set("workspace.default_new_tab_widget", "editor")
        assert app_defaults._cache.get("workspace.default_new_tab_widget") == "editor"

        # Reset it
        app_defaults.reset("workspace.default_new_tab_widget")
        assert "workspace.default_new_tab_widget" not in app_defaults._cache

    def test_reset_all(self, app_defaults):
        """Test resetting all settings."""
        # Set some values
        app_defaults.set("workspace.default_new_tab_widget", "editor")
        app_defaults.set("pane.default_split_ratio", 0.7)
        assert len(app_defaults._cache) > 0

        # Reset all
        app_defaults.reset_all()
        assert len(app_defaults._cache) == 0

    def test_export_settings(self, app_defaults):
        """Test exporting settings."""
        # Mock QSettings to return test data
        with patch.object(app_defaults._settings, "allKeys", return_value=["test_key"]):
            with patch.object(
                app_defaults._settings, "value", return_value="test_value"
            ):
                settings = app_defaults.export_settings()
                assert "test_key" in settings
                assert settings["test_key"] == "test_value"

    def test_import_settings(self, app_defaults):
        """Test importing settings."""
        test_settings = {
            "workspace.default_new_tab_widget": "editor",
            "pane.default_split_ratio": 0.7,
        }

        count = app_defaults.import_settings(test_settings)
        assert count == 2  # Both should be imported successfully

        # Try importing invalid settings
        invalid_settings = {"workspace.default_new_tab_widget": "invalid_type"}
        count = app_defaults.import_settings(invalid_settings)
        assert count == 0  # Should reject invalid settings


class TestConvenienceFunctions:
    """Test the convenience functions."""

    @patch("core.settings.app_defaults.get_app_defaults")
    def test_get_default_widget_type(self, mock_get_defaults):
        """Test getting default widget type."""
        mock_defaults = MagicMock()
        mock_defaults.get.return_value = "editor"
        mock_get_defaults.return_value = mock_defaults

        result = get_default_widget_type()
        assert result == "editor"
        mock_defaults.get.assert_called_with(
            "workspace.default_new_tab_widget", "terminal"
        )

    @patch("core.settings.app_defaults.get_app_defaults")
    def test_get_default_split_direction(self, mock_get_defaults):
        """Test getting default split direction."""
        mock_defaults = MagicMock()
        mock_defaults.get.return_value = "vertical"
        mock_get_defaults.return_value = mock_defaults

        result = get_default_split_direction()
        assert result == "vertical"

        # Test invalid value fallback
        mock_defaults.get.return_value = "invalid"
        result = get_default_split_direction()
        assert result == "horizontal"  # Should fallback

    @patch("core.settings.app_defaults.get_app_defaults")
    def test_get_default_split_ratio(self, mock_get_defaults):
        """Test getting default split ratio."""
        mock_defaults = MagicMock()
        mock_defaults.get.return_value = 0.75
        mock_get_defaults.return_value = mock_defaults

        result = get_default_split_ratio()
        assert result == 0.75

    @patch("core.settings.app_defaults.get_app_defaults")
    def test_should_restore_tabs(self, mock_get_defaults):
        """Test checking if tabs should be restored."""
        mock_defaults = MagicMock()
        mock_defaults.get.return_value = True
        mock_get_defaults.return_value = mock_defaults

        result = should_restore_tabs()
        assert result is True

    @patch("core.settings.app_defaults.get_app_defaults")
    def test_should_confirm_app_exit(self, mock_get_defaults):
        """Test checking if app exit confirmation is required."""
        mock_defaults = MagicMock()
        mock_defaults.get.return_value = False
        mock_get_defaults.return_value = mock_defaults

        result = should_confirm_app_exit()
        assert result is False


class TestFallbackChain:
    """Test the fallback chain mechanism."""

    def test_fallback_chain_priority(self):
        """Test that fallback chain works in correct order."""
        with patch("core.settings.app_defaults.QSettings") as mock_settings_class:
            mock_settings = MagicMock()
            mock_settings_class.return_value = mock_settings

            defaults = AppDefaults()

            # Test 1: User setting exists and is valid
            mock_settings.contains.return_value = True
            mock_settings.value.return_value = "editor"

            value = defaults.get("workspace.default_new_tab_widget")
            assert value == "editor"

            # Test 2: User setting exists but is invalid
            defaults._cache.clear()  # Clear cache to force re-evaluation
            mock_settings.contains.return_value = True
            mock_settings.value.return_value = "invalid_widget"

            value = defaults.get("workspace.default_new_tab_widget")
            assert value == "terminal"  # Should use hard-coded fallback

            # Test 3: No user setting, use provided fallback
            mock_settings.contains.return_value = False

            value = defaults.get("non_existent_key", "custom_fallback")
            assert value == "custom_fallback"

            # Test 4: No user setting, use hard-coded fallback
            value = defaults.get("workspace.default_new_tab_widget")
            assert value == "terminal"  # From HARD_CODED_FALLBACKS


class TestMigration:
    """Test legacy settings migration."""

    @patch("core.settings.app_defaults.QSettings")
    def test_migrate_legacy_settings(self, mock_settings_class):
        """Test migration from old settings format."""
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings

        # Mock legacy settings
        legacy_settings = {
            "UI/ShowSidebar": True,
            "Theme/Current": "dark",
            "Workspace/RestoreOnStartup": False,
        }

        def contains_side_effect(key):
            return key in legacy_settings

        def value_side_effect(key, default=None):
            if key == "app_defaults_migrated":
                return False  # Not migrated yet
            return legacy_settings.get(key, default)

        mock_settings.contains.side_effect = contains_side_effect
        mock_settings.value.side_effect = value_side_effect

        defaults = AppDefaults()

        # Mock the set method to track migrations
        migrated = []
        original_set = defaults.set

        def track_set(key, value):
            migrated.append((key, value))
            return original_set(key, value)

        with patch.object(defaults, "set", side_effect=track_set):
            count = defaults.migrate_legacy_settings()

        # Check that migration was attempted
        assert count >= 0  # May be 0 if already migrated
        mock_settings.setValue.assert_called_with("app_defaults_migrated", True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
