#!/usr/bin/env python3
"""
Terminal Server Manager - Singleton server handling multiple terminal sessions.
Adapted from viloxtermjs but enhanced for multi-session support.
"""

import atexit
import logging
import os
import shlex
import signal
import struct
import sys
import threading

# Platform-specific imports
if sys.platform != 'win32':
    import pty
    import select
    import termios
else:
    # Windows doesn't have these modules
    pty = None
    select = None
    termios = None
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from flask import Flask, request
from flask_socketio import SocketIO, join_room, leave_room
from PySide6.QtCore import QObject, Signal

from ui.terminal.terminal_assets import terminal_asset_bundler

logging.getLogger("werkzeug").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


@dataclass
class TerminalSession:
    """Represents a single terminal session."""

    session_id: str
    fd: Optional[int] = None
    child_pid: Optional[int] = None
    command: str = "bash"
    cmd_args: list = field(default_factory=list)
    cwd: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    rows: int = 24
    cols: int = 80
    active: bool = True


class TerminalServerManager(QObject):
    """
    Singleton manager for terminal server.
    Handles multiple terminal sessions through a single Flask/SocketIO server.
    """

    # Signal emitted when a terminal session process exits
    session_ended = Signal(str)  # session_id

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the terminal server manager (only once)."""
        if self._initialized:
            return

        super().__init__()

        self.port = 0  # Will be assigned when server starts
        self.host = "127.0.0.1"
        self.app = None
        self.socketio = None
        self.server_thread = None
        self.sessions: dict[str, TerminalSession] = {}
        self.running = False
        self.max_sessions = 20  # Increased limit for better UX
        self._setup_flask_app()
        self._initialized = True

        # Register cleanup handlers
        atexit.register(self.shutdown)
        signal.signal(signal.SIGTERM, lambda sig, frame: self.shutdown())
        signal.signal(signal.SIGINT, lambda sig, frame: self.shutdown())

    def _setup_flask_app(self):
        """Setup Flask application with SocketIO."""
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "terminal_server_secret!"
        self.socketio = SocketIO(
            self.app, cors_allowed_origins="*", async_mode="threading"
        )

        @self.app.route("/terminal/<session_id>")
        def terminal_page(session_id):
            """Serve terminal page for a specific session."""
            if session_id not in self.sessions:
                return "Session not found", 404
            # Use bundled assets instead of serving static files
            return terminal_asset_bundler.get_bundled_html(session_id, self.port)

        @self.socketio.on("connect", namespace="/terminal")
        def handle_connect():
            """Handle client connection."""
            session_id = request.args.get("session_id")
            if not session_id or session_id not in self.sessions:
                return False

            join_room(session_id)
            logger.info(f"Client connected to session {session_id}")

            # Start terminal if not already started
            session = self.sessions[session_id]
            if not session.child_pid:
                self._start_terminal_process(session_id)

        @self.socketio.on("heartbeat", namespace="/terminal")
        def handle_heartbeat(data):
            """Handle heartbeat from client to keep session alive."""
            session_id = data.get("session_id")
            if session_id and session_id in self.sessions:
                # Update last activity time to prevent cleanup
                self.sessions[session_id].last_activity = time.time()
                logger.debug(f"Heartbeat received for session {session_id}")

        @self.socketio.on("disconnect", namespace="/terminal")
        def handle_disconnect():
            """Handle client disconnection."""
            session_id = request.args.get("session_id")
            if session_id:
                leave_room(session_id)
                logger.info(f"Client disconnected from session {session_id}")

        @self.socketio.on("pty-input", namespace="/terminal")
        def handle_pty_input(data):
            """Handle input from client."""
            session_id = data.get("session_id")
            if session_id and session_id in self.sessions:
                session = self.sessions[session_id]
                if session.fd:
                    session.last_activity = time.time()
                    os.write(session.fd, data["input"].encode())
                    logger.debug(
                        f"Input to session {session_id}: {data['input'][:20]}..."
                    )

        @self.socketio.on("resize", namespace="/terminal")
        def handle_resize(data):
            """Handle terminal resize."""
            session_id = data.get("session_id")
            if session_id and session_id in self.sessions:
                session = self.sessions[session_id]
                if session.fd:
                    session.rows = data.get("rows", 24)
                    session.cols = data.get("cols", 80)
                    self._set_winsize(session.fd, session.rows, session.cols)
                    logger.debug(
                        f"Resized session {session_id} to {session.rows}x{session.cols}"
                    )

    def _start_terminal_process(self, session_id: str):
        """Start a terminal process for a session."""
        session = self.sessions.get(session_id)
        if not session or session.child_pid:
            return

        if sys.platform == 'win32':
            # Windows doesn't support pty.fork()
            # This would require using Windows-specific APIs like ConPTY
            logger.error("Terminal sessions are not supported on Windows yet")
            return

        # Fork PTY (Unix/Linux/Mac only)
        child_pid, fd = pty.fork()
        if child_pid == 0:
            # Child process - execute shell
            # Change to working directory if specified
            if session.cwd and os.path.exists(session.cwd):
                os.chdir(session.cwd)
            subprocess_cmd = [session.command] + session.cmd_args
            os.execvp(subprocess_cmd[0], subprocess_cmd)
        else:
            # Parent process - store session info
            session.fd = fd
            session.child_pid = child_pid
            self._set_winsize(fd, session.rows, session.cols)

            # Start background task to read output
            self.socketio.start_background_task(
                target=self._read_and_forward_pty_output, session_id=session_id
            )
            logger.info(
                f"Started terminal process for session {session_id}, PID: {child_pid}"
            )

    def _read_and_forward_pty_output(self, session_id: str):
        """Read PTY output and forward to client."""
        max_read_bytes = 1024 * 20
        session = self.sessions.get(session_id)

        while self.running and session and session.active:
            if not session.fd:
                break

            try:
                if sys.platform == 'win32':
                    # Windows doesn't support select on file descriptors
                    logger.warning("Terminal output reading not supported on Windows")
                    break

                # Use select to check if data is available (Unix/Linux/Mac)
                timeout_sec = 0.01
                data_ready, _, _ = select.select([session.fd], [], [], timeout_sec)

                if data_ready:
                    output = os.read(session.fd, max_read_bytes).decode(errors="ignore")
                    self.socketio.emit(
                        "pty-output",
                        {"output": output, "session_id": session_id},
                        namespace="/terminal",
                        room=session_id,
                    )
                    session.last_activity = time.time()
            except OSError:
                # Terminal process ended
                logger.info(f"Terminal process ended for session {session_id}")
                session.active = False
                # Emit signal to notify UI that terminal session ended
                self.session_ended.emit(session_id)
                break

            self.socketio.sleep(0.01)

    def _set_winsize(self, fd: int, rows: int, cols: int, xpix: int = 0, ypix: int = 0):
        """Set terminal window size."""
        if sys.platform != 'win32':
            # Unix/Linux/Mac - use fcntl
            import fcntl
            winsize = struct.pack("HHHH", rows, cols, xpix, ypix)
            fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
        else:
            # Windows - pty.fork() doesn't work on Windows anyway
            # This is a placeholder - full Windows support would require
            # using Windows-specific APIs like ConPTY
            logger.warning("Terminal resize not fully supported on Windows")

    def create_session(
        self, command: str = "bash", cmd_args: str = "", cwd: Optional[str] = None
    ) -> str:
        """Create a new terminal session."""
        if len(self.sessions) >= self.max_sessions:
            raise RuntimeError(
                f"Maximum number of sessions ({self.max_sessions}) reached"
            )

        session_id = str(uuid.uuid4())[:8]
        args_list = shlex.split(cmd_args) if cmd_args else []

        session = TerminalSession(
            session_id=session_id, command=command, cmd_args=args_list, cwd=cwd
        )

        self.sessions[session_id] = session
        logger.info(f"Created terminal session {session_id}")

        # Start server if not running
        if not self.running:
            self.start_server()

        return session_id

    def get_terminal_url(self, session_id: str) -> str:
        """Get the terminal URL for a specific session."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        return f"http://127.0.0.1:{self.port}/terminal/{session_id}"

    def destroy_session(self, session_id: str):
        """Destroy a terminal session."""
        session = self.sessions.get(session_id)
        if not session:
            return

        session.active = False

        # Kill terminal process
        if session.child_pid:
            try:
                os.kill(session.child_pid, signal.SIGTERM)
                # Give it time to terminate gracefully
                time.sleep(0.1)
                # Force kill if still alive
                os.kill(session.child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

        # Close file descriptor
        if session.fd:
            try:
                os.close(session.fd)
            except OSError:
                pass

        # Remove from sessions
        del self.sessions[session_id]
        logger.info(f"Destroyed terminal session {session_id}")

    def start_server(self):
        """Start the Flask/SocketIO server if not already running."""
        if self.running:
            return self.port

        self.running = True

        # Find available port
        if self.port == 0:
            import socket

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", 0))
                self.port = s.getsockname()[1]

        # Start server in background thread
        def run_server():
            self.socketio.run(
                self.app,
                debug=False,
                port=self.port,
                host=self.host,
                allow_unsafe_werkzeug=True,
                use_reloader=False,
            )

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

        # Wait for server to start properly
        # Give it more time since we're loading local files now
        time.sleep(1.0)
        logger.info(f"Terminal server started on {self.host}:{self.port}")

        # Start periodic cleanup of inactive sessions
        self._start_cleanup_timer()

        return self.port

    def shutdown(self):
        """Shutdown the server and cleanup all sessions."""
        if not self.running:
            return

        logger.info("Shutting down terminal server...")
        self.running = False

        # Destroy all sessions
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            self.destroy_session(session_id)

        # Stop server
        if self.socketio:
            try:
                # Try graceful shutdown first
                if hasattr(self.socketio, "stop"):
                    self.socketio.stop()
            except (RuntimeError, AttributeError) as e:
                # If graceful shutdown fails, force cleanup
                logger.warning(f"Graceful shutdown failed: {e}. Forcing cleanup.")
                try:
                    if hasattr(self.socketio, "server") and self.socketio.server:
                        self.socketio.server.shutdown()
                except Exception:
                    pass  # Best effort cleanup

        logger.info("Terminal server shutdown complete")

    def get_session_url(self, session_id: str) -> str:
        """Get the URL for a terminal session."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        return f"http://{self.host}:{self.port}/terminal/{session_id}"

    def cleanup_inactive_sessions(self, timeout_minutes: int = 30):
        """Clean up inactive sessions."""
        current_time = time.time()
        timeout_seconds = timeout_minutes * 60

        sessions_to_remove = []
        for session_id, session in self.sessions.items():
            # Clean up inactive sessions
            if current_time - session.last_activity > timeout_seconds:
                sessions_to_remove.append(session_id)
            # Also clean up sessions where the process has died
            elif session.child_pid and not session.active:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            logger.info(f"Cleaning up inactive session {session_id}")
            self.destroy_session(session_id)

    def cleanup_all_sessions(self):
        """Clean up all terminal sessions. Called on app shutdown."""
        logger.info(f"Cleaning up all {len(self.sessions)} terminal sessions")
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            self.destroy_session(session_id)

    def _start_cleanup_timer(self):
        """Start periodic cleanup of inactive sessions."""

        def cleanup_task():
            while self.running:
                time.sleep(60)  # Run cleanup every minute
                try:
                    # Increased timeout to 60 minutes since we have heartbeat mechanism
                    # Sessions with active heartbeats will never be cleaned up
                    self.cleanup_inactive_sessions(timeout_minutes=60)  # 60 min timeout
                except Exception as e:
                    logger.error(f"Error during session cleanup: {e}")

        if self.running:
            cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
            cleanup_thread.start()


# Create singleton instance
terminal_server = TerminalServerManager()
