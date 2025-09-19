"""Event system for plugin communication."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
import time
import uuid
from threading import Lock

class EventType(Enum):
    """Standard event types."""
    # Lifecycle events
    PLUGIN_LOADED = "plugin.loaded"
    PLUGIN_UNLOADED = "plugin.unloaded"
    PLUGIN_ACTIVATED = "plugin.activated"
    PLUGIN_DEACTIVATED = "plugin.deactivated"

    # Widget events
    WIDGET_CREATED = "widget.created"
    WIDGET_DESTROYED = "widget.destroyed"
    WIDGET_FOCUSED = "widget.focused"
    WIDGET_BLURRED = "widget.blurred"
    WIDGET_STATE_CHANGED = "widget.state_changed"

    # System events
    SETTINGS_CHANGED = "settings.changed"
    THEME_CHANGED = "theme.changed"
    LANGUAGE_CHANGED = "language.changed"

    # Command events
    COMMAND_EXECUTED = "command.executed"
    COMMAND_REGISTERED = "command.registered"
    COMMAND_UNREGISTERED = "command.unregistered"

    # Service events
    SERVICE_REGISTERED = "service.registered"
    SERVICE_UNREGISTERED = "service.unregistered"

    # Custom events
    CUSTOM = "custom"

class EventPriority(Enum):
    """Event priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class PluginEvent:
    """Event data structure."""
    type: EventType
    source: str  # Plugin ID or system component
    data: Dict[str, Any] = field(default_factory=dict)
    target: Optional[str] = None  # Target plugin ID or None for broadcast
    priority: EventPriority = EventPriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def is_broadcast(self) -> bool:
        """Check if this is a broadcast event."""
        return self.target is None

    def matches_filter(self, filter_func: Optional[Callable]) -> bool:
        """Check if event matches a filter function."""
        if filter_func is None:
            return True
        try:
            return filter_func(self)
        except Exception:
            return False

class EventSubscription:
    """Represents an event subscription."""

    def __init__(
        self,
        event_type: EventType,
        handler: Callable[[PluginEvent], None],
        filter_func: Optional[Callable[[PluginEvent], bool]] = None,
        priority: EventPriority = EventPriority.NORMAL,
        subscriber_id: Optional[str] = None
    ):
        self.event_type = event_type
        self.handler = handler
        self.filter_func = filter_func
        self.priority = priority
        self.subscriber_id = subscriber_id or str(uuid.uuid4())
        self.active = True

    def handle(self, event: PluginEvent) -> None:
        """Handle an event if it matches the filter."""
        if self.active and event.matches_filter(self.filter_func):
            self.handler(event)

    def unsubscribe(self) -> None:
        """Mark subscription as inactive."""
        self.active = False

class EventBus:
    """Central event bus for plugin communication."""

    def __init__(self):
        self._subscriptions: Dict[EventType, List[EventSubscription]] = {}
        self._lock = Lock()
        self._event_history: List[PluginEvent] = []
        self._history_limit = 1000

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[PluginEvent], None],
        filter_func: Optional[Callable[[PluginEvent], bool]] = None,
        priority: EventPriority = EventPriority.NORMAL,
        subscriber_id: Optional[str] = None
    ) -> EventSubscription:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Function to call when event occurs
            filter_func: Optional filter function
            priority: Subscription priority
            subscriber_id: Optional subscriber ID

        Returns:
            EventSubscription object
        """
        subscription = EventSubscription(
            event_type, handler, filter_func, priority, subscriber_id
        )

        with self._lock:
            if event_type not in self._subscriptions:
                self._subscriptions[event_type] = []

            # Insert sorted by priority (highest first)
            subscriptions = self._subscriptions[event_type]
            insert_idx = len(subscriptions)
            for i, sub in enumerate(subscriptions):
                if sub.priority.value < subscription.priority.value:
                    insert_idx = i
                    break
            subscriptions.insert(insert_idx, subscription)

        return subscription

    def unsubscribe(self, subscription: EventSubscription) -> None:
        """
        Unsubscribe from events.

        Args:
            subscription: Subscription to remove
        """
        subscription.unsubscribe()

        with self._lock:
            if subscription.event_type in self._subscriptions:
                self._subscriptions[subscription.event_type] = [
                    sub for sub in self._subscriptions[subscription.event_type]
                    if sub.subscriber_id != subscription.subscriber_id
                ]

    def emit(self, event: PluginEvent) -> None:
        """
        Emit an event to all subscribers.

        Args:
            event: Event to emit
        """
        # Add to history
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._history_limit:
                self._event_history.pop(0)

        # Get relevant subscriptions
        subscriptions = []
        with self._lock:
            if event.type in self._subscriptions:
                subscriptions = list(self._subscriptions[event.type])

        # Handle event with each subscription
        for subscription in subscriptions:
            if subscription.active:
                try:
                    subscription.handle(event)
                except Exception as e:
                    # Log error but don't stop processing
                    print(f"Error handling event {event.event_id}: {e}")

    def emit_async(self, event: PluginEvent) -> None:
        """
        Emit an event asynchronously.

        Args:
            event: Event to emit
        """
        # This would be implemented with threading or asyncio
        # For now, just emit synchronously
        self.emit(event)

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[PluginEvent]:
        """
        Get event history.

        Args:
            event_type: Filter by event type
            source: Filter by source
            limit: Maximum number of events

        Returns:
            List of events matching criteria
        """
        with self._lock:
            events = list(self._event_history)

        # Apply filters
        if event_type:
            events = [e for e in events if e.type == event_type]
        if source:
            events = [e for e in events if e.source == source]

        return events[-limit:]