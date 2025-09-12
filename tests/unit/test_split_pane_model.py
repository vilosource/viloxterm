"""Unit tests for the split pane model (tree structure)."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import Qt
from ui.widgets.split_pane_model import SplitPaneModel, LeafNode, SplitNode


@pytest.mark.unit
class TestLeafNode:
    """Test cases for LeafNode class."""

    def test_pane_node_creation(self):
        """Test creating a pane node."""
        node = LeafNode()
        
        assert node.id is not None
        assert node.type == "leaf"
        assert node.parent is None
        assert hasattr(node, 'app_widget')

    def test_pane_node_unique_ids(self):
        """Test that pane nodes have unique IDs."""
        node1 = LeafNode()
        node2 = LeafNode()
        
        assert node1.id != node2.id

    def test_pane_node_parent_relationship(self):
        """Test parent-child relationship for pane nodes."""
        parent = SplitNode(orientation="horizontal")
        child = LeafNode()
        
        parent.first = child
        child.parent = parent
        
        assert child.parent == parent
        assert parent.first == child

    def test_pane_node_is_leaf(self):
        """Test that pane nodes are leaf nodes."""
        node = LeafNode()
        
        assert node.type == "leaf"
        assert not hasattr(node, 'first') or node.first is None
        assert not hasattr(node, 'second') or node.second is None


@pytest.mark.unit
class TestSplitNode:
    """Test cases for SplitNode class."""

    def test_split_node_creation(self):
        """Test creating a split node."""
        node = SplitNode(orientation="horizontal")
        
        assert node.id is not None
        assert node.type == "split"
        assert node.orientation == "horizontal"
        assert node.parent is None
        assert node.first is None
        assert node.second is None

    def test_split_node_add_child(self):
        """Test adding children to split node."""
        split = SplitNode(orientation="vertical")
        pane1 = LeafNode()
        pane2 = LeafNode()
        
        split.first = pane1
        split.second = pane2
        pane1.parent = split
        pane2.parent = split
        
        assert split.first == pane1
        assert split.second == pane2
        assert pane1.parent == split
        assert pane2.parent == split

    def test_split_node_remove_child(self):
        """Test removing children from split node."""
        split = SplitNode(orientation="horizontal")
        pane1 = LeafNode()
        pane2 = LeafNode()
        
        split.first = pane1
        split.second = pane2
        pane1.parent = split
        pane2.parent = split
        
        # Remove first child
        split.first = None
        pane1.parent = None
        
        assert split.first is None
        assert split.second == pane2
        assert pane1.parent is None
        assert pane2.parent == split

    def test_split_node_is_not_leaf(self):
        """Test that split nodes are not leaf nodes."""
        node = SplitNode(orientation="horizontal")
        node.first = LeafNode()
        
        assert node.type == "split"

    def test_split_node_orientation(self):
        """Test split node orientation."""
        h_split = SplitNode(orientation="horizontal")
        v_split = SplitNode(orientation="vertical")
        
        assert h_split.orientation == "horizontal"
        assert v_split.orientation == "vertical"


@pytest.mark.unit
class TestSplitPaneModel:
    """Test cases for SplitPaneModel class."""

    def test_model_initialization(self, qtbot):
        """Test model initializes with root pane."""
        model = SplitPaneModel()
        
        assert model.root is not None
        assert isinstance(model.root, LeafNode)
        assert model.root.type == "leaf"

    def test_split_horizontal(self, qtbot):
        """Test horizontal splitting in model."""
        model = SplitPaneModel()
        original_root_id = model.root.id
        
        # Split the root horizontally
        new_pane_id = model.split_pane(original_root_id, "horizontal")
        
        # Check structure
        assert new_pane_id is not None
        assert isinstance(model.root, SplitNode)
        assert model.root.orientation == "horizontal"
        assert model.root.first is not None
        assert model.root.second is not None

    def test_split_vertical(self, qtbot):
        """Test vertical splitting in model."""
        model = SplitPaneModel()
        original_root_id = model.root.id
        
        # Split the root vertically
        new_pane_id = model.split_pane(original_root_id, "vertical")
        
        # Check structure
        assert new_pane_id is not None
        assert isinstance(model.root, SplitNode)
        assert model.root.orientation == "vertical"
        assert model.root.first is not None
        assert model.root.second is not None

    def test_multiple_splits(self, qtbot):
        """Test multiple split operations."""
        model = SplitPaneModel()
        
        # First split
        pane1_id = model.root.id
        pane2_id = model.split_pane(pane1_id, "horizontal")
        
        # Second split
        pane3_id = model.split_pane(pane2_id, "vertical")
        
        # Check structure
        assert isinstance(model.root, SplitNode)
        assert model.root.orientation == "horizontal"
        
        # First child should be original pane
        assert model.root.first.id == pane1_id
        
        # Second child should be a vertical split
        second_child = model.root.second
        assert isinstance(second_child, SplitNode)
        assert second_child.orientation == "vertical"
        assert second_child.first.id == pane2_id
        assert second_child.second.id == pane3_id

    def test_remove_node(self, qtbot):
        """Test removing nodes from model."""
        model = SplitPaneModel()
        
        # Create structure: horizontal split with two panes
        pane1_id = model.root.id
        pane2_id = model.split_pane(pane1_id, "horizontal")
        
        # Remove pane2
        model.close_pane(pane2_id)
        
        # Root should revert to single pane
        assert model.root.id == pane1_id
        assert isinstance(model.root, LeafNode)

    def test_remove_node_complex_structure(self, qtbot):
        """Test removing node from complex structure."""
        model = SplitPaneModel()
        
        # Create structure
        pane1_id = model.root.id
        pane2_id = model.split_pane(pane1_id, "horizontal")
        pane3_id = model.split_pane(pane2_id, "vertical")
        
        # Remove pane3
        model.close_pane(pane3_id)
        
        # Should simplify structure
        assert isinstance(model.root, SplitNode)
        assert model.root.orientation == "horizontal"
        assert model.root.first.id == pane1_id
        assert model.root.second.id == pane2_id

    def test_find_node(self, qtbot):
        """Test finding nodes by ID."""
        model = SplitPaneModel()
        
        pane1_id = model.root.id
        pane2_id = model.split_pane(pane1_id, "horizontal")
        pane3_id = model.split_pane(pane2_id, "vertical")
        
        # Find each node
        assert model.find_node(pane1_id).id == pane1_id
        assert model.find_node(pane2_id).id == pane2_id
        assert model.find_node(pane3_id).id == pane3_id
        
        # Non-existent node
        assert model.find_node("non-existent") is None

    def test_get_all_panes(self, qtbot):
        """Test getting all pane nodes."""
        model = SplitPaneModel()
        
        pane1_id = model.root.id
        pane2_id = model.split_pane(pane1_id, "horizontal")
        pane3_id = model.split_pane(pane2_id, "vertical")
        pane4_id = model.split_pane(pane1_id, "vertical")
        
        all_leaves = list(model.leaves.values())
        
        # Should have 4 panes
        assert len(all_leaves) == 4
        
        # Check all IDs are present
        all_ids = [leaf.id for leaf in all_leaves]
        assert pane1_id in all_ids
        assert pane2_id in all_ids
        assert pane3_id in all_ids
        assert pane4_id in all_ids
        
        # All should be LeafNodes
        assert all(isinstance(p, LeafNode) for p in all_leaves)

    def test_cannot_remove_last_pane(self, qtbot):
        """Test that the last pane cannot be removed."""
        model = SplitPaneModel()
        
        # Try to remove the only pane
        result = model.close_pane(model.root.id)
        
        # Should not be removed
        assert result == False
        assert model.root is not None
        assert isinstance(model.root, LeafNode)

    def test_split_maintains_parent_references(self, qtbot):
        """Test that splitting maintains correct parent references."""
        model = SplitPaneModel()
        
        pane1_id = model.root.id
        pane2_id = model.split_pane(pane1_id, "horizontal")
        
        # Check parent references
        assert model.root.parent is None
        pane1 = model.find_leaf(pane1_id)
        pane2 = model.find_leaf(pane2_id)
        assert pane1.parent == model.root
        assert pane2.parent == model.root

    def test_tree_traversal(self, qtbot):
        """Test tree traversal methods."""
        model = SplitPaneModel()
        
        # Build a tree
        pane1_id = model.root.id
        pane2_id = model.split_pane(pane1_id, "horizontal")
        pane3_id = model.split_pane(pane2_id, "vertical")
        
        # Get all leaf nodes using traverse_tree (it only returns leaves)
        all_leaves = list(model.traverse_tree())
        
        # Should have 3 leaf nodes after two splits
        assert len(all_leaves) == 3
        
        # All returned nodes should be leaves
        assert all(isinstance(n, LeafNode) for n in all_leaves)
        assert all(n.type == "leaf" for n in all_leaves)