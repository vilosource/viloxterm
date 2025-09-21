#!/usr/bin/env python3
"""
Unix/Linux terminal backend implementation using pty.
"""

import fcntl
import logging
import os
import pty
import select
import signal
import struct
import termios
import time
from typing import Optional

from .base import TerminalBackend, TerminalSession

logger = logging.getLogger(__name__)


class UnixTerminalBackend(TerminalBackend):
    """
    Terminal backend for Unix/Linux systems using pty.

    This implementation uses the traditional Unix PTY (pseudo-terminal)
    system for terminal emulation.
    """

    def start_process(self, session: TerminalSession) -> bool:
        """Start a terminal process using pty.fork()."""
        try:
            # Fork PTY
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

                # Set initial window size
                self.resize(session, session.rows, session.cols)

                logger.info(
                    f"Started Unix terminal process for session {session.session_id}, PID: {child_pid}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to start Unix terminal process: {e}")
            return False

    def read_output(self, session: TerminalSession, max_bytes: int = 1024 * 20) -> Optional[str]:
        """Read output from the terminal process."""
        if not session.fd:
            return None

        try:
            # Check if data is available using select
            timeout_sec = 0.01
            data_ready, _, _ = select.select([session.fd], [], [], timeout_sec)

            if data_ready:
                output = os.read(session.fd, max_bytes).decode(errors="ignore")
                session.last_activity = time.time()
                return output
            return None

        except OSError as e:
            # Terminal process ended or error occurred
            logger.debug(f"Read error for session {session.session_id}: {e}")
            session.active = False
            return None

    def write_input(self, session: TerminalSession, data: str) -> bool:
        """Write input to the terminal process."""
        if not session.fd:
            return False

        try:
            os.write(session.fd, data.encode())
            session.last_activity = time.time()
            return True
        except OSError as e:
            logger.error(f"Write error for session {session.session_id}: {e}")
            return False

    def resize(self, session: TerminalSession, rows: int, cols: int) -> bool:
        """Resize the terminal window using ioctl."""
        if not session.fd:
            return False

        try:
            # Pack window size structure
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(session.fd, termios.TIOCSWINSZ, winsize)

            session.rows = rows
            session.cols = cols
            return True
        except OSError as e:
            logger.error(f"Resize error for session {session.session_id}: {e}")
            return False

    def is_process_alive(self, session: TerminalSession) -> bool:
        """Check if the terminal process is still running."""
        if not session.child_pid:
            return False

        try:
            # Check if process exists without killing it
            os.kill(session.child_pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            # Process exists but we don't have permission
            return True

    def terminate_process(self, session: TerminalSession) -> bool:
        """Terminate the terminal process."""
        if not session.child_pid:
            return True

        try:
            # Try graceful termination first
            os.kill(session.child_pid, signal.SIGTERM)
            time.sleep(0.1)

            # Check if still alive and force kill if needed
            if self.is_process_alive(session):
                os.kill(session.child_pid, signal.SIGKILL)

            return True
        except ProcessLookupError:
            # Already dead
            return True
        except Exception as e:
            logger.error(f"Failed to terminate process for session {session.session_id}: {e}")
            return False

    def cleanup(self, session: TerminalSession):
        """Clean up resources for a terminal session."""
        # Terminate process if still running
        if session.child_pid:
            self.terminate_process(session)
            session.child_pid = None

        # Close file descriptor
        if session.fd:
            try:
                os.close(session.fd)
            except OSError:
                pass
            session.fd = None

        session.active = False

    def poll_process(self, session: TerminalSession, timeout: float = 0.01) -> bool:
        """Poll the terminal process for available data."""
        if not session.fd:
            return False

        try:
            # Use select to check if data is available
            data_ready, _, _ = select.select([session.fd], [], [], timeout)
            return bool(data_ready)
        except OSError:
            return False

    def supports_feature(self, feature: str) -> bool:
        """Check if this backend supports a specific feature."""
        unix_features = {
            "resize",
            "colors",
            "unicode",
            "input",
            "output",
            "signals",
            "job_control",
            "pty",
            "termios",
        }
        return feature in unix_features
