"""Tests for ServiceProxy permission checking."""

from unittest.mock import Mock

import pytest


def test_permission_aware_service_proxy_creation():
    """Test creating a permission-aware service proxy."""
    from viloapp_sdk import IService

    from viloapp.core.plugin_system.security import PermissionManager
    from viloapp.core.plugin_system.service_proxy_impl import PermissionAwareServiceProxy

    # Create mock services
    mock_service = Mock(spec=IService)
    mock_service.get_service_id.return_value = "test-service"
    services = {"test-service": mock_service}

    # Create permission manager
    permission_manager = PermissionManager()

    # Create permission-aware proxy
    proxy = PermissionAwareServiceProxy(
        services=services, permission_manager=permission_manager, plugin_id="test-plugin"
    )

    assert proxy is not None
    assert proxy.plugin_id == "test-plugin"


def test_service_access_with_permission():
    """Test service access when plugin has permission."""
    from viloapp_sdk import IService

    from viloapp.core.plugin_system.security import (
        Permission,
        PermissionCategory,
        PermissionManager,
        PermissionScope,
    )
    from viloapp.core.plugin_system.service_proxy_impl import PermissionAwareServiceProxy

    # Create mock services
    mock_service = Mock(spec=IService)
    mock_service.get_service_id.return_value = "configuration"
    services = {"configuration": mock_service}

    # Create permission manager and grant permission
    permission_manager = PermissionManager()
    permission = Permission(
        category=PermissionCategory.SYSTEM, scope=PermissionScope.READ, resource="configuration"
    )
    permission_manager.grant_permission("test-plugin", permission)

    # Create permission-aware proxy
    proxy = PermissionAwareServiceProxy(
        services=services, permission_manager=permission_manager, plugin_id="test-plugin"
    )

    # Should be able to access service
    service = proxy.get_service("configuration")
    assert service is not None
    # Service is wrapped, so check that we can access the original service methods
    assert hasattr(service, "get_service_id")


def test_service_access_without_permission():
    """Test service access when plugin lacks permission."""
    from viloapp_sdk import IService

    from viloapp.core.plugin_system.security import PermissionManager
    from viloapp.core.plugin_system.service_proxy_impl import PermissionAwareServiceProxy

    # Create mock services
    mock_service = Mock(spec=IService)
    mock_service.get_service_id.return_value = "filesystem"
    services = {"filesystem": mock_service}

    # Create permission manager (no permissions granted)
    permission_manager = PermissionManager()

    # Create permission-aware proxy
    proxy = PermissionAwareServiceProxy(
        services=services, permission_manager=permission_manager, plugin_id="test-plugin"
    )

    # Should not be able to access service
    service = proxy.get_service("filesystem")
    assert service is None


def test_require_service_without_permission():
    """Test require_service throws error when permission denied."""
    from viloapp_sdk import IService, ServiceNotAvailableError

    from viloapp.core.plugin_system.security import PermissionManager
    from viloapp.core.plugin_system.service_proxy_impl import PermissionAwareServiceProxy

    # Create mock services
    mock_service = Mock(spec=IService)
    mock_service.get_service_id.return_value = "filesystem"
    services = {"filesystem": mock_service}

    # Create permission manager (no permissions granted)
    permission_manager = PermissionManager()

    # Create permission-aware proxy
    proxy = PermissionAwareServiceProxy(
        services=services, permission_manager=permission_manager, plugin_id="test-plugin"
    )

    # Should raise error when trying to require service
    with pytest.raises(ServiceNotAvailableError):
        proxy.require_service("filesystem")


def test_service_mapping_permissions():
    """Test that services require appropriate permissions."""
    from viloapp.core.plugin_system.security import (
        PermissionCategory,
        PermissionManager,
        PermissionScope,
    )
    from viloapp.core.plugin_system.service_proxy_impl import PermissionAwareServiceProxy

    permission_manager = PermissionManager()

    # Mock proxy for testing permission mapping
    proxy = PermissionAwareServiceProxy(
        services={}, permission_manager=permission_manager, plugin_id="test-plugin"
    )

    # Test permission mapping for different services
    test_cases = [
        ("configuration", PermissionCategory.SYSTEM, PermissionScope.READ),
        ("filesystem", PermissionCategory.FILESYSTEM, PermissionScope.READ),
        ("network", PermissionCategory.NETWORK, PermissionScope.EXECUTE),
        ("workspace", PermissionCategory.UI, PermissionScope.WRITE),
    ]

    for service_id, category, scope in test_cases:
        required_permission = proxy._get_required_permission(service_id)
        assert required_permission.category == category
        assert required_permission.scope == scope


def test_permission_caching():
    """Test that permission checks are cached for performance."""
    from viloapp_sdk import IService

    from viloapp.core.plugin_system.security import (
        Permission,
        PermissionCategory,
        PermissionManager,
        PermissionScope,
    )
    from viloapp.core.plugin_system.service_proxy_impl import PermissionAwareServiceProxy

    # Create mock services
    mock_service = Mock(spec=IService)
    mock_service.get_service_id.return_value = "configuration"
    services = {"configuration": mock_service}

    # Create permission manager and grant permission
    permission_manager = PermissionManager()
    permission = Permission(
        category=PermissionCategory.SYSTEM, scope=PermissionScope.READ, resource="configuration"
    )
    permission_manager.grant_permission("test-plugin", permission)

    # Spy on permission manager
    permission_manager.has_permission = Mock(wraps=permission_manager.has_permission)

    # Create permission-aware proxy
    proxy = PermissionAwareServiceProxy(
        services=services, permission_manager=permission_manager, plugin_id="test-plugin"
    )

    # Access service multiple times
    proxy.get_service("configuration")
    proxy.get_service("configuration")
    proxy.get_service("configuration")

    # Permission should only be checked once (cached after first check)
    assert permission_manager.has_permission.call_count == 1


def test_service_wrapper_permission_enforcement():
    """Test that service methods are wrapped with permission checks."""
    from viloapp_sdk.service import IConfigurationService

    from viloapp.core.plugin_system.security import (
        Permission,
        PermissionCategory,
        PermissionManager,
        PermissionScope,
    )
    from viloapp.core.plugin_system.service_proxy_impl import PermissionAwareServiceProxy

    # Create mock configuration service
    mock_config_service = Mock(spec=IConfigurationService)
    mock_config_service.get_service_id.return_value = "configuration"
    mock_config_service.get.return_value = "test_value"
    services = {"configuration": mock_config_service}

    # Create permission manager and grant read permission only
    permission_manager = PermissionManager()
    read_permission = Permission(
        category=PermissionCategory.SYSTEM, scope=PermissionScope.READ, resource="configuration"
    )
    permission_manager.grant_permission("test-plugin", read_permission)

    # Create permission-aware proxy
    proxy = PermissionAwareServiceProxy(
        services=services, permission_manager=permission_manager, plugin_id="test-plugin"
    )

    # Get the wrapped service
    service = proxy.get_service("configuration")
    assert service is not None

    # Should be able to call read method
    result = service.get("test_key")
    assert result == "test_value"
    mock_config_service.get.assert_called_with("test_key")

    # Should not be able to call write method (no write permission)
    with pytest.raises(PermissionError):
        service.set("test_key", "new_value")


def test_list_available_services_respects_permissions():
    """Test that list_services only shows services the plugin can access."""
    from viloapp_sdk import IService

    from viloapp.core.plugin_system.security import (
        Permission,
        PermissionCategory,
        PermissionManager,
        PermissionScope,
    )
    from viloapp.core.plugin_system.service_proxy_impl import PermissionAwareServiceProxy

    # Create multiple mock services
    services = {}
    for service_id in ["configuration", "filesystem", "network"]:
        mock_service = Mock(spec=IService)
        mock_service.get_service_id.return_value = service_id
        services[service_id] = mock_service

    # Create permission manager and grant permission to only one service
    permission_manager = PermissionManager()
    permission = Permission(
        category=PermissionCategory.SYSTEM, scope=PermissionScope.READ, resource="configuration"
    )
    permission_manager.grant_permission("test-plugin", permission)

    # Create permission-aware proxy
    proxy = PermissionAwareServiceProxy(
        services=services, permission_manager=permission_manager, plugin_id="test-plugin"
    )

    # Should only list services the plugin has permission to access
    available_services = proxy.list_services()
    assert "configuration" in available_services
    assert "filesystem" not in available_services
    assert "network" not in available_services


def test_permission_denied_logging():
    """Test that permission denials are logged for security monitoring."""
    from unittest.mock import patch

    from viloapp_sdk import IService

    from viloapp.core.plugin_system.security import PermissionManager
    from viloapp.core.plugin_system.service_proxy_impl import PermissionAwareServiceProxy

    # Create mock services
    mock_service = Mock(spec=IService)
    mock_service.get_service_id.return_value = "filesystem"
    services = {"filesystem": mock_service}

    # Create permission manager (no permissions granted)
    permission_manager = PermissionManager()

    # Create permission-aware proxy
    proxy = PermissionAwareServiceProxy(
        services=services, permission_manager=permission_manager, plugin_id="test-plugin"
    )

    # Mock logging
    with patch("core.plugin_system.service_proxy_impl.logger") as mock_logger:
        # Try to access service without permission
        service = proxy.get_service("filesystem")
        assert service is None

        # Should log the permission denial
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "Permission denied" in call_args
        assert "test-plugin" in call_args
        assert "filesystem" in call_args
