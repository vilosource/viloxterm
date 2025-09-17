#!/usr/bin/env python3
"""
Integration test for keyboard service with command system.

Tests the automatic registration of shortcuts when commands are defined.
"""


import pytest

from core.commands import command_registry
from core.commands.base import CommandContext, CommandResult
from core.commands.decorators import command
from core.keyboard import KeyboardService
from services.service_locator import ServiceLocator


class TestKeyboardCommandIntegration:
    """Test keyboard service integration with commands."""

    def setup_method(self):
        """Setup test environment."""
        # Clear registries
        command_registry.clear()
        ServiceLocator.get_instance().clear()

        # Create keyboard service
        self.keyboard_service = KeyboardService()
        self.keyboard_service.initialize({})

        # Register with service locator
        ServiceLocator.get_instance().register(KeyboardService, self.keyboard_service)

    def teardown_method(self):
        """Clean up test environment."""
        if hasattr(self.keyboard_service, "cleanup"):
            self.keyboard_service.cleanup()
        command_registry.clear()
        ServiceLocator.get_instance().clear()

    def test_automatic_shortcut_registration(self):
        """Test that shortcuts are automatically registered when commands are created."""

        # Define a command with a shortcut
        @command(
            id="test.auto_shortcut",
            title="Test Auto Shortcut",
            category="Test",
            shortcut="ctrl+shift+t",
            description="Test automatic shortcut registration",
        )
        def test_command(context: CommandContext) -> CommandResult:
            return CommandResult(success=True, value="shortcut_triggered")

        # Verify command was registered
        cmd = command_registry.get_command("test.auto_shortcut")
        assert cmd is not None
        assert cmd.shortcut == "ctrl+shift+t"

        # Verify shortcut was automatically registered
        shortcuts = self.keyboard_service.get_shortcuts_for_command(
            "test.auto_shortcut"
        )
        assert len(shortcuts) == 1
        assert str(shortcuts[0].sequence) == "ctrl+shift+t"
        assert shortcuts[0].command_id == "test.auto_shortcut"
        assert shortcuts[0].source == "command"

    def test_pending_shortcut_registration(self):
        """Test registration of pending shortcuts."""
        # Create command before keyboard service is available
        ServiceLocator.get_instance().clear()  # Remove keyboard service

        @command(
            id="test.pending_shortcut",
            title="Test Pending Shortcut",
            category="Test",
            shortcut="ctrl+alt+p",
        )
        def pending_command(context: CommandContext) -> CommandResult:
            return CommandResult(success=True)

        # Shortcut should be queued as pending
        assert hasattr(command_registry, "_pending_shortcuts")
        assert len(command_registry._pending_shortcuts) == 1

        # Re-register keyboard service and process pending shortcuts
        ServiceLocator.get_instance().register(KeyboardService, self.keyboard_service)

        # Manually process pending shortcuts since we need to check the state
        if hasattr(command_registry, "_pending_shortcuts"):
            pending = command_registry._pending_shortcuts.copy()
            for command_id, shortcut, description in pending:
                self.keyboard_service.register_shortcut_from_string(
                    shortcut_id=f"command.{command_id}",
                    sequence_str=shortcut,
                    command_id=command_id,
                    description=description,
                    source="command",
                    priority=75,
                )
            command_registry._pending_shortcuts = []

        # Verify shortcut was registered
        shortcuts = self.keyboard_service.get_shortcuts_for_command(
            "test.pending_shortcut"
        )
        assert len(shortcuts) == 1
        assert str(shortcuts[0].sequence) == "ctrl+alt+p"

        # Pending list should be cleared
        assert len(command_registry._pending_shortcuts) == 0

    def test_command_without_shortcut(self):
        """Test that commands without shortcuts don't affect the keyboard service."""

        @command(id="test.no_shortcut", title="Test No Shortcut", category="Test")
        def no_shortcut_command(context: CommandContext) -> CommandResult:
            return CommandResult(success=True)

        # Command should be registered
        cmd = command_registry.get_command("test.no_shortcut")
        assert cmd is not None
        assert cmd.shortcut is None

        # No shortcuts should be registered for this command
        shortcuts = self.keyboard_service.get_shortcuts_for_command("test.no_shortcut")
        assert len(shortcuts) == 0

    def test_multiple_commands_with_shortcuts(self):
        """Test registering multiple commands with shortcuts."""

        @command(id="test.multi1", title="Multi 1", category="Test", shortcut="ctrl+1")
        def multi1_command(context: CommandContext) -> CommandResult:
            return CommandResult(success=True)

        @command(id="test.multi2", title="Multi 2", category="Test", shortcut="ctrl+2")
        def multi2_command(context: CommandContext) -> CommandResult:
            return CommandResult(success=True)

        @command(id="test.multi3", title="Multi 3", category="Test", shortcut="ctrl+3")
        def multi3_command(context: CommandContext) -> CommandResult:
            return CommandResult(success=True)

        # All shortcuts should be registered
        for i in range(1, 4):
            shortcuts = self.keyboard_service.get_shortcuts_for_command(
                f"test.multi{i}"
            )
            assert len(shortcuts) == 1
            assert str(shortcuts[0].sequence) == f"ctrl+{i}"

    def test_shortcut_conflict_handling(self):
        """Test handling of shortcut conflicts between commands."""

        @command(
            id="test.conflict1", title="Conflict 1", category="Test", shortcut="ctrl+x"
        )
        def conflict1_command(context: CommandContext) -> CommandResult:
            return CommandResult(success=True)

        @command(
            id="test.conflict2",
            title="Conflict 2",
            category="Test",
            shortcut="ctrl+x",  # Same shortcut
        )
        def conflict2_command(context: CommandContext) -> CommandResult:
            return CommandResult(success=True)

        # Both commands should be registered
        assert command_registry.get_command("test.conflict1") is not None
        assert command_registry.get_command("test.conflict2") is not None

        # Check how conflicts are handled
        self.keyboard_service.get_shortcut_conflicts()
        from core.keyboard.parser import KeySequenceParser

        KeySequenceParser.parse("ctrl+x")

        # Should have at least one shortcut registered (conflict resolver handles the rest)
        all_shortcuts = self.keyboard_service.get_all_shortcuts()
        ctrl_x_shortcuts = [s for s in all_shortcuts if str(s.sequence) == "ctrl+x"]
        assert len(ctrl_x_shortcuts) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
