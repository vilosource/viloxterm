#!/usr/bin/env python3
"""
GUI tests for keyboard shortcuts, particularly testing the new Ctrl+N terminal tab functionality
and verifying no shortcut conflicts exist.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from viloapp.core.commands.registry import command_registry
from viloapp.ui.main_window import MainWindow
from viloapp.ui.widgets.widget_registry import WidgetType


@pytest.mark.gui
class TestKeyboardShortcutsGUI:
    """Test keyboard shortcuts in the GUI."""

    def test_ctrl_n_creates_terminal_tab(self, qtbot, main_window_fixture):
        """Test that Ctrl+N creates a terminal tab, not an editor tab."""
        window = main_window_fixture
        qtbot.addWidget(window)
        window.show()
        qtbot.waitForWindowShown(window)

        # Get initial tab count
        initial_tab_count = window.workspace.tab_widget.count()

        # Press Ctrl+N
        QTest.keyClick(window, Qt.Key_N, Qt.ControlModifier)
        qtbot.wait(100)

        # Check that a new tab was created
        assert window.workspace.tab_widget.count() == initial_tab_count + 1

        # Get the widget in the new tab
        new_tab_index = window.workspace.tab_widget.count() - 1
        new_tab_widget = window.workspace.tab_widget.widget(new_tab_index)

        # Check if it's a split pane widget containing a terminal
        if hasattr(new_tab_widget, "model"):
            # Get the root node of the split pane
            root = new_tab_widget.model.root
            if hasattr(root, "widget"):
                # Verify it's a terminal widget
                assert (
                    root.widget.widget_type == WidgetType.TERMINAL
                ), f"Expected TERMINAL widget, got {root.widget.widget_type}"

    def test_ctrl_shift_n_creates_editor_tab(self, qtbot, main_window_fixture):
        """Test that Ctrl+Shift+N creates an editor tab."""
        window = main_window_fixture
        qtbot.addWidget(window)
        window.show()
        qtbot.waitForWindowShown(window)

        # Get initial tab count
        initial_tab_count = window.workspace.tab_widget.count()

        # Press Ctrl+Shift+N
        QTest.keyClick(window, Qt.Key_N, Qt.ControlModifier | Qt.ShiftModifier)
        qtbot.wait(100)

        # Check that a new tab was created
        assert window.workspace.tab_widget.count() == initial_tab_count + 1

        # Get the widget in the new tab
        new_tab_index = window.workspace.tab_widget.count() - 1
        new_tab_widget = window.workspace.tab_widget.widget(new_tab_index)

        # Check if it's a split pane widget containing an editor
        if hasattr(new_tab_widget, "model"):
            # Get the root node of the split pane
            root = new_tab_widget.model.root
            if hasattr(root, "widget"):
                # Verify it's a text editor widget
                assert (
                    root.widget.widget_type == WidgetType.TEXT_EDITOR
                ), f"Expected TEXT_EDITOR widget, got {root.widget.widget_type}"

    def test_ctrl_backtick_creates_terminal_tab(self, qtbot, main_window_fixture):
        """Test that Ctrl+` also creates a terminal tab (alternative shortcut)."""
        window = main_window_fixture
        qtbot.addWidget(window)
        window.show()
        qtbot.waitForWindowShown(window)

        # Get initial tab count
        initial_tab_count = window.workspace.tab_widget.count()

        # Press Ctrl+`
        QTest.keyClick(window, Qt.Key_QuoteLeft, Qt.ControlModifier)
        qtbot.wait(100)

        # Check that a new tab was created
        assert window.workspace.tab_widget.count() == initial_tab_count + 1

        # Get the widget in the new tab
        new_tab_index = window.workspace.tab_widget.count() - 1
        new_tab_widget = window.workspace.tab_widget.widget(new_tab_index)

        # Check if it's a split pane widget containing a terminal
        if hasattr(new_tab_widget, "model"):
            # Get the root node of the split pane
            root = new_tab_widget.model.root
            if hasattr(root, "widget"):
                # Verify it's a terminal widget
                assert (
                    root.widget.widget_type == WidgetType.TERMINAL
                ), f"Expected TERMINAL widget, got {root.widget.widget_type}"

    def test_no_shortcut_conflicts(self):
        """Test that there are no conflicting keyboard shortcuts."""
        # Get all registered commands
        commands = command_registry.get_all_commands()

        # Build a map of shortcuts to commands
        shortcut_map = {}
        conflicts = []

        for cmd in commands:
            if hasattr(cmd, "shortcut") and cmd.shortcut:
                # Normalize the shortcut to lowercase for comparison
                shortcut = cmd.shortcut.lower()

                if shortcut in shortcut_map:
                    # Found a conflict
                    conflicts.append(
                        {
                            "shortcut": shortcut,
                            "command1": shortcut_map[shortcut],
                            "command2": cmd.id,
                        }
                    )
                else:
                    shortcut_map[shortcut] = cmd.id

        # Assert no conflicts found
        assert len(conflicts) == 0, f"Found shortcut conflicts: {conflicts}"

    def test_shortcut_case_consistency(self):
        """Test that all shortcuts use consistent lowercase formatting."""
        commands = command_registry.get_all_commands()

        inconsistent = []
        for cmd in commands:
            if hasattr(cmd, "shortcut") and cmd.shortcut:
                # Check if shortcut contains uppercase letters (except for key names)
                # Allow uppercase only for actual key names like Key_A, Key_B, etc.
                parts = cmd.shortcut.split("+")
                for part in parts:
                    if part and part not in ["ctrl", "alt", "shift", "cmd", "meta"]:
                        # Check if it's a function key or special key
                        if not part.startswith("f") and part not in [
                            "tab",
                            "escape",
                            "space",
                            "enter",
                            "return",
                            "backspace",
                            "delete",
                            "insert",
                            "home",
                            "end",
                            "pageup",
                            "pagedown",
                            "up",
                            "down",
                            "left",
                            "right",
                        ]:
                            # Regular keys should be lowercase
                            if part != part.lower():
                                inconsistent.append(
                                    {
                                        "command": cmd.id,
                                        "shortcut": cmd.shortcut,
                                        "issue": f"Part '{part}' should be lowercase",
                                    }
                                )

        assert len(inconsistent) == 0, f"Found inconsistent shortcut formatting: {inconsistent}"

    def test_ctrl_comma_settings_shortcut(self, qtbot, main_window_fixture):
        """Test that Ctrl+, opens settings (not conflicting with view.showSettings)."""
        window = main_window_fixture
        qtbot.addWidget(window)
        window.show()
        qtbot.waitForWindowShown(window)

        # Verify only one command is registered for ctrl+,
        # Note: KeyboardService doesn't use singleton pattern, so we skip this check

        # Get the command for ctrl+,
        # Note: This assumes the shortcut manager has a method to lookup commands by shortcut
        # If not, we can check via the registry
        commands_with_ctrl_comma = []
        for cmd in command_registry.get_all_commands():
            if hasattr(cmd, "shortcut") and cmd.shortcut and cmd.shortcut.lower() == "ctrl+,":
                commands_with_ctrl_comma.append(cmd.id)

        # Should only have one command with this shortcut
        assert (
            len(commands_with_ctrl_comma) == 1
        ), f"Expected 1 command with ctrl+,, found {len(commands_with_ctrl_comma)}: {commands_with_ctrl_comma}"

        # Should be the settings command
        assert (
            commands_with_ctrl_comma[0] == "settings.openSettings"
        ), f"Expected 'settings.openSettings' to have ctrl+,, but found '{commands_with_ctrl_comma[0]}'"

    def test_ctrl_w_closes_tab(self, qtbot, main_window_fixture):
        """Test that Ctrl+W closes the current tab."""
        window = main_window_fixture
        qtbot.addWidget(window)
        window.show()
        qtbot.waitForWindowShown(window)

        # Create a few tabs first
        QTest.keyClick(window, Qt.Key_N, Qt.ControlModifier)  # Create terminal tab
        qtbot.wait(100)
        QTest.keyClick(window, Qt.Key_N, Qt.ControlModifier | Qt.ShiftModifier)  # Create editor tab
        qtbot.wait(100)

        # Should have 3 tabs now (initial + 2 new)
        assert window.workspace.tab_widget.count() == 3

        # Press Ctrl+W to close current tab
        QTest.keyClick(window, Qt.Key_W, Qt.ControlModifier)
        qtbot.wait(100)

        # Should have 2 tabs now
        assert window.workspace.tab_widget.count() == 2

        # Press Ctrl+W again
        QTest.keyClick(window, Qt.Key_W, Qt.ControlModifier)
        qtbot.wait(100)

        # Should have 1 tab now
        assert window.workspace.tab_widget.count() == 1

    def test_ctrl_w_doesnt_close_last_tab(self, qtbot, main_window_fixture):
        """Test that Ctrl+W doesn't close the last remaining tab."""
        window = main_window_fixture
        qtbot.addWidget(window)
        window.show()
        qtbot.waitForWindowShown(window)

        # Close tabs until only one remains
        while window.workspace.tab_widget.count() > 1:
            QTest.keyClick(window, Qt.Key_W, Qt.ControlModifier)
            qtbot.wait(100)

        # Should have exactly 1 tab
        assert window.workspace.tab_widget.count() == 1

        # Try to close the last tab
        QTest.keyClick(window, Qt.Key_W, Qt.ControlModifier)
        qtbot.wait(100)

        # Should still have 1 tab (last tab shouldn't close)
        assert (
            window.workspace.tab_widget.count() == 1
        ), "The last tab should not be closeable with Ctrl+W"


@pytest.fixture
def main_window_fixture(qtbot):
    """Create a MainWindow instance for testing."""
    # Create the main window
    window = MainWindow()

    # Make sure it's properly initialized
    qtbot.addWidget(window)

    # Return the window
    yield window

    # Cleanup
    window.close()
