"""Interfaces for model layer - defining contracts between layers.

These interfaces ensure that the business logic layer is decoupled from
the UI layer, following the dependency inversion principle.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from ..models import (
    ClosePaneRequest,
    OperationResult,
    PaneFocusRequest,
    PaneState,
    SplitPaneRequest,
    TabState,
    WidgetStateUpdateRequest,
    WorkspaceState,
)


class IWorkspaceModel(ABC):
    """Interface for workspace model - no Qt dependencies.

    This interface defines the contract for workspace data management.
    Implementations must be pure Python with no UI dependencies.
    """

    @abstractmethod
    def get_state(self) -> WorkspaceState:
        """Get the current workspace state.

        Returns:
            Complete workspace state as pure data
        """
        pass

    @abstractmethod
    def add_observer(self, callback: Callable[[str, Any], None]) -> None:
        """Add an observer for model changes.

        Args:
            callback: Function called when model changes (event_type, data)
        """
        pass

    @abstractmethod
    def remove_observer(self, callback: Callable[[str, Any], None]) -> None:
        """Remove an observer.

        Args:
            callback: Previously registered callback function
        """
        pass

    # Tab operations
    @abstractmethod
    def add_tab(self, name: str, widget_type: str) -> OperationResult:
        """Add a new tab.

        Args:
            name: Display name for the tab
            widget_type: Type of widget for the initial pane

        Returns:
            OperationResult with tab_id in data if successful
        """
        pass

    @abstractmethod
    def close_tab(self, index: int) -> OperationResult:
        """Close a tab by index.

        Args:
            index: Index of tab to close

        Returns:
            OperationResult indicating success/failure
        """
        pass

    @abstractmethod
    def rename_tab(self, index: int, new_name: str) -> OperationResult:
        """Rename a tab.

        Args:
            index: Index of tab to rename
            new_name: New name for the tab

        Returns:
            OperationResult indicating success/failure
        """
        pass

    @abstractmethod
    def duplicate_tab(self, index: int) -> OperationResult:
        """Duplicate a tab.

        Args:
            index: Index of tab to duplicate

        Returns:
            OperationResult with new_tab_id in data if successful
        """
        pass

    @abstractmethod
    def set_active_tab(self, index: int) -> OperationResult:
        """Set the active tab.

        Args:
            index: Index of tab to activate

        Returns:
            OperationResult indicating success/failure
        """
        pass

    # Pane operations
    @abstractmethod
    def split_pane(self, request: SplitPaneRequest) -> OperationResult:
        """Split a pane.

        Args:
            request: Split pane request with configuration

        Returns:
            OperationResult with SplitPaneResponse in data if successful
        """
        pass

    @abstractmethod
    def close_pane(self, request: ClosePaneRequest) -> OperationResult:
        """Close a pane.

        Args:
            request: Close pane request

        Returns:
            OperationResult indicating success/failure
        """
        pass

    @abstractmethod
    def focus_pane(self, request: PaneFocusRequest) -> OperationResult:
        """Focus a specific pane.

        Args:
            request: Pane focus request

        Returns:
            OperationResult indicating success/failure
        """
        pass

    @abstractmethod
    def update_widget_state(self, request: WidgetStateUpdateRequest) -> OperationResult:
        """Update the state of a widget in a pane.

        Args:
            request: Widget state update request

        Returns:
            OperationResult indicating success/failure
        """
        pass

    # Query operations
    @abstractmethod
    def get_tab_by_id(self, tab_id: str) -> Optional[TabState]:
        """Get a tab by its ID.

        Args:
            tab_id: ID of the tab

        Returns:
            TabState if found, None otherwise
        """
        pass

    @abstractmethod
    def get_pane_by_id(self, pane_id: str) -> Optional[PaneState]:
        """Get a pane by its ID.

        Args:
            pane_id: ID of the pane

        Returns:
            PaneState if found, None otherwise
        """
        pass

    @abstractmethod
    def get_active_pane(self) -> Optional[PaneState]:
        """Get the currently active pane.

        Returns:
            PaneState if there is an active pane, None otherwise
        """
        pass

    @abstractmethod
    def restore_state(self, state_dict: dict) -> OperationResult:
        """Restore workspace state from saved data.

        This is the model-first approach to state restoration.
        The UI should call this instead of creating widgets directly.

        Args:
            state_dict: Saved workspace state dictionary

        Returns:
            OperationResult indicating success or failure
        """
        pass


class ITabModel(ABC):
    """Interface for individual tab model."""

    @abstractmethod
    def get_state(self) -> TabState:
        """Get the current tab state."""
        pass

    @abstractmethod
    def split_pane(self, request: SplitPaneRequest) -> OperationResult:
        """Split a pane within this tab."""
        pass

    @abstractmethod
    def close_pane(self, pane_id: str) -> OperationResult:
        """Close a pane within this tab."""
        pass

    @abstractmethod
    def set_active_pane(self, pane_id: str) -> OperationResult:
        """Set the active pane in this tab."""
        pass


class IPaneModel(ABC):
    """Interface for individual pane model."""

    @abstractmethod
    def get_state(self) -> PaneState:
        """Get the current pane state."""
        pass

    @abstractmethod
    def update_widget_state(self, state_updates: dict, merge: bool = True) -> OperationResult:
        """Update the widget state."""
        pass

    @abstractmethod
    def set_widget_type(self, widget_type: str) -> OperationResult:
        """Change the widget type."""
        pass


class IModelObserver(ABC):
    """Interface for objects that observe model changes."""

    @abstractmethod
    def on_model_changed(self, event_type: str, data: Any) -> None:
        """Handle model change notifications.

        Args:
            event_type: Type of change (e.g., "tab_added", "pane_split")
            data: Event-specific data
        """
        pass
