"""Unit tests for split tree manager."""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtCore import Qt
from ui.widgets.split_tree import SplitTreeManager
from models.layout_state import LayoutState, ContentPane, SplitContainer, TabInfo


@pytest.mark.unit
class TestSplitTreeManager:
    """Test cases for SplitTreeManager class."""

    def test_manager_initialization(self):
        """Test SplitTreeManager initialization."""
        manager = SplitTreeManager()
        
        assert isinstance(manager.layout, LayoutState)
        assert isinstance(manager.layout.root, ContentPane)
        assert manager.get_active_pane_id() is not None
        
    def test_manager_with_custom_layout(self):
        """Test SplitTreeManager with custom layout."""
        custom_layout = LayoutState()
        manager = SplitTreeManager(custom_layout)
        
        assert manager.layout == custom_layout
        
    def test_get_all_pane_ids(self):
        """Test getting all pane IDs."""
        manager = SplitTreeManager()
        pane_ids = manager.get_all_pane_ids()
        
        assert len(pane_ids) == 1
        assert isinstance(pane_ids[0], str)
        
    def test_split_pane_horizontal(self):
        """Test splitting a pane horizontally."""
        manager = SplitTreeManager()
        original_pane_id = manager.get_active_pane_id()
        
        # Mock widget creation to avoid Qt dependencies
        with patch.object(manager, '_rebuild_widget_tree') as mock_rebuild:
            new_pane_id = manager.split_pane(original_pane_id, Qt.Horizontal)
        
        assert new_pane_id is not None
        assert new_pane_id != original_pane_id
        
        # Check that we now have 2 panes
        pane_ids = manager.get_all_pane_ids()
        assert len(pane_ids) == 2
        assert original_pane_id in pane_ids
        assert new_pane_id in pane_ids
        
        # Check structure
        assert isinstance(manager.layout.root, SplitContainer)
        assert manager.layout.root.orientation == Qt.Horizontal
        assert len(manager.layout.root.children) == 2
        
        # Verify widget tree rebuild was called
        mock_rebuild.assert_called_once()
        
    def test_split_pane_vertical(self):
        """Test splitting a pane vertically."""
        manager = SplitTreeManager()
        original_pane_id = manager.get_active_pane_id()
        
        with patch.object(manager, '_rebuild_widget_tree') as mock_rebuild:
            new_pane_id = manager.split_pane(original_pane_id, Qt.Vertical)
        
        assert new_pane_id is not None
        
        # Check structure
        assert isinstance(manager.layout.root, SplitContainer)
        assert manager.layout.root.orientation == Qt.Vertical
        
        mock_rebuild.assert_called_once()
        
    def test_split_nonexistent_pane(self):
        """Test splitting a non-existent pane."""
        manager = SplitTreeManager()
        
        result = manager.split_pane("nonexistent-id", Qt.Horizontal)
        
        assert result is None
        
    def test_close_pane(self):
        """Test closing a pane."""
        manager = SplitTreeManager()
        original_pane_id = manager.get_active_pane_id()
        
        # First split to have multiple panes
        with patch.object(manager, '_rebuild_widget_tree'):
            new_pane_id = manager.split_pane(original_pane_id, Qt.Horizontal)
        
        # Now close one pane
        with patch.object(manager, '_rebuild_widget_tree') as mock_rebuild:
            success = manager.close_pane(new_pane_id)
        
        assert success
        
        # Should be back to single pane
        pane_ids = manager.get_all_pane_ids()
        assert len(pane_ids) == 1
        assert original_pane_id in pane_ids
        assert new_pane_id not in pane_ids
        
        mock_rebuild.assert_called_once()
        
    def test_close_last_pane(self):
        """Test that closing the last pane fails."""
        manager = SplitTreeManager()
        pane_id = manager.get_active_pane_id()
        
        success = manager.close_pane(pane_id)
        
        assert not success
        assert len(manager.get_all_pane_ids()) == 1
        
    def test_close_nonexistent_pane(self):
        """Test closing a non-existent pane."""
        manager = SplitTreeManager()
        
        success = manager.close_pane("nonexistent-id")
        
        assert not success
        
    def test_set_active_pane(self):
        """Test setting the active pane."""
        manager = SplitTreeManager()
        original_pane_id = manager.get_active_pane_id()
        
        # Split to get another pane
        with patch.object(manager, '_rebuild_widget_tree'):
            new_pane_id = manager.split_pane(original_pane_id, Qt.Horizontal)
        
        # Set new pane as active
        success = manager.set_active_pane(new_pane_id)
        
        assert success
        assert manager.get_active_pane_id() == new_pane_id
        
    def test_set_active_pane_invalid(self):
        """Test setting invalid pane as active."""
        manager = SplitTreeManager()
        
        success = manager.set_active_pane("nonexistent-id")
        
        assert not success
        
    def test_add_tab(self):
        """Test adding a tab to a pane."""
        manager = SplitTreeManager()
        pane_id = manager.get_active_pane_id()
        
        tab_info = TabInfo(title="Test Tab")
        success = manager.add_tab(pane_id, tab_info)
        
        assert success
        
        # Check that tab was added to the pane
        pane = manager.layout.find_node(pane_id)
        assert isinstance(pane, ContentPane)
        assert len(pane.tabs) == 2  # Original + new tab
        assert any(tab.title == "Test Tab" for tab in pane.tabs)
        
    def test_add_tab_invalid_pane(self):
        """Test adding tab to invalid pane."""
        manager = SplitTreeManager()
        
        tab_info = TabInfo(title="Test Tab")
        success = manager.add_tab("nonexistent-id", tab_info)
        
        assert not success
        
    def test_remove_tab(self):
        """Test removing a tab from a pane."""
        manager = SplitTreeManager()
        pane_id = manager.get_active_pane_id()
        
        # Add a tab first
        tab_info = TabInfo(title="Test Tab")
        manager.add_tab(pane_id, tab_info)
        
        # Remove the second tab (index 1)
        removed_tab = manager.remove_tab(pane_id, 1)
        
        assert removed_tab is not None
        assert removed_tab.title == "Test Tab"
        
        # Check that tab was removed
        pane = manager.layout.find_node(pane_id)
        assert len(pane.tabs) == 1
        
    def test_remove_tab_invalid_pane(self):
        """Test removing tab from invalid pane."""
        manager = SplitTreeManager()
        
        removed_tab = manager.remove_tab("nonexistent-id", 0)
        
        assert removed_tab is None
        
    def test_move_tab(self):
        """Test moving a tab between panes."""
        manager = SplitTreeManager()
        pane1_id = manager.get_active_pane_id()
        
        # Split to get second pane
        with patch.object(manager, '_rebuild_widget_tree'):
            pane2_id = manager.split_pane(pane1_id, Qt.Horizontal)
        
        # Add a tab to first pane
        tab_info = TabInfo(title="Test Tab")
        manager.add_tab(pane1_id, tab_info)
        
        # Move tab from pane1 to pane2
        success = manager.move_tab(tab_info.tab_id, pane1_id, pane2_id)
        
        assert success
        
        # Check that tab moved
        pane1 = manager.layout.find_node(pane1_id)
        pane2 = manager.layout.find_node(pane2_id)
        
        # pane1 should have 1 tab (original), pane2 should have 2 (original + moved)
        assert len(pane1.tabs) == 1
        assert len(pane2.tabs) == 2
        assert any(tab.title == "Test Tab" for tab in pane2.tabs)
        
    def test_move_tab_invalid_panes(self):
        """Test moving tab with invalid panes."""
        manager = SplitTreeManager()
        
        success = manager.move_tab("tab-id", "invalid1", "invalid2")
        
        assert not success
        
    def test_resize_split(self):
        """Test resizing splits in a container."""
        manager = SplitTreeManager()
        pane_id = manager.get_active_pane_id()
        
        # Split to create container
        with patch.object(manager, '_rebuild_widget_tree'):
            manager.split_pane(pane_id, Qt.Horizontal)
        
        # Get the container ID (root)
        container_id = manager.layout.root.node_id
        
        # Resize with custom sizes
        success = manager.resize_split(container_id, [0.7, 0.3])
        
        assert success
        
        # Check that sizes were set
        container = manager.layout.root
        assert abs(container.sizes[0] - 0.7) < 0.001
        assert abs(container.sizes[1] - 0.3) < 0.001
        
    def test_resize_split_invalid(self):
        """Test resizing invalid container."""
        manager = SplitTreeManager()
        
        success = manager.resize_split("invalid-id", [0.5, 0.5])
        
        assert not success
        
    def test_serialize_state(self):
        """Test serializing manager state."""
        manager = SplitTreeManager()
        
        state_data = manager.serialize_state()
        
        assert isinstance(state_data, dict)
        assert "root" in state_data
        assert "active_pane_id" in state_data
        
    def test_deserialize_state(self):
        """Test deserializing manager state."""
        # Create a manager with some splits
        manager1 = SplitTreeManager()
        pane_id = manager1.get_active_pane_id()
        
        with patch.object(manager1, '_rebuild_widget_tree'):
            manager1.split_pane(pane_id, Qt.Horizontal)
        
        # Serialize state
        state_data = manager1.serialize_state()
        
        # Create new manager and deserialize
        manager2 = SplitTreeManager()
        
        # Mock both set_layout_state and _rebuild_widget_tree 
        with patch.object(manager2, '_rebuild_widget_tree'), \
             patch.object(manager2, '_create_widget_tree', return_value=None):
            success = manager2.deserialize_state(state_data)
        
        assert success
        assert len(manager2.get_all_pane_ids()) == 2
        
    def test_deserialize_invalid_state(self):
        """Test deserializing invalid state."""
        manager = SplitTreeManager()
        
        success = manager.deserialize_state({"invalid": "data"})
        
        assert not success
        
    def test_set_layout_state(self):
        """Test setting a new layout state."""
        manager = SplitTreeManager()
        
        # Create custom layout
        pane1 = ContentPane()
        pane2 = ContentPane()
        container = SplitContainer(children=[pane1, pane2])
        custom_layout = LayoutState(root=container)
        
        with patch.object(manager, '_rebuild_widget_tree'), \
             patch.object(manager, '_create_widget_tree', return_value=None):
            manager.set_layout_state(custom_layout)
        
        assert manager.layout == custom_layout
        assert len(manager.get_all_pane_ids()) == 2
        
    def test_signals_emitted(self):
        """Test that appropriate signals are emitted."""
        manager = SplitTreeManager()
        
        # Mock signal emissions
        manager.pane_split = Mock()
        manager.layout_changed = Mock()
        
        pane_id = manager.get_active_pane_id()
        
        with patch.object(manager, '_rebuild_widget_tree'):
            new_pane_id = manager.split_pane(pane_id, Qt.Horizontal)
        
        # Verify signals were emitted
        manager.pane_split.emit.assert_called_once_with(pane_id, new_pane_id)
        manager.layout_changed.emit.assert_called_once()
        
    def test_multiple_nested_splits(self):
        """Test creating multiple nested splits."""
        manager = SplitTreeManager()
        pane1_id = manager.get_active_pane_id()
        
        with patch.object(manager, '_rebuild_widget_tree'):
            # First split horizontal
            pane2_id = manager.split_pane(pane1_id, Qt.Horizontal)
            
            # Split the new pane vertically
            pane3_id = manager.split_pane(pane2_id, Qt.Vertical)
            
            # Split first pane vertically
            pane4_id = manager.split_pane(pane1_id, Qt.Vertical)
        
        # Should have 4 panes now
        pane_ids = manager.get_all_pane_ids()
        assert len(pane_ids) == 4
        assert all(pid in pane_ids for pid in [pane1_id, pane2_id, pane3_id, pane4_id])
        
        # Root should be a container
        assert isinstance(manager.layout.root, SplitContainer)
        
    def test_complex_close_operations(self):
        """Test complex pane closing that requires tree restructuring."""
        manager = SplitTreeManager()
        pane1_id = manager.get_active_pane_id()
        
        with patch.object(manager, '_rebuild_widget_tree'):
            # Create: pane1 - [pane2, pane3] (horizontal)
            pane2_id = manager.split_pane(pane1_id, Qt.Horizontal)
            pane3_id = manager.split_pane(pane2_id, Qt.Horizontal)
            
            # Now close pane2 - should merge pane3 back with pane1
            success = manager.close_pane(pane2_id)
            
        assert success
        assert len(manager.get_all_pane_ids()) == 2
        assert pane1_id in manager.get_all_pane_ids()
        assert pane3_id in manager.get_all_pane_ids()
        assert pane2_id not in manager.get_all_pane_ids()