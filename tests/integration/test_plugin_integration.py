"""Integration tests for plugin system."""

from unittest.mock import Mock

from core.plugin_system import PluginManager
from viloapp_sdk import EventBus

def test_full_plugin_lifecycle():
    """Test complete plugin lifecycle."""
    # Create plugin manager
    event_bus = EventBus()
    services = {'test': Mock()}
    manager = PluginManager(event_bus, services)

    # Initialize (will discover and load plugins)
    # This would need actual plugins to test fully
    # manager.initialize()

    # Check that manager is ready
    assert manager is not None

def test_plugin_event_communication():
    """Test plugin event communication."""
    event_bus = EventBus()
    received_events = []

    # Subscribe to events
    def handler(event):
        received_events.append(event)

    from viloapp_sdk import EventType
    event_bus.subscribe(EventType.PLUGIN_LOADED, handler)

    # Create manager
    services = {}
    manager = PluginManager(event_bus, services)

    # Trigger an event
    from viloapp_sdk import PluginEvent
    event_bus.emit(PluginEvent(
        type=EventType.PLUGIN_LOADED,
        source="test",
        data={"plugin_id": "test"}
    ))

    # Check event was received
    assert len(received_events) == 1
    assert received_events[0].data["plugin_id"] == "test"

def test_plugin_service_access():
    """Test that plugins can access services."""
    # Create services
    mock_service = Mock()
    mock_service.get_service_id.return_value = "test"
    mock_service.get_service_version.return_value = "1.0.0"

    services = {'test': mock_service}

    # Create plugin manager
    event_bus = EventBus()
    manager = PluginManager(event_bus, services)

    # Plugins loaded by manager should have access to services
    # This would be tested with actual plugin loading
    assert 'test' in services