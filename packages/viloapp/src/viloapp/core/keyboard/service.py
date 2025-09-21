#!/usr/bin/env python3
"""
Keyboard service for centralized keyboard shortcut handling.

This service manages keyboard shortcuts, handles key events, and provides
the main interface for the keyboard subsystem.
"""

import logging
from typing import Any, Callable, Optional

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from viloapp.core.keyboard.conflicts import ConflictResolver
from viloapp.core.keyboard.parser import KeyChord, KeyModifier, KeySequence
from viloapp.core.keyboard.shortcuts import Shortcut, ShortcutRegistry
from viloapp.services.base import Service

logger = logging.getLogger(__name__)


class KeyboardService(Service):
    """Service for managing keyboard shortcuts and handling key events."""

    # Signals
    shortcut_triggered = Signal(str, dict)  # command_id, context
    chord_sequence_started = Signal(str)  # sequence_str
    chord_sequence_cancelled = Signal()

    def __init__(self, name: str = "KeyboardService"):
        """Initialize the keyboard service."""
        super().__init__(name)

        # Core components
        self._registry = ShortcutRegistry()
        self._conflict_resolver = ConflictResolver()

        # Chord sequence state
        self._active_chord_sequence: list[KeyChord] = []
        self._chord_timeout = 1000  # ms to wait for next chord
        self._chord_timer = QTimer()
        self._chord_timer.setSingleShot(True)
        self._chord_timer.timeout.connect(self._on_chord_timeout)

        # Key event tracking
        self._pressed_modifiers: set[str] = set()
        self._last_key_event: Optional[QKeyEvent] = None

        # Context providers
        self._context_providers: list[Callable[[], dict[str, Any]]] = []

    def initialize(self, context: dict[str, Any]) -> None:
        """Initialize the keyboard service."""
        super().initialize(context)

        # Register built-in context providers
        self._register_builtin_context_providers()

        # Load default shortcuts
        self._load_default_shortcuts()

        logger.info("Keyboard service initialized")

    def cleanup(self) -> None:
        """Clean up the keyboard service."""
        self._chord_timer.stop()
        self._registry.clear()
        super().cleanup()
        logger.info("Keyboard service cleaned up")

    def register_shortcut(self, shortcut: Shortcut) -> bool:
        """
        Register a keyboard shortcut.

        Args:
            shortcut: Shortcut to register

        Returns:
            True if registered successfully
        """
        # Check for conflicts
        conflicts = self._conflict_resolver.find_conflicts(shortcut, self._registry)
        if conflicts:
            logger.warning(f"Shortcut conflicts detected for {shortcut}: {conflicts}")
            # Let conflict resolver decide how to handle
            if not self._conflict_resolver.resolve_conflicts(shortcut, conflicts, self._registry):
                return False

        success = self._registry.register(shortcut)
        if success:
            logger.debug(f"Registered shortcut: {shortcut}")

        return success

    def register_shortcut_from_string(
        self,
        shortcut_id: str,
        sequence_str: str,
        command_id: str,
        when: Optional[str] = None,
        description: Optional[str] = None,
        source: str = "user",
        priority: int = 100,
    ) -> bool:
        """
        Register a shortcut from string representation.

        Args:
            shortcut_id: Unique identifier
            sequence_str: Key sequence string (e.g., "ctrl+n")
            command_id: Command to execute
            when: Optional when clause
            description: Optional description
            source: Source of the shortcut
            priority: Priority for conflict resolution

        Returns:
            True if registered successfully
        """
        return self._registry.register_from_string(
            shortcut_id=shortcut_id,
            sequence_str=sequence_str,
            command_id=command_id,
            when=when,
            description=description,
            source=source,
            priority=priority,
        )

    def unregister_shortcut(self, shortcut_id: str) -> bool:
        """
        Unregister a shortcut.

        Args:
            shortcut_id: ID of shortcut to remove

        Returns:
            True if unregistered successfully
        """
        return self._registry.unregister(shortcut_id)

    def handle_key_event(self, event: QKeyEvent) -> bool:
        """
        Handle a key event and check for shortcut matches.

        Args:
            event: Qt key event

        Returns:
            True if event was handled (shortcut triggered)
        """
        if not self.is_initialized:
            return False

        # Convert Qt event to our key representation
        chord = self._qt_event_to_chord(event)
        if not chord:
            return False

        # Handle chord sequences
        if self._active_chord_sequence:
            return self._handle_chord_sequence_event(chord)
        else:
            return self._handle_single_chord_event(chord)

    def get_shortcuts_for_command(self, command_id: str) -> list[Shortcut]:
        """Get all shortcuts for a command."""
        return self._registry.get_shortcuts_for_command(command_id)

    def get_all_shortcuts(self) -> list[Shortcut]:
        """Get all registered shortcuts."""
        return self._registry.get_all_shortcuts()

    def get_shortcut_conflicts(self) -> dict[KeySequence, list[Shortcut]]:
        """Get all shortcut conflicts."""
        return self._registry.get_conflicts()

    def add_context_provider(self, provider: Callable[[], dict[str, Any]]) -> None:
        """Add a context provider function."""
        if provider not in self._context_providers:
            self._context_providers.append(provider)

    def remove_context_provider(self, provider: Callable[[], dict[str, Any]]) -> None:
        """Remove a context provider function."""
        if provider in self._context_providers:
            self._context_providers.remove(provider)

    def set_chord_timeout(self, timeout_ms: int) -> None:
        """Set the chord sequence timeout in milliseconds."""
        self._chord_timeout = timeout_ms

    def _handle_single_chord_event(self, chord: KeyChord) -> bool:
        """Handle a single chord key event."""
        # Create single-chord sequence
        sequence = KeySequence([chord])

        # Get current context
        context = self._get_current_context()

        # Find matching shortcuts
        matching = self._registry.find_matching_shortcuts(sequence, context)

        if not matching:
            # Check if this could be the start of a chord sequence
            return self._check_chord_sequence_start(chord, context)

        # Execute the first matching shortcut (highest priority)
        shortcut = matching[0]
        self._execute_shortcut(shortcut, context)
        return True

    def _handle_chord_sequence_event(self, chord: KeyChord) -> bool:
        """Handle a chord event when a sequence is already active."""
        # Add chord to sequence
        self._active_chord_sequence.append(chord)

        # Create sequence
        sequence = KeySequence(self._active_chord_sequence.copy())

        # Get current context
        context = self._get_current_context()

        # Find matching shortcuts
        matching = self._registry.find_matching_shortcuts(sequence, context)

        if matching:
            # Execute first match
            shortcut = matching[0]
            self._execute_shortcut(shortcut, context)
            self._cancel_chord_sequence()
            return True

        # Check if this could still be part of a longer sequence
        if self._has_potential_chord_matches(sequence, context):
            # Continue waiting for more chords
            self._restart_chord_timer()
            return True
        else:
            # No potential matches, cancel sequence
            self._cancel_chord_sequence()
            return False

    def _check_chord_sequence_start(self, chord: KeyChord, context: dict[str, Any]) -> bool:
        """Check if a chord could start a chord sequence."""
        # Create sequence with just this chord
        KeySequence([chord])

        # Check if any registered shortcuts start with this chord
        for shortcut in self._registry.get_all_shortcuts():
            if (
                shortcut.sequence.chords
                and shortcut.sequence.chords[0] == chord
                and len(shortcut.sequence.chords) > 1
                and shortcut.matches_context(context)
            ):
                # Start chord sequence
                self._start_chord_sequence(chord)
                return True

        return False

    def _has_potential_chord_matches(
        self, partial_sequence: KeySequence, context: dict[str, Any]
    ) -> bool:
        """Check if a partial sequence could match any shortcuts."""
        partial_chords = partial_sequence.chords
        partial_len = len(partial_chords)

        for shortcut in self._registry.get_all_shortcuts():
            if (
                len(shortcut.sequence.chords) > partial_len
                and shortcut.sequence.chords[:partial_len] == partial_chords
                and shortcut.matches_context(context)
            ):
                return True

        return False

    def _start_chord_sequence(self, first_chord: KeyChord) -> None:
        """Start a new chord sequence."""
        self._active_chord_sequence = [first_chord]
        self._restart_chord_timer()

        sequence_str = str(KeySequence(self._active_chord_sequence))
        self.chord_sequence_started.emit(sequence_str)
        logger.debug(f"Started chord sequence: {sequence_str}")

    def _restart_chord_timer(self) -> None:
        """Restart the chord timeout timer."""
        self._chord_timer.stop()
        self._chord_timer.start(self._chord_timeout)

    def _cancel_chord_sequence(self) -> None:
        """Cancel the current chord sequence."""
        if self._active_chord_sequence:
            logger.debug("Cancelled chord sequence")
            self._active_chord_sequence.clear()
            self._chord_timer.stop()
            self.chord_sequence_cancelled.emit()

    def _on_chord_timeout(self) -> None:
        """Handle chord sequence timeout."""
        logger.debug("Chord sequence timed out")
        self._cancel_chord_sequence()

    def _execute_shortcut(self, shortcut: Shortcut, context: dict[str, Any]) -> None:
        """Execute a shortcut."""
        logger.debug(f"Executing shortcut: {shortcut}")
        self.shortcut_triggered.emit(shortcut.command_id, context)

    def _get_current_context(self) -> dict[str, Any]:
        """Get the current context from all providers."""
        context = {}

        for provider in self._context_providers:
            try:
                provider_context = provider()
                if provider_context:
                    context.update(provider_context)
            except Exception as e:
                logger.error(f"Error getting context from provider: {e}")

        return context

    def _qt_event_to_chord(self, event: QKeyEvent) -> Optional[KeyChord]:
        """Convert Qt key event to KeyChord."""
        # Get modifiers
        modifiers = set()
        qt_modifiers = event.modifiers()

        from PySide6.QtCore import Qt

        if qt_modifiers & Qt.ControlModifier:
            modifiers.add(KeyModifier.CTRL)
        if qt_modifiers & Qt.ShiftModifier:
            modifiers.add(KeyModifier.SHIFT)
        if qt_modifiers & Qt.AltModifier:
            modifiers.add(KeyModifier.ALT)
        if qt_modifiers & Qt.MetaModifier:
            modifiers.add(KeyModifier.META)

        # Get key
        key = self._qt_key_to_string(event.key())
        if not key:
            return None

        return KeyChord(modifiers, key)

    def _qt_key_to_string(self, qt_key: int) -> Optional[str]:
        """Convert Qt key code to string representation."""
        from PySide6.QtCore import Qt

        # Function keys
        if Qt.Key_F1 <= qt_key <= Qt.Key_F35:
            return f"f{qt_key - Qt.Key_F1 + 1}"

        # Special keys
        special_keys = {
            Qt.Key_Escape: "escape",
            Qt.Key_Tab: "tab",
            Qt.Key_Space: "space",
            Qt.Key_Return: "return",
            Qt.Key_Enter: "enter",
            Qt.Key_Backspace: "backspace",
            Qt.Key_Delete: "delete",
            Qt.Key_Insert: "insert",
            Qt.Key_Home: "home",
            Qt.Key_End: "end",
            Qt.Key_PageUp: "pageup",
            Qt.Key_PageDown: "pagedown",
            Qt.Key_Up: "up",
            Qt.Key_Down: "down",
            Qt.Key_Left: "left",
            Qt.Key_Right: "right",
        }

        if qt_key in special_keys:
            return special_keys[qt_key]

        # Handle shifted characters - map back to base key for shortcuts
        # When Shift is pressed, Qt gives us the shifted character
        # But shortcuts are defined with the base key + shift modifier
        shifted_to_base = {
            Qt.Key_Bar: "\\",  # | -> \ (for ctrl+shift+\)
            Qt.Key_Plus: "=",  # + -> =
            Qt.Key_Underscore: "-",  # _ -> -
            Qt.Key_BraceLeft: "[",  # { -> [
            Qt.Key_BraceRight: "]",  # } -> ]
            Qt.Key_Colon: ";",  # : -> ;
            Qt.Key_QuoteDbl: "'",  # " -> '
            Qt.Key_Less: ",",  # < -> ,
            Qt.Key_Greater: ".",  # > -> .
            Qt.Key_Question: "/",  # ? -> /
            Qt.Key_AsciiTilde: "`",  # ~ -> `
            Qt.Key_Exclam: "1",  # ! -> 1
            Qt.Key_At: "2",  # @ -> 2
            Qt.Key_NumberSign: "3",  # # -> 3
            Qt.Key_Dollar: "4",  # $ -> 4
            Qt.Key_Percent: "5",  # % -> 5
            Qt.Key_AsciiCircum: "6",  # ^ -> 6
            Qt.Key_Ampersand: "7",  # & -> 7
            Qt.Key_Asterisk: "8",  # * -> 8
            Qt.Key_ParenLeft: "9",  # ( -> 9
            Qt.Key_ParenRight: "0",  # ) -> 0
        }

        if qt_key in shifted_to_base:
            return shifted_to_base[qt_key]

        # Regular keys (letters, numbers, symbols)
        if 32 <= qt_key <= 126:  # Printable ASCII
            return chr(qt_key).lower()

        return None

    def _register_builtin_context_providers(self) -> None:
        """Register built-in context providers."""

        # Add basic application context
        def app_context():
            app = QApplication.instance()
            if not app:
                return {}

            from PySide6.QtCore import Qt

            return {
                "platform": app.platformName(),
                "applicationActive": app.applicationState()
                == Qt.ApplicationState.ApplicationActive,
            }

        self.add_context_provider(app_context)

    def _load_default_shortcuts(self) -> None:
        """Load default shortcuts from commands."""
        # This will be implemented when we integrate with the command system
        # For now, we just log that we're ready to load shortcuts
        logger.debug("Ready to load shortcuts from commands")
