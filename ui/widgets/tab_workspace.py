"""Tab workspace that manages split panes within a single tab."""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal
from .simple_split_manager import SimpleSplitManager


class TabWorkspace(QWidget):
    """Workspace content for a single tab that can be split."""
    
    # Signals
    pane_count_changed = Signal(int)
    active_pane_changed = Signal(str)
    
    def __init__(self, tab_id: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.tab_id = tab_id
        self.split_manager = SimpleSplitManager(self)
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Initialize the UI."""
        self.setObjectName(f"tab_workspace_{self.tab_id}")
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add the root widget from split manager
        if self.split_manager.root_widget:
            layout.addWidget(self.split_manager.root_widget)
    
    def setup_connections(self):
        """Setup signal connections."""
        self.split_manager.pane_added.connect(self._on_pane_added)
        self.split_manager.pane_removed.connect(self._on_pane_removed)
        self.split_manager.active_pane_changed.connect(self.active_pane_changed.emit)
    
    def _on_pane_added(self, pane_id: str):
        """Handle pane added."""
        # Layout updates itself through splitter operations
        self.pane_count_changed.emit(len(self.split_manager.panes))
    
    def _on_pane_removed(self, pane_id: str):
        """Handle pane removed."""
        # Layout updates itself through splitter operations
        # Check if root widget changed (could happen after closing panes)
        if self.split_manager.root_widget and self.split_manager.root_widget.parent() != self:
            # Re-parent the root widget if needed
            layout = self.layout()
            while layout.count():
                item = layout.takeAt(0)
            layout.addWidget(self.split_manager.root_widget)
        self.pane_count_changed.emit(len(self.split_manager.panes))
    
    def _ensure_root_in_layout(self):
        """Ensure the root widget is properly in the layout."""
        if self.split_manager.root_widget:
            if self.split_manager.root_widget.parent() != self:
                layout = self.layout()
                # Clear layout if needed
                while layout.count():
                    layout.takeAt(0)
                # Add root widget
                layout.addWidget(self.split_manager.root_widget)
    
    # Public API
    
    def split_horizontal(self, pane_id: Optional[str] = None) -> Optional[str]:
        """Split a pane horizontally."""
        if pane_id is None:
            pane_id = self.split_manager.get_active_pane_id()
        
        if pane_id:
            new_pane_id = self.split_manager.split_pane_horizontal(pane_id)
            # No need to update layout - splitter manages itself
            return new_pane_id
        return None
    
    def split_vertical(self, pane_id: Optional[str] = None) -> Optional[str]:
        """Split a pane vertically."""
        if pane_id is None:
            pane_id = self.split_manager.get_active_pane_id()
        
        if pane_id:
            new_pane_id = self.split_manager.split_pane_vertical(pane_id)
            # No need to update layout - splitter manages itself
            return new_pane_id
        return None
    
    def close_pane(self, pane_id: Optional[str] = None) -> bool:
        """Close a pane."""
        if pane_id is None:
            pane_id = self.split_manager.get_active_pane_id()
        
        if pane_id:
            success = self.split_manager.close_pane(pane_id)
            if success:
                self._ensure_root_in_layout()
            return success
        return False
    
    def set_pane_widget(self, pane_id: str, widget_type: str, 
                       widget_state: Optional[Dict[str, Any]] = None) -> bool:
        """Set the widget type for a pane."""
        return self.split_manager.set_pane_widget(pane_id, widget_type, widget_state)
    
    def get_active_pane_id(self) -> Optional[str]:
        """Get the active pane ID."""
        return self.split_manager.get_active_pane_id()
    
    def set_active_pane(self, pane_id: str) -> bool:
        """Set the active pane."""
        return self.split_manager.set_active_pane(pane_id)
    
    def get_pane_count(self) -> int:
        """Get the number of panes."""
        return len(self.split_manager.panes)
    
    def get_all_pane_ids(self) -> list[str]:
        """Get all pane IDs."""
        return self.split_manager.get_all_pane_ids()
    
    def save_state(self) -> Dict[str, Any]:
        """Save the workspace state."""
        return {
            'tab_id': self.tab_id,
            'layout': self.split_manager.get_layout_state()
        }
    
    def restore_state(self, state: Dict[str, Any]) -> bool:
        """Restore the workspace state."""
        if 'layout' in state:
            return self.split_manager.restore_layout_state(state['layout'])
        return False