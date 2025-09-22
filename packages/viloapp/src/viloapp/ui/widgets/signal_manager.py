#!/usr/bin/env python3
"""
Signal connection lifecycle management.

Provides automatic tracking and cleanup of Qt signal connections
to prevent memory leaks and ensure proper resource management.
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

from PySide6.QtCore import QObject, Qt

logger = logging.getLogger(__name__)


@dataclass
class SignalConnection:
    """Represents a tracked signal connection."""

    signal: Any  # Qt signal object
    slot: Any  # Slot (callable) connected to signal
    connection_type: Qt.ConnectionType
    description: Optional[str] = None
    group: Optional[str] = None  # Connection group for bulk operations


class SignalManager:
    """
    Manages signal connections with automatic cleanup.

    This class tracks all signal connections made through it
    and provides safe cleanup to prevent memory leaks.
    """

    def __init__(self, owner: QObject):
        """
        Initialize the signal manager.

        Args:
            owner: The QObject that owns these connections
        """
        self.owner = owner
        self.connections: list[SignalConnection] = []
        self._enabled = True

    def connect(
        self,
        signal: Any,
        slot: Any,
        connection_type: Qt.ConnectionType = Qt.AutoConnection,
        description: Optional[str] = None,
        group: Optional[str] = None,
    ) -> SignalConnection:
        """
        Connect a signal with tracking.

        Args:
            signal: Qt signal to connect
            slot: Callable to connect to signal
            connection_type: Type of Qt connection
            description: Optional description for debugging
            group: Optional group name for bulk operations

        Returns:
            SignalConnection object representing the connection
        """
        if not self._enabled:
            logger.warning(f"SignalManager disabled for {self.owner}")
            return None

        try:
            # Make the connection
            signal.connect(slot, connection_type)

            # Track it
            connection = SignalConnection(
                signal=signal,
                slot=slot,
                connection_type=connection_type,
                description=description,
                group=group,
            )
            self.connections.append(connection)

            logger.debug(
                f"Connected signal for {self.owner}: {description or 'unnamed'}"
                + (f" (group: {group})" if group else "")
            )
            return connection

        except Exception as e:
            logger.error(f"Failed to connect signal for {self.owner}: {e}")
            return None

    def disconnect(self, connection: SignalConnection) -> bool:
        """
        Disconnect a specific connection.

        Args:
            connection: SignalConnection to disconnect

        Returns:
            True if disconnected successfully
        """
        if connection not in self.connections:
            return False

        try:
            connection.signal.disconnect(connection.slot)
            self.connections.remove(connection)
            logger.debug(
                f"Disconnected signal for {self.owner}: {connection.description or 'unnamed'}"
            )
            return True

        except RuntimeError:
            # Already disconnected
            if connection in self.connections:
                self.connections.remove(connection)
            return True

        except Exception as e:
            logger.error(f"Error disconnecting signal for {self.owner}: {e}")
            return False

    def disconnect_all(self) -> int:
        """
        Safely disconnect all tracked connections.

        Returns:
            Number of connections disconnected
        """
        count = 0
        # Copy list to avoid modification during iteration
        connections_copy = self.connections.copy()

        for connection in connections_copy:
            if self.disconnect(connection):
                count += 1

        self.connections.clear()

        if count > 0:
            logger.info(f"Disconnected {count} signals for {self.owner}")

        return count

    def disable(self):
        """Disable manager and disconnect all signals."""
        self._enabled = False
        self.disconnect_all()

    def enable(self):
        """Re-enable the manager."""
        self._enabled = True

    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.connections)

    def has_connections(self) -> bool:
        """Check if there are any active connections."""
        return len(self.connections) > 0

    def disconnect_group(self, group: str) -> int:
        """
        Disconnect all connections in a group.

        Args:
            group: Group name to disconnect

        Returns:
            Number of connections disconnected
        """
        if not group:
            return 0

        count = 0
        # Get connections in the group
        group_connections = [c for c in self.connections if c.group == group]

        for connection in group_connections:
            if self.disconnect(connection):
                count += 1

        if count > 0:
            logger.info(f"Disconnected {count} signals in group '{group}' for {self.owner}")

        return count

    def get_group_connections(self, group: str) -> list[SignalConnection]:
        """
        Get all connections in a group.

        Args:
            group: Group name

        Returns:
            List of connections in the group
        """
        return [c for c in self.connections if c.group == group]

    def get_groups(self) -> list[str]:
        """
        Get all group names.

        Returns:
            List of unique group names
        """
        groups = set()
        for connection in self.connections:
            if connection.group:
                groups.add(connection.group)
        return list(groups)

    def enable_group(self, group: str) -> int:
        """
        Enable all connections in a group (reconnect them).

        Args:
            group: Group name to enable

        Returns:
            Number of connections enabled
        """
        count = 0
        group_connections = self.get_group_connections(group)

        for connection in group_connections:
            try:
                # Reconnect the signal
                connection.signal.connect(connection.slot, connection.connection_type)
                count += 1
            except RuntimeError:
                # Already connected
                pass
            except Exception as e:
                logger.error(f"Error enabling connection in group '{group}': {e}")

        if count > 0:
            logger.debug(f"Enabled {count} connections in group '{group}' for {self.owner}")

        return count

    def disable_group(self, group: str) -> int:
        """
        Disable all connections in a group (disconnect without removing).

        Args:
            group: Group name to disable

        Returns:
            Number of connections disabled
        """
        count = 0
        group_connections = self.get_group_connections(group)

        for connection in group_connections:
            try:
                connection.signal.disconnect(connection.slot)
                count += 1
            except RuntimeError:
                # Already disconnected
                pass
            except Exception as e:
                logger.error(f"Error disabling connection in group '{group}': {e}")

        if count > 0:
            logger.debug(f"Disabled {count} connections in group '{group}' for {self.owner}")

        return count

    def __del__(self):
        """Cleanup on deletion."""
        try:
            # Check if owner still exists before accessing it
            if hasattr(self, "owner") and self.owner is not None:
                # Try to access owner, but catch RuntimeError if C++ object is deleted
                try:
                    owner_repr = repr(self.owner)
                except RuntimeError:
                    # C++ object already deleted, just clean up silently
                    if hasattr(self, "_connections"):
                        self._connections.clear()
                    return

                if self.has_connections():
                    logger.warning(
                        f"SignalManager for {owner_repr} being deleted with "
                        f"{self.get_connection_count()} active connections"
                    )
                    self.disconnect_all()
        except Exception:
            # Any other error during cleanup, just ignore
            pass
