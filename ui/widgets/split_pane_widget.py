#!/usr/bin/env python3
"""
Self-contained split pane widget with recursive splitting capability.
Based on the proven tree-split algorithm, this widget manages its own 
split layout independently and can be embedded in tabs or other containers.
"""

import uuid
from typing import Optional, Dict, Union, Callable, Any, List
from dataclasses import dataclass, field

from PySide6.QtWidgets import (
    QWidget, QSplitter, QTextEdit, QPlainTextEdit, QMenu, 
    QVBoxLayout, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QObject, QEvent
from PySide6.QtGui import QAction

# Import our new components
from ui.widgets.pane_header import PaneHeaderBar, CompactPaneHeader
from ui.widgets.widget_registry import WidgetType, widget_registry
from ui.vscode_theme import *


# Note: WidgetType is now imported from widget_registry


# ============================================================================
# Focus Event Filter
# ============================================================================

class PaneFocusEventFilter(QObject):
    """Event filter to capture focus events from content widgets."""
    
    focus_clicked = Signal(str)  # pane_id
    
    def __init__(self, pane_id: str, parent=None):
        super().__init__(parent)
        self.pane_id = pane_id
    
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Filter events to detect mouse clicks and focus changes."""
        if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.FocusIn):
            self.focus_clicked.emit(self.pane_id)
        
        # Always let the event through
        return False


# ============================================================================
# Tree Model Classes
# ============================================================================

@dataclass
class LeafNode:
    """Leaf node containing a widget."""
    type: str = "leaf"
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    widget: Optional[QWidget] = None
    widget_type: WidgetType = WidgetType.PLACEHOLDER
    widget_state: dict = field(default_factory=dict)
    parent: Optional['SplitNode'] = None


@dataclass
class SplitNode:
    """Split node containing two children."""
    type: str = "split"
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    orientation: str = "horizontal"  # "horizontal" or "vertical"
    ratio: float = 0.5
    first: Optional[Union[LeafNode, 'SplitNode']] = None
    second: Optional[Union[LeafNode, 'SplitNode']] = None
    parent: Optional['SplitNode'] = None
    splitter: Optional[QSplitter] = None  # View reference


# ============================================================================
# Pane Content Widget
# ============================================================================

class PaneContent(QWidget):
    """Pane container with header bar and content widget."""
    
    split_horizontal_requested = Signal(str)
    split_vertical_requested = Signal(str)
    close_requested = Signal(str)
    widget_type_changed = Signal(str, str)  # pane_id, new_type
    pane_focused = Signal(str)  # pane_id
    
    def __init__(self, pane_id: str, widget_type: WidgetType = WidgetType.PLACEHOLDER, parent=None):
        super().__init__(parent)
        self.pane_id = pane_id
        self.widget_type = widget_type
        self.content_widget = None
        self.header_bar = None
        self.is_active = False
        self.focus_filter = None
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize the pane UI with header and content."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Check if we should show header for this widget type
        config = widget_registry.get_config(self.widget_type)
        if config and config.show_header:
            # Create header bar
            self.header_bar = PaneHeaderBar(self.pane_id, show_type_menu=config.allow_type_change)
            self.header_bar.split_horizontal_requested.connect(
                lambda: self.split_horizontal_requested.emit(self.pane_id)
            )
            self.header_bar.split_vertical_requested.connect(
                lambda: self.split_vertical_requested.emit(self.pane_id)
            )
            self.header_bar.close_requested.connect(
                lambda: self.close_requested.emit(self.pane_id)
            )
            self.header_bar.type_menu_requested.connect(self.show_type_menu)
            layout.addWidget(self.header_bar)
        
        # Create content widget
        self.content_widget = self.create_content_widget()
        layout.addWidget(self.content_widget)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def create_content_widget(self) -> QWidget:
        """Create the actual content widget using the registry."""
        widget = widget_registry.create_widget(self.widget_type, self.pane_id)
        
        if widget is None:
            # Fallback to placeholder if type not found
            widget = QLabel(f"{self.widget_type.value}\n[{self.pane_id}]")
            widget.setAlignment(Qt.AlignCenter)
            widget.setStyleSheet("""
                QLabel {
                    background-color: #2d2d30;
                    color: #969696;
                    border: 1px solid #3c3c3c;
                    padding: 20px;
                    font-size: 14px;
                }
            """)
        
        # Add pane ID to the content for identification
        if hasattr(widget, 'setPlainText'):
            current_text = widget.toPlainText() if hasattr(widget, 'toPlainText') else ""
            if not current_text:
                widget.setPlainText(f"Pane {self.pane_id}\n")
        
        # Install focus event filter to capture clicks on content widgets
        self.focus_filter = PaneFocusEventFilter(self.pane_id, self)
        self.focus_filter.focus_clicked.connect(self.pane_focused.emit)
        widget.installEventFilter(self.focus_filter)
        
        # For widgets that can receive focus, ensure they can be clicked
        if hasattr(widget, 'setFocusPolicy'):
            widget.setFocusPolicy(Qt.StrongFocus)
        
        return widget
    
    def mousePressEvent(self, event):
        """Handle mouse press to focus this pane."""
        if event.button() == Qt.LeftButton:
            self.pane_focused.emit(self.pane_id)
        super().mousePressEvent(event)
    
    def contextMenuEvent(self, event):
        """Show context menu only for widgets that don't need native menu."""
        # Emit focus signal when context menu is requested
        self.pane_focused.emit(self.pane_id)
        
        # Check if we should preserve native context menu
        config = widget_registry.get_config(self.widget_type)
        if config and config.preserve_context_menu:
            # Let the content widget handle its own context menu
            if self.content_widget:
                # Forward the event to the content widget
                self.content_widget.contextMenuEvent(event)
            return
        
        # Show our custom menu for widgets without important native menus
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d30;
                color: #cccccc;
                border: 1px solid #3c3c3c;
            }
            QMenu::item:selected {
                background-color: #094771;
            }
        """)
        
        # If no header bar, add split/close actions to context menu
        if not self.header_bar:
            split_h = QAction("Split Horizontal →", self)
            split_h.triggered.connect(lambda: self.split_horizontal_requested.emit(self.pane_id))
            menu.addAction(split_h)
            
            split_v = QAction("Split Vertical ↓", self)
            split_v.triggered.connect(lambda: self.split_vertical_requested.emit(self.pane_id))
            menu.addAction(split_v)
            
            menu.addSeparator()
            
            close = QAction("Close Pane", self)
            close.triggered.connect(lambda: self.close_requested.emit(self.pane_id))
            menu.addAction(close)
        
        # Always allow type change from context menu if configured
        if config and config.allow_type_change:
            if not self.header_bar:
                menu.addSeparator()
            type_menu = menu.addMenu("Change Type")
            for widget_type in WidgetType:
                action = QAction(widget_type.value.replace("_", " ").title(), self)
                action.triggered.connect(lambda checked, wt=widget_type: self.change_widget_type(wt))
                if widget_type == self.widget_type:
                    action.setCheckable(True)
                    action.setChecked(True)
                type_menu.addAction(action)
        
        if menu.actions():
            menu.exec(event.globalPos())
    
    def show_type_menu(self):
        """Show menu for changing widget type."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d30;
                color: #cccccc;
                border: 1px solid #3c3c3c;
            }
            QMenu::item:selected {
                background-color: #094771;
            }
        """)
        
        for widget_type in WidgetType:
            action = QAction(widget_type.value.replace("_", " ").title(), self)
            action.triggered.connect(lambda checked, wt=widget_type: self.change_widget_type(wt))
            if widget_type == self.widget_type:
                action.setCheckable(True)
                action.setChecked(True)
            menu.addAction(action)
        
        # Show menu below the type button
        if self.header_bar and hasattr(self.header_bar, 'type_button'):
            menu.exec(self.header_bar.type_button.mapToGlobal(self.header_bar.type_button.rect().bottomLeft()))
        else:
            menu.exec(self.mapToGlobal(self.rect().topLeft()))
    
    def change_widget_type(self, new_type: WidgetType):
        """Change the widget type."""
        if new_type != self.widget_type:
            self.widget_type = new_type
            
            # Remove old event filter
            if self.focus_filter and self.content_widget:
                self.content_widget.removeEventFilter(self.focus_filter)
            
            # Replace content widget
            self.layout().removeWidget(self.content_widget)
            self.content_widget.deleteLater()
            self.content_widget = self.create_content_widget()
            self.layout().addWidget(self.content_widget)
            
            # Update header if it exists
            config = widget_registry.get_config(new_type)
            if self.header_bar and config:
                # Update type menu button visibility
                if hasattr(self.header_bar, 'type_button'):
                    self.header_bar.type_button.setVisible(config.allow_type_change)
            
            self.widget_type_changed.emit(self.pane_id, new_type.value)
    
    def set_active(self, active: bool):
        """Set the active state of this pane."""
        self.is_active = active
        
        # Update header bar if it exists
        if self.header_bar:
            self.header_bar.set_active(active)
        
        # Update border for visual feedback
        if active:
            self.setStyleSheet("""
                PaneContent {
                    border: 2px solid #007ACC;
                }
            """)
        else:
            self.setStyleSheet("""
                PaneContent {
                    border: 1px solid #3c3c3c;
                }
            """)
    
    def get_state(self) -> dict:
        """Get the current state of the widget."""
        state = {"type": self.widget_type.value}
        
        # Save content-specific state
        if isinstance(self.content_widget, (QPlainTextEdit, QTextEdit)):
            state["content"] = self.content_widget.toPlainText()
        
        return state
    
    def set_state(self, state: dict):
        """Restore widget state."""
        # Restore content if applicable
        if "content" in state and isinstance(self.content_widget, (QPlainTextEdit, QTextEdit)):
            self.content_widget.setPlainText(state["content"])


# ============================================================================
# Split Pane Widget
# ============================================================================

class SplitPaneWidget(QWidget):
    """
    Self-contained widget that manages recursive split panes.
    Can be embedded in tabs or other containers.
    """
    
    # Signals
    pane_added = Signal(str)  # pane_id
    pane_removed = Signal(str)  # pane_id
    active_pane_changed = Signal(str)  # pane_id
    layout_changed = Signal()
    
    def __init__(self, initial_widget_type: WidgetType = WidgetType.TEXT_EDITOR,
                 widget_factory: Optional[Callable[[str, WidgetType], QWidget]] = None,
                 parent=None):
        """
        Initialize the split pane widget.
        
        Args:
            initial_widget_type: Type of widget to create in the initial pane
            widget_factory: Optional factory function to create custom widgets
                           Should accept (pane_id, widget_type) and return QWidget
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.widget_factory = widget_factory
        self.root: Union[LeafNode, SplitNode] = None
        self.leaves: Dict[str, LeafNode] = {}
        self.widgets: Dict[str, QWidget] = {}
        self.active_pane_id: Optional[str] = None
        
        self.initialize_root(initial_widget_type)
        self.setup_ui()
    
    def initialize_root(self, widget_type: WidgetType):
        """Create initial root leaf."""
        self.root = LeafNode(widget_type=widget_type)
        self.leaves[self.root.id] = self.root
        self.active_pane_id = self.root.id
    
    def setup_ui(self):
        """Initialize the UI."""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Create initial view
        self.refresh_view()
    
    def create_pane_widget(self, leaf: LeafNode) -> QWidget:
        """Create a widget for a leaf node."""
        if self.widget_factory:
            # Use custom factory
            widget = self.widget_factory(leaf.id, leaf.widget_type)
        else:
            # Use default PaneContent
            widget = PaneContent(leaf.id, leaf.widget_type)
        
        # Connect signals if it's our PaneContent
        if isinstance(widget, PaneContent):
            widget.split_horizontal_requested.connect(self.split_horizontal)
            widget.split_vertical_requested.connect(self.split_vertical)
            widget.close_requested.connect(self.close_pane)
            widget.widget_type_changed.connect(self._on_widget_type_changed)
            widget.pane_focused.connect(self.set_active_pane)
        
        return widget
    
    def render_node(self, node: Union[LeafNode, SplitNode]) -> QWidget:
        """Recursively render a node to Qt widgets."""
        if isinstance(node, LeafNode):
            # Create widget for leaf
            widget = self.create_pane_widget(node)
            
            # Store references
            node.widget = widget
            self.widgets[node.id] = widget
            
            return widget
        
        elif isinstance(node, SplitNode):
            # Create splitter
            if node.orientation == "horizontal":
                splitter = QSplitter(Qt.Horizontal)
            else:
                splitter = QSplitter(Qt.Vertical)
            
            # Apply VSCode theme to splitter
            splitter.setStyleSheet(get_splitter_stylesheet())
            
            # Render children
            if node.first:
                first_widget = self.render_node(node.first)
                splitter.addWidget(first_widget)
            
            if node.second:
                second_widget = self.render_node(node.second)
                splitter.addWidget(second_widget)
            
            # Apply ratio
            total_size = 1000
            first_size = int(total_size * node.ratio)
            second_size = total_size - first_size
            splitter.setSizes([first_size, second_size])
            
            # Track ratio changes
            splitter.splitterMoved.connect(
                lambda: self._update_ratio(node, splitter)
            )
            
            # Store reference
            node.splitter = splitter
            
            return splitter
        
        return QWidget()
    
    def refresh_view(self):
        """Rebuild the view from the model."""
        # Clear existing layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Clear widget references
        self.widgets.clear()
        
        # Create new view
        root_widget = self.render_node(self.root)
        self.layout.addWidget(root_widget)
        
        # Update active pane visual
        self._update_active_pane_visual()
        
        self.layout_changed.emit()
    
    def _update_ratio(self, node: SplitNode, splitter: QSplitter):
        """Update split ratio when user drags splitter."""
        sizes = splitter.sizes()
        total = sum(sizes)
        if total > 0:
            node.ratio = sizes[0] / total
    
    def split_horizontal(self, pane_id: str):
        """Split pane horizontally (left|right)."""
        self._split_pane(pane_id, "horizontal")
    
    def split_vertical(self, pane_id: str):
        """Split pane vertically (top|bottom)."""
        self._split_pane(pane_id, "vertical")
    
    def _split_pane(self, pane_id: str, orientation: str):
        """Split a pane."""
        leaf = self.leaves.get(pane_id)
        if not leaf:
            return
        
        # Store the parent before creating split
        old_parent = leaf.parent
        
        # Create new leaf with same type as current
        new_leaf = LeafNode(widget_type=leaf.widget_type)
        
        # Create split node
        split = SplitNode(
            orientation=orientation,
            ratio=0.5
        )
        
        # Set up the tree structure
        split.first = leaf
        split.second = new_leaf
        leaf.parent = split
        new_leaf.parent = split
        
        # Update tree structure
        if old_parent:
            # Replace leaf with split in parent
            if old_parent.first == leaf:
                old_parent.first = split
            else:
                old_parent.second = split
            split.parent = old_parent
        else:
            # Leaf is root - split becomes new root
            self.root = split
        
        # Update tracking
        self.leaves[new_leaf.id] = new_leaf
        
        # Make new pane active
        self.active_pane_id = new_leaf.id
        
        # Refresh view
        self.refresh_view()
        
        # Focus the newly created widget
        self._focus_widget_in_pane(new_leaf.id)
        
        # Emit signal
        self.pane_added.emit(new_leaf.id)
    
    def close_pane(self, pane_id: str):
        """Close a pane and promote its sibling."""
        leaf = self.leaves.get(pane_id)
        if not leaf:
            return
        
        # Don't close the last pane
        if leaf == self.root:
            return
        
        parent = leaf.parent
        if not parent:
            return
        
        # Find sibling
        sibling = parent.second if parent.first == leaf else parent.first
        if not sibling:
            return
        
        # Promote sibling
        grandparent = parent.parent
        
        if grandparent:
            # Replace parent with sibling in grandparent
            if grandparent.first == parent:
                grandparent.first = sibling
            else:
                grandparent.second = sibling
            sibling.parent = grandparent
        else:
            # Parent is root - sibling becomes new root
            self.root = sibling
            sibling.parent = None
        
        # Clean up
        del self.leaves[pane_id]
        
        # Update active pane if necessary
        if self.active_pane_id == pane_id:
            # Find first available leaf
            if self.leaves:
                self.active_pane_id = next(iter(self.leaves.keys()))
        
        # Clean up widget
        if pane_id in self.widgets:
            self.widgets[pane_id].deleteLater()
        
        # Refresh view
        self.refresh_view()
        
        # Emit signal
        self.pane_removed.emit(pane_id)
    
    def set_active_pane(self, pane_id: str):
        """Set the active pane."""
        if pane_id in self.leaves:
            self.active_pane_id = pane_id
            self._update_active_pane_visual()
            self._focus_widget_in_pane(pane_id)
            self.active_pane_changed.emit(pane_id)
    
    def _update_active_pane_visual(self):
        """Update visual indication of active pane."""
        for pid, widget in self.widgets.items():
            if isinstance(widget, PaneContent):
                widget.set_active(pid == self.active_pane_id)
    
    def _focus_widget_in_pane(self, pane_id: str):
        """Set focus to the content widget in the specified pane."""
        widget = self.widgets.get(pane_id)
        if isinstance(widget, PaneContent) and widget.content_widget:
            # Set focus to the content widget
            widget.content_widget.setFocus(Qt.MouseFocusReason)
    
    def _on_widget_type_changed(self, pane_id: str, new_type: str):
        """Handle widget type change."""
        leaf = self.leaves.get(pane_id)
        if leaf:
            leaf.widget_type = WidgetType(new_type)
    
    def get_state(self) -> dict:
        """Get the current state of the split layout."""
        def serialize_node(node):
            if isinstance(node, LeafNode):
                return {
                    "type": "leaf",
                    "id": node.id,
                    "widget_type": node.widget_type.value,
                    "widget_state": node.widget.get_state() if hasattr(node.widget, 'get_state') else {}
                }
            elif isinstance(node, SplitNode):
                return {
                    "type": "split",
                    "id": node.id,
                    "orientation": node.orientation,
                    "ratio": node.ratio,
                    "first": serialize_node(node.first) if node.first else None,
                    "second": serialize_node(node.second) if node.second else None
                }
            return None
        
        return {
            "root": serialize_node(self.root),
            "active_pane_id": self.active_pane_id
        }
    
    def set_state(self, state: dict):
        """Restore the split layout from a state dict."""
        # This would deserialize the state and rebuild the tree
        # Implementation left as an exercise
        pass
    
    def get_pane_count(self) -> int:
        """Get the number of panes."""
        return len(self.leaves)
    
    def get_all_pane_ids(self) -> List[str]:
        """Get all pane IDs."""
        return list(self.leaves.keys())
    
    def focus_active_pane(self):
        """Focus the currently active pane's content widget."""
        if self.active_pane_id:
            self._focus_widget_in_pane(self.active_pane_id)