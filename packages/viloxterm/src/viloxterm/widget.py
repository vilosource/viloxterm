"""Terminal widget implementation for ViloxTerm plugin."""

import logging
from typing import Optional, Dict, Any

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Signal
from viloapp_sdk import IWidget

from .server import terminal_server
from .features import TerminalSearch

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
        self.search = TerminalSearch()
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create web view for terminal (no toolbar)
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
            self.session_id = terminal_server.create_session(command=command, cwd=cwd)

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

    def _on_search_requested(self, pattern: str):
        """Handle search request."""
        self.search.search_in_terminal(self, pattern)

    def closeEvent(self, event):
        """Handle widget close."""
        self.stop_terminal()
        super().closeEvent(event)


class TerminalWidgetFactory(IWidget):
    """Factory for creating terminal widgets."""

    def __init__(self):
        self._instances = {}  # Track widget instances

    def get_widget_id(self) -> str:
        """Get unique widget identifier."""
        return "terminal"

    def get_title(self) -> str:
        """Get widget display title."""
        return "Terminal"

    def get_icon(self) -> Optional[str]:
        """Get widget icon identifier."""
        return "terminal"

    def create_instance(self, instance_id: str) -> QWidget:
        """Create widget instance with unique ID."""
        widget = TerminalWidget()
        widget.start_terminal()
        self._instances[instance_id] = widget

        # Connect to session ended signal to clean up
        widget.session_ended.connect(lambda session_id: self._on_session_ended(instance_id))

        return widget

    def destroy_instance(self, instance_id: str) -> None:
        """Destroy widget instance and clean up resources."""
        if instance_id in self._instances:
            widget = self._instances[instance_id]
            widget.stop_terminal()  # Clean shutdown of terminal
            widget.deleteLater()
            del self._instances[instance_id]

    def handle_command(self, command: str, args: Dict[str, Any]) -> Any:
        """Handle widget-specific commands."""
        if command == "create_terminal":
            # Create new terminal with specific parameters
            cwd = args.get("cwd")
            cmd = args.get("command")
            instance_id = args.get("instance_id", "default")

            widget = TerminalWidget()
            widget.start_terminal(command=cmd, cwd=cwd)
            self._instances[instance_id] = widget
            return widget

        elif command == "send_text":
            # Send text to specific terminal instance
            instance_id = args.get("instance_id")
            text = args.get("text", "")

            if instance_id in self._instances:
                widget = self._instances[instance_id]
                widget.send_text(text)
                return True
            return False

        elif command == "clear_terminal":
            # Clear specific terminal instance
            instance_id = args.get("instance_id")

            if instance_id in self._instances:
                widget = self._instances[instance_id]
                widget.clear_terminal()
                return True
            return False

        elif command == "focus_terminal":
            # Focus specific terminal instance
            instance_id = args.get("instance_id")

            if instance_id in self._instances:
                widget = self._instances[instance_id]
                widget.focus_terminal()
                return True
            return False

        elif command == "get_sessions":
            # Get list of active sessions
            return {
                instance_id: {
                    "session_id": widget.session_id,
                    "active": widget.session_id is not None,
                }
                for instance_id, widget in self._instances.items()
            }

        return None

    def get_state(self) -> Dict[str, Any]:
        """Get widget state for persistence."""
        return {
            "session_count": len(terminal_server.sessions),
            "instance_count": len(self._instances),
        }

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore widget state."""
        # Terminal sessions are not restored by design
        # They should be recreated fresh on startup
        pass

    def _on_session_ended(self, instance_id: str) -> None:
        """Handle session ended for cleanup."""
        # This could trigger cleanup or recreation logic
        pass
