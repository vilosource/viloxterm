#!/usr/bin/env python3
"""
State Controller - MVC Controller for managing state persistence.

This controller provides clean separation between the UI components (View)
and state data (Model), orchestrating save/restore operations without
coupling the UI to specific persistence mechanisms.
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Optional

from PySide6.QtCore import QObject, Signal

# Import our UI components
from viloapp.ui.widgets.split_pane_widget import SplitPaneWidget
from viloapp.ui.workspace_simple import Workspace


class StateModel(ABC):
    """Abstract base class for state data models."""

    @abstractmethod
    def serialize(self) -> dict[str, Any]:
        """Serialize the state to a dictionary."""
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, data: dict[str, Any]) -> "StateModel":
        """Deserialize state from a dictionary."""
        pass


class SplitPaneStateModel(StateModel):
    """State model for split pane layouts."""

    def __init__(self, root_data: dict[str, Any], active_pane_id: Optional[str] = None):
        self.root_data = root_data
        self.active_pane_id = active_pane_id

    def serialize(self) -> dict[str, Any]:
        """Serialize split pane state."""
        return {
            "type": "split_pane",
            "root": self.root_data,
            "active_pane_id": self.active_pane_id,
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "SplitPaneStateModel":
        """Deserialize split pane state."""
        return cls(root_data=data.get("root", {}), active_pane_id=data.get("active_pane_id"))


class WorkspaceStateModel(StateModel):
    """State model for workspace layouts."""

    def __init__(self, current_tab: int = 0, tabs: Optional[list] = None):
        self.current_tab = current_tab
        self.tabs = tabs or []

    def serialize(self) -> dict[str, Any]:
        """Serialize workspace state."""
        return {"type": "workspace", "current_tab": self.current_tab, "tabs": self.tabs}

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "WorkspaceStateModel":
        """Deserialize workspace state."""
        return cls(current_tab=data.get("current_tab", 0), tabs=data.get("tabs", []))


class StateController(QObject):
    """
    Controller for managing state persistence operations.

    Provides clean separation between UI components and state management,
    following MVC architectural patterns.
    """

    # Signals for state change notifications
    state_saved = Signal(str)  # state_type
    state_restored = Signal(str)  # state_type
    state_error = Signal(str, str)  # state_type, error_message

    def __init__(self, parent=None):
        super().__init__(parent)

    def save_split_pane_state(self, split_widget: SplitPaneWidget) -> SplitPaneStateModel:
        """
        Save split pane state using the controller.

        Args:
            split_widget: The SplitPaneWidget to save state from

        Returns:
            SplitPaneStateModel: The state model containing the serialized data
        """
        try:
            # Get state from the UI component
            ui_state = split_widget.get_state()

            # Create state model
            state_model = SplitPaneStateModel(
                root_data=ui_state.get("root", {}),
                active_pane_id=ui_state.get("active_pane_id"),
            )

            self.state_saved.emit("split_pane")
            return state_model

        except Exception as e:
            self.state_error.emit("split_pane", str(e))
            raise

    def restore_split_pane_state(
        self, split_widget: SplitPaneWidget, state_model: SplitPaneStateModel
    ) -> bool:
        """
        Restore split pane state using the controller.

        Args:
            split_widget: The SplitPaneWidget to restore state to
            state_model: The state model containing the data to restore

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert model back to UI format
            ui_state = state_model.serialize()

            # Restore to UI component
            success = split_widget.set_state(ui_state)

            if success:
                self.state_restored.emit("split_pane")
            else:
                self.state_error.emit("split_pane", "Failed to restore split pane state")

            return success

        except Exception as e:
            self.state_error.emit("split_pane", str(e))
            return False

    def save_workspace_state(self, workspace: Workspace) -> WorkspaceStateModel:
        """
        Save workspace state using the controller.

        Args:
            workspace: The Workspace to save state from

        Returns:
            WorkspaceStateModel: The state model containing the serialized data
        """
        try:
            # Get state from the UI component
            ui_state = workspace.save_state()

            # Create state model
            state_model = WorkspaceStateModel(
                current_tab=ui_state.get("current_tab", 0),
                tabs=ui_state.get("tabs", []),
            )

            self.state_saved.emit("workspace")
            return state_model

        except Exception as e:
            self.state_error.emit("workspace", str(e))
            raise

    def restore_workspace_state(
        self, workspace: Workspace, state_model: WorkspaceStateModel
    ) -> bool:
        """
        Restore workspace state using the controller.

        Args:
            workspace: The Workspace to restore state to
            state_model: The state model containing the data to restore

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert model back to UI format
            ui_state = state_model.serialize()

            # Restore to UI component
            workspace.restore_state(ui_state)

            self.state_restored.emit("workspace")
            return True

        except Exception as e:
            self.state_error.emit("workspace", str(e))
            return False

    def serialize_to_json(self, state_model: StateModel) -> str:
        """
        Serialize a state model to JSON string.

        Args:
            state_model: The state model to serialize

        Returns:
            str: JSON representation of the state
        """
        try:
            return json.dumps(state_model.serialize(), indent=2)
        except Exception as e:
            self.state_error.emit("json", f"Serialization failed: {str(e)}")
            raise

    def deserialize_from_json(self, json_str: str, state_type: str) -> Optional[StateModel]:
        """
        Deserialize a state model from JSON string.

        Args:
            json_str: JSON string to deserialize
            state_type: Type of state to deserialize ("split_pane" or "workspace")

        Returns:
            StateModel: The deserialized state model, or None if failed
        """
        try:
            data = json.loads(json_str)

            if state_type == "split_pane":
                return SplitPaneStateModel.deserialize(data)
            elif state_type == "workspace":
                return WorkspaceStateModel.deserialize(data)
            else:
                raise ValueError(f"Unknown state type: {state_type}")

        except Exception as e:
            self.state_error.emit(state_type, f"Deserialization failed: {str(e)}")
            return None


class ApplicationStateController(StateController):
    """
    High-level controller for managing complete application state.

    Coordinates multiple state controllers and provides a unified interface
    for application-level state persistence operations.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def save_complete_application_state(self, workspace: Workspace) -> dict[str, Any]:
        """
        Save the complete application state.

        Args:
            workspace: The main workspace component

        Returns:
            Dict containing all application state data
        """
        try:
            # Save workspace state
            workspace_model = self.save_workspace_state(workspace)

            # Create comprehensive application state
            app_state = {"version": "1.0", "workspace": workspace_model.serialize()}

            self.state_saved.emit("application")
            return app_state

        except Exception as e:
            self.state_error.emit("application", str(e))
            raise

    def restore_complete_application_state(
        self, workspace: Workspace, app_state: dict[str, Any]
    ) -> bool:
        """
        Restore the complete application state.

        Args:
            workspace: The main workspace component
            app_state: Complete application state data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Restore workspace state
            if "workspace" in app_state:
                workspace_model = WorkspaceStateModel.deserialize(app_state["workspace"])
                success = self.restore_workspace_state(workspace, workspace_model)

                if success:
                    self.state_restored.emit("application")

                return success

            return True  # Empty state is valid

        except Exception as e:
            self.state_error.emit("application", str(e))
            return False
