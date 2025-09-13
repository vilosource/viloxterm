#!/usr/bin/env python3
"""
Theme-related commands for ViloxTerm.
"""

from core.commands.base import CommandContext, CommandResult
from core.commands.decorators import command
from services.theme_service import ThemeService
from services.ui_service import UIService
from ui.themes.theme_provider import ThemeProvider
import logging

logger = logging.getLogger(__name__)

# Register theme editor widget factory when module is imported
try:
    from ui.widgets.theme_editor_widget import ThemeEditorAppWidget
    from ui.widgets.widget_registry import widget_registry, WidgetType, WidgetConfig

    def create_theme_editor_widget(widget_id: str) -> ThemeEditorAppWidget:
        return ThemeEditorAppWidget(widget_id)

    # Register the factory under CUSTOM type
    widget_registry.register_factory(WidgetType.CUSTOM, create_theme_editor_widget)

    # Also register a config for CUSTOM type if not already present
    if not widget_registry.get_config(WidgetType.CUSTOM):
        config = WidgetConfig(
            widget_class=None,  # Will use factory
            factory=create_theme_editor_widget,
            show_header=True,
            allow_type_change=False,
            default_content=""
        )
        widget_registry.register_widget_type(WidgetType.CUSTOM, config)

    logger.debug("Registered theme editor widget factory")
except ImportError as e:
    logger.error(f"Failed to register theme editor widget: {e}")


@command(
    id="theme.selectTheme",
    title="Select Color Theme",
    category="Preferences",
    description="Change the application color theme",
    shortcut="ctrl+k ctrl+t"
)
def select_theme_command(context: CommandContext, theme_id: str = None) -> CommandResult:
    """
    Select and apply a theme.

    Args:
        context: Command context
        theme_id: Optional theme ID to apply directly

    Returns:
        CommandResult indicating success or failure
    """
    try:
        theme_service = context.get_service(ThemeService)
        if not theme_service:
            return CommandResult(success=False, error="ThemeService not available")

        if theme_id:
            # Direct theme selection
            success = theme_service.apply_theme(theme_id)
            if success:
                logger.info(f"Applied theme: {theme_id}")
                return CommandResult(success=True, value={'theme_id': theme_id})
            else:
                return CommandResult(success=False, error=f"Failed to apply theme: {theme_id}")
        else:
            # Cycle through available themes (for now)
            themes = theme_service.get_available_themes()
            if not themes:
                return CommandResult(success=False, error="No themes available")

            current_id = theme_service.get_current_theme_id()
            current_index = next((i for i, t in enumerate(themes) if t.id == current_id), 0)
            next_index = (current_index + 1) % len(themes)
            next_theme = themes[next_index]

            success = theme_service.apply_theme(next_theme.id)
            if success:
                # Show status message
                ui_service = context.get_service(UIService)
                if ui_service:
                    ui_service.set_status_message(f"Theme changed to: {next_theme.name}", 2000)

                logger.info(f"Cycled to theme: {next_theme.id}")
                return CommandResult(success=True, value={'theme_id': next_theme.id})
            else:
                return CommandResult(success=False, error=f"Failed to apply theme: {next_theme.id}")

    except Exception as e:
        logger.error(f"Failed to select theme: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="theme.selectVSCodeDark",
    title="VSCode Dark+ Theme",
    category="Preferences: Color Theme",
    description="Apply VSCode Dark+ theme"
)
def select_vscode_dark_command(context: CommandContext) -> CommandResult:
    """Apply VSCode Dark+ theme."""
    return select_theme_command(context, "vscode-dark")


@command(
    id="theme.selectVSCodeLight",
    title="VSCode Light Theme",
    category="Preferences: Color Theme",
    description="Apply VSCode Light theme"
)
def select_vscode_light_command(context: CommandContext) -> CommandResult:
    """Apply VSCode Light theme."""
    return select_theme_command(context, "vscode-light")


@command(
    id="theme.selectMonokai",
    title="Monokai Theme",
    category="Preferences: Color Theme",
    description="Apply Monokai theme"
)
def select_monokai_command(context: CommandContext) -> CommandResult:
    """Apply Monokai theme."""
    return select_theme_command(context, "monokai")


@command(
    id="theme.selectSolarizedDark",
    title="Solarized Dark Theme",
    category="Preferences: Color Theme",
    description="Apply Solarized Dark theme"
)
def select_solarized_dark_command(context: CommandContext) -> CommandResult:
    """Apply Solarized Dark theme."""
    return select_theme_command(context, "solarized-dark")


@command(
    id="theme.createCustomTheme",
    title="Create Custom Theme...",
    category="Preferences",
    description="Create a new custom theme based on current theme"
)
def create_custom_theme_command(context: CommandContext) -> CommandResult:
    """
    Create a new custom theme.

    Returns:
        CommandResult indicating success or failure
    """
    try:
        theme_service = context.get_service(ThemeService)
        if not theme_service:
            return CommandResult(success=False, error="ThemeService not available")

        # For now, create a copy of the current theme with a generic name
        current_theme = theme_service.get_current_theme()
        if not current_theme:
            return CommandResult(success=False, error="No current theme")

        # Create custom theme
        custom_theme = theme_service.create_custom_theme(
            base_theme_id=current_theme.id,
            name=f"Custom {current_theme.name}",
            description="Custom theme created by user"
        )

        if custom_theme:
            # Save the custom theme
            theme_service.save_custom_theme(custom_theme)

            # Apply the new custom theme
            theme_service.apply_theme(custom_theme.id)

            # Show status message
            ui_service = context.get_service(UIService)
            if ui_service:
                ui_service.set_status_message(f"Created custom theme: {custom_theme.name}", 3000)

            logger.info(f"Created custom theme: {custom_theme.id}")
            return CommandResult(success=True, value={'theme_id': custom_theme.id})
        else:
            return CommandResult(success=False, error="Failed to create custom theme")

    except Exception as e:
        logger.error(f"Failed to create custom theme: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="theme.exportTheme",
    title="Export Current Theme...",
    category="Preferences",
    description="Export the current theme to a file"
)
def export_theme_command(context: CommandContext) -> CommandResult:
    """
    Export the current theme to a file.

    Returns:
        CommandResult indicating success or failure
    """
    try:
        theme_service = context.get_service(ThemeService)
        if not theme_service:
            return CommandResult(success=False, error="ThemeService not available")

        current_theme = theme_service.get_current_theme()
        if not current_theme:
            return CommandResult(success=False, error="No current theme")

        # For now, export to a default location
        from pathlib import Path
        export_path = Path.home() / "Downloads" / f"{current_theme.id}.json"

        success = theme_service.export_theme(current_theme.id, export_path)
        if success:
            # Show status message
            ui_service = context.get_service(UIService)
            if ui_service:
                ui_service.set_status_message(f"Theme exported to: {export_path}", 3000)

            logger.info(f"Exported theme to: {export_path}")
            return CommandResult(success=True, value={'path': str(export_path)})
        else:
            return CommandResult(success=False, error="Failed to export theme")

    except Exception as e:
        logger.error(f"Failed to export theme: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="theme.importTheme",
    title="Import Theme...",
    category="Preferences",
    description="Import a theme from a file"
)
def import_theme_command(context: CommandContext, file_path: str = None) -> CommandResult:
    """
    Import a theme from a file.

    Args:
        context: Command context
        file_path: Optional path to theme file

    Returns:
        CommandResult indicating success or failure
    """
    try:
        theme_service = context.get_service(ThemeService)
        if not theme_service:
            return CommandResult(success=False, error="ThemeService not available")

        if not file_path:
            # In a real implementation, this would open a file dialog
            return CommandResult(success=False, error="No file path provided")

        from pathlib import Path
        import_path = Path(file_path)
        if not import_path.exists():
            return CommandResult(success=False, error=f"File not found: {file_path}")

        theme_id = theme_service.import_theme(import_path)
        if theme_id:
            # Apply the imported theme
            theme_service.apply_theme(theme_id)

            # Show status message
            ui_service = context.get_service(UIService)
            if ui_service:
                ui_service.set_status_message(f"Imported and applied theme: {theme_id}", 3000)

            logger.info(f"Imported theme: {theme_id}")
            return CommandResult(success=True, value={'theme_id': theme_id})
        else:
            return CommandResult(success=False, error="Failed to import theme")

    except Exception as e:
        logger.error(f"Failed to import theme: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="theme.resetToDefault",
    title="Reset Theme to Default",
    category="Preferences",
    description="Reset theme to default VSCode Dark+"
)
def reset_theme_command(context: CommandContext) -> CommandResult:
    """
    Reset theme to default.

    Returns:
        CommandResult indicating success or failure
    """
    return select_theme_command(context, "vscode-dark")


@command(
    id="theme.openEditor",
    title="Open Theme Editor",
    category="Preferences",
    description="Open the theme editor to customize themes",
    shortcut="ctrl+k ctrl+m"
)
def open_theme_editor_command(context: CommandContext) -> CommandResult:
    """Open the theme editor in a new pane."""
    try:
        from services.workspace_service import WorkspaceService
        from ui.widgets.widget_registry import WidgetType
        import uuid

        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(
                success=False,
                error="Workspace service not available"
            )

        # Create unique widget ID
        widget_id = f"theme_editor_{uuid.uuid4().hex[:8]}"

        # Add theme editor widget to workspace using the registered factory
        success = workspace_service.add_app_widget(
            widget_type=WidgetType.CUSTOM,
            widget_id=widget_id,
            name="Theme Editor"
        )

        if success:
            logger.info("Opened theme editor")
            return CommandResult(
                success=True,
                value={'widget_id': widget_id}
            )
        else:
            return CommandResult(
                success=False,
                error="Failed to add theme editor to workspace"
            )

    except Exception as e:
        logger.error(f"Failed to open theme editor: {e}")
        return CommandResult(
            success=False,
            error=f"Failed to open theme editor: {e}"
        )


@command(
    id="theme.importVSCode",
    title="Import VSCode Theme...",
    category="Preferences",
    description="Import a theme from VSCode JSON format"
)
def import_vscode_theme_command(context: CommandContext) -> CommandResult:
    """Import a VSCode theme."""
    try:
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from pathlib import Path
        from core.themes.importers import VSCodeThemeImporter

        theme_service = context.get_service(ThemeService)
        if not theme_service:
            return CommandResult(
                success=False,
                error="Theme service not available"
            )

        # Get main window for dialog parent
        ui_service = context.get_service(UIService)
        parent = ui_service.get_main_window() if ui_service else None

        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            parent,
            "Import VSCode Theme",
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return CommandResult(success=False, error="No file selected")

        # Import theme
        theme = VSCodeThemeImporter.import_from_file(Path(file_path))
        if not theme:
            if parent:
                QMessageBox.critical(
                    parent,
                    "Import Failed",
                    "Failed to import VSCode theme. Please check the file format."
                )
            return CommandResult(
                success=False,
                error="Failed to import theme"
            )

        # Add to theme service
        theme_service._themes[theme.id] = theme
        theme_service.save_custom_theme(theme)

        # Apply imported theme
        theme_service.apply_theme(theme.id)

        if parent:
            QMessageBox.information(
                parent,
                "Import Successful",
                f"Successfully imported theme: {theme.name}"
            )

        logger.info(f"Imported VSCode theme: {theme.id}")
        return CommandResult(success=True, value={'theme_id': theme.id})

    except Exception as e:
        logger.error(f"Failed to import VSCode theme: {e}")
        return CommandResult(
            success=False,
            error=f"Failed to import theme: {e}"
        )


# Register commands with the theme category
def register_theme_commands():
    """Register all theme commands."""
    logger.info("Theme commands registered")