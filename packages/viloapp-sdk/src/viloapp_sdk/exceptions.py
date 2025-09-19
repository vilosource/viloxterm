"""Exception types for plugin SDK."""

class PluginError(Exception):
    """Base exception for plugin-related errors."""
    pass

class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""
    pass

class PluginActivationError(PluginError):
    """Raised when a plugin fails to activate."""
    pass

class PluginDependencyError(PluginError):
    """Raised when plugin dependencies are not met."""
    pass

class PluginVersionError(PluginError):
    """Raised when plugin version requirements are not met."""
    pass

class PluginConfigurationError(PluginError):
    """Raised when plugin configuration is invalid."""
    pass

class PluginSecurityError(PluginError):
    """Raised when plugin violates security constraints."""
    pass

class WidgetCreationError(PluginError):
    """Raised when widget creation fails."""
    pass

class ServiceNotFoundError(PluginError):
    """Raised when a required service is not found."""
    pass