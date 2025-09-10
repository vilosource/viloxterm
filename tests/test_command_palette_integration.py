#!/usr/bin/env python3
"""
Integration tests for command palette functionality.

Tests the complete flow from keyboard shortcut to command execution.
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeyEvent
from PySide6.QtTest import QTest

from ui.main_window import MainWindow
from core.commands.registry import command_registry
from core.context.manager import context_manager
from core.context.keys import ContextKey


@pytest.fixture
def main_window(qtbot):
    """Create main window for testing."""
    window = MainWindow()
    window.show()
    qtbot.addWidget(window)
    qtbot.waitForWindowShown(window)
    return window


def test_command_palette_controller_exists(main_window):
    """Test that command palette controller is initialized."""
    assert hasattr(main_window, 'command_palette_controller')
    assert main_window.command_palette_controller is not None


def test_command_palette_show_command_registered():
    """Test that commandPalette.show is registered."""
    cmd = command_registry.get_command('commandPalette.show')
    assert cmd is not None
    assert cmd.shortcut == 'ctrl+shift+p'
    assert cmd.title == 'Show Command Palette'


def test_keyboard_service_has_palette_shortcut(main_window):
    """Test that keyboard service has ctrl+shift+p registered."""
    # Check that keyboard service exists
    assert hasattr(main_window, 'keyboard_service')
    
    # Check shortcuts are registered
    registry = main_window.keyboard_service._registry
    
    # Look for commandPalette.show in registered shortcuts
    found_palette_shortcut = False
    for shortcuts_list in registry._shortcuts.values():
        for shortcut in shortcuts_list:
            if shortcut.command_id == 'commandPalette.show':
                found_palette_shortcut = True
                break
    
    assert found_palette_shortcut, "commandPalette.show shortcut not found in keyboard registry"


def test_execute_show_palette_command(main_window, qtbot):
    """Test executing the show palette command directly."""
    # Execute command
    result = main_window.execute_command('commandPalette.show')
    
    # Check result
    assert result.success is True
    
    # Give UI time to update
    qtbot.wait(100)
    
    # Check palette is visible
    assert main_window.command_palette_controller.is_visible()
    
    # Check context is updated
    context = context_manager.get(ContextKey.COMMAND_PALETTE_VISIBLE)
    assert context is True
    
    # Hide palette
    main_window.command_palette_controller.hide_palette()
    qtbot.wait(100)
    
    # Check palette is hidden
    assert not main_window.command_palette_controller.is_visible()
    
    # Check context is updated
    context = context_manager.get(ContextKey.COMMAND_PALETTE_VISIBLE)
    assert context is False


def test_keyboard_shortcut_opens_palette(main_window, qtbot):
    """Test that Ctrl+Shift+P opens the command palette."""
    # Ensure palette is hidden initially
    main_window.command_palette_controller.hide_palette()
    qtbot.wait(100)
    assert not main_window.command_palette_controller.is_visible()
    
    # Simulate Ctrl+Shift+P key press
    QTest.keyClick(
        main_window,
        Qt.Key_P,
        Qt.ControlModifier | Qt.ShiftModifier
    )
    
    # Give UI time to update
    qtbot.wait(200)
    
    # Check palette is visible
    assert main_window.command_palette_controller.is_visible()
    
    # Check context is updated
    context = context_manager.get(ContextKey.COMMAND_PALETTE_VISIBLE)
    assert context is True
    
    # Clean up - hide palette
    main_window.command_palette_controller.hide_palette()


def test_escape_closes_palette(main_window, qtbot):
    """Test that Escape closes the command palette."""
    # Open palette first
    main_window.execute_command('commandPalette.show')
    qtbot.wait(100)
    assert main_window.command_palette_controller.is_visible()
    
    # Get the palette widget
    palette_widget = main_window.command_palette_controller.palette_widget
    
    # Simulate Escape key press on the palette
    QTest.keyClick(palette_widget, Qt.Key_Escape)
    
    # Give UI time to update
    qtbot.wait(100)
    
    # Check palette is hidden
    assert not main_window.command_palette_controller.is_visible()
    
    # Check context is updated
    context = context_manager.get(ContextKey.COMMAND_PALETTE_VISIBLE)
    assert context is False


def test_command_filtering_by_context(main_window, qtbot):
    """Test that commands are filtered based on context."""
    # Open palette
    main_window.execute_command('commandPalette.show')
    qtbot.wait(100)
    
    # Get available commands
    palette_widget = main_window.command_palette_controller.palette_widget
    commands = palette_widget.command_list.commands
    
    # Check that commandPalette.show is NOT in the list (when="!commandPaletteVisible")
    show_cmd_in_list = any(cmd.id == 'commandPalette.show' for cmd in commands)
    assert not show_cmd_in_list, "commandPalette.show should be filtered out when palette is visible"
    
    # Check that commandPalette.hide IS in the list (when="commandPaletteVisible")
    hide_cmd_in_list = any(cmd.id == 'commandPalette.hide' for cmd in commands)
    assert hide_cmd_in_list, "commandPalette.hide should be available when palette is visible"
    
    # Clean up
    main_window.command_palette_controller.hide_palette()


def test_command_search(main_window, qtbot):
    """Test searching for commands in the palette."""
    # Open palette
    main_window.execute_command('commandPalette.show')
    qtbot.wait(100)
    
    palette_widget = main_window.command_palette_controller.palette_widget
    
    # Type search query
    palette_widget.search_input.setText("theme")
    qtbot.wait(200)  # Wait for debounce
    
    # Check filtered results
    commands = palette_widget.command_list.commands
    
    # Should have theme-related commands
    theme_commands = [cmd for cmd in commands if 'theme' in cmd.title.lower()]
    assert len(theme_commands) > 0, "Should find theme-related commands"
    
    # Clean up
    main_window.command_palette_controller.hide_palette()


def test_command_execution_from_palette(main_window, qtbot):
    """Test executing a command from the palette."""
    # Get initial theme
    from core.context.manager import context_manager
    initial_theme = context_manager.get('theme')
    
    # Open palette
    main_window.execute_command('commandPalette.show')
    qtbot.wait(100)
    
    palette_widget = main_window.command_palette_controller.palette_widget
    
    # Search for theme toggle command
    palette_widget.search_input.setText("toggle theme")
    qtbot.wait(200)  # Wait for debounce
    
    # Select first result and execute
    if palette_widget.command_list.commands:
        palette_widget.command_list.setCurrentRow(0)
        
        # Simulate Enter key to execute
        QTest.keyClick(palette_widget.command_list, Qt.Key_Return)
        qtbot.wait(100)
        
        # Check palette is closed after execution
        assert not main_window.command_palette_controller.is_visible()
        
        # Check theme changed
        new_theme = context_manager.get('theme')
        assert new_theme != initial_theme, "Theme should have changed"


def test_all_commands_have_unique_ids():
    """Test that all registered commands have unique IDs."""
    all_commands = command_registry.get_all_commands()
    command_ids = [cmd.id for cmd in all_commands]
    
    # Check for duplicates
    assert len(command_ids) == len(set(command_ids)), "Found duplicate command IDs"


def test_shortcut_conflicts_resolved():
    """Test that shortcut conflicts have been resolved."""
    # Known resolved conflicts
    resolved_conflicts = [
        ('ctrl+t', ['view.toggleTheme']),  # settings.toggleTheme removed
        ('escape', ['commandPalette.hide']),  # workbench.action.focusActivePane removed
    ]
    
    all_commands = command_registry.get_all_commands()
    
    for shortcut, expected_commands in resolved_conflicts:
        commands_with_shortcut = [
            cmd.id for cmd in all_commands 
            if cmd.shortcut == shortcut
        ]
        assert commands_with_shortcut == expected_commands, \
            f"Shortcut {shortcut} should only be assigned to {expected_commands}, found {commands_with_shortcut}"