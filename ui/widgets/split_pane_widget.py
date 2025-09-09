#!/usr/bin/env python3
"""
Split pane widget - VIEW LAYER ONLY.

This is a complete rewrite using proper MVC architecture.
The view renders the model's tree structure and handles user interactions.
All content widgets (AppWidgets) are owned by the model.
"""

import logging
from typing import Dict, Optional, Union, List
from PySide6.QtWidgets import (
    QWidget, QSplitter, QVBoxLayout, QHBoxLayout, QMenu, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from ui.widgets.split_pane_model import SplitPaneModel, LeafNode, SplitNode
from ui.widgets.widget_registry import WidgetType, widget_registry
from ui.widgets.pane_header import PaneHeaderBar
from ui.vscode_theme import get_splitter_stylesheet
from PySide6.QtCore import QTimer

logger = logging.getLogger(__name__)


class PaneContent(QWidget):
    """
    View wrapper for AppWidget.
    
    This is a thin presentation layer that:
    - Adds borders and visual styling
    - Provides header bar if configured
    - Handles context menus
    - Routes actions to the model
    
    It does NOT own the AppWidget - that's owned by the LeafNode in the model.
    """
    
    def __init__(self, leaf_node: LeafNode, parent=None):
        """
        Initialize the pane wrapper.
        
        Args:
            leaf_node: The model node containing the AppWidget
            parent: Parent widget
        """
        super().__init__(parent)
        self.leaf_node = leaf_node
        self.header_bar = None
        self.is_active = False
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI wrapper around the AppWidget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Check if we should show header for this widget type
        config = widget_registry.get_config(self.leaf_node.widget_type)
        if config and config.show_header:
            # Create header bar
            self.header_bar = PaneHeaderBar(
                self.leaf_node.id,
                show_type_menu=config.allow_type_change if config else False
            )
            
            # Connect header signals to request actions through AppWidget
            self.header_bar.split_horizontal_requested.connect(
                lambda: self.request_split("horizontal")
            )
            self.header_bar.split_vertical_requested.connect(
                lambda: self.request_split("vertical")
            )
            self.header_bar.close_requested.connect(
                lambda: self.request_close()
            )
            if hasattr(self.header_bar, 'type_menu_requested'):
                self.header_bar.type_menu_requested.connect(self.show_type_menu)
                
            layout.addWidget(self.header_bar)
            
        # Add the AppWidget from the model
        if self.leaf_node.app_widget:
            layout.addWidget(self.leaf_node.app_widget)
        else:
            logger.error(f"No AppWidget in leaf node {self.leaf_node.id}")
            
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
    def request_split(self, orientation: str):
        """Request a split action through the AppWidget."""
        if self.leaf_node.app_widget:
            self.leaf_node.app_widget.request_action('split', {
                'orientation': orientation,
                'leaf_id': self.leaf_node.id
            })
            
    def request_close(self):
        """Request a close action through the AppWidget."""
        if self.leaf_node.app_widget:
            self.leaf_node.app_widget.request_action('close', {
                'leaf_id': self.leaf_node.id
            })
            
    def mousePressEvent(self, event):
        """Handle mouse press to focus this pane."""
        if event.button() == Qt.LeftButton:
            if self.leaf_node.app_widget:
                self.leaf_node.app_widget.request_focus()
        super().mousePressEvent(event)
        
    def contextMenuEvent(self, event):
        """Show context menu."""
        # Request focus first
        if self.leaf_node.app_widget:
            self.leaf_node.app_widget.request_focus()
            
        # Check if we should preserve native context menu
        config = widget_registry.get_config(self.leaf_node.widget_type)
        if config and config.preserve_context_menu:
            # Let the AppWidget handle its own context menu
            if self.leaf_node.app_widget:
                # Forward the event to the AppWidget
                self.leaf_node.app_widget.contextMenuEvent(event)
            return
            
        # Show our custom menu
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
            split_h.triggered.connect(lambda: self.request_split("horizontal"))
            menu.addAction(split_h)
            
            split_v = QAction("Split Vertical ↓", self)
            split_v.triggered.connect(lambda: self.request_split("vertical"))
            menu.addAction(split_v)
            
            menu.addSeparator()
            
            close = QAction("Close Pane", self)
            close.triggered.connect(lambda: self.request_close())
            menu.addAction(close)
            
        # Always allow type change from context menu if configured
        config = widget_registry.get_config(self.leaf_node.widget_type)
        if config and config.allow_type_change:
            if not self.header_bar:
                menu.addSeparator()
            type_menu = menu.addMenu("Change Type")
            for widget_type in WidgetType:
                action = QAction(widget_type.value.replace("_", " ").title(), self)
                action.triggered.connect(
                    lambda checked, wt=widget_type: self.change_widget_type(wt)
                )
                if widget_type == self.leaf_node.widget_type:
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
            action.triggered.connect(
                lambda checked, wt=widget_type: self.change_widget_type(wt)
            )
            if widget_type == self.leaf_node.widget_type:
                action.setCheckable(True)
                action.setChecked(True)
            menu.addAction(action)
            
        # Show menu below the type button
        if self.header_bar and hasattr(self.header_bar, 'type_button'):
            menu.exec(self.header_bar.type_button.mapToGlobal(
                self.header_bar.type_button.rect().bottomLeft()
            ))
        else:
            menu.exec(self.mapToGlobal(self.rect().topLeft()))
            
    def change_widget_type(self, new_type: WidgetType):
        """Request widget type change through AppWidget."""
        if self.leaf_node.app_widget:
            self.leaf_node.app_widget.request_action('change_type', {
                'leaf_id': self.leaf_node.id,
                'new_type': new_type
            })
            
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


class SplitPaneWidget(QWidget):
    """
    View layer for split pane - renders the model's tree structure.
    
    This widget:
    - Uses SplitPaneModel for all data and operations
    - Renders the tree structure as Qt widgets
    - Connects AppWidget signals to model operations
    - Preserves AppWidgets during refresh (they live in the model)
    """
    
    # Signals
    pane_added = Signal(str)  # pane_id
    pane_removed = Signal(str)  # pane_id
    active_pane_changed = Signal(str)  # pane_id
    layout_changed = Signal()
    
    def __init__(self, initial_widget_type: WidgetType = WidgetType.TEXT_EDITOR, parent=None):
        """
        Initialize the split pane widget.
        
        Args:
            initial_widget_type: Type of widget for initial pane
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Create the model - it owns all AppWidgets
        self.model = SplitPaneModel(initial_widget_type)
        
        # View tracking
        self.pane_wrappers: Dict[str, PaneContent] = {}
        self.splitters: Dict[str, QSplitter] = {}
        
        # Set up UI
        self.setup_ui()
        
        # Connect signals from model's AppWidgets
        self.connect_model_signals()
        
        # Set up focus polling timer to detect which pane has focus
        self.focus_timer = QTimer()
        self.focus_timer.timeout.connect(self.check_focus)
        self.focus_timer.start(100)  # Check every 100ms
        
        logger.info(f"SplitPaneWidget initialized with model root {self.model.root.id}")
        
    def setup_ui(self):
        """Initialize the UI."""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Initial render
        self.refresh_view()
        
    def connect_model_signals(self):
        """Connect signals from all AppWidgets in the model to our handlers."""
        def connect_widget(leaf: LeafNode):
            if leaf.app_widget:
                # Clean slate - disconnect all existing connections
                try:
                    leaf.app_widget.action_requested.disconnect()
                except (RuntimeError, TypeError):
                    pass  # No connections to disconnect
                try:
                    leaf.app_widget.focus_requested.disconnect()
                except (RuntimeError, TypeError):
                    pass  # No connections to disconnect
                    
                # Connect to our handlers - use default arguments to capture current values
                leaf.app_widget.action_requested.connect(
                    lambda action, params, leaf_id=leaf.id: self.handle_widget_action(leaf_id, action, params)
                )
                leaf.app_widget.focus_requested.connect(
                    lambda leaf_id=leaf.id: self.set_active_pane(leaf_id)
                )
                
        # Connect all widgets in tree
        self.model.traverse_tree(callback=connect_widget)
        
    def handle_widget_action(self, leaf_id: str, action: str, params: dict):
        """
        Handle action from an AppWidget.
        
        Args:
            leaf_id: ID of leaf that initiated the action
            action: Action type
            params: Action parameters
        """
        logger.info(f"Handling action from {leaf_id}: {action} with params {params}")
        
        if action == 'split':
            orientation = params.get('orientation', 'horizontal')
            target_id = params.get('leaf_id', leaf_id)
            new_id = self.model.split_pane(target_id, orientation)
            if new_id:
                self.refresh_view()
                self.pane_added.emit(new_id)
                
        elif action == 'close':
            target_id = params.get('leaf_id', leaf_id)
            if self.model.close_pane(target_id):
                self.refresh_view()
                self.pane_removed.emit(target_id)
                
        elif action == 'change_type':
            target_id = params.get('leaf_id', leaf_id)
            new_type = params.get('new_type')
            if new_type and self.model.change_pane_type(target_id, new_type):
                self.refresh_view()
                
        elif action == 'focus':
            target_id = params.get('leaf_id', leaf_id)
            self.set_active_pane(target_id)
            
    def refresh_view(self):
        """
        Rebuild the view from the model.
        
        AppWidgets are preserved - they live in the model.
        Only the view wrappers (PaneContent) are recreated.
        """
        logger.debug("Refreshing view")
        
        # Clear layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
                
        # Clean up old view wrappers (NOT the AppWidgets!)
        for wrapper in self.pane_wrappers.values():
            wrapper.deleteLater()
        self.pane_wrappers.clear()
        self.splitters.clear()
        
        # Render the model's tree
        root_widget = self.render_node(self.model.root)
        if root_widget:
            self.layout.addWidget(root_widget)
            
        # Reconnect signals (in case new widgets were created)
        self.connect_model_signals()
        
        # Update active pane visual
        self.update_active_pane_visual()
        
        # Emit signal
        self.layout_changed.emit()
        
    def render_node(self, node: Optional[Union[LeafNode, SplitNode]]) -> Optional[QWidget]:
        """
        Render a node from the model as Qt widgets.
        
        Args:
            node: Node to render
            
        Returns:
            QWidget representing the node
        """
        if not node:
            return None
            
        if isinstance(node, LeafNode):
            # Create view wrapper for the AppWidget
            wrapper = PaneContent(node)
            self.pane_wrappers[node.id] = wrapper
            return wrapper
            
        elif isinstance(node, SplitNode):
            # Create splitter
            splitter = QSplitter(
                Qt.Horizontal if node.orientation == "horizontal" else Qt.Vertical
            )
            
            # Apply styling
            splitter.setStyleSheet(get_splitter_stylesheet())
            
            # Render children
            if node.first:
                first_widget = self.render_node(node.first)
                if first_widget:
                    splitter.addWidget(first_widget)
                    
            if node.second:
                second_widget = self.render_node(node.second)
                if second_widget:
                    splitter.addWidget(second_widget)
                    
            # Apply ratio
            if splitter.count() == 2:
                total = 1000
                first_size = int(total * node.ratio)
                splitter.setSizes([first_size, total - first_size])
                
            # Track ratio changes
            splitter.splitterMoved.connect(
                lambda: self.update_ratio(node, splitter)
            )
            
            self.splitters[node.id] = splitter
            return splitter
            
        return None
        
    def update_ratio(self, node: SplitNode, splitter: QSplitter):
        """Update split ratio when user drags splitter."""
        sizes = splitter.sizes()
        total = sum(sizes)
        if total > 0:
            ratio = sizes[0] / total
            self.model.update_split_ratio(node, ratio)
            
    def check_focus(self):
        """Check which pane currently has focus and update active pane accordingly."""
        try:
            focused_widget = self.focusWidget()
            if focused_widget:
                # Walk up the widget hierarchy to find which pane wrapper contains the focused widget
                current = focused_widget
                while current:
                    # Check if current widget is a pane wrapper
                    for pane_id, wrapper in self.pane_wrappers.items():
                        if current == wrapper or wrapper.isAncestorOf(current):
                            # Found which pane has focus - update active pane if different
                            if pane_id != self.model.get_active_pane_id():
                                print(f"🔍 Focus detected on pane {pane_id} via polling")
                                self.set_active_pane(pane_id)
                            return
                    current = current.parent()
        except Exception as e:
            # Ignore errors in focus polling
            pass

    def update_active_pane_visual(self):
        """Update visual indication of active pane."""
        active_id = self.model.get_active_pane_id()
        for pane_id, wrapper in self.pane_wrappers.items():
            wrapper.set_active(pane_id == active_id)
            
    # Public API methods that delegate to model
    
    def split_horizontal(self, pane_id: str):
        """Split pane horizontally."""
        new_id = self.model.split_pane(pane_id, "horizontal")
        if new_id:
            self.refresh_view()
            self.pane_added.emit(new_id)
            
    def split_vertical(self, pane_id: str):
        """Split pane vertically."""
        new_id = self.model.split_pane(pane_id, "vertical")
        if new_id:
            self.refresh_view()
            self.pane_added.emit(new_id)
            
    def close_pane(self, pane_id: str):
        """Close a pane."""
        if self.model.close_pane(pane_id):
            self.refresh_view()
            self.pane_removed.emit(pane_id)
            
    def set_active_pane(self, pane_id: str):
        """Set the active pane."""
        old_active = self.model.get_active_pane_id()
        print(f"🎯 set_active_pane called: {old_active} → {pane_id}")
        logger.debug(f"🎯 set_active_pane called with: {pane_id}")
        logger.debug(f"🎯 Previous active pane: {old_active}")
        
        if self.model.set_active_pane(pane_id):
            print(f"✅ Active pane successfully changed to: {pane_id}")
            logger.debug(f"✅ Active pane successfully changed to: {pane_id}")
            self.update_active_pane_visual()
            self.active_pane_changed.emit(pane_id)
        else:
            print(f"❌ Failed to set active pane to: {pane_id}")
            logger.warning(f"❌ Failed to set active pane to: {pane_id}")
            
    def get_current_split_widget(self):
        """Compatibility method - returns self."""
        return self
        
    @property
    def active_pane_id(self) -> str:
        """Get active pane ID from model."""
        return self.model.get_active_pane_id()
        
    def get_pane_count(self) -> int:
        """Get number of panes."""
        return len(self.model.leaves)
        
    def get_all_pane_ids(self) -> List[str]:
        """Get all pane IDs."""
        return list(self.model.leaves.keys())
        
    def get_state(self) -> dict:
        """Get state for persistence."""
        return self.model.to_dict()
        
    def set_state(self, state: dict):
        """Restore state from persistence."""
        self.model.from_dict(state)
        self.refresh_view()
        
    def cleanup(self):
        """Clean up all resources."""
        logger.info("Cleaning up SplitPaneWidget")
        if hasattr(self, 'focus_timer'):
            self.focus_timer.stop()
        self.model.cleanup_all_widgets()