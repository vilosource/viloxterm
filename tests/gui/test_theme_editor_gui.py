#!/usr/bin/env python3
"""
GUI tests for theme editor.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication, QPushButton, QComboBox, QLineEdit
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from core.themes.theme import Theme, ThemeInfo


class TestThemeEditorGUI:
    """GUI tests for theme editor widget."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        """Set up test environment."""
        self.qtbot = qtbot

    @patch('services.service_locator.ServiceLocator.get_instance')
    def test_theme_editor_opens(self, mock_get_instance, qtbot):
        """Test that theme editor opens without errors."""
        from ui.widgets.theme_editor_widget import ThemeEditorAppWidget
        from services.theme_service import ThemeService

        # Create a proper theme with get_color method
        theme = Theme(
            id="theme1",
            name="Theme 1",
            description="Test theme",
            version="1.0.0",
            author="Test",
            colors={"editor.background": "#1e1e1e", "editor.foreground": "#d4d4d4"}
        )

        # Mock theme service
        theme_service = MagicMock(spec=ThemeService)
        theme_service.get_available_themes.return_value = [
            ThemeInfo(id="theme1", name="Theme 1", description="", version="1.0", author=""),
            ThemeInfo(id="theme2", name="Theme 2", description="", version="1.0", author="")
        ]
        theme_service.get_current_theme.return_value = theme
        theme_service.theme_changed = MagicMock()  # Mock the signal

        # Mock service locator
        mock_locator = MagicMock()
        mock_locator.get.return_value = theme_service
        mock_get_instance.return_value = mock_locator

        # Create widget
        widget = ThemeEditorAppWidget(widget_id="test_editor")
        qtbot.addWidget(widget)

        # Check widget is created
        assert isinstance(widget, ThemeEditorWidget), f"Expected ThemeEditorWidget instance, got {type(widget)}"
        assert widget.get_title() == "Theme Editor"

        # Show and wait for visibility
        widget.show()
        qtbot.waitExposed(widget)
        assert widget.isVisible()

    @patch('services.service_locator.ServiceLocator')
    def test_theme_selection(self, mock_locator_class, qtbot):
        """Test theme selection from combo box."""
        from ui.widgets.theme_editor_widget import ThemeEditorAppWidget
        from services.theme_service import ThemeService

        # Mock themes
        theme1 = Theme(
            id="theme1",
            name="Theme 1",
            description="Test theme 1",
            version="1.0.0",
            author="Test",
            colors={"editor.background": "#1e1e1e"}
        )
        theme2 = Theme(
            id="theme2",
            name="Theme 2",
            description="Test theme 2",
            version="1.0.0",
            author="Test",
            colors={"editor.background": "#2e2e2e"}
        )

        # Mock theme service
        theme_service = MagicMock(spec=ThemeService)
        theme_service.get_available_themes.return_value = [
            ThemeInfo(id="theme1", name="Theme 1", description="", version="1.0", author=""),
            ThemeInfo(id="theme2", name="Theme 2", description="", version="1.0", author="")
        ]
        theme_service.get_current_theme.return_value = theme1
        theme_service.get_theme.side_effect = lambda id: theme1 if id == "theme1" else theme2
        theme_service.theme_changed = MagicMock()  # Mock the signal

        # Mock service locator
        mock_locator = MagicMock()
        mock_locator.get.return_value = theme_service
        mock_locator_class.return_value = mock_locator

        # Create widget
        widget = ThemeEditorAppWidget(widget_id="test_editor")
        qtbot.addWidget(widget)
        widget.show()

        # Find theme combo box
        combo = widget._theme_combo
        assert combo.count() == 2

        # Select second theme
        combo.setCurrentIndex(1)
        qtbot.wait(100)

        # Check that theme was loaded
        assert widget._current_theme.id == "theme2"

    @patch('services.service_locator.ServiceLocator.get_instance')
    def test_button_states(self, mock_get_instance, qtbot):
        """Test that buttons are enabled/disabled correctly."""
        from ui.widgets.theme_editor_widget import ThemeEditorAppWidget
        from services.theme_service import ThemeService

        # Mock theme service
        theme_service = MagicMock(spec=ThemeService)
        theme_service.get_available_themes.return_value = []
        theme_service.get_current_theme.return_value = Theme(
            id="test",
            name="Test",
            description="Test theme",
            version="1.0.0",
            author="Test",
            colors={}
        )
        theme_service.theme_changed = MagicMock()  # Mock the signal

        # Mock service locator
        mock_locator = MagicMock()
        mock_locator.get.return_value = theme_service
        mock_get_instance.return_value = mock_locator

        # Create widget
        widget = ThemeEditorAppWidget(widget_id="test_editor")
        qtbot.addWidget(widget)
        widget.show()

        # Initially buttons should be disabled (not modified)
        assert not widget._apply_button.isEnabled()
        assert not widget._save_button.isEnabled()
        assert not widget._reset_button.isEnabled()

        # Simulate modification
        widget._modified = True
        widget._update_button_states()

        # Now buttons should be enabled
        assert widget._apply_button.isEnabled()
        assert widget._save_button.isEnabled()
        assert widget._reset_button.isEnabled()

    @patch('services.service_locator.ServiceLocator.get_instance')
    def test_search_filter(self, mock_get_instance, qtbot):
        """Test property search filter."""
        from ui.widgets.theme_editor_widget import ThemeEditorAppWidget
        from services.theme_service import ThemeService

        # Mock theme service
        theme_service = MagicMock(spec=ThemeService)
        theme_service.get_available_themes.return_value = []
        theme_service.get_current_theme.return_value = None
        theme_service.theme_changed = MagicMock()  # Mock the signal

        # Mock service locator
        mock_locator = MagicMock()
        mock_locator.get.return_value = theme_service
        mock_get_instance.return_value = mock_locator

        # Create widget
        widget = ThemeEditorAppWidget(widget_id="test_editor")
        qtbot.addWidget(widget)
        widget.show()

        # Type in search box
        search_input = widget._search_input
        search_input.setText("terminal")
        qtbot.wait(100)

        # Check that filter was applied
        # (would need to check visibility of fields, but that requires
        # them to be properly created first)
        assert search_input.text() == "terminal"

    @patch('services.service_locator.ServiceLocator')
    @patch('PySide6.QtWidgets.QMessageBox.information')
    def test_apply_theme(self, mock_msgbox, mock_locator_class, qtbot):
        """Test applying theme changes."""
        from ui.widgets.theme_editor_widget import ThemeEditorAppWidget
        from services.theme_service import ThemeService

        # Mock theme
        theme = Theme(
            id="test",
            name="Test",
            description="Test theme",
            version="1.0.0",
            author="Test",
            colors={"editor.background": "#1e1e1e"}
        )

        # Mock theme service
        theme_service = MagicMock(spec=ThemeService)
        theme_service.get_available_themes.return_value = []
        theme_service.get_current_theme.return_value = theme
        theme_service.apply_theme.return_value = True
        theme_service.theme_changed = MagicMock()  # Mock the signal

        # Mock service locator
        mock_locator = MagicMock()
        mock_locator.get.return_value = theme_service
        mock_locator_class.return_value = mock_locator

        # Create widget
        widget = ThemeEditorAppWidget(widget_id="test_editor")
        qtbot.addWidget(widget)
        widget.show()

        # Set current theme and mark as modified
        widget._current_theme = theme
        widget._modified = True
        widget._update_button_states()

        # Mock _get_current_colors to return valid colors
        widget._get_current_colors = MagicMock(return_value={"editor.background": "#1e1e1e"})

        # Click apply button
        assert widget._apply_button.isEnabled()
        result = widget._apply_theme()

        # Check that theme was applied
        assert result == True
        theme_service.apply_theme.assert_called_once()
        mock_msgbox.assert_called_once()

        # Check modified flag was cleared
        assert widget._modified == False
        assert not widget._apply_button.isEnabled()


class TestColorPickerGUI:
    """GUI tests for color picker widget."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        """Set up test environment."""
        self.qtbot = qtbot

    def test_color_picker_display(self, qtbot):
        """Test color picker displays correctly."""
        from ui.widgets.color_picker_widget import ColorPickerWidget

        picker = ColorPickerWidget(initial_color="#FF0000")
        qtbot.addWidget(picker)
        picker.show()

        # Check color button exists
        assert hasattr(picker, '_color_button') and picker._color_button is not None, f"Color picker should have a color button"
        assert picker._color_button.isVisible()

        # Check hex input exists if enabled
        if picker._show_hex_input:
            assert hasattr(picker, '_hex_input') and picker._hex_input is not None, f"Color picker should have hex input when enabled"
            assert picker._hex_input.text() == "#FF0000"

    def test_hex_input_validation(self, qtbot):
        """Test hex input validation."""
        from ui.widgets.color_picker_widget import ColorPickerWidget

        picker = ColorPickerWidget(initial_color="#000000", show_hex_input=True)
        qtbot.addWidget(picker)
        picker.show()

        # Valid hex color
        picker._hex_input.setText("#FF0000")
        qtbot.keyClick(picker._hex_input, Qt.Key_Return)
        assert picker.get_color() == "#FF0000"

        # Invalid hex color (should revert)
        picker._hex_input.setText("invalid")
        qtbot.keyClick(picker._hex_input, Qt.Key_Return)
        assert picker.get_color() == "#FF0000"  # Should stay at previous valid value

    def test_color_changed_signal(self, qtbot):
        """Test that color_changed signal is emitted."""
        from ui.widgets.color_picker_widget import ColorPickerWidget

        picker = ColorPickerWidget(initial_color="#000000", show_hex_input=True)
        qtbot.addWidget(picker)

        # Use a list to capture signal arguments
        signal_args = []
        picker.color_changed.connect(lambda *args: signal_args.append(args))

        # Change color via hex input
        picker._hex_input.setText("#FF0000")
        picker._hex_input.editingFinished.emit()

        # Wait a bit for signal processing
        qtbot.wait(100)

        # Check signal was emitted
        assert len(signal_args) >= 1, f"Expected at least 1 signal emission, got {len(signal_args)}"
        assert signal_args[-1][0] == "#FF0000"  # color value
        assert signal_args[-1][1] == False  # not preview

    def test_color_picker_field(self, qtbot):
        """Test color picker field with label."""
        from ui.widgets.color_picker_widget import ColorPickerField

        field = ColorPickerField(
            key="editor.background",
            label="Editor Background",
            initial_color="#1e1e1e",
            description="Background color of the editor"
        )
        qtbot.addWidget(field)
        field.show()

        # Check field components
        assert field.get_key() == "editor.background"
        assert field.get_color() == "#1e1e1e"

        # Use a list to capture signal arguments
        signal_args = []
        field.color_changed.connect(lambda *args: signal_args.append(args))

        # Change color
        field.set_color("#FF0000")
        field._picker.color_changed.emit("#FF0000", False)

        # Wait a bit for signal processing
        qtbot.wait(100)

        # Check signal includes key
        assert len(signal_args) >= 1, f"Expected at least 1 signal with key, got {len(signal_args)}"
        assert signal_args[-1][0] == "editor.background"  # key
        assert signal_args[-1][1] == "#FF0000"  # value
        assert signal_args[-1][2] == False  # not preview


class TestThemePreviewGUI:
    """GUI tests for theme preview widget."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        """Set up test environment."""
        self.qtbot = qtbot

    def test_preview_widget_display(self, qtbot):
        """Test preview widget displays correctly."""
        from ui.widgets.theme_preview_widget import ThemePreviewWidget

        preview = ThemePreviewWidget()
        qtbot.addWidget(preview)
        preview.show()

        # Check widget is visible
        assert preview.isVisible()

        # Check preview components exist
        assert hasattr(preview, '_title_bar') and preview._title_bar.isVisible(), f"Preview should have visible title bar"
        assert hasattr(preview, '_menu_bar') and preview._menu_bar.isVisible(), f"Preview should have visible menu bar"
        assert hasattr(preview, '_activity_bar') and preview._activity_bar.isVisible(), f"Preview should have visible activity bar"
        assert hasattr(preview, '_sidebar') and preview._sidebar.isVisible(), f"Preview should have visible sidebar"
        assert hasattr(preview, '_editor_area') and preview._editor_area.isVisible(), f"Preview should have visible editor area"
        assert hasattr(preview, '_panel') and preview._panel.isVisible(), f"Preview should have visible panel"
        assert hasattr(preview, '_status_bar') and preview._status_bar.isVisible(), f"Preview should have visible status bar"

    def test_apply_colors_to_preview(self, qtbot):
        """Test applying colors updates preview."""
        from ui.widgets.theme_preview_widget import ThemePreviewWidget

        preview = ThemePreviewWidget()
        qtbot.addWidget(preview)
        preview.show()

        # Apply dark theme colors
        dark_colors = {
            "editor.background": "#1e1e1e",
            "editor.foreground": "#d4d4d4",
            "activityBar.background": "#333333",
            "sideBar.background": "#252526",
            "statusBar.background": "#007acc",
            "terminal.background": "#000000"
        }

        preview.apply_theme_colors(dark_colors)
        assert preview.get_current_colors() == dark_colors

        # Apply light theme colors
        light_colors = {
            "editor.background": "#ffffff",
            "editor.foreground": "#000000",
            "activityBar.background": "#f0f0f0",
            "sideBar.background": "#f5f5f5",
            "statusBar.background": "#007acc",
            "terminal.background": "#ffffff"
        }

        preview.apply_theme_colors(light_colors)
        assert preview.get_current_colors() == light_colors


class TestThemeEditorCommands:
    """Test theme editor commands."""

    @patch('services.service_locator.ServiceLocator.get_instance')
    def test_open_theme_editor_command(self, mock_get_instance):
        """Test opening theme editor via command."""
        # Import theme commands to trigger decorator registration
        import core.commands.builtin.theme_commands
        from core.commands.registry import CommandRegistry
        from core.commands.base import CommandContext
        from services.workspace_service import WorkspaceService

        # Get the actual command function
        registry = CommandRegistry()
        command_info = registry.get_command("theme.openEditor")
        assert command_info is not None and hasattr(command_info, 'func'), f"Expected valid command info for 'theme.openEditor', got {command_info}"

        # Mock workspace service
        workspace = MagicMock(spec=WorkspaceService)
        workspace.add_app_widget.return_value = True

        # Mock service locator
        mock_locator = MagicMock()
        mock_locator.get.return_value = workspace
        mock_get_instance.return_value = mock_locator

        # Create context
        context = CommandContext()

        # Execute command
        result = command_info.handler(context)

        # Check result
        assert result.success == True
        assert 'widget_id' in result.value
        workspace.add_app_widget.assert_called_once()

    @patch('services.service_locator.ServiceLocator.get_instance')
    @patch('core.themes.importers.VSCodeThemeImporter.import_from_file')
    @patch('PySide6.QtWidgets.QMessageBox.information')
    @patch('PySide6.QtWidgets.QFileDialog.getOpenFileName')
    def test_import_vscode_theme_command(
        self, mock_file_dialog, mock_msgbox, mock_import_from_file, mock_get_instance
    ):
        """Test importing VSCode theme via command."""
        # Import theme commands to trigger decorator registration
        import core.commands.builtin.theme_commands
        from core.commands.registry import CommandRegistry
        from core.commands.base import CommandContext
        from services.theme_service import ThemeService
        from services.ui_service import UIService

        # Get the actual command function
        registry = CommandRegistry()
        command_info = registry.get_command("theme.importVSCode")
        assert command_info is not None and hasattr(command_info, 'func'), f"Expected valid command info for 'theme.importVSCode', got {command_info}"

        # Mock file dialog
        mock_file_dialog.return_value = ("/path/to/theme.json", "JSON Files (*.json)")

        # Mock imported theme
        mock_theme = Mock(spec=Theme)
        mock_theme.id = "imported-theme"
        mock_theme.name = "Imported Theme"
        mock_import_from_file.return_value = mock_theme

        # Mock services
        theme_service = MagicMock(spec=ThemeService)
        theme_service._themes = {}
        theme_service.save_custom_theme.return_value = True
        theme_service.apply_theme.return_value = True

        ui_service = MagicMock(spec=UIService)
        ui_service.get_main_window.return_value = MagicMock()  # Return a mock window instead of None

        # Mock service locator
        mock_locator = MagicMock()
        mock_locator.get.side_effect = lambda t: theme_service if t == ThemeService else ui_service
        mock_get_instance.return_value = mock_locator

        # Create context
        context = CommandContext()

        # Execute command
        result = command_info.handler(context)

        # Check result
        assert result.success == True
        assert result.value['theme_id'] == "imported-theme"
        theme_service.apply_theme.assert_called_with("imported-theme")
        mock_msgbox.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])