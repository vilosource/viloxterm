#!/usr/bin/env python3
"""
Unit tests for theme editor components.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from core.themes.importers import VSCodeThemeImporter
from core.themes.property_categories import ThemePropertyCategories
from core.themes.theme import Theme


class TestThemePropertyCategories:
    """Test theme property categorization."""

    def test_get_categories(self):
        """Test getting all categories."""
        categories = ThemePropertyCategories.get_categories()

        assert isinstance(categories, dict)
        assert len(categories) > 0

        # Check major categories exist
        assert "Editor" in categories
        assert "Terminal" in categories
        assert "Activity Bar" in categories
        assert "Sidebar" in categories
        assert "Status Bar" in categories

    def test_get_all_properties(self):
        """Test getting flat list of all properties."""
        properties = ThemePropertyCategories.get_all_properties()

        assert isinstance(properties, list)
        assert len(properties) > 100  # Should have 100+ properties

        # Check structure
        for prop in properties[:5]:
            assert len(prop) == 4  # (key, description, category, subcategory)
            assert isinstance(prop[0], str)  # key
            assert isinstance(prop[1], str)  # description
            assert isinstance(prop[2], str)  # category
            assert isinstance(prop[3], str)  # subcategory

    def test_get_properties_by_category(self):
        """Test getting properties for specific category."""
        # Test getting all Editor properties
        editor_props = ThemePropertyCategories.get_properties_by_category("Editor")
        assert len(editor_props) > 0

        # Test getting specific subcategory
        cursor_props = ThemePropertyCategories.get_properties_by_category(
            "Editor", "Cursor & Guides"
        )
        assert len(cursor_props) > 0
        assert len(cursor_props) < len(editor_props)

        # Test non-existent category
        empty_props = ThemePropertyCategories.get_properties_by_category("NonExistent")
        assert len(empty_props) == 0

    def test_search_properties(self):
        """Test searching properties."""
        # Search for terminal properties
        results = ThemePropertyCategories.search_properties("terminal")
        assert len(results) > 0

        for result in results:
            assert "terminal" in result[0].lower() or "terminal" in result[1].lower()

        # Search for cursor
        cursor_results = ThemePropertyCategories.search_properties("cursor")
        assert len(cursor_results) > 0

    def test_get_required_properties(self):
        """Test getting required properties."""
        required = ThemePropertyCategories.get_required_properties()

        assert isinstance(required, list)
        assert len(required) > 0

        # Check essential properties are required
        assert "editor.background" in required
        assert "editor.foreground" in required
        assert "statusBar.background" in required
        assert "statusBar.foreground" in required


class TestVSCodeThemeImporter:
    """Test VSCode theme importer."""

    def test_color_normalization(self):
        """Test color value normalization."""
        # Test with alpha channel
        assert VSCodeThemeImporter._normalize_color("#RRGGBBAA") == "#RRGGBB"

        # Test without hash
        assert VSCodeThemeImporter._normalize_color("RRGGBB") == "#RRGGBB"

        # Test already normalized
        assert VSCodeThemeImporter._normalize_color("#RRGGBB") == "#RRGGBB"

        # Test invalid input
        assert VSCodeThemeImporter._normalize_color(123) == "#000000"

    def test_adjust_brightness(self):
        """Test brightness adjustment."""
        # Test making color lighter
        lighter = VSCodeThemeImporter._adjust_brightness("#808080", 0.5)
        assert lighter != "#808080"

        # Test making color darker
        darker = VSCodeThemeImporter._adjust_brightness("#808080", -0.5)
        assert darker != "#808080"

        # Test with invalid color
        result = VSCodeThemeImporter._adjust_brightness("invalid", 0.5)
        assert result == "invalid"

    def test_vscode_to_vilox_mapping(self):
        """Test VSCode to ViloxTerm color mapping."""
        mapping = VSCodeThemeImporter.VSCODE_TO_VILOX_MAP

        # Check essential mappings exist
        assert "editor.background" in mapping
        assert "terminal.background" in mapping
        assert "activityBar.background" in mapping
        assert "sideBar.background" in mapping
        assert "statusBar.background" in mapping

        # Check terminal ANSI colors
        assert "terminal.ansiBlack" in mapping
        assert "terminal.ansiBrightWhite" in mapping

    def test_convert_vscode_theme(self):
        """Test converting VSCode theme data."""
        vscode_data = {
            "name": "Test Theme",
            "colors": {
                "editor.background": "#1e1e1e",
                "editor.foreground": "#d4d4d4",
                "terminal.background": "#000000",
                "terminal.foreground": "#ffffff"
            }
        }

        theme = VSCodeThemeImporter.convert_vscode_theme(vscode_data, "test-theme")

        assert isinstance(theme, Theme)
        assert theme.name == "Test Theme"
        assert theme.get_color("editor.background") == "#1e1e1e"
        assert theme.get_color("editor.foreground") == "#d4d4d4"

    def test_fill_missing_colors(self):
        """Test filling missing required colors."""
        theme = Theme(
            id="test",
            name="Test",
            description="Test theme",
            version="1.0.0",
            author="Test",
            colors={}
        )

        VSCodeThemeImporter._fill_missing_colors(theme)

        # Check required colors were added
        assert "editor.background" in theme.colors
        assert "editor.foreground" in theme.colors
        assert "terminal.background" in theme.colors
        assert "terminal.foreground" in theme.colors

        # Check ANSI colors were added
        assert "terminal.ansiBlack" in theme.colors
        assert "terminal.ansiBrightWhite" in theme.colors


class TestThemeEditorWidget:
    """Test theme editor widget functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, qapp):
        """Set up test environment."""
        self.qapp = qapp

    @patch('services.service_locator.ServiceLocator')
    @patch('services.theme_service.ThemeService')
    def test_widget_initialization(self, mock_theme_service, mock_locator):
        """Test theme editor widget initialization."""
        from ui.widgets.theme_editor_widget import ThemeEditorAppWidget

        # Mock theme service
        theme_service = MagicMock()
        theme_service.get_available_themes.return_value = []
        theme_service.get_current_theme.return_value = None
        mock_locator.return_value.get.return_value = theme_service

        # Create widget
        widget = ThemeEditorAppWidget(widget_id="test_editor")

        assert widget.widget_id == "test_editor"
        assert widget.get_title() == "Theme Editor"
        assert not widget._modified
        assert not widget._updating

    @patch('services.service_locator.ServiceLocator')
    @patch('services.theme_service.ThemeService')
    def test_theme_loading(self, mock_theme_service, mock_locator):
        """Test loading a theme into the editor."""
        from ui.widgets.theme_editor_widget import ThemeEditorAppWidget

        # Mock theme
        mock_theme = Mock(spec=Theme)
        mock_theme.id = "test-theme"
        mock_theme.name = "Test Theme"
        mock_theme.colors = {
            "editor.background": "#1e1e1e",
            "editor.foreground": "#d4d4d4"
        }
        mock_theme.get_color.side_effect = lambda k, d: mock_theme.colors.get(k, d)

        # Mock theme service
        theme_service = MagicMock()
        theme_service.get_available_themes.return_value = []
        theme_service.get_current_theme.return_value = mock_theme
        mock_locator.return_value.get.return_value = theme_service

        # Create widget
        widget = ThemeEditorAppWidget(widget_id="test_editor")

        # Load theme
        widget._load_theme(mock_theme)

        assert widget._current_theme == mock_theme
        assert not widget._modified

    @patch('services.service_locator.ServiceLocator')
    @patch('services.theme_service.ThemeService')
    def test_recursive_update_prevention(self, mock_theme_service, mock_locator):
        """Test that recursive updates are prevented."""
        from ui.widgets.theme_editor_widget import ThemeEditorAppWidget

        # Mock theme service
        theme_service = MagicMock()
        theme_service.get_available_themes.return_value = []
        theme_service.get_current_theme.return_value = None
        mock_locator.return_value.get.return_value = theme_service

        # Create widget
        widget = ThemeEditorAppWidget(widget_id="test_editor")

        # Set updating flag
        widget._updating = True

        # Try to trigger color change
        widget._on_color_changed("editor.background", "#ffffff", True)

        # Should not mark as modified when updating
        assert not widget._modified

    @patch('services.service_locator.ServiceLocator')
    @patch('services.theme_service.ThemeService')
    def test_get_current_colors(self, mock_theme_service, mock_locator):
        """Test getting current colors from fields."""
        from ui.widgets.theme_editor_widget import ThemeEditorAppWidget

        # Mock theme service
        theme_service = MagicMock()
        theme_service.get_available_themes.return_value = []
        theme_service.get_current_theme.return_value = None
        mock_locator.return_value.get.return_value = theme_service

        # Create widget
        widget = ThemeEditorAppWidget(widget_id="test_editor")

        # Mock color fields
        mock_field = MagicMock()
        mock_field.get_color.return_value = "#123456"
        widget._color_fields = {
            "editor.background": mock_field,
            "editor.foreground": mock_field
        }

        colors = widget._get_current_colors()

        assert colors["editor.background"] == "#123456"
        assert colors["editor.foreground"] == "#123456"


class TestColorPickerWidget:
    """Test color picker widget."""

    @pytest.fixture(autouse=True)
    def setup(self, qapp):
        """Set up test environment."""
        self.qapp = qapp

    def test_color_picker_initialization(self):
        """Test color picker widget initialization."""
        from ui.widgets.color_picker_widget import ColorPickerWidget

        picker = ColorPickerWidget(initial_color="#FF0000")

        assert picker.get_color() == "#FF0000"
        assert picker._original_color == "#FF0000"

    def test_color_picker_set_color(self):
        """Test setting color."""
        from ui.widgets.color_picker_widget import ColorPickerWidget

        picker = ColorPickerWidget(initial_color="#000000")
        picker.set_color("#FFFFFF")

        assert picker.get_color() == "#FFFFFF"
        assert picker._original_color == "#FFFFFF"

    def test_color_picker_reset(self):
        """Test resetting to original color."""
        from ui.widgets.color_picker_widget import ColorPickerWidget

        picker = ColorPickerWidget(initial_color="#FF0000")
        picker._color = "#00FF00"  # Change color internally
        picker.reset()

        assert picker.get_color() == "#FF0000"

    def test_color_picker_field(self):
        """Test color picker field with label."""
        from ui.widgets.color_picker_widget import ColorPickerField

        field = ColorPickerField(
            key="editor.background",
            label="Editor Background",
            initial_color="#1e1e1e"
        )

        assert field.get_key() == "editor.background"
        assert field.get_color() == "#1e1e1e"


class TestThemePreviewWidget:
    """Test theme preview widget."""

    @pytest.fixture(autouse=True)
    def setup(self, qapp):
        """Set up test environment."""
        self.qapp = qapp

    def test_preview_widget_initialization(self):
        """Test preview widget initialization."""
        from ui.widgets.theme_preview_widget import ThemePreviewWidget

        preview = ThemePreviewWidget()

        assert preview._current_colors == {}

    def test_apply_theme_colors(self):
        """Test applying theme colors to preview."""
        from ui.widgets.theme_preview_widget import ThemePreviewWidget

        preview = ThemePreviewWidget()

        colors = {
            "editor.background": "#1e1e1e",
            "editor.foreground": "#d4d4d4",
            "terminal.background": "#000000",
            "terminal.foreground": "#ffffff"
        }

        preview.apply_theme_colors(colors)

        assert preview.get_current_colors() == colors

    def test_stylesheet_generation(self):
        """Test stylesheet generation from colors."""
        from ui.widgets.theme_preview_widget import ThemePreviewWidget

        preview = ThemePreviewWidget()

        colors = {
            "editor.background": "#1e1e1e",
            "editor.foreground": "#d4d4d4",
            "titleBar.activeBackground": "#2d2d30",
            "titleBar.activeForeground": "#cccccc"
        }

        stylesheet = preview._generate_stylesheet(colors)

        assert "#1e1e1e" in stylesheet  # editor background
        assert "#d4d4d4" in stylesheet  # editor foreground
        assert "#2d2d30" in stylesheet  # title bar background
        assert "#cccccc" in stylesheet  # title bar foreground


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
