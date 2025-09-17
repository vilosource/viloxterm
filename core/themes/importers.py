#!/usr/bin/env python3
"""
Theme importers for various formats.

Supports importing themes from VSCode and other popular editors.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

from core.themes.theme import Theme

logger = logging.getLogger(__name__)


class VSCodeThemeImporter:
    """Import VSCode themes and convert to ViloxTerm format."""

    # Mapping from VSCode color keys to ViloxTerm keys
    VSCODE_TO_VILOX_MAP = {
        # Editor colors
        "editor.background": "editor.background",
        "editor.foreground": "editor.foreground",
        "editor.lineHighlightBackground": "editor.lineHighlightBackground",
        "editor.selectionBackground": "editor.selectionBackground",
        "editorCursor.foreground": "editorCursor.foreground",
        "editorWhitespace.foreground": "editorWhitespace.foreground",
        "editorIndentGuide.background": "editorIndentGuide.background",
        "editorIndentGuide.activeBackground": "editorIndentGuide.activeBackground",
        # Activity bar
        "activityBar.background": "activityBar.background",
        "activityBar.foreground": "activityBar.foreground",
        "activityBar.border": "activityBar.border",
        "activityBar.activeBorder": "activityBar.activeBorder",
        "activityBar.activeBackground": "activityBar.activeBackground",
        "activityBar.inactiveForeground": "activityBar.inactiveForeground",
        # Sidebar
        "sideBar.background": "sideBar.background",
        "sideBar.foreground": "sideBar.foreground",
        "sideBar.border": "sideBar.border",
        "sideBarSectionHeader.background": "sideBarSectionHeader.background",
        "sideBarSectionHeader.foreground": "sideBarSectionHeader.foreground",
        # Status bar
        "statusBar.background": "statusBar.background",
        "statusBar.foreground": "statusBar.foreground",
        "statusBar.border": "statusBar.border",
        "statusBar.noFolderBackground": "statusBar.noFolderBackground",
        "statusBar.debuggingBackground": "statusBar.debuggingBackground",
        "statusBar.debuggingForeground": "statusBar.debuggingForeground",
        # Title bar
        "titleBar.activeBackground": "titleBar.activeBackground",
        "titleBar.activeForeground": "titleBar.activeForeground",
        "titleBar.inactiveBackground": "titleBar.inactiveBackground",
        "titleBar.inactiveForeground": "titleBar.inactiveForeground",
        "titleBar.border": "titleBar.border",
        # Tabs
        "tab.activeBackground": "tab.activeBackground",
        "tab.activeForeground": "tab.activeForeground",
        "tab.activeBorder": "tab.activeBorder",
        "tab.activeBorderTop": "tab.activeBorderTop",
        "tab.inactiveBackground": "tab.inactiveBackground",
        "tab.inactiveForeground": "tab.inactiveForeground",
        "tab.border": "tab.border",
        # Panel
        "panel.background": "panel.background",
        "panel.border": "panel.border",
        "panelTitle.activeBorder": "panelTitle.activeBorder",
        "panelTitle.activeForeground": "panelTitle.activeForeground",
        "panelTitle.inactiveForeground": "panelTitle.inactiveForeground",
        # Input controls
        "input.background": "input.background",
        "input.foreground": "input.foreground",
        "input.border": "input.border",
        "input.placeholderForeground": "input.placeholderForeground",
        "focusBorder": "focusBorder",
        # Buttons
        "button.background": "button.background",
        "button.foreground": "button.foreground",
        "button.hoverBackground": "button.hoverBackground",
        "button.secondaryBackground": "button.secondaryBackground",
        "button.secondaryForeground": "button.secondaryForeground",
        "button.border": "button.border",
        # Dropdowns
        "dropdown.background": "dropdown.background",
        "dropdown.foreground": "dropdown.foreground",
        "dropdown.border": "dropdown.border",
        # Lists and trees
        "list.activeSelectionBackground": "list.activeSelectionBackground",
        "list.activeSelectionForeground": "list.activeSelectionForeground",
        "list.inactiveSelectionBackground": "list.inactiveSelectionBackground",
        "list.inactiveSelectionForeground": "list.inactiveSelectionForeground",
        "list.hoverBackground": "list.hoverBackground",
        "list.hoverForeground": "list.hoverForeground",
        # Scrollbar
        "scrollbarSlider.background": "scrollbarSlider.background",
        "scrollbarSlider.hoverBackground": "scrollbarSlider.hoverBackground",
        "scrollbarSlider.activeBackground": "scrollbarSlider.activeBackground",
        # Menu
        "menu.background": "menu.background",
        "menu.foreground": "menu.foreground",
        "menu.selectionBackground": "menu.selectionBackground",
        "menu.selectionForeground": "menu.selectionForeground",
        "menu.selectionBorder": "menu.selectionBorder",
        "menu.separatorBackground": "menu.separatorBackground",
        # Terminal colors
        "terminal.background": "terminal.background",
        "terminal.foreground": "terminal.foreground",
        "terminal.selectionBackground": "terminal.selectionBackground",
        "terminalCursor.background": "terminalCursor.background",
        "terminalCursor.foreground": "terminalCursor.foreground",
        # Terminal ANSI colors
        "terminal.ansiBlack": "terminal.ansiBlack",
        "terminal.ansiRed": "terminal.ansiRed",
        "terminal.ansiGreen": "terminal.ansiGreen",
        "terminal.ansiYellow": "terminal.ansiYellow",
        "terminal.ansiBlue": "terminal.ansiBlue",
        "terminal.ansiMagenta": "terminal.ansiMagenta",
        "terminal.ansiCyan": "terminal.ansiCyan",
        "terminal.ansiWhite": "terminal.ansiWhite",
        "terminal.ansiBrightBlack": "terminal.ansiBrightBlack",
        "terminal.ansiBrightRed": "terminal.ansiBrightRed",
        "terminal.ansiBrightGreen": "terminal.ansiBrightGreen",
        "terminal.ansiBrightYellow": "terminal.ansiBrightYellow",
        "terminal.ansiBrightBlue": "terminal.ansiBrightBlue",
        "terminal.ansiBrightMagenta": "terminal.ansiBrightMagenta",
        "terminal.ansiBrightCyan": "terminal.ansiBrightCyan",
        "terminal.ansiBrightWhite": "terminal.ansiBrightWhite",
        # Additional mappings
        "errorForeground": "errorForeground",
        "warningForeground": "warningForeground",
        "infoForeground": "infoForeground",
        "icon.foreground": "icon.foreground",
    }

    @classmethod
    def import_from_file(cls, file_path: Path) -> Optional[Theme]:
        """
        Import a VSCode theme from JSON file.

        Args:
            file_path: Path to VSCode theme JSON file

        Returns:
            Converted Theme object or None if import failed
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                vscode_data = json.load(f)

            theme_name = file_path.stem
            return cls.convert_vscode_theme(vscode_data, theme_name)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in theme file {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to import VSCode theme from {file_path}: {e}")
            return None

    @classmethod
    def convert_vscode_theme(
        cls, vscode_data: dict[str, Any], theme_name: str
    ) -> Theme:
        """
        Convert VSCode theme data to ViloxTerm Theme.

        Args:
            vscode_data: VSCode theme JSON data
            theme_name: Name for the imported theme

        Returns:
            Converted Theme object
        """
        # Extract colors from VSCode theme
        vscode_colors = vscode_data.get("colors", {})

        # Convert to ViloxTerm format
        vilox_colors = {}
        for vscode_key, vilox_key in cls.VSCODE_TO_VILOX_MAP.items():
            if vscode_key in vscode_colors:
                color_value = vscode_colors[vscode_key]
                # Handle VSCode color format (may include alpha)
                vilox_colors[vilox_key] = cls._normalize_color(color_value)

        # Handle workbench.colorCustomizations if present
        customizations = vscode_data.get("workbench.colorCustomizations", {})
        for vscode_key, vilox_key in cls.VSCODE_TO_VILOX_MAP.items():
            if vscode_key in customizations:
                color_value = customizations[vscode_key]
                vilox_colors[vilox_key] = cls._normalize_color(color_value)

        # Extract metadata
        name = vscode_data.get("name", theme_name)
        author = vscode_data.get("author", vscode_data.get("publisher", "Unknown"))
        description = vscode_data.get(
            "description", f"Imported from VSCode theme: {theme_name}"
        )

        # Create Theme object
        import uuid

        theme = Theme(
            id=f"imported-{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            version="1.0.0",
            author=author,
            colors=vilox_colors,
        )

        # Fill in missing required colors with defaults
        cls._fill_missing_colors(theme)

        logger.info(f"Successfully imported VSCode theme: {name}")
        return theme

    @classmethod
    def _normalize_color(cls, color_value: str) -> str:
        """
        Normalize color value to hex format.

        Args:
            color_value: Color value from VSCode (may include alpha)

        Returns:
            Normalized hex color string
        """
        if not isinstance(color_value, str):
            return "#000000"

        # Remove alpha channel if present (e.g., #RRGGBBAA -> #RRGGBB)
        if len(color_value) == 9 and color_value.startswith("#"):
            return color_value[:7]

        # Ensure it starts with #
        if not color_value.startswith("#"):
            return f"#{color_value}"

        return color_value

    @classmethod
    def _fill_missing_colors(cls, theme: Theme):
        """
        Fill in missing required colors with sensible defaults.

        Args:
            theme: Theme to fill missing colors for
        """
        # Required colors that must be present
        required_with_defaults = {
            "editor.background": "#1e1e1e",
            "editor.foreground": "#d4d4d4",
            "activityBar.background": "#333333",
            "activityBar.foreground": "#ffffff",
            "sideBar.background": "#252526",
            "sideBar.foreground": "#cccccc",
            "statusBar.background": "#007acc",
            "statusBar.foreground": "#ffffff",
            "terminal.background": "#1e1e1e",
            "terminal.foreground": "#d4d4d4",
            "button.background": "#0e639c",
            "button.foreground": "#ffffff",
            "input.background": "#3c3c3c",
            "input.foreground": "#cccccc",
            "input.border": "#3c3c3c",
            "list.activeSelectionBackground": "#094771",
            "list.activeSelectionForeground": "#ffffff",
            "list.hoverBackground": "#2a2d2e",
            "tab.activeBackground": "#1e1e1e",
            "tab.inactiveBackground": "#2d2d30",
            "tab.activeForeground": "#ffffff",
            "tab.inactiveForeground": "#969696",
        }

        for key, default in required_with_defaults.items():
            if key not in theme.colors:
                theme.colors[key] = default

        # Copy some colors to related properties if missing
        if "editor.lineHighlightBackground" not in theme.colors:
            bg = theme.colors.get("editor.background", "#1e1e1e")
            # Make line highlight slightly lighter/darker
            theme.colors["editor.lineHighlightBackground"] = cls._adjust_brightness(
                bg, 0.1
            )

        if "editor.selectionBackground" not in theme.colors:
            theme.colors["editor.selectionBackground"] = "#264f78"

        # Ensure all terminal ANSI colors are present
        default_ansi = {
            "terminal.ansiBlack": "#000000",
            "terminal.ansiRed": "#cd3131",
            "terminal.ansiGreen": "#0dbc79",
            "terminal.ansiYellow": "#e5e510",
            "terminal.ansiBlue": "#2472c8",
            "terminal.ansiMagenta": "#bc3fbc",
            "terminal.ansiCyan": "#11a8cd",
            "terminal.ansiWhite": "#e5e5e5",
            "terminal.ansiBrightBlack": "#666666",
            "terminal.ansiBrightRed": "#f14c4c",
            "terminal.ansiBrightGreen": "#23d18b",
            "terminal.ansiBrightYellow": "#f5f543",
            "terminal.ansiBrightBlue": "#3b8eea",
            "terminal.ansiBrightMagenta": "#d670d6",
            "terminal.ansiBrightCyan": "#29b8db",
            "terminal.ansiBrightWhite": "#e5e5e5",
        }

        for key, default in default_ansi.items():
            if key not in theme.colors:
                theme.colors[key] = default

    @staticmethod
    def _adjust_brightness(color: str, factor: float) -> str:
        """
        Adjust brightness of a color.

        Args:
            color: Hex color string
            factor: Brightness adjustment factor (positive = lighter, negative = darker)

        Returns:
            Adjusted hex color string
        """
        try:
            # Remove # and convert to RGB
            color = color.lstrip("#")
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)

            # Adjust brightness
            if factor > 0:
                # Make lighter
                r = min(255, int(r + (255 - r) * factor))
                g = min(255, int(g + (255 - g) * factor))
                b = min(255, int(b + (255 - b) * factor))
            else:
                # Make darker
                r = max(0, int(r * (1 + factor)))
                g = max(0, int(g * (1 + factor)))
                b = max(0, int(b * (1 + factor)))

            # Convert back to hex
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError, TypeError) as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Failed to adjust color brightness for '{color}': {e}")
            return color  # Return original if adjustment fails


class ThemeImporter:
    """Main theme importer supporting multiple formats."""

    @staticmethod
    def import_from_file(file_path: Path) -> Optional[Theme]:
        """
        Import a theme from file, auto-detecting format.

        Args:
            file_path: Path to theme file

        Returns:
            Imported Theme object or None if import failed
        """
        # For now, we only support VSCode format
        # In the future, we could detect format based on file structure
        return VSCodeThemeImporter.import_from_file(file_path)

    @staticmethod
    def detect_format(file_path: Path) -> str:
        """
        Detect theme file format.

        Args:
            file_path: Path to theme file

        Returns:
            Format identifier ('vscode', 'textmate', etc.)
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # Check for VSCode theme markers
            if "colors" in data or "workbench.colorCustomizations" in data:
                return "vscode"

            # Check for other formats here...

            return "unknown"
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Failed to detect theme format for '{file_path}': {e}")
            return "unknown"
