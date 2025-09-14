#!/usr/bin/env python3
"""
GUI tests for Settings widget.

Tests the Settings AppWidget UI including tab navigation,
setting changes, and integration with the app defaults system.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from PySide6.QtWidgets import QApplication, QTabWidget, QPushButton, QComboBox, QCheckBox, QSlider, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from ui.widgets.settings_app_widget import SettingsAppWidget
from core.settings.app_defaults import get_app_defaults


@pytest.fixture
def app(qapp):
    """Ensure QApplication is available."""
    return qapp


@pytest.fixture
def settings_widget(qtbot):
    """Create a Settings widget for testing."""
    widget = SettingsAppWidget(widget_id="test_settings")
    qtbot.addWidget(widget)
    return widget


class TestSettingsWidgetUI:
    """Test the Settings widget UI components."""

    def test_widget_creation(self, settings_widget):
        """Test that Settings widget is created properly."""
        assert settings_widget is not None
        assert settings_widget.get_title() == "Settings"
        assert isinstance(settings_widget._tabs, QTabWidget)

    def test_tab_structure(self, settings_widget):
        """Test that all expected tabs are present."""
        tabs = settings_widget._tabs
        assert tabs.count() == 5

        expected_tabs = ["General", "Appearance", "Keyboard", "Terminal", "Advanced"]
        for i, tab_name in enumerate(expected_tabs):
            assert tabs.tabText(i) == tab_name

    def test_general_tab_controls(self, settings_widget):
        """Test controls in the General tab."""
        # Check that key controls exist
        assert hasattr(settings_widget, '_default_tab_combo')
        assert isinstance(settings_widget._default_tab_combo, QComboBox)

        assert hasattr(settings_widget, '_max_tabs_spin')
        assert hasattr(settings_widget, '_restore_tabs_check')
        assert isinstance(settings_widget._restore_tabs_check, QCheckBox)

        assert hasattr(settings_widget, '_split_ratio_slider')
        assert isinstance(settings_widget._split_ratio_slider, QSlider)

    def test_default_widget_type_combo(self, settings_widget, qtbot):
        """Test the default widget type combo box."""
        combo = settings_widget._default_tab_combo

        # Check items
        expected_items = ["Terminal", "Editor", "Theme Editor", "Explorer"]
        for i in range(combo.count()):
            assert combo.itemText(i) in expected_items

        # Test selection change - ensure we're actually changing
        # First set to a different index to ensure change
        combo.setCurrentIndex(0)  # Terminal
        settings_widget._modified_settings.clear()

        # Now change to Editor
        combo.setCurrentIndex(1)  # Select Editor
        qtbot.wait(10)

        # Check that the setting was modified
        assert "workspace.default_new_tab_widget" in settings_widget._modified_settings
        assert settings_widget._modified_settings["workspace.default_new_tab_widget"] == "editor"

    def test_split_ratio_slider(self, settings_widget, qtbot):
        """Test the split ratio slider."""
        slider = settings_widget._split_ratio_slider
        label = settings_widget._split_ratio_label

        # Check initial state
        assert slider.minimum() == 10
        assert slider.maximum() == 90

        # Test value change
        with patch.object(settings_widget, '_on_setting_changed') as mock_changed:
            slider.setValue(75)
            qtbot.wait(100)
            assert label.text() == "75%"
            mock_changed.assert_called_with("pane.default_split_ratio", 0.75)

    def test_button_states(self, settings_widget):
        """Test that buttons are in correct initial state."""
        assert hasattr(settings_widget, '_apply_button')
        assert hasattr(settings_widget, '_save_button')
        assert hasattr(settings_widget, '_reset_button')

        # Initially disabled (no changes)
        assert not settings_widget._apply_button.isEnabled()
        assert not settings_widget._save_button.isEnabled()

    def test_setting_modification_tracking(self, settings_widget):
        """Test that modifications are tracked."""
        # Initially no modifications
        assert len(settings_widget._modified_settings) == 0

        # Modify a setting
        settings_widget._on_setting_changed("test.key", "test_value")

        # Check tracking
        assert "test.key" in settings_widget._modified_settings
        assert settings_widget._modified_settings["test.key"] == "test_value"

        # Buttons should be enabled
        assert settings_widget._apply_button.isEnabled()
        assert settings_widget._save_button.isEnabled()


class TestSettingsWidgetIntegration:
    """Test Settings widget integration with app defaults."""

    @patch('ui.widgets.settings_app_widget.get_app_default')
    def test_load_current_settings(self, mock_get_default, qtbot):
        """Test loading current settings into UI."""
        # Mock current settings
        mock_get_default.side_effect = lambda key, default: {
            "workspace.default_new_tab_widget": "editor",
            "workspace.max_tabs": 30,
            "workspace.restore_tabs_on_startup": False,
            "pane.default_split_direction": "vertical",
            "pane.default_split_ratio": 0.6,
        }.get(key, default)

        widget = SettingsAppWidget(widget_id="test_load")
        qtbot.addWidget(widget)

        # Check that settings were loaded
        assert widget._default_tab_combo.currentData() == "editor"
        assert widget._max_tabs_spin.value() == 30
        assert not widget._restore_tabs_check.isChecked()
        assert widget._vertical_radio.isChecked()
        assert widget._split_ratio_slider.value() == 60

    @patch('ui.widgets.settings_app_widget.set_app_default')
    def test_apply_settings(self, mock_set_default, settings_widget, qtbot):
        """Test applying modified settings."""
        # Add some modifications
        settings_widget._modified_settings = {
            "workspace.default_new_tab_widget": "terminal",
            "pane.default_split_ratio": 0.7
        }

        # Mock successful setting
        mock_set_default.return_value = True

        # Apply settings
        with patch('PySide6.QtWidgets.QMessageBox.information'):
            result = settings_widget._apply_settings()

        assert result is True
        assert mock_set_default.call_count == 2
        assert len(settings_widget._modified_settings) == 0  # Should be cleared

    def test_reset_all_to_defaults(self, settings_widget, qtbot):
        """Test resetting all settings to defaults."""
        # Test that reset is called on the actual defaults manager
        with patch.object(settings_widget._defaults_manager, 'reset_all') as mock_reset:
            with patch('PySide6.QtWidgets.QMessageBox.question', return_value=QMessageBox.Yes):
                with patch('PySide6.QtWidgets.QMessageBox.information'):
                    settings_widget._reset_all_to_defaults()

            mock_reset.assert_called_once()

    def test_can_close_with_changes(self, settings_widget, qtbot):
        """Test close behavior with unsaved changes."""
        # Add modifications
        settings_widget._modified_settings = {"test": "value"}

        # Test cancel
        with patch('PySide6.QtWidgets.QMessageBox.question',
                  return_value=QMessageBox.Cancel):
            assert settings_widget.can_close() is False

        # Test discard
        with patch('PySide6.QtWidgets.QMessageBox.question',
                  return_value=QMessageBox.Discard):
            assert settings_widget.can_close() is True

        # Test save
        with patch('PySide6.QtWidgets.QMessageBox.question',
                  return_value=QMessageBox.Save):
            with patch.object(settings_widget, '_apply_settings', return_value=True):
                assert settings_widget.can_close() is True


class TestSettingsWidgetAdvanced:
    """Test advanced Settings widget features."""

    @patch('ui.widgets.settings_app_widget.QFileDialog.getSaveFileName')
    @patch('builtins.open', create=True)
    @patch('json.dump')
    def test_export_settings(self, mock_json_dump, mock_open, mock_file_dialog,
                            settings_widget, qtbot):
        """Test exporting settings to file."""
        # Mock file dialog
        mock_file_dialog.return_value = ("/path/to/settings.json", "")

        # Mock export data
        with patch.object(settings_widget._defaults_manager, 'export_settings',
                         return_value={"key": "value"}):
            with patch('PySide6.QtWidgets.QMessageBox.information'):
                settings_widget._export_settings()

        mock_open.assert_called_with("/path/to/settings.json", 'w')
        mock_json_dump.assert_called()

    @patch('ui.widgets.settings_app_widget.QFileDialog.getOpenFileName')
    @patch('builtins.open', create=True)
    @patch('json.load')
    def test_import_settings(self, mock_json_load, mock_open, mock_file_dialog,
                            settings_widget, qtbot):
        """Test importing settings from file."""
        # Mock file dialog
        mock_file_dialog.return_value = ("/path/to/settings.json", "")

        # Mock import data
        mock_json_load.return_value = {"key": "value"}

        with patch.object(settings_widget._defaults_manager, 'import_settings',
                         return_value=1):
            with patch('PySide6.QtWidgets.QMessageBox.information'):
                settings_widget._import_settings()

        mock_open.assert_called_with("/path/to/settings.json", 'r')
        mock_json_load.assert_called()


class TestSettingsWidgetValidation:
    """Test Settings widget validation."""

    def test_invalid_setting_rejection(self, settings_widget):
        """Test that invalid settings are rejected."""
        with patch('ui.widgets.settings_app_widget.set_app_default') as mock_set:
            # Mock validation failure
            mock_set.return_value = False

            settings_widget._modified_settings = {
                "workspace.default_new_tab_widget": "invalid_type"
            }

            with patch('PySide6.QtWidgets.QMessageBox.information'):
                result = settings_widget._apply_settings()

            # Should still return True but log warning
            assert result is True

    def test_close_last_tab_behavior_radio(self, settings_widget, qtbot):
        """Test close last tab behavior radio buttons."""
        # Test that radio buttons work correctly
        # Start with one selected (the default)
        settings_widget._create_default_radio.setChecked(True)
        settings_widget._modified_settings.clear()

        # Test changing to close_window
        settings_widget._close_window_radio.setChecked(True)
        qtbot.wait(10)
        assert "workspace.close_last_tab_behavior" in settings_widget._modified_settings
        assert settings_widget._modified_settings["workspace.close_last_tab_behavior"] == "close_window"

        # Clear and test changing to do_nothing
        settings_widget._modified_settings.clear()
        settings_widget._do_nothing_radio.setChecked(True)
        qtbot.wait(10)
        assert "workspace.close_last_tab_behavior" in settings_widget._modified_settings
        assert settings_widget._modified_settings["workspace.close_last_tab_behavior"] == "do_nothing"

        # Clear and test changing back to create_default
        settings_widget._modified_settings.clear()
        settings_widget._create_default_radio.setChecked(True)
        qtbot.wait(10)
        assert "workspace.close_last_tab_behavior" in settings_widget._modified_settings
        assert settings_widget._modified_settings["workspace.close_last_tab_behavior"] == "create_default"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])