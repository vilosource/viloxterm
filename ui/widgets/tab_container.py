"""Enhanced tab container with split operations and context menus."""

from typing import Optional, List
from PySide6.QtWidgets import (QTabWidget, QWidget, QMenu, QMessageBox, 
                              QVBoxLayout, QPushButton)
from PySide6.QtCore import Signal, Qt, QPoint
from PySide6.QtGui import QAction, QMouseEvent, QContextMenuEvent
from models.layout_state import TabInfo


class TabContainer(QTabWidget):
    """Enhanced tab container with split operations and context menus."""
    
    # Signals for split operations
    split_horizontal_requested = Signal(str)  # pane_id
    split_vertical_requested = Signal(str)    # pane_id
    close_pane_requested = Signal(str)        # pane_id
    tab_moved_to_new_pane = Signal(str, str)  # tab_id, orientation ("horizontal" or "vertical")
    tab_close_requested = Signal(str, int)    # pane_id, tab_index (for confirmation)
    tab_closed = Signal(str, int)             # pane_id, tab_index (after closing)
    pane_activated = Signal(str)              # pane_id
    
    def __init__(self, pane_id: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.pane_id = pane_id
        self.setup_ui()
        self.setup_context_menu()
        
    def setup_ui(self):
        """Initialize the tab container UI."""
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        self.setElideMode(Qt.ElideRight)
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Connect signals
        self.tabCloseRequested.connect(self._on_tab_close_requested)
        self.currentChanged.connect(self.on_tab_changed)
        
    def setup_context_menu(self):
        """Setup context menu actions."""
        self.context_menu = QMenu(self)
        
        # Split actions
        self.split_horizontal_action = QAction("Split Right", self)
        self.split_horizontal_action.setToolTip("Split this pane horizontally (new pane on right)")
        self.split_horizontal_action.triggered.connect(
            lambda: self.split_horizontal_requested.emit(self.pane_id)
        )
        self.context_menu.addAction(self.split_horizontal_action)
        
        self.split_vertical_action = QAction("Split Down", self)
        self.split_vertical_action.setToolTip("Split this pane vertically (new pane below)")
        self.split_vertical_action.triggered.connect(
            lambda: self.split_vertical_requested.emit(self.pane_id)
        )
        self.context_menu.addAction(self.split_vertical_action)
        
        self.context_menu.addSeparator()
        
        # Tab-specific actions (shown when right-clicking on a tab)
        self.move_tab_right_action = QAction("Move Tab to New Pane (Right)", self)
        self.move_tab_right_action.triggered.connect(self.move_current_tab_to_new_pane_right)
        
        self.move_tab_down_action = QAction("Move Tab to New Pane (Down)", self)
        self.move_tab_down_action.triggered.connect(self.move_current_tab_to_new_pane_down)
        
        self.close_other_tabs_action = QAction("Close Other Tabs", self)
        self.close_other_tabs_action.triggered.connect(self.close_other_tabs)
        
        self.close_all_tabs_action = QAction("Close All Tabs", self)
        self.close_all_tabs_action.triggered.connect(self.close_all_tabs)
        
        self.context_menu.addSeparator()
        
        # Pane actions
        self.close_pane_action = QAction("Close Pane", self)
        self.close_pane_action.setToolTip("Close this entire pane")
        self.close_pane_action.triggered.connect(
            lambda: self.close_pane_requested.emit(self.pane_id)
        )
        self.context_menu.addAction(self.close_pane_action)
        
    def show_context_menu(self, position: QPoint):
        """Show context menu at the given position."""
        # Determine if we're clicking on a tab or empty space
        # Use tabBar().tabAt() instead of tabAt()
        tab_index = self.tabBar().tabAt(position)
        
        # Clear any previous tab-specific actions
        for action in [self.move_tab_right_action, self.move_tab_down_action, 
                      self.close_other_tabs_action, self.close_all_tabs_action]:
            if action in self.context_menu.actions():
                self.context_menu.removeAction(action)
        
        # Add tab-specific actions if clicking on a tab
        if tab_index >= 0 and self.count() > 0:
            separator_before_pane = None
            for action in self.context_menu.actions():
                if action.text() == "Close Pane":
                    separator_before_pane = self.context_menu.insertSeparator(action)
                    break
            
            if separator_before_pane:
                self.context_menu.insertAction(separator_before_pane, self.close_all_tabs_action)
                self.context_menu.insertAction(separator_before_pane, self.close_other_tabs_action)
                self.context_menu.insertAction(separator_before_pane, self.move_tab_down_action)
                self.context_menu.insertAction(separator_before_pane, self.move_tab_right_action)
        
        # Disable pane close if this is the only pane or has critical content
        # (This would be determined by the parent workspace)
        
        # Show the menu
        global_pos = self.mapToGlobal(position)
        self.context_menu.exec(global_pos)
        
    def move_current_tab_to_new_pane_right(self):
        """Move current tab to a new pane on the right."""
        current_tab = self.currentIndex()
        if current_tab >= 0:
            tab_widget = self.widget(current_tab)
            tab_text = self.tabText(current_tab)
            # Create a synthetic tab ID for now
            tab_id = f"{self.pane_id}_tab_{current_tab}"
            self.tab_moved_to_new_pane.emit(tab_id, "horizontal")
            
    def move_current_tab_to_new_pane_down(self):
        """Move current tab to a new pane below."""
        current_tab = self.currentIndex()
        if current_tab >= 0:
            tab_widget = self.widget(current_tab)
            tab_text = self.tabText(current_tab)
            # Create a synthetic tab ID for now
            tab_id = f"{self.pane_id}_tab_{current_tab}"
            self.tab_moved_to_new_pane.emit(tab_id, "vertical")
            
    def close_other_tabs(self):
        """Close all tabs except the current one."""
        current_index = self.currentIndex()
        if current_index < 0:
            return
            
        # Remove tabs in reverse order to maintain indices
        for i in range(self.count() - 1, -1, -1):
            if i != current_index:
                self.removeTab(i)
                
    def close_all_tabs(self):
        """Close all tabs in this pane."""
        reply = QMessageBox.question(
            self, 
            "Close All Tabs", 
            "Are you sure you want to close all tabs in this pane?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            while self.count() > 0:
                self.removeTab(0)
                
    def _on_tab_close_requested(self, index: int):
        """Handle tab close request from UI."""
        # Emit request signal for workspace to handle confirmation
        self.tab_close_requested.emit(self.pane_id, index)
    
    def close_tab(self, index: int):
        """Close a tab at the given index."""
        if 0 <= index < self.count():
            if self.count() == 1:
                # Only 1 tab in this pane - request to close the entire pane
                self.close_pane_requested.emit(self.pane_id)
            else:
                # Multiple tabs - just close this tab
                self.removeTab(index)
                self.tab_closed.emit(self.pane_id, index)
            
    def add_placeholder_tab(self, title: str = "New Tab"):
        """Add a placeholder tab with a simple widget."""
        placeholder = PlaceholderWidget(title)
        index = self.addTab(placeholder, title)
        self.setCurrentIndex(index)
        return index
        
    def add_tab_with_widget(self, widget: QWidget, title: str, closable: bool = True):
        """Add a tab with a specific widget."""
        index = self.addTab(widget, title)
        self.setCurrentIndex(index)
        
        # Note: Tab closable state is controlled by setTabsClosable() globally
        # Individual tab closability would require custom tab bar implementation
        
        return index
        
    def on_tab_changed(self, index: int):
        """Handle tab change events."""
        if index >= 0:
            # Notify that this pane is now active
            self.pane_activated.emit(self.pane_id)
            
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            # Activate this pane when clicked
            self.pane_activated.emit(self.pane_id)
        super().mousePressEvent(event)
        
    def get_tab_info_list(self) -> List[TabInfo]:
        """Get list of TabInfo objects representing current tabs."""
        tab_infos = []
        for i in range(self.count()):
            tab_text = self.tabText(i)
            widget = self.widget(i)
            
            # Determine widget type
            widget_type = "placeholder"
            if isinstance(widget, PlaceholderWidget):
                widget_type = "placeholder"
            # Add more widget type detection as needed
            
            tab_info = TabInfo(
                tab_id=f"{self.pane_id}_tab_{i}",  # Generate ID
                title=tab_text,
                widget_type=widget_type,
                is_closable=True
            )
            tab_infos.append(tab_info)
            
        return tab_infos
        
    def set_active_tab(self, index: int) -> bool:
        """Set the active tab by index."""
        if 0 <= index < self.count():
            self.setCurrentIndex(index)
            return True
        return False
        
    def get_pane_id(self) -> str:
        """Get the pane ID."""
        return self.pane_id
        
    def set_pane_id(self, pane_id: str):
        """Set the pane ID."""
        self.pane_id = pane_id


class PlaceholderWidget(QWidget):
    """Simple placeholder widget for tabs."""
    
    def __init__(self, text: str = "New Pane", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setup_ui(text)
    
    def setup_ui(self, text: str):
        """Setup placeholder UI."""
        layout = QVBoxLayout(self)
        
        button = QPushButton(text)
        button.setEnabled(False)  # Make it non-interactive for now
        button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 20px;
                font-size: 14px;
                color: #666;
            }
        """)
        
        layout.addWidget(button)
        layout.setAlignment(Qt.AlignCenter)
        
    def set_text(self, text: str):
        """Update the placeholder text."""
        if self.layout() and self.layout().count() > 0:
            button = self.layout().itemAt(0).widget()
            if isinstance(button, QPushButton):
                button.setText(text)