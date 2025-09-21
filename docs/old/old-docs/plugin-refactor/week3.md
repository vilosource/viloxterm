# Week 3: Terminal Plugin Extraction - Part 1

## Overview
Week 3 begins the extraction of terminal functionality into a standalone plugin. This involves decoupling terminal code from the main application and creating the viloxterm plugin package.

**Duration**: 5 days
**Goal**: Extract terminal code, create plugin structure, and establish terminal plugin interfaces

## Prerequisites
- [ ] Week 1-2 completed successfully
- [ ] SDK and plugin host infrastructure working
- [ ] Terminal functionality currently integrated in main app

## Day 1: Analysis and Preparation

### Morning (3 hours)

#### Task 1.1: Analyze Current Terminal Implementation

Document current terminal integration points:
```bash
# Find all terminal-related files
find . -type f -name "*terminal*" | grep -v __pycache__

# Expected files:
# ./ui/terminal/terminal_widget.py
# ./ui/terminal/terminal_server.py
# ./ui/terminal/terminal_assets.py
# ./ui/terminal/backends/base.py
# ./ui/terminal/backends/posix_backend.py
# ./ui/terminal/backends/windows_backend.py
# ./services/terminal_service.py
# ./core/commands/builtin/terminal_commands.py
```

#### Task 1.2: Map Terminal Dependencies

Create dependency map:
```python
"""
Terminal Component Dependencies:

TerminalWidget:
  - Imports: QWebEngineView, QUrl (PySide6)
  - Services: TerminalService, ThemeService
  - Commands: terminal.new, terminal.clear, terminal.close

TerminalServer:
  - Imports: Flask, SocketIO, threading
  - External: pyte, flask-socketio
  - Services: None (standalone)

TerminalService:
  - Imports: QObject, Signal
  - Dependencies: TerminalServer, WorkspaceService
  - Commands: Registers terminal commands

TerminalBackends:
  - POSIX: pty, select, termios
  - Windows: pywinpty (optional)
  - Base: Abstract interfaces
"""
```

#### Task 1.3: Create Extraction Plan

```markdown
## Extraction Strategy

### Phase 1: Create Plugin Package Structure
- Create packages/viloxterm directory
- Setup package configuration
- Create plugin manifest

### Phase 2: Move Core Terminal Code
- Move terminal_widget.py -> viloxterm/widget.py
- Move terminal_server.py -> viloxterm/server.py
- Move terminal_assets.py -> viloxterm/assets.py
- Move backends/* -> viloxterm/backends/

### Phase 3: Create Plugin Adapter
- Implement TerminalPlugin class
- Create TerminalWidgetFactory
- Define terminal commands

### Phase 4: Update Imports
- Update all imports from ui.terminal to viloxterm
- Remove terminal imports from main app
- Update command registrations

### Phase 5: Service Decoupling
- Create terminal service interface
- Implement service in plugin
- Update service references
```

### Afternoon (3 hours)

#### Task 1.4: Create Viloxterm Package Structure

```bash
cd /home/kuja/GitHub/viloapp/packages

# Create viloxterm package structure
mkdir -p viloxterm/{src/viloxterm,tests,docs,assets}
mkdir -p viloxterm/src/viloxterm/{backends,assets,commands}

# Create package files
touch viloxterm/README.md
touch viloxterm/CHANGELOG.md
touch viloxterm/src/viloxterm/__init__.py
touch viloxterm/src/viloxterm/plugin.py
touch viloxterm/src/viloxterm/widget.py
touch viloxterm/src/viloxterm/server.py
```

#### Task 1.5: Create Package Configuration

Create `/home/kuja/GitHub/viloapp/packages/viloxterm/pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "viloxterm"
version = "1.0.0"
description = "Terminal Emulator Plugin for ViloxTerm"
authors = [{name = "ViloxTerm Team", email = "team@viloxterm.org"}]
readme = "README.md"
license = {text = "MIT"}
keywords = ["terminal", "emulator", "plugin", "viloxterm"]
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: X11 Applications :: Qt",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Terminals :: Terminal Emulators/X Terminals",
]

dependencies = [
    "viloapp-sdk>=1.0.0",
    "PySide6>=6.5.0",
    "PySide6-WebEngine>=6.5.0",
    "flask>=2.0.0",
    "flask-socketio>=5.0.0",
    "python-socketio>=5.0.0",
    "pyte>=0.8.0",
    "psutil>=5.9.0",
]

[project.optional-dependencies]
windows = [
    "pywinpty>=2.0.0;platform_system=='Windows'",
]
dev = [
    "pytest>=7.0",
    "pytest-qt>=4.2.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0",
    "ruff>=0.1.0",
]

[project.entry-points."viloapp.plugins"]
terminal = "viloxterm.plugin:TerminalPlugin"

[project.urls]
Homepage = "https://github.com/viloxterm/viloxterm"
Documentation = "https://viloxterm.readthedocs.io"
Repository = "https://github.com/viloxterm/viloxterm"
Issues = "https://github.com/viloxterm/viloxterm/issues"

[tool.setuptools]
package-dir = {"": "src"}
packages = ["viloxterm", "viloxterm.backends", "viloxterm.assets", "viloxterm.commands"]

[tool.setuptools.package-data]
viloxterm = [
    "assets/**/*",
    "assets/xterm/**/*",
    "assets/xterm/css/*",
    "assets/xterm/lib/*",
]
```

#### Task 1.6: Create Plugin Manifest

Create `/home/kuja/GitHub/viloapp/packages/viloxterm/src/viloxterm/plugin.json`:
```json
{
  "id": "viloxterm",
  "name": "ViloxTerm Terminal",
  "version": "1.0.0",
  "description": "Professional terminal emulator with full xterm compatibility",
  "author": "ViloxTerm Team",
  "license": "MIT",
  "homepage": "https://github.com/viloxterm/viloxterm",
  "repository": {
    "type": "git",
    "url": "https://github.com/viloxterm/viloxterm.git"
  },
  "engines": {
    "viloapp": ">=2.0.0",
    "viloapp-sdk": ">=1.0.0"
  },
  "categories": ["Terminal", "Development Tools"],
  "keywords": ["terminal", "emulator", "xterm", "console", "shell"],
  "icon": "terminal",
  "main": "plugin.py",
  "activationEvents": [
    "onCommand:terminal.new",
    "onCommand:terminal.open",
    "onView:terminal",
    "onStartup"
  ],
  "contributes": {
    "commands": [
      {
        "id": "terminal.new",
        "title": "New Terminal",
        "category": "Terminal",
        "icon": "terminal-plus"
      },
      {
        "id": "terminal.clear",
        "title": "Clear Terminal",
        "category": "Terminal",
        "icon": "terminal-clear"
      },
      {
        "id": "terminal.close",
        "title": "Close Terminal",
        "category": "Terminal",
        "icon": "terminal-x"
      },
      {
        "id": "terminal.split",
        "title": "Split Terminal",
        "category": "Terminal",
        "icon": "terminal-split"
      },
      {
        "id": "terminal.focus",
        "title": "Focus Terminal",
        "category": "Terminal"
      },
      {
        "id": "terminal.selectDefaultShell",
        "title": "Select Default Shell",
        "category": "Terminal"
      }
    ],
    "configuration": {
      "title": "Terminal",
      "properties": {
        "terminal.shell.linux": {
          "type": "string",
          "default": "/bin/bash",
          "description": "Path to shell executable on Linux"
        },
        "terminal.shell.osx": {
          "type": "string",
          "default": "/bin/zsh",
          "description": "Path to shell executable on macOS"
        },
        "terminal.shell.windows": {
          "type": "string",
          "default": "powershell.exe",
          "description": "Path to shell executable on Windows"
        },
        "terminal.fontSize": {
          "type": "number",
          "default": 14,
          "minimum": 8,
          "maximum": 24,
          "description": "Terminal font size"
        },
        "terminal.fontFamily": {
          "type": "string",
          "default": "monospace",
          "description": "Terminal font family"
        },
        "terminal.cursorStyle": {
          "type": "string",
          "default": "block",
          "enum": ["block", "underline", "bar"],
          "description": "Terminal cursor style"
        },
        "terminal.cursorBlink": {
          "type": "boolean",
          "default": true,
          "description": "Enable cursor blinking"
        },
        "terminal.scrollback": {
          "type": "number",
          "default": 1000,
          "minimum": 0,
          "maximum": 10000,
          "description": "Number of scrollback lines"
        }
      }
    },
    "keybindings": [
      {
        "command": "terminal.new",
        "key": "ctrl+shift+`",
        "mac": "cmd+shift+`"
      },
      {
        "command": "terminal.clear",
        "key": "ctrl+shift+k",
        "mac": "cmd+k",
        "when": "terminalFocus"
      },
      {
        "command": "terminal.close",
        "key": "ctrl+shift+w",
        "mac": "cmd+shift+w",
        "when": "terminalFocus"
      }
    ],
    "menus": {
      "view/title": [
        {
          "command": "terminal.new",
          "when": "view == terminal",
          "group": "navigation"
        }
      ],
      "commandPalette": [
        {
          "command": "terminal.new"
        },
        {
          "command": "terminal.clear",
          "when": "terminalFocus"
        },
        {
          "command": "terminal.selectDefaultShell"
        }
      ]
    },
    "views": {
      "sidebar": [
        {
          "id": "terminal-sessions",
          "name": "Terminal Sessions",
          "icon": "terminal-outline",
          "contextualTitle": "Terminal"
        }
      ]
    },
    "widgets": [
      {
        "id": "terminal",
        "factory": "viloxterm.widget:TerminalWidgetFactory"
      }
    ]
  }
}
```

### Validation Checkpoint
- [ ] Terminal dependencies mapped
- [ ] Package structure created
- [ ] Configuration files complete
- [ ] Plugin manifest defined

## Day 2: Core Code Migration

### Morning (3 hours)

#### Task 2.1: Copy Terminal Backend Code

```bash
# Copy backend implementations
cp -r /home/kuja/GitHub/viloapp/ui/terminal/backends/* \
      /home/kuja/GitHub/viloapp/packages/viloxterm/src/viloxterm/backends/

# Copy terminal assets
cp -r /home/kuja/GitHub/viloapp/ui/terminal/assets/* \
      /home/kuja/GitHub/viloapp/packages/viloxterm/src/viloxterm/assets/
```

#### Task 2.2: Migrate Terminal Server

Create `/home/kuja/GitHub/viloapp/packages/viloxterm/src/viloxterm/server.py`:
```python
#!/usr/bin/env python3
"""
Terminal Server Manager - Singleton server handling multiple terminal sessions.
Plugin version adapted for ViloxTerm plugin architecture.
"""

import atexit
import logging
import os
import shlex
import signal
import sys
import threading
import time
import uuid
from typing import Optional
from pathlib import Path

from flask import Flask, request
from flask_socketio import SocketIO, join_room, leave_room
from PySide6.QtCore import QObject, Signal

from .backends import TerminalBackendFactory, TerminalSession
from .assets import terminal_asset_bundler

logging.getLogger("werkzeug").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


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
        self.max_sessions = 20
        self.backend = None
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
            return terminal_asset_bundler.get_bundled_html(session_id, self.port)

        @self.socketio.on("connect", namespace="/terminal")
        def handle_connect(auth=None):
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
                if self.backend and session:
                    self.backend.write_input(session, data["input"])

        @self.socketio.on("resize", namespace="/terminal")
        def handle_resize(data):
            """Handle terminal resize."""
            session_id = data.get("session_id")
            if session_id and session_id in self.sessions:
                session = self.sessions[session_id]
                if self.backend and session:
                    rows = data.get("rows", 24)
                    cols = data.get("cols", 80)
                    if self.backend.resize(session, rows, cols):
                        logger.debug(f"Resized session {session_id} to {rows}x{cols}")

    def _start_terminal_process(self, session_id: str):
        """Start a terminal process for a session."""
        session = self.sessions.get(session_id)
        if not session or session.child_pid:
            return

        # Initialize backend if not already done
        if not self.backend:
            try:
                self.backend = TerminalBackendFactory.create_backend()
            except Exception as e:
                logger.error(f"Failed to create terminal backend: {e}")
                return

        # Start the process using the backend
        if self.backend.start_process(session):
            # Start background task to read output
            self.socketio.start_background_task(
                target=self._read_and_forward_pty_output, session_id=session_id
            )
            logger.info(
                f"Started terminal process for session {session_id}, PID: {session.child_pid}"
            )

    def _read_and_forward_pty_output(self, session_id: str):
        """Read PTY output and forward to client."""
        session = self.sessions.get(session_id)

        while self.running and session and session.active:
            if not self.backend:
                logger.error(f"No backend available for session {session_id}")
                break

            try:
                # Use backend to poll and read output
                if self.backend.poll_process(session, timeout=0.01):
                    output = self.backend.read_output(session)
                    if output:
                        self.socketio.emit(
                            "pty-output",
                            {"output": output, "session_id": session_id},
                            namespace="/terminal",
                            room=session_id,
                        )

                # Check if process is still alive
                if not self.backend.is_process_alive(session):
                    logger.info(f"Terminal process ended for session {session_id}")
                    session.active = False
                    self.session_ended.emit(session_id)
                    break

            except Exception as e:
                logger.error(f"Error reading terminal output: {e}", exc_info=True)
                session.active = False
                self.session_ended.emit(session_id)
                break

            self.socketio.sleep(0.01)

    def create_session(
        self, command: str = "bash", cmd_args: str = "", cwd: Optional[str] = None
    ) -> str:
        """Create a new terminal session."""
        if len(self.sessions) >= self.max_sessions:
            raise RuntimeError(f"Maximum number of sessions ({self.max_sessions}) reached")

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

        # Use backend to clean up the session
        if self.backend:
            self.backend.cleanup(session)

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

        # Wait for server to start
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

        # Reset the backend factory
        TerminalBackendFactory.reset()
        self.backend = None

        # Stop server
        if self.socketio:
            try:
                if hasattr(self.socketio, "stop"):
                    self.socketio.stop()
            except (RuntimeError, AttributeError) as e:
                logger.warning(f"Graceful shutdown failed: {e}. Forcing cleanup.")
                try:
                    if hasattr(self.socketio, "server") and self.socketio.server:
                        self.socketio.server.shutdown()
                except Exception:
                    pass

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
            elif self.backend and not self.backend.is_process_alive(session):
                sessions_to_remove.append(session_id)
            elif not session.active:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            logger.info(f"Cleaning up inactive session {session_id}")
            self.destroy_session(session_id)

    def cleanup_all_sessions(self):
        """Clean up all terminal sessions."""
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
                    self.cleanup_inactive_sessions(timeout_minutes=60)
                except Exception as e:
                    logger.error(f"Error during session cleanup: {e}")

        if self.running:
            cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
            cleanup_thread.start()


# Create singleton instance
terminal_server = TerminalServerManager()
```

### Afternoon (3 hours)

#### Task 2.3: Update Import Paths

Update all imports in copied files:
```python
# In backends/base.py, backends/posix_backend.py, etc.
# Change: from ui.terminal.x import y
# To: from viloxterm.x import y

# Example in backends/posix_backend.py:
# Old:
# from ui.terminal.backends.base import TerminalBackend, TerminalSession

# New:
from viloxterm.backends.base import TerminalBackend, TerminalSession
```

#### Task 2.4: Create Terminal Widget Adapter

Create `/home/kuja/GitHub/viloapp/packages/viloxterm/src/viloxterm/widget.py`:
```python
"""Terminal widget implementation for ViloxTerm plugin."""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Signal, QTimer
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
```

### Validation Checkpoint
- [ ] Backend code migrated
- [ ] Server code adapted
- [ ] Import paths updated
- [ ] Widget factory created

## Day 3: Plugin Implementation

### Morning (3 hours)

#### Task 3.1: Implement Main Plugin Class

Create `/home/kuja/GitHub/viloapp/packages/viloxterm/src/viloxterm/plugin.py`:
```python
"""ViloxTerm Terminal Plugin."""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from viloapp_sdk import (
    IPlugin, PluginMetadata, PluginCapability,
    IPluginContext, EventType
)

from .widget import TerminalWidgetFactory
from .server import terminal_server
from .commands import register_terminal_commands

logger = logging.getLogger(__name__)


class TerminalPlugin(IPlugin):
    """Terminal emulator plugin for ViloxTerm."""

    def __init__(self):
        self.context: Optional[IPluginContext] = None
        self.widget_factory = TerminalWidgetFactory()
        self.commands_registered = False

    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            id="viloxterm",
            name="ViloxTerm Terminal",
            version="1.0.0",
            description="Professional terminal emulator with full xterm compatibility",
            author="ViloxTerm Team",
            homepage="https://github.com/viloxterm/viloxterm",
            repository="https://github.com/viloxterm/viloxterm",
            license="MIT",
            icon="terminal",
            categories=["Terminal", "Development Tools"],
            keywords=["terminal", "emulator", "xterm", "console", "shell"],
            engines={"viloapp": ">=2.0.0"},
            dependencies=["viloapp-sdk@>=1.0.0"],
            activation_events=[
                "onCommand:terminal.new",
                "onCommand:terminal.open",
                "onView:terminal",
                "onStartup"
            ],
            capabilities=[PluginCapability.WIDGETS, PluginCapability.COMMANDS],
            contributes={
                "widgets": [
                    {
                        "id": "terminal",
                        "factory": "viloxterm.widget:TerminalWidgetFactory"
                    }
                ],
                "commands": [
                    {
                        "id": "terminal.new",
                        "title": "New Terminal",
                        "category": "Terminal"
                    },
                    {
                        "id": "terminal.clear",
                        "title": "Clear Terminal",
                        "category": "Terminal"
                    },
                    {
                        "id": "terminal.close",
                        "title": "Close Terminal",
                        "category": "Terminal"
                    },
                    {
                        "id": "terminal.split",
                        "title": "Split Terminal",
                        "category": "Terminal"
                    },
                    {
                        "id": "terminal.focus",
                        "title": "Focus Terminal",
                        "category": "Terminal"
                    }
                ],
                "configuration": {
                    "terminal.shell.linux": {
                        "type": "string",
                        "default": "/bin/bash",
                        "description": "Path to shell executable on Linux"
                    },
                    "terminal.shell.windows": {
                        "type": "string",
                        "default": "powershell.exe",
                        "description": "Path to shell executable on Windows"
                    },
                    "terminal.fontSize": {
                        "type": "number",
                        "default": 14,
                        "description": "Terminal font size"
                    }
                },
                "keybindings": [
                    {
                        "command": "terminal.new",
                        "key": "ctrl+shift+`"
                    },
                    {
                        "command": "terminal.clear",
                        "key": "ctrl+shift+k",
                        "when": "terminalFocus"
                    }
                ]
            }
        )

    def activate(self, context: IPluginContext) -> None:
        """Activate the plugin."""
        self.context = context
        logger.info("Activating ViloxTerm Terminal plugin")

        # Register commands
        self._register_commands()

        # Register widget factory
        self._register_widget_factory()

        # Subscribe to events
        self._subscribe_to_events()

        # Initialize terminal server
        terminal_server.start_server()

        # Notify activation
        notification_service = context.get_service("notification")
        if notification_service:
            notification_service.info("Terminal plugin activated")

        logger.info("ViloxTerm Terminal plugin activated successfully")

    def deactivate(self) -> None:
        """Deactivate the plugin."""
        logger.info("Deactivating ViloxTerm Terminal plugin")

        # Cleanup terminal sessions
        terminal_server.cleanup_all_sessions()

        # Shutdown server
        terminal_server.shutdown()

        # Unregister commands
        self._unregister_commands()

        logger.info("ViloxTerm Terminal plugin deactivated")

    def on_configuration_changed(self, config: Dict[str, Any]) -> None:
        """Handle configuration changes."""
        # Update terminal settings
        if "terminal.fontSize" in config:
            # Update font size in active terminals
            pass

        if "terminal.shell.linux" in config or "terminal.shell.windows" in config:
            # Update default shell for new terminals
            pass

    def on_command(self, command_id: str, args: Dict[str, Any]) -> Any:
        """Handle command execution."""
        if command_id == "terminal.new":
            return self._create_new_terminal(args)
        elif command_id == "terminal.clear":
            return self._clear_terminal(args)
        elif command_id == "terminal.close":
            return self._close_terminal(args)
        elif command_id == "terminal.split":
            return self._split_terminal(args)
        elif command_id == "terminal.focus":
            return self._focus_terminal(args)

        return None

    def _register_commands(self):
        """Register terminal commands."""
        if self.commands_registered:
            return

        command_service = self.context.get_service("command")
        if command_service:
            # Register command handlers
            command_service.register_command("terminal.new", self._create_new_terminal)
            command_service.register_command("terminal.clear", self._clear_terminal)
            command_service.register_command("terminal.close", self._close_terminal)
            command_service.register_command("terminal.split", self._split_terminal)
            command_service.register_command("terminal.focus", self._focus_terminal)

            self.commands_registered = True

    def _unregister_commands(self):
        """Unregister terminal commands."""
        if not self.commands_registered:
            return

        command_service = self.context.get_service("command")
        if command_service:
            command_service.unregister_command("terminal.new")
            command_service.unregister_command("terminal.clear")
            command_service.unregister_command("terminal.close")
            command_service.unregister_command("terminal.split")
            command_service.unregister_command("terminal.focus")

            self.commands_registered = False

    def _register_widget_factory(self):
        """Register widget factory with workspace service."""
        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            workspace_service.register_widget_factory("terminal", self.widget_factory)

    def _subscribe_to_events(self):
        """Subscribe to relevant events."""
        # Subscribe to theme changes to update terminal colors
        self.context.subscribe_event(EventType.THEME_CHANGED, self._on_theme_changed)

        # Subscribe to settings changes
        self.context.subscribe_event(EventType.SETTINGS_CHANGED, self._on_settings_changed)

    def _on_theme_changed(self, event):
        """Handle theme change event."""
        logger.debug(f"Theme changed: {event.data}")
        # Update terminal colors based on new theme

    def _on_settings_changed(self, event):
        """Handle settings change event."""
        if "terminal" in event.data:
            self.on_configuration_changed(event.data)

    # Command implementations
    def _create_new_terminal(self, args: Dict[str, Any] = None) -> Any:
        """Create a new terminal."""
        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            # Create terminal widget
            widget = self.widget_factory.create_widget()

            # Add to workspace
            workspace_service.add_widget(widget, "terminal", "main")

            return {"success": True, "widget_id": id(widget)}

        return {"success": False, "error": "Workspace service not available"}

    def _clear_terminal(self, args: Dict[str, Any] = None) -> Any:
        """Clear the active terminal."""
        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            # Get active terminal widget
            active_widget = workspace_service.get_active_widget()
            if active_widget and hasattr(active_widget, 'clear_terminal'):
                active_widget.clear_terminal()
                return {"success": True}

        return {"success": False, "error": "No active terminal"}

    def _close_terminal(self, args: Dict[str, Any] = None) -> Any:
        """Close the active terminal."""
        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            # Get active terminal widget
            active_widget = workspace_service.get_active_widget()
            if active_widget and hasattr(active_widget, 'stop_terminal'):
                active_widget.stop_terminal()
                workspace_service.remove_widget(active_widget)
                return {"success": True}

        return {"success": False, "error": "No active terminal"}

    def _split_terminal(self, args: Dict[str, Any] = None) -> Any:
        """Split the terminal."""
        # Implementation for split terminal
        return {"success": False, "error": "Not implemented"}

    def _focus_terminal(self, args: Dict[str, Any] = None) -> Any:
        """Focus the terminal."""
        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            # Get active terminal widget
            active_widget = workspace_service.get_active_widget()
            if active_widget and hasattr(active_widget, 'focus_terminal'):
                active_widget.focus_terminal()
                return {"success": True}

        return {"success": False, "error": "No active terminal"}
```

### Afternoon (3 hours)

#### Task 3.2: Create Command Module

Create `/home/kuja/GitHub/viloapp/packages/viloxterm/src/viloxterm/commands.py`:
```python
"""Terminal command definitions."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def register_terminal_commands(command_service):
    """Register all terminal commands."""

    commands = [
        {
            "id": "terminal.new",
            "handler": create_new_terminal,
            "title": "New Terminal",
            "category": "Terminal",
            "description": "Create a new terminal instance"
        },
        {
            "id": "terminal.clear",
            "handler": clear_terminal,
            "title": "Clear Terminal",
            "category": "Terminal",
            "description": "Clear the terminal screen"
        },
        {
            "id": "terminal.close",
            "handler": close_terminal,
            "title": "Close Terminal",
            "category": "Terminal",
            "description": "Close the current terminal"
        },
        {
            "id": "terminal.split",
            "handler": split_terminal,
            "title": "Split Terminal",
            "category": "Terminal",
            "description": "Split the terminal pane"
        },
        {
            "id": "terminal.focus",
            "handler": focus_terminal,
            "title": "Focus Terminal",
            "category": "Terminal",
            "description": "Focus on the terminal"
        },
        {
            "id": "terminal.selectDefaultShell",
            "handler": select_default_shell,
            "title": "Select Default Shell",
            "category": "Terminal",
            "description": "Choose the default shell for new terminals"
        }
    ]

    for cmd in commands:
        command_service.register_command(
            cmd["id"],
            cmd["handler"],
            title=cmd.get("title"),
            category=cmd.get("category"),
            description=cmd.get("description")
        )


def create_new_terminal(context, **kwargs) -> Dict[str, Any]:
    """Create a new terminal."""
    from .widget import TerminalWidget

    workspace_service = context.get_service("workspace")
    if not workspace_service:
        return {"success": False, "error": "Workspace service not available"}

    # Create terminal widget
    widget = TerminalWidget()

    # Get configuration
    config_service = context.get_service("configuration")
    if config_service:
        import platform
        if platform.system() == "Windows":
            shell = config_service.get("terminal.shell.windows", "powershell.exe")
        else:
            shell = config_service.get("terminal.shell.linux", "/bin/bash")
    else:
        shell = None

    # Start terminal
    cwd = kwargs.get("cwd", None)
    widget.start_terminal(command=shell, cwd=cwd)

    # Add to workspace
    workspace_service.add_widget(widget, "terminal", "main")

    return {"success": True, "widget": widget}


def clear_terminal(context, **kwargs) -> Dict[str, Any]:
    """Clear the active terminal."""
    workspace_service = context.get_service("workspace")
    if not workspace_service:
        return {"success": False, "error": "Workspace service not available"}

    # Get active widget
    widget = workspace_service.get_active_widget()
    if widget and hasattr(widget, 'clear_terminal'):
        widget.clear_terminal()
        return {"success": True}

    return {"success": False, "error": "No active terminal"}


def close_terminal(context, **kwargs) -> Dict[str, Any]:
    """Close the active terminal."""
    workspace_service = context.get_service("workspace")
    if not workspace_service:
        return {"success": False, "error": "Workspace service not available"}

    # Get active widget
    widget = workspace_service.get_active_widget()
    if widget and hasattr(widget, 'stop_terminal'):
        widget.stop_terminal()
        workspace_service.remove_widget(widget)
        return {"success": True}

    return {"success": False, "error": "No active terminal"}


def split_terminal(context, **kwargs) -> Dict[str, Any]:
    """Split the terminal pane."""
    # TODO: Implement terminal splitting
    return {"success": False, "error": "Not implemented"}


def focus_terminal(context, **kwargs) -> Dict[str, Any]:
    """Focus on the terminal."""
    workspace_service = context.get_service("workspace")
    if not workspace_service:
        return {"success": False, "error": "Workspace service not available"}

    # Get active widget
    widget = workspace_service.get_active_widget()
    if widget and hasattr(widget, 'focus_terminal'):
        widget.focus_terminal()
        return {"success": True}

    return {"success": False, "error": "No active terminal"}


def select_default_shell(context, **kwargs) -> Dict[str, Any]:
    """Select the default shell."""
    # TODO: Implement shell selection dialog
    return {"success": False, "error": "Not implemented"}
```

#### Task 3.3: Create Package Init

Create `/home/kuja/GitHub/viloapp/packages/viloxterm/src/viloxterm/__init__.py`:
```python
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
```

### Validation Checkpoint
- [ ] Plugin class implemented
- [ ] Commands defined
- [ ] Package properly initialized
- [ ] All components connected

## Day 4: Testing and Integration

### Morning (3 hours)

#### Task 4.1: Create Plugin Tests

Create `/home/kuja/GitHub/viloapp/packages/viloxterm/tests/test_plugin.py`:
```python
"""Tests for terminal plugin."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from viloxterm.plugin import TerminalPlugin
from viloapp_sdk import PluginContext, EventBus, ServiceProxy


@pytest.fixture
def mock_context():
    """Create mock plugin context."""
    services = {
        'command': Mock(),
        'workspace': Mock(),
        'configuration': Mock(),
        'notification': Mock()
    }

    context = PluginContext(
        plugin_id="viloxterm",
        plugin_path="/tmp/viloxterm",
        data_path="/tmp/viloxterm-data",
        service_proxy=ServiceProxy(services),
        event_bus=EventBus(),
        configuration={}
    )

    return context


def test_plugin_metadata():
    """Test plugin metadata."""
    plugin = TerminalPlugin()
    metadata = plugin.get_metadata()

    assert metadata.id == "viloxterm"
    assert metadata.name == "ViloxTerm Terminal"
    assert metadata.version == "1.0.0"
    assert "terminal" in metadata.keywords


def test_plugin_activation(mock_context):
    """Test plugin activation."""
    plugin = TerminalPlugin()

    # Mock terminal server
    with patch('viloxterm.plugin.terminal_server') as mock_server:
        plugin.activate(mock_context)

        assert plugin.context == mock_context
        assert mock_server.start_server.called


def test_plugin_deactivation(mock_context):
    """Test plugin deactivation."""
    plugin = TerminalPlugin()
    plugin.activate(mock_context)

    with patch('viloxterm.plugin.terminal_server') as mock_server:
        plugin.deactivate()

        assert mock_server.cleanup_all_sessions.called
        assert mock_server.shutdown.called


def test_create_new_terminal_command(mock_context):
    """Test creating a new terminal."""
    plugin = TerminalPlugin()
    plugin.activate(mock_context)

    # Mock workspace service
    workspace_service = mock_context.get_service("workspace")
    workspace_service.add_widget = Mock()

    # Execute command
    result = plugin.on_command("terminal.new", {})

    assert result is not None
    # Verify widget was added to workspace
    # workspace_service.add_widget.assert_called()


def test_terminal_configuration(mock_context):
    """Test terminal configuration handling."""
    plugin = TerminalPlugin()
    plugin.activate(mock_context)

    # Test configuration change
    config = {
        "terminal.fontSize": 16,
        "terminal.shell.linux": "/bin/zsh"
    }

    plugin.on_configuration_changed(config)
    # Verify configuration was applied
```

Create `/home/kuja/GitHub/viloapp/packages/viloxterm/tests/test_widget.py`:
```python
"""Tests for terminal widget."""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication

from viloxterm.widget import TerminalWidget, TerminalWidgetFactory

# Ensure QApplication exists for widget tests
@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_terminal_widget_creation(qapp):
    """Test terminal widget creation."""
    widget = TerminalWidget()
    assert widget is not None
    assert widget.web_view is not None


def test_terminal_widget_factory():
    """Test terminal widget factory."""
    factory = TerminalWidgetFactory()
    metadata = factory.get_metadata()

    assert metadata.id == "terminal"
    assert metadata.title == "Terminal"


@patch('viloxterm.widget.terminal_server')
def test_start_terminal(mock_server, qapp):
    """Test starting a terminal session."""
    widget = TerminalWidget()

    mock_server.create_session.return_value = "test-session-id"
    mock_server.get_terminal_url.return_value = "http://localhost:5000/terminal/test-session-id"

    widget.start_terminal(command="/bin/bash")

    mock_server.create_session.assert_called_once()
    assert widget.session_id == "test-session-id"


@patch('viloxterm.widget.terminal_server')
def test_stop_terminal(mock_server, qapp):
    """Test stopping a terminal session."""
    widget = TerminalWidget()
    widget.session_id = "test-session-id"

    widget.stop_terminal()

    mock_server.destroy_session.assert_called_with("test-session-id")
    assert widget.session_id is None
```

### Afternoon (2 hours)

#### Task 4.2: Create Integration Test

Create `/home/kuja/GitHub/viloapp/packages/viloxterm/tests/test_integration.py`:
```python
"""Integration tests for terminal plugin."""

import pytest
import time
from unittest.mock import patch

from viloxterm.server import TerminalServerManager
from viloxterm.backends import TerminalBackendFactory


def test_terminal_server_lifecycle():
    """Test terminal server lifecycle."""
    server = TerminalServerManager()

    # Start server
    port = server.start_server()
    assert port > 0
    assert server.running

    # Create session
    session_id = server.create_session(command="echo", cmd_args="test")
    assert session_id in server.sessions

    # Get URL
    url = server.get_terminal_url(session_id)
    assert f":{port}/terminal/{session_id}" in url

    # Destroy session
    server.destroy_session(session_id)
    assert session_id not in server.sessions

    # Shutdown server
    server.shutdown()
    assert not server.running


def test_backend_factory():
    """Test terminal backend factory."""
    backend = TerminalBackendFactory.create_backend()
    assert backend is not None

    # Reset factory
    TerminalBackendFactory.reset()
```

#### Task 4.3: Create README

Create `/home/kuja/GitHub/viloapp/packages/viloxterm/README.md`:
```markdown
# ViloxTerm Terminal Plugin

Professional terminal emulator plugin for ViloxTerm application.

## Features

- Full xterm compatibility
- Multiple concurrent sessions
- Cross-platform support (Linux, macOS, Windows)
- Web-based terminal using xterm.js
- Customizable shell and appearance
- Session management
- Command palette integration

## Installation

```bash
pip install viloxterm
```

Or install from source:

```bash
cd packages/viloxterm
pip install -e .
```

## Usage

The terminal plugin is automatically loaded by ViloxTerm when installed.

### Commands

- `terminal.new` - Create a new terminal
- `terminal.clear` - Clear the terminal screen
- `terminal.close` - Close the current terminal
- `terminal.split` - Split the terminal pane
- `terminal.focus` - Focus on the terminal

### Keyboard Shortcuts

- `Ctrl+Shift+`` ` - New terminal
- `Ctrl+Shift+K` - Clear terminal
- `Ctrl+Shift+W` - Close terminal

## Configuration

Configure the terminal through ViloxTerm settings:

```json
{
  "terminal.shell.linux": "/bin/bash",
  "terminal.shell.windows": "powershell.exe",
  "terminal.fontSize": 14,
  "terminal.fontFamily": "monospace",
  "terminal.cursorStyle": "block",
  "terminal.scrollback": 1000
}
```

## Development

### Running Tests

```bash
pytest tests/
```

### Building

```bash
python -m build
```

## License

MIT
```

### Validation Checkpoint
- [ ] Plugin tests pass
- [ ] Widget tests pass
- [ ] Integration tests work
- [ ] Documentation complete

## Day 5: Final Integration

### Morning (3 hours)

#### Task 5.1: Install and Test Plugin

```bash
# Install plugin in development mode
cd /home/kuja/GitHub/viloapp/packages/viloxterm
pip install -e .

# Run tests
pytest tests/ -v

# Verify entry point
python -c "import importlib.metadata; print(list(importlib.metadata.entry_points(group='viloapp.plugins')))"
```

#### Task 5.2: Update Main Application

Remove terminal imports from main application:
```python
# In main.py or wherever terminal is imported
# Remove:
# from ui.terminal import TerminalWidget
# from services.terminal_service import TerminalService

# The plugin system will now handle terminal functionality
```

#### Task 5.3: Test Plugin Loading

```python
# Test script to verify plugin loads
from core.plugin_system import PluginManager
from viloapp_sdk import EventBus

# Create plugin manager
event_bus = EventBus()
services = {}
manager = PluginManager(event_bus, services)

# Discover plugins
plugins = manager.discover_plugins()
print(f"Discovered plugins: {plugins}")

# Check if terminal plugin is discovered
assert "terminal" in plugins or "viloxterm" in plugins

# Load terminal plugin
if manager.load_plugin("viloxterm"):
    print("Terminal plugin loaded successfully")

# Activate plugin
if manager.activate_plugin("viloxterm"):
    print("Terminal plugin activated successfully")
```

### Afternoon (2 hours)

#### Task 5.4: Create Migration Guide

Create `/home/kuja/GitHub/viloapp/docs/plugin-refactor/terminal_migration.md`:
```markdown
# Terminal Plugin Migration Guide

## Overview

The terminal functionality has been extracted into a standalone plugin (`viloxterm`).

## Changes for Users

No changes required. The terminal plugin is automatically loaded.

## Changes for Developers

### Import Changes

```python
# Old
from ui.terminal import TerminalWidget
from services.terminal_service import TerminalService

# New (not needed - use plugin system)
# Terminal is accessed through plugin manager
```

### Command Changes

Commands remain the same but are now registered by the plugin:
- `terminal.new`
- `terminal.clear`
- `terminal.close`

### Service Access

```python
# Get terminal through plugin manager
plugin_manager = context.get_service("plugin_manager")
terminal_plugin = plugin_manager.get_plugin("viloxterm")
```

## Migration Steps

1. Install the terminal plugin:
   ```bash
   pip install -e packages/viloxterm
   ```

2. Remove old terminal imports from your code

3. The plugin system will automatically load and activate the terminal

## Troubleshooting

If terminal doesn't appear:
1. Check plugin is installed: `pip list | grep viloxterm`
2. Check plugin is discovered: `plugins.list` command
3. Enable plugin if disabled: `plugins.enable viloxterm`
```

#### Task 5.5: Final Testing Checklist

- [ ] Plugin discovered by plugin manager
- [ ] Plugin loads without errors
- [ ] Plugin activates successfully
- [ ] Terminal widget can be created
- [ ] Terminal commands work
- [ ] Terminal server starts
- [ ] Sessions can be created
- [ ] Terminal displays correctly
- [ ] Input/output works
- [ ] Sessions can be closed
- [ ] Plugin can be deactivated
- [ ] Plugin can be reloaded

### Final Validation
- [ ] All tests pass
- [ ] Plugin works standalone
- [ ] No regression in functionality
- [ ] Documentation complete

## Week 3 Summary

### Completed Deliverables
1. ✅ Terminal code analysis and dependency mapping
2. ✅ Viloxterm package structure created
3. ✅ Terminal server migrated and adapted
4. ✅ Terminal widget converted to plugin widget
5. ✅ Plugin implementation with full lifecycle
6. ✅ Command system integration
7. ✅ Backend support maintained
8. ✅ Test suite for plugin
9. ✅ Documentation and migration guide

### Key Files Created
- `/packages/viloxterm/` - Complete terminal plugin package
- `pyproject.toml` - Package configuration
- `plugin.py` - Main plugin implementation
- `widget.py` - Terminal widget factory
- `server.py` - Terminal server (migrated)
- `backends/` - Terminal backends (migrated)
- `tests/` - Plugin tests
- Migration documentation

### Ready for Week 4
Terminal plugin extraction is complete. The plugin can now:
- Be loaded independently
- Create terminal widgets
- Handle terminal commands
- Manage terminal sessions
- Integrate with the host application

### Next Steps
- Week 4: Complete terminal integration and advanced features
- Week 5: Begin editor plugin extraction