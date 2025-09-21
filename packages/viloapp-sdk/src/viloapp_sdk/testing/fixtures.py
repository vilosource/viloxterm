"""Pytest fixtures for plugin testing."""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import Mock

from ..context import IPluginContext
from ..service import IService, ServiceProxy
from ..events import EventBus
from ..plugin import PluginMetadata, PluginCapability
from ..interfaces import IPlugin, IMetadata
from .mock_host import (
    MockPluginHost, MockService, MockCommandService, MockConfigurationService,
    MockWorkspaceService, MockThemeService, MockNotificationService,
    create_mock_plugin_context, create_mock_service_proxy
)

# Core testing fixtures

@pytest.fixture
def mock_plugin_host():
    """
    Fixture providing a MockPluginHost for testing.

    Example usage:
        def test_my_plugin(mock_plugin_host):
            context = mock_plugin_host.create_context()
            plugin = MyPlugin()
            plugin.activate(context)
            assert plugin.is_active
    """
    with MockPluginHost() as host:
        yield host

@pytest.fixture
def mock_plugin_context(mock_plugin_host):
    """
    Fixture providing a mock plugin context.

    Example usage:
        def test_plugin_activation(mock_plugin_context):
            plugin = MyPlugin()
            plugin.activate(mock_plugin_context)
            assert plugin.context == mock_plugin_context
    """
    return mock_plugin_host.create_context()

@pytest.fixture
def mock_services():
    """
    Fixture providing a complete set of mock services.

    Returns:
        dict: Dictionary of service_id -> service_instance

    Example usage:
        def test_with_services(mock_services):
            command_service = mock_services["command"]
            command_service.register_command("test", lambda: "result")
            assert command_service.execute_command("test") == "result"
    """
    return {
        "command": MockCommandService(),
        "configuration": MockConfigurationService(),
        "workspace": MockWorkspaceService(),
        "theme": MockThemeService(),
        "notification": MockNotificationService(),
    }

@pytest.fixture
def mock_service_proxy(mock_services):
    """
    Fixture providing a ServiceProxy with mock services.

    Example usage:
        def test_service_access(mock_service_proxy):
            command_service = mock_service_proxy.get_service("command")
            assert command_service is not None
    """
    return ServiceProxy(mock_services)

@pytest.fixture
def mock_event_bus():
    """
    Fixture providing a mock event bus.

    Example usage:
        def test_events(mock_event_bus):
            from viloapp_sdk.events import PluginEvent, EventType

            events = []
            mock_event_bus.subscribe(
                EventType.PLUGIN_ACTIVATED,
                lambda e: events.append(e)
            )

            event = PluginEvent(EventType.PLUGIN_ACTIVATED, "test")
            mock_event_bus.emit(event)
            assert len(events) == 1
    """
    return EventBus()

# Plugin creation fixtures

@pytest.fixture
def sample_plugin_metadata():
    """
    Fixture providing sample plugin metadata.

    Example usage:
        def test_metadata(sample_plugin_metadata):
            assert sample_plugin_metadata.id == "sample-plugin"
            assert sample_plugin_metadata.version == "1.0.0"
    """
    return PluginMetadata(
        id="sample-plugin",
        name="Sample Plugin",
        version="1.0.0",
        description="A sample plugin for testing",
        author="Test Author",
        capabilities=[PluginCapability.WIDGETS, PluginCapability.COMMANDS]
    )

@pytest.fixture
def sample_plugin_class(sample_plugin_metadata):
    """
    Fixture providing a sample plugin class for testing.

    Example usage:
        def test_plugin_behavior(sample_plugin_class, mock_plugin_context):
            plugin = sample_plugin_class()
            plugin.activate(mock_plugin_context)
            assert plugin.activated
    """
    class SamplePlugin(IPlugin):
        def __init__(self):
            self.activated = False
            self.deactivated = False
            self.context = None
            self.command_results = {}

        def get_metadata(self) -> PluginMetadata:
            return sample_plugin_metadata

        def activate(self, context: IPluginContext) -> None:
            self.activated = True
            self.context = context

        def deactivate(self) -> None:
            self.deactivated = True

        def on_command(self, command_id: str, args: Dict[str, Any]) -> Any:
            return self.command_results.get(command_id, f"executed_{command_id}")

    return SamplePlugin

@pytest.fixture
def sample_plugin(sample_plugin_class):
    """
    Fixture providing an instantiated sample plugin.

    Example usage:
        def test_plugin_instance(sample_plugin):
            metadata = sample_plugin.get_metadata()
            assert metadata.name == "Sample Plugin"
    """
    return sample_plugin_class()

# Directory and file fixtures

@pytest.fixture
def temp_plugin_dir():
    """
    Fixture providing a temporary directory for plugin testing.

    Example usage:
        def test_plugin_files(temp_plugin_dir):
            manifest_file = temp_plugin_dir / "plugin.json"
            manifest_file.write_text('{"id": "test"}')
            assert manifest_file.exists()
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="test_plugin_"))
    try:
        yield temp_dir
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

@pytest.fixture
def plugin_manifest_dir(temp_plugin_dir, sample_plugin_metadata):
    """
    Fixture providing a directory with a plugin manifest file.

    Example usage:
        def test_plugin_loading(plugin_manifest_dir):
            manifest_file = plugin_manifest_dir / "plugin.json"
            assert manifest_file.exists()
    """
    import json

    manifest_data = {
        "id": sample_plugin_metadata.id,
        "name": sample_plugin_metadata.name,
        "version": sample_plugin_metadata.version,
        "description": sample_plugin_metadata.description,
        "author": sample_plugin_metadata.author,
        "capabilities": [cap.value for cap in sample_plugin_metadata.capabilities],
        "entry_point": "plugin.SamplePlugin"
    }

    manifest_file = temp_plugin_dir / "plugin.json"
    with open(manifest_file, 'w') as f:
        json.dump(manifest_data, f, indent=2)

    return temp_plugin_dir

# Configuration fixtures

@pytest.fixture
def plugin_configuration():
    """
    Fixture providing sample plugin configuration.

    Example usage:
        def test_configuration(plugin_configuration):
            assert plugin_configuration["debug"] is True
            assert plugin_configuration["theme"] == "dark"
    """
    return {
        "debug": True,
        "theme": "dark",
        "max_connections": 10,
        "features": {
            "autocomplete": True,
            "syntax_highlighting": True
        },
        "paths": {
            "cache": "/tmp/plugin-cache",
            "logs": "/tmp/plugin-logs"
        }
    }

# Service-specific fixtures

@pytest.fixture
def mock_command_service():
    """Fixture providing a mock command service."""
    return MockCommandService()

@pytest.fixture
def mock_configuration_service():
    """Fixture providing a mock configuration service."""
    service = MockConfigurationService()
    # Pre-populate with some common settings
    service.set("editor.fontSize", 14)
    service.set("editor.theme", "dark")
    service.set("workspace.autosave", True)
    return service

@pytest.fixture
def mock_workspace_service():
    """Fixture providing a mock workspace service."""
    return MockWorkspaceService()

@pytest.fixture
def mock_theme_service():
    """Fixture providing a mock theme service."""
    return MockThemeService()

@pytest.fixture
def mock_notification_service():
    """Fixture providing a mock notification service."""
    return MockNotificationService()

# Utility fixtures

@pytest.fixture
def mock_widget():
    """
    Fixture providing a mock widget for testing.

    Example usage:
        def test_widget_creation(mock_widget):
            mock_widget.show()
            mock_widget.show.assert_called_once()
    """
    from unittest.mock import Mock
    widget = Mock()
    widget.isVisible.return_value = True
    widget.size.return_value = (800, 600)
    return widget

# Parameterized fixtures for testing different scenarios

@pytest.fixture(params=[
    {"debug": True, "verbose": False},
    {"debug": False, "verbose": True},
    {"debug": True, "verbose": True},
])
def various_configurations(request):
    """
    Parameterized fixture for testing with different configurations.

    Example usage:
        def test_with_different_configs(various_configurations):
            # This test will run 3 times with different config values
            debug_mode = various_configurations["debug"]
            verbose_mode = various_configurations["verbose"]
    """
    return request.param

@pytest.fixture(params=["command", "configuration", "workspace", "theme", "notification"])
def service_types(request):
    """
    Parameterized fixture for testing different service types.

    Example usage:
        def test_all_services(service_types, mock_services):
            service = mock_services[service_types]
            assert service.get_service_id() == service_types
    """
    return request.param

# Integration testing fixtures

@pytest.fixture
def integrated_plugin_environment(mock_plugin_host, sample_plugin, plugin_configuration):
    """
    Fixture providing a complete integrated environment for plugin testing.

    Returns:
        dict: Contains host, plugin, context, and other testing components

    Example usage:
        def test_full_integration(integrated_plugin_environment):
            env = integrated_plugin_environment
            plugin = env["plugin"]
            context = env["context"]

            plugin.activate(context)
            assert plugin.activated
    """
    context = mock_plugin_host.create_context(configuration=plugin_configuration)

    return {
        "host": mock_plugin_host,
        "plugin": sample_plugin,
        "context": context,
        "configuration": plugin_configuration,
        "services": mock_plugin_host._services,
        "event_bus": mock_plugin_host.get_event_bus()
    }

# Cleanup fixtures

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """
    Auto-use fixture that ensures cleanup after each test.
    This fixture automatically runs after every test to clean up resources.
    """
    yield
    # Cleanup code runs here after each test
    # This is useful for ensuring no state leaks between tests

# Helper fixture for asserting mock calls

@pytest.fixture
def assert_mock_calls():
    """
    Fixture providing helper functions for asserting mock calls.

    Example usage:
        def test_mock_assertions(assert_mock_calls, mock_command_service):
            mock_command_service.execute_command("test")
            assert_mock_calls.assert_called_once(
                mock_command_service.mock.execute_command,
                "test"
            )
    """
    class MockCallAssertions:
        def assert_called_once(self, mock_method, *args, **kwargs):
            mock_method.assert_called_once_with(*args, **kwargs)

        def assert_called_n_times(self, mock_method, n):
            assert mock_method.call_count == n

        def assert_not_called(self, mock_method):
            mock_method.assert_not_called()

    return MockCallAssertions()