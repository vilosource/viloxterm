"""Unit tests for the workspace component."""

import pytest
from unittest.mock import Mock, patch
from pytestqt.qt_compat import qt_api
from PySide6.QtWidgets import QWidget, QSplitter, QTabWidget, QLabel
from PySide6.QtCore import Qt
from ui.workspace import Workspace, TabContainer


@pytest.mark.unit
class TestWorkspace:
    """Test cases for Workspace class."""

    def test_workspace_initialization(self, qtbot):
        """Test workspace initializes correctly."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        assert workspace.objectName() == "workspace"
        assert hasattr(workspace, 'root_splitter')
        assert isinstance(workspace.root_splitter, QSplitter)
        assert workspace.root_splitter.orientation() == Qt.Horizontal

    def test_initial_pane_created(self, qtbot):
        """Test initial pane is created with welcome tab."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        # Check root splitter has one widget
        assert workspace.root_splitter.count() == 1
        
        # Check that widget is a TabContainer
        initial_pane = workspace.root_splitter.widget(0)
        assert isinstance(initial_pane, TabContainer)
        
        # Check initial tab exists
        assert initial_pane.count() == 1
        assert initial_pane.tabText(0) == "Welcome"

    def test_split_horizontal_default_widget(self, qtbot):
        """Test horizontal split with default widget."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        # Get initial pane count
        initial_count = workspace.root_splitter.count()
        
        # Split horizontally
        new_pane = workspace.split_horizontal()
        
        # Check new pane was created
        assert isinstance(new_pane, TabContainer)
        assert new_pane.count() == 1
        assert new_pane.tabText(0) == "New Tab"
        
        # Check structure changed
        # Root splitter should still have 1 widget, but it should be a new splitter
        assert workspace.root_splitter.count() == 1
        new_splitter = workspace.root_splitter.widget(0)
        assert isinstance(new_splitter, QSplitter)
        assert new_splitter.orientation() == Qt.Horizontal
        assert new_splitter.count() == 2

    def test_split_vertical_default_widget(self, qtbot):
        """Test vertical split with default widget."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        # Split vertically
        new_pane = workspace.split_vertical()
        
        # Check new pane was created
        assert isinstance(new_pane, TabContainer)
        assert new_pane.count() == 1
        assert new_pane.tabText(0) == "New Tab"
        
        # Check structure changed
        assert workspace.root_splitter.count() == 1
        new_splitter = workspace.root_splitter.widget(0)
        assert isinstance(new_splitter, QSplitter)
        assert new_splitter.orientation() == Qt.Vertical
        assert new_splitter.count() == 2

    def test_split_horizontal_specific_widget(self, qtbot):
        """Test horizontal split with specific widget."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        # Get the initial pane
        initial_pane = workspace.root_splitter.widget(0)
        
        # Split the specific widget
        new_pane = workspace.split_horizontal(initial_pane)
        
        # Check new pane was created
        assert isinstance(new_pane, TabContainer)
        
        # Check the initial pane is still in the structure
        new_splitter = workspace.root_splitter.widget(0)
        assert initial_pane in [new_splitter.widget(i) for i in range(new_splitter.count())]

    def test_split_vertical_specific_widget(self, qtbot):
        """Test vertical split with specific widget."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        # Get the initial pane
        initial_pane = workspace.root_splitter.widget(0)
        
        # Split the specific widget
        new_pane = workspace.split_vertical(initial_pane)
        
        # Check new pane was created
        assert isinstance(new_pane, TabContainer)
        
        # Check the initial pane is still in the structure
        new_splitter = workspace.root_splitter.widget(0)
        assert initial_pane in [new_splitter.widget(i) for i in range(new_splitter.count())]

    def test_multiple_splits(self, qtbot):
        """Test multiple splits create correct structure."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        # First horizontal split
        pane1 = workspace.split_horizontal()
        
        # Second vertical split on new pane
        pane2 = workspace.split_vertical(pane1)
        
        # Check all panes exist and are TabContainers
        assert isinstance(pane1, TabContainer)
        assert isinstance(pane2, TabContainer)

    def test_layout_setup(self, qtbot):
        """Test layout is set up correctly."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        layout = workspace.layout()
        assert layout is not None
        assert layout.contentsMargins().left() == 0
        assert layout.contentsMargins().top() == 0
        assert layout.contentsMargins().right() == 0
        assert layout.contentsMargins().bottom() == 0


@pytest.mark.unit
class TestTabContainer:
    """Test cases for TabContainer class."""

    def test_tab_container_initialization(self, qtbot):
        """Test tab container initializes correctly."""
        container = TabContainer()
        qtbot.addWidget(container)
        
        assert container.tabsClosable()
        assert container.isMovable()
        assert container.documentMode()

    def test_add_tab(self, qtbot):
        """Test adding a new tab."""
        container = TabContainer()
        qtbot.addWidget(container)
        
        # Add a tab
        widget = QLabel("Test Content")
        index = container.add_tab("Test Tab", widget)
        
        # Check tab was added
        assert container.count() == 1
        assert container.tabText(index) == "Test Tab"
        assert container.widget(index) == widget
        assert container.currentIndex() == index

    def test_add_multiple_tabs(self, qtbot):
        """Test adding multiple tabs."""
        container = TabContainer()
        qtbot.addWidget(container)
        
        # Add multiple tabs
        widget1 = QLabel("Content 1")
        widget2 = QLabel("Content 2")
        widget3 = QLabel("Content 3")
        
        index1 = container.add_tab("Tab 1", widget1)
        index2 = container.add_tab("Tab 2", widget2)
        index3 = container.add_tab("Tab 3", widget3)
        
        # Check all tabs added
        assert container.count() == 3
        assert container.tabText(0) == "Tab 1"
        assert container.tabText(1) == "Tab 2"
        assert container.tabText(2) == "Tab 3"
        
        # Check current tab is the last added
        assert container.currentIndex() == index3

    def test_close_tab_multiple_tabs(self, qtbot):
        """Test closing a tab when multiple tabs exist."""
        container = TabContainer()
        qtbot.addWidget(container)
        
        # Add multiple tabs
        container.add_tab("Tab 1", QLabel("Content 1"))
        container.add_tab("Tab 2", QLabel("Content 2"))
        container.add_tab("Tab 3", QLabel("Content 3"))
        
        assert container.count() == 3
        
        # Close middle tab
        container.close_tab(1)
        
        # Check tab was closed
        assert container.count() == 2
        assert container.tabText(0) == "Tab 1"
        assert container.tabText(1) == "Tab 3"

    def test_close_tab_single_tab(self, qtbot):
        """Test closing the last remaining tab does nothing."""
        container = TabContainer()
        qtbot.addWidget(container)
        
        # Add single tab
        container.add_tab("Only Tab", QLabel("Content"))
        assert container.count() == 1
        
        # Try to close the only tab
        container.close_tab(0)
        
        # Check tab was not closed
        assert container.count() == 1
        assert container.tabText(0) == "Only Tab"

    def test_tab_close_signal_connected(self, qtbot):
        """Test tab close signal is connected."""
        container = TabContainer()
        qtbot.addWidget(container)
        
        # Mock the close_tab method
        container.close_tab = Mock()
        
        # Add tabs
        container.add_tab("Tab 1", QLabel("Content 1"))
        container.add_tab("Tab 2", QLabel("Content 2"))
        
        # Emit tabCloseRequested signal
        container.tabCloseRequested.emit(1)
        
        # Check close_tab was called with correct index
        container.close_tab.assert_called_once_with(1)

    def test_tab_container_properties(self, qtbot):
        """Test tab container UI properties."""
        container = TabContainer()
        qtbot.addWidget(container)
        
        # Check properties are set correctly
        assert container.tabsClosable() == True
        assert container.isMovable() == True
        assert container.documentMode() == True

    def test_current_tab_changes_on_add(self, qtbot):
        """Test current tab changes when new tab is added."""
        container = TabContainer()
        qtbot.addWidget(container)
        
        # Add first tab
        index1 = container.add_tab("Tab 1", QLabel("Content 1"))
        assert container.currentIndex() == index1
        
        # Add second tab
        index2 = container.add_tab("Tab 2", QLabel("Content 2"))
        assert container.currentIndex() == index2
        
        # Add third tab
        index3 = container.add_tab("Tab 3", QLabel("Content 3"))
        assert container.currentIndex() == index3

    def test_widget_retrieval(self, qtbot):
        """Test retrieving widgets from tabs."""
        container = TabContainer()
        qtbot.addWidget(container)
        
        # Add tabs with specific widgets
        widget1 = QLabel("Content 1")
        widget2 = QLabel("Content 2")
        
        container.add_tab("Tab 1", widget1)
        container.add_tab("Tab 2", widget2)
        
        # Check widgets can be retrieved correctly
        assert container.widget(0) == widget1
        assert container.widget(1) == widget2


@pytest.mark.unit
class TestTabCloseBehavior:
    """Test cases for tab closing behavior without confirmation."""
    
    def test_tab_close_last_tab_in_last_pane(self, qtbot):
        """Test closing last tab in last pane adds placeholder."""
        # Create workspace with mock UI
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        # Create mock tab container with single tab
        from ui.widgets.tab_container import TabContainer
        pane_id = "test-pane-1"
        tab_container = Mock(spec=TabContainer)
        tab_container.count.return_value = 1  # Single tab
        tab_container.removeTab = Mock()
        tab_container.add_placeholder_tab = Mock()
        tab_container.tab_closed = Mock()
        
        workspace._tab_containers[pane_id] = tab_container
        
        # Mock get_pane_count to return 1 (single pane)
        workspace.get_pane_count = Mock(return_value=1)
        
        # Trigger tab close request
        workspace._on_tab_close_requested(pane_id, 0)
        
        # Should add placeholder instead of closing pane
        tab_container.removeTab.assert_called_once_with(0)
        tab_container.add_placeholder_tab.assert_called_once()
        tab_container.close_tab.assert_not_called()
    
    def test_tab_close_multiple_tabs_in_pane(self, qtbot):
        """Test closing tab when multiple tabs exist in pane."""
        # Create workspace with mock UI
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        # Create mock tab container with multiple tabs
        from ui.widgets.tab_container import TabContainer
        pane_id = "test-pane-1"
        tab_container = Mock(spec=TabContainer)
        tab_container.count.return_value = 3  # Multiple tabs
        tab_container.close_tab = Mock()
        
        workspace._tab_containers[pane_id] = tab_container
        
        # Mock get_pane_count to return 2 (multiple panes)
        workspace.get_pane_count = Mock(return_value=2)
        
        # Trigger tab close request
        workspace._on_tab_close_requested(pane_id, 1)
        
        # Should call close_tab which will just remove the tab
        tab_container.close_tab.assert_called_once_with(1)
    
    def test_tab_close_single_tab_in_pane_with_multiple_panes(self, qtbot):
        """Test closing single tab in pane when multiple panes exist."""
        # Create workspace with mock UI
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        # Create mock tab container with single tab
        from ui.widgets.tab_container import TabContainer
        pane_id = "test-pane-1"
        tab_container = Mock(spec=TabContainer)
        tab_container.count.return_value = 1  # Single tab
        tab_container.close_tab = Mock()
        
        workspace._tab_containers[pane_id] = tab_container
        
        # Mock get_pane_count to return 2 (multiple panes)
        workspace.get_pane_count = Mock(return_value=2)
        
        # Trigger tab close request
        workspace._on_tab_close_requested(pane_id, 0)
        
        # Should call close_tab which will emit close_pane_requested
        tab_container.close_tab.assert_called_once_with(0)