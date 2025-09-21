#!/usr/bin/env python3
"""
Extended theme management commands for proper architectural flow.

These commands ensure theme operations go through the command pattern:
User Action → Command → Service → UI Update
"""

import logging
from pathlib import Path
from typing import Any, Optional

from viloapp.core.commands.base import CommandContext, CommandResult
from viloapp.core.commands.decorators import command
from viloapp.services.theme_service import ThemeService

logger = logging.getLogger(__name__)


@command(
    id="theme.getAvailableThemes",
    title="Get Available Themes",
    category="Theme",
    description="Get list of all available themes",
)
def get_available_themes_command(context: CommandContext) -> CommandResult:
    """Get all available themes."""
    theme_service = context.get_service(ThemeService)
    if not theme_service:
        return CommandResult(success=False, error="ThemeService not available")

    try:
        themes = theme_service.get_available_themes()
        return CommandResult(success=True, value={"themes": themes})
    except Exception as e:
        logger.error(f"Failed to get available themes: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="theme.getCurrentTheme",
    title="Get Current Theme",
    category="Theme",
    description="Get the currently active theme",
)
def get_current_theme_command(context: CommandContext) -> CommandResult:
    """Get the current theme."""
    theme_service = context.get_service(ThemeService)
    if not theme_service:
        return CommandResult(success=False, error="ThemeService not available")

    try:
        theme = theme_service.get_current_theme()
        return CommandResult(success=True, value={"theme": theme})
    except Exception as e:
        logger.error(f"Failed to get current theme: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="theme.getTheme",
    title="Get Theme by ID",
    category="Theme",
    description="Get a specific theme by its ID",
    visible=False,  # Internal command, not for command palette
)
def get_theme_command(context: CommandContext, theme_id: str) -> CommandResult:
    """Get a specific theme."""
    theme_service = context.get_service(ThemeService)
    if not theme_service:
        return CommandResult(success=False, error="ThemeService not available")

    try:
        theme = theme_service.get_theme(theme_id)
        if theme:
            return CommandResult(success=True, value={"theme": theme})
        else:
            return CommandResult(success=False, error=f"Theme {theme_id} not found")
    except Exception as e:
        logger.error(f"Failed to get theme {theme_id}: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="theme.applyTheme",
    title="Apply Theme",
    category="Theme",
    description="Apply a theme by its ID",
    visible=False,  # Internal command, requires theme_id parameter
)
def apply_theme_command(context: CommandContext, theme_id: str) -> CommandResult:
    """Apply a theme."""
    theme_service = context.get_service(ThemeService)
    if not theme_service:
        return CommandResult(success=False, error="ThemeService not available")

    try:
        theme_service.apply_theme(theme_id)
        return CommandResult(success=True, value={"theme_id": theme_id})
    except Exception as e:
        logger.error(f"Failed to apply theme {theme_id}: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="theme.saveCustomTheme",
    title="Save Custom Theme",
    category="Theme",
    description="Save a custom theme",
    visible=False,  # Internal command, requires theme_data parameter
)
def save_custom_theme_command(
    context: CommandContext, theme_data: dict[str, Any]
) -> CommandResult:
    """Save a custom theme."""
    theme_service = context.get_service(ThemeService)
    if not theme_service:
        return CommandResult(success=False, error="ThemeService not available")

    try:
        # Create theme object from data
        from viloapp.services.theme_service import Theme

        theme = Theme.from_dict(theme_data)

        success = theme_service.save_custom_theme(theme)
        if success:
            return CommandResult(success=True, value={"theme_id": theme.id})
        else:
            return CommandResult(success=False, error="Failed to save custom theme")
    except Exception as e:
        logger.error(f"Failed to save custom theme: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="theme.createCustomTheme",
    title="Create Custom Theme",
    category="Theme",
    description="Create a new custom theme based on an existing theme",
    visible=False,  # Internal command, requires multiple parameters
)
def create_custom_theme_command(
    context: CommandContext,
    base_theme_id: str,
    name: str,
    description: Optional[str] = None,
) -> CommandResult:
    """Create a new custom theme."""
    theme_service = context.get_service(ThemeService)
    if not theme_service:
        return CommandResult(success=False, error="ThemeService not available")

    try:
        new_theme = theme_service.create_custom_theme(base_theme_id, name, description)
        if new_theme:
            return CommandResult(success=True, value={"theme": new_theme})
        else:
            return CommandResult(success=False, error="Failed to create custom theme")
    except Exception as e:
        logger.error(f"Failed to create custom theme: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="theme.deleteCustomTheme",
    title="Delete Custom Theme",
    category="Theme",
    description="Delete a custom theme",
    visible=False,  # Internal command, requires theme_id parameter
)
def delete_custom_theme_command(
    context: CommandContext, theme_id: str
) -> CommandResult:
    """Delete a custom theme."""
    theme_service = context.get_service(ThemeService)
    if not theme_service:
        return CommandResult(success=False, error="ThemeService not available")

    try:
        success = theme_service.delete_custom_theme(theme_id)
        if success:
            return CommandResult(success=True, value={"theme_id": theme_id})
        else:
            return CommandResult(
                success=False, error=f"Failed to delete theme {theme_id}"
            )
    except Exception as e:
        logger.error(f"Failed to delete custom theme {theme_id}: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="theme.importTheme",
    title="Import Theme",
    category="Theme",
    description="Import a theme from a file",
    visible=False,  # Internal command, requires file_path parameter
)
def import_theme_command(context: CommandContext, file_path: str) -> CommandResult:
    """Import a theme from a file."""
    theme_service = context.get_service(ThemeService)
    if not theme_service:
        return CommandResult(success=False, error="ThemeService not available")

    try:
        theme_id = theme_service.import_theme(Path(file_path))
        if theme_id:
            return CommandResult(success=True, value={"theme_id": theme_id})
        else:
            return CommandResult(success=False, error="Failed to import theme")
    except Exception as e:
        logger.error(f"Failed to import theme from {file_path}: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="theme.exportTheme",
    title="Export Theme",
    category="Theme",
    description="Export a theme to a file",
    visible=False,  # Internal command, requires parameters
)
def export_theme_command(
    context: CommandContext, theme_id: str, file_path: str
) -> CommandResult:
    """Export a theme to a file."""
    theme_service = context.get_service(ThemeService)
    if not theme_service:
        return CommandResult(success=False, error="ThemeService not available")

    try:
        success = theme_service.export_theme(theme_id, Path(file_path))
        if success:
            return CommandResult(
                success=True, value={"theme_id": theme_id, "file_path": file_path}
            )
        else:
            return CommandResult(
                success=False, error=f"Failed to export theme {theme_id}"
            )
    except Exception as e:
        logger.error(f"Failed to export theme {theme_id} to {file_path}: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="theme.applyTypographyPreset",
    title="Apply Typography Preset",
    category="Theme",
    description="Apply a typography preset",
    visible=False,  # Internal command, requires preset parameter
)
def apply_typography_preset_command(
    context: CommandContext, preset: str
) -> CommandResult:
    """Apply a typography preset."""
    theme_service = context.get_service(ThemeService)
    if not theme_service:
        return CommandResult(success=False, error="ThemeService not available")

    try:
        theme_service.apply_typography_preset(preset)
        return CommandResult(success=True, value={"preset": preset})
    except Exception as e:
        logger.error(f"Failed to apply typography preset {preset}: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="theme.getTypography",
    title="Get Typography Settings",
    category="Theme",
    description="Get current typography settings",
)
def get_typography_command(context: CommandContext) -> CommandResult:
    """Get typography settings."""
    theme_service = context.get_service(ThemeService)
    if not theme_service:
        return CommandResult(success=False, error="ThemeService not available")

    try:
        typography = theme_service.get_typography()
        return CommandResult(success=True, value={"typography": typography})
    except Exception as e:
        logger.error(f"Failed to get typography: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="theme.applyThemePreview",
    title="Apply Theme Preview",
    category="Theme",
    description="Apply a temporary theme preview",
    visible=False,  # Internal command, requires colors parameter
)
def apply_theme_preview_command(
    context: CommandContext,
    colors: dict[str, str],
    typography: Optional[dict[str, Any]] = None,
) -> CommandResult:
    """Apply a theme preview."""
    theme_service = context.get_service(ThemeService)
    if not theme_service:
        return CommandResult(success=False, error="ThemeService not available")

    try:
        theme_service.apply_theme_preview(colors, typography)
        return CommandResult(success=True, value={"preview_applied": True})
    except Exception as e:
        logger.error(f"Failed to apply theme preview: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="theme.getCurrentColors",
    title="Get Current Theme Colors",
    category="Theme",
    description="Get the current theme's color palette",
)
def get_current_colors_command(context: CommandContext) -> CommandResult:
    """Get current theme colors."""
    theme_service = context.get_service(ThemeService)
    if not theme_service:
        return CommandResult(success=False, error="ThemeService not available")

    try:
        theme = theme_service.get_current_theme()
        if theme and hasattr(theme, "colors"):
            colors = theme.colors
        else:
            # Fallback colors
            colors = {
                "editor.background": "#252526",
                "editor.foreground": "#cccccc",
                "panel.background": "#252526",
                "statusBar.background": "#007ACC",
                "statusBar.foreground": "#ffffff",
                "list.hoverBackground": "#2a2d2e",
                "activityBar.activeBorder": "#007ACC",
                "widget.border": "#3e3e42",
                "tab.inactiveForeground": "#969696",
            }

        return CommandResult(success=True, value=colors)
    except Exception as e:
        logger.error(f"Failed to get current colors: {e}")
        # Return fallback colors
        fallback_colors = {
            "editor.background": "#252526",
            "editor.foreground": "#cccccc",
            "panel.background": "#252526",
            "statusBar.background": "#007ACC",
            "statusBar.foreground": "#ffffff",
            "list.hoverBackground": "#2a2d2e",
            "activityBar.activeBorder": "#007ACC",
            "widget.border": "#3e3e42",
            "tab.inactiveForeground": "#969696",
        }
        return CommandResult(success=True, value=fallback_colors)


@command(
    id="theme.updateThemeColors",
    title="Update Theme Colors",
    category="Theme",
    description="Update colors in the current theme",
    visible=False,  # Internal command, requires multiple parameters
)
def update_theme_colors_command(
    context: CommandContext, theme_id: str, colors: dict[str, str]
) -> CommandResult:
    """Update theme colors."""
    theme_service = context.get_service(ThemeService)
    if not theme_service:
        return CommandResult(success=False, error="ThemeService not available")

    try:
        theme = theme_service.get_theme(theme_id)
        if not theme:
            return CommandResult(success=False, error=f"Theme {theme_id} not found")

        # Update theme colors
        theme.colors.update(colors)

        # Save if it's a custom theme
        if theme.is_custom:
            success = theme_service.save_custom_theme(theme)
            if not success:
                return CommandResult(
                    success=False, error="Failed to save theme changes"
                )

        return CommandResult(
            success=True, value={"theme_id": theme_id, "updated_colors": len(colors)}
        )
    except Exception as e:
        logger.error(f"Failed to update theme colors: {e}")
        return CommandResult(success=False, error=str(e))
