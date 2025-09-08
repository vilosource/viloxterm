"""Workspace implementation with split panes and tabs."""

from PySide6.QtWidgets import QWidget, QSplitter, QTabWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal


class Workspace(QWidget):
    """Central workspace area with split panes and tabs."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the workspace UI."""
        self.setObjectName("workspace")
        
        # Create main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create root splitter
        self.root_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.root_splitter)
        
        # Create initial pane with tabs
        self.create_initial_pane()
        
    def create_initial_pane(self):
        """Create the initial pane with a tab widget."""
        initial_pane = TabContainer()
        initial_pane.add_tab("Welcome", QLabel("Welcome to ViloApp"))
        self.root_splitter.addWidget(initial_pane)
        
    def split_horizontal(self, widget=None):
        """Split the current pane horizontally."""
        if widget is None:
            widget = self.root_splitter.widget(0)
            
        # Create new splitter
        new_splitter = QSplitter(Qt.Horizontal)
        
        # Get parent splitter and index
        parent = widget.parent()
        if isinstance(parent, QSplitter):
            index = parent.indexOf(widget)
            parent.replaceWidget(index, new_splitter)
        else:
            self.root_splitter.replaceWidget(0, new_splitter)
            
        # Add original widget and new pane to splitter
        new_splitter.addWidget(widget)
        new_pane = TabContainer()
        new_pane.add_tab("New Tab", QLabel("New Tab Content"))
        new_splitter.addWidget(new_pane)
        
        return new_pane
        
    def split_vertical(self, widget=None):
        """Split the current pane vertically."""
        if widget is None:
            widget = self.root_splitter.widget(0)
            
        # Create new splitter
        new_splitter = QSplitter(Qt.Vertical)
        
        # Get parent splitter and index
        parent = widget.parent()
        if isinstance(parent, QSplitter):
            index = parent.indexOf(widget)
            parent.replaceWidget(index, new_splitter)
        else:
            self.root_splitter.replaceWidget(0, new_splitter)
            
        # Add original widget and new pane to splitter
        new_splitter.addWidget(widget)
        new_pane = TabContainer()
        new_pane.add_tab("New Tab", QLabel("New Tab Content"))
        new_splitter.addWidget(new_pane)
        
        return new_pane


class TabContainer(QTabWidget):
    """Container for tabs within a pane."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the tab container UI."""
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        
        # Connect signals
        self.tabCloseRequested.connect(self.close_tab)
        
    def add_tab(self, title: str, widget: QWidget):
        """Add a new tab."""
        index = self.addTab(widget, title)
        self.setCurrentIndex(index)
        return index
        
    def close_tab(self, index: int):
        """Close a tab."""
        if self.count() > 1:
            self.removeTab(index)
        else:
            # Don't close the last tab
            pass