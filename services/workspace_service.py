#!/usr/bin/env python3
"""
Workspace service for managing tabs, panes, and layouts.

This service encapsulates all workspace-related business logic,
providing a clean interface for commands and UI components.
"""

from typing import Optional, Dict, Any, List, Tuple
import logging

from services.base import Service

logger = logging.getLogger(__name__)


class WorkspaceService(Service):
    """
    Service for managing workspace operations.
    
    Handles tab management, pane splitting, layout operations,
    and workspace state management.
    """
    
    def __init__(self, workspace=None):
        """
        Initialize the workspace service.
        
        Args:
            workspace: Optional workspace instance
        """
        super().__init__("WorkspaceService")
        self._workspace = workspace
        self._tab_counter = 0
        self._pane_counter = 0
        
    def initialize(self, context: Dict[str, Any]) -> None:
        """Initialize the service with application context."""
        super().initialize(context)
        
        # Get workspace from context if not provided
        if not self._workspace:
            self._workspace = context.get('workspace')
        
        if not self._workspace:
            logger.warning("WorkspaceService initialized without workspace reference")
    
    def cleanup(self) -> None:
        """Cleanup service resources."""
        self._workspace = None
        super().cleanup()
    
    # ============= Tab Operations =============
    
    def add_editor_tab(self, name: Optional[str] = None) -> int:
        """
        Add a new editor tab to the workspace.
        
        Args:
            name: Optional tab name, auto-generated if not provided
            
        Returns:
            Index of the created tab
            
        Raises:
            RuntimeError: If workspace is not available
        """
        self.validate_initialized()
        
        if not self._workspace:
            raise RuntimeError("Workspace not available")
        
        # Auto-generate name if not provided
        if not name:
            self._tab_counter += 1
            name = f"Editor {self._tab_counter}"
        
        # Add the tab
        index = self._workspace.add_editor_tab(name)
        
        # Notify observers
        self.notify('tab_added', {
            'type': 'editor',
            'name': name,
            'index': index
        })
        
        # Update context
        from core.context.manager import context_manager
        context_manager.set('workbench.tabs.count', self.get_tab_count())
        context_manager.set('workbench.tabs.hasMultiple', self.get_tab_count() > 1)
        
        logger.info(f"Added editor tab '{name}' at index {index}")
        return index
    
    def add_terminal_tab(self, name: Optional[str] = None) -> int:
        """
        Add a new terminal tab to the workspace.
        
        Args:
            name: Optional tab name, auto-generated if not provided
            
        Returns:
            Index of the created tab
            
        Raises:
            RuntimeError: If workspace is not available
        """
        self.validate_initialized()
        
        if not self._workspace:
            raise RuntimeError("Workspace not available")
        
        # Auto-generate name if not provided
        if not name:
            self._tab_counter += 1
            name = f"Terminal {self._tab_counter}"
        
        # Add the tab
        index = self._workspace.add_terminal_tab(name)
        
        # Notify observers
        self.notify('tab_added', {
            'type': 'terminal',
            'name': name,
            'index': index
        })
        
        # Update context
        from core.context.manager import context_manager
        context_manager.set('workbench.tabs.count', self.get_tab_count())
        context_manager.set('workbench.tabs.hasMultiple', self.get_tab_count() > 1)
        
        logger.info(f"Added terminal tab '{name}' at index {index}")
        return index
    
    def close_tab(self, index: Optional[int] = None) -> bool:
        """
        Close a tab.
        
        Args:
            index: Tab index to close, or None for current tab
            
        Returns:
            True if tab was closed
        """
        self.validate_initialized()
        
        if not self._workspace:
            return False
        
        # Get current index if not provided
        if index is None:
            index = self._workspace.tab_widget.currentIndex()
        
        if index < 0:
            return False
        
        # Get tab info before closing
        tab_info = self._workspace.get_tab_info(index)
        
        # Close the tab
        self._workspace.close_tab(index)
        
        # Notify observers
        self.notify('tab_closed', {
            'index': index,
            'name': tab_info.get('name') if tab_info else None
        })
        
        # Update context
        from core.context.manager import context_manager
        context_manager.set('workbench.tabs.count', self.get_tab_count())
        context_manager.set('workbench.tabs.hasMultiple', self.get_tab_count() > 1)
        
        logger.info(f"Closed tab at index {index}")
        return True
    
    def get_current_tab_index(self) -> int:
        """
        Get the index of the current tab.
        
        Returns:
            Current tab index, or -1 if no tabs
        """
        if not self._workspace:
            return -1
        return self._workspace.tab_widget.currentIndex()
    
    def get_tab_count(self) -> int:
        """
        Get the number of open tabs.
        
        Returns:
            Number of tabs
        """
        if not self._workspace:
            return 0
        return self._workspace.tab_widget.count()
    
    def switch_to_tab(self, index: int) -> bool:
        """
        Switch to a specific tab.
        
        Args:
            index: Tab index
            
        Returns:
            True if switched successfully
        """
        self.validate_initialized()
        
        if not self._workspace:
            return False
        
        if 0 <= index < self._workspace.tab_widget.count():
            self._workspace.tab_widget.setCurrentIndex(index)
            
            self.notify('tab_switched', {'index': index})
            return True
        
        return False
    
    # ============= Pane Operations =============
    
    def split_active_pane(self, orientation: str = "horizontal") -> Optional[str]:
        """
        Split the active pane in the current tab.
        
        Args:
            orientation: "horizontal" or "vertical"
            
        Returns:
            ID of the new pane, or None if split failed
        """
        self.validate_initialized()
        
        if not self._workspace:
            return None
        
        # Get current split widget
        widget = self._workspace.get_current_split_widget()
        if not widget or not widget.active_pane_id:
            logger.warning("No active pane to split")
            return None
        
        # Perform the split
        if orientation == "horizontal":
            new_id = widget.split_horizontal(widget.active_pane_id)
        elif orientation == "vertical":
            new_id = widget.split_vertical(widget.active_pane_id)
        else:
            logger.error(f"Invalid split orientation: {orientation}")
            return None
        
        if new_id:
            self._pane_counter += 1
            
            # Notify observers
            self.notify('pane_split', {
                'orientation': orientation,
                'new_pane_id': new_id,
                'parent_pane_id': widget.active_pane_id
            })
            
            # Update context
            from core.context.manager import context_manager
            context_manager.set('workbench.pane.count', self.get_pane_count())
            context_manager.set('workbench.pane.hasMultiple', self.get_pane_count() > 1)
            
            logger.info(f"Split pane {orientation}ly, created pane {new_id}")
        
        return new_id
    
    def close_active_pane(self) -> bool:
        """
        Close the active pane in the current tab.
        
        Returns:
            True if pane was closed
        """
        self.validate_initialized()
        
        if not self._workspace:
            return False
        
        # Get current split widget
        widget = self._workspace.get_current_split_widget()
        if not widget or not widget.active_pane_id:
            logger.warning("No active pane to close")
            return False
        
        # Can't close if it's the only pane
        if widget.get_pane_count() <= 1:
            logger.info("Cannot close the last pane")
            return False
        
        pane_id = widget.active_pane_id
        
        # Close the pane
        widget.close_pane(pane_id)
        
        # Notify observers
        self.notify('pane_closed', {'pane_id': pane_id})
        
        # Update context
        from core.context.manager import context_manager
        context_manager.set('workbench.pane.count', self.get_pane_count())
        context_manager.set('workbench.pane.hasMultiple', self.get_pane_count() > 1)
        
        logger.info(f"Closed pane {pane_id}")
        return True
    
    def focus_pane(self, pane_id: str) -> bool:
        """
        Focus a specific pane.
        
        Args:
            pane_id: ID of the pane to focus
            
        Returns:
            True if pane was focused
        """
        self.validate_initialized()
        
        if not self._workspace:
            return False
        
        widget = self._workspace.get_current_split_widget()
        if not widget:
            return False
        
        # Set the active pane AND request keyboard focus
        widget.set_active_pane(pane_id, focus=True)
        
        # Notify observers
        self.notify('pane_focused', {'pane_id': pane_id})
        
        return True
    
    def toggle_pane_numbers(self) -> bool:
        """
        Toggle the visibility of pane identification numbers.
        
        Returns:
            New visibility state (True if now visible, False if hidden)
        """
        self.validate_initialized()
        
        if not self._workspace:
            logger.warning("Cannot toggle pane numbers: workspace not available")
            return False
        
        widget = self._workspace.get_current_split_widget()
        if not widget:
            logger.warning("Cannot toggle pane numbers: no current split widget")
            return False
        
        # Toggle the numbers
        visible = widget.toggle_pane_numbers()
        
        # Update context for conditional commands
        from core.context.manager import context_manager
        context_manager.set('workbench.panes.numbersVisible', visible)
        
        # Notify observers
        self.notify('pane_numbers_toggled', {'visible': visible})
        
        logger.info(f"Pane numbers {'shown' if visible else 'hidden'}")
        return visible
    
    def show_pane_numbers(self) -> bool:
        """
        Show pane identification numbers.
        
        Returns:
            True if numbers are now visible
        """
        self.validate_initialized()
        
        if not self._workspace:
            return False
        
        widget = self._workspace.get_current_split_widget()
        if not widget:
            return False
        
        # Show the numbers if not already visible
        if hasattr(widget, 'model') and not widget.model.show_pane_numbers:
            widget.toggle_pane_numbers()
            logger.info("Pane numbers shown")
            return True
        
        return False
    
    def hide_pane_numbers(self) -> bool:
        """
        Hide pane identification numbers.
        
        Returns:
            True if numbers are now hidden
        """
        self.validate_initialized()
        
        if not self._workspace:
            return False
        
        widget = self._workspace.get_current_split_widget()
        if not widget:
            return False
        
        # Hide the numbers if currently visible
        if hasattr(widget, 'model') and widget.model.show_pane_numbers:
            widget.toggle_pane_numbers()
            logger.info("Pane numbers hidden")
            return True
        
        return False
    
    def switch_to_pane_by_number(self, number: int) -> bool:
        """
        Switch to a pane by its displayed number.
        
        Args:
            number: The pane number (1-9)
            
        Returns:
            True if successfully switched to the pane
        """
        self.validate_initialized()
        
        if not self._workspace:
            logger.warning("Cannot switch pane: workspace not available")
            return False
        
        widget = self._workspace.get_current_split_widget()
        if not widget:
            logger.warning("Cannot switch pane: no current split widget")
            return False
        
        # Find the pane ID for the given number
        if hasattr(widget, 'model') and hasattr(widget.model, 'pane_indices'):
            # Reverse lookup: find pane_id for the given number
            for pane_id, pane_number in widget.model.pane_indices.items():
                if pane_number == number:
                    # Focus the pane
                    if self.focus_pane(pane_id):
                        logger.info(f"Switched to pane {number} (id: {pane_id})")
                        return True
                    break
        
        logger.warning(f"Could not find pane with number {number}")
        return False
    
    def enter_pane_command_mode(self) -> bool:
        """
        Enter command mode for pane navigation.
        Shows pane numbers and prepares for digit input.
        
        Returns:
            True if command mode was entered successfully
        """
        self.validate_initialized()
        
        # Show pane numbers
        if not self.show_pane_numbers():
            logger.warning("Could not enter pane command mode: no panes to show")
            return False
        
        # Get main window and activate focus sink
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            for window in app.topLevelWidgets():
                if hasattr(window, 'focus_sink'):
                    # Get currently focused widget to restore later
                    current_focus = app.focusWidget()
                    
                    # Enter command mode with focus sink
                    window.focus_sink.enter_command_mode(current_focus)
                    logger.info("Entered pane command mode")
                    return True
        
        logger.warning("Could not find main window with focus sink")
        return False
    
    def get_pane_count(self) -> int:
        """
        Get the number of panes in the current tab.
        
        Returns:
            Number of panes
        """
        if not self._workspace:
            return 0
        
        widget = self._workspace.get_current_split_widget()
        return widget.get_pane_count() if widget else 0
    
    def get_active_pane_id(self) -> Optional[str]:
        """
        Get the ID of the active pane.
        
        Returns:
            Active pane ID or None
        """
        if not self._workspace:
            return None
        
        widget = self._workspace.get_current_split_widget()
        return widget.active_pane_id if widget else None
    
    def navigate_in_direction(self, direction: str) -> bool:
        """
        Navigate to a pane in the specified direction.
        
        Uses tree structure and position overlap to find the most intuitive target.
        
        Args:
            direction: One of "left", "right", "up", "down"
            
        Returns:
            True if successfully navigated to a pane
        """
        self.validate_initialized()
        
        if not self._workspace:
            return False
        
        widget = self._workspace.get_current_split_widget()
        if not widget or not widget.active_pane_id:
            logger.warning("No active pane to navigate from")
            return False
        
        # Use the model's directional navigation
        target_id = widget.model.find_pane_in_direction(
            widget.active_pane_id, direction
        )
        
        if target_id:
            widget.focus_specific_pane(target_id)
            success = True  # focus_specific_pane doesn't return a value
            if success:
                logger.info(f"Navigated {direction} from {widget.active_pane_id} to {target_id}")
                self.notify('pane_navigated', {
                    'from': widget.active_pane_id,
                    'to': target_id,
                    'direction': direction
                })
            return success
        else:
            logger.debug(f"No pane found in direction: {direction}")
            return False
    
    # ============= Layout Operations =============
    
    def save_layout(self) -> Dict[str, Any]:
        """
        Save the current workspace layout.
        
        Returns:
            Dictionary containing layout state
        """
        if not self._workspace:
            return {}
        
        return self._workspace.get_state()
    
    def restore_layout(self, state: Dict[str, Any]) -> bool:
        """
        Restore a workspace layout.
        
        Args:
            state: Layout state dictionary
            
        Returns:
            True if layout was restored
        """
        self.validate_initialized()
        
        if not self._workspace:
            return False
        
        try:
            self._workspace.set_state(state)
            
            self.notify('layout_restored', {'state': state})
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore layout: {e}")
            return False
    
    # ============= Navigation =============
    
    def navigate_to_next_pane(self) -> bool:
        """
        Navigate to the next pane in the current tab.
        
        Returns:
            True if navigation succeeded
        """
        self.validate_initialized()
        
        if not self._workspace:
            return False
        
        widget = self._workspace.get_current_split_widget()
        if not widget:
            return False
        
        # Get all pane IDs
        panes = widget.get_all_pane_ids()
        if len(panes) <= 1:
            return False
        
        # Find current pane index
        current_id = widget.active_pane_id
        if current_id not in panes:
            return False
        
        current_index = panes.index(current_id)
        next_index = (current_index + 1) % len(panes)
        
        return self.focus_pane(panes[next_index])
    
    def navigate_to_previous_pane(self) -> bool:
        """
        Navigate to the previous pane in the current tab.
        
        Returns:
            True if navigation succeeded
        """
        self.validate_initialized()
        
        if not self._workspace:
            return False
        
        widget = self._workspace.get_current_split_widget()
        if not widget:
            return False
        
        # Get all pane IDs
        panes = widget.get_all_pane_ids()
        if len(panes) <= 1:
            return False
        
        # Find current pane index
        current_id = widget.active_pane_id
        if current_id not in panes:
            return False
        
        current_index = panes.index(current_id)
        prev_index = (current_index - 1) % len(panes)
        
        return self.focus_pane(panes[prev_index])
    
    # ============= Utility Methods =============
    
    def get_workspace_info(self) -> Dict[str, Any]:
        """
        Get comprehensive workspace information.
        
        Returns:
            Dictionary with workspace state information
        """
        if not self._workspace:
            return {
                'available': False,
                'tab_count': 0,
                'current_tab': -1
            }
        
        current_index = self.get_current_tab_index()
        widget = self._workspace.get_current_split_widget()
        
        return {
            'available': True,
            'tab_count': self.get_tab_count(),
            'current_tab': current_index,
            'current_tab_info': self._workspace.get_current_tab_info(),
            'pane_count': widget.get_pane_count() if widget else 0,
            'active_pane_id': widget.active_pane_id if widget else None
        }