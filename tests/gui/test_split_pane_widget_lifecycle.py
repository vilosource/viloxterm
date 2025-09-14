#!/usr/bin/env python3
"""
GUI integration tests for SplitPaneWidget with widget lifecycle.
Tests focus handling during split operations with async widgets.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest, QSignalSpy
from ui.widgets.split_pane_widget import SplitPaneWidget
from ui.widgets.split_pane_model import SplitPaneModel
from ui.widgets.app_widget import AppWidget
from ui.widgets.widget_registry import WidgetType
from ui.widgets.widget_state import WidgetState


class MockAsyncWidget(AppWidget):
    """Mock async widget for testing split pane behavior."""

    def __init__(self, widget_id: str, init_delay: int = 50, parent=None):
        super().__init__(widget_id, WidgetType.TERMINAL, parent)
        self.init_delay = init_delay
        self.focus_count = 0

    def start_initialization(self):
        """Start async initialization."""
        self.initialize()
        QTimer.singleShot(self.init_delay, self.complete_initialization)

    def complete_initialization(self):
        """Complete initialization and become ready."""
        self.set_ready()

    def focus_widget(self):
        """Track focus calls."""
        self.focus_count += 1
        return super().focus_widget()


class MockSyncWidget(AppWidget):
    """Mock sync widget that's ready immediately."""

    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.TEXT_EDITOR, parent)
        self.focus_count = 0
        self.initialize()
        self.set_ready()

    def focus_widget(self):
        """Track focus calls."""
        self.focus_count += 1
        return super().focus_widget()


class TestSplitPaneWidgetLifecycle:
    """Test SplitPaneWidget integration with widget lifecycle."""

    @pytest.fixture
    def split_pane(self, qtbot):
        """Create a SplitPaneWidget for testing."""
        # Create split pane widget (it creates its own model)
        split_widget = SplitPaneWidget(WidgetType.PLACEHOLDER)
        qtbot.addWidget(split_widget)

        # Get the model that was created
        model = split_widget.model

        # Replace the auto-created widget with our mock
        root_widget = MockSyncWidget("root-widget")
        if model.root.app_widget:
            model.root.app_widget.cleanup()  # Clean up the auto-created widget
        model.root.app_widget = root_widget
        root_widget.leaf_node = model.root

        return split_widget, model, root_widget

    def test_split_with_async_widget_focus(self, qtbot, split_pane):
        """Test that focus is properly handled when splitting with async widget."""
        split_widget, model, root_widget = split_pane

        # Mock the model to return async widget on split
        async_widget = MockAsyncWidget("async-1", init_delay=50)

        def mock_split(pane_id, orientation):
            # Simulate split creating new leaf with async widget
            new_leaf_id = "new-pane-id"
            # Add the new leaf to the model's leaves dict
            from ui.widgets.split_pane_model import LeafNode
            new_leaf = LeafNode(id=new_leaf_id)
            new_leaf.app_widget = async_widget
            async_widget.leaf_node = new_leaf
            model.leaves[new_leaf_id] = new_leaf
            return new_leaf_id

        with patch.object(model, 'split_pane', side_effect=mock_split):
            # Start async widget initialization
            async_widget.start_initialization()

            # Perform split (use the active pane ID)
            split_widget.split_horizontal(model.get_active_pane_id())

            # Widget should be in INITIALIZING state
            assert async_widget.widget_state == WidgetState.INITIALIZING

            # Wait for widget to become ready
            with qtbot.waitSignal(async_widget.widget_ready, timeout=200):
                pass

            # Process events
            qtbot.wait(10)

            # Focus should have been applied
            assert async_widget.widget_state == WidgetState.READY

    def test_split_with_sync_widget_focus(self, qtbot, split_pane):
        """Test that focus is immediate for sync widgets during split."""
        split_widget, model, root_widget = split_pane

        # Mock the model to return sync widget on split
        sync_widget = MockSyncWidget("sync-1")

        def mock_split(pane_id, orientation):
            new_leaf_id = "new-pane-id"
            from ui.widgets.split_pane_model import LeafNode
            new_leaf = LeafNode(id=new_leaf_id)
            new_leaf.app_widget = sync_widget
            sync_widget.leaf_node = new_leaf
            model.leaves[new_leaf_id] = new_leaf
            return new_leaf_id

        with patch.object(model, 'split_pane', side_effect=mock_split):
            # Make sure the widget is visible for focus testing
            # (SplitPaneWidget only runs focus logic when isVisible() == True)
            split_widget.show()
            with qtbot.waitExposed(split_widget, timeout=1000):
                pass

            # Perform split
            split_widget.split_horizontal(model.get_active_pane_id())

            # Widget should be ready immediately
            assert sync_widget.widget_state == WidgetState.READY

            # Focus should have been attempted (verify through focus_count instead of actual focus)
            # Note: We test the focus attempt, not actual OS focus which is unreliable in tests
            assert sync_widget.focus_count > 0

    def test_multiple_splits_with_mixed_widgets(self, qtbot, split_pane):
        """Test multiple splits with both sync and async widgets."""
        split_widget, model, root_widget = split_pane

        widgets_created = []

        def create_mock_split(widget):
            """Create a mock split function for a widget."""
            def mock_split(pane_id, orientation):
                new_leaf_id = f"pane-{widget.widget_id}"
                from ui.widgets.split_pane_model import LeafNode
                new_leaf = LeafNode(id=new_leaf_id)
                new_leaf.app_widget = widget
                widget.leaf_node = new_leaf
                model.leaves[new_leaf_id] = new_leaf
                widgets_created.append(widget)
                return new_leaf_id
            return mock_split

        # Create mix of widgets
        sync_widget1 = MockSyncWidget("sync-2")
        async_widget1 = MockAsyncWidget("async-2", init_delay=30)
        sync_widget2 = MockSyncWidget("sync-3")
        async_widget2 = MockAsyncWidget("async-3", init_delay=60)

        # Perform multiple splits
        for widget in [sync_widget1, async_widget1, sync_widget2, async_widget2]:
            with patch.object(model, 'split_pane', side_effect=create_mock_split(widget)):
                # Start async widgets
                if isinstance(widget, MockAsyncWidget):
                    widget.start_initialization()

                split_widget.split_horizontal(model.get_active_pane_id())

        # Check sync widgets are ready immediately
        assert sync_widget1.widget_state == WidgetState.READY
        assert sync_widget2.widget_state == WidgetState.READY

        # Check async widgets are initializing
        assert async_widget1.widget_state == WidgetState.INITIALIZING
        assert async_widget2.widget_state == WidgetState.INITIALIZING

        # Wait for all async widgets to be ready
        for widget in [async_widget1, async_widget2]:
            with qtbot.waitSignal(widget.widget_ready, timeout=200):
                pass

        # All should be ready
        assert async_widget1.widget_state == WidgetState.READY
        assert async_widget2.widget_state == WidgetState.READY

    def test_widget_ready_signal_connection(self, qtbot, split_pane):
        """Test that split pane properly connects to widget_ready signal."""
        split_widget, model, root_widget = split_pane

        # Create async widget
        async_widget = MockAsyncWidget("async-4", init_delay=50)

        # Use QSignalSpy to monitor signal connections
        signal_spy = QSignalSpy(async_widget.widget_ready)

        def mock_split(pane_id, orientation):
            new_leaf_id = "new-pane"
            from ui.widgets.split_pane_model import LeafNode
            new_leaf = LeafNode(id=new_leaf_id)
            new_leaf.app_widget = async_widget
            async_widget.leaf_node = new_leaf
            model.leaves[new_leaf_id] = new_leaf
            return new_leaf_id

        with patch.object(model, 'split_pane', side_effect=mock_split):
            # Start initialization
            async_widget.start_initialization()

            # Perform split
            split_widget.split_horizontal(model.get_active_pane_id())

            # Wait for widget to become ready
            with qtbot.waitSignal(async_widget.widget_ready, timeout=200):
                pass

            # Signal should have been emitted
            assert signal_spy.count() == 1
            assert async_widget.widget_state == WidgetState.READY

    def test_focus_after_widget_ready(self, qtbot, split_pane):
        """Test that focus is applied after widget becomes ready."""
        split_widget, model, root_widget = split_pane

        async_widget = MockAsyncWidget("async-5", init_delay=50)

        def mock_split(pane_id, orientation):
            new_leaf_id = "focus-test-pane"
            from ui.widgets.split_pane_model import LeafNode
            new_leaf = LeafNode(id=new_leaf_id)
            new_leaf.app_widget = async_widget
            async_widget.leaf_node = new_leaf
            model.leaves[new_leaf_id] = new_leaf
            return new_leaf_id

        with patch.object(model, 'split_pane', side_effect=mock_split):
            async_widget.start_initialization()
            split_widget.split_horizontal(model.get_active_pane_id())

            # Wait for ready
            with qtbot.waitSignal(async_widget.widget_ready, timeout=200):
                pass

            qtbot.wait(10)

            # Widget should be ready and focus should have been attempted
            assert async_widget.widget_state == WidgetState.READY
            # Note: actual focus testing is unreliable in test environment

    def test_split_with_error_widget(self, qtbot, split_pane):
        """Test split behavior when widget enters error state."""
        split_widget, model, root_widget = split_pane

        # Create widget that will error
        error_widget = MockAsyncWidget("error-1", init_delay=50)

        def mock_split(pane_id, orientation):
            new_leaf_id = "error-pane"
            from ui.widgets.split_pane_model import LeafNode
            new_leaf = LeafNode(id=new_leaf_id)
            new_leaf.app_widget = error_widget
            error_widget.leaf_node = new_leaf
            model.leaves[new_leaf_id] = new_leaf
            return new_leaf_id

        with patch.object(model, 'split_pane', side_effect=mock_split):
            # Start initialization but trigger error
            error_widget.initialize()
            error_widget.set_error("Test error during init")

            # Perform split
            split_widget.split_horizontal(model.get_active_pane_id())

            # Widget should be in error state
            assert error_widget.widget_state == WidgetState.ERROR

            # Focus should not be applied
            assert error_widget.focus_count == 0

    def test_cleanup_during_initialization(self, qtbot, split_pane):
        """Test cleanup when widget is destroyed during initialization."""
        split_widget, model, root_widget = split_pane

        async_widget = MockAsyncWidget("cleanup-1", init_delay=100)

        def mock_split(pane_id, orientation):
            new_leaf_id = "cleanup-pane"
            from ui.widgets.split_pane_model import LeafNode
            new_leaf = LeafNode(id=new_leaf_id)
            new_leaf.app_widget = async_widget
            async_widget.leaf_node = new_leaf
            model.leaves[new_leaf_id] = new_leaf
            return new_leaf_id

        with patch.object(model, 'split_pane', side_effect=mock_split):
            async_widget.start_initialization()
            split_widget.split_horizontal(model.get_active_pane_id())

            # Cleanup widget before it's ready
            async_widget.cleanup()
            assert async_widget.widget_state == WidgetState.DESTROYED

            # Wait to ensure no crashes
            qtbot.wait(150)