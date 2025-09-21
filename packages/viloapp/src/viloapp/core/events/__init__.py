"""
Event system for decoupling architectural layers.

This module provides the event bus and related patterns for breaking circular
dependencies between services and UI layers.
"""

__all__ = ["EventBus", "WorkspaceEvent", "PaneEvent", "TabEvent"]

from .event_bus import EventBus
from .events import PaneEvent, TabEvent, WorkspaceEvent
