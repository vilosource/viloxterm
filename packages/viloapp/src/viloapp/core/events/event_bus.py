#!/usr/bin/env python3
"""
Event Bus for breaking circular dependencies.

The EventBus provides publish-subscribe pattern to allow services to
notify UI changes without directly calling UI methods.
"""

import logging
from collections import defaultdict
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class EventBus:
    """
    Singleton Event Bus for decoupling architectural layers.

    Services publish events, UI components subscribe to events.
    This breaks circular dependencies by ensuring one-way data flow:
    UI → Command → Service → Model → Event → UI
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
            self._initialized = True

    def subscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: The type of event to listen for
            callback: Function to call when event is published
        """
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to event: {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: The type of event to stop listening for
            callback: The callback function to remove
        """
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
            logger.debug(f"Unsubscribed from event: {event_type}")

    def publish(self, event_type: str, data: Any = None) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event_type: The type of event being published
            data: Optional data to send with the event
        """
        logger.debug(f"Publishing event: {event_type} with data: {data}")

        for callback in self._subscribers[event_type]:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in event callback for {event_type}: {e}")

    def clear_subscribers(self, event_type: str = None) -> None:
        """
        Clear subscribers for a specific event type or all events.

        Args:
            event_type: Specific event type to clear, or None for all events
        """
        if event_type:
            self._subscribers[event_type].clear()
            logger.debug(f"Cleared subscribers for event: {event_type}")
        else:
            self._subscribers.clear()
            logger.debug("Cleared all event subscribers")

    def get_subscriber_count(self, event_type: str) -> int:
        """
        Get the number of subscribers for an event type.

        Args:
            event_type: The event type to check

        Returns:
            Number of subscribers
        """
        return len(self._subscribers[event_type])


# Global instance for easy access
event_bus = EventBus()
