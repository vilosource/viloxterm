"""Plugin interface and metadata definitions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

class PluginCapability(Enum):
    """Plugin capabilities that can be declared."""
    WIDGETS = "widgets"
    COMMANDS = "commands"
    THEMES = "themes"
    LANGUAGES = "languages"
    DEBUGGERS = "debuggers"
    TERMINALS = "terminals"
    EDITORS = "editors"
    VIEWS = "views"
    SETTINGS = "settings"

@dataclass
class PluginMetadata:
    """Plugin metadata and manifest information."""
    # Required fields
    id: str
    name: str
    version: str
    description: str
    author: str

    # Optional fields
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = None
    icon: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)

    # Technical fields
    engines: Dict[str, str] = field(default_factory=dict)  # {"viloapp": ">=2.0.0"}
    dependencies: List[str] = field(default_factory=list)
    activation_events: List[str] = field(default_factory=list)
    capabilities: List[PluginCapability] = field(default_factory=list)

    # Contributions
    contributes: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Validate metadata and return list of errors."""
        errors = []

        if not self.id:
            errors.append("Plugin ID is required")
        if not self.name:
            errors.append("Plugin name is required")
        if not self.version:
            errors.append("Plugin version is required")
        if not self.description:
            errors.append("Plugin description is required")
        if not self.author:
            errors.append("Plugin author is required")

        # Validate ID format (alphanumeric with hyphens)
        if self.id and not all(c.isalnum() or c == '-' for c in self.id):
            errors.append("Plugin ID must be alphanumeric with hyphens only")

        return errors

class IPlugin(ABC):
    """Base interface for all plugins."""

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """
        Get plugin metadata.

        Returns:
            PluginMetadata: The plugin's metadata
        """
        pass

    @abstractmethod
    def activate(self, context: 'IPluginContext') -> None:
        """
        Called when the plugin is activated.

        Args:
            context: Plugin context providing access to host services
        """
        pass

    @abstractmethod
    def deactivate(self) -> None:
        """
        Called when the plugin is deactivated.

        Should clean up resources, unregister handlers, etc.
        """
        pass

    def on_configuration_changed(self, config: Dict[str, Any]) -> None:
        """
        Called when plugin configuration changes.

        Args:
            config: Updated configuration dictionary
        """
        pass

    def on_command(self, command_id: str, args: Dict[str, Any]) -> Any:
        """
        Handle command execution.

        Args:
            command_id: The command ID to execute
            args: Command arguments

        Returns:
            Command result
        """
        pass