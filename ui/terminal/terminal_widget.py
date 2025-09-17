#!/usr/bin/env python3
"""
Terminal Widget - QWidget that embeds a terminal using QWebEngineView.
Connects to the shared TerminalServerManager for session management.

.. deprecated:: 1.0
    TerminalWidget is deprecated. Use TerminalAppWidget instead,
    which properly extends AppWidget and integrates with the
    AppWidgetManager system.
"""

import logging
import warnings
from typing import Any, Optional

from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .terminal_config import TerminalConfig, terminal_config
from .terminal_server import terminal_server

logger = logging.getLogger(__name__)


class TerminalWebPage(QWebEnginePage):
    """Custom QWebEnginePage for terminal with better error handling."""

    def javaScriptConsoleMessage(self, level, message, line, sourceId):
        """Log JavaScript console messages for debugging."""
        if level == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
            logger.error(f"JS Error: {message} (line {line} in {sourceId})")
        elif level == QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel:
            logger.warning(f"JS Warning: {message}")
        else:
            logger.debug(f"JS: {message}")


class TerminalWidget(QWidget):
    """
    Terminal widget that connects to a shared terminal server.
    Each widget gets its own session but shares the server infrastructure.
    """

    # Signals
    terminal_closed = Signal(str)  # session_id
    title_changed = Signal(str)  # new title
    ready = Signal()  # Terminal is ready

    def __init__(
        self,
        config: Optional[TerminalConfig] = None,
        command: Optional[str] = None,
        args: str = "",
        parent=None,
    ):
        """
        Initialize terminal widget.

        Args:
            config: Terminal configuration (uses global if not provided)
            command: Shell command to run (overrides config)
            args: Command arguments
            parent: Parent widget
        """
        warnings.warn(
            "TerminalWidget is deprecated. Use TerminalAppWidget instead, "
            "which properly extends AppWidget and integrates with the AppWidgetManager.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(parent)

        # Configuration
        self.config = config or terminal_config
        self.command = command or self.config.get_shell_command()
        self.args = args or self.config.shell_args

        # Session management
        self.session_id: Optional[str] = None
        self.web_view: Optional[QWebEngineView] = None
        self.is_ready = False
        self.is_dark_theme = True  # Default to dark

        # Setup UI
        self._setup_ui()

        # Start terminal session
        self._start_terminal()

    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create web view for terminal
        self.web_view = QWebEngineView(self)

        # Use custom page for better error handling
        page = TerminalWebPage(self.web_view)
        self.web_view.setPage(page)

        # Configure web view
        self.web_view.setContextMenuPolicy(Qt.NoContextMenu)  # Disable right-click menu
        self.web_view.setFocusPolicy(Qt.StrongFocus)

        layout.addWidget(self.web_view)

        # Set minimum size
        self.setMinimumSize(400, 300)

    def _start_terminal(self):
        """Start a new terminal session."""
        try:
            # Create session on the server
            self.session_id = terminal_server.create_session(
                command=self.command, cmd_args=self.args
            )

            # Get terminal URL
            terminal_url = terminal_server.get_session_url(self.session_id)
            logger.info(
                f"Loading terminal session {self.session_id} from {terminal_url}"
            )

            # Load terminal in web view
            self.web_view.load(QUrl(terminal_url))

            # Connect to load finished signal
            self.web_view.loadFinished.connect(self._on_load_finished)

        except Exception as e:
            logger.error(f"Failed to start terminal: {e}")
            self._show_error(f"Failed to start terminal:\n{str(e)}")

    def _on_load_finished(self, success: bool):
        """Handle web view load finished."""
        if success:
            self.is_ready = True
            self.ready.emit()
            logger.info(f"Terminal session {self.session_id} loaded successfully")

            # Apply theme
            self._apply_theme()

            # Set focus to terminal
            QTimer.singleShot(100, self.focus_terminal)
        else:
            logger.error(f"Failed to load terminal session {self.session_id}")
            self._show_error("Failed to load terminal interface")

    def _show_error(self, message: str):
        """Display error message in the widget."""
        error_label = QLabel(message)
        error_label.setWordWrap(True)
        error_label.setStyleSheet(
            """
            QLabel {
                color: #f14c4c;
                padding: 20px;
                background-color: #2d2d30;
                border: 1px solid #f14c4c;
                border-radius: 4px;
            }
        """
        )
        self.layout().addWidget(error_label)

    def _apply_theme(self):
        """Apply current theme to terminal."""
        if not self.is_ready or not self.web_view:
            return

        # Get color scheme
        color_scheme = self.config.get_color_scheme(self.is_dark_theme)

        # Build JavaScript to update terminal theme
        theme_js = f"""
        if (typeof term !== 'undefined') {{
            term.setOption('theme', {{
                background: '{color_scheme.background}',
                foreground: '{color_scheme.foreground}',
                cursor: '{color_scheme.cursor}',
                cursorAccent: '{color_scheme.cursor_accent}',
                selection: '{color_scheme.selection}',
                black: '{color_scheme.black}',
                red: '{color_scheme.red}',
                green: '{color_scheme.green}',
                yellow: '{color_scheme.yellow}',
                blue: '{color_scheme.blue}',
                magenta: '{color_scheme.magenta}',
                cyan: '{color_scheme.cyan}',
                white: '{color_scheme.white}',
                brightBlack: '{color_scheme.bright_black}',
                brightRed: '{color_scheme.bright_red}',
                brightGreen: '{color_scheme.bright_green}',
                brightYellow: '{color_scheme.bright_yellow}',
                brightBlue: '{color_scheme.bright_blue}',
                brightMagenta: '{color_scheme.bright_magenta}',
                brightCyan: '{color_scheme.bright_cyan}',
                brightWhite: '{color_scheme.bright_white}'
            }});

            // Update font settings
            term.setOption('fontSize', {self.config.font_size});
            term.setOption('fontFamily', '{self.config.font_family}');
            term.setOption('lineHeight', {self.config.line_height});
        }}
        """

        # Execute JavaScript
        self.web_view.page().runJavaScript(theme_js)

    def set_theme(self, is_dark: bool):
        """Set terminal theme."""
        self.is_dark_theme = is_dark
        self._apply_theme()

    def focus_terminal(self):
        """Set focus to the terminal."""
        if self.web_view:
            self.web_view.setFocus()
            # Also focus the terminal element in JavaScript
            self.web_view.page().runJavaScript(
                "if (typeof term !== 'undefined') { term.focus(); }"
            )

    def clear_terminal(self):
        """Clear terminal buffer."""
        if self.is_ready and self.web_view:
            self.web_view.page().runJavaScript(
                "if (typeof term !== 'undefined') { term.clear(); }"
            )

    def reset_terminal(self):
        """Reset terminal (clear buffer and reset state)."""
        if self.is_ready and self.web_view:
            self.web_view.page().runJavaScript(
                "if (typeof term !== 'undefined') { term.reset(); }"
            )

    def write_to_terminal(self, text: str):
        """Write text to terminal (for programmatic input)."""
        if self.is_ready and self.web_view and text is not None:
            # Escape the text for JavaScript
            escaped_text = (
                text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
            )
            self.web_view.page().runJavaScript(
                f"if (typeof term !== 'undefined') {{ term.write('{escaped_text}'); }}"
            )

    def paste_to_terminal(self, text: str):
        """Paste text to terminal (sends as input)."""
        if self.is_ready and self.web_view and text is not None:
            # Escape the text for JavaScript
            escaped_text = text.replace("\\", "\\\\").replace("'", "\\'")
            self.web_view.page().runJavaScript(
                f"if (typeof term !== 'undefined') {{ term.paste('{escaped_text}'); }}"
            )

    def get_session_id(self) -> Optional[str]:
        """Get the terminal session ID."""
        return self.session_id

    def get_state(self) -> dict[str, Any]:
        """Get terminal state for serialization."""
        return {
            "session_id": self.session_id,
            "command": self.command,
            "args": self.args,
            "is_dark_theme": self.is_dark_theme,
        }

    def restore_state(self, state: dict[str, Any]):
        """Restore terminal state."""
        # For now, we'll create a new session with the same command
        # In the future, we could implement session persistence
        self.command = state.get("command", self.command)
        self.args = state.get("args", self.args)
        self.is_dark_theme = state.get("is_dark_theme", self.is_dark_theme)

        # Restart terminal with restored settings
        if self.session_id:
            self.close_terminal()
        self._start_terminal()

    def close_terminal(self):
        """Close the terminal session."""
        if self.session_id:
            logger.info(f"Closing terminal session {self.session_id}")
            terminal_server.destroy_session(self.session_id)
            self.terminal_closed.emit(self.session_id)
            self.session_id = None

    def closeEvent(self, event):
        """Handle widget close event."""
        self.close_terminal()
        super().closeEvent(event)

    def __del__(self):
        """Cleanup on deletion."""
        if hasattr(self, "session_id") and self.session_id:
            try:
                terminal_server.destroy_session(self.session_id)
            except (AttributeError, OSError, RuntimeError) as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.debug(
                    f"Failed to destroy terminal session {self.session_id}: {e}"
                )
                # Ignore errors during cleanup as destructor should not raise
