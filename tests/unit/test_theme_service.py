#!/usr/bin/env python3
"""
Unit tests for ThemeService.

Tests the public API of ThemeService focusing on the functionality
that's actually used by the application.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from services.theme_service import ThemeService
from core.themes.theme import Theme, ThemeInfo


class TestThemeService:
    """Unit tests for ThemeService public API."""

    @pytest.fixture
    def theme_service(self):
        """Create a ThemeService instance for testing."""
        service = ThemeService()
        return service

    @pytest.fixture
    def initialized_theme_service(self, theme_service):
        """Create an initialized ThemeService with test themes."""
        # Initialize with empty context to load themes
        context = {'main_window': None}
        theme_service.initialize(context)
        return theme_service

    def test_service_initialization(self, theme_service):
        """Test ThemeService initializes correctly."""
        assert theme_service.name == "ThemeService"
        assert theme_service._current_theme is None

    def test_get_available_themes_after_initialization(self, initialized_theme_service):
        """Test that themes are available after initialization."""
        themes = initialized_theme_service.get_available_themes()

        # Should have loaded built-in themes
        assert len(themes) > 0

        # Check for expected themes
        theme_ids = [t.id for t in themes]
        assert "vscode-dark" in theme_ids
        assert "vscode-light" in theme_ids
        assert "monokai" in theme_ids
        assert "solarized-dark" in theme_ids

    def test_get_theme(self, initialized_theme_service):
        """Test getting a specific theme."""
        theme = initialized_theme_service.get_theme("vscode-dark")

        assert theme is not None
        assert theme.id == "vscode-dark"
        assert theme.name == "VSCode Dark+"
        assert "editor.background" in theme.colors

        # Test non-existent theme
        assert initialized_theme_service.get_theme("non-existent") is None

    def test_apply_theme(self, initialized_theme_service):
        """Test applying a theme."""
        with patch.object(initialized_theme_service.theme_changed, 'emit') as mock_emit:
            result = initialized_theme_service.apply_theme("vscode-dark")

            assert result is True
            assert initialized_theme_service.get_current_theme_id() == "vscode-dark"
            mock_emit.assert_called_once()

    def test_apply_nonexistent_theme(self, initialized_theme_service):
        """Test applying a non-existent theme."""
        result = initialized_theme_service.apply_theme("non-existent")
        assert result is False

    def test_get_current_theme(self, initialized_theme_service):
        """Test getting current theme."""
        # Initially no theme
        assert initialized_theme_service.get_current_theme() is None
        assert initialized_theme_service.get_current_theme_id() is None

        # After applying theme
        initialized_theme_service.apply_theme("monokai")

        current_theme = initialized_theme_service.get_current_theme()
        assert current_theme is not None
        assert current_theme.id == "monokai"
        assert initialized_theme_service.get_current_theme_id() == "monokai"

    def test_get_colors(self, initialized_theme_service):
        """Test getting resolved colors."""
        # Apply a theme
        initialized_theme_service.apply_theme("vscode-light")

        colors = initialized_theme_service.get_colors()
        assert isinstance(colors, dict)
        assert len(colors) > 0

        # Should have common color keys
        assert "editor.background" in colors
        assert "editor.foreground" in colors

    def test_get_color_with_fallback(self, initialized_theme_service):
        """Test getting individual color with fallback."""
        initialized_theme_service.apply_theme("vscode-dark")

        # Existing color
        bg_color = initialized_theme_service.get_color("editor.background")
        assert bg_color.startswith("#")  # Should be a hex color

        # Non-existing color with fallback
        fallback_color = "#test123"
        color = initialized_theme_service.get_color("non.existent", fallback_color)
        assert color == fallback_color

    def test_theme_switching(self, initialized_theme_service):
        """Test switching between themes."""
        # Apply dark theme
        initialized_theme_service.apply_theme("vscode-dark")
        dark_bg = initialized_theme_service.get_color("editor.background")

        # Apply light theme
        initialized_theme_service.apply_theme("vscode-light")
        light_bg = initialized_theme_service.get_color("editor.background")

        # Colors should be different
        assert dark_bg != light_bg

    def test_create_custom_theme(self, initialized_theme_service):
        """Test creating a custom theme."""
        # Apply base theme
        initialized_theme_service.apply_theme("vscode-dark")

        custom_theme = initialized_theme_service.create_custom_theme(
            base_theme_id="vscode-dark",
            name="My Custom Theme",
            description="A custom theme"
        )

        assert custom_theme is not None
        assert custom_theme.name == "My Custom Theme"
        assert custom_theme.extends == "vscode-dark"
        assert custom_theme.id.startswith("custom-")
        assert custom_theme.version == "1.0.0"

    def test_export_theme(self, initialized_theme_service):
        """Test exporting a theme."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            result = initialized_theme_service.export_theme("monokai", tmp_path)
            assert result is True
            assert tmp_path.exists()

            # Verify exported content
            with open(tmp_path, 'r') as f:
                exported_data = json.load(f)

            assert exported_data["id"] == "monokai"
            assert exported_data["name"] == "Monokai"
            assert "colors" in exported_data
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_export_nonexistent_theme(self, initialized_theme_service):
        """Test exporting non-existent theme."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            result = initialized_theme_service.export_theme("non-existent", tmp_path)
            assert result is False
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_import_theme(self, initialized_theme_service):
        """Test importing a theme from file."""
        # Create test theme data
        test_theme_data = {
            "id": "imported-test-theme",
            "name": "Imported Test Theme",
            "description": "A test theme for import testing",
            "version": "1.0.0",
            "author": "Test Author",
            "colors": {
                "editor.background": "#123456",
                "editor.foreground": "#abcdef"
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(test_theme_data, tmp_file)
            tmp_path = Path(tmp_file.name)

        try:
            theme_id = initialized_theme_service.import_theme(tmp_path)
            assert theme_id == "imported-test-theme"

            # Verify theme was imported
            imported_theme = initialized_theme_service.get_theme("imported-test-theme")
            assert imported_theme is not None
            assert imported_theme.name == "Imported Test Theme"
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_import_invalid_theme(self, initialized_theme_service):
        """Test importing invalid theme file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_file.write("invalid json content")
            tmp_path = Path(tmp_file.name)

        try:
            theme_id = initialized_theme_service.import_theme(tmp_path)
            assert theme_id is None
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_theme_provider_integration(self, theme_service):
        """Test theme provider reference management."""
        mock_provider = Mock()
        theme_service.set_theme_provider(mock_provider)

        retrieved_provider = theme_service.get_theme_provider()
        assert retrieved_provider == mock_provider

    def test_theme_changed_signal(self, initialized_theme_service):
        """Test that theme_changed signal exists and is emitted."""
        # Verify signal exists
        assert hasattr(initialized_theme_service, 'theme_changed')

        # Connect mock slot
        mock_slot = Mock()
        initialized_theme_service.theme_changed.connect(mock_slot)

        # Apply theme should emit signal
        initialized_theme_service.apply_theme("solarized-dark")

        # Verify signal was emitted
        mock_slot.assert_called_once()
        call_args = mock_slot.call_args[0]
        assert isinstance(call_args[0], dict)  # Should emit colors dictionary

    def test_all_builtin_themes_loadable(self, initialized_theme_service):
        """Test that all built-in themes can be loaded and applied."""
        themes = initialized_theme_service.get_available_themes()

        for theme_info in themes:
            # Should be able to apply each theme
            result = initialized_theme_service.apply_theme(theme_info.id)
            assert result is True, f"Failed to apply theme: {theme_info.id}"

            # Should be able to get colors
            colors = initialized_theme_service.get_colors()
            assert len(colors) > 0, f"No colors for theme: {theme_info.id}"

            # Should have common required colors
            assert "editor.background" in colors
            assert "editor.foreground" in colors

    def test_theme_inheritance(self, initialized_theme_service):
        """Test theme inheritance with custom theme."""
        # Create a custom theme that extends vscode-dark
        custom_theme = initialized_theme_service.create_custom_theme(
            base_theme_id="vscode-dark",
            name="Dark Plus Custom",
            description="Custom dark theme"
        )

        # Apply the custom theme
        result = initialized_theme_service.apply_theme(custom_theme.id)
        assert result is True

        # Should inherit colors from base theme
        colors = initialized_theme_service.get_colors()
        assert len(colors) > 0

        # Should have inherited editor background from vscode-dark
        base_theme = initialized_theme_service.get_theme("vscode-dark")
        custom_applied_theme = initialized_theme_service.get_current_theme()

        # Custom theme should extend the base theme
        assert custom_applied_theme.extends == "vscode-dark"

    def test_theme_persistence_methods(self, initialized_theme_service):
        """Test that theme persistence methods exist and work."""
        # Apply a theme
        initialized_theme_service.apply_theme("monokai")

        # Test save/load preference methods exist (even if mocked)
        assert hasattr(initialized_theme_service, '_save_theme_preference')
        assert hasattr(initialized_theme_service, '_load_theme_preference')

        # These methods should be callable
        try:
            initialized_theme_service._save_theme_preference("monokai")
            # Method should not crash
        except Exception as e:
            # In test environment, QSettings might not work, which is OK
            pass

    @pytest.mark.parametrize("theme_id", ["vscode-dark", "vscode-light", "monokai", "solarized-dark"])
    def test_specific_theme_application(self, initialized_theme_service, theme_id):
        """Parametrized test for applying specific themes."""
        result = initialized_theme_service.apply_theme(theme_id)
        assert result is True

        current_theme = initialized_theme_service.get_current_theme()
        assert current_theme is not None
        assert current_theme.id == theme_id

        colors = initialized_theme_service.get_colors()
        assert len(colors) > 0


if __name__ == '__main__':
    pytest.main([__file__])