"""Content pane widget for the simplified split architecture."""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMenu
from PySide6.QtCore import Signal, Qt, QPoint
from PySide6.QtGui import QAction, QMouseEvent
from .widget_factory import WidgetFactory


class ContentPane(QWidget):
    """A content pane that directly displays a widget without tabs."""
    
    # Signals
    split_horizontal_requested = Signal(str)  # pane_id
    split_vertical_requested = Signal(str)    # pane_id
    close_pane_requested = Signal(str)        # pane_id
    pane_activated = Signal(str)              # pane_id
    widget_type_changed = Signal(str, str)    # pane_id, new_widget_type
    
    def __init__(self, pane_id: str, widget_type: str = "placeholder", 
                 widget_state: Optional[Dict[str, Any]] = None,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.pane_id = pane_id
        self.widget_type = widget_type
        self.widget_state = widget_state or {}
        self.current_widget = None
        self.setup_ui()
        self.setup_context_menu()
        
    def setup_ui(self):
        """Initialize the pane UI."""
        self.setObjectName(f"content_pane_{self.pane_id}")
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Create and add the widget
        self.set_widget_type(self.widget_type, self.widget_state)
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def setup_context_menu(self):
        """Setup the context menu for split and close operations."""
        self.context_menu = QMenu(self)
        
        # Split actions
        self.split_right_action = QAction("Split Right", self)
        self.split_right_action.setToolTip("Split this pane horizontally (new pane on right)")
        self.split_right_action.triggered.connect(
            lambda: self.split_horizontal_requested.emit(self.pane_id)
        )
        self.context_menu.addAction(self.split_right_action)
        
        self.split_down_action = QAction("Split Down", self)
        self.split_down_action.setToolTip("Split this pane vertically (new pane below)")
        self.split_down_action.triggered.connect(
            lambda: self.split_vertical_requested.emit(self.pane_id)
        )
        self.context_menu.addAction(self.split_down_action)
        
        self.context_menu.addSeparator()
        
        # Open submenu
        self.open_menu = QMenu("Open", self)
        for widget_type in WidgetFactory.get_available_widget_types():
            if widget_type != 'placeholder':
                action = QAction(WidgetFactory.get_widget_display_name(widget_type), self)
                action.triggered.connect(lambda checked, wt=widget_type: self.open_widget_in_split(wt))
                self.open_menu.addAction(action)
        self.context_menu.addMenu(self.open_menu)
        
        # Replace submenu
        self.replace_menu = QMenu("Replace With", self)
        for widget_type in WidgetFactory.get_available_widget_types():
            action = QAction(WidgetFactory.get_widget_display_name(widget_type), self)
            action.triggered.connect(lambda checked, wt=widget_type: self.set_widget_type(wt))
            self.replace_menu.addAction(action)
        self.context_menu.addMenu(self.replace_menu)
        
        self.context_menu.addSeparator()
        
        # Close action
        self.close_pane_action = QAction("Close Pane", self)
        self.close_pane_action.setToolTip("Close this pane")
        self.close_pane_action.triggered.connect(
            lambda: self.close_pane_requested.emit(self.pane_id)
        )
        self.context_menu.addAction(self.close_pane_action)
        
    def show_context_menu(self, position: QPoint):
        """Show the context menu at the given position."""
        global_pos = self.mapToGlobal(position)
        self.context_menu.exec(global_pos)
        
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            # Activate this pane when clicked
            self.pane_activated.emit(self.pane_id)
        super().mousePressEvent(event)
        
    def set_widget_type(self, widget_type: str, widget_state: Optional[Dict[str, Any]] = None):
        """Change the widget type in this pane."""
        # Save current widget state if needed
        if self.current_widget and self.widget_type != 'placeholder':
            self.widget_state = WidgetFactory.get_widget_state(self.current_widget, self.widget_type)
        
        # Remove old widget
        if self.current_widget:
            self.layout.removeWidget(self.current_widget)
            self.current_widget.deleteLater()
        
        # Create new widget
        self.widget_type = widget_type
        self.widget_state = widget_state or {}
        self.current_widget = WidgetFactory.create_widget(widget_type, self.widget_state, self)
        self.layout.addWidget(self.current_widget)
        
        # Emit signal
        self.widget_type_changed.emit(self.pane_id, widget_type)
    
    def open_widget_in_split(self, widget_type: str):
        """Request to split and open a widget type in the new pane."""
        # This will be handled by the parent - just emit split request
        # The parent can then set the widget type on the new pane
        self.split_horizontal_requested.emit(self.pane_id)
        # TODO: Pass widget_type information to the split handler
    
    def get_widget_type(self) -> str:
        """Get the current widget type."""
        return self.widget_type
    
    def get_widget_state(self) -> Dict[str, Any]:
        """Get the current widget state."""
        if self.current_widget:
            return WidgetFactory.get_widget_state(self.current_widget, self.widget_type)
        return self.widget_state
        
    def get_pane_id(self) -> str:
        """Get the pane ID."""
        return self.pane_id
        
    def set_pane_id(self, pane_id: str):
        """Set the pane ID."""
        self.pane_id = pane_id
        self.setObjectName(f"content_pane_{pane_id}")
        
    def set_active(self, active: bool):
        """Set the active state of the pane."""
        if active:
            self.setStyleSheet("""
                ContentPane {
                    border-left: 3px solid #0078d4;
                }
            """)
        else:
            self.setStyleSheet("")
            
    def can_close(self) -> bool:
        """Check if this pane can be closed."""
        # Will be determined by the parent container
        # (can't close if it's the last pane)
        return True