"""Unit tests for layout state data model."""

import pytest
from unittest.mock import Mock
from PySide6.QtCore import Qt
from models.layout_state import (
    SplitNode, SplitContainer, ContentPane, TabInfo, LayoutState
)


@pytest.mark.unit
class TestTabInfo:
    """Test cases for TabInfo class."""

    def test_tab_info_creation(self):
        """Test creating a TabInfo object."""
        tab = TabInfo(title="Test Tab", widget_type="placeholder")
        
        assert tab.title == "Test Tab"
        assert tab.widget_type == "placeholder"
        assert tab.is_closable == True
        assert tab.tab_id  # Should have a generated ID
        
    def test_tab_info_serialization(self):
        """Test TabInfo serialization."""
        tab = TabInfo(title="Test Tab", widget_type="text_editor")
        data = tab.to_dict()
        
        assert data["title"] == "Test Tab"
        assert data["widget_type"] == "text_editor"
        assert data["tab_id"] == tab.tab_id
        
    def test_tab_info_deserialization(self):
        """Test TabInfo deserialization."""
        data = {
            "tab_id": "test-id",
            "title": "Test Tab",
            "widget_type": "text_editor",
            "widget_data": {"content": "test"},
            "is_closable": False
        }
        
        tab = TabInfo.from_dict(data)
        assert tab.tab_id == "test-id"
        assert tab.title == "Test Tab" 
        assert tab.widget_type == "text_editor"
        assert tab.widget_data == {"content": "test"}
        assert tab.is_closable == False


@pytest.mark.unit
class TestContentPane:
    """Test cases for ContentPane class."""

    def test_content_pane_creation(self):
        """Test creating a ContentPane object."""
        pane = ContentPane()
        
        assert len(pane.tabs) == 1  # Should have default tab
        assert pane.active_tab == 0
        assert pane.node_id  # Should have generated ID
        
    def test_add_tab(self):
        """Test adding tabs to pane."""
        pane = ContentPane(tabs=[])  # Start with empty tabs
        pane.tabs = []  # Clear default tab for test
        
        tab1 = TabInfo(title="Tab 1")
        tab2 = TabInfo(title="Tab 2")
        
        pane.add_tab(tab1)
        assert len(pane.tabs) == 1
        assert pane.active_tab == 0
        
        pane.add_tab(tab2)
        assert len(pane.tabs) == 2
        assert pane.active_tab == 1  # Latest tab becomes active
        
    def test_remove_tab(self):
        """Test removing tabs from pane."""
        tab1 = TabInfo(title="Tab 1")
        tab2 = TabInfo(title="Tab 2")
        tab3 = TabInfo(title="Tab 3")
        
        pane = ContentPane(tabs=[tab1, tab2, tab3], active_tab=1)
        
        removed_tab = pane.remove_tab(1)  # Remove middle tab
        
        assert removed_tab == tab2
        assert len(pane.tabs) == 2
        assert pane.active_tab == 1  # Should point to tab3 now
        
    def test_remove_all_tabs_keeps_one(self):
        """Test that removing all tabs keeps at least one."""
        tab1 = TabInfo(title="Tab 1")
        pane = ContentPane(tabs=[tab1])
        
        removed_tab = pane.remove_tab(0)
        
        assert removed_tab == tab1
        assert len(pane.tabs) == 1  # Should add empty tab
        assert pane.tabs[0].title == "Empty"
        
    def test_move_tab(self):
        """Test moving tabs within pane."""
        tab1 = TabInfo(title="Tab 1")
        tab2 = TabInfo(title="Tab 2")
        tab3 = TabInfo(title="Tab 3")
        
        pane = ContentPane(tabs=[tab1, tab2, tab3], active_tab=0)
        
        success = pane.move_tab(0, 2)  # Move first tab to end
        
        assert success
        assert pane.tabs[0] == tab2
        assert pane.tabs[1] == tab3
        assert pane.tabs[2] == tab1
        assert pane.active_tab == 2  # Active tab moved
        
    def test_serialization(self):
        """Test ContentPane serialization."""
        tab1 = TabInfo(title="Tab 1")
        pane = ContentPane(tabs=[tab1], active_tab=0)
        
        data = pane.to_dict()
        
        assert data["type"] == "pane"
        assert data["node_id"] == pane.node_id
        assert len(data["tabs"]) == 1
        assert data["active_tab"] == 0
        
    def test_deserialization(self):
        """Test ContentPane deserialization."""
        data = {
            "type": "pane",
            "node_id": "test-pane",
            "tabs": [{"title": "Test Tab", "widget_type": "placeholder"}],
            "active_tab": 0
        }
        
        pane = ContentPane.from_dict(data)
        
        assert pane.node_id == "test-pane"
        assert len(pane.tabs) == 1
        assert pane.tabs[0].title == "Test Tab"
        assert pane.active_tab == 0


@pytest.mark.unit  
class TestSplitContainer:
    """Test cases for SplitContainer class."""

    def test_split_container_creation(self):
        """Test creating a SplitContainer object."""
        pane1 = ContentPane()
        pane2 = ContentPane()
        
        container = SplitContainer(
            orientation=Qt.Horizontal,
            children=[pane1, pane2]
        )
        
        assert container.orientation == Qt.Horizontal
        assert len(container.children) == 2
        assert len(container.sizes) == 2  # Should be normalized
        assert abs(sum(container.sizes) - 1.0) < 0.001  # Should sum to 1.0
        
        # Check parent references
        assert pane1.parent == container
        assert pane2.parent == container
        
    def test_add_child(self):
        """Test adding children to container."""
        container = SplitContainer(orientation=Qt.Horizontal)
        pane = ContentPane()
        
        container.add_child(pane)
        
        assert len(container.children) == 1
        assert pane.parent == container
        assert len(container.sizes) == 1
        assert container.sizes[0] == 1.0
        
    def test_remove_child(self):
        """Test removing children from container."""
        pane1 = ContentPane()
        pane2 = ContentPane()
        container = SplitContainer(children=[pane1, pane2])
        
        success = container.remove_child(pane1)
        
        assert success
        assert len(container.children) == 1
        assert container.children[0] == pane2
        assert pane1.parent is None
        assert len(container.sizes) == 1
        
    def test_replace_child(self):
        """Test replacing a child in container."""
        pane1 = ContentPane()
        pane2 = ContentPane()
        pane3 = ContentPane()
        
        container = SplitContainer(children=[pane1, pane2])
        
        success = container.replace_child(pane1, pane3)
        
        assert success
        assert container.children[0] == pane3
        assert container.children[1] == pane2
        assert pane1.parent is None
        assert pane3.parent == container
        
    def test_find_node(self):
        """Test finding nodes in container tree."""
        pane1 = ContentPane()
        pane2 = ContentPane()
        sub_container = SplitContainer(children=[pane2])
        root_container = SplitContainer(children=[pane1, sub_container])
        
        # Find direct child
        found = root_container.find_node(pane1.node_id)
        assert found == pane1
        
        # Find nested child
        found = root_container.find_node(pane2.node_id)
        assert found == pane2
        
        # Find container
        found = root_container.find_node(sub_container.node_id)
        assert found == sub_container
        
        # Find non-existent
        found = root_container.find_node("non-existent")
        assert found is None
        
    def test_get_all_panes(self):
        """Test getting all content panes from container."""
        pane1 = ContentPane()
        pane2 = ContentPane()
        pane3 = ContentPane()
        
        sub_container = SplitContainer(children=[pane2, pane3])
        root_container = SplitContainer(children=[pane1, sub_container])
        
        panes = root_container.get_all_panes()
        
        assert len(panes) == 3
        assert pane1 in panes
        assert pane2 in panes
        assert pane3 in panes
        
    def test_serialization(self):
        """Test SplitContainer serialization."""
        pane1 = ContentPane()
        pane2 = ContentPane()
        container = SplitContainer(
            orientation=Qt.Vertical,
            children=[pane1, pane2]
        )
        
        data = container.to_dict()
        
        assert data["type"] == "split"
        assert data["orientation"] == "vertical"
        assert len(data["children"]) == 2
        assert len(data["sizes"]) == 2
        
    def test_deserialization(self):
        """Test SplitContainer deserialization."""
        data = {
            "type": "split",
            "orientation": "vertical",
            "children": [
                {"type": "pane", "tabs": [], "active_tab": 0},
                {"type": "pane", "tabs": [], "active_tab": 0}
            ],
            "sizes": [0.6, 0.4]
        }
        
        container = SplitContainer.from_dict(data)
        
        assert container.orientation == Qt.Vertical
        assert len(container.children) == 2
        assert all(isinstance(child, ContentPane) for child in container.children)
        assert container.sizes == [0.6, 0.4]


@pytest.mark.unit
class TestLayoutState:
    """Test cases for LayoutState class."""

    def test_layout_state_creation(self):
        """Test creating LayoutState with default."""
        layout = LayoutState()
        
        assert isinstance(layout.root, ContentPane)
        assert layout.active_pane_id == layout.root.node_id
        
    def test_layout_state_with_container(self):
        """Test creating LayoutState with container root."""
        pane1 = ContentPane()
        pane2 = ContentPane()
        container = SplitContainer(children=[pane1, pane2])
        
        layout = LayoutState(root=container)
        
        assert layout.root == container
        assert layout.active_pane_id == pane1.node_id  # First pane
        
    def test_find_node(self):
        """Test finding nodes in layout."""
        layout = LayoutState()
        root_pane = layout.root
        
        found = layout.find_node(root_pane.node_id)
        assert found == root_pane
        
    def test_get_all_panes(self):
        """Test getting all panes from layout."""
        pane1 = ContentPane()
        pane2 = ContentPane()
        container = SplitContainer(children=[pane1, pane2])
        layout = LayoutState(root=container)
        
        panes = layout.get_all_panes()
        
        assert len(panes) == 2
        assert pane1 in panes
        assert pane2 in panes
        
    def test_set_active_pane(self):
        """Test setting active pane."""
        pane1 = ContentPane()
        pane2 = ContentPane()
        container = SplitContainer(children=[pane1, pane2])
        layout = LayoutState(root=container)
        
        success = layout.set_active_pane(pane2.node_id)
        
        assert success
        assert layout.active_pane_id == pane2.node_id
        
    def test_serialization(self):
        """Test LayoutState serialization."""
        layout = LayoutState()
        data = layout.to_dict()
        
        assert "root" in data
        assert "active_pane_id" in data
        assert "version" in data
        assert data["version"] == "1.0"
        
    def test_json_serialization(self):
        """Test JSON serialization."""
        layout = LayoutState()
        json_str = layout.to_json()
        
        assert isinstance(json_str, str)
        assert "root" in json_str
        assert "active_pane_id" in json_str
        
    def test_json_deserialization(self):
        """Test JSON deserialization."""
        original_layout = LayoutState()
        json_str = original_layout.to_json()
        
        restored_layout = LayoutState.from_json(json_str)
        
        assert isinstance(restored_layout.root, ContentPane)
        assert restored_layout.active_pane_id is not None
        
    def test_invalid_json_fallback(self):
        """Test fallback on invalid JSON."""
        layout = LayoutState.from_json("invalid json")
        
        assert isinstance(layout.root, ContentPane)
        assert layout.active_pane_id is not None