#!/usr/bin/env python3
"""
Abstract base class for terminal backends.
Provides a unified interface for different platform implementations.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TerminalSession:
    """Represents a single terminal session."""

    session_id: str
    fd: Optional[int] = None  # File descriptor (Unix) or handle (Windows)
    child_pid: Optional[int] = None  # Process ID
    command: str = "bash"
    cmd_args: list = field(default_factory=list)
    cwd: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    rows: int = 24
    cols: int = 80
    active: bool = True
    # Platform-specific data can be stored here
    platform_data: dict = field(default_factory=dict)


class TerminalBackend(ABC):
    """
    Abstract base class for terminal backend implementations.

    Provides a platform-agnostic interface for terminal operations.
    Subclasses implement platform-specific functionality.
    """

    def __init__(self):
        """Initialize the terminal backend."""
        self.sessions: dict[str, TerminalSession] = {}

    @abstractmethod
    def start_process(self, session: TerminalSession) -> bool:
        """
        Start a terminal process for the given session.

        Args:
            session: The terminal session to start

        Returns:
            True if the process started successfully, False otherwise
        """
        pass

    @abstractmethod
    def read_output(self, session: TerminalSession, max_bytes: int = 1024 * 20) -> Optional[str]:
        """
        Read output from the terminal process.

        Args:
            session: The terminal session to read from
            max_bytes: Maximum number of bytes to read

        Returns:
            The output string if available, None otherwise
        """
        pass

    @abstractmethod
    def write_input(self, session: TerminalSession, data: str) -> bool:
        """
        Write input to the terminal process.

        Args:
            session: The terminal session to write to
            data: The input data to write

        Returns:
            True if the write was successful, False otherwise
        """
        pass

    @abstractmethod
    def resize(self, session: TerminalSession, rows: int, cols: int) -> bool:
        """
        Resize the terminal window.

        Args:
            session: The terminal session to resize
            rows: Number of rows
            cols: Number of columns

        Returns:
            True if the resize was successful, False otherwise
        """
        pass

    @abstractmethod
    def is_process_alive(self, session: TerminalSession) -> bool:
        """
        Check if the terminal process is still running.

        Args:
            session: The terminal session to check

        Returns:
            True if the process is alive, False otherwise
        """
        pass

    @abstractmethod
    def terminate_process(self, session: TerminalSession) -> bool:
        """
        Terminate the terminal process.

        Args:
            session: The terminal session to terminate

        Returns:
            True if the termination was successful, False otherwise
        """
        pass

    @abstractmethod
    def cleanup(self, session: TerminalSession):
        """
        Clean up resources for a terminal session.

        Args:
            session: The terminal session to clean up
        """
        pass

    @abstractmethod
    def poll_process(self, session: TerminalSession, timeout: float = 0.01) -> bool:
        """
        Poll the terminal process for available data.

        Args:
            session: The terminal session to poll
            timeout: Timeout in seconds

        Returns:
            True if data is available, False otherwise
        """
        pass

    def get_platform_name(self) -> str:
        """
        Get the name of the platform this backend supports.

        Returns:
            Platform name (e.g., "Unix", "Windows")
        """
        return self.__class__.__name__.replace("TerminalBackend", "")

    def supports_feature(self, feature: str) -> bool:
        """
        Check if this backend supports a specific feature.

        Args:
            feature: Feature name (e.g., "resize", "colors", "unicode")

        Returns:
            True if the feature is supported
        """
        # Base implementation - subclasses can override
        base_features = {"resize", "colors", "unicode", "input", "output"}
        return feature in base_features
