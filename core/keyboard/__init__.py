#!/usr/bin/env python3
"""
Keyboard handling system for ViloApp.

This module provides centralized keyboard shortcut management,
key sequence parsing, conflict resolution, and keymap support.
"""

from core.keyboard.conflicts import ConflictResolver
from core.keyboard.keymaps import KeymapManager
from core.keyboard.parser import KeyChord, KeyModifier, KeySequence, KeySequenceParser
from core.keyboard.service import KeyboardService
from core.keyboard.shortcuts import Shortcut, ShortcutRegistry

__all__ = [
    'KeyboardService',
    'Shortcut',
    'ShortcutRegistry',
    'KeySequenceParser',
    'KeySequence',
    'KeyChord',
    'KeyModifier',
    'ConflictResolver',
    'KeymapManager',
]
