"""Tests for event system."""

from viloapp_sdk.events import EventBus, PluginEvent, EventType, EventPriority
import time


def test_event_bus_subscribe_emit():
    """Test basic event subscription and emission."""
    bus = EventBus()
    received_events = []

    def handler(event):
        received_events.append(event)

    # Subscribe to event
    bus.subscribe(EventType.PLUGIN_LOADED, handler)

    # Emit event
    event = PluginEvent(
        type=EventType.PLUGIN_LOADED, source="test", data={"plugin_id": "test-plugin"}
    )
    bus.emit(event)

    # Check event was received
    assert len(received_events) == 1
    assert received_events[0].data["plugin_id"] == "test-plugin"


def test_event_filtering():
    """Test event filtering."""
    bus = EventBus()
    received_events = []

    def handler(event):
        received_events.append(event)

    # Subscribe with filter
    def filter_func(event):
        return event.data.get("important", False)

    bus.subscribe(EventType.CUSTOM, handler, filter_func=filter_func)

    # Emit non-matching event
    event1 = PluginEvent(type=EventType.CUSTOM, source="test", data={"important": False})
    bus.emit(event1)

    # Emit matching event
    event2 = PluginEvent(type=EventType.CUSTOM, source="test", data={"important": True})
    bus.emit(event2)

    # Only matching event should be received
    assert len(received_events) == 1
    assert received_events[0].data["important"]


def test_event_priority():
    """Test event priority handling."""
    bus = EventBus()
    call_order = []

    def handler_low(event):
        call_order.append("low")

    def handler_normal(event):
        call_order.append("normal")

    def handler_high(event):
        call_order.append("high")

    # Subscribe with different priorities
    bus.subscribe(EventType.CUSTOM, handler_low, priority=EventPriority.LOW)
    bus.subscribe(EventType.CUSTOM, handler_normal, priority=EventPriority.NORMAL)
    bus.subscribe(EventType.CUSTOM, handler_high, priority=EventPriority.HIGH)

    # Emit event
    event = PluginEvent(type=EventType.CUSTOM, source="test")
    bus.emit(event)

    # Check call order (high priority first)
    assert call_order == ["high", "normal", "low"]


def test_event_unsubscribe():
    """Test event unsubscription."""
    bus = EventBus()
    received_count = 0

    def handler(event):
        nonlocal received_count
        received_count += 1

    # Subscribe to event
    subscription = bus.subscribe(EventType.CUSTOM, handler)

    # Emit event
    event = PluginEvent(type=EventType.CUSTOM, source="test")
    bus.emit(event)
    assert received_count == 1

    # Unsubscribe
    bus.unsubscribe(subscription)

    # Emit event again
    bus.emit(event)
    assert received_count == 1  # Should not increase


def test_event_history():
    """Test event history."""
    bus = EventBus()

    # Emit some events
    for i in range(5):
        event = PluginEvent(type=EventType.CUSTOM, source="test", data={"index": i})
        bus.emit(event)
        time.sleep(0.01)  # Ensure different timestamps

    # Get history
    history = bus.get_history(limit=3)
    assert len(history) == 3

    # Check filtering
    event = PluginEvent(type=EventType.PLUGIN_LOADED, source="other")
    bus.emit(event)

    history = bus.get_history(event_type=EventType.CUSTOM)
    assert all(e.type == EventType.CUSTOM for e in history)

    history = bus.get_history(source="other")
    assert all(e.source == "other" for e in history)
