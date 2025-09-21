"""Permission system for plugin security."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Set, Any, Optional
import fnmatch
import json
from pathlib import Path


class PermissionCategory(Enum):
    """Categories of permissions a plugin can request."""
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    SYSTEM = "system"
    UI = "ui"


class PermissionScope(Enum):
    """Scope of permissions within a category."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"


@dataclass(frozen=True)
class Permission:
    """Represents a specific permission for a plugin."""
    category: PermissionCategory
    scope: PermissionScope
    resource: str

    def __str__(self) -> str:
        """String representation of permission."""
        return f"{self.category.value}:{self.scope.value}:{self.resource}"

    def __eq__(self, other) -> bool:
        """Check equality with another permission."""
        if not isinstance(other, Permission):
            return False
        return (
            self.category == other.category and
            self.scope == other.scope and
            self.resource == other.resource
        )

    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash((self.category, self.scope, self.resource))

    def matches_resource(self, resource_path: str) -> bool:
        """Check if this permission matches a specific resource path."""
        # Handle exact matches
        if self.resource == resource_path:
            return True

        # Handle wildcard matching
        if fnmatch.fnmatch(resource_path, self.resource):
            return True

        # Handle directory access - if permission is for directory, allow access to files within
        if self.category == PermissionCategory.FILESYSTEM:
            # If permission resource is a directory, allow access to files within it
            if resource_path.startswith(self.resource + "/"):
                return True
            # If permission resource ends with /*, allow access to files in directory
            if self.resource.endswith("/*") and resource_path.startswith(self.resource[:-2] + "/"):
                return True

        return False


class PermissionManager:
    """Manages permissions for plugins."""

    def __init__(self):
        """Initialize permission manager."""
        self._plugin_permissions: Dict[str, Set[Permission]] = {}
        self._default_permissions: Dict[str, List[Permission]] = self._initialize_defaults()

    def _initialize_defaults(self) -> Dict[str, List[Permission]]:
        """Initialize default permission sets for different plugin types."""
        return {
            "widget": [
                Permission(PermissionCategory.UI, PermissionScope.READ, "*"),
                Permission(PermissionCategory.UI, PermissionScope.WRITE, "*"),
            ],
            "service": [
                Permission(PermissionCategory.SYSTEM, PermissionScope.READ, "config"),
            ],
            "command": [
                Permission(PermissionCategory.UI, PermissionScope.EXECUTE, "commands"),
            ]
        }

    def set_plugin_permissions(self, plugin_id: str, permissions: List[Permission]) -> None:
        """Set permissions for a plugin."""
        self._plugin_permissions[plugin_id] = set(permissions)

    def get_plugin_permissions(self, plugin_id: str) -> List[Permission]:
        """Get all permissions for a plugin."""
        permissions = self._plugin_permissions.get(plugin_id, set())
        return list(permissions)

    def grant_permission(self, plugin_id: str, permission: Permission) -> None:
        """Grant a specific permission to a plugin."""
        if plugin_id not in self._plugin_permissions:
            self._plugin_permissions[plugin_id] = set()
        self._plugin_permissions[plugin_id].add(permission)

    def revoke_permission(self, plugin_id: str, permission: Permission) -> None:
        """Revoke a specific permission from a plugin."""
        if plugin_id in self._plugin_permissions:
            self._plugin_permissions[plugin_id].discard(permission)

    def has_permission(self, plugin_id: str, permission: Permission) -> bool:
        """Check if a plugin has a specific permission."""
        plugin_permissions = self._plugin_permissions.get(plugin_id, set())
        return permission in plugin_permissions

    def can_access(
        self,
        plugin_id: str,
        category: PermissionCategory,
        scope: PermissionScope,
        resource: str
    ) -> bool:
        """
        Check if a plugin can access a specific resource.

        Args:
            plugin_id: Plugin identifier
            category: Permission category
            scope: Permission scope
            resource: Resource path/identifier

        Returns:
            True if plugin has permission to access resource
        """
        plugin_permissions = self._plugin_permissions.get(plugin_id, set())

        for permission in plugin_permissions:
            if (permission.category == category and
                permission.scope == scope and
                permission.matches_resource(resource)):
                return True

        return False

    def get_default_permissions(self, plugin_type: str) -> List[Permission]:
        """Get default permissions for a plugin type."""
        return self._default_permissions.get(plugin_type, []).copy()

    def permissions_from_manifest(self, manifest: Dict[str, Any]) -> List[Permission]:
        """
        Extract permissions from a plugin manifest.

        Args:
            manifest: Plugin manifest dictionary

        Returns:
            List of Permission objects

        Raises:
            ValueError: If manifest contains invalid permission data
        """
        permissions = []
        manifest_perms = manifest.get("permissions", [])

        for perm_data in manifest_perms:
            try:
                category_str = perm_data["category"].upper()
                scope_str = perm_data["scope"].upper()
                resource = perm_data["resource"]

                # Validate category
                try:
                    category = PermissionCategory[category_str]
                except KeyError:
                    raise ValueError(f"Invalid permission category: {category_str}")

                # Validate scope
                try:
                    scope = PermissionScope[scope_str]
                except KeyError:
                    raise ValueError(f"Invalid permission scope: {scope_str}")

                permission = Permission(category, scope, resource)
                permissions.append(permission)

            except KeyError as e:
                raise ValueError(f"Missing required permission field: {e}")

        return permissions

    def save_configuration(self) -> Dict[str, Any]:
        """
        Save permission configuration to a dictionary.

        Returns:
            Configuration dictionary
        """
        config = {}
        for plugin_id, permissions in self._plugin_permissions.items():
            config[plugin_id] = [
                {
                    "category": perm.category.value,
                    "scope": perm.scope.value,
                    "resource": perm.resource
                }
                for perm in permissions
            ]
        return config

    def load_configuration(self, config: Dict[str, Any]) -> None:
        """
        Load permission configuration from a dictionary.

        Args:
            config: Configuration dictionary
        """
        self._plugin_permissions.clear()

        for plugin_id, perm_list in config.items():
            permissions = []
            for perm_data in perm_list:
                category = PermissionCategory(perm_data["category"])
                scope = PermissionScope(perm_data["scope"])
                resource = perm_data["resource"]
                permissions.append(Permission(category, scope, resource))

            self._plugin_permissions[plugin_id] = set(permissions)

    def request_permission(
        self,
        plugin_id: str,
        permission: Permission,
        reason: Optional[str] = None
    ) -> bool:
        """
        Request a permission for a plugin.

        This would typically show a dialog to the user in a real implementation.
        For now, we'll grant basic permissions automatically and deny risky ones.

        Args:
            plugin_id: Plugin requesting permission
            permission: Permission being requested
            reason: Optional reason for the permission request

        Returns:
            True if permission granted, False if denied
        """
        # Basic security policy - auto-grant safe permissions
        safe_permissions = [
            (PermissionCategory.UI, PermissionScope.READ),
            (PermissionCategory.UI, PermissionScope.WRITE),
            (PermissionCategory.FILESYSTEM, PermissionScope.READ),
        ]

        permission_tuple = (permission.category, permission.scope)

        if permission_tuple in safe_permissions:
            self.grant_permission(plugin_id, permission)
            return True

        # For now, deny potentially dangerous permissions
        # In a real implementation, this would show a user dialog
        return False

    def validate_plugin_permissions(self, plugin_id: str, manifest: Dict[str, Any]) -> bool:
        """
        Validate that a plugin's requested permissions are acceptable.

        Args:
            plugin_id: Plugin identifier
            manifest: Plugin manifest

        Returns:
            True if all permissions are valid and granted
        """
        try:
            requested_permissions = self.permissions_from_manifest(manifest)

            # Check each permission
            for permission in requested_permissions:
                if not self.request_permission(plugin_id, permission):
                    return False

            return True

        except ValueError:
            # Invalid permission data in manifest
            return False

    def get_permission_summary(self, plugin_id: str) -> Dict[str, Any]:
        """
        Get a human-readable summary of a plugin's permissions.

        Args:
            plugin_id: Plugin identifier

        Returns:
            Permission summary dictionary
        """
        permissions = self.get_plugin_permissions(plugin_id)
        summary = {
            "plugin_id": plugin_id,
            "total_permissions": len(permissions),
            "by_category": {},
            "risky_permissions": []
        }

        # Group by category
        for perm in permissions:
            category = perm.category.value
            if category not in summary["by_category"]:
                summary["by_category"][category] = []

            summary["by_category"][category].append({
                "scope": perm.scope.value,
                "resource": perm.resource
            })

            # Flag risky permissions
            if perm.scope == PermissionScope.EXECUTE or perm.resource == "*":
                summary["risky_permissions"].append(str(perm))

        return summary