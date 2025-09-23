"""Models package for data structures and business logic."""

from .base import OperationResult

# Import compatibility layer for old interfaces
from .compatibility import (
    ClosePaneRequest,
    PaneFocusRequest,
    PaneState,
    SplitConfiguration,
    SplitPaneRequest,
    SplitPaneResponse,
    TabOperationRequest,
    TabOperationResponse,
    TabState,
    WidgetStateUpdateRequest,
    # WidgetType removed - now using string widget_ids
)

# Import from our new model
from .workspace_model import (
    Pane,
    PaneNode,
    PaneTree,
    Tab,
    WorkspaceModel,
    WorkspaceState,
)

__all__ = [
    # Base classes
    "OperationResult",
    # Compatibility classes (for old interfaces)
    "PaneState",
    "SplitConfiguration",
    "TabState",
    "SplitPaneRequest",
    "SplitPaneResponse",
    "ClosePaneRequest",
    "TabOperationRequest",
    "TabOperationResponse",
    "PaneFocusRequest",
    "WidgetStateUpdateRequest",
    # New model classes
    "Pane",
    "PaneNode",
    "PaneTree",
    "Tab",
    "WorkspaceModel",
    "WorkspaceState",
]
