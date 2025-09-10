#!/usr/bin/env python3
"""
Command registry for managing all application commands.

The CommandRegistry is a singleton that maintains all registered commands,
handles command indexing, and provides search capabilities.
"""

from typing import Dict, List, Optional, Set, Callable, Any
import logging
from threading import Lock

from core.commands.base import Command, CommandContext

logger = logging.getLogger(__name__)


class CommandRegistry:
    """
    Central registry for all application commands.
    
    This is a singleton that manages command registration, lookup,
    and categorization. All commands must be registered here to be
    available to the system.
    """
    
    _instance: Optional['CommandRegistry'] = None
    _lock = Lock()
    
    def __new__(cls) -> 'CommandRegistry':
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
            
        self._commands: Dict[str, Command] = {}
        self._categories: Dict[str, List[Command]] = {}
        self._shortcuts: Dict[str, List[str]] = {}  # shortcut -> [command_ids]
        self._keywords_index: Dict[str, Set[str]] = {}  # keyword -> {command_ids}
        self._observers: List[Callable[[str, Command], None]] = []
        self._initialized = True
        
        logger.info("CommandRegistry initialized")
    
    def register(self, command: Command) -> None:
        """
        Register a command.
        
        Args:
            command: Command to register
            
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
                logger.warning(
                    f"Shortcut conflict for {shortcut}: {self._shortcuts[shortcut]}"
                )
        
        # Index by keywords
        self._index_keywords(command)
        
        # Notify observers
        self._notify_observers('registered', command)
        
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
        self._notify_observers('unregistered', command)
        
        logger.debug(f"Unregistered command: {command_id}")
        return True
    
    def get_command(self, command_id: str) -> Optional[Command]:
        """
        Get a command by ID.
        
        Args:
            command_id: Command ID to look up
            
        Returns:
            Command if found, None otherwise
        """
        return self._commands.get(command_id)
    
    def get_all_commands(self) -> List[Command]:
        """
        Get all registered commands.
        
        Returns:
            List of all commands
        """
        return list(self._commands.values())
    
    def get_commands_by_category(self, category: str) -> List[Command]:
        """
        Get all commands in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of commands in the category
        """
        return self._categories.get(category, []).copy()
    
    def get_categories(self) -> List[str]:
        """
        Get all command categories.
        
        Returns:
            List of category names
        """
        return list(self._categories.keys())
    
    def get_commands_by_shortcut(self, shortcut: str) -> List[Command]:
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
    
    def search_commands(self, query: str) -> List[Command]:
        """
        Search for commands by title, description, or keywords.
        
        Args:
            query: Search query
            
        Returns:
            List of matching commands sorted by relevance
        """
        query_lower = query.lower()
        results = []
        
        for command in self._commands.values():
            score = 0
            
            # Check title (highest priority)
            if query_lower in command.title.lower():
                score += 10
                if command.title.lower().startswith(query_lower):
                    score += 5
            
            # Check category
            if query_lower in command.category.lower():
                score += 5
            
            # Check description
            if command.description and query_lower in command.description.lower():
                score += 3
            
            # Check keywords
            for keyword in command.keywords:
                if query_lower in keyword.lower():
                    score += 2
                    if keyword.lower() == query_lower:
                        score += 3
            
            # Check command ID
            if query_lower in command.id.lower():
                score += 1
            
            if score > 0:
                results.append((score, command))
        
        # Sort by score (descending) and then by title
        results.sort(key=lambda x: (-x[0], x[1].title))
        
        return [cmd for _, cmd in results]
    
    def get_executable_commands(self, context: Dict[str, Any]) -> List[Command]:
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
    
    def add_observer(self, observer: Callable[[str, Command], None]) -> None:
        """
        Add an observer for registry changes.
        
        Args:
            observer: Callback function(event_type, command)
        """
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer: Callable[[str, Command], None]) -> None:
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
        parts = shortcut.lower().split('+')
        modifiers = []
        key = ''
        
        for part in parts:
            part = part.strip()
            if part in ['ctrl', 'alt', 'shift', 'cmd', 'meta']:
                modifiers.append(part)
            else:
                key = part
        
        # Sort modifiers for consistent ordering
        modifiers.sort()
        
        if modifiers:
            return '+'.join(modifiers) + '+' + key
        return key
    
    def _index_keywords(self, command: Command) -> None:
        """Index a command's keywords for search."""
        for keyword in command.keywords:
            keyword_lower = keyword.lower()
            if keyword_lower not in self._keywords_index:
                self._keywords_index[keyword_lower] = set()
            self._keywords_index[keyword_lower].add(command.id)
    
    def _unindex_keywords(self, command: Command) -> None:
        """Remove a command's keywords from the index."""
        for keyword in command.keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in self._keywords_index:
                self._keywords_index[keyword_lower].discard(command.id)
                if not self._keywords_index[keyword_lower]:
                    del self._keywords_index[keyword_lower]
    
    def _notify_observers(self, event_type: str, command: Command) -> None:
        """Notify all observers of a registry change."""
        for observer in self._observers:
            try:
                observer(event_type, command)
            except Exception as e:
                logger.error(f"Error notifying observer: {e}", exc_info=True)


# Global singleton instance
command_registry = CommandRegistry()