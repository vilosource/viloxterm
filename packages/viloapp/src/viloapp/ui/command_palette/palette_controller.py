#!/usr/bin/env python3
"""
Command palette controller - coordinates between UI and command execution.

This controller implements the MVC pattern by mediating between the
command palette widget (view) and the command system (model).
"""

import json
import logging
from typing import Any, Optional

from PySide6.QtCore import QObject, QSettings, Signal

from viloapp.core.commands.base import Command, CommandContext
from viloapp.core.commands.executor import command_executor
from viloapp.core.commands.registry import command_registry
from viloapp.core.context.manager import context_manager

from .palette_widget import CommandPaletteWidget

logger = logging.getLogger(__name__)


class CommandPaletteController(QObject):
    """
    Controller for command palette MVC architecture.

    Integrates with existing systems:
    - CommandRegistry for search and command management
    - ContextManager for when-clause evaluation
    - Command system for accessing services
    """

    # Signals
    palette_shown = Signal()
    palette_hidden = Signal()
    command_executed = Signal(str, dict)  # command_id, result

    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)

        self.main_window = main_window

        # Create palette widget
        self.palette_widget = CommandPaletteWidget(main_window)

        # Connect signals
        self.palette_widget.command_executed.connect(self.on_command_executed)
        self.palette_widget.palette_closed.connect(self.on_palette_closed)

        # Command execution state
        self.current_context: Optional[dict[str, Any]] = None

        # Recent commands tracking
        self._recent_commands: list[str] = []
        self._max_recent = 20
        self._load_recent_commands()

        logger.info("CommandPaletteController initialized")

    def show_palette(self):
        """Show the command palette with filtered commands."""
        try:
            # Update context to indicate palette is visible
            from viloapp.core.context.keys import ContextKey

            context_manager.set(ContextKey.COMMAND_PALETTE_VISIBLE, True)
            context_manager.set(ContextKey.COMMAND_PALETTE_FOCUS, True)

            # Get current context for filtering
            self.current_context = context_manager.get_all()
            logger.debug(f"Current context keys: {list(self.current_context.keys())}")

            # Get all available commands
            all_commands = command_registry.get_all_commands()

            # Filter commands based on current context
            available_commands = []
            for command in all_commands:
                if command.can_execute(self.current_context):
                    available_commands.append(command)
                else:
                    logger.debug(
                        f"Command {command.id} filtered out by when-clause: {command.when}"
                    )

            logger.info(
                f"Showing palette with {len(available_commands)} of {len(all_commands)} commands"
            )

            # Get recent commands (if any)
            recent_command_objects = []
            for cmd_id in self._recent_commands[:5]:  # Show top 5 recent
                cmd = command_registry.get_command(cmd_id)
                if cmd and cmd.can_execute(self.current_context):
                    recent_command_objects.append(cmd)

            # Show palette with filtered commands and recent section
            self.palette_widget.show_palette(available_commands, recent_command_objects)
            self.palette_shown.emit()

        except Exception as e:
            logger.error(f"Failed to show command palette: {e}")

    def hide_palette(self):
        """Hide the command palette."""
        self.palette_widget.close_palette()

    def is_visible(self) -> bool:
        """Check if the palette is currently visible."""
        return self.palette_widget.isVisible()

    def search_commands(self, query: str) -> list[Command]:
        """
        Search commands using the registry's fuzzy search.

        Args:
            query: Search query

        Returns:
            List of matching commands, filtered by context
        """
        try:
            # Use registry's search functionality
            search_results = command_registry.search_commands(query)

            # Filter by current context
            if self.current_context:
                filtered_results = []
                for command in search_results:
                    if command.can_execute(self.current_context):
                        filtered_results.append(command)

                logger.debug(
                    f"Search '{query}': {len(filtered_results)} of {len(search_results)} results available"
                )
                return filtered_results

            return search_results

        except Exception as e:
            logger.error(f"Command search failed: {e}")
            return []

    def on_command_executed(self, command_id: str, kwargs: dict[str, Any]):
        """
        Handle command execution from the palette.

        Args:
            command_id: ID of command to execute
            kwargs: Command arguments
        """
        try:
            logger.info(f"Executing command from palette: {command_id}")

            # Create command context
            context = CommandContext(main_window=self.main_window, args=kwargs)

            # Execute command through executor
            result = command_executor.execute(command_id, context)

            if result.success:
                self._add_recent_command(command_id)
                logger.info(f"Command {command_id} executed successfully")

                # Update command usage statistics (future enhancement)
                self._track_command_usage(command_id, context)

                # Emit success signal
                self.command_executed.emit(
                    command_id, {"success": True, "value": result.value}
                )

            else:
                logger.warning(f"Command {command_id} failed: {result.error}")

                # Emit failure signal
                self.command_executed.emit(
                    command_id, {"success": False, "error": result.error}
                )

                # Show error to user if main window available
                if self.main_window and hasattr(self.main_window, "status_bar"):
                    self.main_window.status_bar.set_message(
                        f"Command failed: {result.error}", 5000
                    )

        except Exception as e:
            logger.error(f"Failed to execute command {command_id}: {e}")

            # Emit failure signal
            self.command_executed.emit(command_id, {"success": False, "error": str(e)})

    def on_palette_closed(self):
        """Handle palette being closed."""
        logger.debug("Command palette closed")

        # Update context to indicate palette is hidden
        from viloapp.core.context.keys import ContextKey

        context_manager.set(ContextKey.COMMAND_PALETTE_VISIBLE, False)
        context_manager.set(ContextKey.COMMAND_PALETTE_FOCUS, False)

        self.current_context = None
        self.palette_hidden.emit()

    def _track_command_usage(self, command_id: str, context: CommandContext):
        """
        Track command usage for analytics and recommendations.

        Args:
            command_id: ID of executed command
            context: Command execution context
        """
        try:
            # This will be implemented when we add command history/analytics
            # For now, just log usage
            logger.debug(f"Command usage: {command_id}")

            # Future: Update usage statistics through commands

        except Exception as e:
            logger.error(f"Failed to track command usage: {e}")

    def get_palette_settings(self) -> dict[str, Any]:
        """
        Get command palette configuration from settings.

        Returns:
            Palette settings dictionary
        """
        # Return default settings since this method is not currently used
        # If settings are needed in the future, they should be accessed through commands
        return {}

    def update_palette_settings(self, settings: dict[str, Any]) -> bool:
        """
        Update command palette settings.

        Args:
            settings: New palette settings

        Returns:
            True if settings were updated successfully
        """
        # Return True since this method is not currently used
        # If settings updates are needed in the future, they should be done through commands
        return True

    def get_recent_commands(self) -> list[str]:
        """
        Get list of recently used command IDs.

        Returns:
            List of command IDs in reverse chronological order
        """
        return self._recent_commands.copy()

    def clear_recent_commands(self):
        """Clear the recent commands history."""
        self._recent_commands.clear()
        self._save_recent_commands()

    def _add_recent_command(self, command_id: str):
        """Add a command to recent history."""
        # Remove if already in list
        if command_id in self._recent_commands:
            self._recent_commands.remove(command_id)

        # Add to front
        self._recent_commands.insert(0, command_id)

        # Trim to max size
        if len(self._recent_commands) > self._max_recent:
            self._recent_commands = self._recent_commands[: self._max_recent]

        # Save to settings
        self._save_recent_commands()

    def _load_recent_commands(self):
        """Load recent commands from settings."""
        try:
            settings = QSettings("ViloxTerm", "CommandPalette")
            recent_json = settings.value("recent_commands", "[]")
            if recent_json:
                self._recent_commands = json.loads(recent_json)
                # Validate that all commands still exist
                self._recent_commands = [
                    cmd_id
                    for cmd_id in self._recent_commands
                    if command_registry.get_command(cmd_id)
                ]
        except Exception as e:
            logger.error(f"Failed to load recent commands: {e}")
            self._recent_commands = []

    def _save_recent_commands(self):
        """Save recent commands to settings."""
        try:
            settings = QSettings("ViloxTerm", "CommandPalette")
            settings.setValue("recent_commands", json.dumps(self._recent_commands))
        except Exception as e:
            logger.error(f"Failed to save recent commands: {e}")

    def set_command_favorite(self, command_id: str, is_favorite: bool) -> bool:
        """
        Mark a command as favorite or remove from favorites.

        Args:
            command_id: Command to mark/unmark as favorite
            is_favorite: True to add to favorites, False to remove

        Returns:
            True if favorite status was updated
        """
        # Future enhancement: implement favorites system
        return False

    def get_favorite_commands(self) -> list[str]:
        """
        Get list of favorite command IDs.

        Returns:
            List of favorite command IDs
        """
        # Future enhancement
        return []

    def get_command_recommendations(self) -> list[Command]:
        """
        Get recommended commands based on context and usage history.

        Returns:
            List of recommended commands
        """
        try:
            # Simple implementation: return most common commands by category
            current_context = context_manager.get_all()
            all_commands = command_registry.get_all_commands()

            recommendations = []

            # Add commands from common categories
            common_categories = ["File", "Edit", "View", "Workspace"]
            for category in common_categories:
                category_commands = [
                    cmd
                    for cmd in all_commands
                    if cmd.category == category and cmd.can_execute(current_context)
                ]
                recommendations.extend(category_commands[:2])  # Top 2 per category

            return recommendations[:8]  # Limit to 8 recommendations

        except Exception as e:
            logger.error(f"Failed to get command recommendations: {e}")
            return []

    def refresh_commands(self):
        """Refresh the command list in the palette (if visible)."""
        if self.is_visible():
            logger.debug("Refreshing command palette")
            self.show_palette()  # Re-show with updated commands

    def cleanup(self):
        """Cleanup controller resources."""
        logger.debug("Cleaning up CommandPaletteController")

        if self.palette_widget:
            self.palette_widget.close()
            self.palette_widget = None

        self.current_context = None
        self.main_window = None
