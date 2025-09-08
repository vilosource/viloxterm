"""Split tree manager for handling recursive workspace splits."""

import uuid
from typing import Dict, List, Optional, Tuple, Any
from PySide6.QtWidgets import QWidget, QSplitter, QTabWidget, QPushButton, QVBoxLayout
from PySide6.QtCore import QObject, Signal, Qt
from models.layout_state import LayoutState, SplitNode, SplitContainer, ContentPane, TabInfo


class PlaceholderWidget(QWidget):
    """Simple placeholder widget for new splits."""
    
    def __init__(self, text: str = "New Pane"):
        super().__init__()
        self.setup_ui(text)
    
    def setup_ui(self, text: str):
        """Setup placeholder UI."""
        layout = QVBoxLayout(self)
        button = QPushButton(text)
        button.setEnabled(False)  # Non-interactive for now
        layout.addWidget(button)


class SplitTreeManager(QObject):
    """Manages split tree operations and widget synchronization."""
    
    # Signals
    pane_split = Signal(str, str)  # old_pane_id, new_pane_id
    pane_closed = Signal(str)  # pane_id
    tab_added = Signal(str, str)  # pane_id, tab_id
    tab_removed = Signal(str, str)  # pane_id, tab_id
    tab_moved = Signal(str, str, str)  # tab_id, from_pane_id, to_pane_id
    active_pane_changed = Signal(str)  # pane_id
    layout_changed = Signal()  # General layout structure change
    
    def __init__(self, initial_layout: Optional[LayoutState] = None):
        super().__init__()
        self.layout = initial_layout or LayoutState()
        self._widget_cache: Dict[str, QWidget] = {}
        self._root_widget: Optional[QWidget] = None
        
    @property
    def root_widget(self) -> Optional[QWidget]:
        """Get the root widget representing the layout."""
        return self._root_widget
    
    def get_layout_state(self) -> LayoutState:
        """Get current layout state."""
        return self.layout
    
    def set_layout_state(self, layout: LayoutState) -> None:
        """Set new layout state and rebuild widgets."""
        self.layout = layout
        self._clear_widget_cache()
        self._root_widget = self._create_widget_tree(self.layout.root)
        self.layout_changed.emit()
    
    def get_active_pane_id(self) -> Optional[str]:
        """Get the currently active pane ID."""
        return self.layout.active_pane_id
    
    def set_active_pane(self, pane_id: str) -> bool:
        """Set the active pane."""
        if self.layout.set_active_pane(pane_id):
            self.active_pane_changed.emit(pane_id)
            return True
        return False
    
    def get_all_pane_ids(self) -> List[str]:
        """Get all pane IDs in the layout."""
        return [pane.node_id for pane in self.layout.get_all_panes()]
    
    def split_pane(self, pane_id: str, orientation: Qt.Orientation) -> Optional[str]:
        """
        Split a pane in the specified orientation.
        Returns the ID of the newly created pane, or None if failed.
        """
        pane = self.layout.find_node(pane_id)
        if not isinstance(pane, ContentPane):
            return None
        
        # Create new pane
        new_pane = ContentPane()
        
        if pane.parent is None:
            # Root pane case - create new container as root
            new_container = SplitContainer(
                orientation=orientation,
                children=[pane, new_pane]
            )
            self.layout.root = new_container
        else:
            # Non-root pane case
            parent = pane.parent
            
            if parent.orientation == orientation and len(parent.children) > 1:
                # Same orientation - add to existing container
                pane_index = parent.children.index(pane)
                parent.add_child(new_pane, pane_index + 1)
            else:
                # Different orientation or single child - create new container
                new_container = SplitContainer(
                    orientation=orientation,
                    children=[pane, new_pane]
                )
                parent.replace_child(pane, new_container)
        
        # Update widgets
        self._rebuild_widget_tree()
        
        # Emit signals
        self.pane_split.emit(pane_id, new_pane.node_id)
        self.layout_changed.emit()
        
        return new_pane.node_id
    
    def close_pane(self, pane_id: str) -> bool:
        """
        Close a pane and merge its parent if necessary.
        Returns True if successful, False otherwise.
        """
        pane = self.layout.find_node(pane_id)
        if not isinstance(pane, ContentPane):
            return False
        
        # Don't close the last pane
        if len(self.layout.get_all_panes()) <= 1:
            return False
        
        # Update active pane if necessary
        if self.layout.active_pane_id == pane_id:
            other_panes = [p for p in self.layout.get_all_panes() if p.node_id != pane_id]
            if other_panes:
                self.layout.active_pane_id = other_panes[0].node_id
        
        if pane.parent is None:
            # This shouldn't happen if there are multiple panes
            return False
        
        parent = pane.parent
        parent.remove_child(pane)
        
        # Simplify parent if it has only one child
        if parent.can_be_simplified() and parent.parent is not None:
            grandparent = parent.parent
            if parent.children:
                remaining_child = parent.children[0]
                grandparent.replace_child(parent, remaining_child)
            else:
                grandparent.remove_child(parent)
        elif parent.can_be_simplified() and parent.parent is None:
            # Parent is root with one child
            if parent.children:
                self.layout.root = parent.children[0]
                self.layout.root.parent = None
        
        # Update widgets
        self._rebuild_widget_tree()
        
        # Emit signals
        self.pane_closed.emit(pane_id)
        self.layout_changed.emit()
        
        return True
    
    def add_tab(self, pane_id: str, tab_info: TabInfo, index: Optional[int] = None) -> bool:
        """Add a tab to the specified pane."""
        pane = self.layout.find_node(pane_id)
        if not isinstance(pane, ContentPane):
            return False
        
        pane.add_tab(tab_info, index)
        
        # Update the corresponding widget if it exists
        widget = self._widget_cache.get(pane_id)
        if isinstance(widget, QTabWidget):
            self._sync_tab_widget(widget, pane)
        
        self.tab_added.emit(pane_id, tab_info.tab_id)
        return True
    
    def remove_tab(self, pane_id: str, tab_index: int) -> Optional[TabInfo]:
        """Remove a tab from the specified pane."""
        pane = self.layout.find_node(pane_id)
        if not isinstance(pane, ContentPane):
            return None
        
        tab_info = pane.remove_tab(tab_index)
        if tab_info:
            # Update the corresponding widget if it exists
            widget = self._widget_cache.get(pane_id)
            if isinstance(widget, QTabWidget):
                self._sync_tab_widget(widget, pane)
            
            self.tab_removed.emit(pane_id, tab_info.tab_id)
        
        return tab_info
    
    def move_tab(self, tab_id: str, from_pane_id: str, to_pane_id: str, 
                 to_index: Optional[int] = None) -> bool:
        """Move a tab from one pane to another."""
        from_pane = self.layout.find_node(from_pane_id)
        to_pane = self.layout.find_node(to_pane_id)
        
        if not (isinstance(from_pane, ContentPane) and isinstance(to_pane, ContentPane)):
            return False
        
        # Find the tab in the source pane
        tab_info = None
        tab_index = -1
        for i, tab in enumerate(from_pane.tabs):
            if tab.tab_id == tab_id:
                tab_info = tab
                tab_index = i
                break
        
        if tab_info is None:
            return False
        
        # Remove from source and add to destination
        from_pane.remove_tab(tab_index)
        to_pane.add_tab(tab_info, to_index)
        
        # Update widgets
        from_widget = self._widget_cache.get(from_pane_id)
        to_widget = self._widget_cache.get(to_pane_id)
        
        if isinstance(from_widget, QTabWidget):
            self._sync_tab_widget(from_widget, from_pane)
        if isinstance(to_widget, QTabWidget):
            self._sync_tab_widget(to_widget, to_pane)
        
        self.tab_moved.emit(tab_id, from_pane_id, to_pane_id)
        return True
    
    def resize_split(self, container_id: str, sizes: List[float]) -> bool:
        """Resize the splits in a container."""
        container = self.layout.find_node(container_id)
        if not isinstance(container, SplitContainer):
            return False
        
        if container.set_sizes(sizes):
            # Update the corresponding splitter widget
            widget = self._widget_cache.get(container_id)
            if isinstance(widget, QSplitter):
                self._sync_splitter_sizes(widget, container)
            return True
        
        return False
    
    def _create_widget_tree(self, node: SplitNode) -> QWidget:
        """Create Qt widgets from the split tree."""
        if isinstance(node, ContentPane):
            return self._create_tab_widget(node)
        elif isinstance(node, SplitContainer):
            return self._create_splitter_widget(node)
        else:
            return PlaceholderWidget("Unknown Node")
    
    def _create_tab_widget(self, pane: ContentPane):
        """Create a TabContainer for a content pane."""
        from ui.widgets.tab_container import TabContainer, PlaceholderWidget
        
        tab_widget = TabContainer(pane.node_id)
        
        # Add tabs
        for tab_info in pane.tabs:
            if tab_info.widget_type == "placeholder":
                widget = PlaceholderWidget(tab_info.title)
            else:
                # For now, everything is a placeholder
                widget = PlaceholderWidget(tab_info.title)
            
            tab_widget.add_tab_with_widget(widget, tab_info.title)
        
        # Set active tab
        if 0 <= pane.active_tab < tab_widget.count():
            tab_widget.setCurrentIndex(pane.active_tab)
        
        # Cache the widget
        self._widget_cache[pane.node_id] = tab_widget
        
        return tab_widget
    
    def _create_splitter_widget(self, container: SplitContainer) -> QSplitter:
        """Create a QSplitter for a split container."""
        splitter = QSplitter(container.orientation)
        
        # Add child widgets
        for child in container.children:
            child_widget = self._create_widget_tree(child)
            splitter.addWidget(child_widget)
        
        # Set sizes
        if container.sizes and len(container.sizes) == len(container.children):
            # Convert relative sizes to absolute sizes
            total_size = 1000  # Use a fixed total for calculations
            absolute_sizes = [int(size * total_size) for size in container.sizes]
            splitter.setSizes(absolute_sizes)
        
        # Cache the widget
        self._widget_cache[container.node_id] = splitter
        
        return splitter
    
    def _sync_tab_widget(self, tab_widget, pane: ContentPane) -> None:
        """Synchronize a tab widget with its pane data."""
        from ui.widgets.tab_container import TabContainer, PlaceholderWidget
        
        # Clear existing tabs
        while tab_widget.count() > 0:
            tab_widget.removeTab(0)
        
        # Add current tabs
        for tab_info in pane.tabs:
            if tab_info.widget_type == "placeholder":
                widget = PlaceholderWidget(tab_info.title)
            else:
                widget = PlaceholderWidget(tab_info.title)
            
            if isinstance(tab_widget, TabContainer):
                tab_widget.add_tab_with_widget(widget, tab_info.title)
            else:
                tab_widget.addTab(widget, tab_info.title)
        
        # Set active tab
        if 0 <= pane.active_tab < tab_widget.count():
            tab_widget.setCurrentIndex(pane.active_tab)
    
    def _sync_splitter_sizes(self, splitter: QSplitter, container: SplitContainer) -> None:
        """Synchronize splitter sizes with container data."""
        if container.sizes and len(container.sizes) == splitter.count():
            total_size = 1000
            absolute_sizes = [int(size * total_size) for size in container.sizes]
            splitter.setSizes(absolute_sizes)
    
    def _rebuild_widget_tree(self) -> None:
        """Rebuild the entire widget tree."""
        self._clear_widget_cache()
        self._root_widget = self._create_widget_tree(self.layout.root)
    
    def _clear_widget_cache(self) -> None:
        """Clear the widget cache."""
        self._widget_cache.clear()
    
    def get_widget_for_pane(self, pane_id: str) -> Optional[QWidget]:
        """Get the widget associated with a pane ID."""
        return self._widget_cache.get(pane_id)
    
    def serialize_state(self) -> dict:
        """Serialize the current layout state."""
        return self.layout.to_dict()
    
    def deserialize_state(self, state_data: dict) -> bool:
        """Deserialize and apply a layout state."""
        try:
            new_layout = LayoutState.from_dict(state_data)
            self.set_layout_state(new_layout)
            return True
        except Exception:
            return False