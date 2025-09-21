#!/usr/bin/env python3
"""
Event types and data structures for the event bus.

These events allow services to communicate UI changes without directly
calling UI methods, breaking circular dependencies.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class WorkspaceEvent:
    """Base class for workspace-level events."""

    event_type: str
    data: Optional[Dict[str, Any]] = None


@dataclass
class TabEvent(WorkspaceEvent):
    """Events related to tab operations."""

    tab_id: Optional[str] = None
    tab_index: Optional[int] = None
    tab_name: Optional[str] = None

    def __post_init__(self):
        if not self.event_type.startswith("tab."):
            self.event_type = f"tab.{self.event_type}"


@dataclass
class PaneEvent(WorkspaceEvent):
    """Events related to pane operations."""

    pane_id: Optional[str] = None
    orientation: Optional[str] = None
    show_numbers: Optional[bool] = None

    def __post_init__(self):
        if not self.event_type.startswith("pane."):
            self.event_type = f"pane.{self.event_type}"


# Event type constants
class EventTypes:
    """Constants for common event types."""

    # Pane events
    PANE_CLOSED = "pane.closed"
    PANE_SPLIT = "pane.split"
    PANE_FOCUSED = "pane.focused"
    PANE_NUMBERS_SHOW = "pane.numbers.show"
    PANE_NUMBERS_HIDE = "pane.numbers.hide"
    PANE_NUMBERS_TOGGLE = "pane.numbers.toggle"

    # Tab events
    TAB_ADDED = "tab.added"
    TAB_CLOSED = "tab.closed"
    TAB_SWITCHED = "tab.switched"
    TAB_RENAMED = "tab.renamed"

    # Workspace events
    WORKSPACE_LAYOUT_CHANGED = "workspace.layout.changed"
    WORKSPACE_STATE_CHANGED = "workspace.state.changed"
