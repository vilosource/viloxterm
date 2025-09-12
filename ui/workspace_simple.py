#!/usr/bin/env python3
"""
New workspace implementation using tabs with SplitPaneWidget.
Each tab has its own independent split layout.
"""

import logging
from typing import Optional, Dict, List
from PySide6.QtWidgets import (
    QWidget, QTabWidget, QVBoxLayout, QMenu, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from ui.widgets.split_pane_widget import SplitPaneWidget
from ui.widgets.widget_registry import WidgetType
from ui.widgets.rename_editor import RenameEditor
from ui.vscode_theme import *
from core.commands.executor import execute_command

logger = logging.getLogger(__name__)


class WorkspaceTab:
    """Container for tab data."""
    def __init__(self, name: str, split_widget: SplitPaneWidget):
        self.name = name
        self.split_widget = split_widget
        self.metadata = {}  # For storing additional tab data


class Workspace(QWidget):
    """
    Central workspace with tabs.
    Each tab contains its own SplitPaneWidget for independent layouts.
    """
    
    # Signals
    tab_changed = Signal(int)  # tab index
    tab_added = Signal(str)  # tab name
    tab_removed = Signal(str)  # tab name
    active_pane_changed = Signal(str, str)  # tab_name, pane_id
    layout_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tabs: Dict[int, WorkspaceTab] = {}  # index -> WorkspaceTab
        self.setup_ui()
        self.create_default_tab()
    
    def setup_ui(self):
        """Initialize the workspace UI."""
        self.setObjectName("workspace")
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setElideMode(Qt.ElideRight)
        
        # Apply VSCode theme to tab widget
        self.tab_widget.setStyleSheet(get_tab_widget_stylesheet())
        
        layout.addWidget(self.tab_widget)
        
        # Connect signals
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.tab_widget.tabBarDoubleClicked.connect(self.on_tab_double_clicked)
        
        # Enable context menu on tab bar
        self.tab_widget.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_widget.tabBar().customContextMenuRequested.connect(self.show_tab_context_menu)
    
    def _cleanup_split_widget(self, split_widget: SplitPaneWidget):
        """Clean up a split widget and all its AppWidgets before removal."""
        # The new architecture: just call cleanup on the widget
        # It will use the model's tree traversal to clean up all AppWidgets
        split_widget.cleanup()
        
        # Delete the widget
        split_widget.deleteLater()
    
    def create_default_tab(self):
        """Create the initial default tab."""
        self.add_editor_tab("Welcome")
    
    def add_editor_tab(self, name: str = "Editor") -> int:
        """Add a new editor tab with split pane widget."""
        split_widget = SplitPaneWidget(
            initial_widget_type=WidgetType.TEXT_EDITOR
        )
        
        # Connect split widget signals
        split_widget.pane_added.connect(
            lambda pane_id: self.on_pane_added(name, pane_id)
        )
        split_widget.pane_removed.connect(
            lambda pane_id: self.on_pane_removed(name, pane_id)
        )
        split_widget.active_pane_changed.connect(
            lambda pane_id: self.active_pane_changed.emit(name, pane_id)
        )
        split_widget.layout_changed.connect(self.layout_changed.emit)
        
        # Add to tab widget
        index = self.tab_widget.addTab(split_widget, name)
        
        # Store tab data
        self.tabs[index] = WorkspaceTab(name, split_widget)
        
        # Switch to new tab
        self.tab_widget.setCurrentIndex(index)
        
        # Emit signal
        self.tab_added.emit(name)
        
        return index
    
    def add_terminal_tab(self, name: str = "Terminal") -> int:
        """Add a new terminal tab."""
        split_widget = SplitPaneWidget(
            initial_widget_type=WidgetType.TERMINAL
        )
        
        # Connect signals
        split_widget.pane_added.connect(
            lambda pane_id: self.on_pane_added(name, pane_id)
        )
        split_widget.pane_removed.connect(
            lambda pane_id: self.on_pane_removed(name, pane_id)
        )
        split_widget.active_pane_changed.connect(
            lambda pane_id: self.active_pane_changed.emit(name, pane_id)
        )
        
        # Add to tab widget
        index = self.tab_widget.addTab(split_widget, name)
        
        # Store tab data
        self.tabs[index] = WorkspaceTab(name, split_widget)
        
        # Switch to new tab
        self.tab_widget.setCurrentIndex(index)
        
        # Emit signal
        self.tab_added.emit(name)
        
        return index
    
    def add_output_tab(self, name: str = "Output") -> int:
        """Add a new output tab."""
        split_widget = SplitPaneWidget(
            initial_widget_type=WidgetType.OUTPUT
        )
        
        # Connect signals
        split_widget.pane_added.connect(
            lambda pane_id: self.on_pane_added(name, pane_id)
        )
        split_widget.pane_removed.connect(
            lambda pane_id: self.on_pane_removed(name, pane_id)
        )
        split_widget.active_pane_changed.connect(
            lambda pane_id: self.active_pane_changed.emit(name, pane_id)
        )
        
        # Add to tab widget
        index = self.tab_widget.addTab(split_widget, name)
        
        # Store tab data
        self.tabs[index] = WorkspaceTab(name, split_widget)
        
        # Switch to new tab
        self.tab_widget.setCurrentIndex(index)
        
        # Emit signal
        self.tab_added.emit(name)
        
        return index
    
    def close_tab(self, index: int):
        """Close a tab."""
        # Don't close the last tab
        if self.tab_widget.count() <= 1:
            QMessageBox.information(
                self,
                "Cannot Close Tab",
                "Cannot close the last remaining tab."
            )
            return
        
        # Get tab data
        if index in self.tabs:
            tab_data = self.tabs[index]
            
            # Clean up the split widget's terminals before removing
            if tab_data.split_widget:
                self._cleanup_split_widget(tab_data.split_widget)
            
            # Remove from tabs dict
            del self.tabs[index]
            
            # Remove from tab widget
            self.tab_widget.removeTab(index)
            
            # Update indices for remaining tabs
            new_tabs = {}
            for i in range(self.tab_widget.count()):
                # Find the tab data that corresponds to this widget
                widget = self.tab_widget.widget(i)
                for old_index, data in self.tabs.items():
                    if data.split_widget == widget:
                        new_tabs[i] = data
                        break
            self.tabs = new_tabs
            
            # Emit signal
            self.tab_removed.emit(tab_data.name)
    
    def get_current_split_widget(self) -> Optional[SplitPaneWidget]:
        """Get the current tab's split widget."""
        index = self.tab_widget.currentIndex()
        if index >= 0:
            widget = self.tab_widget.widget(index)
            if isinstance(widget, SplitPaneWidget):
                return widget
            # If stored in tabs dict, get from there
            if index in self.tabs:
                return self.tabs[index].split_widget
        return None
    
    def on_tab_changed(self, index: int):
        """Handle tab change."""
        self.tab_changed.emit(index)
    
    def on_tab_double_clicked(self, index: int):
        """Handle tab double-click (could be used for renaming)."""
        # Basic implementation: create rename editor
        current_text = self.tab_widget.tabText(index)
        self.start_tab_rename(index, current_text)
    
    def start_tab_rename(self, index: int, current_text: str):
        """Start renaming a tab with inline editor."""
        if index < 0 or index >= self.tab_widget.count():
            return
        
        # Create rename editor
        self.rename_editor = RenameEditor(current_text, self)
        
        # Connect signals
        self.rename_editor.rename_completed.connect(
            lambda name: self.complete_tab_rename(index, name)
        )
        self.rename_editor.rename_cancelled.connect(self.cancel_tab_rename)
        
        # Position the editor over the tab
        tab_bar = self.tab_widget.tabBar()
        tab_rect = tab_bar.tabRect(index)
        self.rename_editor.setGeometry(tab_rect)
        self.rename_editor.show()
        self.rename_editor.setFocus()
        
    def complete_tab_rename(self, index: int, new_name: str):
        """Complete tab rename with validation."""
        if not hasattr(self, 'rename_editor'):
            return
            
        # Clean up the rename editor
        self.rename_editor.hide()
        self.rename_editor.deleteLater()
        delattr(self, 'rename_editor')
        
        # Validate and apply new name
        new_name = new_name.strip()
        if new_name and index in self.tabs:
            self.tab_widget.setTabText(index, new_name)
            self.tabs[index].name = new_name
            
    def cancel_tab_rename(self):
        """Cancel tab rename."""
        if not hasattr(self, 'rename_editor'):
            return
            
        # Clean up the rename editor
        self.rename_editor.hide()
        self.rename_editor.deleteLater()
        delattr(self, 'rename_editor')
        
    def on_pane_added(self, tab_name: str, pane_id: str):
        """Handle pane added in a tab."""
        # Could update status or emit combined signal
        pass
    
    def on_pane_removed(self, tab_name: str, pane_id: str):
        """Handle pane removed in a tab."""
        # Could update status or emit combined signal
        pass
    
    def show_tab_context_menu(self, pos):
        """Show context menu for tabs."""
        # Get the tab index at position
        index = self.tab_widget.tabBar().tabAt(pos)
        if index < 0:
            return
        
        menu = QMenu(self)
        menu.setStyleSheet(get_menu_stylesheet())
        
        # Duplicate tab action
        duplicate_action = QAction("Duplicate Tab", self)
        duplicate_action.triggered.connect(lambda: execute_command("workbench.action.duplicateTab", tab_index=index))
        menu.addAction(duplicate_action)
        
        # Close other tabs
        if self.tab_widget.count() > 1:
            close_others_action = QAction("Close Other Tabs", self)
            close_others_action.triggered.connect(lambda: execute_command("workbench.action.closeOtherTabs", tab_index=index))
            menu.addAction(close_others_action)
        
        # Close tabs to the right
        if index < self.tab_widget.count() - 1:
            close_right_action = QAction("Close Tabs to the Right", self)
            close_right_action.triggered.connect(lambda: execute_command("workbench.action.closeTabsToRight", tab_index=index))
            menu.addAction(close_right_action)
        
        menu.addSeparator()
        
        # Rename tab
        rename_action = QAction("Rename Tab", self)
        rename_action.triggered.connect(
            lambda: execute_command("workbench.action.renameTab", tab_index=index)
        )
        menu.addAction(rename_action)
        
        menu.addSeparator()
        
        # Close tab
        close_action = QAction("Close Tab", self)
        close_action.triggered.connect(lambda: execute_command("file.closeTab", tab_index=index))
        menu.addAction(close_action)
        
        menu.exec(self.tab_widget.tabBar().mapToGlobal(pos))
    
    def duplicate_tab(self, index: int):
        """Duplicate a tab."""
        if index in self.tabs:
            tab_data = self.tabs[index]
            # Create new tab with same type
            # TODO: Could also duplicate the split layout
            self.add_editor_tab(f"{tab_data.name} (Copy)")
    
    def close_other_tabs(self, keep_index: int):
        """Close all tabs except the specified one."""
        # Close from right to left to maintain indices
        for i in range(self.tab_widget.count() - 1, -1, -1):
            if i != keep_index:
                self.close_tab(i)
    
    def close_tabs_to_right(self, index: int):
        """Close all tabs to the right of the specified index."""
        # Close from right to left to maintain indices
        for i in range(self.tab_widget.count() - 1, index, -1):
            self.close_tab(i)
    
    # Public API for compatibility with existing code
    
    def split_active_pane_horizontal(self):
        """Split the active pane in the current tab horizontally."""
        widget = self.get_current_split_widget()
        if widget and widget.active_pane_id:
            widget.split_horizontal(widget.active_pane_id)
    
    def split_active_pane_vertical(self):
        """Split the active pane in the current tab vertically."""
        widget = self.get_current_split_widget()
        if widget and widget.active_pane_id:
            widget.split_vertical(widget.active_pane_id)
    
    def close_active_pane(self):
        """Close the active pane in the current tab."""
        widget = self.get_current_split_widget()
        if widget and widget.active_pane_id:
            if widget.get_pane_count() > 1:
                widget.close_pane(widget.active_pane_id)
            else:
                QMessageBox.information(
                    self,
                    "Cannot Close Pane",
                    "Cannot close the last remaining pane in a tab."
                )
    
    def get_current_tab_info(self) -> Optional[Dict]:
        """Get information about the current tab."""
        index = self.tab_widget.currentIndex()
        if index >= 0 and index in self.tabs:
            tab_data = self.tabs[index]
            widget = tab_data.split_widget
            return {
                "name": tab_data.name,
                "index": index,
                "pane_count": widget.get_pane_count(),
                "active_pane": widget.active_pane_id,
                "all_panes": widget.get_all_pane_ids()
            }
        return None
    
    def get_tab_count(self) -> int:
        """Get the number of tabs."""
        return self.tab_widget.count()
    
    # Save/restore state
    
    def save_state(self) -> Dict:
        """Save workspace state."""
        state = {
            "current_tab": self.tab_widget.currentIndex(),
            "tabs": []
        }
        
        for i in range(self.tab_widget.count()):
            if i in self.tabs:
                tab_data = self.tabs[i]
                tab_state = {
                    "name": tab_data.name,
                    "split_state": tab_data.split_widget.get_state()
                }
                state["tabs"].append(tab_state)
        
        return state
    
    def restore_state(self, state: Dict):
        """Restore workspace state."""
        # Clear existing tabs
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        self.tabs.clear()
        
        # Restore tabs
        if "tabs" in state:
            for tab_state in state["tabs"]:
                # Create tab (for now just create editor tabs)
                index = self.add_editor_tab(tab_state.get("name", "Editor"))
                
                # Restore split state
                if index in self.tabs and "split_state" in tab_state:
                    try:
                        success = self.tabs[index].split_widget.set_state(tab_state["split_state"])
                        if not success:
                            logger.warning(f"Failed to restore split state for tab: {tab_state.get('name', 'Unknown')}")
                    except Exception as e:
                        logger.error(f"Error restoring split state for tab {tab_state.get('name', 'Unknown')}: {e}")
        
        # Restore current tab
        if "current_tab" in state:
            self.tab_widget.setCurrentIndex(state["current_tab"])
        
        # Create default tab if none were restored
        if self.tab_widget.count() == 0:
            self.create_default_tab()
    
    def reset_to_default_layout(self):
        """Reset workspace to default single pane layout."""
        # Clean up all existing tabs properly
        for tab_data in self.tabs.values():
            if tab_data.split_widget:
                self._cleanup_split_widget(tab_data.split_widget)
        
        # Clear all tabs
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        self.tabs.clear()
        
        # Create default tab
        self.create_default_tab()