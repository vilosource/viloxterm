"""
Widget-related commands for managing widget preferences and defaults.
"""

import logging
from typing import Optional

from viloapp.core.commands.base import Command, CommandContext, CommandResult, CommandStatus

logger = logging.getLogger(__name__)


class SetDefaultWidgetCommand(Command):
    """Command to set the default widget for a context."""

    def __init__(self, context: str, widget_id: str):
        """Initialize set default widget command.

        Args:
            context: The context (e.g., "general", "file:python")
            widget_id: The widget ID to set as default
        """
        self.context = context
        self.widget_id = widget_id

    def execute(self, context: CommandContext) -> CommandResult:
        """Execute the set default widget command."""
        try:
            # Get widget service
            widget_service = context.get_service("WidgetService")
            if not widget_service:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message="Widget service not available"
                )

            # Set the default
            if widget_service.set_default_widget(self.context, self.widget_id):
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=f"Set default widget for {self.context} to {self.widget_id}"
                )
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message=f"Failed to set default widget: {self.widget_id} not available"
                )

        except Exception as e:
            logger.error(f"Error setting default widget: {e}", exc_info=True)
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error: {str(e)}"
            )


class ClearDefaultWidgetCommand(Command):
    """Command to clear the default widget for a context."""

    def __init__(self, context: str):
        """Initialize clear default widget command.

        Args:
            context: The context to clear
        """
        self.context = context

    def execute(self, context: CommandContext) -> CommandResult:
        """Execute the clear default widget command."""
        try:
            # Get widget service
            widget_service = context.get_service("WidgetService")
            if not widget_service:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message="Widget service not available"
                )

            # Clear the default
            if widget_service.clear_default_widget(self.context):
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=f"Cleared default widget for {self.context}"
                )
            else:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=f"No default widget set for {self.context}"
                )

        except Exception as e:
            logger.error(f"Error clearing default widget: {e}", exc_info=True)
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error: {str(e)}"
            )


class ShowWidgetPreferencesCommand(Command):
    """Command to show all widget preferences."""

    def execute(self, context: CommandContext) -> CommandResult:
        """Execute the show widget preferences command."""
        try:
            # Get widget service
            widget_service = context.get_service("WidgetService")
            if not widget_service:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message="Widget service not available"
                )

            # Get all preferences
            preferences = widget_service.get_all_preferences()

            if preferences:
                lines = ["Widget Preferences:"]
                for ctx, widget_id in preferences.items():
                    lines.append(f"  {ctx}: {widget_id}")
                message = "\n".join(lines)
            else:
                message = "No widget preferences set"

            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=message,
                data={"preferences": preferences}
            )

        except Exception as e:
            logger.error(f"Error showing widget preferences: {e}", exc_info=True)
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error: {str(e)}"
            )


class ListAvailableWidgetsCommand(Command):
    """Command to list all available widgets."""

    def __init__(self, category: Optional[str] = None):
        """Initialize list available widgets command.

        Args:
            category: Optional category to filter by
        """
        self.category = category

    def execute(self, context: CommandContext) -> CommandResult:
        """Execute the list available widgets command."""
        try:
            # Get widget service
            widget_service = context.get_service("WidgetService")
            if not widget_service:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message="Widget service not available"
                )

            # Get available widgets
            if self.category:
                widget_ids = widget_service.get_widgets_by_category(self.category)
                widgets = [widget_service.get_widget_info(w) for w in widget_ids]
                widgets = [w for w in widgets if w]  # Filter None values
            else:
                widgets = widget_service.get_available_widgets()

            if widgets:
                lines = [f"Available Widgets{f' in {self.category}' if self.category else ''}:"]
                for widget in widgets:
                    lines.append(f"  {widget['id']}: {widget['name']}")
                    if widget.get('description'):
                        lines.append(f"    {widget['description']}")
                message = "\n".join(lines)
            else:
                message = f"No widgets available{f' in category {self.category}' if self.category else ''}"

            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=message,
                data={"widgets": widgets}
            )

        except Exception as e:
            logger.error(f"Error listing widgets: {e}", exc_info=True)
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error: {str(e)}"
            )


class ChangePaneWidgetCommand(Command):
    """Command to change the widget in a specific pane."""

    def __init__(self, pane_id: str, widget_id: str):
        """Initialize change pane widget command.

        Args:
            pane_id: The pane ID to change
            widget_id: The new widget ID
        """
        self.pane_id = pane_id
        self.widget_id = widget_id

    def execute(self, context: CommandContext) -> CommandResult:
        """Execute the change pane widget command."""
        try:
            # Get widget service
            widget_service = context.get_service("WidgetService")
            if not widget_service:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message="Widget service not available"
                )

            # Change the pane widget
            if widget_service.change_pane_widget(self.pane_id, self.widget_id):
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=f"Changed pane {self.pane_id} to widget {self.widget_id}"
                )
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message="Failed to change pane widget"
                )

        except Exception as e:
            logger.error(f"Error changing pane widget: {e}", exc_info=True)
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error: {str(e)}"
            )


# Register commands
def register_widget_commands():
    """Register widget commands with the command registry."""
    # Widget preference commands
    from viloapp.core.commands.base import FunctionCommand
    from viloapp.core.commands.registry import command_registry

    command_registry.register(
        FunctionCommand(
            id="widget.setDefault",
            title="Set Default Widget",
            category="Widget",
            handler=lambda ctx: SetDefaultWidgetCommand(
                ctx.parameters.get("context", "general"),
                ctx.parameters.get("widget_id", "com.viloapp.placeholder")
            ).execute(ctx),
            description="Set default widget for a context"
        )
    )

    command_registry.register(
        FunctionCommand(
            id="widget.clearDefault",
            title="Clear Default Widget",
            category="Widget",
            handler=lambda ctx: ClearDefaultWidgetCommand(
                ctx.parameters.get("context", "general")
            ).execute(ctx),
            description="Clear default widget for a context"
        )
    )

    command_registry.register(
        FunctionCommand(
            id="widget.showPreferences",
            title="Show Widget Preferences",
            category="Widget",
            handler=lambda ctx: ShowWidgetPreferencesCommand().execute(ctx),
            description="Show all widget preferences"
        )
    )

    # Widget discovery commands
    command_registry.register(
        FunctionCommand(
            id="widget.list",
            title="List Widgets",
            category="Widget",
            handler=lambda ctx: ListAvailableWidgetsCommand(
                ctx.parameters.get("category") if ctx.parameters else None
            ).execute(ctx),
            description="List available widgets"
        )
    )

    # Widget manipulation commands
    command_registry.register(
        FunctionCommand(
            id="widget.changePane",
            title="Change Pane Widget",
            category="Widget",
            handler=lambda ctx: ChangePaneWidgetCommand(
                ctx.parameters.get("pane_id", ""),
                ctx.parameters.get("widget_id", "com.viloapp.placeholder")
            ).execute(ctx),
            description="Change widget in a pane"
        )
    )

    logger.info("Registered widget commands")
