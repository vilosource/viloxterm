"""Data Transfer Objects (DTOs) for operations.

These classes define the inputs and outputs for various workspace operations,
ensuring type safety and clear contracts between layers.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .workspace_models import WidgetType


@dataclass
class SplitPaneRequest:
    """Request to split a pane.

    Args:
        pane_id: ID of the pane to split
        orientation: "horizontal" or "vertical" split
        ratio: Split ratio (0.1 to 0.9)
        new_widget_type: Type of widget for the new pane
    """

    pane_id: str
    orientation: str  # "horizontal" or "vertical"
    ratio: float = 0.5
    new_widget_type: WidgetType = WidgetType.EMPTY

    def __post_init__(self):
        """Validate split pane request."""
        if self.orientation not in ("horizontal", "vertical"):
            raise ValueError(f"Invalid orientation: {self.orientation}")
        if not 0.1 <= self.ratio <= 0.9:
            raise ValueError(f"Invalid ratio: {self.ratio}. Must be between 0.1 and 0.9")


@dataclass
class ClosePaneRequest:
    """Request to close a pane.

    Args:
        pane_id: ID of the pane to close
        force: If True, close even if pane has unsaved data
    """

    pane_id: str
    force: bool = False


@dataclass
class TabOperationRequest:
    """Request for tab operations.

    Args:
        operation: Type of operation ("add", "close", "rename", "duplicate")
        tab_index: Index of tab for operations that need it
        tab_name: New name for rename operations
        tab_type: Type of tab for add operations
        widget_type: Initial widget type for new tabs
    """

    operation: str  # "add", "close", "rename", "duplicate"
    tab_index: Optional[int] = None
    tab_name: Optional[str] = None
    tab_type: Optional[str] = None
    widget_type: WidgetType = WidgetType.EMPTY

    def __post_init__(self):
        """Validate tab operation request."""
        valid_operations = {"add", "close", "rename", "duplicate"}
        if self.operation not in valid_operations:
            raise ValueError(
                f"Invalid operation: {self.operation}. Must be one of {valid_operations}"
            )

        # Validate required fields for specific operations
        if self.operation == "close" and self.tab_index is None:
            raise ValueError("tab_index is required for close operation")
        if self.operation == "rename" and (self.tab_index is None or self.tab_name is None):
            raise ValueError("tab_index and tab_name are required for rename operation")
        if self.operation == "duplicate" and self.tab_index is None:
            raise ValueError("tab_index is required for duplicate operation")


@dataclass
class PaneFocusRequest:
    """Request to focus a specific pane.

    Args:
        pane_id: ID of the pane to focus
        tab_index: Optional tab index if focusing pane in different tab
    """

    pane_id: str
    tab_index: Optional[int] = None


@dataclass
class WidgetStateUpdateRequest:
    """Request to update widget state in a pane.

    Args:
        pane_id: ID of the pane containing the widget
        state_updates: Dictionary of state updates to apply
        merge: If True, merge with existing state; if False, replace
    """

    pane_id: str
    state_updates: Dict[str, Any]
    merge: bool = True

    def __post_init__(self):
        """Validate widget state update request."""
        if not self.state_updates:
            raise ValueError("state_updates cannot be empty")


@dataclass
class SplitPaneResponse:
    """Response from splitting a pane.

    Args:
        original_pane_id: ID of the original pane
        new_pane_id: ID of the newly created pane
        split_config: Configuration used for the split
    """

    original_pane_id: str
    new_pane_id: str
    split_config: Dict[str, Any]


@dataclass
class TabOperationResponse:
    """Response from tab operations.

    Args:
        tab_id: ID of the affected tab
        tab_index: Index of the affected tab
        operation_data: Additional data specific to the operation
    """

    tab_id: str
    tab_index: int
    operation_data: Optional[Dict[str, Any]] = None
