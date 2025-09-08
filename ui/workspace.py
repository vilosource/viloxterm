"""Workspace implementation with recursive split functionality."""

from typing import Optional, Dict
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QTimer
from ui.widgets.split_tree import SplitTreeManager
from ui.widgets.tab_container import TabContainer
from models.layout_state import LayoutState, ContentPane, TabInfo


class Workspace(QWidget):
    """Central workspace area with recursive split panes and tabs."""
    
    # Signals
    active_pane_changed = Signal(str)  # pane_id
    layout_changed = Signal()
    pane_count_changed = Signal(int)  # number of panes
    
    def __init__(self):
        super().__init__()
        
        # Initialize split tree manager
        self.split_manager = SplitTreeManager()
        
        # Keep track of tab container widgets
        self._tab_containers: Dict[str, TabContainer] = {}
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Initialize the workspace UI."""
        self.setObjectName("workspace")
        
        # Create main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Create initial widget tree
        self._rebuild_ui()
        
    def setup_connections(self):
        """Setup signal connections."""
        # Connect split manager signals
        self.split_manager.layout_changed.connect(self._on_layout_changed)
        self.split_manager.active_pane_changed.connect(self.active_pane_changed.emit)
        self.split_manager.pane_split.connect(self._on_pane_split)
        self.split_manager.pane_closed.connect(self._on_pane_closed)
        
    def _rebuild_ui(self):
        """Rebuild the UI from the split tree."""
        # Clear existing layout
        if self.layout.count() > 0:
            old_widget = self.layout.takeAt(0).widget()
            if old_widget:
                old_widget.deleteLater()
        
        # Create new widget tree
        root_widget = self.split_manager.root_widget
        if root_widget:
            self.layout.addWidget(root_widget)
            self._setup_tab_containers_recursive(root_widget)
        
    def _setup_tab_containers_recursive(self, widget):
        """Recursively setup tab containers with proper connections."""
        if isinstance(widget, TabContainer):
            pane_id = widget.get_pane_id()
            self._tab_containers[pane_id] = widget
            
            # Connect tab container signals
            widget.split_horizontal_requested.connect(self.split_pane_horizontal)
            widget.split_vertical_requested.connect(self.split_pane_vertical)
            widget.close_pane_requested.connect(self.close_pane)
            widget.tab_close_requested.connect(self._on_tab_close_requested)
            widget.tab_moved_to_new_pane.connect(self._on_tab_moved_to_new_pane)
            widget.pane_activated.connect(self.set_active_pane)
            
        elif hasattr(widget, 'count'):
            # Handle splitters and other containers
            for i in range(widget.count()):
                child = widget.widget(i)
                if child:
                    self._setup_tab_containers_recursive(child)
    
    def _on_layout_changed(self):
        """Handle layout changes."""
        self._rebuild_ui()
        self.layout_changed.emit()
        
        # Update pane count
        pane_count = len(self.split_manager.get_all_pane_ids())
        self.pane_count_changed.emit(pane_count)
        
    def _on_pane_split(self, old_pane_id: str, new_pane_id: str):
        """Handle pane split events."""
        # The UI rebuild will handle creating new tab containers
        pass
        
    def _on_pane_closed(self, pane_id: str):
        """Handle pane close events."""
        # Remove from our tracking
        if pane_id in self._tab_containers:
            del self._tab_containers[pane_id]
            
    def _on_tab_close_requested(self, pane_id: str, tab_index: int):
        """Handle tab close request."""
        tab_container = self._tab_containers.get(pane_id)
        if tab_container:
            # Check if this is the last pane and last tab
            pane_count = self.get_pane_count()
            if pane_count == 1 and tab_container.count() == 1:
                # Last tab in last pane - add a placeholder instead of closing
                tab_container.removeTab(tab_index)
                tab_container.add_placeholder_tab()
                tab_container.tab_closed.emit(pane_id, tab_index)
            else:
                # Normal close - will either close tab or entire pane
                tab_container.close_tab(tab_index)
    
    def _on_tab_moved_to_new_pane(self, tab_id: str, orientation: str):
        """Handle tab being moved to a new pane."""
        # For now, we'll implement this as splitting the pane and moving the tab
        # This is a simplified version - full implementation would move the actual tab
        sender = self.sender()
        if isinstance(sender, TabContainer):
            pane_id = sender.get_pane_id()
            if orientation == "horizontal":
                self.split_pane_horizontal(pane_id)
            else:
                self.split_pane_vertical(pane_id)
    
    # Public API
    
    def split_pane_horizontal(self, pane_id: Optional[str] = None) -> Optional[str]:
        """Split a pane horizontally. Returns new pane ID or None if failed."""
        if pane_id is None:
            pane_id = self.split_manager.get_active_pane_id()
        
        if pane_id:
            return self.split_manager.split_pane(pane_id, Qt.Horizontal)
        return None
        
    def split_pane_vertical(self, pane_id: Optional[str] = None) -> Optional[str]:
        """Split a pane vertically. Returns new pane ID or None if failed."""
        if pane_id is None:
            pane_id = self.split_manager.get_active_pane_id()
        
        if pane_id:
            return self.split_manager.split_pane(pane_id, Qt.Vertical)
        return None
        
    def close_pane(self, pane_id: Optional[str] = None) -> bool:
        """Close a pane. Returns True if successful."""
        if pane_id is None:
            pane_id = self.split_manager.get_active_pane_id()
            
        if pane_id:
            # Check if this is the last pane
            pane_count = len(self.split_manager.get_all_pane_ids())
            if pane_count <= 1:
                QMessageBox.information(
                    self,
                    "Cannot Close Pane",
                    "Cannot close the last remaining pane."
                )
                return False
                
            return self.split_manager.close_pane(pane_id)
        return False
        
    def get_active_pane_id(self) -> Optional[str]:
        """Get the currently active pane ID."""
        return self.split_manager.get_active_pane_id()
        
    def set_active_pane(self, pane_id: str) -> bool:
        """Set the active pane."""
        return self.split_manager.set_active_pane(pane_id)
        
    def get_all_pane_ids(self) -> list[str]:
        """Get all pane IDs."""
        return self.split_manager.get_all_pane_ids()
        
    def add_tab_to_pane(self, pane_id: str, title: str = "New Tab", 
                       widget_type: str = "placeholder") -> bool:
        """Add a tab to a specific pane."""
        tab_info = TabInfo(title=title, widget_type=widget_type)
        return self.split_manager.add_tab(pane_id, tab_info)
        
    def add_tab_to_active_pane(self, title: str = "New Tab", 
                              widget_type: str = "placeholder") -> bool:
        """Add a tab to the currently active pane."""
        pane_id = self.split_manager.get_active_pane_id()
        if pane_id:
            return self.add_tab_to_pane(pane_id, title, widget_type)
        return False
        
    def close_tab(self, pane_id: str, tab_index: int) -> bool:
        """Close a specific tab."""
        tab_info = self.split_manager.remove_tab(pane_id, tab_index)
        return tab_info is not None
        
    # State management
    
    def save_layout_state(self) -> dict:
        """Save the current layout state."""
        return self.split_manager.serialize_state()
        
    def restore_layout_state(self, state_data: dict) -> bool:
        """Restore layout state from data."""
        return self.split_manager.deserialize_state(state_data)
        
    def reset_to_default_layout(self):
        """Reset to the default single-pane layout."""
        default_layout = LayoutState()
        self.split_manager.set_layout_state(default_layout)
        
    # Convenience methods for keyboard shortcuts and menu actions
    
    def split_active_pane_horizontal(self):
        """Split the currently active pane horizontally."""
        self.split_pane_horizontal()
        
    def split_active_pane_vertical(self):
        """Split the currently active pane vertically."""
        self.split_pane_vertical()
        
    def close_active_pane(self):
        """Close the currently active pane."""
        self.close_pane()
        
    # Advanced operations
    
    def move_tab_between_panes(self, tab_id: str, from_pane_id: str, 
                              to_pane_id: str, to_index: Optional[int] = None) -> bool:
        """Move a tab from one pane to another."""
        return self.split_manager.move_tab(tab_id, from_pane_id, to_pane_id, to_index)
        
    def resize_split(self, container_id: str, sizes: list[float]) -> bool:
        """Resize splits in a container."""
        return self.split_manager.resize_split(container_id, sizes)
        
    def get_pane_count(self) -> int:
        """Get the total number of panes."""
        return len(self.split_manager.get_all_pane_ids())
        
    # For backward compatibility with existing code
    
    def split_horizontal(self, widget=None):
        """Legacy method - split horizontally."""
        return self.split_active_pane_horizontal()
        
    def split_vertical(self, widget=None):
        """Legacy method - split vertically.""" 
        return self.split_active_pane_vertical()