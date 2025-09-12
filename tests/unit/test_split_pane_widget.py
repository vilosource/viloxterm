"""Unit tests for the split pane widget functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pytestqt.qt_compat import qt_api
from PySide6.QtWidgets import QWidget, QSplitter, QTabWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt
from ui.widgets.split_pane_widget import PaneContent, SplitPaneWidget
from ui.widgets.split_pane_model import LeafNode, SplitNode
from ui.widgets.widget_registry import WidgetType


@pytest.mark.unit
class TestPaneContent:
    """Test cases for PaneContent class."""

    @pytest.fixture
    def mock_leaf_node(self, qtbot):
        """Create a mock LeafNode for testing."""
        leaf = Mock(spec=LeafNode)
        leaf.id = "test-pane-1"
        leaf.widget_type = WidgetType.TEXT_EDITOR
        
        # Create a real QWidget for the app_widget since layout expects it
        from PySide6.QtWidgets import QLabel
        leaf.app_widget = QLabel("Test Widget")
        leaf.app_widget.widget_id = "mock-widget-1"
        leaf.app_widget.request_action = Mock()
        leaf.app_widget.request_focus = Mock()
        qtbot.addWidget(leaf.app_widget)
        
        return leaf

    def test_pane_content_initialization(self, qtbot, mock_leaf_node):
        """Test pane content initializes correctly."""
        from PySide6.QtWidgets import QLabel
        
        pane = PaneContent(mock_leaf_node)
        qtbot.addWidget(pane)
        
        # Check basic attributes
        assert pane.leaf_node == mock_leaf_node
        assert pane.is_active == False
        assert hasattr(pane, 'header_bar')
        
        # Check unique IDs through leaf nodes
        leaf2 = Mock(spec=LeafNode)
        leaf2.id = "test-pane-2"
        leaf2.widget_type = WidgetType.TEXT_EDITOR
        leaf2.app_widget = QLabel("Test Widget 2")
        leaf2.app_widget.widget_id = "mock-widget-2"
        leaf2.app_widget.request_action = Mock()
        leaf2.app_widget.request_focus = Mock()
        qtbot.addWidget(leaf2.app_widget)
        pane2 = PaneContent(leaf2)
        assert pane.leaf_node.id != pane2.leaf_node.id

    def test_pane_content_active_state(self, qtbot, mock_leaf_node):
        """Test active state management."""
        pane = PaneContent(mock_leaf_node)
        qtbot.addWidget(pane)
        
        # Test setting active state
        pane.set_active(True)
        assert pane.is_active == True
        
        pane.set_active(False)
        assert pane.is_active == False

    def test_pane_content_request_split(self, qtbot, mock_leaf_node):
        """Test split request handling."""
        pane = PaneContent(mock_leaf_node)
        qtbot.addWidget(pane)
        
        # Test horizontal split request
        pane.request_split("horizontal")
        mock_leaf_node.app_widget.request_action.assert_called_with(
            'split', {'orientation': 'horizontal', 'leaf_id': mock_leaf_node.id}
        )

    def test_pane_content_request_close(self, qtbot, mock_leaf_node):
        """Test close request handling."""
        pane = PaneContent(mock_leaf_node)
        qtbot.addWidget(pane)
        
        # Test close request
        pane.request_close()
        mock_leaf_node.app_widget.request_action.assert_called_with(
            'close', {'leaf_id': mock_leaf_node.id}
        )

    def test_pane_content_layout(self, qtbot, mock_leaf_node):
        """Test pane content has proper layout."""
        pane = PaneContent(mock_leaf_node)
        qtbot.addWidget(pane)
        
        layout = pane.layout()
        assert layout is not None
        assert isinstance(layout, QVBoxLayout)
        assert layout.contentsMargins().left() == 0
        assert layout.contentsMargins().top() == 0
        assert layout.contentsMargins().right() == 0
        assert layout.contentsMargins().bottom() == 0

    def test_pane_content_mouse_press(self, qtbot, mock_leaf_node):
        """Test mouse press focus handling."""
        pane = PaneContent(mock_leaf_node)
        qtbot.addWidget(pane)
        
        # Simulate mouse press
        from PySide6.QtGui import QMouseEvent
        from PySide6.QtCore import QPointF
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPointF(10, 10),
            QPointF(10, 10),  # global position
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        # Should request focus through app widget
        pane.mousePressEvent(event)
        mock_leaf_node.app_widget.request_focus.assert_called_once()

    def test_pane_content_change_widget_type(self, qtbot, mock_leaf_node):
        """Test widget type change request."""
        pane = PaneContent(mock_leaf_node)
        qtbot.addWidget(pane)
        
        # Test type change request
        new_type = WidgetType.TERMINAL
        pane.change_widget_type(new_type)
        mock_leaf_node.app_widget.request_action.assert_called_with(
            'change_type', {'leaf_id': mock_leaf_node.id, 'new_type': new_type}
        )


@pytest.mark.unit
class TestSplitPaneWidget:
    """Test cases for SplitPaneWidget class."""

    def test_split_pane_widget_initialization(self, qtbot):
        """Test split pane widget initializes correctly."""
        widget = SplitPaneWidget()
        qtbot.addWidget(widget)
        
        # Should have model with root pane
        assert widget.model is not None
        assert widget.model.root is not None
        
        # Should have active pane ID
        active_id = widget.active_pane_id
        assert active_id is not None
        assert isinstance(active_id, str)
        
        # Should have at least one pane
        assert widget.get_pane_count() >= 1

    def test_split_horizontal(self, qtbot):
        """Test horizontal splitting."""
        widget = SplitPaneWidget()
        qtbot.addWidget(widget)
        
        initial_count = widget.get_pane_count()
        active_pane_id = widget.active_pane_id
        
        # Split horizontally
        new_pane_id = widget.split_horizontal(active_pane_id)
        
        # Check new pane was created
        assert new_pane_id is not None
        assert isinstance(new_pane_id, str)
        assert widget.get_pane_count() == initial_count + 1
        assert new_pane_id in widget.get_all_pane_ids()

    def test_split_vertical(self, qtbot):
        """Test vertical splitting."""
        widget = SplitPaneWidget()
        qtbot.addWidget(widget)
        
        initial_count = widget.get_pane_count()
        active_pane_id = widget.active_pane_id
        
        # Split vertically
        new_pane_id = widget.split_vertical(active_pane_id)
        
        # Check new pane was created
        assert new_pane_id is not None
        assert isinstance(new_pane_id, str)
        assert widget.get_pane_count() == initial_count + 1
        assert new_pane_id in widget.get_all_pane_ids()

    def test_close_pane(self, qtbot):
        """Test closing a pane."""
        widget = SplitPaneWidget()
        qtbot.addWidget(widget)
        
        # First split to have multiple panes
        active_pane_id = widget.active_pane_id
        new_pane_id = widget.split_horizontal(active_pane_id)
        
        initial_count = widget.get_pane_count()
        assert initial_count >= 2
        
        # Close the new pane
        widget.close_pane(new_pane_id)
        
        # Check pane was removed
        assert widget.get_pane_count() == initial_count - 1
        assert new_pane_id not in widget.get_all_pane_ids()

    def test_close_last_pane_prevented(self, qtbot):
        """Test that closing the last pane is prevented."""
        widget = SplitPaneWidget()
        qtbot.addWidget(widget)
        
        # Should have exactly one pane
        initial_count = widget.get_pane_count()
        if initial_count == 1:
            last_pane_id = widget.active_pane_id
            
            # Try to close the last pane
            widget.close_pane(last_pane_id)
            
            # Should still have one pane
            assert widget.get_pane_count() == 1

    def test_set_active_pane(self, qtbot):
        """Test setting the active pane."""
        widget = SplitPaneWidget()
        qtbot.addWidget(widget)
        
        # Split to have multiple panes
        first_pane_id = widget.active_pane_id
        second_pane_id = widget.split_horizontal(first_pane_id)
        
        # Set second pane as active
        widget.set_active_pane(second_pane_id)
        assert widget.active_pane_id == second_pane_id
        
        # Set first pane as active
        widget.set_active_pane(first_pane_id)
        assert widget.active_pane_id == first_pane_id

    def test_get_all_pane_ids(self, qtbot):
        """Test getting all pane IDs."""
        widget = SplitPaneWidget()
        qtbot.addWidget(widget)
        
        # Create multiple panes
        first_pane_id = widget.active_pane_id
        second_pane_id = widget.split_horizontal(first_pane_id)
        third_pane_id = widget.split_vertical(second_pane_id)
        
        all_pane_ids = widget.get_all_pane_ids()
        
        # Check all panes are returned
        assert len(all_pane_ids) >= 3
        assert first_pane_id in all_pane_ids
        assert second_pane_id in all_pane_ids
        assert third_pane_id in all_pane_ids
        
        # Check all are strings
        assert all(isinstance(pane_id, str) for pane_id in all_pane_ids)

    def test_multiple_splits(self, qtbot):
        """Test multiple split operations."""
        widget = SplitPaneWidget()
        qtbot.addWidget(widget)
        
        # Perform multiple splits
        pane1_id = widget.active_pane_id
        pane2_id = widget.split_horizontal(pane1_id)
        pane3_id = widget.split_vertical(pane2_id)
        pane4_id = widget.split_horizontal(pane3_id)
        
        all_pane_ids = widget.get_all_pane_ids()
        
        # Should have 4 panes
        assert len(all_pane_ids) == 4
        assert all(isinstance(p_id, str) for p_id in all_pane_ids)
        assert widget.get_pane_count() == 4

    def test_pane_navigation(self, qtbot):
        """Test navigating between panes."""
        widget = SplitPaneWidget()
        qtbot.addWidget(widget)
        
        # Create panes in specific arrangement
        pane1_id = widget.active_pane_id
        pane2_id = widget.split_horizontal(pane1_id)
        
        # Navigate between panes
        widget.set_active_pane(pane2_id)
        assert widget.active_pane_id == pane2_id
        
        widget.set_active_pane(pane1_id)
        assert widget.active_pane_id == pane1_id

    def test_pane_focus_tracking(self, qtbot):
        """Test that focus is tracked correctly."""
        widget = SplitPaneWidget()
        qtbot.addWidget(widget)
        
        pane1_id = widget.active_pane_id
        pane2_id = widget.split_horizontal(pane1_id)
        
        # Simulate focus change
        widget.set_active_pane(pane2_id)
        
        # Check active pane is updated
        assert widget.active_pane_id == pane2_id
        
        # Check wrappers have correct active state
        pane1_wrapper = widget.pane_wrappers.get(pane1_id)
        pane2_wrapper = widget.pane_wrappers.get(pane2_id)
        
        if pane1_wrapper and pane2_wrapper:
            assert pane2_wrapper.is_active == True
            assert pane1_wrapper.is_active == False
            
    def test_get_state_and_set_state(self, qtbot):
        """Test state persistence."""
        widget = SplitPaneWidget()
        qtbot.addWidget(widget)
        
        # Create some panes
        pane1_id = widget.active_pane_id
        pane2_id = widget.split_horizontal(pane1_id)
        
        # Get state
        state = widget.get_state()
        assert isinstance(state, dict)
        
        # Create new widget and restore state
        widget2 = SplitPaneWidget()
        qtbot.addWidget(widget2)
        success = widget2.set_state(state)
        
        # Should restore successfully
        assert success == True
        assert widget2.get_pane_count() >= 2
        
    def test_pane_numbers_toggle(self, qtbot):
        """Test pane number visibility toggle."""
        widget = SplitPaneWidget()
        qtbot.addWidget(widget)
        
        # Should have toggle method
        visible = widget.toggle_pane_numbers()
        assert isinstance(visible, bool)
        
        # Toggle again
        visible2 = widget.toggle_pane_numbers()
        assert visible2 != visible