"""Examples of using the SDK testing utilities.

This module provides examples showing how to use the testing utilities
to write comprehensive tests for your plugins.
"""

from viloapp_sdk import IPlugin, PluginMetadata, PluginCapability
from viloapp_sdk.context import IPluginContext
from viloapp_sdk.events import EventType, PluginEvent
from viloapp_sdk.testing import MockPluginHost
from viloapp_sdk.testing.fixtures import *


class ExamplePlugin(IPlugin):
    """Example plugin for demonstrating testing utilities."""

    def __init__(self):
        self.activated = False
        self.context = None
        self.commands_executed = []

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="example-plugin",
            name="Example Plugin",
            version="1.0.0",
            description="An example plugin for testing",
            author="ViloxTerm Team",
            capabilities=[PluginCapability.COMMANDS, PluginCapability.WIDGETS]
        )

    def activate(self, context: IPluginContext) -> None:
        self.activated = True
        self.context = context

        # Register a command
        command_service = context.get_service("command")
        if command_service:
            command_service.register_command("example.hello", self._hello_command)

        # Subscribe to events
        context.subscribe_event(EventType.SETTINGS_CHANGED, self._on_settings_changed)

    def deactivate(self) -> None:
        self.activated = False
        if self.context:
            # Unregister command
            command_service = self.context.get_service("command")
            if command_service:
                command_service.unregister_command("example.hello")

    def _hello_command(self, name="World"):
        """Example command that says hello."""
        self.commands_executed.append(f"hello:{name}")
        return f"Hello, {name}!"

    def _on_settings_changed(self, event: PluginEvent):
        """Handle settings changes."""
        self.commands_executed.append(f"settings_changed:{event.data}")


# Example 1: Basic plugin testing using MockPluginHost
def test_plugin_with_mock_host():
    """Example of testing a plugin using MockPluginHost directly."""
    # Create a mock host
    with MockPluginHost("example-plugin") as host:
        # Create plugin and context
        plugin = ExamplePlugin()
        context = host.create_context()

        # Test activation
        plugin.activate(context)
        assert plugin.activated
        assert plugin.context == context

        # Test command execution
        command_service = context.get_service("command")
        result = command_service.execute_command("example.hello", name="Test")
        assert result == "Hello, Test!"
        assert "hello:Test" in plugin.commands_executed

        # Test event handling
        host.emit_event(EventType.SETTINGS_CHANGED, {"key": "value"})
        assert "settings_changed:{'key': 'value'}" in plugin.commands_executed

        # Test deactivation
        plugin.deactivate()
        assert not plugin.activated


# Example 2: Using pytest fixtures
def test_plugin_with_fixtures(mock_plugin_host, mock_services):
    """Example of testing a plugin using pytest fixtures."""
    plugin = ExamplePlugin()

    # Create context with specific configuration
    context = mock_plugin_host.create_context(
        configuration={"debug": True, "log_level": "INFO"}
    )

    # Test activation
    plugin.activate(context)
    assert plugin.activated

    # Verify services are available
    assert context.get_service("command") is not None
    assert context.get_service("configuration") is not None

    # Test configuration access
    config = context.get_configuration()
    assert config["debug"] is True
    assert config["log_level"] == "INFO"


# Example 3: Testing service interactions
def test_service_interactions(mock_plugin_host):
    """Example of testing plugin interactions with services."""
    plugin = ExamplePlugin()
    context = mock_plugin_host.create_context()

    # Activate plugin
    plugin.activate(context)

    # Test configuration service
    config_service = context.get_service("configuration")
    config_service.set("example.setting", "test_value")
    assert config_service.get("example.setting") == "test_value"

    # Test notification service
    notification_service = context.get_service("notification")
    notification_service.info("Test message", "Test Title")

    # Verify notification was recorded
    assert len(notification_service.notifications) == 1
    assert notification_service.notifications[0]["message"] == "Test message"

    # Test workspace service
    workspace_service = context.get_service("workspace")
    workspace_service.open_file("/path/to/test.py")

    # Verify mock was called
    workspace_service.mock.open_file.assert_called_with("/path/to/test.py")


# Example 4: Testing with custom services
def test_plugin_with_custom_service(mock_plugin_host):
    """Example of testing with custom mock services."""
    from viloapp_sdk.testing.mock_host import MockService

    # Create custom service
    class CustomService(MockService):
        def __init__(self):
            super().__init__("custom", "1.0.0")
            self.data = {}

        def store_data(self, key, value):
            self.data[key] = value
            self.mock.store_data(key, value)

        def get_data(self, key):
            value = self.data.get(key)
            self.mock.get_data(key)
            return value

    # Add custom service to host
    custom_service = CustomService()
    mock_plugin_host.add_service(custom_service)

    plugin = ExamplePlugin()
    context = mock_plugin_host.create_context()

    # Test plugin can access custom service
    custom = context.get_service("custom")
    assert custom is not None
    assert custom == custom_service

    # Test custom service functionality
    custom.store_data("test_key", "test_value")
    assert custom.get_data("test_key") == "test_value"


# Example 5: Testing error conditions
def test_plugin_error_handling(mock_plugin_host):
    """Example of testing plugin error handling."""
    plugin = ExamplePlugin()
    context = mock_plugin_host.create_context()

    # Test activation with missing service
    mock_plugin_host.remove_service("command")
    plugin.activate(context)

    # Plugin should still activate but handle missing service gracefully
    assert plugin.activated
    assert context.get_service("command") is None


# Example 6: Testing with integrated environment fixture
def test_plugin_with_integrated_environment(integrated_plugin_environment):
    """Example using the integrated environment fixture."""
    env = integrated_plugin_environment

    plugin = env["plugin"]
    context = env["context"]
    host = env["host"]

    # Test plugin in full environment
    plugin.activate(context)
    assert plugin.activated

    # Test event handling
    event_bus = env["event_bus"]
    events_received = []
    event_bus.subscribe(EventType.PLUGIN_ACTIVATED, lambda e: events_received.append(e))

    # Emit event
    host.emit_event(EventType.PLUGIN_ACTIVATED, {"plugin_id": plugin.get_metadata().id})

    # Verify event was received
    assert len(events_received) == 1
    assert events_received[0].data["plugin_id"] == "sample-plugin"


# Example 7: Testing widget functionality (requires implementing IWidget)
def test_widget_factory_example():
    """Example of testing a widget factory using testing utilities."""
    from viloapp_sdk import IWidget
    from PySide6.QtWidgets import QWidget, QLabel

    class ExampleWidgetFactory(IWidget):
        def __init__(self):
            self.instances = {}

        def get_widget_id(self) -> str:
            return "example-widget"

        def get_title(self) -> str:
            return "Example Widget"

        def get_icon(self) -> str:
            return "example-icon"

        def create_instance(self, instance_id: str) -> QWidget:
            widget = QLabel(f"Example Widget {instance_id}")
            self.instances[instance_id] = widget
            return widget

        def destroy_instance(self, instance_id: str) -> None:
            if instance_id in self.instances:
                widget = self.instances[instance_id]
                widget.deleteLater()
                del self.instances[instance_id]

        def handle_command(self, command: str, args: dict) -> any:
            if command == "set_text":
                text = args.get("text", "")
                for widget in self.instances.values():
                    widget.setText(text)
                return f"Set text to: {text}"
            return None

        def get_state(self) -> dict:
            return {"instance_count": len(self.instances)}

        def restore_state(self, state: dict) -> None:
            # In a real implementation, you'd restore widgets
            pass

    # Test widget factory
    factory = ExampleWidgetFactory()

    assert factory.get_widget_id() == "example-widget"
    assert factory.get_title() == "Example Widget"

    # Create widget instance
    widget = factory.create_instance("test-1")
    assert widget is not None
    assert "test-1" in factory.instances

    # Test command handling
    result = factory.handle_command("set_text", {"text": "Hello World"})
    assert result == "Set text to: Hello World"

    # Test state management
    state = factory.get_state()
    assert state["instance_count"] == 1

    # Destroy instance
    factory.destroy_instance("test-1")
    assert "test-1" not in factory.instances


if __name__ == "__main__":
    # This allows running examples directly for demonstration
    print("Running SDK testing utilities examples...")

    # Run basic host example
    test_plugin_with_mock_host()
    print("✓ Basic MockPluginHost example passed")

    # Run widget example (requires QApplication)
    try:
        from PySide6.QtWidgets import QApplication
        import sys
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        test_widget_factory_example()
        print("✓ Widget factory example passed")
    except ImportError:
        print("⚠ Skipping widget example (PySide6 not available)")
    except Exception as e:
        print(f"⚠ Widget example failed: {e}")

    print("All examples completed successfully!")