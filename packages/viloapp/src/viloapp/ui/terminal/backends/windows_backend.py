#!/usr/bin/env python3
"""
Windows terminal backend implementation using pywinpty.
"""

import logging
import os
import queue
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
        self._output_queues = {}  # Store output queues for each session

    def start_process(self, session: TerminalSession) -> bool:
        """Start a terminal process using pywinpty."""
        try:
            # Prepare command
            if session.command.lower() in ["powershell", "powershell.exe"]:
                # Use PowerShell with specific settings for better terminal compatibility
                cmd = "powershell.exe"
                # Add arguments for better terminal behavior
                if not session.cmd_args:
                    session.cmd_args = [
                        "-NoLogo",  # Don't show PowerShell logo
                        "-ExecutionPolicy",
                        "Bypass",  # Allow scripts
                    ]
            elif session.command.lower() in ["cmd", "cmd.exe"]:
                cmd = "cmd.exe"
            else:
                cmd = session.command

            # Build command as a list for pywinpty
            if session.cmd_args:
                # Pass as list when there are arguments
                spawn_cmd = [cmd] + session.cmd_args
            else:
                # Pass as simple string when no arguments
                spawn_cmd = cmd

            logger.debug(f"Windows backend: Starting {spawn_cmd} in {session.cwd or os.getcwd()}")

            # Create PTY process with proper environment
            env = os.environ.copy()

            # Enable ANSI color support in Windows console
            env["TERM"] = "xterm-256color"

            # For PowerShell, enable proper terminal behavior
            if "powershell" in cmd.lower():
                # Disable progress bars that mess up terminal output
                env["PSStyle.Progress.View"] = "Minimal"
                # Set output encoding to UTF-8
                env["OutputEncoding"] = "utf-8"

            proc = winpty.PtyProcess.spawn(
                spawn_cmd,
                cwd=session.cwd or os.getcwd(),
                dimensions=(session.rows, session.cols),
                env=env,
            )

            # Store process information
            session.platform_data["pty_process"] = proc
            session.child_pid = proc.pid
            session.fd = proc.fileno()  # For compatibility

            logger.info(
                f"Started Windows terminal process for session {session.session_id}, PID: {proc.pid}"
            )

            # Create output queue for this session
            output_queue = queue.Queue()
            self._output_queues[session.session_id] = output_queue

            # Start reader thread for this session
            reader_thread = threading.Thread(
                target=self._reader_thread,
                args=(session.session_id, proc, output_queue),
                daemon=True,
            )
            reader_thread.start()
            self._read_threads[session.session_id] = reader_thread

            logger.debug("Windows backend: Started reader thread for non-blocking I/O")

            return True

        except Exception as e:
            logger.error(f"Failed to start Windows terminal process: {e}", exc_info=True)
            return False

    def _reader_thread(self, session_id: str, proc, output_queue: queue.Queue):
        """Background thread to read from the PTY process."""
        while proc.isalive():
            try:
                # This will block until data is available
                chunk = proc.read(1024)
                if chunk:
                    output_queue.put(chunk)
                else:
                    # Empty read might mean process is ending
                    time.sleep(0.01)
            except Exception as e:
                if proc.isalive():
                    logger.error(f"Windows backend: Reader thread error: {e}")
                break

    def read_output(self, session: TerminalSession, max_bytes: int = 1024 * 20) -> Optional[str]:
        """Read output from the terminal process."""
        proc = session.platform_data.get("pty_process")
        if not proc:
            logger.debug(f"Windows backend: No process for session {session.session_id}")
            return None

        # Get the output queue for this session
        output_queue = self._output_queues.get(session.session_id)
        if not output_queue:
            logger.debug(f"Windows backend: No output queue for session {session.session_id}")
            return None

        try:
            # Check if process is still alive
            if not proc.isalive():
                logger.debug(f"Windows backend: Process dead for session {session.session_id}")
                session.active = False
                return None

            # Collect all available output from the queue (non-blocking)
            output = ""
            try:
                while len(output) < max_bytes:
                    # Get data from queue with no wait
                    chunk = output_queue.get_nowait()
                    output += chunk
            except queue.Empty:
                # No more data in queue
                pass

            if output:
                session.last_activity = time.time()
                # Process Windows output for xterm.js
                # Don't convert \r\n to \n - let xterm.js handle it naturally
                # This preserves cursor positioning
                return output
            else:
                # No data available
                return None

        except Exception as e:
            logger.error(
                f"Windows backend: Read error for session {session.session_id}: {e}", exc_info=True
            )
            return None

    def write_input(self, session: TerminalSession, data: str) -> bool:
        """Write input to the terminal process."""
        proc = session.platform_data.get("pty_process")
        if not proc:
            logger.debug(f"Windows backend: No process for write to session {session.session_id}")
            return False

        try:
            proc.write(data)
            session.last_activity = time.time()

            # Don't try to read response here - let the reader thread handle it
            return True
        except Exception as e:
            logger.error(
                f"Windows backend: Write error for session {session.session_id}: {e}", exc_info=True
            )
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
            # Thread will stop when process dies

        # Clean up output queue
        if session.session_id in self._output_queues:
            self._output_queues.pop(session.session_id)

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

        # Get the output queue for this session
        output_queue = self._output_queues.get(session.session_id)
        if not output_queue:
            return False

        try:
            # Check if there's data in the queue or if process is alive
            has_data = not output_queue.empty()
            is_alive = proc.isalive()

            # Return True if there's data to read or False if process is dead
            if has_data:
                return True
            elif is_alive:
                # Process is alive but no data yet - wait a bit
                time.sleep(timeout)
                return False
            else:
                # Process is dead
                return False
        except Exception:
            return False

    def supports_feature(self, feature: str) -> bool:
        """Check if this backend supports a specific feature."""
        windows_features = {
            "resize",
            "colors",
            "unicode",
            "input",
            "output",
            "conpty",
            "powershell",
            "cmd",
        }
        return feature in windows_features

    def get_default_shell(self) -> str:
        """Get the default shell for Windows."""
        # Check if PowerShell is available
        powershell_path = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
        if os.path.exists(powershell_path):
            return "powershell.exe"
        return "cmd.exe"
