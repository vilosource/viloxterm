"""Unit tests for the workspace component."""

from unittest.mock import patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTabWidget

from ui.widgets.split_pane_widget import SplitPaneWidget
from ui.workspace import Workspace


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

    @patch('ui.workspace.QMessageBox.information')
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

    @patch('ui.workspace.QMessageBox.information')
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
        assert tab_widget.tabsClosable()
        assert tab_widget.isMovable()
        assert tab_widget.documentMode()
        assert tab_widget.elideMode() == Qt.ElideRight

    # Test Monkey Pattern: Always test signal connections exist
    def test_workspace_has_required_signals(self, qtbot):
        """Test Workspace defines all required signals."""
        workspace = Workspace()
        qtbot.addWidget(workspace)

        # Verify all documented signals exist
        assert hasattr(workspace, 'tab_changed'), "Workspace must have tab_changed signal"
        assert hasattr(workspace, 'tab_added'), "Workspace must have tab_added signal"
        assert hasattr(workspace, 'tab_removed'), "Workspace must have tab_removed signal"
        assert hasattr(workspace, 'active_pane_changed'), "Workspace must have active_pane_changed signal"
        assert hasattr(workspace, 'layout_changed'), "Workspace must have layout_changed signal"

        # Verify signals are actually Signal class attributes
        assert hasattr(type(workspace), 'tab_changed'), "tab_changed must be a Signal class attribute"
        assert hasattr(type(workspace), 'tab_added'), "tab_added must be a Signal class attribute"
        assert hasattr(type(workspace), 'tab_removed'), "tab_removed must be a Signal class attribute"
        assert hasattr(type(workspace), 'active_pane_changed'), "active_pane_changed must be a Signal class attribute"
        assert hasattr(type(workspace), 'layout_changed'), "layout_changed must be a Signal class attribute"

    def test_tab_added_signal_emission(self, qtbot):
        """Test tab_added signal is emitted when adding tabs."""
        workspace = Workspace()
        qtbot.addWidget(workspace)

        # Test signal emission when adding editor tab
        with qtbot.waitSignal(workspace.tab_added, timeout=1000) as blocker:
            workspace.add_editor_tab("Test Editor")

        # Verify signal was emitted with correct tab name
        assert blocker.args == ["Test Editor"], (
            f"Expected tab_added signal with args ['Test Editor'], "
            f"but got {blocker.args}"
        )

    def test_tab_added_signal_emission_terminal(self, qtbot):
        """Test tab_added signal is emitted when adding terminal tabs."""
        workspace = Workspace()
        qtbot.addWidget(workspace)

        # Test signal emission when adding terminal tab
        with qtbot.waitSignal(workspace.tab_added, timeout=1000) as blocker:
            workspace.add_terminal_tab("Test Terminal")

        # Verify signal was emitted with correct tab name
        assert blocker.args == ["Test Terminal"], (
            f"Expected tab_added signal with args ['Test Terminal'], "
            f"but got {blocker.args}"
        )

    def test_tab_removed_signal_emission(self, qtbot):
        """Test tab_removed signal is emitted when closing tabs."""
        workspace = Workspace()
        qtbot.addWidget(workspace)

        # Add a tab first
        tab_name = "Test Tab to Remove"
        index = workspace.add_editor_tab(tab_name)

        # Test signal emission when closing tab
        with qtbot.waitSignal(workspace.tab_removed, timeout=1000) as blocker:
            workspace.close_tab(index)

        # Verify signal was emitted with correct tab name
        assert blocker.args == [tab_name], (
            f"Expected tab_removed signal with args ['{tab_name}'], "
            f"but got {blocker.args}"
        )

    def test_tab_changed_signal_emission(self, qtbot):
        """Test tab_changed signal is emitted when switching tabs."""
        workspace = Workspace()
        qtbot.addWidget(workspace)

        # Add multiple tabs
        workspace.add_editor_tab("Tab 1")
        workspace.add_editor_tab("Tab 2")

        # Test signal emission when switching tabs
        with qtbot.waitSignal(workspace.tab_changed, timeout=1000) as blocker:
            workspace.tab_widget.setCurrentIndex(0)  # Switch to first tab

        # Verify signal was emitted with correct tab index
        assert blocker.args == [0], (
            f"Expected tab_changed signal with args [0], "
            f"but got {blocker.args}"
        )

    def test_active_pane_changed_signal_emission(self, qtbot):
        """Test active_pane_changed signal is emitted when pane focus changes."""
        workspace = Workspace()
        qtbot.addWidget(workspace)

        # Add a tab and get its split widget
        tab_name = "Test Tab"
        workspace.add_editor_tab(tab_name)
        split_widget = workspace.get_current_split_widget()

        # Create multiple panes in the tab
        active_pane_id = split_widget.active_pane_id
        split_widget.split_horizontal(active_pane_id)

        # Test signal emission when active pane changes
        with qtbot.waitSignal(workspace.active_pane_changed, timeout=1000) as blocker:
            # Trigger active pane change by setting a different pane as active
            all_pane_ids = split_widget.get_all_pane_ids()
            if len(all_pane_ids) > 1:
                different_pane_id = [p for p in all_pane_ids if p != active_pane_id][0]
                split_widget.set_active_pane(different_pane_id)

        # Verify signal was emitted with correct tab name and pane ID
        assert len(blocker.args) == 2, f"Expected 2 args (tab_name, pane_id), got {len(blocker.args)}"
        assert blocker.args[0] == tab_name, f"Expected tab name '{tab_name}', got '{blocker.args[0]}'"

    def test_layout_changed_signal_forwarding(self, qtbot):
        """Test layout_changed signal is forwarded from split widgets."""
        workspace = Workspace()
        qtbot.addWidget(workspace)

        # Add a tab and get its split widget
        workspace.add_editor_tab("Test Tab")
        split_widget = workspace.get_current_split_widget()

        # Test signal forwarding when split widget layout changes
        with qtbot.waitSignal(workspace.layout_changed, timeout=1000):
            # Trigger layout change in split widget
            active_pane_id = split_widget.active_pane_id
            split_widget.split_horizontal(active_pane_id)

        # Signal should have been forwarded successfully (no specific args to check)

    def test_multiple_tab_signals_during_batch_operations(self, qtbot):
        """Test multiple tab signals are emitted during batch operations."""
        workspace = Workspace()
        qtbot.addWidget(workspace)

        # Set up spies to track multiple signals
        tab_added_spy = qtbot.spy(workspace.tab_added)
        tab_changed_spy = qtbot.spy(workspace.tab_changed)

        # Perform batch tab operations
        workspace.add_editor_tab("Tab 1")
        workspace.add_terminal_tab("Tab 2")
        workspace.add_output_tab("Tab 3")

        qtbot.wait(100)  # Allow signals to be processed

        # Verify multiple tab_added signals were emitted
        assert len(tab_added_spy) == 3, f"Expected 3 tab_added signals, got {len(tab_added_spy)}"

        # Verify tab names in signal emissions
        emitted_names = [call[0] for call in tab_added_spy]
        assert "Tab 1" in emitted_names, "Tab 1 should have been added"
        assert "Tab 2" in emitted_names, "Tab 2 should have been added"
        assert "Tab 3" in emitted_names, "Tab 3 should have been added"

        # tab_changed should also have been emitted for each new current tab
        assert len(tab_changed_spy) >= 3, f"Expected at least 3 tab_changed signals, got {len(tab_changed_spy)}"

    def test_no_signal_emission_on_invalid_operations(self, qtbot):
        """Test signals are not emitted for invalid operations."""
        workspace = Workspace()
        qtbot.addWidget(workspace)

        # Set up spies to track signal emissions
        tab_removed_spy = qtbot.spy(workspace.tab_removed)
        qtbot.spy(workspace.tab_changed)

        initial_tab_count = workspace.get_tab_count()

        # Try to close invalid tab index
        workspace.close_tab(-1)  # Invalid negative index
        workspace.close_tab(999)  # Invalid high index

        qtbot.wait(100)

        # Should not have emitted tab_removed signals for invalid operations
        assert len(tab_removed_spy) == 0, (
            f"tab_removed signal should not be emitted for invalid operations, "
            f"but got {len(tab_removed_spy)} emissions"
        )

        # Tab count should remain unchanged
        assert workspace.get_tab_count() == initial_tab_count

    def test_signal_emission_during_tab_close_batch_operations(self, qtbot):
        """Test signals during batch tab closing operations."""
        workspace = Workspace()
        qtbot.addWidget(workspace)

        # Add multiple tabs
        workspace.add_editor_tab("Tab 1")
        workspace.add_editor_tab("Tab 2")
        workspace.add_editor_tab("Tab 3")
        workspace.add_editor_tab("Tab 4")

        # Set up spy for tab_removed signals
        tab_removed_spy = qtbot.spy(workspace.tab_removed)

        # Perform batch close operation
        workspace.close_tabs_to_right(1)  # Close tabs to right of index 1

        qtbot.wait(100)

        # Should have emitted tab_removed signals for closed tabs
        assert len(tab_removed_spy) >= 2, (
            f"Expected at least 2 tab_removed signals, got {len(tab_removed_spy)}"
        )

    def test_signal_connections_persist_after_state_restoration(self, qtbot):
        """Test signal connections remain valid after state save/restore."""
        # Create workspace with tabs
        workspace1 = Workspace()
        qtbot.addWidget(workspace1)
        workspace1.add_editor_tab("Persistent Tab")

        # Save state
        state = workspace1.save_state()

        # Create new workspace and restore state
        workspace2 = Workspace()
        qtbot.addWidget(workspace2)
        workspace2.restore_state(state)

        # Test that signals still work after restoration
        with qtbot.waitSignal(workspace2.tab_added, timeout=1000) as blocker:
            workspace2.add_terminal_tab("New Terminal After Restore")

        # Signal should still be emitted correctly
        assert blocker.args == ["New Terminal After Restore"], (
            f"Expected tab_added signal after restore, got {blocker.args}"
        )

    def test_signal_emission_edge_cases(self, qtbot):
        """Test signal emission in edge cases and boundary conditions."""
        workspace = Workspace()
        qtbot.addWidget(workspace)

        # Test with empty tab name
        with qtbot.waitSignal(workspace.tab_added, timeout=1000) as blocker:
            workspace.add_editor_tab("")  # Empty name

        assert blocker.args == [""], "Should emit signal even for empty tab name"

        # Test with very long tab name
        long_name = "A" * 1000
        with qtbot.waitSignal(workspace.tab_added, timeout=1000) as blocker:
            workspace.add_editor_tab(long_name)

        assert blocker.args == [long_name], "Should emit signal for very long tab names"

        # Test with special characters in name
        special_name = "Tab with 特殊字符 and émojis 🚀"
        with qtbot.waitSignal(workspace.tab_added, timeout=1000) as blocker:
            workspace.add_editor_tab(special_name)

        assert blocker.args == [special_name], "Should emit signal for tab names with special characters"
