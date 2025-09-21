#!/usr/bin/env python3
"""
Conflict resolution for keyboard shortcuts.

This module handles detection and resolution of shortcut conflicts,
including priority-based resolution and user choice dialogs.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from viloapp.core.keyboard.parser import KeySequence
from viloapp.core.keyboard.shortcuts import Shortcut, ShortcutRegistry

logger = logging.getLogger(__name__)


class ConflictResolution(Enum):
    """Conflict resolution strategies."""

    PRIORITY = "priority"  # Use priority to resolve
    USER_CHOICE = "user"  # Let user choose
    REPLACE = "replace"  # Replace existing
    REJECT = "reject"  # Reject new shortcut
    COEXIST = "coexist"  # Allow both (different contexts)


@dataclass
class ConflictInfo:
    """Information about a shortcut conflict."""

    new_shortcut: Shortcut
    existing_shortcuts: list[Shortcut]
    conflict_type: str  # "exact", "prefix", "context_overlap"
    resolution: Optional[ConflictResolution] = None


class ConflictResolver:
    """Resolves keyboard shortcut conflicts."""

    def __init__(self):
        """Initialize the conflict resolver."""
        self._default_resolution = ConflictResolution.PRIORITY
        self._resolution_callbacks: dict[str, callable] = {}

    def find_conflicts(
        self, new_shortcut: Shortcut, registry: ShortcutRegistry
    ) -> list[ConflictInfo]:
        """
        Find conflicts for a new shortcut.

        Args:
            new_shortcut: Shortcut to check
            registry: Current shortcut registry

        Returns:
            List of conflict information
        """
        conflicts = []

        # Get existing shortcuts with same sequence
        existing = registry.get_shortcuts_for_sequence(new_shortcut.sequence)

        if not existing:
            return conflicts

        # Analyze conflicts
        for existing_shortcut in existing:
            conflict_type = self._analyze_conflict(new_shortcut, existing_shortcut)

            if conflict_type:
                conflict = ConflictInfo(
                    new_shortcut=new_shortcut,
                    existing_shortcuts=[existing_shortcut],
                    conflict_type=conflict_type,
                )
                conflicts.append(conflict)

        # Group related conflicts
        return self._group_conflicts(conflicts)

    def resolve_conflicts(
        self,
        new_shortcut: Shortcut,
        conflicts: list[ConflictInfo],
        registry: ShortcutRegistry,
    ) -> bool:
        """
        Resolve conflicts for a new shortcut.

        Args:
            new_shortcut: Shortcut to add
            conflicts: List of conflicts
            registry: Shortcut registry

        Returns:
            True if shortcut can be added
        """
        for conflict in conflicts:
            resolution = self._determine_resolution(conflict)

            if not self._apply_resolution(resolution, conflict, registry):
                return False

        return True

    def set_default_resolution(self, resolution: ConflictResolution) -> None:
        """Set the default conflict resolution strategy."""
        self._default_resolution = resolution

    def register_resolution_callback(
        self, conflict_type: str, callback: callable
    ) -> None:
        """Register a callback for resolving specific conflict types."""
        self._resolution_callbacks[conflict_type] = callback

    def _analyze_conflict(
        self, new_shortcut: Shortcut, existing_shortcut: Shortcut
    ) -> Optional[str]:
        """
        Analyze the type of conflict between two shortcuts.

        Returns:
            Conflict type or None if no conflict
        """
        # Same sequence
        if new_shortcut.sequence == existing_shortcut.sequence:
            # Check context overlap
            if self._contexts_overlap(new_shortcut.when, existing_shortcut.when):
                return "exact"
            else:
                return None  # Different contexts, no conflict

        # Check for prefix conflicts (chord sequences)
        if len(new_shortcut.sequence.chords) != len(existing_shortcut.sequence.chords):
            if self._is_prefix(new_shortcut.sequence, existing_shortcut.sequence):
                return "prefix"

        return None

    def _contexts_overlap(self, when1: Optional[str], when2: Optional[str]) -> bool:
        """
        Check if two when clauses have overlapping contexts.

        Args:
            when1: First when clause
            when2: Second when clause

        Returns:
            True if contexts overlap
        """
        # If either is None (global), they overlap
        if when1 is None or when2 is None:
            return True

        # If they're identical, they overlap
        if when1 == when2:
            return True

        # For now, assume different when clauses don't overlap
        # This could be enhanced with proper when clause analysis
        return False

    def _is_prefix(self, seq1: KeySequence, seq2: KeySequence) -> bool:
        """
        Check if one sequence is a prefix of another.

        Args:
            seq1: First sequence
            seq2: Second sequence

        Returns:
            True if one is a prefix of the other
        """
        chords1 = seq1.chords
        chords2 = seq2.chords

        min_len = min(len(chords1), len(chords2))

        # Check if the shorter sequence is a prefix of the longer
        return chords1[:min_len] == chords2[:min_len]

    def _group_conflicts(self, conflicts: list[ConflictInfo]) -> list[ConflictInfo]:
        """
        Group related conflicts together.

        Args:
            conflicts: List of individual conflicts

        Returns:
            List of grouped conflicts
        """
        # For now, return as-is
        # Could be enhanced to group by sequence/type
        return conflicts

    def _determine_resolution(self, conflict: ConflictInfo) -> ConflictResolution:
        """
        Determine how to resolve a conflict.

        Args:
            conflict: Conflict information

        Returns:
            Resolution strategy
        """
        # Check for registered callback
        if conflict.conflict_type in self._resolution_callbacks:
            try:
                callback = self._resolution_callbacks[conflict.conflict_type]
                return callback(conflict)
            except Exception as e:
                logger.error(f"Error in conflict resolution callback: {e}")

        # Use default resolution based on conflict type
        if conflict.conflict_type == "exact":
            return self._resolve_exact_conflict(conflict)
        elif conflict.conflict_type == "prefix":
            return self._resolve_prefix_conflict(conflict)
        else:
            return self._default_resolution

    def _resolve_exact_conflict(self, conflict: ConflictInfo) -> ConflictResolution:
        """Resolve an exact sequence conflict."""
        new_shortcut = conflict.new_shortcut
        existing_shortcuts = conflict.existing_shortcuts

        # Compare priorities
        if existing_shortcuts:
            existing = existing_shortcuts[0]  # Take first for comparison

            # Higher priority (lower number) wins
            if new_shortcut.priority < existing.priority:
                return ConflictResolution.REPLACE
            elif new_shortcut.priority > existing.priority:
                return ConflictResolution.REJECT
            else:
                # Same priority, check source
                return self._resolve_by_source(new_shortcut, existing)

        return self._default_resolution

    def _resolve_prefix_conflict(self, conflict: ConflictInfo) -> ConflictResolution:
        """Resolve a prefix conflict."""
        # Prefix conflicts are generally not allowed as they create ambiguity
        # The shorter sequence would always trigger before the longer one
        logger.warning(f"Prefix conflict detected: {conflict}")
        return ConflictResolution.REJECT

    def _resolve_by_source(
        self, new_shortcut: Shortcut, existing_shortcut: Shortcut
    ) -> ConflictResolution:
        """Resolve conflict based on shortcut source."""
        # Source priority: builtin < user < extension
        source_priority = {"builtin": 0, "user": 1, "extension": 2}

        new_priority = source_priority.get(new_shortcut.source, 1)
        existing_priority = source_priority.get(existing_shortcut.source, 1)

        if new_priority > existing_priority:
            return ConflictResolution.REPLACE
        elif new_priority < existing_priority:
            return ConflictResolution.REJECT
        else:
            # Same source priority
            return ConflictResolution.USER_CHOICE

    def _apply_resolution(
        self,
        resolution: ConflictResolution,
        conflict: ConflictInfo,
        registry: ShortcutRegistry,
    ) -> bool:
        """
        Apply a conflict resolution.

        Args:
            resolution: Resolution to apply
            conflict: Conflict information
            registry: Shortcut registry

        Returns:
            True if shortcut can be added
        """
        if resolution == ConflictResolution.PRIORITY:
            # Let priority system handle it naturally
            return True

        elif resolution == ConflictResolution.REPLACE:
            # Remove existing shortcuts
            for existing in conflict.existing_shortcuts:
                registry.unregister(existing.id)
                logger.info(
                    f"Replaced shortcut {existing.id} with {conflict.new_shortcut.id}"
                )
            return True

        elif resolution == ConflictResolution.REJECT:
            # Don't add the new shortcut
            logger.info(f"Rejected shortcut {conflict.new_shortcut.id} due to conflict")
            return False

        elif resolution == ConflictResolution.COEXIST:
            # Allow both (they have different contexts)
            return True

        elif resolution == ConflictResolution.USER_CHOICE:
            # For now, default to priority-based resolution
            # In a real implementation, this would show a dialog
            logger.warning(f"User choice needed for conflict: {conflict}")
            return self._apply_resolution(
                ConflictResolution.PRIORITY, conflict, registry
            )

        return False
