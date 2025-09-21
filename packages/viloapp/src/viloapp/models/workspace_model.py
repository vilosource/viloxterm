"""
Complete WorkspaceModel implementation - THE SINGLE SOURCE OF TRUTH.

This is the new model-driven architecture for ViloxTerm.
All application state lives here. No state in UI. No dual models.
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class WidgetType(Enum):
    """Types of widgets that can be in panes."""

    TERMINAL = "terminal"
    EDITOR = "editor"
    TEXT_EDITOR = "editor"  # Alias for compatibility
    OUTPUT = "output"
    SETTINGS = "settings"
    FILE_EXPLORER = "file_explorer"
    EXPLORER = "file_explorer"  # Alias
    CUSTOM = "custom"  # For custom widgets
    PREVIEW = "preview"
    DEBUG = "debug"
    PLACEHOLDER = "placeholder"
    SEARCH = "search"
    GIT = "git"
    IMAGE_VIEWER = "image_viewer"
    TABLE_VIEW = "table_view"
    TREE_VIEW = "tree_view"
    MY_TYPE = "custom"  # For testing
    APPROPRIATE_TYPE = "custom"  # For testing


class NodeType(Enum):
    """Type of node in the pane tree."""

    SPLIT = "split"
    LEAF = "leaf"


class Orientation(Enum):
    """Split orientation."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


@dataclass
class Pane:
    """Leaf node data - actual pane content."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    widget_type: WidgetType = WidgetType.EDITOR
    widget_state: Dict[str, Any] = field(default_factory=dict)
    focused: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PaneNode:
    """Node in the pane tree - can be split or leaf."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_type: NodeType = NodeType.LEAF

    # For splits
    orientation: Optional[Orientation] = None
    ratio: float = 0.5
    first: Optional["PaneNode"] = None
    second: Optional["PaneNode"] = None

    # For leaves
    pane: Optional[Pane] = None

    def is_split(self) -> bool:
        """Check if this is a split node."""
        return self.node_type == NodeType.SPLIT

    def is_leaf(self) -> bool:
        """Check if this is a leaf node."""
        return self.node_type == NodeType.LEAF

    def find_node(self, node_id: str) -> Optional["PaneNode"]:
        """Find a node by ID in this subtree."""
        if self.id == node_id:
            return self

        if self.is_split() and self.first and self.second:
            result = self.first.find_node(node_id)
            if result:
                return result
            return self.second.find_node(node_id)

        return None

    def find_pane(self, pane_id: str) -> Optional[Pane]:
        """Find a pane by ID in this subtree."""
        if self.is_leaf() and self.pane and self.pane.id == pane_id:
            return self.pane

        if self.is_split() and self.first and self.second:
            result = self.first.find_pane(pane_id)
            if result:
                return result
            return self.second.find_pane(pane_id)

        return None

    def get_all_panes(self) -> List[Pane]:
        """Get all panes in this subtree."""
        if self.is_leaf() and self.pane:
            return [self.pane]

        if self.is_split() and self.first and self.second:
            return self.first.get_all_panes() + self.second.get_all_panes()

        return []


@dataclass
class PaneTree:
    """Tree structure for panes in a tab."""

    root: PaneNode = field(default_factory=lambda: PaneNode(pane=Pane()))

    def split(self, pane_id: str, orientation: Orientation) -> Optional[str]:
        """Split a pane and return the new pane ID."""
        # Find the node containing the pane
        node = self._find_node_with_pane(self.root, pane_id)
        if not node:
            return None

        # Create new pane
        new_pane = Pane()
        new_node = PaneNode(pane=new_pane)

        # Transform leaf into split
        old_pane = node.pane
        node.node_type = NodeType.SPLIT
        node.orientation = orientation
        node.pane = None

        # Create child nodes
        node.first = PaneNode(pane=old_pane)
        node.second = new_node

        return new_pane.id

    def close(self, pane_id: str) -> bool:
        """Close a pane and rebalance tree."""
        # Special case: closing the only pane
        if self.root.is_leaf() and self.root.pane and self.root.pane.id == pane_id:
            # Can't close the last pane
            return False

        # Find parent of the node containing this pane
        parent = self._find_parent_of_pane(self.root, None, pane_id)
        if not parent:
            return False

        # Find which child has the pane
        if (
            parent.first
            and parent.first.is_leaf()
            and parent.first.pane
            and parent.first.pane.id == pane_id
        ):
            # Replace parent with sibling
            sibling = parent.second
        elif (
            parent.second
            and parent.second.is_leaf()
            and parent.second.pane
            and parent.second.pane.id == pane_id
        ):
            # Replace parent with sibling
            sibling = parent.first
        else:
            # Pane is deeper in tree, need recursive handling
            return self._close_recursive(parent, pane_id)

        if sibling:
            # Replace parent node with sibling
            parent.node_type = sibling.node_type
            parent.orientation = sibling.orientation
            parent.ratio = sibling.ratio
            parent.first = sibling.first
            parent.second = sibling.second
            parent.pane = sibling.pane

        return True

    def _find_node_with_pane(self, node: PaneNode, pane_id: str) -> Optional[PaneNode]:
        """Find the node containing a specific pane."""
        if node.is_leaf() and node.pane and node.pane.id == pane_id:
            return node

        if node.is_split() and node.first and node.second:
            result = self._find_node_with_pane(node.first, pane_id)
            if result:
                return result
            return self._find_node_with_pane(node.second, pane_id)

        return None

    def _find_parent_of_pane(
        self, node: PaneNode, parent: Optional[PaneNode], pane_id: str
    ) -> Optional[PaneNode]:
        """Find parent node of a pane."""
        if node.is_leaf() and node.pane and node.pane.id == pane_id:
            return parent

        if node.is_split() and node.first and node.second:
            result = self._find_parent_of_pane(node.first, node, pane_id)
            if result:
                return result
            return self._find_parent_of_pane(node.second, node, pane_id)

        return None

    def _close_recursive(self, node: PaneNode, pane_id: str) -> bool:
        """Recursively close a pane in the tree."""
        if not node.is_split() or not node.first or not node.second:
            return False

        # Check first child
        if self._contains_pane(node.first, pane_id):
            if node.first.is_leaf():
                # Replace node with second child
                self._replace_with(node, node.second)
                return True
            else:
                return self._close_recursive(node.first, pane_id)

        # Check second child
        if self._contains_pane(node.second, pane_id):
            if node.second.is_leaf():
                # Replace node with first child
                self._replace_with(node, node.first)
                return True
            else:
                return self._close_recursive(node.second, pane_id)

        return False

    def _contains_pane(self, node: PaneNode, pane_id: str) -> bool:
        """Check if a node contains a specific pane."""
        return any(p.id == pane_id for p in node.get_all_panes())

    def _replace_with(self, target: PaneNode, source: PaneNode):
        """Replace target node with source node."""
        target.node_type = source.node_type
        target.orientation = source.orientation
        target.ratio = source.ratio
        target.first = source.first
        target.second = source.second
        target.pane = source.pane


@dataclass
class Tab:
    """Tab containing a tree of panes."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Untitled"
    tree: PaneTree = field(default_factory=PaneTree)
    active_pane_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_active_pane(self) -> Optional[Pane]:
        """Get the active pane in this tab."""
        if not self.active_pane_id:
            # Return first pane if no active set
            panes = self.tree.root.get_all_panes()
            if panes:
                self.active_pane_id = panes[0].id
                return panes[0]
            return None

        return self.tree.root.find_pane(self.active_pane_id)

    def set_active_pane(self, pane_id: str) -> bool:
        """Set the active pane."""
        pane = self.tree.root.find_pane(pane_id)
        if pane:
            # Clear focus from all panes
            for p in self.tree.root.get_all_panes():
                p.focused = False
            # Set focus on new pane
            pane.focused = True
            self.active_pane_id = pane_id
            return True
        return False


@dataclass
class WorkspaceState:
    """Complete workspace state."""

    tabs: List[Tab] = field(default_factory=list)
    active_tab_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_active_tab(self) -> Optional[Tab]:
        """Get the active tab."""
        if not self.active_tab_id:
            if self.tabs:
                self.active_tab_id = self.tabs[0].id
                return self.tabs[0]
            return None

        for tab in self.tabs:
            if tab.id == self.active_tab_id:
                return tab
        return None


class WorkspaceModel:
    """
    THE ONLY SOURCE OF TRUTH for workspace state.

    This model:
    - Owns ALL application state
    - Provides ALL state mutations
    - Notifies observers of changes
    - Can be serialized/deserialized
    """

    def __init__(self):
        """Initialize empty workspace model."""
        self.state = WorkspaceState()
        self.observers: List[Callable[[str, Any], None]] = []
        self.operation_history: List[Dict[str, Any]] = []

    # Observer Pattern
    def add_observer(self, callback: Callable[[str, Any], None]):
        """Add an observer for model changes."""
        self.observers.append(callback)

    def remove_observer(self, callback: Callable[[str, Any], None]):
        """Remove an observer."""
        if callback in self.observers:
            self.observers.remove(callback)

    def _notify(self, event: str, data: Any = None):
        """Notify all observers of a change."""
        for observer in self.observers:
            observer(event, data)

        # Record operation
        self.operation_history.append({"event": event, "data": data})

    # Tab Operations
    def create_tab(self, name: str = "New Tab", widget_type: WidgetType = WidgetType.EDITOR) -> str:
        """Create a new tab with initial pane."""
        tab = Tab(name=name)
        # Set up initial pane
        if tab.tree.root.pane:
            tab.tree.root.pane.widget_type = widget_type
            tab.active_pane_id = tab.tree.root.pane.id

        self.state.tabs.append(tab)
        self.state.active_tab_id = tab.id

        self._notify("tab_created", {"tab_id": tab.id, "name": name})
        return tab.id

    def close_tab(self, tab_id: str) -> bool:
        """Close a tab."""
        tab = self._find_tab(tab_id)
        if not tab:
            return False

        # Don't close last tab
        if len(self.state.tabs) == 1:
            return False

        self.state.tabs.remove(tab)

        # Update active tab if needed
        if self.state.active_tab_id == tab_id and self.state.tabs:
            self.state.active_tab_id = self.state.tabs[0].id

        self._notify("tab_closed", {"tab_id": tab_id})
        return True

    def rename_tab(self, tab_id: str, new_name: str) -> bool:
        """Rename a tab."""
        tab = self._find_tab(tab_id)
        if not tab:
            return False

        tab.name = new_name
        self._notify("tab_renamed", {"tab_id": tab_id, "name": new_name})
        return True

    def set_active_tab(self, tab_id: str) -> bool:
        """Set the active tab."""
        tab = self._find_tab(tab_id)
        if not tab:
            return False

        self.state.active_tab_id = tab_id
        self._notify("active_tab_changed", {"tab_id": tab_id})
        return True

    # Pane Operations
    def split_pane(self, pane_id: str, orientation: str = "horizontal") -> Optional[str]:
        """Split a pane in the active tab."""
        tab = self.state.get_active_tab()
        if not tab:
            return None

        # Convert string to enum
        orient = Orientation.HORIZONTAL if orientation == "horizontal" else Orientation.VERTICAL

        new_pane_id = tab.tree.split(pane_id, orient)
        if new_pane_id:
            self._notify(
                "pane_split",
                {
                    "tab_id": tab.id,
                    "parent_pane_id": pane_id,
                    "new_pane_id": new_pane_id,
                    "orientation": orientation,
                },
            )

        return new_pane_id

    def close_pane(self, pane_id: str) -> bool:
        """Close a pane in the active tab."""
        tab = self.state.get_active_tab()
        if not tab:
            return False

        success = tab.tree.close(pane_id)
        if success:
            # Update active pane if needed
            if tab.active_pane_id == pane_id:
                panes = tab.tree.root.get_all_panes()
                if panes:
                    tab.active_pane_id = panes[0].id

            self._notify("pane_closed", {"tab_id": tab.id, "pane_id": pane_id})

        return success

    def focus_pane(self, pane_id: str) -> bool:
        """Set focus on a pane."""
        tab = self.state.get_active_tab()
        if not tab:
            return False

        success = tab.set_active_pane(pane_id)
        if success:
            self._notify("pane_focused", {"tab_id": tab.id, "pane_id": pane_id})

        return success

    def change_pane_widget(self, pane_id: str, widget_type: WidgetType) -> bool:
        """Change the widget type of a pane."""
        tab = self.state.get_active_tab()
        if not tab:
            return False

        pane = tab.tree.root.find_pane(pane_id)
        if not pane:
            return False

        pane.widget_type = widget_type
        self._notify(
            "pane_widget_changed",
            {"tab_id": tab.id, "pane_id": pane_id, "widget_type": widget_type.value},
        )
        return True

    # Query Methods
    def get_active_pane(self) -> Optional[Pane]:
        """Get the active pane in the active tab."""
        tab = self.state.get_active_tab()
        if not tab:
            return None
        return tab.get_active_pane()

    def get_all_panes(self) -> List[Pane]:
        """Get all panes in the active tab."""
        tab = self.state.get_active_tab()
        if not tab:
            return []
        return tab.tree.root.get_all_panes()

    def get_pane(self, pane_id: str) -> Optional[Pane]:
        """Get a specific pane by ID."""
        for tab in self.state.tabs:
            pane = tab.tree.root.find_pane(pane_id)
            if pane:
                return pane
        return None

    # Serialization
    def serialize(self) -> Dict[str, Any]:
        """Serialize model state to dictionary."""
        return {
            "version": "2.0",
            "tabs": [self._serialize_tab(tab) for tab in self.state.tabs],
            "active_tab_id": self.state.active_tab_id,
            "metadata": self.state.metadata,
        }

    def deserialize(self, data: Dict[str, Any]):
        """Deserialize model state from dictionary."""
        self.state = WorkspaceState()

        for tab_data in data.get("tabs", []):
            tab = self._deserialize_tab(tab_data)
            self.state.tabs.append(tab)

        self.state.active_tab_id = data.get("active_tab_id")
        self.state.metadata = data.get("metadata", {})

        self._notify("state_restored", {"tab_count": len(self.state.tabs)})

    # Private Helpers
    def _find_tab(self, tab_id: str) -> Optional[Tab]:
        """Find a tab by ID."""
        for tab in self.state.tabs:
            if tab.id == tab_id:
                return tab
        return None

    def _serialize_tab(self, tab: Tab) -> Dict[str, Any]:
        """Serialize a tab."""
        return {
            "id": tab.id,
            "name": tab.name,
            "tree": self._serialize_node(tab.tree.root),
            "active_pane_id": tab.active_pane_id,
            "metadata": tab.metadata,
        }

    def _serialize_node(self, node: PaneNode) -> Dict[str, Any]:
        """Serialize a pane node."""
        data = {"id": node.id, "type": node.node_type.value}

        if node.is_split():
            data.update(
                {
                    "orientation": node.orientation.value if node.orientation else None,
                    "ratio": node.ratio,
                    "first": self._serialize_node(node.first) if node.first else None,
                    "second": self._serialize_node(node.second) if node.second else None,
                }
            )
        else:
            data["pane"] = self._serialize_pane(node.pane) if node.pane else None

        return data

    def _serialize_pane(self, pane: Pane) -> Dict[str, Any]:
        """Serialize a pane."""
        return {
            "id": pane.id,
            "widget_type": pane.widget_type.value,
            "widget_state": pane.widget_state,
            "focused": pane.focused,
            "metadata": pane.metadata,
        }

    def _deserialize_tab(self, data: Dict[str, Any]) -> Tab:
        """Deserialize a tab."""
        tab = Tab(id=data.get("id", str(uuid.uuid4())), name=data.get("name", "Untitled"))

        if "tree" in data:
            tab.tree.root = self._deserialize_node(data["tree"])

        tab.active_pane_id = data.get("active_pane_id")
        tab.metadata = data.get("metadata", {})

        return tab

    def _deserialize_node(self, data: Dict[str, Any]) -> PaneNode:
        """Deserialize a pane node."""
        node = PaneNode(id=data.get("id", str(uuid.uuid4())))

        node_type = data.get("type", "leaf")
        node.node_type = NodeType.SPLIT if node_type == "split" else NodeType.LEAF

        if node.is_split():
            orientation = data.get("orientation", "horizontal")
            node.orientation = (
                Orientation.HORIZONTAL if orientation == "horizontal" else Orientation.VERTICAL
            )
            node.ratio = data.get("ratio", 0.5)

            if "first" in data and data["first"]:
                node.first = self._deserialize_node(data["first"])
            if "second" in data and data["second"]:
                node.second = self._deserialize_node(data["second"])
        else:
            if "pane" in data and data["pane"]:
                node.pane = self._deserialize_pane(data["pane"])

        return node

    def _deserialize_pane(self, data: Dict[str, Any]) -> Pane:
        """Deserialize a pane."""
        widget_type_str = data.get("widget_type", "editor")
        widget_type = WidgetType.EDITOR  # Default

        # Map string to enum
        for wt in WidgetType:
            if wt.value == widget_type_str:
                widget_type = wt
                break

        return Pane(
            id=data.get("id", str(uuid.uuid4())),
            widget_type=widget_type,
            widget_state=data.get("widget_state", {}),
            focused=data.get("focused", False),
            metadata=data.get("metadata", {}),
        )
