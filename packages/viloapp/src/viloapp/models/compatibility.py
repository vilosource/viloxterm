"""
Compatibility layer to bridge old interfaces with new model.

This is a temporary bridge until we update all the interfaces.
"""

from dataclasses import dataclass
from typing import Optional

from .workspace_model import WidgetType as NewWidgetType


# Map old model classes to satisfy imports
@dataclass
class PaneState:
    """Compatibility class for old PaneState."""

    id: str
    widget_type: str
    focused: bool = False


@dataclass
class SplitConfiguration:
    """Compatibility class for old SplitConfiguration."""

    orientation: str = "horizontal"
    ratio: float = 0.5


@dataclass
class TabState:
    """Compatibility class for old TabState."""

    id: str
    name: str
    active_pane_id: Optional[str] = None


@dataclass
class SplitPaneRequest:
    """Request to split a pane."""

    pane_id: str
    orientation: str = "horizontal"
    widget_type: Optional[str] = None


@dataclass
class SplitPaneResponse:
    """Response from split pane operation."""

    new_pane_id: str
    success: bool = True


@dataclass
class ClosePaneRequest:
    """Request to close a pane."""

    pane_id: str


@dataclass
class TabOperationRequest:
    """Request for tab operations."""

    operation: str  # "create", "close", "rename", etc.
    tab_id: Optional[str] = None
    name: Optional[str] = None
    widget_type: Optional[str] = None


@dataclass
class TabOperationResponse:
    """Response from tab operation."""

    tab_id: Optional[str] = None
    success: bool = True
    message: Optional[str] = None


@dataclass
class PaneFocusRequest:
    """Request to focus a pane."""

    pane_id: str


@dataclass
class WidgetStateUpdateRequest:
    """Request to update widget state."""

    pane_id: str
    state: dict


# Re-export WidgetType from new model
WidgetType = NewWidgetType
