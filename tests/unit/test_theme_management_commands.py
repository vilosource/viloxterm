#!/usr/bin/env python3
"""
Unit tests for theme management commands.

Tests that theme commands properly manage themes through the service layer.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.commands.base import CommandContext
from core.commands.builtin.theme_management_commands import (
    apply_theme_command,
    apply_theme_preview_command,
    apply_typography_preset_command,
    create_custom_theme_command,
    delete_custom_theme_command,
    export_theme_command,
    get_available_themes_command,
    get_current_theme_command,
    get_theme_command,
    get_typography_command,
    import_theme_command,
    save_custom_theme_command,
    update_theme_colors_command,
)
from core.themes.typography import ThemeTypography
from services.theme_service import Theme, ThemeService


class TestThemeManagementCommands:
    """Test suite for theme management commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_theme_service = MagicMock(spec=ThemeService)
        self.mock_context = MagicMock(spec=CommandContext)
        self.mock_context.get_service.return_value = self.mock_theme_service

        # Create sample themes
        self.sample_theme = Theme(
            id="test-theme",
            name="Test Theme",
            description="Test theme",
            colors={"background": "#000000"},
            version="1.0.0",
            author="Test Author"
        )
        self.sample_theme.is_custom = True  # Set as attribute

        self.builtin_theme = Theme(
            id="vscode-dark",
            name="VSCode Dark",
            description="Built-in theme",
            colors={"background": "#1e1e1e"},
            version="1.0.0",
            author="Microsoft"
        )
        self.builtin_theme.is_custom = False  # Set as attribute

    def test_get_available_themes(self):
        """Test getting available themes."""
        themes = [self.builtin_theme, self.sample_theme]
        self.mock_theme_service.get_available_themes.return_value = themes

        result = get_available_themes_command._original_func(self.mock_context)

        assert result.success
        assert result.value["themes"] == themes
        self.mock_theme_service.get_available_themes.assert_called_once()

    def test_get_current_theme(self):
        """Test getting current theme."""
        self.mock_theme_service.get_current_theme.return_value = self.sample_theme

        result = get_current_theme_command._original_func(self.mock_context)

        assert result.success
        assert result.value["theme"] == self.sample_theme
        self.mock_theme_service.get_current_theme.assert_called_once()

    def test_get_theme_by_id(self):
        """Test getting a specific theme by ID."""
        self.mock_theme_service.get_theme.return_value = self.sample_theme

        result = get_theme_command._original_func(
            self.mock_context,
            theme_id="test-theme"
        )

        assert result.success
        assert result.value["theme"] == self.sample_theme
        self.mock_theme_service.get_theme.assert_called_once_with("test-theme")

    def test_get_theme_not_found(self):
        """Test getting a theme that doesn't exist."""
        self.mock_theme_service.get_theme.return_value = None

        result = get_theme_command._original_func(
            self.mock_context,
            theme_id="nonexistent"
        )

        assert not result.success
        assert "not found" in result.error

    def test_apply_theme(self):
        """Test applying a theme."""
        result = apply_theme_command._original_func(
            self.mock_context,
            theme_id="test-theme"
        )

        assert result.success
        assert result.value["theme_id"] == "test-theme"
        self.mock_theme_service.apply_theme.assert_called_once_with("test-theme")

    def test_save_custom_theme(self):
        """Test saving a custom theme."""
        theme_data = self.sample_theme.to_dict()
        self.mock_theme_service.save_custom_theme.return_value = True

        with patch('core.commands.builtin.theme_management_commands.Theme') as MockTheme:
            MockTheme.from_dict.return_value = self.sample_theme

            result = save_custom_theme_command._original_func(
                self.mock_context,
                theme_data=theme_data
            )

            assert result.success
            assert result.value["theme_id"] == "test-theme"
            MockTheme.from_dict.assert_called_once_with(theme_data)
            self.mock_theme_service.save_custom_theme.assert_called_once_with(self.sample_theme)

    def test_save_custom_theme_failure(self):
        """Test saving a custom theme when save fails."""
        theme_data = self.sample_theme.to_dict()
        self.mock_theme_service.save_custom_theme.return_value = False

        with patch('core.commands.builtin.theme_management_commands.Theme') as MockTheme:
            MockTheme.from_dict.return_value = self.sample_theme

            result = save_custom_theme_command._original_func(
                self.mock_context,
                theme_data=theme_data
            )

            assert not result.success
            assert "Failed to save" in result.error

    def test_create_custom_theme(self):
        """Test creating a custom theme."""
        self.mock_theme_service.create_custom_theme.return_value = self.sample_theme

        result = create_custom_theme_command._original_func(
            self.mock_context,
            base_theme_id="vscode-dark",
            name="My Theme",
            description="Custom theme"
        )

        assert result.success
        assert result.value["theme"] == self.sample_theme
        self.mock_theme_service.create_custom_theme.assert_called_once_with(
            "vscode-dark",
            "My Theme",
            "Custom theme"
        )

    def test_delete_custom_theme(self):
        """Test deleting a custom theme."""
        self.mock_theme_service.delete_custom_theme.return_value = True

        result = delete_custom_theme_command._original_func(
            self.mock_context,
            theme_id="test-theme"
        )

        assert result.success
        assert result.value["theme_id"] == "test-theme"
        self.mock_theme_service.delete_custom_theme.assert_called_once_with("test-theme")

    def test_delete_custom_theme_failure(self):
        """Test deleting a theme that can't be deleted."""
        self.mock_theme_service.delete_custom_theme.return_value = False

        result = delete_custom_theme_command._original_func(
            self.mock_context,
            theme_id="vscode-dark"
        )

        assert not result.success
        assert "Failed to delete" in result.error

    def test_import_theme(self):
        """Test importing a theme from file."""
        self.mock_theme_service.import_theme.return_value = "imported-theme"

        result = import_theme_command._original_func(
            self.mock_context,
            file_path="/path/to/theme.json"
        )

        assert result.success
        assert result.value["theme_id"] == "imported-theme"
        self.mock_theme_service.import_theme.assert_called_once_with(Path("/path/to/theme.json"))

    def test_export_theme(self):
        """Test exporting a theme to file."""
        self.mock_theme_service.export_theme.return_value = True

        result = export_theme_command._original_func(
            self.mock_context,
            theme_id="test-theme",
            file_path="/path/to/export.json"
        )

        assert result.success
        assert result.value["theme_id"] == "test-theme"
        assert result.value["file_path"] == "/path/to/export.json"
        self.mock_theme_service.export_theme.assert_called_once_with(
            "test-theme",
            Path("/path/to/export.json")
        )

    def test_apply_typography_preset(self):
        """Test applying a typography preset."""
        result = apply_typography_preset_command._original_func(
            self.mock_context,
            preset="compact"
        )

        assert result.success
        assert result.value["preset"] == "compact"
        self.mock_theme_service.apply_typography_preset.assert_called_once_with("compact")

    def test_get_typography(self):
        """Test getting typography settings."""
        typography = ThemeTypography(
            font_family="monospace",
            font_size_base=14,
            line_height=1.5
        )
        self.mock_theme_service.get_typography.return_value = typography

        result = get_typography_command._original_func(self.mock_context)

        assert result.success
        assert result.value["typography"] == typography
        self.mock_theme_service.get_typography.assert_called_once()

    def test_apply_theme_preview(self):
        """Test applying a theme preview."""
        colors = {"background": "#ffffff"}
        typography = {"font_size_base": 16}

        result = apply_theme_preview_command._original_func(
            self.mock_context,
            colors=colors,
            typography=typography
        )

        assert result.success
        assert result.value["preview_applied"] is True
        self.mock_theme_service.apply_theme_preview.assert_called_once_with(colors, typography)

    def test_update_theme_colors(self):
        """Test updating theme colors."""
        self.mock_theme_service.get_theme.return_value = self.sample_theme
        self.mock_theme_service.save_custom_theme.return_value = True

        colors = {"background": "#ffffff", "foreground": "#000000"}

        result = update_theme_colors_command._original_func(
            self.mock_context,
            theme_id="test-theme",
            colors=colors
        )

        assert result.success
        assert result.value["theme_id"] == "test-theme"
        assert result.value["updated_colors"] == 2
        assert self.sample_theme.colors["background"] == "#ffffff"
        assert self.sample_theme.colors["foreground"] == "#000000"

    def test_update_theme_colors_not_found(self):
        """Test updating colors for non-existent theme."""
        self.mock_theme_service.get_theme.return_value = None

        result = update_theme_colors_command._original_func(
            self.mock_context,
            theme_id="nonexistent",
            colors={"background": "#ffffff"}
        )

        assert not result.success
        assert "not found" in result.error

    def test_no_service_available(self):
        """Test handling when theme service is not available."""
        self.mock_context.get_service.return_value = None

        # Test each command
        result = get_available_themes_command._original_func(self.mock_context)
        assert not result.success
        assert "ThemeService not available" in result.error

        result = apply_theme_command._original_func(self.mock_context, theme_id="test")
        assert not result.success
        assert "ThemeService not available" in result.error

    def test_exception_handling(self):
        """Test that commands handle exceptions gracefully."""
        self.mock_theme_service.apply_theme.side_effect = Exception("Test error")

        result = apply_theme_command._original_func(
            self.mock_context,
            theme_id="test-theme"
        )

        assert not result.success
        assert "Test error" in result.error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
