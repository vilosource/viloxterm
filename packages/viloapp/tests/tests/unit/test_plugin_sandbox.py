"""Tests for plugin sandboxing."""

from unittest.mock import Mock, patch


def test_plugin_sandbox_creation():
    """Test PluginSandbox creation."""
    from viloapp.core.plugin_system.security import PluginSandbox

    sandbox = PluginSandbox(plugin_id="test-plugin")
    assert sandbox is not None
    assert sandbox.plugin_id == "test-plugin"


def test_plugin_sandbox_isolation():
    """Test basic plugin isolation."""
    from viloapp.core.plugin_system.security import PluginSandbox

    sandbox = PluginSandbox(plugin_id="test-plugin")

    # Test that sandbox provides isolated environment
    isolated_env = sandbox.get_isolated_environment()
    assert isolated_env is not None
    assert isinstance(isolated_env, dict)


def test_plugin_sandbox_with_permissions():
    """Test sandbox with permission manager."""
    from viloapp.core.plugin_system.security import PermissionManager, PluginSandbox

    permission_manager = PermissionManager()
    sandbox = PluginSandbox(plugin_id="test-plugin", permission_manager=permission_manager)

    assert sandbox.permission_manager is permission_manager


def test_plugin_sandbox_with_resource_limiter():
    """Test sandbox with resource limiter."""
    from viloapp.core.plugin_system.security import PluginSandbox, ResourceLimiter, ResourceType

    limits = {ResourceType.MEMORY: 100 * 1024 * 1024}
    resource_limiter = ResourceLimiter(plugin_id="test-plugin", limits=limits)

    sandbox = PluginSandbox(plugin_id="test-plugin", resource_limiter=resource_limiter)

    assert sandbox.resource_limiter is resource_limiter


def test_plugin_sandbox_crash_recovery():
    """Test crash recovery mechanism."""
    from viloapp.core.plugin_system.security import PluginSandbox

    crash_callback = Mock()

    sandbox = PluginSandbox(plugin_id="test-plugin", crash_callback=crash_callback)

    # Simulate a plugin crash
    exception = Exception("Plugin crashed")
    sandbox.handle_plugin_crash(exception)

    # Crash callback should be called
    crash_callback.assert_called_once_with("test-plugin", exception)


def test_plugin_sandbox_restart_policy():
    """Test plugin restart policies."""
    from viloapp.core.plugin_system.security import PluginSandbox, RestartPolicy

    sandbox = PluginSandbox(plugin_id="test-plugin", restart_policy=RestartPolicy.ALWAYS)

    assert sandbox.restart_policy == RestartPolicy.ALWAYS

    # Test automatic restart after crash
    restart_callback = Mock()
    sandbox.restart_callback = restart_callback

    exception = Exception("Plugin crashed")
    sandbox.handle_plugin_crash(exception)

    # Should attempt restart for ALWAYS policy
    restart_callback.assert_called_once_with("test-plugin")


def test_plugin_sandbox_no_restart_policy():
    """Test no restart policy."""
    from viloapp.core.plugin_system.security import PluginSandbox, RestartPolicy

    sandbox = PluginSandbox(plugin_id="test-plugin", restart_policy=RestartPolicy.NEVER)

    restart_callback = Mock()
    sandbox.restart_callback = restart_callback

    exception = Exception("Plugin crashed")
    sandbox.handle_plugin_crash(exception)

    # Should not attempt restart for NEVER policy
    restart_callback.assert_not_called()


def test_plugin_sandbox_restart_limit():
    """Test restart attempt limits."""
    from viloapp.core.plugin_system.security import PluginSandbox, RestartPolicy

    sandbox = PluginSandbox(
        plugin_id="test-plugin", restart_policy=RestartPolicy.ON_FAILURE, max_restart_attempts=2
    )

    restart_callback = Mock()
    sandbox.restart_callback = restart_callback

    # Simulate multiple crashes
    exception = Exception("Plugin crashed")

    for _i in range(3):
        sandbox.handle_plugin_crash(exception)

    # Should only restart up to the limit
    assert restart_callback.call_count == 2


def test_plugin_sandbox_error_logging():
    """Test that sandbox logs errors properly."""
    from viloapp.core.plugin_system.security import PluginSandbox

    with patch("core.plugin_system.security.sandbox.logger") as mock_logger:
        sandbox = PluginSandbox(plugin_id="test-plugin")

        exception = Exception("Test error")
        sandbox.handle_plugin_crash(exception)

        # Should log the error
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "test-plugin" in call_args
        assert "crashed" in call_args.lower()


def test_plugin_sandbox_environment_variables():
    """Test environment variable isolation."""
    from viloapp.core.plugin_system.security import PluginSandbox

    sandbox = PluginSandbox(plugin_id="test-plugin")

    # Set some environment variables for the plugin
    plugin_env = {
        "PLUGIN_ID": "test-plugin",
        "PLUGIN_DATA_DIR": "/tmp/test-plugin",
        "RESTRICTED_ACCESS": "false",
    }

    isolated_env = sandbox.get_isolated_environment(plugin_env)

    # Should include plugin-specific variables
    assert isolated_env["PLUGIN_ID"] == "test-plugin"
    assert isolated_env["PLUGIN_DATA_DIR"] == "/tmp/test-plugin"


def test_plugin_sandbox_file_system_isolation():
    """Test file system access restrictions."""
    from viloapp.core.plugin_system.security import PluginSandbox

    sandbox = PluginSandbox(plugin_id="test-plugin")

    # Test allowed paths
    allowed_paths = ["/tmp/test-plugin", "/home/user/.config/viloapp/plugins/test-plugin"]
    sandbox.set_allowed_paths(allowed_paths)

    # Should allow access to specified paths
    assert sandbox.is_path_allowed("/tmp/test-plugin/data.txt")
    assert sandbox.is_path_allowed("/home/user/.config/viloapp/plugins/test-plugin/config.json")

    # Should deny access to other paths
    assert not sandbox.is_path_allowed("/etc/passwd")
    assert not sandbox.is_path_allowed("/home/user/.ssh/id_rsa")


def test_plugin_sandbox_network_isolation():
    """Test network access restrictions."""
    from viloapp.core.plugin_system.security import PluginSandbox

    sandbox = PluginSandbox(plugin_id="test-plugin")

    # Set allowed network destinations
    allowed_hosts = ["api.example.com", "cdn.example.com"]
    sandbox.set_allowed_hosts(allowed_hosts)

    # Should allow access to specified hosts
    assert sandbox.is_host_allowed("api.example.com")
    assert sandbox.is_host_allowed("cdn.example.com")

    # Should deny access to other hosts
    assert not sandbox.is_host_allowed("malicious.com")
    assert not sandbox.is_host_allowed("localhost")


def test_plugin_sandbox_integration():
    """Test full sandbox integration with permissions and resources."""
    from viloapp.core.plugin_system.security import (
        Permission,
        PermissionCategory,
        PermissionManager,
        PermissionScope,
        PluginSandbox,
        ResourceLimiter,
        ResourceType,
    )

    # Create permission manager with filesystem permission
    permission_manager = PermissionManager()
    fs_permission = Permission(PermissionCategory.FILESYSTEM, PermissionScope.READ, "/tmp/*")
    permission_manager.grant_permission("test-plugin", fs_permission)

    # Create resource limiter with a higher limit to avoid false positives
    limits = {ResourceType.MEMORY: 500 * 1024 * 1024}  # 500MB
    resource_limiter = ResourceLimiter(plugin_id="test-plugin", limits=limits)

    # Create sandbox with both
    sandbox = PluginSandbox(
        plugin_id="test-plugin",
        permission_manager=permission_manager,
        resource_limiter=resource_limiter,
    )

    # Test that sandbox enforces both permission and resource constraints
    assert sandbox.has_permission(
        PermissionCategory.FILESYSTEM, PermissionScope.READ, "/tmp/test.txt"
    )
    assert not sandbox.has_permission(
        PermissionCategory.FILESYSTEM, PermissionScope.WRITE, "/tmp/test.txt"
    )

    # Test resource checking
    violation = sandbox.check_resource_limits()
    # Should be None if within limits
    assert violation is None or violation.current_usage <= violation.limit


def test_plugin_sandbox_telemetry():
    """Test sandbox telemetry collection."""
    from viloapp.core.plugin_system.security import PluginSandbox

    sandbox = PluginSandbox(plugin_id="test-plugin")

    # Enable telemetry
    sandbox.enable_telemetry()

    # Simulate some operations
    sandbox.record_operation("file_read", "/tmp/test.txt")
    sandbox.record_operation("network_request", "api.example.com")

    # Get telemetry data
    telemetry = sandbox.get_telemetry()

    assert telemetry["plugin_id"] == "test-plugin"
    assert len(telemetry["operations"]) == 2
    assert any(op["type"] == "file_read" for op in telemetry["operations"])
    assert any(op["type"] == "network_request" for op in telemetry["operations"])


def test_plugin_sandbox_cleanup():
    """Test sandbox cleanup on plugin shutdown."""
    from viloapp.core.plugin_system.security import PluginSandbox

    sandbox = PluginSandbox(plugin_id="test-plugin")

    # Enable telemetry and record some operations
    sandbox.enable_telemetry()
    sandbox.record_operation("test_operation", "test_data")

    # Cleanup should clear all state
    sandbox.cleanup()

    telemetry = sandbox.get_telemetry()
    assert len(telemetry["operations"]) == 0


def test_restart_policy_enum():
    """Test RestartPolicy enumeration."""
    from viloapp.core.plugin_system.security import RestartPolicy

    expected_policies = ["NEVER", "ON_FAILURE", "ALWAYS"]

    for policy in expected_policies:
        assert hasattr(RestartPolicy, policy)


def test_plugin_sandbox_context_manager():
    """Test using sandbox as context manager."""
    from viloapp.core.plugin_system.security import PluginSandbox

    cleanup_called = False

    class TestSandbox(PluginSandbox):
        def cleanup(self):
            nonlocal cleanup_called
            cleanup_called = True
            super().cleanup()

    # Use sandbox as context manager
    with TestSandbox(plugin_id="test-plugin") as sandbox:
        assert sandbox.plugin_id == "test-plugin"

    # Cleanup should be called automatically
    assert cleanup_called
