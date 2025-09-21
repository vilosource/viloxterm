"""Models package for data structures and business logic."""

from .base import OperationResult
from .operations import (
    ClosePaneRequest,
    PaneFocusRequest,
    SplitPaneRequest,
    SplitPaneResponse,
    TabOperationRequest,
    TabOperationResponse,
    WidgetStateUpdateRequest,
)
from .workspace_models import (
    PaneState,
    SplitConfiguration,
    TabState,
    WidgetType,
    WorkspaceState,
)

__all__ = [
    # Base classes
    "OperationResult",
    # Workspace models
    "WidgetType",
    "PaneState",
    "SplitConfiguration",
    "TabState",
    "WorkspaceState",
    # Operation DTOs
    "SplitPaneRequest",
    "ClosePaneRequest",
    "TabOperationRequest",
    "PaneFocusRequest",
    "WidgetStateUpdateRequest",
    "SplitPaneResponse",
    "TabOperationResponse",
]
