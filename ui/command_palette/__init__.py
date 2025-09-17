#!/usr/bin/env python3
"""
Command palette UI components.

This package provides the VSCode-style command palette with fuzzy search,
keyboard navigation, and integration with the command system.
"""

from .palette_controller import CommandPaletteController
from .palette_widget import CommandPaletteWidget

__all__ = [
    'CommandPaletteWidget',
    'CommandPaletteController',
]
