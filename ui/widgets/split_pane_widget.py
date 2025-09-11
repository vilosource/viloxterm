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
from PySide6.QtCore import Qt, Signal, QEvent, QTimer
from PySide6.QtGui import QAction

from ui.widgets.split_pane_model import SplitPaneModel, LeafNode, SplitNode
from ui.widgets.widget_registry import WidgetType, widget_registry
from ui.widgets.pane_header import PaneHeaderBar
from ui.widgets.widget_pool import get_widget_pool, cleanup_widget_pool
# from ui.widgets.overlay_transition import TransitionManager  # Disabled - causing UI freeze
from ui.vscode_theme import get_splitter_stylesheet, EDITOR_BACKGROUND

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
        
        # Configure widget attributes to prevent white flash
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)  # Widget paints all pixels
        self.setAttribute(Qt.WA_NoSystemBackground, True)  # No system background
        self.setAutoFillBackground(False)  # No automatic background fill
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI wrapper around the AppWidget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Check if we should show header for this widget type
        config = widget_registry.get_config(self.leaf_node.widget_type)
        logger.debug(f"PaneContent setup for {self.leaf_node.id}: widget_type={self.leaf_node.widget_type}, config={config}")
        if config:
            logger.debug(f"  show_header={config.show_header}, allow_type_change={config.allow_type_change}")
        
        if config and config.show_header:
            # Create header bar
            self.header_bar = PaneHeaderBar(
                self.leaf_node.id,
                show_type_menu=config.allow_type_change if config else False
            )
            logger.debug(f"Created header bar with show_type_menu={config.allow_type_change}")
            
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
            logger.debug(f"Added AppWidget {self.leaf_node.app_widget.widget_id} to PaneContent")
        else:
            logger.error(f"No AppWidget in leaf node {self.leaf_node.id} of type {self.leaf_node.widget_type}")
            # Create a placeholder to show the issue visually
            from PySide6.QtWidgets import QLabel
            placeholder = QLabel(f"Widget Loading Failed\nNode: {self.leaf_node.id}\nType: {self.leaf_node.widget_type}")
            placeholder.setStyleSheet("""
                QLabel {
                    background-color: #3c3c3c;
                    color: #ff6b6b;
                    padding: 20px;
                    font-family: monospace;
                }
            """)
            placeholder.setAlignment(Qt.AlignCenter)
            layout.addWidget(placeholder)
            
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
        
        # Initialize widget pool for reusing widgets
        self.widget_pool = get_widget_pool()
        
        # Initialize transition manager for overlay effects
        self.transition_manager = None  # Will be initialized after UI setup
        
        # Set up UI
        self.setup_ui()
        
        # Connect signals from model's AppWidgets
        self.connect_model_signals()
        
        # Event-driven focus detection will be set up when panes are created
        
        logger.info(f"SplitPaneWidget initialized with model root {self.model.root.id}")
        
    def setup_ui(self):
        """Initialize the UI."""
        # Set dark background to prevent white flash
        self.setStyleSheet(f"""
            SplitPaneWidget {{
                background-color: {EDITOR_BACKGROUND};
            }}
        """)
        self.setAutoFillBackground(True)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Initial render
        self.refresh_view()
        
        # Transition manager disabled - was causing UI to freeze
        # self.transition_manager = TransitionManager(self)
        self.transition_manager = None
        
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
        
        # Disable updates during the entire refresh to prevent white flash
        self.setUpdatesEnabled(False)
        try:
            # Clear layout
            while self.layout.count():
                item = self.layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
                    
            # Clean up old view wrappers (NOT the AppWidgets!)
            # IMPORTANT: Detach AppWidgets first to prevent them from being deleted
            for wrapper in self.pane_wrappers.values():
                if hasattr(wrapper, 'leaf_node') and wrapper.leaf_node.app_widget:
                    # Detach the AppWidget from the wrapper before deleting wrapper
                    wrapper.leaf_node.app_widget.setParent(None)
                    logger.debug(f"Detached AppWidget {wrapper.leaf_node.app_widget.widget_id} from wrapper before deletion")
                wrapper.deleteLater()
            self.pane_wrappers.clear()
            
            # Release splitters back to pool for reuse
            for splitter in self.splitters.values():
                self.widget_pool.release(splitter)
            self.splitters.clear()
            
            # Render the model's tree
            root_widget = self.render_node(self.model.root)
            if root_widget:
                self.layout.addWidget(root_widget)
                
            # Reconnect signals (in case new widgets were created)
            self.connect_model_signals()
            
            # Update active pane visual
            self.update_active_pane_visual()
            
            # Update pane numbers display
            self.update_pane_numbers_display()
            
        finally:
            # Re-enable updates once the entire refresh is complete
            self.setUpdatesEnabled(True)
            
        # Emit signal
        self.layout_changed.emit()
    
    def incremental_update_for_split(self, original_pane_id: str, new_pane_id: str):
        """
        Incrementally update the view for a split operation without full refresh.
        This avoids destroying and recreating the entire widget tree.
        
        Args:
            original_pane_id: ID of the pane that was split (now first child of split)
            new_pane_id: ID of the newly created pane (second child of split)
        """
        logger.debug(f"Incremental update for split: {original_pane_id} -> {new_pane_id}")
        
        # Disable updates during the incremental change
        self.setUpdatesEnabled(False)
        try:
            # Find the widget that needs to be replaced (the original pane that was split)
            old_wrapper = self.pane_wrappers.get(original_pane_id)
            if not old_wrapper:
                logger.warning(f"Could not find wrapper for {original_pane_id}, falling back to full refresh")
                self.refresh_view()
                return
            
            # Find the parent widget of the old wrapper
            parent_widget = old_wrapper.parent()
            if not parent_widget:
                logger.warning("Old wrapper has no parent, falling back to full refresh")
                self.refresh_view()
                return
            
            # Find the original leaf node in the model
            original_leaf = self.model.find_leaf(original_pane_id)
            if not original_leaf or not original_leaf.parent:
                logger.warning(f"Could not find original leaf or its parent for {original_pane_id}, falling back to full refresh")
                self.refresh_view()
                return
            
            # The parent of the original leaf should now be the split node
            split_node = original_leaf.parent
            if not isinstance(split_node, SplitNode):
                logger.warning(f"Parent of {original_pane_id} is not a SplitNode, falling back to full refresh")
                self.refresh_view()
                return
            
            # Create the new splitter widget for this split node
            new_splitter = self.render_node(split_node)
            if not new_splitter:
                logger.warning("Failed to render split node, falling back to full refresh")
                self.refresh_view()
                return
            
            # Replace the old wrapper with the new splitter in the parent
            if isinstance(parent_widget, QSplitter):
                # Find the index of the old widget
                index = -1
                for i in range(parent_widget.count()):
                    if parent_widget.widget(i) == old_wrapper:
                        index = i
                        break
                
                if index >= 0:
                    # Get the size of the old widget before removing
                    sizes = parent_widget.sizes()
                    
                    # Remove old wrapper from parent splitter
                    old_wrapper.setParent(None)
                    old_wrapper.deleteLater()
                    # Don't delete from pane_wrappers - render_node will update it
                    
                    # Insert new splitter at the same position
                    parent_widget.insertWidget(index, new_splitter)
                    
                    # Restore the size
                    parent_widget.setSizes(sizes)
                else:
                    logger.warning("Could not find old wrapper in parent splitter")
                    self.refresh_view()
                    return
            elif isinstance(parent_widget, QWidget) and parent_widget == self:
                # This is the root widget
                # Remove old wrapper from layout
                self.layout.removeWidget(old_wrapper)
                old_wrapper.setParent(None)
                old_wrapper.deleteLater()
                # Don't delete from pane_wrappers - render_node will update it
                
                # Add new splitter to layout
                self.layout.addWidget(new_splitter)
            else:
                logger.warning(f"Unexpected parent widget type: {type(parent_widget)}")
                self.refresh_view()
                return
            
            # Reconnect signals for new widgets
            self.connect_model_signals()
            
            # Update active pane visual
            self.update_active_pane_visual()
            
            logger.debug("Incremental update completed successfully")
            
        finally:
            # Re-enable updates
            self.setUpdatesEnabled(True)
        
        # Emit signal
        self.layout_changed.emit()
    
    def _find_node_by_id(self, node: Optional[Union[LeafNode, SplitNode]], node_id: str) -> Optional[Union[LeafNode, SplitNode]]:
        """
        Recursively find a node in the tree by its ID.
        
        Args:
            node: Current node to search from
            node_id: ID of the node to find
            
        Returns:
            The node with the given ID, or None if not found
        """
        if not node:
            return None
        
        if node.id == node_id:
            return node
        
        if isinstance(node, SplitNode):
            # Search in children
            result = self._find_node_by_id(node.first, node_id)
            if result:
                return result
            return self._find_node_by_id(node.second, node_id)
        
        return None
        
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
            
            # Install event filter to detect focus changes
            self.install_focus_event_filters(wrapper)
            
            return wrapper
            
        elif isinstance(node, SplitNode):
            # Get splitter from pool or create new one
            orientation = Qt.Horizontal if node.orientation == "horizontal" else Qt.Vertical
            splitter = self.widget_pool.acquire_splitter(orientation)
            
            # Pool already configures optimal settings, but ensure they're set
            splitter.setOpaqueResize(True)  # Real-time resize (actually reduces flashing)
            splitter.setChildrenCollapsible(False)  # Prevent child widgets from collapsing
            
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
            
    def eventFilter(self, obj, event):
        """Event filter to detect focus changes without polling."""
        if event.type() == QEvent.FocusIn:
            # Check if this widget belongs to one of our panes
            current = obj
            while current:
                for pane_id, wrapper in self.pane_wrappers.items():
                    if current == wrapper or wrapper.isAncestorOf(current):
                        # Found which pane got focus - update active pane if different
                        if pane_id != self.model.get_active_pane_id():
                            logger.debug(f"Focus detected on pane {pane_id} via event filter")
                            self.set_active_pane(pane_id)
                        return super().eventFilter(obj, event)
                current = current.parent()
        return super().eventFilter(obj, event)
        
    def install_focus_event_filters(self, wrapper):
        """Install event filters on wrapper and its child widgets to detect focus changes."""
        # Install filter on the wrapper itself
        wrapper.installEventFilter(self)
        
        # Install filters on all child widgets recursively
        def install_on_children(widget):
            for child in widget.findChildren(QWidget):
                child.installEventFilter(self)
                # Recursively install on children's children
                install_on_children(child)
                
        install_on_children(wrapper)

    def update_active_pane_visual(self):
        """Update visual indication of active pane."""
        active_id = self.model.get_active_pane_id()
        for pane_id, wrapper in self.pane_wrappers.items():
            wrapper.set_active(pane_id == active_id)
            
    def toggle_pane_numbers(self) -> bool:
        """
        Toggle pane number visibility.
        
        Returns:
            New visibility state
        """
        visible = self.model.toggle_pane_numbers()
        self.update_pane_numbers_display()
        return visible
        
    def update_pane_numbers_display(self):
        """Update all pane headers with current numbers."""
        # Ensure model indices are up to date
        self.model.update_pane_indices()
        
        # Update each pane's header
        for pane_id, wrapper in self.pane_wrappers.items():
            if wrapper.header_bar:
                number = self.model.get_pane_index(pane_id)
                wrapper.header_bar.set_pane_number(
                    number, 
                    self.model.show_pane_numbers
                )
            
    # Public API methods that delegate to model
    
    def split_horizontal(self, pane_id: str):
        """Split pane horizontally."""
        # Overlay transitions disabled - causing UI to freeze
        # if self.transition_manager:
        #     self.transition_manager.begin_transition()
        
        new_id = self.model.split_pane(pane_id, "horizontal")
        if new_id:
            # Full refresh is more reliable for now
            self.refresh_view()
            self.pane_added.emit(new_id)
            # Only restore focus if this widget is visible (i.e., in the active tab)
            if self.isVisible():
                self.restore_active_pane_focus()
        
        # End transition with fade
        # if self.transition_manager:
        #     self.transition_manager.end_transition(delay=10)
        
        return new_id
            
    def split_vertical(self, pane_id: str):
        """Split pane vertically."""
        # Overlay transitions disabled - causing UI to freeze
        # if self.transition_manager:
        #     self.transition_manager.begin_transition()
        
        new_id = self.model.split_pane(pane_id, "vertical")
        if new_id:
            # Full refresh is more reliable for now
            self.refresh_view()
            self.pane_added.emit(new_id)
            # Only restore focus if this widget is visible (i.e., in the active tab)
            if self.isVisible():
                self.restore_active_pane_focus()
        
        # End transition with fade
        # if self.transition_manager:
        #     self.transition_manager.end_transition(delay=10)
        
        return new_id
            
    def close_pane(self, pane_id: str):
        """Close a pane."""
        # Overlay transitions disabled - causing UI to freeze
        # if self.transition_manager:
        #     self.transition_manager.begin_transition()
        
        if self.model.close_pane(pane_id):
            self.refresh_view()
            # End transition with fade
            # if self.transition_manager:
            #     self.transition_manager.end_transition(delay=10)
            self.pane_removed.emit(pane_id)
            # Restore focus to the new active pane
            self.restore_active_pane_focus()
            
    def set_active_pane(self, pane_id: str, focus: bool = False):
        """
        Set the active pane.
        
        Args:
            pane_id: ID of the pane to activate
            focus: If True, also set keyboard focus to the pane's widget
        """
        old_active = self.model.get_active_pane_id()
        logger.debug(f"set_active_pane called: {old_active} → {pane_id}")
        logger.debug(f"🎯 set_active_pane called with: {pane_id}")
        logger.debug(f"🎯 Previous active pane: {old_active}")
        
        if self.model.set_active_pane(pane_id):
            logger.debug(f"Active pane successfully changed to: {pane_id}")
            logger.debug(f"✅ Active pane successfully changed to: {pane_id}")
            self.update_active_pane_visual()
            self.active_pane_changed.emit(pane_id)
            
            # If requested, also set keyboard focus to the specific pane
            if focus:
                # Focus the specific pane, not just the active one
                self.focus_specific_pane(pane_id)
        else:
            logger.debug(f"Failed to set active pane to: {pane_id}")
            logger.warning(f"❌ Failed to set active pane to: {pane_id}")
            
    def focus_specific_pane(self, pane_id: str):
        """
        Set keyboard focus to a specific pane's widget.
        
        Args:
            pane_id: ID of the pane to focus
        """
        # Find the pane's leaf node
        leaf = self.model.find_leaf(pane_id)
        if not leaf or not leaf.app_widget:
            logger.warning(f"Cannot focus pane {pane_id}: not found or no widget")
            return
            
        # Use a timer to ensure widget is ready, like restore_active_pane_focus does
        def set_focus():
            try:
                # Call the focus_widget method on the AppWidget
                if leaf.app_widget and hasattr(leaf.app_widget, 'focus_widget'):
                    logger.debug(f"Calling focus_widget on {leaf.app_widget.__class__.__name__} for pane {pane_id}")
                    leaf.app_widget.focus_widget()
                    logger.info(f"Keyboard focus set to pane {pane_id} widget")
            except Exception as e:
                logger.warning(f"Failed to set focus to pane {pane_id}: {e}")
                
        # Use slightly longer delay to ensure widget is fully ready
        QTimer.singleShot(50, set_focus)
    
    def restore_active_pane_focus(self):
        """
        Restore keyboard focus to the active pane's widget after a refresh.
        
        Uses QTimer to ensure the widget tree is fully rendered before setting focus.
        """
        # Prevent multiple simultaneous focus restorations
        if hasattr(self, '_restoring_focus') and self._restoring_focus:
            return
            
        active_id = self.model.get_active_pane_id()
        if not active_id:
            return
            
        # Find the active pane's leaf node
        leaf = self.model.find_leaf(active_id)
        if not leaf or not leaf.app_widget:
            return
            
        # Mark that we're restoring focus
        self._restoring_focus = True
        
        # Use a minimal timer delay to ensure widgets are ready
        def set_focus():
            try:
                # Call the focus_widget method on the AppWidget
                if leaf.app_widget and hasattr(leaf.app_widget, 'focus_widget'):
                    leaf.app_widget.focus_widget()
                    logger.debug(f"Focus restored to pane {active_id} after split")
            except Exception as e:
                logger.warning(f"Failed to restore focus to pane {active_id}: {e}")
            finally:
                # Clear the flag
                self._restoring_focus = False
                
        QTimer.singleShot(10, set_focus)
            
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
        
    def set_state(self, state: dict) -> bool:
        """
        Restore state from persistence.
        
        Returns:
            True if state was restored successfully, False otherwise
        """
        try:
            self.model.from_dict(state)
            self.refresh_view()
            # Restore focus to active pane after state restoration
            self.restore_active_pane_focus()
            return True
        except Exception as e:
            logger.error(f"Failed to restore state: {e}")
            return False
        
    def cleanup(self):
        """Clean up all resources."""
        logger.info("Cleaning up SplitPaneWidget")
        # No timer cleanup needed with event-driven focus
        self.model.cleanup_all_widgets()
        
        # Clean up widget pool and log statistics
        self.widget_pool.log_stats()
        # Note: Global pool cleanup is handled at application shutdown