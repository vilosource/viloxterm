#!/usr/bin/env python3
"""
Key sequence parser for keyboard shortcuts.

Handles parsing and validation of keyboard shortcut strings like:
- "ctrl+n"
- "ctrl+shift+p"
- "alt+f4"
- "cmd+," (Mac)
- "ctrl+k ctrl+w" (chord sequences)
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence

logger = logging.getLogger(__name__)


class KeyModifier(Enum):
    """Key modifiers."""

    CTRL = "ctrl"
    SHIFT = "shift"
    ALT = "alt"
    META = "meta"  # Cmd on Mac, Win on Windows
    CMD = "cmd"  # Alias for Meta on Mac


@dataclass
class KeyChord:
    """Represents a single key chord (modifiers + key)."""

    modifiers: set[KeyModifier]
    key: str

    def __str__(self) -> str:
        """String representation of the chord."""
        parts = []

        # Order modifiers consistently
        if KeyModifier.CTRL in self.modifiers:
            parts.append("ctrl")
        if KeyModifier.SHIFT in self.modifiers:
            parts.append("shift")
        if KeyModifier.ALT in self.modifiers:
            parts.append("alt")
        if KeyModifier.META in self.modifiers or KeyModifier.CMD in self.modifiers:
            parts.append("cmd")

        parts.append(self.key.lower())
        return "+".join(parts)

    def __hash__(self) -> int:
        """Make KeyChord hashable."""
        return hash((frozenset(self.modifiers), self.key.lower()))

    def __eq__(self, other) -> bool:
        """Check equality."""
        if not isinstance(other, KeyChord):
            return False
        return (
            self.modifiers == other.modifiers and self.key.lower() == other.key.lower()
        )


@dataclass
class KeySequence:
    """Represents a key sequence (one or more chords)."""

    chords: list[KeyChord]

    def __str__(self) -> str:
        """String representation of the sequence."""
        return " ".join(str(chord) for chord in self.chords)

    def __hash__(self) -> int:
        """Make KeySequence hashable."""
        return hash(tuple(self.chords))

    def __eq__(self, other) -> bool:
        """Check equality."""
        if not isinstance(other, KeySequence):
            return False
        return self.chords == other.chords

    @property
    def is_chord_sequence(self) -> bool:
        """Check if this is a multi-chord sequence."""
        return len(self.chords) > 1

    def to_qt_sequence(self) -> Optional[QKeySequence]:
        """Convert to Qt key sequence (single chord only)."""
        if len(self.chords) != 1:
            return None  # Qt doesn't support chord sequences

        chord = self.chords[0]

        # Build Qt key combination
        key_combo = 0

        # Add modifiers
        if KeyModifier.CTRL in chord.modifiers:
            key_combo |= Qt.ControlModifier
        if KeyModifier.SHIFT in chord.modifiers:
            key_combo |= Qt.ShiftModifier
        if KeyModifier.ALT in chord.modifiers:
            key_combo |= Qt.AltModifier
        if KeyModifier.META in chord.modifiers or KeyModifier.CMD in chord.modifiers:
            key_combo |= Qt.MetaModifier

        # Add key
        qt_key = self._key_to_qt(chord.key)
        if qt_key is None:
            return None

        key_combo |= qt_key
        return QKeySequence(key_combo)

    def _key_to_qt(self, key: str) -> Optional[int]:
        """Convert key string to Qt key code."""
        key = key.lower()

        # Function keys
        if key.startswith("f") and key[1:].isdigit():
            num = int(key[1:])
            if 1 <= num <= 35:
                return getattr(Qt, f"Key_F{num}")

        # Special keys
        special_keys = {
            "escape": Qt.Key_Escape,
            "esc": Qt.Key_Escape,
            "tab": Qt.Key_Tab,
            "space": Qt.Key_Space,
            "return": Qt.Key_Return,
            "enter": Qt.Key_Enter,
            "backspace": Qt.Key_Backspace,
            "delete": Qt.Key_Delete,
            "del": Qt.Key_Delete,
            "insert": Qt.Key_Insert,
            "ins": Qt.Key_Insert,
            "home": Qt.Key_Home,
            "end": Qt.Key_End,
            "pageup": Qt.Key_PageUp,
            "pagedown": Qt.Key_PageDown,
            "up": Qt.Key_Up,
            "down": Qt.Key_Down,
            "left": Qt.Key_Left,
            "right": Qt.Key_Right,
            "capslock": Qt.Key_CapsLock,
            "numlock": Qt.Key_NumLock,
            "scrolllock": Qt.Key_ScrollLock,
            "pause": Qt.Key_Pause,
            "printscreen": Qt.Key_Print,
        }

        if key in special_keys:
            return special_keys[key]

        # Regular keys
        if len(key) == 1:
            if key.isalpha():
                return ord(key.upper())
            elif key.isdigit():
                return ord(key)
            else:
                # Symbol keys
                symbol_keys = {
                    "`": Qt.Key_QuoteLeft,
                    "~": Qt.Key_AsciiTilde,
                    "!": Qt.Key_Exclam,
                    "@": Qt.Key_At,
                    "#": Qt.Key_NumberSign,
                    "$": Qt.Key_Dollar,
                    "%": Qt.Key_Percent,
                    "^": Qt.Key_AsciiCircum,
                    "&": Qt.Key_Ampersand,
                    "*": Qt.Key_Asterisk,
                    "(": Qt.Key_ParenLeft,
                    ")": Qt.Key_ParenRight,
                    "-": Qt.Key_Minus,
                    "_": Qt.Key_Underscore,
                    "=": Qt.Key_Equal,
                    "+": Qt.Key_Plus,
                    "[": Qt.Key_BracketLeft,
                    "]": Qt.Key_BracketRight,
                    "{": Qt.Key_BraceLeft,
                    "}": Qt.Key_BraceRight,
                    "\\": Qt.Key_Backslash,
                    "|": Qt.Key_Bar,
                    ";": Qt.Key_Semicolon,
                    ":": Qt.Key_Colon,
                    "'": Qt.Key_Apostrophe,
                    '"': Qt.Key_QuoteDbl,
                    ",": Qt.Key_Comma,
                    ".": Qt.Key_Period,
                    "/": Qt.Key_Slash,
                    "?": Qt.Key_Question,
                    "<": Qt.Key_Less,
                    ">": Qt.Key_Greater,
                }
                return symbol_keys.get(key)

        return None


class KeySequenceParser:
    """Parses keyboard shortcut strings into KeySequence objects."""

    # Regular expression for parsing key chords
    CHORD_PATTERN = re.compile(
        r'^(?:(ctrl|shift|alt|meta|cmd)\+)*([a-zA-Z0-9`~!@#$%^&*()_+\-=\[\]{}\\|;:\'",.<>/?]|f\d+|escape|esc|tab|space|return|enter|backspace|delete|del|insert|ins|home|end|pageup|pagedown|up|down|left|right|capslock|numlock|scrolllock|pause|printscreen)$',
        re.IGNORECASE,
    )

    @classmethod
    def parse(cls, shortcut_str: str) -> Optional[KeySequence]:
        """
        Parse a shortcut string into a KeySequence.

        Args:
            shortcut_str: String like "ctrl+n" or "ctrl+k ctrl+w"

        Returns:
            Parsed KeySequence or None if invalid
        """
        if not shortcut_str or not isinstance(shortcut_str, str):
            return None

        # Split into chords (space-separated)
        chord_strs = shortcut_str.strip().split()
        if not chord_strs:
            return None

        chords = []
        for chord_str in chord_strs:
            chord = cls._parse_chord(chord_str)
            if chord is None:
                logger.warning(f"Invalid chord in sequence: {chord_str}")
                return None
            chords.append(chord)

        return KeySequence(chords)

    @classmethod
    def _parse_chord(cls, chord_str: str) -> Optional[KeyChord]:
        """Parse a single chord string."""
        chord_str = chord_str.strip().lower()

        if not cls.CHORD_PATTERN.match(chord_str):
            return None

        # Split by + to get modifiers and key
        parts = chord_str.split("+")
        if not parts:
            return None

        # Last part is the key
        key = parts[-1]

        # Earlier parts are modifiers
        modifiers = set()
        for part in parts[:-1]:
            try:
                modifier = KeyModifier(part)
                modifiers.add(modifier)
            except ValueError:
                logger.warning(f"Unknown modifier: {part}")
                return None

        return KeyChord(modifiers, key)

    @classmethod
    def validate(cls, shortcut_str: str) -> tuple[bool, Optional[str]]:
        """
        Validate a shortcut string.

        Returns:
            (is_valid, error_message)
        """
        if not shortcut_str or not isinstance(shortcut_str, str):
            return False, "Empty or invalid shortcut string"

        try:
            sequence = cls.parse(shortcut_str)
            if sequence is None:
                return False, "Failed to parse shortcut"

            # Additional validation rules
            for chord in sequence.chords:
                # Check for conflicts with system shortcuts
                if cls._is_system_shortcut(chord):
                    return False, f"Conflicts with system shortcut: {chord}"

                # Check for reasonable modifier combinations
                if len(chord.modifiers) > 3:
                    return False, f"Too many modifiers: {chord}"

            return True, None

        except Exception as e:
            return False, f"Validation error: {e}"

    @classmethod
    def _is_system_shortcut(cls, chord: KeyChord) -> bool:
        """Check if chord conflicts with common system shortcuts."""
        # This is a basic check - could be expanded based on platform
        system_shortcuts = {
            # Windows/Linux system shortcuts
            KeyChord({KeyModifier.ALT}, "f4"),
            KeyChord({KeyModifier.ALT}, "tab"),
            KeyChord({KeyModifier.CTRL, KeyModifier.ALT}, "delete"),
            # Mac system shortcuts (when running on Mac)
            KeyChord({KeyModifier.CMD}, "q"),
            KeyChord({KeyModifier.CMD}, "tab"),
            KeyChord({KeyModifier.CMD, KeyModifier.SHIFT}, "3"),
            KeyChord({KeyModifier.CMD, KeyModifier.SHIFT}, "4"),
        }

        return chord in system_shortcuts

    @classmethod
    def normalize(cls, shortcut_str: str) -> Optional[str]:
        """
        Normalize a shortcut string to a canonical form.

        Args:
            shortcut_str: Input shortcut string

        Returns:
            Normalized string or None if invalid
        """
        sequence = cls.parse(shortcut_str)
        if sequence is None:
            return None

        return str(sequence)
