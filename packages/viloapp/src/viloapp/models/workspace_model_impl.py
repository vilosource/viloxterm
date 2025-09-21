"""Implementation of the workspace model interface.

This module provides a concrete implementation of IWorkspaceModel that manages
workspace state as pure data without any UI dependencies.
"""

import logging
import uuid
from typing import Any, Callable, Dict, List, Optional

from ..interfaces.model_interfaces import IWorkspaceModel
from ..models import (
    ClosePaneRequest,
    OperationResult,
    PaneFocusRequest,
    PaneState,
    SplitConfiguration,
    SplitPaneRequest,
    TabState,
    WidgetStateUpdateRequest,
    WidgetType,
    WorkspaceState,
)

logger = logging.getLogger(__name__)


class WorkspaceModelImpl(IWorkspaceModel):
    """Pure data model for workspace - no UI dependencies.

    This implementation manages workspace state as pure data and notifies
    observers about changes without any knowledge of the UI layer.
    """

    def __init__(self):
        """Initialize the workspace model with empty state."""
        self._state = WorkspaceState(tabs=[], active_tab_index=0)
        self._observers: List[Callable[[str, Any], None]] = []
        logger.debug("WorkspaceModel initialized with empty state")

    def get_state(self) -> WorkspaceState:
        """Get the current workspace state.

        Returns:
            Complete workspace state as pure data
        """
        return self._state

    def add_observer(self, callback: Callable[[str, Any], None]) -> None:
        """Add an observer for model changes.

        Args:
            callback: Function called when model changes (event_type, data)
        """
        if callback not in self._observers:
            self._observers.append(callback)
            logger.debug(f"Added observer: {callback}")

    def remove_observer(self, callback: Callable[[str, Any], None]) -> None:
        """Remove an observer.

        Args:
            callback: Previously registered callback function
        """
        if callback in self._observers:
            self._observers.remove(callback)
            logger.debug(f"Removed observer: {callback}")

    def _notify(self, event_type: str, data: Any) -> None:
        """Notify all observers of a model change.

        Args:
            event_type: Type of change (e.g., "tab_added", "pane_split")
            data: Event-specific data
        """
        logger.debug(f"Notifying {len(self._observers)} observers of event: {event_type}")
        for observer in self._observers:
            try:
                observer(event_type, data)
            except Exception as e:
                logger.error(f"Observer {observer} failed with error: {e}")

    def _generate_id(self) -> str:
        """Generate a unique ID for tabs/panes."""
        return str(uuid.uuid4())

    # Tab operations
    def add_tab(self, name: str, widget_type: str) -> OperationResult:
        """Add a new tab.

        Args:
            name: Display name for the tab
            widget_type: Type of widget for the initial pane

        Returns:
            OperationResult with tab_id in data if successful
        """
        try:
            # Validate widget type
            try:
                widget_type_enum = WidgetType(widget_type)
            except ValueError:
                return OperationResult.error_result(f"Invalid widget type: {widget_type}")

            # Generate IDs
            tab_id = self._generate_id()
            pane_id = self._generate_id()

            # Create initial pane
            initial_pane = PaneState(
                id=pane_id,
                widget_type=widget_type_enum,
                widget_state={},
                is_active=True
            )

            # Create tab with initial pane
            tab = TabState(
                id=tab_id,
                name=name,
                pane_tree={"root": pane_id},  # Simple tree with single pane
                active_pane_id=pane_id,
                panes={pane_id: initial_pane}
            )

            # Add to workspace
            self._state.tabs.append(tab)
            self._state.active_tab_index = len(self._state.tabs) - 1

            # Notify observers
            self._notify("tab_added", {
                "tab_id": tab_id,
                "name": name,
                "widget_type": widget_type,
                "index": len(self._state.tabs) - 1
            })

            logger.info(f"Added tab '{name}' with ID {tab_id}")
            return OperationResult.success_result({"tab_id": tab_id})

        except Exception as e:
            logger.error(f"Failed to add tab: {e}")
            return OperationResult.error_result(f"Failed to add tab: {e}")

    def close_tab(self, index: int) -> OperationResult:
        """Close a tab by index.

        Args:
            index: Index of tab to close

        Returns:
            OperationResult indicating success/failure
        """
        # Check if tab can be closed
        validation_result = self._state.can_close_tab(index)
        if not validation_result.success:
            return validation_result

        try:
            # Get tab info before removal
            tab = self._state.tabs[index]
            tab_id = tab.id
            tab_name = tab.name

            # Remove tab
            self._state.tabs.pop(index)

            # Update active tab index
            if self._state.active_tab_index >= len(self._state.tabs):
                self._state.active_tab_index = len(self._state.tabs) - 1
            elif self._state.active_tab_index > index:
                self._state.active_tab_index -= 1

            # Notify observers
            self._notify("tab_closed", {
                "tab_id": tab_id,
                "name": tab_name,
                "index": index,
                "new_active_index": self._state.active_tab_index
            })

            logger.info(f"Closed tab '{tab_name}' at index {index}")
            return OperationResult.success_result()

        except Exception as e:
            logger.error(f"Failed to close tab: {e}")
            return OperationResult.error_result(f"Failed to close tab: {e}")

    def rename_tab(self, index: int, new_name: str) -> OperationResult:
        """Rename a tab.

        Args:
            index: Index of tab to rename
            new_name: New name for the tab

        Returns:
            OperationResult indicating success/failure
        """
        if index < 0 or index >= len(self._state.tabs):
            return OperationResult.error_result(f"Invalid tab index: {index}")

        if not new_name or not new_name.strip():
            return OperationResult.error_result("Tab name cannot be empty")

        try:
            tab = self._state.tabs[index]
            old_name = tab.name
            tab.name = new_name.strip()

            # Notify observers
            self._notify("tab_renamed", {
                "tab_id": tab.id,
                "index": index,
                "old_name": old_name,
                "new_name": new_name
            })

            logger.info(f"Renamed tab at index {index} from '{old_name}' to '{new_name}'")
            return OperationResult.success_result()

        except Exception as e:
            logger.error(f"Failed to rename tab: {e}")
            return OperationResult.error_result(f"Failed to rename tab: {e}")

    def duplicate_tab(self, index: int) -> OperationResult:
        """Duplicate a tab.

        Args:
            index: Index of tab to duplicate

        Returns:
            OperationResult with new_tab_id in data if successful
        """
        if index < 0 or index >= len(self._state.tabs):
            return OperationResult.error_result(f"Invalid tab index: {index}")

        try:
            # Get original tab
            original_tab = self._state.tabs[index]

            # Create new tab with copied state
            new_tab_id = self._generate_id()
            new_name = f"{original_tab.name} (Copy)"

            # Deep copy panes with new IDs
            new_panes = {}
            pane_id_mapping = {}

            for pane_id, pane in original_tab.panes.items():
                new_pane_id = self._generate_id()
                pane_id_mapping[pane_id] = new_pane_id

                new_panes[new_pane_id] = PaneState(
                    id=new_pane_id,
                    widget_type=pane.widget_type,
                    widget_state=pane.widget_state.copy(),
                    is_active=pane.is_active
                )

            # Update pane tree structure with new IDs
            new_pane_tree = self._update_pane_tree_ids(original_tab.pane_tree, pane_id_mapping)
            new_active_pane_id = pane_id_mapping.get(original_tab.active_pane_id, original_tab.active_pane_id)

            # Create new tab
            new_tab = TabState(
                id=new_tab_id,
                name=new_name,
                pane_tree=new_pane_tree,
                active_pane_id=new_active_pane_id,
                panes=new_panes
            )

            # Insert after original tab
            self._state.tabs.insert(index + 1, new_tab)

            # Update active tab index
            if self._state.active_tab_index > index:
                self._state.active_tab_index += 1

            # Notify observers
            self._notify("tab_duplicated", {
                "original_tab_id": original_tab.id,
                "new_tab_id": new_tab_id,
                "original_index": index,
                "new_index": index + 1,
                "new_name": new_name
            })

            logger.info(f"Duplicated tab '{original_tab.name}' as '{new_name}'")
            return OperationResult.success_result({"new_tab_id": new_tab_id})

        except Exception as e:
            logger.error(f"Failed to duplicate tab: {e}")
            return OperationResult.error_result(f"Failed to duplicate tab: {e}")

    def _update_pane_tree_ids(self, tree: Dict[str, Any], id_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Update pane IDs in the tree structure."""
        if isinstance(tree, dict):
            new_tree = {}
            for key, value in tree.items():
                if key in id_mapping:
                    new_tree[id_mapping[key]] = self._update_pane_tree_ids(value, id_mapping)
                elif isinstance(value, str) and value in id_mapping:
                    new_tree[key] = id_mapping[value]
                else:
                    new_tree[key] = self._update_pane_tree_ids(value, id_mapping)
            return new_tree
        elif isinstance(tree, str) and tree in id_mapping:
            return id_mapping[tree]
        else:
            return tree

    def set_active_tab(self, index: int) -> OperationResult:
        """Set the active tab.

        Args:
            index: Index of tab to activate

        Returns:
            OperationResult indicating success/failure
        """
        if index < 0 or index >= len(self._state.tabs):
            return OperationResult.error_result(f"Invalid tab index: {index}")

        if self._state.active_tab_index == index:
            return OperationResult.success_result()  # Already active

        try:
            old_index = self._state.active_tab_index
            self._state.active_tab_index = index

            tab = self._state.tabs[index]

            # Notify observers
            self._notify("tab_activated", {
                "tab_id": tab.id,
                "index": index,
                "old_index": old_index,
                "name": tab.name
            })

            logger.debug(f"Activated tab '{tab.name}' at index {index}")
            return OperationResult.success_result()

        except Exception as e:
            logger.error(f"Failed to set active tab: {e}")
            return OperationResult.error_result(f"Failed to set active tab: {e}")

    # Pane operations
    def split_pane(self, request: SplitPaneRequest) -> OperationResult:
        """Split a pane.

        Args:
            request: Split pane request with configuration

        Returns:
            OperationResult with SplitPaneResponse in data if successful
        """
        # Validate request
        validation_result = self._state.can_split_pane(request.pane_id)
        if not validation_result.success:
            return validation_result

        try:
            active_tab = self._state.get_active_tab()
            if not active_tab:
                return OperationResult.error_result("No active tab")

            # Get the pane to split
            pane_to_split = active_tab.panes.get(request.pane_id)
            if not pane_to_split:
                return OperationResult.error_result(f"Pane not found: {request.pane_id}")

            # Create new pane
            new_pane_id = self._generate_id()
            new_pane = PaneState(
                id=new_pane_id,
                widget_type=request.new_widget_type or pane_to_split.widget_type,
                widget_state={},
                is_active=False
            )

            # Add new pane to tab
            active_tab.panes[new_pane_id] = new_pane

            # Update pane tree to reflect split
            # For now, use a simple structure - can be enhanced later
            SplitConfiguration(
                orientation=request.orientation,
                ratio=request.ratio,
                left_pane_id=request.pane_id,
                right_pane_id=new_pane_id
            )

            # Update tree structure (simplified)
            if active_tab.pane_tree.get("root") == request.pane_id:
                active_tab.pane_tree = {
                    "root": {
                        "type": "split",
                        "orientation": request.orientation,
                        "ratio": request.ratio,
                        "left": request.pane_id,
                        "right": new_pane_id
                    }
                }
            else:
                # More complex tree updates would go here
                pass

            # Notify observers
            self._notify("pane_split", {
                "parent_pane_id": request.pane_id,
                "new_pane_id": new_pane_id,
                "orientation": request.orientation,
                "ratio": request.ratio,
                "tab_id": active_tab.id
            })

            logger.info(f"Split pane {request.pane_id} {request.orientation}, created {new_pane_id}")
            return OperationResult.success_result({
                "new_pane_id": new_pane_id,
                "parent_pane_id": request.pane_id,
                "orientation": request.orientation,
                "ratio": request.ratio
            })

        except Exception as e:
            logger.error(f"Failed to split pane: {e}")
            return OperationResult.error_result(f"Failed to split pane: {e}")

    def close_pane(self, request: ClosePaneRequest) -> OperationResult:
        """Close a pane.

        Args:
            request: Close pane request

        Returns:
            OperationResult indicating success/failure
        """
        active_tab = self._state.get_active_tab()
        if not active_tab:
            return OperationResult.error_result("No active tab")

        if request.pane_id not in active_tab.panes:
            return OperationResult.error_result(f"Pane not found: {request.pane_id}")

        # Can't close the last pane
        if len(active_tab.panes) <= 1 and not request.force:
            return OperationResult.error_result("Cannot close the last pane")

        try:
            # Remove pane
            active_tab.panes.pop(request.pane_id)

            # Update active pane if necessary
            if active_tab.active_pane_id == request.pane_id:
                # Set new active pane (first available)
                if active_tab.panes:
                    active_tab.active_pane_id = next(iter(active_tab.panes.keys()))
                    active_tab.panes[active_tab.active_pane_id].is_active = True

            # Update pane tree (simplified - remove from tree structure)
            # More complex tree updates would go here

            # Notify observers
            self._notify("pane_closed", {
                "pane_id": request.pane_id,
                "tab_id": active_tab.id,
                "new_active_pane_id": active_tab.active_pane_id if active_tab.panes else None
            })

            logger.info(f"Closed pane {request.pane_id}")
            return OperationResult.success_result()

        except Exception as e:
            logger.error(f"Failed to close pane: {e}")
            return OperationResult.error_result(f"Failed to close pane: {e}")

    def focus_pane(self, request: PaneFocusRequest) -> OperationResult:
        """Focus a specific pane.

        Args:
            request: Pane focus request

        Returns:
            OperationResult indicating success/failure
        """
        active_tab = self._state.get_active_tab()
        if not active_tab:
            return OperationResult.error_result("No active tab")

        if request.pane_id not in active_tab.panes:
            return OperationResult.error_result(f"Pane not found: {request.pane_id}")

        if active_tab.active_pane_id == request.pane_id:
            return OperationResult.success_result()  # Already focused

        try:
            # Update focus
            old_active_pane_id = active_tab.active_pane_id

            # Set old pane as inactive
            if old_active_pane_id in active_tab.panes:
                active_tab.panes[old_active_pane_id].is_active = False

            # Set new pane as active
            active_tab.active_pane_id = request.pane_id
            active_tab.panes[request.pane_id].is_active = True

            # Notify observers
            self._notify("pane_focused", {
                "pane_id": request.pane_id,
                "old_pane_id": old_active_pane_id,
                "tab_id": active_tab.id
            })

            logger.debug(f"Focused pane {request.pane_id}")
            return OperationResult.success_result()

        except Exception as e:
            logger.error(f"Failed to focus pane: {e}")
            return OperationResult.error_result(f"Failed to focus pane: {e}")

    def update_widget_state(self, request: WidgetStateUpdateRequest) -> OperationResult:
        """Update the state of a widget in a pane.

        Args:
            request: Widget state update request

        Returns:
            OperationResult indicating success/failure
        """
        pane = self.get_pane_by_id(request.pane_id)
        if not pane:
            return OperationResult.error_result(f"Pane not found: {request.pane_id}")

        try:
            if request.merge:
                # Merge with existing state
                pane.widget_state.update(request.state_updates)
            else:
                # Replace entire state
                pane.widget_state = request.state_updates.copy()

            # Notify observers
            self._notify("widget_state_updated", {
                "pane_id": request.pane_id,
                "state_updates": request.state_updates,
                "merge": request.merge
            })

            logger.debug(f"Updated widget state for pane {request.pane_id}")
            return OperationResult.success_result()

        except Exception as e:
            logger.error(f"Failed to update widget state: {e}")
            return OperationResult.error_result(f"Failed to update widget state: {e}")

    # Query operations
    def get_tab_by_id(self, tab_id: str) -> Optional[TabState]:
        """Get a tab by its ID.

        Args:
            tab_id: ID of the tab

        Returns:
            TabState if found, None otherwise
        """
        for tab in self._state.tabs:
            if tab.id == tab_id:
                return tab
        return None

    def get_pane_by_id(self, pane_id: str) -> Optional[PaneState]:
        """Get a pane by its ID.

        Args:
            pane_id: ID of the pane

        Returns:
            PaneState if found, None otherwise
        """
        for tab in self._state.tabs:
            if pane_id in tab.panes:
                return tab.panes[pane_id]
        return None

    def get_active_pane(self) -> Optional[PaneState]:
        """Get the currently active pane.

        Returns:
            PaneState if there is an active pane, None otherwise
        """
        return self._state.get_active_pane()
