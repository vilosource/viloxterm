#!/usr/bin/env python3
"""
Factory for creating platform-specific terminal backends.
"""

import logging
import sys
from typing import Optional

from .base import TerminalBackend

logger = logging.getLogger(__name__)


class TerminalBackendFactory:
    """
    Factory class for creating the appropriate terminal backend
    based on the current platform.
    """

    _backend_instance: Optional[TerminalBackend] = None

    @staticmethod
    def create_backend() -> TerminalBackend:
        """
        Create and return the appropriate terminal backend for the current platform.

        Returns:
            TerminalBackend: Platform-specific terminal backend instance

        Raises:
            RuntimeError: If the platform is not supported
        """
        # Use singleton pattern - create only one backend instance
        if TerminalBackendFactory._backend_instance is not None:
            return TerminalBackendFactory._backend_instance

        if sys.platform == "win32":
            logger.info("Creating Windows terminal backend")
            try:
                from .windows_backend import WindowsTerminalBackend

                TerminalBackendFactory._backend_instance = WindowsTerminalBackend()
            except ImportError as e:
                logger.error(f"Failed to import Windows backend: {e}")
                raise RuntimeError(
                    "Windows terminal backend requires pywinpty. "
                    "Please install it with: pip install pywinpty"
                )
        else:
            # Unix-like systems (Linux, macOS, BSD, etc.)
            logger.info(f"Creating Unix terminal backend for platform: {sys.platform}")
            from .unix_backend import UnixTerminalBackend

            TerminalBackendFactory._backend_instance = UnixTerminalBackend()

        logger.info(
            f"Terminal backend created: {TerminalBackendFactory._backend_instance.get_platform_name()}"
        )
        return TerminalBackendFactory._backend_instance

    @staticmethod
    def get_backend() -> Optional[TerminalBackend]:
        """
        Get the current backend instance if one has been created.

        Returns:
            Optional[TerminalBackend]: The backend instance or None
        """
        return TerminalBackendFactory._backend_instance

    @staticmethod
    def reset():
        """Reset the factory, clearing the cached backend instance."""
        if TerminalBackendFactory._backend_instance:
            logger.info("Resetting terminal backend factory")
            # Clean up any active sessions
            for session in list(TerminalBackendFactory._backend_instance.sessions.values()):
                TerminalBackendFactory._backend_instance.cleanup(session)
            TerminalBackendFactory._backend_instance = None

    @staticmethod
    def is_platform_supported() -> bool:
        """
        Check if the current platform is supported.

        Returns:
            bool: True if the platform is supported
        """
        if sys.platform == "win32":
            try:
                import winpty

                return True
            except ImportError:
                return False
        else:
            # Unix-like systems are always supported
            return True

    @staticmethod
    def get_platform_info() -> dict:
        """
        Get information about terminal support on the current platform.

        Returns:
            dict: Platform information including support status and features
        """
        info = {
            "platform": sys.platform,
            "supported": TerminalBackendFactory.is_platform_supported(),
            "backend_type": None,
            "features": [],
            "requirements": [],
        }

        if sys.platform == "win32":
            info["backend_type"] = "Windows (ConPTY)"
            info["features"] = ["conpty", "powershell", "cmd", "resize", "colors"]
            try:
                import winpty

                info["requirements"].append(f"pywinpty {winpty.__version__}")
            except ImportError:
                info["requirements"].append("pywinpty (not installed)")
        else:
            info["backend_type"] = "Unix (PTY)"
            info["features"] = ["pty", "signals", "job_control", "resize", "colors"]
            info["requirements"].append("Built-in Unix PTY support")

        return info
