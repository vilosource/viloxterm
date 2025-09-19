"""
ViloxTerm Plugin SDK.

Build powerful plugins for ViloxTerm terminal emulator and editor.
"""

from .plugin import IPlugin, PluginMetadata, PluginCapability
from .widget import IWidget, WidgetMetadata, WidgetPosition
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

__version__ = "1.0.0"

__all__ = [
    # Plugin interfaces
    "IPlugin",
    "PluginMetadata",
    "PluginCapability",

    # Widget interfaces
    "IWidget",
    "WidgetMetadata",
    "WidgetPosition",

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