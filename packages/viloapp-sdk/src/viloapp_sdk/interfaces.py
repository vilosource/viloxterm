"""Core interfaces for the ViloxTerm Plugin SDK."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class IMetadata(ABC):
    """Interface for plugin metadata providers."""

    @abstractmethod
    def get_id(self) -> str:
        """
        Get unique plugin identifier.

        Returns:
            str: Unique identifier for the plugin
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Get plugin display name.

        Returns:
            str: Human-readable plugin name
        """
        pass

    @abstractmethod
    def get_version(self) -> str:
        """
        Get plugin version.

        Returns:
            str: Plugin version in semantic versioning format
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """
        Get plugin description.

        Returns:
            str: Brief description of plugin functionality
        """
        pass

    @abstractmethod
    def get_author(self) -> Dict[str, str]:
        """
        Get plugin author information.

        Returns:
            Dict[str, str]: Author information with keys like 'name', 'email', 'url'
        """
        pass

    @abstractmethod
    def get_license(self) -> str:
        """
        Get plugin license.

        Returns:
            str: License identifier (e.g., 'MIT', 'GPL-3.0', 'proprietary')
        """
        pass

    @abstractmethod
    def get_dependencies(self) -> Dict[str, str]:
        """
        Get plugin dependencies.

        Returns:
            Dict[str, str]: Dependencies with version constraints
                          e.g., {"viloapp": ">=2.0.0", "python": ">=3.8"}
        """
        pass

    @abstractmethod
    def get_keywords(self) -> List[str]:
        """
        Get plugin keywords for discovery and categorization.

        Returns:
            List[str]: List of keywords
        """
        pass

    def get_homepage(self) -> Optional[str]:
        """
        Get plugin homepage URL.

        Returns:
            Optional[str]: Homepage URL or None
        """
        return None

    def get_repository(self) -> Optional[str]:
        """
        Get plugin repository URL.

        Returns:
            Optional[str]: Repository URL or None
        """
        return None

    def get_icon(self) -> Optional[str]:
        """
        Get plugin icon identifier.

        Returns:
            Optional[str]: Icon identifier or None
        """
        return None

    def get_categories(self) -> List[str]:
        """
        Get plugin categories.

        Returns:
            List[str]: List of categories for plugin organization
        """
        return []

    def validate(self) -> List[str]:
        """
        Validate metadata and return list of errors.

        Returns:
            List[str]: List of validation error messages
        """
        errors = []

        # Check required fields
        if not self.get_id():
            errors.append("Plugin ID is required")
        if not self.get_name():
            errors.append("Plugin name is required")
        if not self.get_version():
            errors.append("Plugin version is required")
        if not self.get_description():
            errors.append("Plugin description is required")
        if not self.get_author():
            errors.append("Plugin author is required")
        if not self.get_license():
            errors.append("Plugin license is required")

        # Validate ID format (alphanumeric with hyphens and dots)
        plugin_id = self.get_id()
        if plugin_id and not all(c.isalnum() or c in "-." for c in plugin_id):
            errors.append("Plugin ID must be alphanumeric with hyphens and dots only")

        # Validate version format (basic semver check)
        version = self.get_version()
        if version:
            version_parts = version.split(".")
            if len(version_parts) != 3 or not all(part.isdigit() for part in version_parts):
                errors.append("Plugin version must be in semantic versioning format (x.y.z)")

        # Validate author format
        author = self.get_author()
        if author and not isinstance(author, dict):
            errors.append("Plugin author must be a dictionary")
        elif author and "name" not in author:
            errors.append("Plugin author must include 'name' field")

        return errors


class IPlugin(ABC):
    """Base interface for all plugins."""

    @abstractmethod
    def get_metadata(self) -> "PluginMetadata":
        """
        Get plugin metadata.

        Returns:
            PluginMetadata: The plugin's metadata
        """
        pass

    @abstractmethod
    def activate(self, context: "IPluginContext") -> None:
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


class IPluginWithMetadata(IPlugin, IMetadata):
    """
    Extended plugin interface that combines plugin functionality with metadata interface.

    This interface allows plugins to implement both the core plugin functionality
    and provide metadata through the new IMetadata interface methods.
    """

    pass
