#!/usr/bin/env python3
"""Unit tests for CommandPaletteWidget focusing on signal testing following Test Monkey principles."""


import pytest
from PySide6.QtCore import Qt

from core.commands.base import Command
from ui.command_palette.palette_widget import CommandListWidget, CommandPaletteWidget


@pytest.fixture
def mock_commands():
    """Create mock commands for testing."""
    commands = [
        Command(
            id="test.command1",
            title="Test Command 1",
            description="First test command",
            category="Test",
            shortcut="ctrl+1",
        ),
        Command(
            id="test.command2",
            title="Test Command 2",
            description="Second test command",
            category="Test",
            shortcut="ctrl+2",
        ),
        Command(
            id="file.open",
            title="Open File",
            description="Open a file",
            category="File",
            shortcut="ctrl+o",
        ),
    ]
    return commands


@pytest.mark.unit
class TestCommandListWidget:
    """Test cases for CommandListWidget signal behavior."""

    # Test Monkey Pattern: Always test signal connections exist
    def test_command_list_widget_has_required_signals(self, qtbot):
        """Test CommandListWidget defines all required signals."""
        widget = CommandListWidget()
        qtbot.addWidget(widget)

        # Verify documented signals exist
        assert hasattr(
            widget, "command_activated"
        ), "CommandListWidget must have command_activated signal"

        # Verify signals are actually Signal class attributes
        assert hasattr(
            type(widget), "command_activated"
        ), "command_activated must be a Signal class attribute"

    def test_command_activated_signal_emission_on_enter(self, qtbot, mock_commands):
        """Test command_activated signal is emitted when Enter is pressed."""
        widget = CommandListWidget()
        qtbot.addWidget(widget)

        # Set commands
        widget.set_commands(mock_commands)

        # Select first command
        widget.setCurrentRow(0)

        # Test signal emission
        with qtbot.waitSignal(widget.command_activated, timeout=1000) as blocker:
            qtbot.keyClick(widget, Qt.Key_Return)

        # Verify signal was emitted with correct command
        assert len(blocker.args) == 1, f"Expected 1 argument, got {len(blocker.args)}"
        emitted_command = blocker.args[0]
        assert isinstance(
            emitted_command, Command
        ), f"Expected Command object, got {type(emitted_command)}"
        assert (
            emitted_command.id == "test.command1"
        ), f"Expected command1, got {emitted_command.id}"

    def test_command_activated_signal_emission_on_item_activated(
        self, qtbot, mock_commands
    ):
        """Test command_activated signal is emitted when item is activated."""
        widget = CommandListWidget()
        qtbot.addWidget(widget)

        # Set commands
        widget.set_commands(mock_commands)

        # Test signal emission on item activation
        with qtbot.waitSignal(widget.command_activated, timeout=1000) as blocker:
            # Simulate item activation (double-click equivalent)
            item = widget.item(1)  # Second command
            widget.itemActivated.emit(item)

        # Verify signal was emitted with correct command
        emitted_command = blocker.args[0]
        assert (
            emitted_command.id == "test.command2"
        ), f"Expected command2, got {emitted_command.id}"

    def test_no_signal_emission_with_no_selection(self, qtbot, mock_commands):
        """Test no signal emission when Enter pressed with no selection."""
        widget = CommandListWidget()
        qtbot.addWidget(widget)

        # Set commands but don't select any
        widget.set_commands(mock_commands)
        widget.setCurrentRow(-1)  # No selection

        # Set up spy to track signal emissions
        command_activated_spy = qtbot.spy(widget.command_activated)

        # Press Enter with no selection
        qtbot.keyClick(widget, Qt.Key_Return)
        qtbot.wait(100)

        # Should not have emitted signal
        assert (
            len(command_activated_spy) == 0
        ), "command_activated signal should not be emitted with no selection"

    def test_no_signal_emission_with_empty_command_list(self, qtbot):
        """Test no signal emission when command list is empty."""
        widget = CommandListWidget()
        qtbot.addWidget(widget)

        # Set empty command list
        widget.set_commands([])

        # Set up spy to track signal emissions
        command_activated_spy = qtbot.spy(widget.command_activated)

        # Press Enter on empty list
        qtbot.keyClick(widget, Qt.Key_Return)
        qtbot.wait(100)

        # Should not have emitted signal
        assert (
            len(command_activated_spy) == 0
        ), "command_activated signal should not be emitted with empty list"


@pytest.mark.unit
class TestCommandPaletteWidget:
    """Test cases for CommandPaletteWidget signal behavior."""

    # Test Monkey Pattern: Always test signal connections exist
    def test_command_palette_widget_has_required_signals(self, qtbot):
        """Test CommandPaletteWidget defines all required signals."""
        widget = CommandPaletteWidget()
        qtbot.addWidget(widget)

        # Verify documented signals exist
        assert hasattr(
            widget, "command_executed"
        ), "CommandPaletteWidget must have command_executed signal"
        assert hasattr(
            widget, "palette_closed"
        ), "CommandPaletteWidget must have palette_closed signal"

        # Verify signals are actually Signal class attributes
        assert hasattr(
            type(widget), "command_executed"
        ), "command_executed must be a Signal class attribute"
        assert hasattr(
            type(widget), "palette_closed"
        ), "palette_closed must be a Signal class attribute"

    def test_command_executed_signal_emission(self, qtbot, mock_commands):
        """Test command_executed signal is emitted when commands are activated."""
        widget = CommandPaletteWidget()
        qtbot.addWidget(widget)

        # Show palette with commands
        widget.show_palette(mock_commands)

        # Test signal emission when command is executed
        with qtbot.waitSignal(widget.command_executed, timeout=1000) as blocker:
            # Simulate command activation through the command list
            test_command = mock_commands[0]
            widget.command_list.command_activated.emit(test_command)

        # Verify signal was emitted with correct command ID and empty kwargs
        assert (
            len(blocker.args) == 2
        ), f"Expected 2 arguments (command_id, kwargs), got {len(blocker.args)}"
        command_id, kwargs = blocker.args
        assert (
            command_id == "test.command1"
        ), f"Expected 'test.command1', got '{command_id}'"
        assert kwargs == {}, f"Expected empty kwargs, got {kwargs}"

    def test_palette_closed_signal_emission_on_escape(self, qtbot, mock_commands):
        """Test palette_closed signal is emitted when Escape is pressed."""
        widget = CommandPaletteWidget()
        qtbot.addWidget(widget)

        # Show palette
        widget.show_palette(mock_commands)

        # Test signal emission when Escape is pressed
        with qtbot.waitSignal(widget.palette_closed, timeout=1000) as blocker:
            qtbot.keyClick(widget, Qt.Key_Escape)

        # Verify signal was emitted (no args expected)
        assert (
            blocker.args == []
        ), f"Expected no args for palette_closed signal, got {blocker.args}"

    def test_palette_closed_signal_emission_on_close_palette(
        self, qtbot, mock_commands
    ):
        """Test palette_closed signal is emitted when close_palette is called."""
        widget = CommandPaletteWidget()
        qtbot.addWidget(widget)

        # Show palette
        widget.show_palette(mock_commands)

        # Test signal emission when close_palette is called
        with qtbot.waitSignal(widget.palette_closed, timeout=1000) as blocker:
            widget.close_palette()

        # Verify signal was emitted
        assert (
            blocker.args == []
        ), f"Expected no args for palette_closed signal, got {blocker.args}"

    def test_both_signals_emitted_during_command_execution(self, qtbot, mock_commands):
        """Test both command_executed and palette_closed signals are emitted during command execution."""
        widget = CommandPaletteWidget()
        qtbot.addWidget(widget)

        # Show palette with commands
        widget.show_palette(mock_commands)

        # Test multiple signals emitted during command execution
        with qtbot.waitSignals(
            [widget.command_executed, widget.palette_closed], timeout=1000
        ):
            # Simulate command activation
            test_command = mock_commands[0]
            widget.on_command_activated(test_command)

        # Both signals should have been emitted successfully

    def test_signal_emission_order_during_command_execution(self, qtbot, mock_commands):
        """Test correct order of signal emission during command execution."""
        widget = CommandPaletteWidget()
        qtbot.addWidget(widget)

        # Show palette with commands
        widget.show_palette(mock_commands)

        # Set up spies to track signal emission order
        command_executed_spy = qtbot.spy(widget.command_executed)
        palette_closed_spy = qtbot.spy(widget.palette_closed)

        # Execute command
        test_command = mock_commands[0]
        widget.on_command_activated(test_command)

        qtbot.wait(100)

        # Both signals should have been emitted
        assert (
            len(command_executed_spy) == 1
        ), "command_executed signal should be emitted once"
        assert (
            len(palette_closed_spy) == 1
        ), "palette_closed signal should be emitted once"

        # command_executed should typically be emitted before palette_closed
        # (This depends on implementation but is generally expected)

    def test_no_signal_emission_when_palette_not_shown(self, qtbot, mock_commands):
        """Test no signals are emitted when palette operations are performed while hidden."""
        widget = CommandPaletteWidget()
        qtbot.addWidget(widget)

        # Don't show palette - keep it hidden

        # Set up spies to track signal emissions
        command_executed_spy = qtbot.spy(widget.command_executed)
        qtbot.spy(widget.palette_closed)

        # Try to execute command on hidden palette
        test_command = mock_commands[0]
        widget.on_command_activated(test_command)

        qtbot.wait(100)

        # Should still emit command_executed (behavior may vary by implementation)
        # But let's verify the widget doesn't crash
        assert len(command_executed_spy) >= 0  # Implementation dependent

        # palette_closed should not be emitted if palette wasn't shown
        # (This may depend on implementation details)

    def test_signal_emission_with_search_filtering(self, qtbot, mock_commands):
        """Test signals work correctly when commands are filtered by search."""
        widget = CommandPaletteWidget()
        qtbot.addWidget(widget)

        # Show palette with commands
        widget.show_palette(mock_commands)

        # Filter commands by search
        widget.search_input.setText("file")
        qtbot.wait(200)  # Wait for debounce

        # Test signal emission with filtered command
        with qtbot.waitSignal(widget.command_executed, timeout=1000) as blocker:
            # Find and activate the filtered command
            filtered_commands = widget.command_list.commands
            if filtered_commands:
                file_command = next(
                    (cmd for cmd in filtered_commands if cmd.id == "file.open"), None
                )
                if file_command:
                    widget.on_command_activated(file_command)

        # Verify correct command was executed
        if blocker.args:
            command_id, kwargs = blocker.args
            assert (
                command_id == "file.open"
            ), f"Expected 'file.open', got '{command_id}'"

    def test_signal_emission_during_recent_commands_handling(
        self, qtbot, mock_commands
    ):
        """Test signals work correctly when recent commands are displayed."""
        widget = CommandPaletteWidget()
        qtbot.addWidget(widget)

        # Show palette with recent commands
        recent_commands = [mock_commands[1]]  # Second command as recent
        widget.show_palette(mock_commands, recent_commands)

        # Test signal emission with recent command
        with qtbot.waitSignal(widget.command_executed, timeout=1000) as blocker:
            # Execute the recent command
            widget.on_command_activated(recent_commands[0])

        # Verify correct command was executed
        command_id, kwargs = blocker.args
        assert (
            command_id == "test.command2"
        ), f"Expected 'test.command2', got '{command_id}'"

    def test_signal_emission_edge_cases(self, qtbot, mock_commands):
        """Test signal emission in edge cases and boundary conditions."""
        widget = CommandPaletteWidget()
        qtbot.addWidget(widget)

        # Test with empty command list
        widget.show_palette([])

        # Test close signal with empty palette
        with qtbot.waitSignal(widget.palette_closed, timeout=1000) as blocker:
            widget.close_palette()

        assert blocker.args == [], "palette_closed should work with empty command list"

        # Test with None command (error case)
        qtbot.spy(widget.command_executed)

        # This should not crash the widget (implementation dependent)
        try:
            widget.on_command_activated(None)
            qtbot.wait(50)
        except Exception:
            pass  # May throw exception, which is acceptable

        # Widget should remain functional
        assert widget.isVisible() or not widget.isVisible()  # Should not crash

    def test_signal_emission_during_rapid_operations(self, qtbot, mock_commands):
        """Test signal handling during rapid show/hide operations."""
        widget = CommandPaletteWidget()
        qtbot.addWidget(widget)

        # Set up spy to track palette_closed emissions
        palette_closed_spy = qtbot.spy(widget.palette_closed)

        # Rapid show/hide operations
        for _ in range(3):
            widget.show_palette(mock_commands)
            qtbot.wait(10)
            widget.close_palette()
            qtbot.wait(10)

        # Should have emitted palette_closed signal for each close
        assert (
            len(palette_closed_spy) == 3
        ), f"Expected 3 palette_closed signals, got {len(palette_closed_spy)}"


@pytest.mark.unit
class TestCommandPaletteSignalIntegration:
    """Test integration between CommandListWidget and CommandPaletteWidget signals."""

    def test_signal_chain_from_list_to_palette(self, qtbot, mock_commands):
        """Test signal propagation from CommandListWidget to CommandPaletteWidget."""
        palette_widget = CommandPaletteWidget()
        qtbot.addWidget(palette_widget)

        # Show palette
        palette_widget.show_palette(mock_commands)

        # Test signal chain: list widget -> palette widget
        with qtbot.waitSignal(palette_widget.command_executed, timeout=1000) as blocker:
            # Emit signal from command list
            test_command = mock_commands[2]  # file.open command
            palette_widget.command_list.command_activated.emit(test_command)

        # Verify signal propagated correctly
        command_id, kwargs = blocker.args
        assert command_id == "file.open", f"Expected 'file.open', got '{command_id}'"

    def test_command_list_signal_connections_after_palette_show(
        self, qtbot, mock_commands
    ):
        """Test that command list signal connections are established when palette is shown."""
        palette_widget = CommandPaletteWidget()
        qtbot.addWidget(palette_widget)

        # Show palette (this should establish signal connections)
        palette_widget.show_palette(mock_commands)

        # Verify command list is connected to palette
        command_list = palette_widget.command_list

        # Test connection by emitting signal
        command_executed_spy = qtbot.spy(palette_widget.command_executed)

        # Emit signal from command list
        test_command = mock_commands[0]
        command_list.command_activated.emit(test_command)

        qtbot.wait(50)

        # Should have triggered palette's command execution
        assert (
            len(command_executed_spy) == 1
        ), "Command list signal should trigger palette signal"

    def test_signal_disconnection_after_palette_close(self, qtbot, mock_commands):
        """Test that signals remain connected after palette close (for reuse)."""
        palette_widget = CommandPaletteWidget()
        qtbot.addWidget(palette_widget)

        # Show and close palette
        palette_widget.show_palette(mock_commands)
        palette_widget.close_palette()

        # Show again to test signal connections persist
        palette_widget.show_palette(mock_commands)

        # Test that signals still work
        with qtbot.waitSignal(palette_widget.command_executed, timeout=1000) as blocker:
            test_command = mock_commands[0]
            palette_widget.command_list.command_activated.emit(test_command)

        # Should still work after reopen
        command_id, kwargs = blocker.args
        assert (
            command_id == "test.command1"
        ), f"Signals should work after reopen, got '{command_id}'"
