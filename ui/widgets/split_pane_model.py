#!/usr/bin/env python3
"""
Pure model for split pane - no widget references, just data structure.
This maintains clean separation of concerns.
"""

import uuid
from typing import Optional, Dict, Union, Any
from dataclasses import dataclass, field
from ui.widgets.widget_registry import WidgetType


@dataclass
class LeafNode:
    """Leaf node containing widget metadata - no actual widget references."""
    type: str = "leaf"
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    widget_type: WidgetType = WidgetType.PLACEHOLDER
    widget_state: dict = field(default_factory=dict)
    parent: Optional['SplitNode'] = None
    # NO widget reference here - that belongs in the view


@dataclass  
class SplitNode:
    """Split node containing two children - pure data, no widget references."""
    type: str = "split"
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    orientation: str = "horizontal"  # "horizontal" or "vertical"
    ratio: float = 0.5
    first: Optional[Union[LeafNode, 'SplitNode']] = None
    second: Optional[Union[LeafNode, 'SplitNode']] = None
    parent: Optional['SplitNode'] = None
    # NO splitter reference here - that belongs in the view


class SplitPaneModel:
    """
    Pure model for split pane tree structure.
    Manages the tree and active pane state without any view dependencies.
    """
    
    def __init__(self, initial_widget_type: WidgetType = WidgetType.PLACEHOLDER):
        """Initialize with a single root leaf."""
        self.root = LeafNode(widget_type=initial_widget_type)
        self.leaves: Dict[str, LeafNode] = {self.root.id: self.root}
        self.active_pane_id: str = self.root.id  # Active pane is MODEL state
    
    def split_pane(self, pane_id: str, orientation: str) -> Optional[str]:
        """
        Split a pane in the model.
        Returns the ID of the new pane or None if split failed.
        """
        leaf = self.leaves.get(pane_id)
        if not leaf:
            return None
        
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
        
        # Keep focus on the original pane (not the new one)
        # This is important - the active pane doesn't change on split
        # self.active_pane_id remains the same
        
        return new_leaf.id
    
    def close_pane(self, pane_id: str) -> bool:
        """
        Close a pane in the model.
        Returns True if successful.
        """
        leaf = self.leaves.get(pane_id)
        if not leaf:
            return False
        
        # Don't close the last pane
        if leaf == self.root:
            return False
        
        parent = leaf.parent
        if not parent:
            return False
        
        # Find sibling
        sibling = parent.second if parent.first == leaf else parent.first
        if not sibling:
            return False
        
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
        
        return True
    
    def set_active_pane(self, pane_id: str) -> bool:
        """Set the active pane if it exists."""
        if pane_id in self.leaves:
            self.active_pane_id = pane_id
            return True
        return False
    
    def get_active_pane_id(self) -> str:
        """Get the currently active pane ID."""
        return self.active_pane_id
    
    def change_pane_type(self, pane_id: str, new_type: WidgetType) -> bool:
        """Change the widget type of a pane."""
        leaf = self.leaves.get(pane_id)
        if leaf:
            leaf.widget_type = new_type
            return True
        return False
    
    def update_split_ratio(self, split_node: SplitNode, ratio: float):
        """Update the split ratio for a split node."""
        split_node.ratio = max(0.1, min(0.9, ratio))  # Clamp between 10% and 90%
    
    def to_dict(self) -> dict:
        """Serialize model to dictionary."""
        def node_to_dict(node):
            if isinstance(node, LeafNode):
                return {
                    "type": "leaf",
                    "id": node.id,
                    "widget_type": node.widget_type.value,
                    "widget_state": node.widget_state
                }
            elif isinstance(node, SplitNode):
                return {
                    "type": "split",
                    "orientation": node.orientation,
                    "ratio": node.ratio,
                    "first": node_to_dict(node.first) if node.first else None,
                    "second": node_to_dict(node.second) if node.second else None
                }
            return None
        
        return {
            "root": node_to_dict(self.root),
            "active_pane_id": self.active_pane_id
        }
    
    def from_dict(self, data: dict):
        """Restore model from dictionary."""
        def dict_to_node(node_dict, parent=None):
            if not node_dict:
                return None
                
            if node_dict["type"] == "leaf":
                leaf = LeafNode(
                    id=node_dict["id"],
                    widget_type=WidgetType(node_dict["widget_type"]),
                    widget_state=node_dict.get("widget_state", {}),
                    parent=parent
                )
                self.leaves[leaf.id] = leaf
                return leaf
            elif node_dict["type"] == "split":
                split = SplitNode(
                    orientation=node_dict["orientation"],
                    ratio=node_dict["ratio"],
                    parent=parent
                )
                split.first = dict_to_node(node_dict.get("first"), split)
                split.second = dict_to_node(node_dict.get("second"), split)
                return split
            return None
        
        self.leaves.clear()
        self.root = dict_to_node(data["root"])
        self.active_pane_id = data.get("active_pane_id", "")
        
        # Validate active pane
        if self.active_pane_id not in self.leaves and self.leaves:
            self.active_pane_id = next(iter(self.leaves.keys()))