"""Tests for SDK testing utilities."""

from unittest.mock import Mock

from viloapp_sdk.testing.mock_host import (
    MockPluginHost, MockService, MockCommandService, MockConfigurationService,
    MockWorkspaceService, MockThemeService, MockNotificationService,
    create_mock_plugin_context, create_mock_service_proxy
)
from viloapp_sdk.testing.fixtures import *  # Import all fixtures
from viloapp_sdk.context import IPluginContext
from viloapp_sdk.service import ServiceProxy
from viloapp_sdk.events import EventBus, EventType


class TestMockService:
    """Test the base MockService class."""

    def test_mock_service_creation(self):
        """Test creating a mock service."""
        service = MockService("test-service", "2.0.0")

        assert service.get_service_id() == "test-service"
        assert service.get_service_version() == "2.0.0"
        assert hasattr(service, 'mock')
        assert isinstance(service.mock, Mock)

    def test_mock_service_defaults(self):
        """Test mock service with default version."""
        service = MockService("test-service")

        assert service.get_service_id() == "test-service"
        assert service.get_service_version() == "1.0.0"


class TestMockCommandService:
    """Test the MockCommandService implementation."""

    def test_command_service_creation(self):
        """Test creating a mock command service."""
        service = MockCommandService()

        assert service.get_service_id() == "command"
        assert service.get_service_version() == "1.0.0"

    def test_register_and_execute_command(self):
        """Test registering and executing commands."""
        service = MockCommandService()

        def test_handler(arg1=None, arg2=None):
            return f"result:{arg1}:{arg2}"

        # Register command
        service.register_command("test.command", test_handler)

        # Execute command (should call handler directly, not mock)
        result = service.execute_command("test.command", arg1="hello", arg2="world")
        assert result == "result:hello:world"

        # Verify register_command mock was called
        service.mock.register_command.assert_called_once_with("test.command", test_handler)
        # execute_command mock should NOT be called for registered commands
        service.mock.execute_command.assert_not_called()

    def test_unregister_command(self):
        """Test unregistering commands."""
        service = MockCommandService()

        # Register and then unregister
        service.register_command("test.command", lambda: "result")
        service.unregister_command("test.command")

        # Should fallback to mock
        service.execute_command("test.command")
        service.mock.execute_command.assert_called_with("test.command")

    def test_unknown_command_delegates_to_mock(self):
        """Test that unknown commands delegate to mock."""
        service = MockCommandService()

        # Execute unknown command
        service.execute_command("unknown.command", arg="value")

        # Should delegate to mock
        service.mock.execute_command.assert_called_once_with("unknown.command", arg="value")


class TestMockConfigurationService:
    """Test the MockConfigurationService implementation."""

    def test_configuration_service_creation(self):
        """Test creating a mock configuration service."""
        service = MockConfigurationService()

        assert service.get_service_id() == "configuration"
        assert service.get_service_version() == "1.0.0"

    def test_get_set_configuration(self):
        """Test getting and setting configuration values."""
        service = MockConfigurationService()

        # Test default value
        assert service.get("test.key", "default") == "default"

        # Set and get value
        service.set("test.key", "test_value")
        assert service.get("test.key") == "test_value"

        # Verify mock calls
        service.mock.get.assert_called()
        service.mock.set.assert_called_with("test.key", "test_value")

    def test_configuration_change_listeners(self):
        """Test configuration change listeners."""
        service = MockConfigurationService()

        # Track changes
        changes = []
        def listener(key, new_value, old_value):
            changes.append((key, new_value, old_value))

        # Register listener
        service.on_change("test.key", listener)

        # Change value
        service.set("test.key", "new_value")

        # Verify listener was called
        assert len(changes) == 1
        assert changes[0] == ("test.key", "new_value", None)

        # Change again
        service.set("test.key", "newer_value")
        assert len(changes) == 2
        assert changes[1] == ("test.key", "newer_value", "new_value")


class TestMockWorkspaceService:
    """Test the MockWorkspaceService implementation."""

    def test_workspace_service_creation(self):
        """Test creating a mock workspace service."""
        service = MockWorkspaceService()

        assert service.get_service_id() == "workspace"
        assert service.get_service_version() == "1.0.0"

    def test_open_file(self):
        """Test opening files."""
        service = MockWorkspaceService()

        # Open files
        service.open_file("/path/to/file1.py")
        service.open_file("/path/to/file2.py")
        service.open_file("/path/to/file1.py")  # Open same file again

        # Verify files are tracked
        assert "/path/to/file1.py" in service._open_files
        assert "/path/to/file2.py" in service._open_files
        assert len(service._open_files) == 2  # No duplicates

        # Verify mock calls
        assert service.mock.open_file.call_count == 3

    def test_active_editor(self):
        """Test active editor functionality."""
        service = MockWorkspaceService()

        # Initially no active editor
        assert service.get_active_editor() is None

        # Set active editor
        mock_editor = Mock()
        service._active_editor = mock_editor

        assert service.get_active_editor() == mock_editor


class TestMockThemeService:
    """Test the MockThemeService implementation."""

    def test_theme_service_creation(self):
        """Test creating a mock theme service."""
        service = MockThemeService()

        assert service.get_service_id() == "theme"
        assert service.get_service_version() == "1.0.0"

    def test_get_theme_and_colors(self):
        """Test getting theme and colors."""
        service = MockThemeService()

        # Get theme
        theme = service.get_current_theme()
        assert theme["name"] == "test-theme"
        assert "colors" in theme

        # Get colors
        assert service.get_color("background") == "#ffffff"
        assert service.get_color("foreground") == "#000000"
        assert service.get_color("unknown") == "#000000"  # Default

    def test_theme_change_listeners(self):
        """Test theme change listeners."""
        service = MockThemeService()

        # Track changes
        theme_changes = []
        def listener(theme):
            theme_changes.append(theme)

        # Register listener
        service.on_theme_changed(listener)

        # Change theme
        new_theme = {"name": "dark-theme", "colors": {"background": "#000000"}}
        service.set_theme(new_theme)

        # Verify listener was called
        assert len(theme_changes) == 1
        assert theme_changes[0] == new_theme

        # Verify theme was updated
        assert service.get_current_theme() == new_theme


class TestMockNotificationService:
    """Test the MockNotificationService implementation."""

    def test_notification_service_creation(self):
        """Test creating a mock notification service."""
        service = MockNotificationService()

        assert service.get_service_id() == "notification"
        assert service.get_service_version() == "1.0.0"
        assert len(service.notifications) == 0

    def test_show_notifications(self):
        """Test showing different types of notifications."""
        service = MockNotificationService()

        # Show different notification types
        service.info("Info message", "Info Title")
        service.warning("Warning message")
        service.error("Error message", "Error Title")

        # Verify notifications were recorded
        assert len(service.notifications) == 3

        assert service.notifications[0] == {
            "type": "info", "message": "Info message", "title": "Info Title"
        }
        assert service.notifications[1] == {
            "type": "warning", "message": "Warning message", "title": None
        }
        assert service.notifications[2] == {
            "type": "error", "message": "Error message", "title": "Error Title"
        }

        # Verify mock calls
        service.mock.info.assert_called_once_with("Info message", "Info Title")
        service.mock.warning.assert_called_once_with("Warning message", None)
        service.mock.error.assert_called_once_with("Error message", "Error Title")


class TestMockPluginHost:
    """Test the MockPluginHost class."""

    def test_plugin_host_creation(self):
        """Test creating a mock plugin host."""
        host = MockPluginHost("test-plugin")

        assert host.plugin_id == "test-plugin"
        assert len(host._services) == 5  # Default services

        # Verify default services
        assert "command" in host._services
        assert "configuration" in host._services
        assert "workspace" in host._services
        assert "theme" in host._services
        assert "notification" in host._services

    def test_plugin_host_default_services(self):
        """Test default services are properly set up."""
        host = MockPluginHost()

        # Test service access
        assert isinstance(host.command_service, MockCommandService)
        assert isinstance(host.configuration_service, MockConfigurationService)
        assert isinstance(host.workspace_service, MockWorkspaceService)
        assert isinstance(host.theme_service, MockThemeService)
        assert isinstance(host.notification_service, MockNotificationService)

    def test_add_remove_services(self):
        """Test adding and removing custom services."""
        host = MockPluginHost()

        # Add custom service
        custom_service = MockService("custom", "1.0.0")
        host.add_service(custom_service)

        assert host.get_service("custom") == custom_service
        assert len(host._services) == 6

        # Remove service
        host.remove_service("custom")
        assert host.get_service("custom") is None
        assert len(host._services) == 5

    def test_create_context(self):
        """Test creating plugin context."""
        host = MockPluginHost("test-plugin")

        context = host.create_context()

        assert isinstance(context, IPluginContext)
        assert context.get_plugin_id() == "test-plugin"
        assert context.get_plugin_path().exists()
        assert context.get_data_path().exists()
        assert isinstance(context.get_service_proxy(), ServiceProxy)
        assert isinstance(context.get_event_bus(), EventBus)

    def test_context_manager(self):
        """Test using host as context manager."""
        with MockPluginHost("test-plugin") as host:
            temp_dir = host.get_temp_dir()
            assert temp_dir.exists()

        # After context exit, temp dir should be cleaned up
        assert not temp_dir.exists()

    def test_event_handling(self):
        """Test event handling utilities."""
        host = MockPluginHost()

        # Emit event
        host.emit_event(EventType.PLUGIN_ACTIVATED, {"plugin_id": "test"})

        # Check event was emitted
        assert host.assert_event_emitted(EventType.PLUGIN_ACTIVATED)

        # Get last event
        last_event = host.get_last_event(EventType.PLUGIN_ACTIVATED)
        assert last_event is not None
        assert last_event.type == EventType.PLUGIN_ACTIVATED
        assert last_event.data["plugin_id"] == "test"

    def test_reset_mocks(self):
        """Test resetting all mock call histories."""
        host = MockPluginHost()

        # Make some calls
        host.command_service.execute_command("test")
        host.configuration_service.get("test")

        # Verify calls were made
        assert host.command_service.mock.execute_command.called
        assert host.configuration_service.mock.get.called

        # Reset mocks
        host.reset_mocks()

        # Verify call histories were reset
        assert not host.command_service.mock.execute_command.called
        assert not host.configuration_service.mock.get.called


class TestUtilityFunctions:
    """Test utility functions."""

    def test_create_mock_plugin_context(self):
        """Test create_mock_plugin_context utility function."""
        context = create_mock_plugin_context("test-plugin")

        assert isinstance(context, IPluginContext)
        assert context.get_plugin_id() == "test-plugin"

    def test_create_mock_plugin_context_with_services(self):
        """Test create_mock_plugin_context with custom services."""
        custom_service = MockService("custom", "1.0.0")
        services = {"custom": custom_service}

        context = create_mock_plugin_context("test-plugin", services=services)

        # Should have both default and custom services
        service_proxy = context.get_service_proxy()
        assert service_proxy.get_service("custom") == custom_service
        assert service_proxy.get_service("command") is not None

    def test_create_mock_service_proxy(self):
        """Test create_mock_service_proxy utility function."""
        proxy = create_mock_service_proxy()

        assert isinstance(proxy, ServiceProxy)
        assert proxy.get_service("command") is not None
        assert proxy.get_service("configuration") is not None

    def test_create_mock_service_proxy_with_services(self):
        """Test create_mock_service_proxy with custom services."""
        custom_service = MockService("custom", "1.0.0")
        services = {"custom": custom_service}

        proxy = create_mock_service_proxy(services)

        assert proxy.get_service("custom") == custom_service
        assert proxy.get_service("command") is None  # Only custom services