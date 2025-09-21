"""
ViloxTerm Plugin SDK.

Build powerful plugins for ViloxTerm terminal emulator and editor.
"""

from .plugin import PluginMetadata, PluginCapability
from .interfaces import IPlugin, IMetadata, IPluginWithMetadata
from .widget import IWidget, WidgetMetadata, WidgetPosition, LegacyWidgetAdapter
from .service import IService, ServiceProxy, ServiceNotAvailableError
from .events import EventBus, PluginEvent, EventType, EventPriority
from .lifecycle import ILifecycle, LifecycleState, LifecycleHook
from .context import PluginContext, IPluginContext
from .types import (
    CommandContribution,
    MenuContribution,
    KeybindingContribution,
    ConfigurationContribution
)
from .exceptions import (
    PluginError,
    PluginLoadError,
    PluginActivationError,
    PluginDependencyError
)

# Testing utilities (optional import - only available if testing module is used)
try:
    from . import testing
    _testing_available = True
except ImportError:
    _testing_available = False

# Utilities (optional import - decorators and validators)
try:
    from . import utils
    _utils_available = True
except ImportError:
    _utils_available = False

__version__ = "1.0.0"

__all__ = [
    # Plugin interfaces
    "IPlugin",
    "IMetadata",
    "IPluginWithMetadata",
    "PluginMetadata",
    "PluginCapability",

    # Widget interfaces
    "IWidget",
    "WidgetMetadata",
    "WidgetPosition",
    "LegacyWidgetAdapter",

    # Service interfaces
    "IService",
    "ServiceProxy",
    "ServiceNotAvailableError",

    # Event system
    "EventBus",
    "PluginEvent",
    "EventType",
    "EventPriority",

    # Lifecycle
    "ILifecycle",
    "LifecycleState",
    "LifecycleHook",

    # Context
    "PluginContext",
    "IPluginContext",

    # Types
    "CommandContribution",
    "MenuContribution",
    "KeybindingContribution",
    "ConfigurationContribution",

    # Exceptions
    "PluginError",
    "PluginLoadError",
    "PluginActivationError",
    "PluginDependencyError",
]

# Add testing module to __all__ if available
if _testing_available:
    __all__.append("testing")

# Add utils module to __all__ if available
if _utils_available:
    __all__.append("utils")