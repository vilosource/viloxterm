"""Service adapters for plugin SDK interfaces."""

from typing import Any, Optional, Dict
from viloapp_sdk import IService

class CommandServiceAdapter(IService):
    """Adapter for command service."""

    def __init__(self, command_service):
        self.command_service = command_service

    def get_service_id(self) -> str:
        return "command"

    def get_service_version(self) -> str:
        return "1.0.0"

    def execute_command(self, command_id: str, **kwargs) -> Any:
        from core.commands.executor import execute_command
        result = execute_command(command_id, **kwargs)
        return result.value if result.success else None

    def register_command(self, command_id: str, handler: callable) -> None:
        """Register a command with the command registry."""
        from core.commands.registry import command_registry
        from core.commands.base import Command, CommandContext, CommandResult

        # Create wrapper that converts plugin handler to command handler
        def command_wrapper(context: CommandContext) -> CommandResult:
            try:
                # Convert CommandContext to plugin args
                plugin_args = {
                    'workspace': context.workspace,
                    'active_widget': context.active_widget,
                    **context.args
                }
                result = handler(plugin_args)
                return CommandResult(success=True, value=result)
            except Exception as e:
                return CommandResult(success=False, error=str(e))

        # Create Command instance
        command = Command(
            id=command_id,
            title=command_id.replace('.', ' ').title(),
            category="Plugin",
            handler=command_wrapper
        )

        # Register with command registry
        command_registry.register(command)

    def unregister_command(self, command_id: str) -> None:
        """Unregister a command from the command registry."""
        from core.commands.registry import command_registry
        command_registry.unregister(command_id)

class ConfigurationServiceAdapter(IService):
    """Adapter for configuration service."""

    def __init__(self, settings_service):
        self.settings_service = settings_service

    def get_service_id(self) -> str:
        return "configuration"

    def get_service_version(self) -> str:
        return "1.0.0"

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings_service.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.settings_service.set(key, value)

    def on_change(self, key: str, callback: callable) -> None:
        """Subscribe to configuration changes."""
        if hasattr(self.settings_service, 'setting_changed'):
            # Connect to settings service signal
            self.settings_service.setting_changed.connect(
                lambda k, v: callback(v) if k == key else None
            )
        else:
            # Settings service doesn't support change notifications
            pass

class WorkspaceServiceAdapter(IService):
    """Adapter for workspace service."""

    def __init__(self, workspace_service):
        self.workspace_service = workspace_service

    def get_service_id(self) -> str:
        return "workspace"

    def get_service_version(self) -> str:
        return "1.0.0"

    def open_file(self, path: str) -> None:
        """Open file in editor."""
        try:
            # Use workspace service to open file
            if hasattr(self.workspace_service, 'open_file'):
                self.workspace_service.open_file(path)
            else:
                # Fallback: create new editor tab with file
                from ui.widgets.widget_registry import WidgetType
                widget_id = f"editor_{path.split('/')[-1]}"
                if hasattr(self.workspace_service, 'add_tab'):
                    self.workspace_service.add_tab(widget_id, WidgetType.TEXT_EDITOR, title=path.split('/')[-1])
        except Exception as e:
            print(f"Failed to open file {path}: {e}")

    def get_active_editor(self) -> Optional[Any]:
        """Return active editor widget."""
        try:
            if hasattr(self.workspace_service, 'get_active_widget'):
                widget = self.workspace_service.get_active_widget()
                if widget and hasattr(widget, 'widget_type'):
                    from ui.widgets.widget_registry import WidgetType
                    if widget.widget_type == WidgetType.TEXT_EDITOR:
                        return widget
            return None
        except Exception as e:
            print(f"Failed to get active editor: {e}")
            return None

    def create_pane(self, widget: Any, position: str) -> None:
        """Create new pane with widget."""
        try:
            if hasattr(self.workspace_service, 'workspace'):
                workspace = self.workspace_service.workspace
                # Implementation depends on workspace structure
                if hasattr(workspace, 'split_pane'):
                    workspace.split_pane(widget, position)
                elif hasattr(self.workspace_service, 'split_current_pane'):
                    # Alternative method
                    self.workspace_service.split_current_pane(position)
        except Exception as e:
            print(f"Failed to create pane: {e}")

    def register_widget_factory(self, widget_id: str, factory: Any) -> None:
        """Register a widget factory (for plugins)."""
        try:
            if hasattr(self.workspace_service, 'register_widget_factory'):
                self.workspace_service.register_widget_factory(widget_id, factory)
            else:
                print(f"WorkspaceService doesn't support widget factory registration")
        except Exception as e:
            print(f"Failed to register widget factory {widget_id}: {e}")

    def create_widget(self, widget_id: str, instance_id: str) -> Optional[Any]:
        """Create a widget using registered factory."""
        try:
            if hasattr(self.workspace_service, 'create_widget'):
                return self.workspace_service.create_widget(widget_id, instance_id)
            else:
                print(f"WorkspaceService doesn't support widget creation")
                return None
        except Exception as e:
            print(f"Failed to create widget {widget_id}: {e}")
            return None

class ThemeServiceAdapter(IService):
    """Adapter for theme service."""

    def __init__(self, theme_service):
        self.theme_service = theme_service

    def get_service_id(self) -> str:
        return "theme"

    def get_service_version(self) -> str:
        return "1.0.0"

    def get_current_theme(self) -> Dict[str, Any]:
        theme = self.theme_service.get_current_theme()
        return {
            "id": theme.id,
            "name": theme.name,
            "colors": theme.colors
        }

    def get_color(self, key: str) -> str:
        return self.theme_service.get_color(key)

    def on_theme_changed(self, callback: callable) -> None:
        self.theme_service.theme_changed.connect(callback)

class NotificationServiceAdapter(IService):
    """Adapter for notification service."""

    def __init__(self, ui_service):
        self.ui_service = ui_service

    def get_service_id(self) -> str:
        return "notification"

    def get_service_version(self) -> str:
        return "1.0.0"

    def info(self, message: str, title: Optional[str] = None) -> None:
        # Show info notification
        print(f"INFO: {title or ''} - {message}")

    def warning(self, message: str, title: Optional[str] = None) -> None:
        # Show warning notification
        print(f"WARNING: {title or ''} - {message}")

    def error(self, message: str, title: Optional[str] = None) -> None:
        # Show error notification
        print(f"ERROR: {title or ''} - {message}")

def create_service_adapters(services: Dict[str, Any]) -> Dict[str, Any]:
    """Create service adapters for plugins."""
    adapters = {}

    # Add command service
    if 'command_service' in services:
        adapters['command'] = CommandServiceAdapter(services['command_service'])

    # Add configuration service
    if 'settings_service' in services:
        adapters['configuration'] = ConfigurationServiceAdapter(services['settings_service'])

    # Add workspace service
    if 'workspace_service' in services:
        adapters['workspace'] = WorkspaceServiceAdapter(services['workspace_service'])

    # Add theme service
    if 'theme_service' in services:
        adapters['theme'] = ThemeServiceAdapter(services['theme_service'])

    # Add notification service
    if 'ui_service' in services:
        adapters['notification'] = NotificationServiceAdapter(services['ui_service'])

    return adapters