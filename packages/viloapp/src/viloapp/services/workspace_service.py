#!/usr/bin/env python3
"""
Workspace service for managing tabs, panes, and layouts.

This service coordinates workspace-related operations through the workspace model
interface, following proper architecture separation.
"""

import logging
from typing import Any, Optional

from viloapp.core.settings.app_defaults import get_default_split_direction
from viloapp.interfaces.model_interfaces import IWorkspaceModel
from viloapp.models import (
    SplitPaneRequest,
    WidgetStateUpdateRequest,
    WidgetType,
)
from viloapp.services.base import Service
from viloapp.services.workspace_pane_manager import WorkspacePaneManager
from viloapp.services.workspace_tab_manager import WorkspaceTabManager
from viloapp.services.workspace_widget_registry import WorkspaceWidgetRegistry

logger = logging.getLogger(__name__)


class WorkspaceService(Service):
    """
    Service for coordinating workspace operations.

    Works with IWorkspaceModel interface for business logic and maintains
    backward compatibility with existing managers.
    """

    def __init__(self, model: Optional[IWorkspaceModel] = None, workspace=None):
        """
        Initialize the workspace service.

        Args:
            model: Workspace model for business logic
            workspace: Optional workspace instance (for backward compatibility)
        """
        super().__init__("WorkspaceService")
        self._model = model
        self._workspace = workspace  # Keep for backward compatibility during transition

        # Initialize specialized managers
        self._widget_registry = WorkspaceWidgetRegistry()
        self._tab_manager = WorkspaceTabManager(model, self._widget_registry) if model else None
        self._pane_manager = WorkspacePaneManager(model) if model else None

        # Initialize widget factories for plugins
        self._widget_factories = {}

    def get_workspace(self):
        """Get the workspace instance."""
        return self._workspace

    def set_model(self, model: IWorkspaceModel):
        """Set the workspace model."""
        self._model = model

    def get_model(self) -> Optional[IWorkspaceModel]:
        """Get the workspace model."""
        return self._model

    def set_workspace(self, workspace):
        """Set the workspace instance."""
        self._workspace = workspace
        # Update all managers with new workspace
        if self._tab_manager:
            self._tab_manager.set_workspace(workspace)
            self._tab_manager.set_model(self._model)
        if self._pane_manager:
            self._pane_manager.set_workspace(workspace)
            self._pane_manager.set_model(self._model)

    def initialize(self, context: dict[str, Any]) -> None:
        """Initialize the service with application context."""
        super().initialize(context)

        # Get workspace from context if not provided
        if not self._workspace:
            self._workspace = context.get("workspace")

        if not self._workspace:
            logger.warning("WorkspaceService initialized without workspace reference")

    def cleanup(self) -> None:
        """Cleanup service resources."""
        self._workspace = None
        self._widget_registry.clear()
        self._widget_factories.clear()
        super().cleanup()

    # ============= Widget Registry Operations (Delegated) =============

    def has_widget(self, widget_id: str) -> bool:
        """Check if a widget with the given ID exists."""
        return self._widget_registry.has_widget(widget_id)

    def focus_widget(self, widget_id: str) -> bool:
        """Focus (switch to) a widget by its ID."""
        return self._tab_manager.focus_widget(widget_id)

    def register_widget(self, widget_id: str, tab_index: int) -> bool:
        """Register a widget with its tab index."""
        return self._widget_registry.register_widget(widget_id, tab_index)

    def unregister_widget(self, widget_id: str) -> bool:
        """Unregister a widget from the registry."""
        return self._widget_registry.unregister_widget(widget_id)

    def update_registry_after_tab_close(
        self, closed_index: int, widget_id: Optional[str] = None
    ) -> int:
        """Update registry indices after a tab is closed."""
        return self._widget_registry.update_registry_after_tab_close(closed_index, widget_id)

    def get_widget_tab_index(self, widget_id: str) -> Optional[int]:
        """Get the tab index for a registered widget."""
        return self._widget_registry.get_widget_tab_index(widget_id)

    def is_widget_registered(self, widget_id: str) -> bool:
        """Check if a widget is registered."""
        return self._widget_registry.is_widget_registered(widget_id)

    # ============= Tab Operations (Delegated) =============

    def add_editor_tab(self, name: Optional[str] = None) -> int:
        """Add a new editor tab to the workspace."""
        self.validate_initialized()

        if self._model:
            # Use model interface for business logic
            tab_name = name or f"Editor {len(self._model.get_state().tabs) + 1}"
            result = self._model.add_tab(tab_name, WidgetType.EDITOR.value)

            if result.success:
                # Get the new tab index
                state = self._model.get_state()
                index = len(state.tabs) - 1

                # Update context
                from viloapp.core.context.manager import context_manager

                context_manager.set("workbench.tabs.count", len(state.tabs))
                context_manager.set("workbench.tabs.hasMultiple", len(state.tabs) > 1)

                return index
            else:
                logger.error(f"Failed to add editor tab: {result.error}")
                return -1
        else:
            # Fallback to legacy manager
            if not self._tab_manager:
                logger.error("No model or tab manager available")
                return -1

            index = self._tab_manager.add_editor_tab(name)

            # Notify observers
            self.notify(
                "tab_added",
                {"type": "editor", "name": name or f"Editor {index}", "index": index},
            )

            # Update context
            from viloapp.core.context.manager import context_manager

            context_manager.set("workbench.tabs.count", self.get_tab_count())
            context_manager.set("workbench.tabs.hasMultiple", self.get_tab_count() > 1)

            return index

    def add_terminal_tab(self, name: Optional[str] = None) -> int:
        """Add a new terminal tab to the workspace."""
        self.validate_initialized()

        if self._model:
            # Use model interface for business logic
            tab_name = name or f"Terminal {len(self._model.get_state().tabs) + 1}"
            result = self._model.add_tab(tab_name, WidgetType.TERMINAL.value)

            if result.success:
                # Get the new tab index
                state = self._model.get_state()
                index = len(state.tabs) - 1

                # Update context
                from viloapp.core.context.manager import context_manager

                context_manager.set("workbench.tabs.count", len(state.tabs))
                context_manager.set("workbench.tabs.hasMultiple", len(state.tabs) > 1)

                return index
            else:
                logger.error(f"Failed to add terminal tab: {result.error}")
                return -1
        else:
            # Fallback to legacy manager
            if not self._tab_manager:
                logger.error("No model or tab manager available")
                return -1

            index = self._tab_manager.add_terminal_tab(name)

            # Notify observers
            self.notify(
                "tab_added",
                {"type": "terminal", "name": name or f"Terminal {index}", "index": index},
            )

            # Update context
            from viloapp.core.context.manager import context_manager

            context_manager.set("workbench.tabs.count", self.get_tab_count())
            context_manager.set("workbench.tabs.hasMultiple", self.get_tab_count() > 1)

            return index

    def add_app_widget(self, widget_type, widget_id: str, name: Optional[str] = None) -> bool:
        """Add a generic app widget tab."""
        # Delegate to tab manager
        success = self._tab_manager.add_app_widget(widget_type, widget_id, name)

        if success:
            # Notify observers
            self.notify(
                "tab_added",
                {"type": str(widget_type.value), "widget_id": widget_id, "name": name},
            )

            # Update context
            from viloapp.core.context.manager import context_manager

            context_manager.set("workbench.tabs.count", self.get_tab_count())
            context_manager.set("workbench.tabs.hasMultiple", self.get_tab_count() > 1)

        return success

    def close_tab(self, index: Optional[int] = None) -> bool:
        """Close a tab."""
        self.validate_initialized()

        if self._model:
            # Use model interface for business logic
            state = self._model.get_state()

            # Use current active tab if no index specified
            if index is None:
                index = state.active_tab_index

            # Get tab info before closing
            tab_name = None
            if 0 <= index < len(state.tabs):
                tab_name = state.tabs[index].name

            # Close through model
            result = self._model.close_tab(index)

            if result.success:
                # Update context
                from viloapp.core.context.manager import context_manager

                new_state = self._model.get_state()
                context_manager.set("workbench.tabs.count", len(new_state.tabs))
                context_manager.set("workbench.tabs.hasMultiple", len(new_state.tabs) > 1)

                return True
            else:
                logger.error(f"Failed to close tab: {result.error}")
                return False
        else:
            # Fallback to legacy manager
            if not self._tab_manager:
                logger.error("No model or tab manager available")
                return False

            # Get current index from model if not provided
            if index is None and self._model:
                state = self._model.get_state()
                index = state.active_tab_index

            # Get tab name from model
            tab_name = None
            if self._model and index is not None and index >= 0:
                state = self._model.get_state()
                if 0 <= index < len(state.tabs):
                    tab_name = state.tabs[index].name

            # Delegate to tab manager
            success = self._tab_manager.close_tab(index)

            if success:
                # Notify observers
                self.notify("tab_closed", {"index": index, "name": tab_name})

                # Update context
                from viloapp.core.context.manager import context_manager

                context_manager.set("workbench.tabs.count", self.get_tab_count())
                context_manager.set("workbench.tabs.hasMultiple", self.get_tab_count() > 1)

            return success

    def get_current_tab_index(self) -> int:
        """Get the index of the current tab."""
        if self._model:
            return self._model.get_state().active_tab_index
        elif self._tab_manager:
            return self._tab_manager.get_current_tab_index()
        else:
            return 0

    def get_tab_count(self) -> int:
        """Get the number of open tabs."""
        if self._model:
            return len(self._model.get_state().tabs)
        elif self._tab_manager:
            return self._tab_manager.get_tab_count()
        else:
            return 0

    def switch_to_tab(self, index: int) -> bool:
        """Switch to a specific tab."""
        self.validate_initialized()

        if self._model:
            # Use model interface
            result = self._model.set_active_tab(index)
            return result.success
        elif self._tab_manager:
            # Fallback to legacy manager
            success = self._tab_manager.switch_to_tab(index)

            if success:
                self.notify("tab_switched", {"index": index})

            return success
        else:
            logger.error("No model or tab manager available")
            return False

    def duplicate_tab(self, tab_index: int) -> int:
        """Duplicate a tab at the specified index."""
        self.validate_initialized()

        if not self._workspace:
            raise ValueError("Workspace not available")

        # Delegate to workspace method (will be updated to use tab manager)
        if hasattr(self._workspace, "duplicate_tab"):
            new_index = self._workspace.duplicate_tab(tab_index)

            # Notify observers
            self.notify("tab_duplicated", {"original_index": tab_index, "new_index": new_index})

            # Update context
            from viloapp.core.context.manager import context_manager

            context_manager.set("workbench.tabs.count", self.get_tab_count())
            context_manager.set("workbench.tabs.hasMultiple", self.get_tab_count() > 1)

            return new_index
        else:
            # Use model interface to get tab name for duplication
            if self._model:
                state = self._model.get_state()
                if 0 <= tab_index < len(state.tabs):
                    original_name = state.tabs[tab_index].name
                    new_name = f"{original_name} (Copy)"
                    return self.add_editor_tab(new_name)
                else:
                    raise ValueError(f"Invalid tab index: {tab_index}")
            else:
                raise ValueError("No model interface available for tab duplication")

    def close_tabs_to_right(self, tab_index: int) -> int:
        """Close all tabs to the right of the specified index."""
        self.validate_initialized()

        if not self._workspace:
            raise ValueError("Workspace not available")

        # Delegate to workspace method (will be updated to use tab manager)
        if hasattr(self._workspace, "close_tabs_to_right"):
            closed_count = self._workspace.close_tabs_to_right(tab_index)
        else:
            # Fallback implementation
            total_tabs = self.get_tab_count()
            closed_count = 0

            # Close tabs from right to left to maintain indices
            for i in range(total_tabs - 1, tab_index, -1):
                if self.close_tab(i):
                    closed_count += 1

        # Notify observers
        self.notify("tabs_closed_to_right", {"from_index": tab_index, "closed_count": closed_count})

        # Update context
        from viloapp.core.context.manager import context_manager

        context_manager.set("workbench.tabs.count", self.get_tab_count())
        context_manager.set("workbench.tabs.hasMultiple", self.get_tab_count() > 1)

        return closed_count

    def close_other_tabs(self, keep_tab_index: int) -> int:
        """Close all tabs except the one at the specified index."""
        self.validate_initialized()

        if not self._workspace:
            raise ValueError("Workspace not available")

        # Delegate to workspace method (will be updated to use tab manager)
        if hasattr(self._workspace, "close_other_tabs"):
            closed_count = self._workspace.close_other_tabs(keep_tab_index)
        else:
            # Fallback implementation
            total_tabs = self.get_tab_count()
            closed_count = 0

            # Close tabs from right to left to maintain indices, skipping the one to keep
            for i in range(total_tabs - 1, -1, -1):
                if i != keep_tab_index:
                    if self.close_tab(i):
                        closed_count += 1

        # Notify observers
        self.notify(
            "other_tabs_closed", {"kept_index": keep_tab_index, "closed_count": closed_count}
        )

        # Update context
        from viloapp.core.context.manager import context_manager

        context_manager.set("workbench.tabs.count", self.get_tab_count())
        context_manager.set("workbench.tabs.hasMultiple", self.get_tab_count() > 1)

        return closed_count

    def rename_tab(self, tab_index: int, new_name: str) -> bool:
        """Rename a tab at the specified index."""
        self.validate_initialized()

        if self._model:
            # Use model interface
            result = self._model.rename_tab(tab_index, new_name)
            return result.success
        elif self._workspace:
            # Fallback to legacy UI access
            if hasattr(self._workspace, "tab_widget"):
                tab_widget = self._workspace.tab_widget
                if 0 <= tab_index < tab_widget.count():
                    old_name = tab_widget.tabText(tab_index)
                    tab_widget.setTabText(tab_index, new_name)

                    # Update internal tab data if available
                    if hasattr(self._workspace, "tabs") and tab_index in self._workspace.tabs:
                        self._workspace.tabs[tab_index].name = new_name

                    # Notify observers
                    self.notify(
                        "tab_renamed",
                        {"index": tab_index, "old_name": old_name, "new_name": new_name},
                    )

                    return True
            return False
        else:
            logger.error("No model or workspace available")
            return False

    def get_tab_name(self, tab_index: int) -> str:
        """Get the name of a tab at the specified index."""
        self.validate_initialized()

        if self._model:
            # Use model interface
            state = self._model.get_state()
            if 0 <= tab_index < len(state.tabs):
                return state.tabs[tab_index].name
            return ""
        elif self._workspace and hasattr(self._workspace, "tab_widget"):
            # Fallback to legacy UI access
            tab_widget = self._workspace.tab_widget
            if 0 <= tab_index < tab_widget.count():
                return tab_widget.tabText(tab_index)
            return ""
        else:
            logger.error("No model or workspace available")
            return ""

    def start_interactive_tab_rename(self, tab_index: int) -> bool:
        """Start interactive renaming for a tab."""
        self.validate_initialized()

        # Get current tab name through service
        current_name = self.get_tab_name(tab_index)

        if self._workspace and hasattr(self._workspace, "start_tab_rename"):
            # Use workspace's interactive rename capability
            self._workspace.start_tab_rename(tab_index, current_name)

            # Notify observers
            self.notify(
                "tab_rename_started", {"tab_index": tab_index, "current_name": current_name}
            )
            return True
        else:
            logger.warning("Interactive tab rename not supported")
            return False

    def get_current_widget(self):
        """Get the current active widget in the workspace."""
        self.validate_initialized()

        if not self._workspace:
            return None

        # Delegate to workspace method
        if hasattr(self._workspace, "get_current_widget"):
            return self._workspace.get_current_widget()

        return None

    def get_current_split_widget(self):
        """Get the current split widget in the workspace."""
        self.validate_initialized()

        if not self._workspace:
            return None

        # Get current tab's split widget
        if hasattr(self._workspace, "tab_widget"):
            tab_widget = self._workspace.tab_widget
            current_tab = tab_widget.currentWidget()
            return current_tab

        return None

    # ============= Pane Operations (Delegated) =============

    def split_active_pane(self, orientation: Optional[str] = None) -> Optional[str]:
        """Split the active pane in the current tab."""
        self.validate_initialized()

        if self._model:
            # Use model interface
            state = self._model.get_state()
            active_pane = state.get_active_pane()

            if not active_pane:
                logger.error("No active pane to split")
                return None

            orientation = orientation or get_default_split_direction()
            request = SplitPaneRequest(pane_id=active_pane.id, orientation=orientation, ratio=0.5)

            result = self._model.split_pane(request)
            if result.success and result.data:
                new_pane_id = result.data.get("new_pane_id")

                # Update context
                from viloapp.core.context.manager import context_manager

                new_state = self._model.get_state()
                active_tab = new_state.get_active_tab()
                pane_count = len(active_tab.panes) if active_tab else 0

                context_manager.set("workbench.pane.count", pane_count)
                context_manager.set("workbench.pane.hasMultiple", pane_count > 1)

                return new_pane_id
            else:
                logger.error(f"Failed to split pane: {result.error}")
                return None
        elif self._pane_manager:
            # Fallback to legacy manager
            new_id = self._pane_manager.split_active_pane(orientation)

            if new_id:
                # Notify observers
                active_pane = self._pane_manager.get_active_pane_id()
                self.notify(
                    "pane_split",
                    {
                        "orientation": orientation or get_default_split_direction(),
                        "new_pane_id": new_id,
                        "parent_pane_id": active_pane,
                    },
                )

                # Update context
                from viloapp.core.context.manager import context_manager

                context_manager.set("workbench.pane.count", self.get_pane_count())
                context_manager.set("workbench.pane.hasMultiple", self.get_pane_count() > 1)

            return new_id
        else:
            logger.error("No model or pane manager available")
            return None

    def close_active_pane(self) -> bool:
        """Close the active pane in the current tab."""
        self.validate_initialized()

        # Get pane ID before closing
        pane_id = self._pane_manager.get_active_pane_id()

        # Delegate to pane manager
        success = self._pane_manager.close_active_pane()

        if success:
            # Notify observers
            self.notify("pane_closed", {"pane_id": pane_id})

            # Update context
            from viloapp.core.context.manager import context_manager

            context_manager.set("workbench.pane.count", self.get_pane_count())
            context_manager.set("workbench.pane.hasMultiple", self.get_pane_count() > 1)

        return success

    def close_pane(self, pane_id: str) -> bool:
        """Close a specific pane by its ID."""
        self.validate_initialized()

        # Delegate to pane manager
        success = self._pane_manager.close_pane(pane_id)

        if success:
            # Notify observers
            self.notify("pane_closed", {"pane_id": pane_id})

            # Update context
            from viloapp.core.context.manager import context_manager

            context_manager.set("workbench.pane.count", self.get_pane_count())
            context_manager.set("workbench.pane.hasMultiple", self.get_pane_count() > 1)

        return success

    def focus_pane(self, pane_id: str) -> bool:
        """Focus a specific pane."""
        self.validate_initialized()

        # Delegate to pane manager
        success = self._pane_manager.focus_pane(pane_id)

        if success:
            # Notify observers
            self.notify("pane_focused", {"pane_id": pane_id})

        return success

    def toggle_pane_numbers(self) -> bool:
        """Toggle the visibility of pane identification numbers."""
        self.validate_initialized()

        # Delegate to pane manager
        visible = self._pane_manager.toggle_pane_numbers()

        # Update context for conditional commands
        from viloapp.core.context.manager import context_manager

        context_manager.set("workbench.panes.numbersVisible", visible)

        # Notify observers
        self.notify("pane_numbers_toggled", {"visible": visible})

        return visible

    def show_pane_numbers(self) -> bool:
        """Show pane identification numbers."""
        self.validate_initialized()
        return self._pane_manager.show_pane_numbers()

    def hide_pane_numbers(self) -> bool:
        """Hide pane identification numbers."""
        self.validate_initialized()
        return self._pane_manager.hide_pane_numbers()

    def switch_to_pane_by_number(self, number: int) -> bool:
        """Switch to a pane by its displayed number."""
        self.validate_initialized()
        return self._pane_manager.switch_to_pane_by_number(number)

    def enter_pane_command_mode(self) -> bool:
        """Enter command mode for pane navigation."""
        self.validate_initialized()
        return self._pane_manager.enter_pane_command_mode()

    def get_pane_count(self) -> int:
        """Get the number of panes in the current tab."""
        return self._pane_manager.get_pane_count()

    def get_active_pane_id(self) -> Optional[str]:
        """Get the ID of the active pane."""
        return self._pane_manager.get_active_pane_id()

    def navigate_in_direction(self, direction: str) -> bool:
        """Navigate to a pane in the specified direction."""
        self.validate_initialized()

        # Get current pane before navigation
        from_pane = self._pane_manager.get_active_pane_id()

        # Delegate to pane manager
        success = self._pane_manager.navigate_in_direction(direction)

        if success:
            to_pane = self._pane_manager.get_active_pane_id()
            self.notify(
                "pane_navigated",
                {"from": from_pane, "to": to_pane, "direction": direction},
            )

        return success

    # ============= Layout Operations =============

    def save_layout(self) -> dict[str, Any]:
        """
        Save the current workspace layout.

        Returns:
            Dictionary containing layout state
        """
        if self._model:
            # Use model interface to get state
            state = self._model.get_state()
            # Convert to dictionary format for serialization
            return {
                "tabs": [
                    {
                        "id": tab.id,
                        "name": tab.name,
                        "pane_tree": tab.pane_tree,
                        "active_pane_id": tab.active_pane_id,
                        "panes": {
                            pane_id: {
                                "id": pane.id,
                                "widget_type": pane.widget_type.value,
                                "widget_state": pane.widget_state,
                                "is_active": pane.is_active,
                            }
                            for pane_id, pane in tab.panes.items()
                        },
                    }
                    for tab in state.tabs
                ],
                "active_tab_index": state.active_tab_index,
            }
        elif self._workspace:
            # Fallback to legacy workspace method
            return self._workspace.get_state()
        else:
            return {}

    def restore_layout(self, state: dict[str, Any]) -> bool:
        """
        Restore a workspace layout.

        Args:
            state: Layout state dictionary

        Returns:
            True if layout was restored
        """
        self.validate_initialized()

        if self._model:
            # Restore layout through model interface
            # For now, this is a simplified implementation
            # A complete implementation would reconstruct the entire workspace state
            logger.info("Layout restoration through model interface not yet fully implemented")
            self.notify("layout_restore_attempted", {"state": state})
            return True
        elif self._workspace:
            # Fallback to legacy workspace method
            try:
                self._workspace.set_state(state)
                self.notify("layout_restored", {"state": state})
                return True
            except Exception as e:
                logger.error(f"Failed to restore layout: {e}")
                return False
        else:
            logger.error("No model or workspace available for layout restoration")
            return False

    # ============= Navigation =============

    def navigate_to_next_pane(self) -> bool:
        """Navigate to the next pane in the current tab."""
        self.validate_initialized()
        return self._pane_manager.navigate_to_next_pane()

    def navigate_to_previous_pane(self) -> bool:
        """Navigate to the previous pane in the current tab."""
        self.validate_initialized()
        return self._pane_manager.navigate_to_previous_pane()

    def change_pane_widget_type(self, pane_id: str, widget_type: str) -> bool:
        """Change the widget type of a specific pane."""
        self.validate_initialized()

        if self._model:
            # Use model interface for changing widget type
            try:
                # Convert string to WidgetType enum
                widget_type_enum = WidgetType(widget_type)
            except ValueError:
                logger.error(f"Invalid widget type: {widget_type}")
                return False

            request = WidgetStateUpdateRequest(
                pane_id=pane_id, widget_type=widget_type_enum, widget_state={}
            )
            result = self._model.update_widget_state(request)

            if result.success:
                # Notify observers
                self.notify("pane_widget_changed", {"pane_id": pane_id, "widget_type": widget_type})
                return True
            else:
                logger.error(f"Failed to change pane widget type: {result.error}")
                return False
        elif self._pane_manager:
            # Fallback to legacy pane manager
            return self._pane_manager.change_pane_widget_type(pane_id, widget_type)
        else:
            logger.error("No model or pane manager available")
            return False

    # ============= Plugin Widget Factory Methods =============

    def register_widget_factory(self, widget_id: str, factory: Any) -> None:
        """Register a widget factory (for plugins)."""
        self._widget_factories[widget_id] = factory
        logger.info(f"Registered widget factory: {widget_id}")

    def create_widget(self, widget_id: str, instance_id: str) -> Optional[Any]:
        """Create a widget using registered factory."""
        if widget_id in self._widget_factories:
            factory = self._widget_factories[widget_id]
            # Handle both IWidget and direct factory functions
            if hasattr(factory, "create_instance"):
                return factory.create_instance(instance_id)
            elif callable(factory):
                return factory(instance_id)
        return None

    def get_widget_factories(self) -> dict[str, Any]:
        """Get all registered widget factories."""
        return self._widget_factories.copy()

    # ============= Utility Methods =============

    def get_workspace_info(self) -> dict[str, Any]:
        """Get comprehensive workspace information."""
        if not self._workspace:
            return {"available": False, "tab_count": 0, "current_tab": -1}

        # Combine information from all managers
        tab_info = self._tab_manager.get_tab_info()
        pane_info = self._pane_manager.get_pane_info()

        return {
            "available": True,
            "tab_count": tab_info["count"],
            "current_tab": tab_info["current"],
            "current_tab_info": tab_info.get("current_tab_info"),
            "pane_count": pane_info["count"],
            "active_pane_id": pane_info["active"],
        }
