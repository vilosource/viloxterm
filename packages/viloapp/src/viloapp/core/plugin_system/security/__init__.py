"""Security framework for plugin system."""

from .permissions import Permission, PermissionCategory, PermissionManager, PermissionScope
from .resources import ResourceLimiter, ResourceMonitor, ResourceType, ResourceViolation
from .sandbox import PluginSandbox, RestartPolicy

__all__ = [
    "Permission",
    "PermissionManager",
    "PermissionScope",
    "PermissionCategory",
    "ResourceMonitor",
    "ResourceLimiter",
    "ResourceType",
    "ResourceViolation",
    "PluginSandbox",
    "RestartPolicy",
]
