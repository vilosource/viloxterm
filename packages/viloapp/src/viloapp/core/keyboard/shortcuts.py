#!/usr/bin/env python3
"""
Shortcut management and registry for the keyboard system.
"""

import logging
from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable, Optional

from viloapp.core.keyboard.parser import KeySequence, KeySequenceParser

logger = logging.getLogger(__name__)


@dataclass
class Shortcut:
    """Represents a keyboard shortcut binding."""

    # Identity
    id: str  # Unique shortcut identifier
    sequence: KeySequence  # Key sequence
    command_id: str  # Command to execute

    # Context
    when: Optional[str] = None  # When clause for conditional activation
    description: Optional[str] = None  # Human-readable description

    # Metadata
    source: str = "user"  # Source: "builtin", "user", "extension"
    priority: int = 100  # Priority for conflict resolution (lower = higher priority)
    enabled: bool = True  # Whether shortcut is active

    def __str__(self) -> str:
        """String representation."""
        return f"{self.sequence} -> {self.command_id}"

    def __hash__(self) -> int:
        """Make hashable for use in sets."""
        return hash((self.id, self.sequence, self.command_id))

    def matches_context(self, context: dict[str, Any]) -> bool:
        """Check if shortcut matches the current context."""
        if not self.enabled:
            return False

        if not self.when:
            return True

        # Import here to avoid circular dependency
        from viloapp.core.context.evaluator import WhenClauseEvaluator

        return WhenClauseEvaluator.evaluate(self.when, context)


class ShortcutRegistry:
    """Registry for managing keyboard shortcuts."""

    def __init__(self):
        """Initialize the registry."""
        self._shortcuts: dict[str, Shortcut] = {}  # id -> shortcut
        self._by_sequence: dict[KeySequence, list[Shortcut]] = (
            {}
        )  # sequence -> shortcuts
        self._by_command: dict[str, list[Shortcut]] = {}  # command_id -> shortcuts
        self._observers: list[Callable[[str, Shortcut], None]] = []
        self._lock = Lock()

    def register(self, shortcut: Shortcut) -> bool:
        """
        Register a shortcut.

        Args:
            shortcut: Shortcut to register

        Returns:
            True if registered successfully
        """
        with self._lock:
            # Check for ID conflicts
            if shortcut.id in self._shortcuts:
                logger.warning(f"Shortcut ID already exists: {shortcut.id}")
                return False

            # Store shortcut
            self._shortcuts[shortcut.id] = shortcut

            # Index by sequence
            if shortcut.sequence not in self._by_sequence:
                self._by_sequence[shortcut.sequence] = []
            self._by_sequence[shortcut.sequence].append(shortcut)

            # Index by command
            if shortcut.command_id not in self._by_command:
                self._by_command[shortcut.command_id] = []
            self._by_command[shortcut.command_id].append(shortcut)

            # Sort by priority (lower number = higher priority)
            self._by_sequence[shortcut.sequence].sort(key=lambda s: s.priority)

            # Notify observers
            self._notify_observers("registered", shortcut)

            logger.debug(f"Registered shortcut: {shortcut}")
            return True

    def unregister(self, shortcut_id: str) -> bool:
        """
        Unregister a shortcut by ID.

        Args:
            shortcut_id: ID of shortcut to remove

        Returns:
            True if unregistered successfully
        """
        with self._lock:
            if shortcut_id not in self._shortcuts:
                return False

            shortcut = self._shortcuts[shortcut_id]

            # Remove from indices
            del self._shortcuts[shortcut_id]

            if shortcut.sequence in self._by_sequence:
                self._by_sequence[shortcut.sequence].remove(shortcut)
                if not self._by_sequence[shortcut.sequence]:
                    del self._by_sequence[shortcut.sequence]

            if shortcut.command_id in self._by_command:
                self._by_command[shortcut.command_id].remove(shortcut)
                if not self._by_command[shortcut.command_id]:
                    del self._by_command[shortcut.command_id]

            # Notify observers
            self._notify_observers("unregistered", shortcut)

            logger.debug(f"Unregistered shortcut: {shortcut}")
            return True

    def get_shortcut(self, shortcut_id: str) -> Optional[Shortcut]:
        """Get a shortcut by ID."""
        return self._shortcuts.get(shortcut_id)

    def get_shortcuts_for_sequence(self, sequence: KeySequence) -> list[Shortcut]:
        """Get all shortcuts for a key sequence."""
        return self._by_sequence.get(sequence, []).copy()

    def get_shortcuts_for_command(self, command_id: str) -> list[Shortcut]:
        """Get all shortcuts for a command."""
        return self._by_command.get(command_id, []).copy()

    def find_matching_shortcuts(
        self, sequence: KeySequence, context: dict[str, Any]
    ) -> list[Shortcut]:
        """
        Find shortcuts that match the sequence and context.

        Args:
            sequence: Key sequence to match
            context: Current context for when clause evaluation

        Returns:
            List of matching shortcuts, ordered by priority
        """
        shortcuts = self.get_shortcuts_for_sequence(sequence)

        # Filter by context and enabled status
        matching = []
        for shortcut in shortcuts:
            if shortcut.matches_context(context):
                matching.append(shortcut)

        return matching

    def get_all_shortcuts(self) -> list[Shortcut]:
        """Get all registered shortcuts."""
        return list(self._shortcuts.values())

    def get_conflicts(self) -> dict[KeySequence, list[Shortcut]]:
        """
        Get all shortcut conflicts.

        Returns:
            Dictionary mapping sequences to conflicting shortcuts
        """
        conflicts = {}
        for sequence, shortcuts in self._by_sequence.items():
            if len(shortcuts) > 1:
                # Check if they actually conflict (same context)
                context_groups = {}
                for shortcut in shortcuts:
                    key = shortcut.when or "global"
                    if key not in context_groups:
                        context_groups[key] = []
                    context_groups[key].append(shortcut)

                # Only consider it a conflict if multiple shortcuts have overlapping contexts
                conflicting = []
                for group in context_groups.values():
                    if len(group) > 1:
                        conflicting.extend(group)

                if conflicting:
                    conflicts[sequence] = conflicting

        return conflicts

    def register_from_string(
        self,
        shortcut_id: str,
        sequence_str: str,
        command_id: str,
        when: Optional[str] = None,
        description: Optional[str] = None,
        source: str = "user",
        priority: int = 100,
    ) -> bool:
        """
        Register a shortcut from string representation.

        Args:
            shortcut_id: Unique identifier
            sequence_str: Key sequence string (e.g., "ctrl+n")
            command_id: Command to execute
            when: Optional when clause
            description: Optional description
            source: Source of the shortcut
            priority: Priority for conflict resolution

        Returns:
            True if registered successfully
        """
        # Parse sequence
        sequence = KeySequenceParser.parse(sequence_str)
        if sequence is None:
            logger.error(f"Failed to parse shortcut sequence: {sequence_str}")
            return False

        # Create shortcut
        shortcut = Shortcut(
            id=shortcut_id,
            sequence=sequence,
            command_id=command_id,
            when=when,
            description=description,
            source=source,
            priority=priority,
        )

        return self.register(shortcut)

    def update_shortcut(self, shortcut_id: str, **updates) -> bool:
        """
        Update an existing shortcut.

        Args:
            shortcut_id: ID of shortcut to update
            **updates: Fields to update

        Returns:
            True if updated successfully
        """
        with self._lock:
            if shortcut_id not in self._shortcuts:
                return False

            old_shortcut = self._shortcuts[shortcut_id]

            # Create updated shortcut
            new_data = {
                "id": old_shortcut.id,
                "sequence": old_shortcut.sequence,
                "command_id": old_shortcut.command_id,
                "when": old_shortcut.when,
                "description": old_shortcut.description,
                "source": old_shortcut.source,
                "priority": old_shortcut.priority,
                "enabled": old_shortcut.enabled,
            }
            new_data.update(updates)

            # Handle sequence string update
            if "sequence_str" in updates:
                sequence = KeySequenceParser.parse(updates["sequence_str"])
                if sequence is None:
                    logger.error(
                        f"Invalid sequence in update: {updates['sequence_str']}"
                    )
                    return False
                new_data["sequence"] = sequence
                del new_data["sequence_str"]

            new_shortcut = Shortcut(**new_data)

            # Unregister old and register new
            self.unregister(shortcut_id)
            return self.register(new_shortcut)

    def enable_shortcut(self, shortcut_id: str) -> bool:
        """Enable a shortcut."""
        return self.update_shortcut(shortcut_id, enabled=True)

    def disable_shortcut(self, shortcut_id: str) -> bool:
        """Disable a shortcut."""
        return self.update_shortcut(shortcut_id, enabled=False)

    def clear(self, source: Optional[str] = None) -> None:
        """
        Clear shortcuts.

        Args:
            source: If specified, only clear shortcuts from this source
        """
        with self._lock:
            if source is None:
                # Clear all
                self._shortcuts.clear()
                self._by_sequence.clear()
                self._by_command.clear()
            else:
                # Clear by source
                to_remove = [
                    s.id for s in self._shortcuts.values() if s.source == source
                ]
                for shortcut_id in to_remove:
                    self.unregister(shortcut_id)

    def add_observer(self, observer: Callable[[str, Shortcut], None]) -> None:
        """Add an observer for shortcut events."""
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: Callable[[str, Shortcut], None]) -> None:
        """Remove an observer."""
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify_observers(self, event: str, shortcut: Shortcut) -> None:
        """Notify observers of events."""
        for observer in self._observers:
            try:
                observer(event, shortcut)
            except Exception as e:
                logger.error(f"Error in shortcut observer: {e}")

    def export_shortcuts(self, source: Optional[str] = None) -> list[dict[str, Any]]:
        """
        Export shortcuts to a serializable format.

        Args:
            source: If specified, only export shortcuts from this source

        Returns:
            List of shortcut dictionaries
        """
        shortcuts = self.get_all_shortcuts()
        if source:
            shortcuts = [s for s in shortcuts if s.source == source]

        return [
            {
                "id": s.id,
                "sequence": str(s.sequence),
                "command_id": s.command_id,
                "when": s.when,
                "description": s.description,
                "source": s.source,
                "priority": s.priority,
                "enabled": s.enabled,
            }
            for s in shortcuts
        ]

    def import_shortcuts(
        self, shortcuts_data: list[dict[str, Any]], source: str = "import"
    ) -> int:
        """
        Import shortcuts from serialized data.

        Args:
            shortcuts_data: List of shortcut dictionaries
            source: Source to assign to imported shortcuts

        Returns:
            Number of shortcuts successfully imported
        """
        imported = 0
        for data in shortcuts_data:
            try:
                success = self.register_from_string(
                    shortcut_id=data["id"],
                    sequence_str=data["sequence"],
                    command_id=data["command_id"],
                    when=data.get("when"),
                    description=data.get("description"),
                    source=source,
                    priority=data.get("priority", 100),
                )
                if success:
                    imported += 1
                    # Set enabled state if specified
                    if not data.get("enabled", True):
                        self.disable_shortcut(data["id"])
            except Exception as e:
                logger.error(f"Failed to import shortcut {data}: {e}")

        logger.info(f"Imported {imported}/{len(shortcuts_data)} shortcuts")
        return imported
