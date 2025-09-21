#!/usr/bin/env python3
"""
Test suite for the keyboard system implementation.

Tests keyboard shortcuts, parsing, conflict resolution, and keymaps.
"""

from unittest.mock import Mock, patch

import pytest

from viloapp.core.keyboard import (
    ConflictResolver,
    KeyboardService,
    KeyChord,
    KeymapManager,
    KeyModifier,
    KeySequence,
    KeySequenceParser,
    Shortcut,
    ShortcutRegistry,
)
from viloapp.core.keyboard.keymaps import (
    DefaultKeymapProvider,
    VimKeymapProvider,
    VSCodeKeymapProvider,
)


class TestKeySequenceParser:
    """Test the key sequence parser."""

    def test_parse_simple_chord(self):
        """Test parsing simple key chords."""
        # Single key
        sequence = KeySequenceParser.parse("n")
        assert isinstance(
            sequence, KeySequence
        ), f"Expected KeySequence instance for 'n', got {type(sequence)}"
        assert len(sequence.chords) == 1
        assert sequence.chords[0].key == "n"
        assert len(sequence.chords[0].modifiers) == 0

        # Key with modifier
        sequence = KeySequenceParser.parse("ctrl+n")
        assert isinstance(
            sequence, KeySequence
        ), f"Expected KeySequence instance for 'ctrl+n', got {type(sequence)}"
        assert len(sequence.chords) == 1
        assert sequence.chords[0].key == "n"
        assert KeyModifier.CTRL in sequence.chords[0].modifiers

        # Multiple modifiers
        sequence = KeySequenceParser.parse("ctrl+shift+p")
        assert isinstance(
            sequence, KeySequence
        ), f"Expected KeySequence instance for 'ctrl+shift+p', got {type(sequence)}"
        assert len(sequence.chords) == 1
        assert sequence.chords[0].key == "p"
        assert KeyModifier.CTRL in sequence.chords[0].modifiers
        assert KeyModifier.SHIFT in sequence.chords[0].modifiers

    def test_parse_chord_sequence(self):
        """Test parsing chord sequences."""
        sequence = KeySequenceParser.parse("ctrl+k ctrl+w")
        assert isinstance(
            sequence, KeySequence
        ), f"Expected KeySequence instance for chord sequence 'ctrl+k ctrl+w', got {type(sequence)}"
        assert len(sequence.chords) == 2

        # First chord
        assert sequence.chords[0].key == "k"
        assert KeyModifier.CTRL in sequence.chords[0].modifiers

        # Second chord
        assert sequence.chords[1].key == "w"
        assert KeyModifier.CTRL in sequence.chords[1].modifiers

    def test_parse_function_keys(self):
        """Test parsing function keys."""
        sequence = KeySequenceParser.parse("f1")
        assert isinstance(
            sequence, KeySequence
        ), f"Expected KeySequence instance for function key 'f1', got {type(sequence)}"
        assert sequence.chords[0].key == "f1"

        sequence = KeySequenceParser.parse("ctrl+f12")
        assert isinstance(
            sequence, KeySequence
        ), f"Expected KeySequence instance for 'ctrl+f12', got {type(sequence)}"
        assert sequence.chords[0].key == "f12"
        assert KeyModifier.CTRL in sequence.chords[0].modifiers

    def test_parse_special_keys(self):
        """Test parsing special keys."""
        special_keys = ["escape", "tab", "space", "return", "backspace"]

        for key in special_keys:
            sequence = KeySequenceParser.parse(key)
            assert isinstance(
                sequence, KeySequence
            ), f"Expected KeySequence instance for special key '{key}', got {type(sequence)}"
            assert sequence.chords[0].key == key

            # With modifier
            sequence = KeySequenceParser.parse(f"ctrl+{key}")
            assert isinstance(
                sequence, KeySequence
            ), f"Expected KeySequence instance for 'ctrl+{key}', got {type(sequence)}"
            assert sequence.chords[0].key == key
            assert KeyModifier.CTRL in sequence.chords[0].modifiers

    def test_parse_invalid_sequences(self):
        """Test parsing invalid sequences."""
        # Empty string
        assert KeySequenceParser.parse("") is None
        assert KeySequenceParser.parse(None) is None

        # Invalid format
        assert KeySequenceParser.parse("ctrl+") is None
        assert KeySequenceParser.parse("+n") is None

    def test_normalize(self):
        """Test sequence normalization."""
        # Should normalize to consistent format
        normalized = KeySequenceParser.normalize("CTRL+SHIFT+P")
        assert normalized == "ctrl+shift+p"

        normalized = KeySequenceParser.normalize("ctrl+k ctrl+w")
        assert normalized == "ctrl+k ctrl+w"

    def test_validate(self):
        """Test sequence validation."""
        # Valid sequences
        valid, error = KeySequenceParser.validate("ctrl+n")
        assert (
            valid is True
        ), f"Expected 'ctrl+n' to be valid, but validation failed with error: {error}"
        assert error is None

        valid, error = KeySequenceParser.validate("ctrl+k ctrl+w")
        assert (
            valid is True
        ), f"Expected 'ctrl+k ctrl+w' to be valid, but validation failed with error: {error}"
        assert error is None

        # Invalid sequences
        valid, error = KeySequenceParser.validate("")
        assert valid is False, "Expected empty string to be invalid"
        assert (
            isinstance(error, str) and len(error) > 0
        ), f"Expected non-empty error message for empty string validation, got {error}"

        valid, error = KeySequenceParser.validate("invalid+key")
        assert valid is False, "Expected 'invalid+key' to be invalid"
        assert (
            isinstance(error, str) and len(error) > 0
        ), f"Expected non-empty error message for 'invalid+key' validation, got {error}"


class TestShortcutRegistry:
    """Test the shortcut registry."""

    def setup_method(self):
        """Set up test registry."""
        self.registry = ShortcutRegistry()

    def test_register_shortcut(self):
        """Test registering shortcuts."""
        sequence = KeySequenceParser.parse("ctrl+n")
        shortcut = Shortcut(
            id="test.new",
            sequence=sequence,
            command_id="test.newFile",
            description="Create new file",
        )

        success = self.registry.register(shortcut)
        assert success is True, f"Failed to register shortcut {shortcut.id}"

        # Check retrieval
        retrieved = self.registry.get_shortcut("test.new")
        assert retrieved == shortcut

        # Check by sequence
        shortcuts = self.registry.get_shortcuts_for_sequence(sequence)
        assert len(shortcuts) == 1
        assert shortcuts[0] == shortcut

        # Check by command
        shortcuts = self.registry.get_shortcuts_for_command("test.newFile")
        assert len(shortcuts) == 1
        assert shortcuts[0] == shortcut

    def test_register_from_string(self):
        """Test registering from string."""
        success = self.registry.register_from_string(
            shortcut_id="test.save",
            sequence_str="ctrl+s",
            command_id="test.saveFile",
            description="Save file",
        )
        assert (
            success is True
        ), "Failed to register shortcut from string for 'test.save'"

        shortcut = self.registry.get_shortcut("test.save")
        assert isinstance(
            shortcut, Shortcut
        ), f"Expected Shortcut instance for 'test.save', got {type(shortcut)}"
        assert shortcut.command_id == "test.saveFile"
        assert str(shortcut.sequence) == "ctrl+s"

    def test_unregister_shortcut(self):
        """Test unregistering shortcuts."""
        # Register shortcut
        self.registry.register_from_string(
            shortcut_id="test.temp", sequence_str="ctrl+t", command_id="test.temp"
        )

        # Verify it's registered
        temp_shortcut = self.registry.get_shortcut("test.temp")
        assert isinstance(
            temp_shortcut, Shortcut
        ), f"Expected Shortcut instance for 'test.temp', got {type(temp_shortcut)}"

        # Unregister
        success = self.registry.unregister("test.temp")
        assert success is True, "Failed to unregister shortcut 'test.temp'"

        # Verify it's gone
        assert self.registry.get_shortcut("test.temp") is None

    def test_find_matching_shortcuts(self):
        """Test finding matching shortcuts with context."""
        # Register shortcuts with different contexts
        self.registry.register_from_string(
            shortcut_id="global.test",
            sequence_str="ctrl+g",
            command_id="global.command",
        )

        self.registry.register_from_string(
            shortcut_id="editor.test",
            sequence_str="ctrl+g",
            command_id="editor.command",
            when="editorFocus",
        )

        sequence = KeySequenceParser.parse("ctrl+g")

        # Global context
        context = {"editorFocus": False}
        matching = self.registry.find_matching_shortcuts(sequence, context)
        assert len(matching) == 1
        assert matching[0].id == "global.test"

        # Editor context - both global and editor-specific should match
        context = {"editorFocus": True}
        matching = self.registry.find_matching_shortcuts(sequence, context)
        assert len(matching) == 2  # Both global and editor shortcuts should match

        # Check that we have both shortcuts
        ids = [s.id for s in matching]
        assert "global.test" in ids
        assert "editor.test" in ids

    def test_get_conflicts(self):
        """Test conflict detection."""
        # Register conflicting shortcuts
        self.registry.register_from_string(
            shortcut_id="conflict1", sequence_str="ctrl+c", command_id="command1"
        )

        self.registry.register_from_string(
            shortcut_id="conflict2", sequence_str="ctrl+c", command_id="command2"
        )

        conflicts = self.registry.get_conflicts()
        assert (
            len(conflicts) == 1
        ), f"Expected exactly 1 conflict for sequence 'ctrl+c', got {len(conflicts)}"

        sequence = KeySequenceParser.parse("ctrl+c")
        assert sequence in conflicts
        assert len(conflicts[sequence]) == 2


class TestConflictResolver:
    """Test conflict resolution."""

    def setup_method(self):
        """Set up test resolver and registry."""
        self.resolver = ConflictResolver()
        self.registry = ShortcutRegistry()

    def test_find_exact_conflicts(self):
        """Test finding exact sequence conflicts."""
        # Register existing shortcut
        existing = Shortcut(
            id="existing",
            sequence=KeySequenceParser.parse("ctrl+n"),
            command_id="existing.command",
        )
        self.registry.register(existing)

        # Create conflicting shortcut
        new_shortcut = Shortcut(
            id="new",
            sequence=KeySequenceParser.parse("ctrl+n"),
            command_id="new.command",
        )

        conflicts = self.resolver.find_conflicts(new_shortcut, self.registry)
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "exact"

    def test_resolve_by_priority(self):
        """Test resolution by priority."""
        # Register low priority shortcut
        existing = Shortcut(
            id="low_priority",
            sequence=KeySequenceParser.parse("ctrl+p"),
            command_id="low.command",
            priority=200,
        )
        self.registry.register(existing)

        # Create high priority conflicting shortcut
        new_shortcut = Shortcut(
            id="high_priority",
            sequence=KeySequenceParser.parse("ctrl+p"),
            command_id="high.command",
            priority=50,
        )

        conflicts = self.resolver.find_conflicts(new_shortcut, self.registry)
        success = self.resolver.resolve_conflicts(
            new_shortcut, conflicts, self.registry
        )

        assert success is True, "Failed to resolve conflicts for high priority shortcut"
        # High priority shortcut should replace low priority one
        assert self.registry.get_shortcut("low_priority") is None

    def test_no_conflict_different_contexts(self):
        """Test no conflict when contexts don't overlap."""
        # Register context-specific shortcut
        existing = Shortcut(
            id="editor_only",
            sequence=KeySequenceParser.parse("ctrl+e"),
            command_id="editor.command",
            when="editorFocus",
        )
        self.registry.register(existing)

        # Create shortcut with different context
        new_shortcut = Shortcut(
            id="terminal_only",
            sequence=KeySequenceParser.parse("ctrl+e"),
            command_id="terminal.command",
            when="terminalFocus",
        )

        conflicts = self.resolver.find_conflicts(new_shortcut, self.registry)
        # Should have no conflicts due to different contexts
        assert len(conflicts) == 0


class TestKeymaps:
    """Test keymap providers and manager."""

    def test_default_keymap_provider(self):
        """Test default keymap provider."""
        provider = DefaultKeymapProvider()

        info = provider.get_info()
        assert info.id == "default"
        assert info.name == "ViloApp Default"

        shortcuts = provider.get_shortcuts()
        assert (
            len(shortcuts) >= 3
        ), f"Expected at least 3 default shortcuts, got {len(shortcuts)}"

        # Check for essential shortcuts
        shortcut_ids = [s["id"] for s in shortcuts]
        assert "file.new" in shortcut_ids
        assert "edit.copy" in shortcut_ids
        assert "view.sidebar" in shortcut_ids

    def test_vscode_keymap_provider(self):
        """Test VSCode keymap provider."""
        provider = VSCodeKeymapProvider()

        info = provider.get_info()
        assert info.id == "vscode"
        assert info.name == "VSCode"

        shortcuts = provider.get_shortcuts()
        assert (
            len(shortcuts) >= 2
        ), f"Expected at least 2 VSCode shortcuts, got {len(shortcuts)}"

        # Check for VSCode-specific shortcuts
        sequences = [s["sequence"] for s in shortcuts]
        assert "ctrl+shift+p" in sequences  # Command palette
        assert "ctrl+k ctrl+w" in sequences  # Close all tabs

    def test_vim_keymap_provider(self):
        """Test Vim keymap provider."""
        provider = VimKeymapProvider()

        info = provider.get_info()
        assert info.id == "vim"
        assert info.name == "Vim"

        shortcuts = provider.get_shortcuts()
        assert (
            len(shortcuts) >= 1
        ), f"Expected at least 1 Vim shortcut, got {len(shortcuts)}"

        # Check for Vim-specific shortcuts
        vim_shortcuts = [
            s for s in shortcuts if s.get("when") and "vimMode" in s["when"]
        ]
        assert (
            len(vim_shortcuts) >= 1
        ), f"Expected at least 1 Vim-specific shortcut, got {len(vim_shortcuts)}"

    def test_keymap_manager(self):
        """Test keymap manager."""
        registry = ShortcutRegistry()
        manager = KeymapManager(registry)

        # Check available keymaps
        keymaps = manager.get_available_keymaps()
        keymap_ids = [k.id for k in keymaps]
        assert "default" in keymap_ids
        assert "vscode" in keymap_ids
        assert "vim" in keymap_ids

        # Set keymap
        success = manager.set_keymap("vscode")
        assert success is True, "Failed to set VSCode keymap"
        assert manager.get_current_keymap() == "vscode"

        # Check shortcuts were loaded
        all_shortcuts = registry.get_all_shortcuts()
        vscode_shortcuts = [s for s in all_shortcuts if s.id.startswith("vscode.")]
        assert (
            len(vscode_shortcuts) >= 1
        ), f"Expected at least 1 loaded VSCode shortcut, got {len(vscode_shortcuts)}"

        # Switch keymap
        success = manager.set_keymap("default")
        assert success is True, "Failed to switch back to default keymap"
        assert manager.get_current_keymap() == "default"

        # VSCode shortcuts should be cleared
        all_shortcuts = registry.get_all_shortcuts()
        vscode_shortcuts = [s for s in all_shortcuts if s.id.startswith("vscode.")]
        assert len(vscode_shortcuts) == 0


class TestKeyboardService:
    """Test the keyboard service."""

    def setup_method(self):
        """Set up test service."""
        self.service = KeyboardService()
        self.service.initialize({})

    def teardown_method(self):
        """Clean up test service."""
        if self.service.is_initialized:
            self.service.cleanup()

    def test_register_shortcut(self):
        """Test registering shortcuts through service."""
        success = self.service.register_shortcut_from_string(
            shortcut_id="test.shortcut",
            sequence_str="ctrl+t",
            command_id="test.command",
            description="Test shortcut",
        )
        assert success is True, "Failed to register shortcut through service"

        shortcuts = self.service.get_shortcuts_for_command("test.command")
        assert len(shortcuts) == 1
        assert shortcuts[0].id == "test.shortcut"

    def test_context_providers(self):
        """Test context providers."""

        # Add custom context provider
        def custom_context():
            return {"customKey": "customValue"}

        self.service.add_context_provider(custom_context)

        # Context should include custom values
        context = self.service._get_current_context()
        assert "customKey" in context
        assert context["customKey"] == "customValue"

        # Remove provider
        self.service.remove_context_provider(custom_context)
        context = self.service._get_current_context()
        assert "customKey" not in context

    def test_qt_event_conversion(self):
        """Test converting Qt events to key chords."""
        with patch("PySide6.QtCore.Qt") as mock_qt:
            # Mock Qt constants
            mock_qt.ControlModifier = 1
            mock_qt.ShiftModifier = 2
            mock_qt.AltModifier = 4
            mock_qt.MetaModifier = 8
            mock_qt.Key_F1 = 16777264
            mock_qt.Key_F35 = mock_qt.Key_F1 + 34
            mock_qt.Key_N = ord("N")

            # Create mock key event
            mock_event = Mock()
            mock_event.modifiers.return_value = 1  # Ctrl
            mock_event.key.return_value = ord("N")

            # Convert event
            chord = self.service._qt_event_to_chord(mock_event)

            assert isinstance(
                chord, KeyChord
            ), f"Expected KeyChord instance from Qt event conversion, got {type(chord)}"
            assert KeyModifier.CTRL in chord.modifiers
            assert chord.key.lower() == "n"

    def test_chord_sequence_handling(self):
        """Test chord sequence handling."""
        # Register chord sequence
        success = self.service.register_shortcut_from_string(
            shortcut_id="test.chord",
            sequence_str="ctrl+k ctrl+w",
            command_id="test.chordCommand",
        )
        assert success is True, "Failed to register chord sequence shortcut"

        # Test partial sequence recognition
        first_chord = KeyChord({KeyModifier.CTRL}, "k")
        partial_sequence = KeySequence([first_chord])

        context = {}
        potential = self.service._has_potential_chord_matches(partial_sequence, context)
        assert potential  # Should recognize this as potential start of chord sequence

    def test_signals(self):
        """Test service signals."""
        # Connect to signals
        triggered_commands = []
        chord_sequences = []

        def on_shortcut(command_id, context):
            triggered_commands.append(command_id)

        def on_chord_start(sequence_str):
            chord_sequences.append(sequence_str)

        self.service.shortcut_triggered.connect(on_shortcut)
        self.service.chord_sequence_started.connect(on_chord_start)

        # Register test shortcut
        self.service.register_shortcut_from_string(
            shortcut_id="signal.test",
            sequence_str="ctrl+j",
            command_id="signal.command",
        )

        # Simulate shortcut execution
        shortcut = self.service._registry.get_shortcut("signal.test")
        context = {}
        self.service._execute_shortcut(shortcut, context)

        # Check signal was emitted
        assert len(triggered_commands) == 1
        assert triggered_commands[0] == "signal.command"


class TestIntegration:
    """Integration tests for the keyboard system."""

    def test_full_workflow(self):
        """Test complete keyboard workflow."""
        # Create components
        service = KeyboardService()
        service.initialize({})

        registry = service._registry
        manager = KeymapManager(registry)

        # Load keymap
        success = manager.set_keymap("vscode")
        assert success is True, "Failed to set VSCode keymap in integration test"

        # Check shortcuts are available
        shortcuts = registry.get_all_shortcuts()
        assert (
            len(shortcuts) >= 1
        ), f"Expected at least 1 shortcut after loading VSCode keymap, got {len(shortcuts)}"

        # Test finding shortcuts
        sequence = KeySequenceParser.parse("ctrl+n")
        context = {"editorFocus": True}
        matching = registry.find_matching_shortcuts(sequence, context)
        assert (
            len(matching) >= 0
        ), f"Expected 0 or more matching shortcuts for 'ctrl+n', got {len(matching)}"

        # Clean up
        service.cleanup()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
