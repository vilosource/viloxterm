"""Unit tests for the workspace component."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pytestqt.qt_compat import qt_api
from PySide6.QtWidgets import QWidget, QSplitter, QTabWidget, QLabel
from PySide6.QtCore import Qt
from ui.workspace_simple import Workspace
from ui.widgets.split_pane_widget import SplitPaneWidget
from ui.widgets.widget_registry import WidgetType
from core.commands.executor import execute_command


@pytest.mark.unit
class TestWorkspace:
    """Test cases for Workspace class."""

    def test_workspace_initialization(self, qtbot):
        """Test workspace initializes correctly."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        assert workspace.objectName() == "workspace"
        assert hasattr(workspace, 'tab_widget')
        assert isinstance(workspace.tab_widget, QTabWidget)
        
        # Should have at least one tab created by default
        assert workspace.get_tab_count() >= 1

    def test_initial_tab_created(self, qtbot):
        """Test initial tab is created with split widget."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        # Check that tab widget exists with content
        assert workspace.tab_widget is not None
        assert workspace.get_tab_count() == 1
        
        # Check that current tab has a split widget
        current_split = workspace.get_current_split_widget()
        assert current_split is not None
        assert isinstance(current_split, SplitPaneWidget)

    def test_add_editor_tab(self, qtbot):
        """Test adding editor tabs."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        initial_count = workspace.get_tab_count()
        
        # Add an editor tab
        index = workspace.add_editor_tab("New Editor")
        
        # Should have one more tab
        assert workspace.get_tab_count() == initial_count + 1
        assert workspace.tab_widget.tabText(index) == "New Editor"
        
        # New tab should be current
        assert workspace.tab_widget.currentIndex() == index

    def test_add_terminal_tab(self, qtbot):
        """Test adding terminal tabs."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        initial_count = workspace.get_tab_count()
        
        # Add a terminal tab
        index = workspace.add_terminal_tab("Terminal")
        
        # Should have one more tab
        assert workspace.get_tab_count() == initial_count + 1
        assert workspace.tab_widget.tabText(index) == "Terminal"

    def test_add_output_tab(self, qtbot):
        """Test adding output tabs."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        initial_count = workspace.get_tab_count()
        
        # Add an output tab
        index = workspace.add_output_tab("Output")
        
        # Should have one more tab
        assert workspace.get_tab_count() == initial_count + 1
        assert workspace.tab_widget.tabText(index) == "Output"

    def test_close_tab(self, qtbot):
        """Test closing tabs."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        # Add another tab so we can close one
        workspace.add_editor_tab("Second Tab")
        initial_count = workspace.get_tab_count()
        
        # Close the second tab (index 1)
        workspace.close_tab(1)
        
        # Should have one less tab
        assert workspace.get_tab_count() == initial_count - 1

    @patch('ui.workspace_simple.QMessageBox.information')
    def test_close_last_tab_prevented(self, mock_msgbox, qtbot):
        """Test that closing the last tab is prevented."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        # Should have exactly one tab
        initial_count = workspace.get_tab_count()
        if initial_count == 1:
            # Try to close the only tab
            workspace.close_tab(0)
            
            # Should still have one tab
            assert workspace.get_tab_count() == 1
            # Should have shown a message box
            mock_msgbox.assert_called_once()

    def test_get_current_split_widget(self, qtbot):
        """Test getting current split widget."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        split_widget = workspace.get_current_split_widget()
        assert split_widget is not None
        assert isinstance(split_widget, SplitPaneWidget)

    def test_tab_switching(self, qtbot):
        """Test switching between tabs."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        # Add multiple tabs
        index1 = workspace.add_editor_tab("Tab 1")
        index2 = workspace.add_terminal_tab("Tab 2")
        
        # Switch to first tab
        workspace.tab_widget.setCurrentIndex(index1)
        assert workspace.tab_widget.currentIndex() == index1
        
        # Switch to second tab  
        workspace.tab_widget.setCurrentIndex(index2)
        assert workspace.tab_widget.currentIndex() == index2

    def test_split_active_pane_horizontal(self, qtbot):
        """Test splitting active pane horizontally."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        split_widget = workspace.get_current_split_widget()
        initial_count = split_widget.get_pane_count()
        
        # Split horizontally
        workspace.split_active_pane_horizontal()
        
        # Should have more panes
        assert split_widget.get_pane_count() > initial_count

    def test_split_active_pane_vertical(self, qtbot):
        """Test splitting active pane vertically."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        split_widget = workspace.get_current_split_widget()
        initial_count = split_widget.get_pane_count()
        
        # Split vertically
        workspace.split_active_pane_vertical()
        
        # Should have more panes
        assert split_widget.get_pane_count() > initial_count

    def test_close_active_pane(self, qtbot):
        """Test closing active pane."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        split_widget = workspace.get_current_split_widget()
        
        # First split to have multiple panes
        workspace.split_active_pane_horizontal()
        initial_count = split_widget.get_pane_count()
        
        # Close active pane
        workspace.close_active_pane()
        
        # Should have fewer panes
        assert split_widget.get_pane_count() < initial_count

    @patch('ui.workspace_simple.QMessageBox.information')
    def test_close_last_pane_prevented(self, mock_msgbox, qtbot):
        """Test that closing last pane in tab is prevented."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        split_widget = workspace.get_current_split_widget()
        
        # Should have exactly one pane initially
        initial_count = split_widget.get_pane_count()
        if initial_count == 1:
            # Try to close the only pane
            workspace.close_active_pane()
            
            # Should still have one pane
            assert split_widget.get_pane_count() == 1
            # Should have shown a message box
            mock_msgbox.assert_called_once()

    def test_get_current_tab_info(self, qtbot):
        """Test getting current tab information."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        # Add a named tab
        workspace.add_editor_tab("Test Tab")
        
        info = workspace.get_current_tab_info()
        assert info is not None
        assert isinstance(info, dict)
        assert "name" in info
        assert "index" in info
        assert "pane_count" in info
        assert "active_pane" in info
        assert "all_panes" in info

    def test_duplicate_tab(self, qtbot):
        """Test duplicating tabs."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        initial_count = workspace.get_tab_count()
        
        # Duplicate current tab (index 0)
        workspace.duplicate_tab(0)
        
        # Should have one more tab
        assert workspace.get_tab_count() == initial_count + 1

    def test_close_other_tabs(self, qtbot):
        """Test closing other tabs."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        # Add multiple tabs
        workspace.add_editor_tab("Tab 2")
        workspace.add_editor_tab("Tab 3")
        
        # Close other tabs except index 1
        workspace.close_other_tabs(1)
        
        # Should have only one tab remaining
        assert workspace.get_tab_count() == 1

    def test_close_tabs_to_right(self, qtbot):
        """Test closing tabs to the right."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        # Add multiple tabs
        workspace.add_editor_tab("Tab 2")
        workspace.add_editor_tab("Tab 3")
        workspace.add_editor_tab("Tab 4")
        
        initial_count = workspace.get_tab_count()
        
        # Close tabs to the right of index 1
        workspace.close_tabs_to_right(1)
        
        # Should have fewer tabs
        assert workspace.get_tab_count() < initial_count
        assert workspace.get_tab_count() <= 2  # Index 0 and 1

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

    def test_workspace_has_tab_widget(self, qtbot):
        """Test workspace contains tab widget."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        assert hasattr(workspace, 'tab_widget')
        assert isinstance(workspace.tab_widget, QTabWidget)
        
        # Check it's added to the layout
        layout = workspace.layout()
        assert layout.count() > 0

    def test_save_restore_state(self, qtbot):
        """Test state save and restore."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        # Add some tabs and modify state
        workspace.add_editor_tab("Test Tab")
        
        # Save state
        state = workspace.save_state()
        assert isinstance(state, dict)
        assert "current_tab" in state
        assert "tabs" in state
        
        # Create new workspace and restore
        workspace2 = Workspace()
        qtbot.addWidget(workspace2)
        workspace2.restore_state(state)
        
        # Should have similar structure
        assert workspace2.get_tab_count() >= 1

    def test_reset_to_default_layout(self, qtbot):
        """Test resetting to default layout."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        # Add multiple tabs
        workspace.add_editor_tab("Extra Tab")
        workspace.add_terminal_tab("Terminal")
        
        # Reset to default
        workspace.reset_to_default_layout()
        
        # Should have only default tab
        assert workspace.get_tab_count() == 1
        split_widget = workspace.get_current_split_widget()
        assert split_widget is not None
        assert split_widget.get_pane_count() >= 1

    def test_tab_widget_properties(self, qtbot):
        """Test tab widget properties."""
        workspace = Workspace()
        qtbot.addWidget(workspace)
        
        tab_widget = workspace.tab_widget
        
        # Check properties are set correctly
        assert tab_widget.tabsClosable() == True
        assert tab_widget.isMovable() == True
        assert tab_widget.documentMode() == True
        assert tab_widget.elideMode() == Qt.ElideRight