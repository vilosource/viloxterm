#!/usr/bin/env python3
"""
UI theme system for ViloxTerm.

This module provides the UI layer for the theme system:
- ThemeProvider: Bridge between theme service and UI
- StylesheetGenerator: Dynamic stylesheet generation
"""

from ui.themes.theme_provider import ThemeProvider
from ui.themes.stylesheet_generator import StylesheetGenerator

__all__ = [
    'ThemeProvider',
    'StylesheetGenerator',
]