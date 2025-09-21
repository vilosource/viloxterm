"""Security framework for plugin system."""

from .permissions import Permission, PermissionManager, PermissionScope, PermissionCategory
from .resources import ResourceMonitor, ResourceLimiter, ResourceType, ResourceViolation
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