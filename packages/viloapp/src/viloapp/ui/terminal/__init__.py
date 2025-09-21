"""Terminal widget module for viloapp."""

from .terminal_app_widget import TerminalAppWidget

# Note: TerminalWidget (old implementation) is deprecated
# Use TerminalAppWidget which properly extends AppWidget
# TerminalServerManager has been moved to services.terminal_server

__all__ = ["TerminalAppWidget"]
