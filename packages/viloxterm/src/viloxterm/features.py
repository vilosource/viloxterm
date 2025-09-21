"""Advanced terminal features."""

import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TerminalProfile:
    """Terminal profile configuration."""

    name: str
    shell: str
    args: List[str] = None
    env: Dict[str, str] = None
    cwd: str = None
    icon: str = "terminal"
    color: str = None


class TerminalProfileManager:
    """Manages terminal profiles."""

    def __init__(self):
        self.profiles: Dict[str, TerminalProfile] = {}
        self._load_default_profiles()

    def _load_default_profiles(self):
        """Load default terminal profiles."""
        import platform

        if platform.system() == "Windows":
            self.profiles["powershell"] = TerminalProfile(
                name="PowerShell", shell="powershell.exe", icon="terminal-powershell"
            )
            self.profiles["cmd"] = TerminalProfile(
                name="Command Prompt", shell="cmd.exe", icon="terminal-cmd"
            )
            # Check for WSL
            try:
                import subprocess

                result = subprocess.run(["wsl", "--list"], capture_output=True)
                if result.returncode == 0:
                    self.profiles["wsl"] = TerminalProfile(
                        name="WSL", shell="wsl.exe", icon="terminal-linux"
                    )
            except:
                pass

        else:  # Unix-like systems
            self.profiles["bash"] = TerminalProfile(
                name="Bash", shell="/bin/bash", icon="terminal-bash"
            )
            self.profiles["zsh"] = TerminalProfile(
                name="Zsh", shell="/bin/zsh", icon="terminal-zsh"
            )
            self.profiles["sh"] = TerminalProfile(name="Shell", shell="/bin/sh", icon="terminal")

            # Check for additional shells
            import os

            if os.path.exists("/usr/bin/fish"):
                self.profiles["fish"] = TerminalProfile(
                    name="Fish", shell="/usr/bin/fish", icon="terminal-fish"
                )

    def add_profile(self, profile_id: str, profile: TerminalProfile):
        """Add a custom profile."""
        self.profiles[profile_id] = profile

    def get_profile(self, profile_id: str) -> Optional[TerminalProfile]:
        """Get a profile by ID."""
        return self.profiles.get(profile_id)

    def list_profiles(self) -> List[TerminalProfile]:
        """List all available profiles."""
        return list(self.profiles.values())

    def get_default_profile(self) -> TerminalProfile:
        """Get the default profile for the current platform."""
        import platform

        if platform.system() == "Windows":
            return self.profiles.get("powershell", TerminalProfile("Default", "powershell.exe"))
        else:
            return self.profiles.get("bash", TerminalProfile("Default", "/bin/bash"))


class TerminalSessionManager:
    """Enhanced session management."""

    def __init__(self, server_manager):
        self.server = server_manager
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, profile: TerminalProfile = None, name: str = None) -> str:
        """Create a new session with profile."""
        if profile is None:
            manager = TerminalProfileManager()
            profile = manager.get_default_profile()

        session_id = self.server.create_session(
            command=profile.shell,
            cmd_args=" ".join(profile.args) if profile.args else "",
            cwd=profile.cwd,
        )

        self.sessions[session_id] = {
            "name": name or f"Terminal {len(self.sessions) + 1}",
            "profile": profile,
            "created_at": time.time(),
        }

        return session_id

    def rename_session(self, session_id: str, name: str):
        """Rename a session."""
        if session_id in self.sessions:
            self.sessions[session_id]["name"] = name

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        return self.sessions.get(session_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions with info."""
        result = []
        for session_id, info in self.sessions.items():
            result.append(
                {
                    "id": session_id,
                    "name": info["name"],
                    "profile": info["profile"].name,
                    "created_at": info["created_at"],
                }
            )
        return result


class TerminalSearch:
    """Terminal search functionality."""

    def __init__(self):
        self.search_history: List[str] = []

    def search_in_terminal(self, terminal_widget, pattern: str, case_sensitive: bool = False):
        """Search for pattern in terminal output."""
        if not terminal_widget or not terminal_widget.web_view:
            return

        # JavaScript for searching in xterm.js
        js_code = f"""
        (function() {{
            const searchAddon = term.searchAddon;
            if (searchAddon) {{
                searchAddon.findNext('{pattern}', {{
                    caseSensitive: {str(case_sensitive).lower()},
                    wholeWord: false,
                    regex: false
                }});
            }}
        }})();
        """

        terminal_widget.web_view.page().runJavaScript(js_code)

        # Add to history
        if pattern and pattern not in self.search_history:
            self.search_history.append(pattern)

    def find_next(self, terminal_widget):
        """Find next occurrence."""
        if terminal_widget and terminal_widget.web_view:
            terminal_widget.web_view.page().runJavaScript(
                "if (term.searchAddon) term.searchAddon.findNext();"
            )

    def find_previous(self, terminal_widget):
        """Find previous occurrence."""
        if terminal_widget and terminal_widget.web_view:
            terminal_widget.web_view.page().runJavaScript(
                "if (term.searchAddon) term.searchAddon.findPrevious();"
            )
