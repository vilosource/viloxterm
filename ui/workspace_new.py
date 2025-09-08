"""New workspace implementation with tab-based split management."""

from typing import Optional, Dict
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from ui.widgets.tab_workspace import TabWorkspace


class Workspace(QWidget):
    """Central workspace with tabs, each containing splittable content."""
    
    # Signals
    active_pane_changed = Signal(str, str)  # tab_id, pane_id
    tab_changed = Signal(str)  # tab_id
    
    def __init__(self):
        super().__init__()
        self.tab_workspaces: Dict[str, TabWorkspace] = {}
        self.next_tab_id = 1
        self.setup_ui()
        self.create_initial_tab()
        
    def setup_ui(self):
        """Initialize the workspace UI."""
        self.setObjectName("workspace")
        
        # Create main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        
        # Add "+" button for new tabs
        self.new_tab_button = QPushButton("+")
        self.new_tab_button.setFixedSize(30, 25)
        self.new_tab_button.clicked.connect(self.add_new_tab)
        self.tab_widget.setCornerWidget(self.new_tab_button, Qt.TopRightCorner)
        
        # Connect signals
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        layout.addWidget(self.tab_widget)
    
    def create_initial_tab(self):
        """Create the initial welcome tab."""
        self.add_new_tab("Welcome")
    
    def add_new_tab(self, title: Optional[str] = None) -> str:
        """Add a new tab with a workspace."""
        if title is None:
            title = f"Tab {self.next_tab_id}"
        
        tab_id = f"tab_{self.next_tab_id}"
        self.next_tab_id += 1
        
        # Create tab workspace
        workspace = TabWorkspace(tab_id, self)
        workspace.active_pane_changed.connect(
            lambda pane_id: self.active_pane_changed.emit(tab_id, pane_id)
        )
        
        # Add to tab widget
        index = self.tab_widget.addTab(workspace, title)
        self.tab_widget.setCurrentIndex(index)
        
        # Track workspace
        self.tab_workspaces[tab_id] = workspace
        
        return tab_id
    
    def close_tab(self, index: int):
        """Close a tab at the given index."""
        # Don't close if it's the last tab
        if self.tab_widget.count() <= 1:
            return
        
        # Get tab workspace
        widget = self.tab_widget.widget(index)
        if isinstance(widget, TabWorkspace):
            tab_id = widget.tab_id
            if tab_id in self.tab_workspaces:
                del self.tab_workspaces[tab_id]
        
        # Remove tab
        self.tab_widget.removeTab(index)
    
    def _on_tab_changed(self, index: int):
        """Handle tab change."""
        if index >= 0:
            widget = self.tab_widget.widget(index)
            if isinstance(widget, TabWorkspace):
                self.tab_changed.emit(widget.tab_id)
                
                # Emit active pane for the new tab
                active_pane = widget.get_active_pane_id()
                if active_pane:
                    self.active_pane_changed.emit(widget.tab_id, active_pane)
    
    def get_current_tab_workspace(self) -> Optional[TabWorkspace]:
        """Get the current tab's workspace."""
        index = self.tab_widget.currentIndex()
        if index >= 0:
            widget = self.tab_widget.widget(index)
            if isinstance(widget, TabWorkspace):
                return widget
        return None
    
    def get_tab_workspace(self, tab_id: str) -> Optional[TabWorkspace]:
        """Get a specific tab's workspace."""
        return self.tab_workspaces.get(tab_id)
    
    # Convenience methods for current tab operations
    
    def split_horizontal(self, pane_id: Optional[str] = None) -> Optional[str]:
        """Split horizontally in the current tab."""
        workspace = self.get_current_tab_workspace()
        if workspace:
            return workspace.split_horizontal(pane_id)
        return None
    
    def split_vertical(self, pane_id: Optional[str] = None) -> Optional[str]:
        """Split vertically in the current tab."""
        workspace = self.get_current_tab_workspace()
        if workspace:
            return workspace.split_vertical(pane_id)
        return None
    
    def close_pane(self, pane_id: Optional[str] = None) -> bool:
        """Close a pane in the current tab."""
        workspace = self.get_current_tab_workspace()
        if workspace:
            return workspace.close_pane(pane_id)
        return False
    
    def set_pane_widget(self, pane_id: str, widget_type: str) -> bool:
        """Set widget type for a pane in the current tab."""
        workspace = self.get_current_tab_workspace()
        if workspace:
            return workspace.set_pane_widget(pane_id, widget_type)
        return False
    
    # State management
    
    def save_state(self) -> Dict:
        """Save the workspace state."""
        state = {
            'tabs': [],
            'current_tab_index': self.tab_widget.currentIndex()
        }
        
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, TabWorkspace):
                tab_state = {
                    'title': self.tab_widget.tabText(i),
                    'workspace': widget.save_state()
                }
                state['tabs'].append(tab_state)
        
        return state
    
    def restore_state(self, state: Dict) -> bool:
        """Restore the workspace state."""
        # Clear current tabs
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        self.tab_workspaces.clear()
        
        # Restore tabs
        if 'tabs' in state:
            for tab_state in state['tabs']:
                tab_id = self.add_new_tab(tab_state.get('title', 'Tab'))
                workspace = self.tab_workspaces.get(tab_id)
                if workspace and 'workspace' in tab_state:
                    workspace.restore_state(tab_state['workspace'])
        
        # Restore current tab
        if 'current_tab_index' in state:
            self.tab_widget.setCurrentIndex(state['current_tab_index'])
        
        # Create initial tab if no tabs were restored
        if self.tab_widget.count() == 0:
            self.create_initial_tab()
        
        return True
    
    # Keyboard shortcuts support
    
    def split_active_pane_horizontal(self):
        """Split the active pane horizontally."""
        self.split_horizontal()
    
    def split_active_pane_vertical(self):
        """Split the active pane vertically."""
        self.split_vertical()
    
    def close_active_pane(self):
        """Close the active pane."""
        self.close_pane()