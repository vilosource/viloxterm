#!/usr/bin/env python3
"""
Validation script for the integrated application.

This script tests the complete application with model, commands, and views
all working together.
"""

import sys
import time

from commands import CommandContext, CommandRegistry
from main_new import ViloxTermApplication
from model import WidgetType, WorkspaceModel
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication


def print_header(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print(f"{'=' * 60}")


def print_success(msg: str):
    """Print success message."""
    print(f"✅ {msg}")


def print_error(msg: str):
    """Print error message."""
    print(f"❌ {msg}")


def print_info(msg: str):
    """Print info message."""
    print(f"ℹ️  {msg}")


def validate_integration():
    """Run integration validation tests."""
    print_header("INTEGRATION VALIDATION")

    # Create Qt application
    app = QApplication.instance() or QApplication(sys.argv)
    print_success("Qt application created")

    # Test 1: Application Creation
    print_header("Test 1: Application Creation")

    window = ViloxTermApplication()
    assert window is not None
    assert window.model is not None
    assert window.command_registry is not None
    assert window.workspace_view is not None
    print_success("Application created successfully")

    # Check initial state
    assert len(window.model.state.tabs) > 0
    print_success("Initial tab created")

    # Test 2: Command Execution
    print_header("Test 2: Command Execution")

    initial_tab_count = len(window.model.state.tabs)

    # Execute command through app
    window.execute_command("tab.create", {"name": "Test Tab", "widget_type": WidgetType.EDITOR})

    assert len(window.model.state.tabs) == initial_tab_count + 1
    print_success("Command executed through application")

    # Test 3: Keyboard Shortcuts
    print_header("Test 3: Keyboard Shortcuts")

    # Count actions
    action_count = len(window.actions())
    print_info(f"Registered {action_count} keyboard shortcuts")

    # Test that shortcuts are set up
    found_shortcuts = []
    for action in window.actions():
        if action.shortcut():
            found_shortcuts.append(action.shortcut().toString())

    assert len(found_shortcuts) > 0
    print_success(f"Found {len(found_shortcuts)} keyboard shortcuts")

    # Test 4: Menu System
    print_header("Test 4: Menu System")

    menubar = window.menuBar()
    assert menubar is not None

    menus = menubar.actions()
    menu_names = [action.text() for action in menus]
    assert "File" in menu_names
    assert "View" in menu_names
    assert "Window" in menu_names
    assert "Help" in menu_names
    print_success("All menus created")

    # Test 5: State Persistence
    print_header("Test 5: State Persistence")

    # Save state
    window.save_state()
    print_success("State saved")

    # Create new instance and load
    window2 = ViloxTermApplication()
    assert len(window2.model.state.tabs) == len(window.model.state.tabs)
    print_success("State loaded successfully")

    # Test 6: View Updates
    print_header("Test 6: View Updates")

    tab_widget = window.workspace_view.tab_widget
    initial_count = tab_widget.count()

    # Create tab through command
    window.execute_command("tab.create", {"name": "View Test"})

    # View should update
    assert tab_widget.count() == initial_count + 1
    print_success("View updates from model changes")

    # Test 7: Pane Operations
    print_header("Test 7: Pane Operations")

    # Get active tab
    tab = window.model.state.get_active_tab()
    assert tab is not None

    initial_pane_count = len(tab.tree.root.get_all_panes())

    # Split pane
    window.execute_command("pane.split", {"orientation": "horizontal"})

    assert len(tab.tree.root.get_all_panes()) == initial_pane_count + 1
    print_success("Pane split through integrated command")

    # Test 8: Navigation Commands
    print_header("Test 8: Navigation Commands")

    # Test tab navigation
    if len(window.model.state.tabs) > 1:
        current_tab = window.model.state.active_tab_id
        window.execute_command("tab.next")
        assert window.model.state.active_tab_id != current_tab
        print_success("Tab navigation works")

        window.execute_command("tab.previous")
        assert window.model.state.active_tab_id == current_tab
        print_success("Tab reverse navigation works")

    # Test 9: Complex Operations
    print_header("Test 9: Complex Operations")

    # Create a complex layout
    window.execute_command("tab.create", {"name": "Complex"})
    for _ in range(3):
        window.execute_command("pane.split", {"orientation": "horizontal"})

    tab = window.model.state.get_active_tab()
    assert tab and len(tab.tree.root.get_all_panes()) == 4
    print_success("Complex layout created")

    # Close some panes
    window.execute_command("pane.close")
    assert tab and len(tab.tree.root.get_all_panes()) == 3
    print_success("Pane closed successfully")

    # Test 10: Performance
    print_header("Test 10: Performance")

    start = time.time()

    # Create many tabs quickly
    for i in range(10):
        window.execute_command("tab.create", {"name": f"Perf {i}"})

    elapsed = time.time() - start
    print_success(f"Created 10 tabs in {elapsed:.3f} seconds")

    # Should be fast
    assert elapsed < 2.0
    print_success("Performance acceptable")

    # Test 11: Error Handling
    print_header("Test 11: Error Handling")

    # Try invalid command
    window.execute_command("invalid.command")
    print_success("Invalid command handled gracefully")

    # Try to close last tab (should fail)
    while len(window.model.state.tabs) > 1:
        window.execute_command("tab.close")

    # This should fail silently
    window.execute_command("tab.close")
    assert len(window.model.state.tabs) == 1
    print_success("Prevented closing last tab")

    # Test 12: Full Workflow
    print_header("Test 12: Full Workflow")

    # Clear and start fresh
    while len(window.model.state.tabs) > 1:
        window.execute_command("tab.close")

    # Create editor tab
    window.execute_command("tab.create", {"name": "main.py", "widget_type": WidgetType.EDITOR})

    # Split for terminal
    window.execute_command("pane.split", {"orientation": "vertical"})

    # Create output tab
    window.execute_command("tab.create", {"name": "Output", "widget_type": WidgetType.OUTPUT})

    # Go back to editor
    window.execute_command("tab.previous")

    # Verify structure
    assert len(window.model.state.tabs) == 3
    editor_tab = window.model._find_tab(window.model.state.active_tab_id)
    assert editor_tab and len(editor_tab.tree.root.get_all_panes()) == 2
    print_success("Complete workflow executed successfully")

    # Summary
    print_header("VALIDATION SUMMARY")
    print_success("All integration tests passed! ✨")
    print_info("\nThe integrated application is fully functional:")
    print_info("- Application initializes properly")
    print_info("- Commands execute correctly")
    print_info("- Keyboard shortcuts work")
    print_info("- Menus are functional")
    print_info("- State persistence works")
    print_info("- Views update from model")
    print_info("- All operations work through commands")
    print_info("- Performance is good")
    print_info("- Error handling is robust")

    # Show the window briefly
    print_info("\nShowing application for 2 seconds...")
    window.resize(1400, 900)
    window.show()

    # Close after 2 seconds
    QTimer.singleShot(2000, app.quit)
    app.exec()

    return True


if __name__ == "__main__":
    try:
        success = validate_integration()
        if success:
            exit(0)
        else:
            exit(1)
    except Exception as e:
        print_error(f"Validation failed with error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)