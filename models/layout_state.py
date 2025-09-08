"""Split tree data model for recursive workspace layouts."""

import json
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from abc import ABC, abstractmethod
from PySide6.QtCore import Qt


@dataclass
class SplitNode(ABC):
    """Abstract base class for split tree nodes."""
    
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent: Optional['SplitContainer'] = field(default=None, repr=False)
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize node to dictionary."""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SplitNode':
        """Deserialize node from dictionary."""
        pass
    
    def get_root(self) -> 'SplitNode':
        """Get the root node of the tree."""
        if self.parent is None:
            return self
        return self.parent.get_root()
    
    def get_path(self) -> List[str]:
        """Get path from root to this node."""
        if self.parent is None:
            return [self.node_id]
        return self.parent.get_path() + [self.node_id]


@dataclass
class TabInfo:
    """Information about a tab within a pane."""
    
    tab_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "New Tab"
    widget_type: str = "placeholder"
    widget_data: Dict[str, Any] = field(default_factory=dict)
    is_closable: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize tab info to dictionary."""
        return {
            "tab_id": self.tab_id,
            "title": self.title,
            "widget_type": self.widget_type,
            "widget_data": self.widget_data,
            "is_closable": self.is_closable
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TabInfo':
        """Deserialize tab info from dictionary."""
        return cls(
            tab_id=data.get("tab_id", str(uuid.uuid4())),
            title=data.get("title", "New Tab"),
            widget_type=data.get("widget_type", "placeholder"),
            widget_data=data.get("widget_data", {}),
            is_closable=data.get("is_closable", True)
        )


@dataclass
class ContentPane(SplitNode):
    """Leaf node containing tabs and content widgets."""
    
    tabs: List[TabInfo] = field(default_factory=list)
    active_tab: int = 0
    
    def __post_init__(self):
        """Initialize with default tab if empty."""
        if not self.tabs:
            self.add_tab(TabInfo(title="Welcome"))
    
    def add_tab(self, tab_info: TabInfo, index: Optional[int] = None) -> None:
        """Add a tab to this pane."""
        if index is None:
            self.tabs.append(tab_info)
            self.active_tab = len(self.tabs) - 1
        else:
            self.tabs.insert(index, tab_info)
            if index <= self.active_tab:
                self.active_tab = min(self.active_tab + 1, len(self.tabs) - 1)
    
    def remove_tab(self, tab_index: int) -> Optional[TabInfo]:
        """Remove a tab by index. Returns removed tab or None."""
        if 0 <= tab_index < len(self.tabs):
            tab_info = self.tabs.pop(tab_index)
            
            # Adjust active tab index
            if tab_index < self.active_tab:
                self.active_tab -= 1
            elif tab_index == self.active_tab:
                self.active_tab = min(self.active_tab, len(self.tabs) - 1)
                
            # Ensure at least one tab remains
            if not self.tabs:
                self.add_tab(TabInfo(title="Empty"))
                
            return tab_info
        return None
    
    def move_tab(self, from_index: int, to_index: int) -> bool:
        """Move a tab from one position to another."""
        if not (0 <= from_index < len(self.tabs) and 0 <= to_index < len(self.tabs)):
            return False
            
        tab_info = self.tabs.pop(from_index)
        self.tabs.insert(to_index, tab_info)
        
        # Update active tab index
        if from_index == self.active_tab:
            self.active_tab = to_index
        elif from_index < self.active_tab <= to_index:
            self.active_tab -= 1
        elif to_index <= self.active_tab < from_index:
            self.active_tab += 1
            
        return True
    
    def get_active_tab(self) -> Optional[TabInfo]:
        """Get the currently active tab."""
        if 0 <= self.active_tab < len(self.tabs):
            return self.tabs[self.active_tab]
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize pane to dictionary."""
        return {
            "type": "pane",
            "node_id": self.node_id,
            "tabs": [tab.to_dict() for tab in self.tabs],
            "active_tab": self.active_tab
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentPane':
        """Deserialize pane from dictionary."""
        tabs = [TabInfo.from_dict(tab_data) for tab_data in data.get("tabs", [])]
        return cls(
            node_id=data.get("node_id", str(uuid.uuid4())),
            tabs=tabs,
            active_tab=data.get("active_tab", 0)
        )


@dataclass
class SplitContainer(SplitNode):
    """Container node that holds child splits."""
    
    orientation: Qt.Orientation = Qt.Horizontal
    children: List[SplitNode] = field(default_factory=list)
    sizes: List[float] = field(default_factory=list)
    
    def __post_init__(self):
        """Set parent references for children."""
        for child in self.children:
            child.parent = self
        
        # Ensure sizes match children count
        if len(self.sizes) != len(self.children):
            self.normalize_sizes()
    
    def add_child(self, child: SplitNode, index: Optional[int] = None) -> None:
        """Add a child node."""
        child.parent = self
        
        if index is None:
            self.children.append(child)
        else:
            self.children.insert(index, child)
            
        self.normalize_sizes()
    
    def remove_child(self, child: SplitNode) -> bool:
        """Remove a child node."""
        try:
            index = self.children.index(child)
            self.children.pop(index)
            child.parent = None
            self.normalize_sizes()
            return True
        except ValueError:
            return False
    
    def remove_child_by_index(self, index: int) -> Optional[SplitNode]:
        """Remove child by index. Returns removed child or None."""
        if 0 <= index < len(self.children):
            child = self.children.pop(index)
            child.parent = None
            self.normalize_sizes()
            return child
        return None
    
    def replace_child(self, old_child: SplitNode, new_child: SplitNode) -> bool:
        """Replace one child with another."""
        try:
            index = self.children.index(old_child)
            self.children[index] = new_child
            old_child.parent = None
            new_child.parent = self
            return True
        except ValueError:
            return False
    
    def normalize_sizes(self) -> None:
        """Ensure sizes list matches children count and sums to 1.0."""
        child_count = len(self.children)
        if child_count == 0:
            self.sizes = []
            return
        
        # If sizes don't match children count, create equal distribution
        if len(self.sizes) != child_count:
            self.sizes = [1.0 / child_count] * child_count
        else:
            # Normalize existing sizes to sum to 1.0
            total = sum(self.sizes)
            if total > 0:
                self.sizes = [size / total for size in self.sizes]
            else:
                self.sizes = [1.0 / child_count] * child_count
    
    def set_sizes(self, sizes: List[float]) -> bool:
        """Set custom sizes for children."""
        if len(sizes) != len(self.children):
            return False
        
        # Normalize to sum to 1.0
        total = sum(sizes)
        if total <= 0:
            return False
            
        self.sizes = [size / total for size in sizes]
        return True
    
    def find_node(self, node_id: str) -> Optional[SplitNode]:
        """Find a node by ID in the subtree."""
        if self.node_id == node_id:
            return self
        
        for child in self.children:
            if child.node_id == node_id:
                return child
            elif isinstance(child, SplitContainer):
                result = child.find_node(node_id)
                if result:
                    return result
        
        return None
    
    def get_all_panes(self) -> List[ContentPane]:
        """Get all content panes in the subtree."""
        panes = []
        for child in self.children:
            if isinstance(child, ContentPane):
                panes.append(child)
            elif isinstance(child, SplitContainer):
                panes.extend(child.get_all_panes())
        return panes
    
    def can_be_simplified(self) -> bool:
        """Check if this container can be simplified (has only one child)."""
        return len(self.children) <= 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize container to dictionary."""
        return {
            "type": "split",
            "node_id": self.node_id,
            "orientation": "horizontal" if self.orientation == Qt.Horizontal else "vertical",
            "children": [child.to_dict() for child in self.children],
            "sizes": self.sizes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SplitContainer':
        """Deserialize container from dictionary."""
        orientation_str = data.get("orientation", "horizontal")
        orientation = Qt.Horizontal if orientation_str == "horizontal" else Qt.Vertical
        
        # Recursively create children
        children = []
        for child_data in data.get("children", []):
            if child_data.get("type") == "pane":
                children.append(ContentPane.from_dict(child_data))
            elif child_data.get("type") == "split":
                children.append(SplitContainer.from_dict(child_data))
        
        container = cls(
            node_id=data.get("node_id", str(uuid.uuid4())),
            orientation=orientation,
            children=children,
            sizes=data.get("sizes", [])
        )
        
        return container


class LayoutState:
    """Complete layout state manager."""
    
    def __init__(self, root: Optional[SplitNode] = None):
        """Initialize with optional root node."""
        self.root = root or ContentPane()
        self.active_pane_id: Optional[str] = None
        
        # Set initial active pane
        if isinstance(self.root, ContentPane):
            self.active_pane_id = self.root.node_id
        else:
            panes = self.get_all_panes()
            if panes:
                self.active_pane_id = panes[0].node_id
    
    def find_node(self, node_id: str) -> Optional[SplitNode]:
        """Find any node by ID."""
        if self.root.node_id == node_id:
            return self.root
        
        if isinstance(self.root, SplitContainer):
            return self.root.find_node(node_id)
        
        return None
    
    def get_all_panes(self) -> List[ContentPane]:
        """Get all content panes in the layout."""
        if isinstance(self.root, ContentPane):
            return [self.root]
        elif isinstance(self.root, SplitContainer):
            return self.root.get_all_panes()
        return []
    
    def get_active_pane(self) -> Optional[ContentPane]:
        """Get the currently active pane."""
        if self.active_pane_id:
            node = self.find_node(self.active_pane_id)
            if isinstance(node, ContentPane):
                return node
        
        # Fallback to first pane
        panes = self.get_all_panes()
        if panes:
            self.active_pane_id = panes[0].node_id
            return panes[0]
        
        return None
    
    def set_active_pane(self, pane_id: str) -> bool:
        """Set the active pane by ID."""
        node = self.find_node(pane_id)
        if isinstance(node, ContentPane):
            self.active_pane_id = pane_id
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize complete layout state."""
        return {
            "root": self.root.to_dict(),
            "active_pane_id": self.active_pane_id,
            "version": "1.0"
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LayoutState':
        """Deserialize complete layout state."""
        root_data = data.get("root", {})
        
        if root_data.get("type") == "pane":
            root = ContentPane.from_dict(root_data)
        elif root_data.get("type") == "split":
            root = SplitContainer.from_dict(root_data)
        else:
            # Default fallback
            root = ContentPane()
        
        layout = cls(root)
        layout.active_pane_id = data.get("active_pane_id")
        
        return layout
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'LayoutState':
        """Deserialize from JSON string."""
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            # Return default layout on error
            return cls()