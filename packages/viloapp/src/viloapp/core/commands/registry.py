#!/usr/bin/env python3
"""
FunctionCommand registry for managing all application commands.

The FunctionCommandRegistry is a singleton that maintains all registered commands,
handles command indexing, and provides search capabilities.
"""

import logging
from threading import Lock
from typing import Any, Callable, Optional

from viloapp.core.commands.base import FunctionCommand

logger = logging.getLogger(__name__)


class CommandRegistry:
    """
    Central registry for all application commands.

    This is a singleton that manages command registration, lookup,
    and categorization. All commands must be registered here to be
    available to the system.
    """

    _instance: Optional["CommandRegistry"] = None
    _lock = Lock()

    def __new__(cls) -> "CommandRegistry":
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the registry (only once)."""
        if self._initialized:
            return

        self._commands: dict[str, FunctionCommand] = {}
        self._categories: dict[str, list[FunctionCommand]] = {}
        self._shortcuts: dict[str, list[str]] = {}  # shortcut -> [command_ids]
        self._keywords_index: dict[str, set[str]] = {}  # keyword -> {command_ids}
        self._observers: list[Callable[[str, FunctionCommand], None]] = []
        self._initialized = True

        logger.info("CommandRegistry initialized")

    def register(self, command: FunctionCommand) -> None:
        """
        Register a command.

        Args:
            command: FunctionCommand to register

        Raises:
            ValueError: If a command with the same ID already exists
        """
        if command.id in self._commands:
            logger.warning(f"Overwriting existing command: {command.id}")

        # Store the command
        self._commands[command.id] = command

        # Index by category
        if command.category not in self._categories:
            self._categories[command.category] = []
        if command not in self._categories[command.category]:
            self._categories[command.category].append(command)

        # Index by shortcut
        if command.shortcut:
            shortcut = self._normalize_shortcut(command.shortcut)
            if shortcut not in self._shortcuts:
                self._shortcuts[shortcut] = []
            if command.id not in self._shortcuts[shortcut]:
                self._shortcuts[shortcut].append(command.id)

            # Warn about conflicts
            if len(self._shortcuts[shortcut]) > 1:
                logger.warning(f"Shortcut conflict for {shortcut}: {self._shortcuts[shortcut]}")

        # Index by keywords
        self._index_keywords(command)

        # Notify observers
        self._notify_observers("registered", command)

        logger.debug(f"Registered command: {command.id}")

    def unregister(self, command_id: str) -> bool:
        """
        Unregister a command.

        Args:
            command_id: ID of command to unregister

        Returns:
            True if command was unregistered, False if not found
        """
        if command_id not in self._commands:
            return False

        command = self._commands[command_id]

        # Remove from main registry
        del self._commands[command_id]

        # Remove from category index
        if command.category in self._categories:
            self._categories[command.category].remove(command)
            if not self._categories[command.category]:
                del self._categories[command.category]

        # Remove from shortcut index
        if command.shortcut:
            shortcut = self._normalize_shortcut(command.shortcut)
            if shortcut in self._shortcuts:
                self._shortcuts[shortcut].remove(command_id)
                if not self._shortcuts[shortcut]:
                    del self._shortcuts[shortcut]

        # Remove from keyword index
        self._unindex_keywords(command)

        # Notify observers
        self._notify_observers("unregistered", command)

        logger.debug(f"Unregistered command: {command_id}")
        return True

    def get_command(self, command_id: str) -> Optional[FunctionCommand]:
        """
        Get a command by ID.

        Args:
            command_id: FunctionCommand ID to look up

        Returns:
            FunctionCommand if found, None otherwise
        """
        return self._commands.get(command_id)

    def get_all_commands(self) -> list[FunctionCommand]:
        """
        Get all registered commands.

        Returns:
            List of all commands
        """
        return list(self._commands.values())

    def get_commands_for_category(self, category: str) -> list[FunctionCommand]:
        """
        Get all commands in a category.

        Args:
            category: Category name

        Returns:
            List of commands in the category
        """
        return self._categories.get(category, []).copy()

    def get_commands_by_category(self, category: str) -> list[FunctionCommand]:
        """
        DEPRECATED: Use get_commands_for_category instead.

        Alias for backward compatibility.
        """
        import warnings

        warnings.warn(
            "get_commands_by_category is deprecated, use get_commands_for_category",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.get_commands_for_category(category)

    def get_categories(self) -> list[str]:
        """
        Get all command categories.

        Returns:
            List of category names
        """
        return list(self._categories.keys())

    def get_commands_by_shortcut(self, shortcut: str) -> list[FunctionCommand]:
        """
        Get commands bound to a shortcut.

        Args:
            shortcut: Keyboard shortcut

        Returns:
            List of commands with this shortcut
        """
        shortcut = self._normalize_shortcut(shortcut)
        command_ids = self._shortcuts.get(shortcut, [])
        return [self._commands[cmd_id] for cmd_id in command_ids if cmd_id in self._commands]

    def search_commands(self, query: str, use_fuzzy: bool = True) -> list[FunctionCommand]:
        """
        Search for commands by title, description, or keywords.

        Args:
            query: Search query
            use_fuzzy: Whether to use fuzzy matching (default: True)

        Returns:
            List of matching commands sorted by relevance
        """
        if not query:
            return list(self._commands.values())

        query_lower = query.lower()
        results = []

        for command in self._commands.values():
            if use_fuzzy:
                score = self._fuzzy_score(query_lower, command)
            else:
                score = self._substring_score(query_lower, command)

            if score > 0:
                results.append((score, command))

        # Sort by score (descending) and then by title
        results.sort(key=lambda x: (-x[0], x[1].title))

        return [cmd for _, cmd in results]

    def _substring_score(self, query: str, command: FunctionCommand) -> float:
        """Calculate score using substring matching (original implementation)."""
        score = 0

        # Check title (highest priority)
        if query in command.title.lower():
            score += 10
            if command.title.lower().startswith(query):
                score += 5

        # Check category
        if query in command.category.lower():
            score += 5

        # Check description
        if command.description and query in command.description.lower():
            score += 3

        # Check keywords
        for keyword in command.keywords:
            if query in keyword.lower():
                score += 2
                if keyword.lower() == query:
                    score += 3

        # Check command ID
        if query in command.id.lower():
            score += 1

        return score

    def _fuzzy_score(self, query: str, command: FunctionCommand) -> float:
        """
        Calculate fuzzy matching score for a command.

        Uses a simple fuzzy matching algorithm that:
        - Rewards consecutive character matches
        - Rewards matches at word boundaries
        - Penalizes gaps between matches
        """
        best_score = 0

        # Fields to search with their weights
        search_fields = [
            (command.title, 10),  # Title has highest weight
            (command.category, 5),
            (command.description or "", 3),
            (command.id, 2),
        ]

        # Add keywords
        for keyword in command.keywords:
            search_fields.append((keyword, 2))

        for text, base_weight in search_fields:
            text_lower = text.lower()
            field_score = self._fuzzy_match(query, text_lower)

            if field_score > 0:
                # Apply weight and bonus for exact matches
                weighted_score = field_score * base_weight

                # Bonus for exact match
                if query == text_lower:
                    weighted_score *= 2
                # Bonus for prefix match
                elif text_lower.startswith(query):
                    weighted_score *= 1.5

                best_score = max(best_score, weighted_score)

        return best_score

    def _fuzzy_match(self, pattern: str, text: str) -> float:
        """
        Fuzzy match a pattern against text.

        Returns a score from 0 to 1 indicating match quality.
        """
        if not pattern or not text:
            return 0

        pattern_len = len(pattern)
        text_len = len(text)

        if pattern_len > text_len:
            return 0

        # Track the position of matches
        pattern_idx = 0
        text_idx = 0
        matches = []

        while pattern_idx < pattern_len and text_idx < text_len:
            if pattern[pattern_idx] == text[text_idx]:
                matches.append(text_idx)
                pattern_idx += 1
            text_idx += 1

        # All characters must match
        if pattern_idx != pattern_len:
            return 0

        # Calculate score based on match quality
        if not matches:
            return 0

        # Base score for having all characters
        score = 0.5

        # Bonus for consecutive matches
        consecutive_bonus = 0
        for i in range(1, len(matches)):
            if matches[i] == matches[i - 1] + 1:
                consecutive_bonus += 0.1
        score += min(consecutive_bonus, 0.3)

        # Bonus for early matches
        first_match_pos = matches[0]
        if first_match_pos == 0:
            score += 0.2
        elif first_match_pos < 3:
            score += 0.1

        # Penalty for spread (gaps between matches)
        if len(matches) > 1:
            spread = matches[-1] - matches[0] + 1
            density = len(matches) / spread
            score *= 0.5 + 0.5 * density

        return min(score, 1.0)

    def get_executable_commands(self, context: dict[str, Any]) -> list[FunctionCommand]:
        """
        Get all commands that can execute in the current context.

        Args:
            context: Current application context

        Returns:
            List of executable commands
        """
        executable = []

        for command in self._commands.values():
            if command.visible and command.can_execute(context):
                executable.append(command)

        return executable

    def add_observer(self, observer: Callable[[str, FunctionCommand], None]) -> None:
        """
        Add an observer for registry changes.

        Args:
            observer: Callback function(event_type, command)
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: Callable[[str, FunctionCommand], None]) -> None:
        """
        Remove an observer.

        Args:
            observer: Observer to remove
        """
        if observer in self._observers:
            self._observers.remove(observer)

    def clear(self) -> None:
        """Clear all registered commands (mainly for testing)."""
        self._commands.clear()
        self._categories.clear()
        self._shortcuts.clear()
        self._keywords_index.clear()
        logger.info("CommandRegistry cleared")

    # Private methods

    def _normalize_shortcut(self, shortcut: str) -> str:
        """
        Normalize a shortcut string for consistent comparison.

        Args:
            shortcut: Shortcut string

        Returns:
            Normalized shortcut
        """
        # Convert to lowercase and sort modifiers
        parts = shortcut.lower().split("+")
        modifiers = []
        key = ""

        for part in parts:
            part = part.strip()
            if part in ["ctrl", "alt", "shift", "cmd", "meta"]:
                modifiers.append(part)
            else:
                key = part

        # Sort modifiers for consistent ordering
        modifiers.sort()

        if modifiers:
            return "+".join(modifiers) + "+" + key
        return key

    def _index_keywords(self, command: FunctionCommand) -> None:
        """Index a command's keywords for search."""
        for keyword in command.keywords:
            keyword_lower = keyword.lower()
            if keyword_lower not in self._keywords_index:
                self._keywords_index[keyword_lower] = set()
            self._keywords_index[keyword_lower].add(command.id)

    def _unindex_keywords(self, command: FunctionCommand) -> None:
        """Remove a command's keywords from the index."""
        for keyword in command.keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in self._keywords_index:
                self._keywords_index[keyword_lower].discard(command.id)
                if not self._keywords_index[keyword_lower]:
                    del self._keywords_index[keyword_lower]

    def _notify_observers(self, event_type: str, command: FunctionCommand) -> None:
        """Notify all observers of a registry change."""
        for observer in self._observers:
            try:
                observer(event_type, command)
            except Exception as e:
                logger.error(f"Error notifying observer: {e}", exc_info=True)

    def execute(self, command_id: str, context, **kwargs):
        """
        Execute a command by ID, handling both FunctionCommand and Command classes.

        Args:
            command_id: ID of the command to execute
            context: CommandContext with model reference
            **kwargs: Additional arguments for the command

        Returns:
            CommandResult from the execution
        """
        # Import here to avoid circular dependency
        from viloapp.core.commands.base import CommandResult, CommandStatus

        # First, check if it's a registered FunctionCommand
        legacy_cmd = self.get_command(command_id)
        if legacy_cmd:
            # Update context with kwargs for legacy commands
            if hasattr(context, "args"):
                context.args.update(kwargs)
            elif hasattr(context, "parameters"):
                context.parameters.update(kwargs)
            return legacy_cmd.execute(context)

        # Second, check if it's a Command class
        command_class = self.get_command_class(command_id)
        if command_class:
            try:
                # Instantiate the command with kwargs
                cmd = command_class(**kwargs)
                return cmd.execute(context)
            except Exception as e:
                logger.error(f"Error executing command {command_id}: {e}")
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message=f"Error executing command: {str(e)}",
                    error=e,
                )

        # Command not found
        logger.warning(f"Command not found: {command_id}")
        return CommandResult(
            status=CommandStatus.FAILURE, message=f"Command not found: {command_id}"
        )

    def get_command_class(self, command_id: str):
        """
        Get a Command class by ID.

        Args:
            command_id: The command ID to look up

        Returns:
            Command class if found, None otherwise
        """
        # Import Command classes here to avoid circular dependency
        from viloapp.core.commands.builtin.pane_commands import (
            ChangeWidgetTypeCommand,
            ClosePaneCommand,
            FocusPaneCommand,
            NavigatePaneCommand,
            SplitPaneCommand,
        )
        from viloapp.core.commands.builtin.tab_commands import (
            CloseTabCommand,
            CreateTabCommand,
            RenameTabCommand,
            SwitchTabCommand,
        )

        # Map command IDs to Command classes
        # Handle special cases for split and navigation that need parameters
        if command_id == "pane.splitHorizontal":
            return lambda **kw: SplitPaneCommand(orientation="horizontal", **kw)
        elif command_id == "pane.splitVertical":
            return lambda **kw: SplitPaneCommand(orientation="vertical", **kw)
        elif command_id.startswith("navigate."):
            direction = command_id.split(".")[-1]
            return lambda **kw: NavigatePaneCommand(direction=direction, **kw)

        # Direct Command class mappings
        COMMAND_CLASSES = {
            "tab.create": CreateTabCommand,
            "tab.close": CloseTabCommand,
            "tab.rename": RenameTabCommand,
            "tab.switch": SwitchTabCommand,
            "pane.split": SplitPaneCommand,
            "pane.close": ClosePaneCommand,
            "pane.focus": FocusPaneCommand,
            "pane.changeWidget": ChangeWidgetTypeCommand,
        }

        return COMMAND_CLASSES.get(command_id)


# Global singleton instance
command_registry = CommandRegistry()
