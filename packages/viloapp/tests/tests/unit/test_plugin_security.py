"""Tests for plugin security system."""

import pytest

# Since the security modules don't exist yet, we'll import them as they are created
# For now, we'll test against the interfaces we're about to create

def test_permission_creation():
    """Test Permission class creation."""
    from viloapp.core.plugin_system.security import Permission, PermissionCategory, PermissionScope

    # Test basic permission creation
    permission = Permission(
        category=PermissionCategory.FILESYSTEM,
        scope=PermissionScope.READ,
        resource="/home/user/documents"
    )

    assert permission.category == PermissionCategory.FILESYSTEM
    assert permission.scope == PermissionScope.READ
    assert permission.resource == "/home/user/documents"

def test_permission_equality():
    """Test Permission equality comparison."""
    from viloapp.core.plugin_system.security import Permission, PermissionCategory, PermissionScope

    perm1 = Permission(
        category=PermissionCategory.FILESYSTEM,
        scope=PermissionScope.READ,
        resource="/tmp"
    )

    perm2 = Permission(
        category=PermissionCategory.FILESYSTEM,
        scope=PermissionScope.READ,
        resource="/tmp"
    )

    perm3 = Permission(
        category=PermissionCategory.FILESYSTEM,
        scope=PermissionScope.WRITE,
        resource="/tmp"
    )

    assert perm1 == perm2
    assert perm1 != perm3

def test_permission_string_representation():
    """Test Permission string representation."""
    from viloapp.core.plugin_system.security import Permission, PermissionCategory, PermissionScope

    permission = Permission(
        category=PermissionCategory.NETWORK,
        scope=PermissionScope.EXECUTE,
        resource="http://api.example.com"
    )

    str_repr = str(permission)
    assert "network" in str_repr.lower()
    assert "execute" in str_repr.lower()
    assert "api.example.com" in str_repr

def test_permission_manager_creation():
    """Test PermissionManager creation."""
    from viloapp.core.plugin_system.security import PermissionManager

    manager = PermissionManager()
    assert manager is not None

    # Test with plugin permissions
    plugin_id = "test-plugin"
    permissions = []
    manager.set_plugin_permissions(plugin_id, permissions)

    # Should start with empty permissions
    assert manager.get_plugin_permissions(plugin_id) == []

def test_permission_manager_grant_permission():
    """Test granting permissions to a plugin."""
    from viloapp.core.plugin_system.security import (
        PermissionManager, Permission, PermissionCategory, PermissionScope
    )

    manager = PermissionManager()
    plugin_id = "test-plugin"

    permission = Permission(
        category=PermissionCategory.FILESYSTEM,
        scope=PermissionScope.READ,
        resource="/tmp"
    )

    # Grant permission
    manager.grant_permission(plugin_id, permission)

    # Check permission is granted
    permissions = manager.get_plugin_permissions(plugin_id)
    assert permission in permissions

def test_permission_manager_revoke_permission():
    """Test revoking permissions from a plugin."""
    from viloapp.core.plugin_system.security import (
        PermissionManager, Permission, PermissionCategory, PermissionScope
    )

    manager = PermissionManager()
    plugin_id = "test-plugin"

    permission = Permission(
        category=PermissionCategory.FILESYSTEM,
        scope=PermissionScope.READ,
        resource="/tmp"
    )

    # Grant then revoke permission
    manager.grant_permission(plugin_id, permission)
    manager.revoke_permission(plugin_id, permission)

    # Check permission is revoked
    permissions = manager.get_plugin_permissions(plugin_id)
    assert permission not in permissions

def test_permission_manager_check_permission():
    """Test checking if a plugin has a specific permission."""
    from viloapp.core.plugin_system.security import (
        PermissionManager, Permission, PermissionCategory, PermissionScope
    )

    manager = PermissionManager()
    plugin_id = "test-plugin"

    permission = Permission(
        category=PermissionCategory.FILESYSTEM,
        scope=PermissionScope.READ,
        resource="/tmp"
    )

    # Should not have permission initially
    assert not manager.has_permission(plugin_id, permission)

    # Grant permission
    manager.grant_permission(plugin_id, permission)

    # Should have permission now
    assert manager.has_permission(plugin_id, permission)

def test_permission_manager_check_specific_access():
    """Test checking specific access patterns."""
    from viloapp.core.plugin_system.security import (
        PermissionManager, Permission, PermissionCategory, PermissionScope
    )

    manager = PermissionManager()
    plugin_id = "test-plugin"

    # Grant read access to /tmp directory
    read_permission = Permission(
        category=PermissionCategory.FILESYSTEM,
        scope=PermissionScope.READ,
        resource="/tmp"
    )
    manager.grant_permission(plugin_id, read_permission)

    # Should be able to check filesystem read access
    assert manager.can_access(
        plugin_id,
        PermissionCategory.FILESYSTEM,
        PermissionScope.READ,
        "/tmp/somefile.txt"
    )

    # Should NOT be able to write to same directory
    assert not manager.can_access(
        plugin_id,
        PermissionCategory.FILESYSTEM,
        PermissionScope.WRITE,
        "/tmp/somefile.txt"
    )

def test_permission_manager_wildcard_resources():
    """Test permission checking with wildcard resources."""
    from viloapp.core.plugin_system.security import (
        PermissionManager, Permission, PermissionCategory, PermissionScope
    )

    manager = PermissionManager()
    plugin_id = "test-plugin"

    # Grant access to all files in /tmp directory
    permission = Permission(
        category=PermissionCategory.FILESYSTEM,
        scope=PermissionScope.READ,
        resource="/tmp/*"
    )
    manager.grant_permission(plugin_id, permission)

    # Should be able to access files in the directory
    assert manager.can_access(
        plugin_id,
        PermissionCategory.FILESYSTEM,
        PermissionScope.READ,
        "/tmp/test.txt"
    )

    # Should NOT be able to access files outside directory
    assert not manager.can_access(
        plugin_id,
        PermissionCategory.FILESYSTEM,
        PermissionScope.READ,
        "/home/user/test.txt"
    )

def test_permission_categories():
    """Test all permission categories are available."""
    from viloapp.core.plugin_system.security import PermissionCategory

    expected_categories = ["FILESYSTEM", "NETWORK", "SYSTEM", "UI"]

    for category in expected_categories:
        assert hasattr(PermissionCategory, category)

def test_permission_scopes():
    """Test all permission scopes are available."""
    from viloapp.core.plugin_system.security import PermissionScope

    expected_scopes = ["READ", "WRITE", "EXECUTE"]

    for scope in expected_scopes:
        assert hasattr(PermissionScope, scope)

def test_permission_manager_default_permissions():
    """Test default permission sets."""
    from viloapp.core.plugin_system.security import PermissionManager

    manager = PermissionManager()

    # Test getting default permissions for different plugin types
    widget_permissions = manager.get_default_permissions("widget")
    service_permissions = manager.get_default_permissions("service")
    command_permissions = manager.get_default_permissions("command")

    # Widget should have UI permissions
    assert any(p.category.name == "UI" for p in widget_permissions)

    # All should have basic access
    for permissions in [widget_permissions, service_permissions, command_permissions]:
        assert len(permissions) > 0

def test_permission_manager_persistence():
    """Test saving and loading permission configurations."""
    from viloapp.core.plugin_system.security import (
        PermissionManager, Permission, PermissionCategory, PermissionScope
    )

    manager = PermissionManager()
    plugin_id = "test-plugin"

    permission = Permission(
        category=PermissionCategory.FILESYSTEM,
        scope=PermissionScope.READ,
        resource="/tmp"
    )
    manager.grant_permission(plugin_id, permission)

    # Save permissions
    config = manager.save_configuration()
    assert config is not None
    assert plugin_id in config

    # Create new manager and load
    new_manager = PermissionManager()
    new_manager.load_configuration(config)

    # Should have same permissions
    assert new_manager.has_permission(plugin_id, permission)

@pytest.fixture
def mock_plugin_manifest():
    """Mock plugin manifest with permissions."""
    return {
        "id": "test-plugin",
        "name": "Test Plugin",
        "version": "1.0.0",
        "permissions": [
            {
                "category": "filesystem",
                "scope": "read",
                "resource": "/tmp/*"
            },
            {
                "category": "network",
                "scope": "execute",
                "resource": "https://api.example.com/*"
            }
        ]
    }

def test_permission_manager_from_manifest(mock_plugin_manifest):
    """Test loading permissions from plugin manifest."""
    from viloapp.core.plugin_system.security import PermissionManager

    manager = PermissionManager()

    # Load permissions from manifest
    permissions = manager.permissions_from_manifest(mock_plugin_manifest)

    assert len(permissions) == 2

    # Check filesystem permission
    fs_perm = next(p for p in permissions if p.category.name == "FILESYSTEM")
    assert fs_perm.scope.name == "READ"
    assert fs_perm.resource == "/tmp/*"

    # Check network permission
    net_perm = next(p for p in permissions if p.category.name == "NETWORK")
    assert net_perm.scope.name == "EXECUTE"
    assert net_perm.resource == "https://api.example.com/*"

class TestServiceProxyPermissions:
    """Test service proxy permission checking."""

    def test_service_proxy_permission_check(self):
        """Test that service proxy checks permissions before service access."""
        from viloapp.core.plugin_system.security import PermissionManager
        from viloapp_sdk import ServiceProxy

        # This test will need to be implemented after ServiceProxy is updated
        # For now, we'll create a mock scenario

        manager = PermissionManager()
        services = {}

        # Create proxy with permission checking (to be implemented)
        proxy = ServiceProxy(services)

        # This will be implemented when we update ServiceProxy
        assert proxy is not None

def test_permission_validation_error_handling():
    """Test error handling in permission validation."""
    from viloapp.core.plugin_system.security import PermissionManager

    manager = PermissionManager()

    # Test with invalid plugin ID
    result = manager.get_plugin_permissions("non-existent-plugin")
    assert result == []

    # Test with invalid permission data
    with pytest.raises(ValueError):
        manager.permissions_from_manifest({
            "id": "test",
            "permissions": [
                {
                    "category": "invalid_category",
                    "scope": "read",
                    "resource": "test"
                }
            ]
        })