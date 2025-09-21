#!/usr/bin/env python3
"""
Keyboard handling system for ViloApp.

This module provides centralized keyboard shortcut management,
key sequence parsing, conflict resolution, and keymap support.
"""

from viloapp.core.keyboard.conflicts import ConflictResolver
from viloapp.core.keyboard.keymaps import KeymapManager
from viloapp.core.keyboard.parser import KeyChord, KeyModifier, KeySequence, KeySequenceParser
from viloapp.core.keyboard.service import KeyboardService
from viloapp.core.keyboard.shortcuts import Shortcut, ShortcutRegistry

__all__ = [
    "KeyboardService",
    "Shortcut",
    "ShortcutRegistry",
    "KeySequenceParser",
    "KeySequence",
    "KeyChord",
    "KeyModifier",
    "ConflictResolver",
    "KeymapManager",
]
