"""
Implementation of IWorkspaceModel that bridges to the new Model-View-Command architecture.

This adapter allows the existing WorkspaceService to work with the new architecture.
"""

import logging
from dataclasses import dataclass
from typing import Any, List, Optional

from viloapp.core.commands.workspace_commands import CommandContext, CommandRegistry
from viloapp.interfaces.model_interfaces import IWorkspaceModel
from viloapp.models.base import OperationResult
from viloapp.models.compatibility import (
    ClosePaneRequest,
    PaneFocusRequest,
    SplitPaneRequest,
    TabOperationResponse,
    WidgetStateUpdateRequest,
)
from viloapp.models.workspace_model import WidgetType, WorkspaceModel


@dataclass
class StateSnapshot:
    """Represents a snapshot of the workspace state."""

    tabs: List[Any]
    active_tab_index: int = 0


logger = logging.getLogger(__name__)


class WorkspaceModelImpl(IWorkspaceModel):
    """
    Adapter that bridges the old IWorkspaceModel interface to the new WorkspaceModel.

    This allows WorkspaceService to work with our new Model-View-Command architecture.
    """

    def __init__(self):
        """Initialize the adapter with the new model and command registry."""
        self._model = WorkspaceModel()
        self._command_registry = CommandRegistry()

    def get_state(self) -> StateSnapshot:
        """Get current workspace state."""
        # Return the compatibility StateSnapshot
        from viloapp.models.compatibility import TabState

        # Convert new model state to old format
        tabs = []
        for tab in self._model.state.tabs:
            # Create tab state
            tab_state = TabState(id=tab.id, name=tab.name, active_pane_id=tab.active_pane_id)
            tabs.append(tab_state)

        # Get active tab
        active_tab = self._model.state.get_active_tab()
        active_tab_index = 0
        if active_tab:
            for i, tab in enumerate(self._model.state.tabs):
                if tab.id == active_tab.id:
                    active_tab_index = i
                    break

        # Create state snapshot
        return StateSnapshot(tabs=tabs, active_tab_index=active_tab_index)

    def split_pane(self, request: SplitPaneRequest) -> OperationResult:
        """Split a pane in the workspace."""
        try:
            # Get the active tab
            active_tab = self._model.state.get_active_tab()
            if not active_tab:
                return OperationResult(success=False, error="No active tab")

            # Find the pane to split
            pane = active_tab.get_pane(request.pane_id)
            if not pane:
                return OperationResult(success=False, error=f"Pane {request.pane_id} not found")

            # Execute split command through new architecture
            context = CommandContext(model=self._model)
            context.active_tab_id = active_tab.id
            context.active_pane_id = request.pane_id

            # Use the new command registry to split
            result = self._command_registry.execute(
                "pane.split",
                context,
                orientation=request.orientation,
                widget_type=request.widget_type or WidgetType.TERMINAL,
            )

            if result.success:
                # Get the new pane ID from the result
                new_pane = active_tab.get_active_pane()
                if new_pane and new_pane.id != request.pane_id:
                    return OperationResult(success=True, data={"new_pane_id": new_pane.id})
                else:
                    # Find the newly created pane
                    all_panes = active_tab.get_all_panes()
                    for p in all_panes:
                        if p.id not in [
                            pane.id for pane in active_tab.get_all_panes() if pane.id != p.id
                        ]:
                            return OperationResult(success=True, data={"new_pane_id": p.id})
                    return OperationResult(success=True, data={"new_pane_id": "unknown"})
            else:
                return OperationResult(success=False, error=result.error or "Split failed")

        except Exception as e:
            logger.error(f"Error splitting pane: {e}")
            return OperationResult(success=False, error=str(e))

    def close_pane(self, request: ClosePaneRequest) -> OperationResult:
        """Close a pane in the workspace."""
        try:
            # Get the active tab
            active_tab = self._model.state.get_active_tab()
            if not active_tab:
                return OperationResult(success=False, error="No active tab")

            # Execute close command through new architecture
            context = CommandContext(model=self._model)
            context.active_tab_id = active_tab.id
            context.active_pane_id = request.pane_id

            result = self._command_registry.execute("pane.close", context, pane_id=request.pane_id)

            return OperationResult(success=result.success, error=result.error)

        except Exception as e:
            logger.error(f"Error closing pane: {e}")
            return OperationResult(success=False, error=str(e))

    def focus_pane(self, request: PaneFocusRequest) -> OperationResult:
        """Focus a specific pane."""
        try:
            # Get the active tab
            active_tab = self._model.state.get_active_tab()
            if not active_tab:
                return OperationResult(success=False, error="No active tab")

            # Execute focus command through new architecture
            context = CommandContext(model=self._model)
            context.active_tab_id = active_tab.id

            result = self._command_registry.execute("pane.focus", context, pane_id=request.pane_id)

            return OperationResult(success=result.success, error=result.error)

        except Exception as e:
            logger.error(f"Error focusing pane: {e}")
            return OperationResult(success=False, error=str(e))

    def add_tab(self, name: str, widget_type: Optional[str] = None) -> TabOperationResponse:
        """Add a new tab to the workspace."""
        try:
            # Convert string widget type to enum
            wtype = WidgetType.TERMINAL
            if widget_type:
                try:
                    wtype = WidgetType(widget_type)
                except ValueError:
                    # Try to find by name
                    for t in WidgetType:
                        if t.value == widget_type:
                            wtype = t
                            break

            # Execute through new architecture
            context = CommandContext(model=self._model)
            result = self._command_registry.execute(
                "tab.create", context, name=name, widget_type=wtype
            )

            if result.success:
                # Get the new tab
                if len(self._model.state.tabs) > 0:
                    new_tab = self._model.state.tabs[-1]
                    return TabOperationResponse(tab_id=new_tab.id, success=True)

            return TabOperationResponse(success=False, message=result.error)

        except Exception as e:
            logger.error(f"Error adding tab: {e}")
            return TabOperationResponse(success=False, message=str(e))

    def close_tab(self, index: int) -> OperationResult:
        """Close a tab by index."""
        try:
            # Get tab at index
            if 0 <= index < len(self._model.state.tabs):
                tab = self._model.state.tabs[index]

                # Execute through new architecture
                context = CommandContext(model=self._model)
                result = self._command_registry.execute("tab.close", context, tab_id=tab.id)

                return OperationResult(success=result.success, error=result.error)
            else:
                return OperationResult(success=False, error=f"Tab index {index} out of range")

        except Exception as e:
            logger.error(f"Error closing tab: {e}")
            return OperationResult(success=False, error=str(e))

    def switch_tab(self, index: int) -> OperationResult:
        """Switch to a tab by index."""
        try:
            # Get tab at index
            if 0 <= index < len(self._model.state.tabs):
                tab = self._model.state.tabs[index]

                # Execute through new architecture
                context = CommandContext(model=self._model)
                result = self._command_registry.execute("tab.switch", context, tab_id=tab.id)

                return OperationResult(success=result.success, error=result.error)
            else:
                return OperationResult(success=False, error=f"Tab index {index} out of range")

        except Exception as e:
            logger.error(f"Error switching tab: {e}")
            return OperationResult(success=False, error=str(e))

    def update_widget_state(self, request: WidgetStateUpdateRequest) -> OperationResult:
        """Update widget state (not fully implemented in new architecture yet)."""
        # This would need to be implemented when widgets have state
        return OperationResult(success=True)

    def navigate_pane(self, direction: str) -> OperationResult:
        """Navigate to adjacent pane."""
        try:
            # Execute through new architecture
            context = CommandContext(model=self._model)

            # Map direction to command
            command_map = {
                "up": "pane.focusUp",
                "down": "pane.focusDown",
                "left": "pane.focusLeft",
                "right": "pane.focusRight",
            }

            command = command_map.get(direction.lower())
            if not command:
                return OperationResult(success=False, error=f"Invalid direction: {direction}")

            result = self._command_registry.execute(command, context)

            return OperationResult(success=result.success, error=result.error)

        except Exception as e:
            logger.error(f"Error navigating pane: {e}")
            return OperationResult(success=False, error=str(e))

    def resize_pane(self, pane_id: str, delta: float) -> OperationResult:
        """Resize a pane (not fully implemented yet)."""
        # This would need to be implemented in the new architecture
        return OperationResult(success=True)

    def save_state(self) -> dict[str, Any]:
        """Save workspace state for persistence."""
        # Convert model state to dict
        return {
            "tabs": [
                {
                    "id": tab.id,
                    "name": tab.name,
                    "active_pane_id": tab.active_pane_id,
                    "panes": [
                        {"id": pane.id, "widget_type": pane.widget_type.value}
                        for pane in tab.get_all_panes()
                    ],
                }
                for tab in self._model.state.tabs
            ],
            "active_tab_id": self._model.state.active_tab_id,
        }

    def restore_state(self, state: dict[str, Any]) -> bool:
        """Restore workspace state from persistence."""
        # This would need more implementation
        return True

    def validate_operation(self, operation: str, **kwargs) -> tuple[bool, Optional[str]]:
        """Validate if an operation can be performed."""
        # Basic validation
        if operation == "split_pane":
            active_tab = self._model.state.get_active_tab()
            if not active_tab:
                return False, "No active tab"
            if not active_tab.get_active_pane():
                return False, "No active pane"
            return True, None
        elif operation == "close_pane":
            active_tab = self._model.state.get_active_tab()
            if not active_tab:
                return False, "No active tab"
            if len(active_tab.get_all_panes()) <= 1:
                return False, "Cannot close last pane"
            return True, None
        else:
            return True, None

    # Additional abstract methods from IWorkspaceModel
    def add_observer(self, observer):
        """Add an observer to the model."""
        # The new model has its own observer pattern
        self._model.add_observer(observer)

    def remove_observer(self, observer):
        """Remove an observer from the model."""
        self._model.remove_observer(observer)

    def get_tab_by_id(self, tab_id: str):
        """Get a tab by its ID."""
        for tab in self._model.state.tabs:
            if tab.id == tab_id:
                return tab
        return None

    def get_pane_by_id(self, pane_id: str):
        """Get a pane by its ID."""
        for tab in self._model.state.tabs:
            pane = tab.get_pane(pane_id)
            if pane:
                return pane
        return None

    def get_active_pane(self):
        """Get the currently active pane."""
        active_tab = self._model.state.get_active_tab()
        if active_tab:
            return active_tab.get_active_pane()
        return None

    def set_active_tab(self, tab_id: str) -> bool:
        """Set the active tab by ID."""
        context = CommandContext(model=self._model)
        result = self._command_registry.execute("tab.switch", context, tab_id=tab_id)
        return result.success

    def rename_tab(self, tab_id: str, new_name: str) -> OperationResult:
        """Rename a tab."""
        tab = self.get_tab_by_id(tab_id)
        if tab:
            tab.name = new_name
            return OperationResult(success=True)
        return OperationResult(success=False, error=f"Tab {tab_id} not found")

    def duplicate_tab(self, tab_id: str) -> OperationResult:
        """Duplicate a tab (not fully implemented)."""
        # This would need more implementation
        return OperationResult(success=False, error="Duplicate tab not implemented")
