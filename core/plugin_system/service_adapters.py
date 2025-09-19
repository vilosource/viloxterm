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
        # This would need implementation in command registry
        pass

    def unregister_command(self, command_id: str) -> None:
        # This would need implementation in command registry
        pass

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
        # This would need signal connection
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
        # Implementation would open file in editor
        pass

    def get_active_editor(self) -> Optional[Any]:
        # Return active editor widget
        return None

    def create_pane(self, widget: Any, position: str) -> None:
        # Create new pane with widget
        pass

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