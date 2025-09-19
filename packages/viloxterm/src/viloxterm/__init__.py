"""
ViloxTerm Terminal Plugin.

Professional terminal emulator for ViloxTerm.
"""

from .plugin import TerminalPlugin
from .widget import TerminalWidget, TerminalWidgetFactory
from .server import terminal_server

__version__ = "1.0.0"
__author__ = "ViloxTerm Team"

__all__ = [
    "TerminalPlugin",
    "TerminalWidget",
    "TerminalWidgetFactory",
    "terminal_server"
]

# Plugin entry point
Plugin = TerminalPlugin