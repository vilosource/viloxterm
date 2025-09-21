"""Core data models for workspace state management.

These models represent pure data with no Qt dependencies, following the
architectural principle of separation of concerns.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from .base import OperationResult


class WidgetType(Enum):
    """Types of widgets that can be hosted in panes."""
    TERMINAL = "terminal"
    EDITOR = "editor"
    BROWSER = "browser"
    SETTINGS = "settings"
    EMPTY = "empty"


@dataclass
class PaneState:
    """Pure data representation of a pane.

    A pane is a container that holds a widget. It has an ID, a widget type,
    and maintains the widget's state as serializable data.
    """
    id: str
    widget_type: WidgetType
    widget_state: Dict[str, Any]
    is_active: bool

    def __post_init__(self):
        """Ensure widget_state is not None."""
        if self.widget_state is None:
            self.widget_state = {}


@dataclass
class SplitConfiguration:
    """Configuration for a split layout."""
    orientation: str  # "horizontal" or "vertical"
    ratio: float = 0.5
    left_pane_id: Optional[str] = None
    right_pane_id: Optional[str] = None

    def __post_init__(self):
        """Validate split configuration."""
        if self.orientation not in ("horizontal", "vertical"):
            raise ValueError(f"Invalid orientation: {self.orientation}")
        if not 0.1 <= self.ratio <= 0.9:
            raise ValueError(f"Invalid ratio: {self.ratio}")


@dataclass
class TabState:
    """Pure data representation of a tab.

    A tab contains a pane tree structure and tracks which pane is currently active.
    The pane_tree represents the hierarchical split layout as serializable data.
    """
    id: str
    name: str
    pane_tree: Dict[str, Any]  # Serialized tree structure
    active_pane_id: str
    panes: Dict[str, PaneState] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure required fields are not None."""
        if self.pane_tree is None:
            self.pane_tree = {}
        if self.panes is None:
            self.panes = {}


@dataclass
class WorkspaceState:
    """Pure data representation of the entire workspace.

    This is the root state object that contains all tabs and tracks
    which tab is currently active.
    """
    tabs: List[TabState] = field(default_factory=list)
    active_tab_index: int = 0

    def can_close_tab(self, index: int) -> OperationResult:
        """Business rule: Can't close the last remaining tab.

        Args:
            index: Index of tab to close

        Returns:
            OperationResult indicating if tab can be closed
        """
        if index < 0 or index >= len(self.tabs):
            return OperationResult.error_result(f"Invalid tab index: {index}")
        if len(self.tabs) <= 1:
            return OperationResult.error_result("Cannot close the last remaining tab")
        return OperationResult.success_result()

    def can_split_pane(self, pane_id: str) -> OperationResult:
        """Business rule: Can only split existing panes.

        Args:
            pane_id: ID of pane to split

        Returns:
            OperationResult indicating if pane can be split
        """
        if not self.tabs:
            return OperationResult.error_result("No tabs available")

        current_tab = self.tabs[self.active_tab_index]
        if pane_id not in current_tab.panes:
            return OperationResult.error_result(f"Pane not found: {pane_id}")

        return OperationResult.success_result()

    def get_active_tab(self) -> Optional[TabState]:
        """Get the currently active tab.

        Returns:
            Active tab or None if no tabs exist
        """
        if not self.tabs or self.active_tab_index >= len(self.tabs):
            return None
        return self.tabs[self.active_tab_index]

    def get_active_pane(self) -> Optional[PaneState]:
        """Get the currently active pane in the active tab.

        Returns:
            Active pane or None if no active pane
        """
        active_tab = self.get_active_tab()
        if not active_tab:
            return None
        return active_tab.panes.get(active_tab.active_pane_id)