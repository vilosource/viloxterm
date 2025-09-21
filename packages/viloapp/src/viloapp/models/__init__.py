"""Models package for data structures and business logic."""

from .base import OperationResult
from .workspace_models import (
    WidgetType,
    PaneState,
    SplitConfiguration,
    TabState,
    WorkspaceState,
)
from .operations import (
    SplitPaneRequest,
    ClosePaneRequest,
    TabOperationRequest,
    PaneFocusRequest,
    WidgetStateUpdateRequest,
    SplitPaneResponse,
    TabOperationResponse,
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
