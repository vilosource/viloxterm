#!/usr/bin/env python3
"""
Clean tree-based split pane model.

Data model:
- Leaf: { type: "leaf", widget }
- Split: { type: "split", orientation: "vertical"|"horizontal", ratio∈(0,1), first, second }

Operations:
- Split right/bottom: Creates split node with existing leaf as first, new leaf as second
- Close: Promotes sibling and collapses degenerate splits
"""

from typing import Optional, Union, Literal
import uuid


class TreeNode:
    """Base class for tree nodes."""
    def __init__(self, node_id: Optional[str] = None):
        self.id = node_id or str(uuid.uuid4())[:8]
        self.parent: Optional['SplitNode'] = None


class LeafNode(TreeNode):
    """Leaf node containing a widget."""
    def __init__(self, node_id: Optional[str] = None, widget_type: str = "placeholder", widget_state: Optional[dict] = None):
        super().__init__(node_id)
        self.type: Literal["leaf"] = "leaf"
        self.widget_type = widget_type
        self.widget_state = widget_state or {}
    
    def __repr__(self):
        return f"Leaf({self.id}, {self.widget_type})"


class SplitNode(TreeNode):
    """Split node containing two children."""
    def __init__(self, node_id: Optional[str] = None, orientation: Literal["vertical", "horizontal"] = "vertical", 
                 ratio: float = 0.5, first: Optional[TreeNode] = None, second: Optional[TreeNode] = None):
        super().__init__(node_id)
        self.type: Literal["split"] = "split"
        self.orientation = orientation
        self.ratio = ratio  # first / (first + second)
        self.first = first
        self.second = second
        
        if self.first:
            self.first.parent = self
        if self.second:
            self.second.parent = self
    
    def __repr__(self):
        orient = "V" if self.orientation == "vertical" else "H"
        return f"Split({self.id}, {orient}, {self.ratio:.2f})"


class TreeSplitModel:
    """Tree-based split pane model."""
    
    def __init__(self):
        # Start with a single leaf as root
        self.root: TreeNode = LeafNode()
        self.leaves: dict[str, LeafNode] = {self.root.id: self.root}
        self.active_leaf_id: Optional[str] = self.root.id
    
    def find_leaf(self, leaf_id: str) -> Optional[LeafNode]:
        """Find a leaf node by ID."""
        return self.leaves.get(leaf_id)
    
    def split_right(self, leaf_id: str, new_widget_type: str = "placeholder") -> Optional[str]:
        """Split a leaf to the right (vertical split)."""
        return self._split_leaf(leaf_id, "vertical", new_widget_type)
    
    def split_bottom(self, leaf_id: str, new_widget_type: str = "placeholder") -> Optional[str]:
        """Split a leaf to the bottom (horizontal split)."""
        return self._split_leaf(leaf_id, "horizontal", new_widget_type)
    
    def _split_leaf(self, leaf_id: str, orientation: str, new_widget_type: str) -> Optional[str]:
        """Split a leaf node."""
        leaf = self.find_leaf(leaf_id)
        if not leaf:
            return None
        
        # Create new leaf for the right/bottom
        new_leaf = LeafNode(widget_type=new_widget_type)
        
        # Create split node
        split = SplitNode(
            orientation=orientation,
            ratio=0.5,
            first=leaf,
            second=new_leaf
        )
        
        # Update parent relationships
        if leaf.parent:
            # Leaf has a parent - replace leaf with split in parent
            parent = leaf.parent
            if parent.first == leaf:
                parent.first = split
            elif parent.second == leaf:
                parent.second = split
            split.parent = parent
        else:
            # Leaf is root - split becomes new root
            self.root = split
        
        # Update leaf tracking
        self.leaves[new_leaf.id] = new_leaf
        
        # Make new leaf active
        self.active_leaf_id = new_leaf.id
        
        return new_leaf.id
    
    def close_leaf(self, leaf_id: str) -> bool:
        """Close a leaf node and promote its sibling."""
        leaf = self.find_leaf(leaf_id)
        if not leaf:
            return False
        
        # Case 1: Leaf is root (only pane)
        if leaf == self.root:
            # Replace with fresh placeholder or disallow
            leaf.widget_type = "placeholder"
            leaf.widget_state = {}
            return True
        
        # Case 2: Leaf has parent (normal case)
        parent = leaf.parent
        if not parent:
            return False
        
        # Find sibling
        sibling = parent.second if parent.first == leaf else parent.first
        if not sibling:
            return False
        
        # Promote sibling - replace parent with sibling in grandparent
        grandparent = parent.parent
        
        if grandparent:
            # Parent has a parent - replace parent with sibling
            if grandparent.first == parent:
                grandparent.first = sibling
            elif grandparent.second == parent:
                grandparent.second = sibling
            sibling.parent = grandparent
        else:
            # Parent is root - sibling becomes new root
            self.root = sibling
            sibling.parent = None
        
        # Remove leaf from tracking
        del self.leaves[leaf_id]
        
        # Update active leaf
        if self.active_leaf_id == leaf_id:
            # Find first available leaf
            if self.leaves:
                self.active_leaf_id = next(iter(self.leaves.keys()))
            else:
                self.active_leaf_id = None
        
        return True
    
    def get_tree_structure(self, node: Optional[TreeNode] = None, indent: int = 0) -> str:
        """Get string representation of tree structure."""
        if node is None:
            node = self.root
        
        prefix = "  " * indent
        
        if isinstance(node, LeafNode):
            active = " *" if node.id == self.active_leaf_id else ""
            return f"{prefix}Leaf({node.id}, {node.widget_type}){active}"
        
        elif isinstance(node, SplitNode):
            orient = "V" if node.orientation == "vertical" else "H"
            result = f"{prefix}Split({orient}, {node.ratio:.2f})"
            if node.first:
                result += "\n" + self.get_tree_structure(node.first, indent + 1)
            if node.second:
                result += "\n" + self.get_tree_structure(node.second, indent + 1)
            return result
        
        return ""
    
    def set_active_leaf(self, leaf_id: str) -> bool:
        """Set the active leaf."""
        if leaf_id in self.leaves:
            self.active_leaf_id = leaf_id
            return True
        return False
    
    def get_all_leaf_ids(self) -> list[str]:
        """Get all leaf IDs."""
        return list(self.leaves.keys())
    
    def update_split_ratio(self, split_node: SplitNode, ratio: float):
        """Update the ratio of a split node."""
        split_node.ratio = max(0.1, min(0.9, ratio))  # Clamp between 0.1 and 0.9