"""Terminal widget module for viloapp."""

from .terminal_app_widget import TerminalAppWidget
from .terminal_server import TerminalServerManager

# Note: TerminalWidget (old implementation) is deprecated
# Use TerminalAppWidget which properly extends AppWidget

__all__ = ['TerminalAppWidget', 'TerminalServerManager']
