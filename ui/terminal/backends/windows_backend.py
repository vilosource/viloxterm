#!/usr/bin/env python3
"""
Windows terminal backend implementation using pywinpty.
"""

import logging
import os
import signal
import threading
import time
from typing import Optional

from .base import TerminalBackend, TerminalSession

logger = logging.getLogger(__name__)

# Only import winpty on Windows
try:
    import winpty
    WINPTY_AVAILABLE = True
except ImportError:
    WINPTY_AVAILABLE = False
    logger.warning("pywinpty not available - Windows terminal support disabled")


class WindowsTerminalBackend(TerminalBackend):
    """
    Terminal backend for Windows systems using pywinpty.

    This implementation uses Windows ConPTY (Pseudo Console) API
    through the pywinpty library for terminal emulation.
    """

    def __init__(self):
        """Initialize the Windows terminal backend."""
        super().__init__()
        if not WINPTY_AVAILABLE:
            raise RuntimeError("pywinpty is required for Windows terminal support")
        self._read_threads = {}  # Store read threads for each session

    def start_process(self, session: TerminalSession) -> bool:
        """Start a terminal process using pywinpty."""
        try:
            # Prepare command
            if session.command.lower() in ["powershell", "powershell.exe"]:
                cmd = "powershell.exe"
            elif session.command.lower() in ["cmd", "cmd.exe"]:
                cmd = "cmd.exe"
            else:
                cmd = session.command

            # Build full command with arguments
            if session.cmd_args:
                full_cmd = f'"{cmd}" {" ".join(session.cmd_args)}'
            else:
                full_cmd = cmd

            # Create PTY process
            proc = winpty.PtyProcess.spawn(
                full_cmd,
                cwd=session.cwd or os.getcwd(),
                dimensions=(session.rows, session.cols)
            )

            # Store process information
            session.platform_data["pty_process"] = proc
            session.child_pid = proc.pid
            session.fd = proc.fileno()  # For compatibility

            logger.info(
                f"Started Windows terminal process for session {session.session_id}, PID: {proc.pid}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to start Windows terminal process: {e}")
            return False

    def read_output(self, session: TerminalSession, max_bytes: int = 1024 * 20) -> Optional[str]:
        """Read output from the terminal process."""
        proc = session.platform_data.get("pty_process")
        if not proc:
            return None

        try:
            # Check if process is still alive
            if not proc.isalive():
                session.active = False
                return None

            # For pywinpty, we need to handle reading differently
            # The read() method in pywinpty can block, so we use a different approach
            # We'll read in smaller chunks and use exception handling
            output = ""
            chunk_size = 1024  # Read in smaller chunks

            # Try to read a chunk
            # Note: This will return immediately if no data is available
            chunk = proc.read(chunk_size)
            if chunk:
                output = chunk
                session.last_activity = time.time()

                # Try to read more if available (up to max_bytes)
                while len(output) < max_bytes:
                    try:
                        more_data = proc.read(min(chunk_size, max_bytes - len(output)))
                        if not more_data:
                            break
                        output += more_data
                    except:
                        # No more data available
                        break

                # Windows uses \r\n, but xterm.js expects \n
                return output.replace('\r\n', '\n')

            return None

        except EOFError:
            # Process ended
            logger.debug(f"Process ended for session {session.session_id}")
            session.active = False
            return None
        except TimeoutError:
            # No data available right now
            return None
        except Exception as e:
            # Log only if it's not a known "no data" situation
            error_msg = str(e).lower()
            if "timeout" not in error_msg and "would block" not in error_msg:
                logger.error(f"Read error for session {session.session_id}: {e}")
            return None

    def write_input(self, session: TerminalSession, data: str) -> bool:
        """Write input to the terminal process."""
        proc = session.platform_data.get("pty_process")
        if not proc:
            return False

        try:
            proc.write(data)
            session.last_activity = time.time()
            return True
        except Exception as e:
            logger.error(f"Write error for session {session.session_id}: {e}")
            return False

    def resize(self, session: TerminalSession, rows: int, cols: int) -> bool:
        """Resize the terminal window."""
        proc = session.platform_data.get("pty_process")
        if not proc:
            return False

        try:
            proc.setwinsize(rows, cols)
            session.rows = rows
            session.cols = cols
            return True
        except Exception as e:
            logger.error(f"Resize error for session {session.session_id}: {e}")
            return False

    def is_process_alive(self, session: TerminalSession) -> bool:
        """Check if the terminal process is still running."""
        proc = session.platform_data.get("pty_process")
        if not proc:
            return False

        try:
            return proc.isalive()
        except Exception:
            return False

    def terminate_process(self, session: TerminalSession) -> bool:
        """Terminate the terminal process."""
        proc = session.platform_data.get("pty_process")
        if not proc:
            return True

        try:
            # Try to terminate gracefully
            if proc.isalive():
                proc.terminate()
                time.sleep(0.1)

            # Force kill if still alive
            if proc.isalive():
                proc.kill()

            return True
        except Exception as e:
            logger.error(f"Failed to terminate process for session {session.session_id}: {e}")
            return False

    def cleanup(self, session: TerminalSession):
        """Clean up resources for a terminal session."""
        # Stop read thread if exists
        if session.session_id in self._read_threads:
            thread = self._read_threads.pop(session.session_id)
            if thread.is_alive():
                # Thread will stop when process dies
                pass

        # Terminate process
        proc = session.platform_data.get("pty_process")
        if proc:
            self.terminate_process(session)
            session.platform_data.pop("pty_process", None)

        session.child_pid = None
        session.fd = None
        session.active = False

    def poll_process(self, session: TerminalSession, timeout: float = 0.01) -> bool:
        """Poll the terminal process for available data."""
        proc = session.platform_data.get("pty_process")
        if not proc:
            return False

        try:
            # Windows doesn't have select() for PTY, so we check if process is alive
            # and assume data might be available
            return proc.isalive()
        except Exception:
            return False

    def supports_feature(self, feature: str) -> bool:
        """Check if this backend supports a specific feature."""
        windows_features = {
            "resize", "colors", "unicode", "input", "output",
            "conpty", "powershell", "cmd"
        }
        return feature in windows_features

    def get_default_shell(self) -> str:
        """Get the default shell for Windows."""
        # Check if PowerShell is available
        powershell_path = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
        if os.path.exists(powershell_path):
            return "powershell.exe"
        return "cmd.exe"