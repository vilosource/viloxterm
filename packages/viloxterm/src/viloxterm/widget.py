"""Terminal widget implementation for ViloxTerm plugin."""

import logging
from typing import Optional, Dict, Any

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Signal
from viloapp_sdk import IWidget, WidgetMetadata, WidgetPosition

from .server import terminal_server

logger = logging.getLogger(__name__)


class TerminalWidget(QWidget):
    """Terminal widget using QWebEngineView."""

    # Signals
    session_started = Signal(str)  # session_id
    session_ended = Signal(str)  # session_id
    title_changed = Signal(str)  # title

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session_id = None
        self.web_view = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Create web view for terminal
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)

        self.setLayout(layout)

    def start_terminal(self, command: str = None, cwd: str = None):
        """Start a new terminal session."""
        try:
            # Get default shell if not specified
            if not command:
                import platform
                if platform.system() == "Windows":
                    command = "powershell.exe"
                else:
                    command = "/bin/bash"

            # Create terminal session
            self.session_id = terminal_server.create_session(
                command=command,
                cwd=cwd
            )

            # Get terminal URL
            url = terminal_server.get_terminal_url(self.session_id)

            # Load terminal in web view
            self.web_view.load(QUrl(url))

            # Connect to session ended signal
            terminal_server.session_ended.connect(self._on_session_ended)

            # Emit signal
            self.session_started.emit(self.session_id)

            logger.info(f"Started terminal session {self.session_id}")

        except Exception as e:
            logger.error(f"Failed to start terminal: {e}")

    def stop_terminal(self):
        """Stop the terminal session."""
        if self.session_id:
            try:
                terminal_server.destroy_session(self.session_id)
                self.session_ended.emit(self.session_id)
                self.session_id = None
            except Exception as e:
                logger.error(f"Failed to stop terminal: {e}")

    def _on_session_ended(self, session_id: str):
        """Handle session ended signal."""
        if session_id == self.session_id:
            self.session_ended.emit(session_id)
            self.session_id = None

    def clear_terminal(self):
        """Clear terminal screen."""
        if self.web_view:
            self.web_view.page().runJavaScript("term.clear()")

    def focus_terminal(self):
        """Focus the terminal."""
        if self.web_view:
            self.web_view.setFocus()

    def send_text(self, text: str):
        """Send text to terminal."""
        if self.web_view and text:
            # Escape text for JavaScript
            escaped = text.replace("\\", "\\\\").replace("'", "\\'")
            self.web_view.page().runJavaScript(f"term.write('{escaped}')")

    def closeEvent(self, event):
        """Handle widget close."""
        self.stop_terminal()
        super().closeEvent(event)


class TerminalWidgetFactory(IWidget):
    """Factory for creating terminal widgets."""

    def get_metadata(self) -> WidgetMetadata:
        return WidgetMetadata(
            id="terminal",
            title="Terminal",
            position=WidgetPosition.MAIN,
            icon="terminal",
            closable=True,
            singleton=False
        )

    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """Create a new terminal widget."""
        widget = TerminalWidget(parent)
        widget.start_terminal()
        return widget

    def get_state(self) -> Dict[str, Any]:
        """Get widget state for persistence."""
        return {
            "session_count": len(terminal_server.sessions)
        }

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore widget state."""
        # Terminal sessions are not restored
        pass