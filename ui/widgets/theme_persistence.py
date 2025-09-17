#!/usr/bin/env python3
"""
Theme persistence operations for import, export, save and load.

Handles all theme file operations including VSCode theme imports,
custom theme management, and backup/restore functionality.
"""

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QWidget

from core.themes.importers import VSCodeThemeImporter
from core.themes.theme import Theme

logger = logging.getLogger(__name__)


class ThemePersistenceManager(QObject):
    """
    Manages all theme persistence operations.

    Provides centralized handling of theme import/export, save/load,
    and theme creation/duplication/deletion operations.
    """

    # Signals
    theme_imported = Signal(str)  # theme_id
    theme_saved = Signal(str)  # theme_id
    theme_created = Signal(str)  # theme_id
    theme_deleted = Signal(str)  # theme_id
    operation_failed = Signal(str)  # error_message

    def __init__(self, parent_widget: QWidget):
        """
        Initialize theme persistence manager.

        Args:
            parent_widget: Parent widget for dialogs
        """
        super().__init__(parent_widget)
        self._parent = parent_widget

    def create_new_theme(self, current_theme: Optional[Theme] = None) -> Optional[str]:
        """
        Create a new theme with user input.

        Args:
            current_theme: Current theme to base new theme on

        Returns:
            New theme ID if created, None if cancelled
        """
        # Get name from user
        name, ok = QInputDialog.getText(self._parent, "New Theme", "Enter theme name:")

        if ok and name:
            try:
                from core.commands.executor import execute_command

                # Create based on current theme
                base_id = current_theme.id if current_theme else "vscode-dark"
                result = execute_command(
                    "theme.createCustomTheme",
                    base_theme_id=base_id,
                    name=name,
                    description=f"Custom theme created from {base_id}",
                )

                if result.success and result.value:
                    new_theme = result.value.get("theme")
                    if new_theme:
                        # Save using command
                        theme_data = new_theme.to_dict()
                        save_result = execute_command(
                            "theme.saveCustomTheme", theme_data=theme_data
                        )

                        if save_result.success:
                            self.theme_created.emit(new_theme.id)
                            return new_theme.id
                        else:
                            self.operation_failed.emit(
                                f"Failed to save new theme: {save_result.error}"
                            )
                    else:
                        self.operation_failed.emit("Failed to create theme")
                else:
                    self.operation_failed.emit(result.error or "Failed to create theme")

            except Exception as e:
                logger.error(f"Failed to create new theme: {e}")
                self.operation_failed.emit(f"Failed to create theme: {e}")

        return None

    def duplicate_theme(
        self, theme: Theme, colors: Optional[dict[str, str]] = None
    ) -> Optional[str]:
        """
        Duplicate an existing theme.

        Args:
            theme: Theme to duplicate
            colors: Optional current colors to use instead of theme colors

        Returns:
            New theme ID if created, None if cancelled
        """
        if not theme:
            self.operation_failed.emit("No theme selected for duplication")
            return None

        # Get name from user
        name, ok = QInputDialog.getText(
            self._parent,
            "Duplicate Theme",
            "Enter theme name:",
            text=f"{theme.name} Copy",
        )

        if ok and name:
            try:
                from core.commands.executor import execute_command

                # Create custom theme using command
                result = execute_command(
                    "theme.createCustomTheme",
                    base_theme_id=theme.id,
                    name=name,
                    description=f"Duplicate of {theme.name}",
                )

                if result.success and result.value:
                    new_theme = result.value.get("theme")
                    if new_theme:
                        # Copy current colors (if provided) or theme colors
                        new_theme.colors = colors or theme.colors

                        # Save using command
                        theme_data = new_theme.to_dict()
                        save_result = execute_command(
                            "theme.saveCustomTheme", theme_data=theme_data
                        )

                        if save_result.success:
                            self.theme_created.emit(new_theme.id)
                            return new_theme.id
                        else:
                            self.operation_failed.emit(
                                f"Failed to save duplicated theme: {save_result.error}"
                            )
                    else:
                        self.operation_failed.emit("Failed to create duplicate theme")
                else:
                    self.operation_failed.emit(
                        result.error or "Failed to create duplicate theme"
                    )

            except Exception as e:
                logger.error(f"Failed to duplicate theme: {e}")
                self.operation_failed.emit(f"Failed to duplicate theme: {e}")

        return None

    def delete_theme(self, theme: Theme) -> bool:
        """
        Delete a theme with confirmation.

        Args:
            theme: Theme to delete

        Returns:
            True if deleted, False if cancelled or failed
        """
        if not theme:
            self.operation_failed.emit("No theme selected for deletion")
            return False

        # Confirm deletion
        reply = QMessageBox.question(
            self._parent,
            "Delete Theme",
            f"Are you sure you want to delete '{theme.name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                from core.commands.executor import execute_command

                result = execute_command("theme.deleteCustomTheme", theme_id=theme.id)

                if result.success:
                    QMessageBox.information(
                        self._parent, "Success", "Theme deleted successfully!"
                    )
                    self.theme_deleted.emit(theme.id)
                    return True
                else:
                    self.operation_failed.emit(result.error or "Cannot delete theme")
                    return False

            except Exception as e:
                logger.error(f"Failed to delete theme: {e}")
                self.operation_failed.emit(f"Failed to delete theme: {e}")
                return False

        return False

    def save_theme(
        self, theme: Theme, colors: dict[str, str], typography_data: dict[str, any]
    ) -> bool:
        """
        Save theme with current settings.

        Args:
            theme: Theme to save
            colors: Current color values
            typography_data: Typography settings

        Returns:
            True if saved successfully
        """
        if not theme:
            self.operation_failed.emit("No theme selected for saving")
            return False

        try:
            # Update theme colors
            theme.colors = colors

            # Update theme typography
            from core.themes.typography import ThemeTypography

            theme.typography = ThemeTypography(
                font_family=f"{typography_data['font_family']}, monospace",
                font_size_base=typography_data["font_size_base"],
                line_height=typography_data["line_height"],
            )

            # Save theme using command
            from core.commands.executor import execute_command

            theme_data = theme.to_dict()
            result = execute_command("theme.saveCustomTheme", theme_data=theme_data)

            if result.success:
                QMessageBox.information(
                    self._parent, "Success", "Theme saved successfully!"
                )
                self.theme_saved.emit(theme.id)
                return True
            else:
                self.operation_failed.emit(f"Failed to save theme: {result.error}")
                return False

        except Exception as e:
            logger.error(f"Failed to save theme: {e}")
            self.operation_failed.emit(f"Failed to save theme: {e}")
            return False

    def apply_theme(
        self, theme: Theme, colors: dict[str, str], typography_data: dict[str, any]
    ) -> bool:
        """
        Apply theme to the application.

        Args:
            theme: Theme to apply
            colors: Current color values
            typography_data: Typography settings

        Returns:
            True if applied successfully
        """
        if not theme:
            self.operation_failed.emit("No theme selected for application")
            return False

        try:
            # Update theme colors
            theme.colors = colors

            # Update theme typography
            from core.themes.typography import ThemeTypography

            theme.typography = ThemeTypography(
                font_family=f"{typography_data['font_family']}, monospace",
                font_size_base=typography_data["font_size_base"],
                line_height=typography_data["line_height"],
            )

            # Apply theme using command
            from core.commands.executor import execute_command

            result = execute_command("theme.applyTheme", theme_id=theme.id)

            if result.success:
                QMessageBox.information(
                    self._parent, "Success", "Theme applied successfully!"
                )
                return True
            else:
                self.operation_failed.emit(f"Failed to apply theme: {result.error}")
                return False

        except Exception as e:
            logger.error(f"Failed to apply theme: {e}")
            self.operation_failed.emit(f"Failed to apply theme: {e}")
            return False

    def import_theme(self) -> Optional[str]:
        """
        Import theme from file.

        Returns:
            Theme ID if imported successfully, None if cancelled or failed
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self._parent, "Import Theme", "", "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                from core.commands.executor import execute_command

                result = execute_command("theme.importTheme", file_path=file_path)

                if result.success and result.value:
                    theme_id = result.value.get("theme_id")
                    QMessageBox.information(
                        self._parent, "Success", "Theme imported successfully!"
                    )
                    self.theme_imported.emit(theme_id)
                    return theme_id
                else:
                    self.operation_failed.emit(result.error or "Failed to import theme")
                    return None

            except Exception as e:
                logger.error(f"Failed to import theme: {e}")
                self.operation_failed.emit(f"Failed to import theme: {e}")
                return None

        return None

    def export_theme(
        self, theme: Theme, colors: Optional[dict[str, str]] = None
    ) -> bool:
        """
        Export theme to file.

        Args:
            theme: Theme to export
            colors: Optional current colors to include

        Returns:
            True if exported successfully
        """
        if not theme:
            self.operation_failed.emit("No theme selected for export")
            return False

        file_path, _ = QFileDialog.getSaveFileName(
            self._parent, "Export Theme", f"{theme.id}.json", "JSON Files (*.json)"
        )

        if file_path:
            try:
                # Update theme with current colors before export if provided
                if colors:
                    theme.colors = colors

                from core.commands.executor import execute_command

                result = execute_command(
                    "theme.exportTheme", theme_id=theme.id, file_path=file_path
                )

                if result.success:
                    QMessageBox.information(
                        self._parent, "Success", "Theme exported successfully!"
                    )
                    return True
                else:
                    self.operation_failed.emit(result.error or "Failed to export theme")
                    return False

            except Exception as e:
                logger.error(f"Failed to export theme: {e}")
                self.operation_failed.emit(f"Failed to export theme: {e}")
                return False

        return False

    def import_vscode_theme(self) -> Optional[str]:
        """
        Import VSCode theme from file.

        Returns:
            Theme ID if imported successfully, None if cancelled or failed
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self._parent,
            "Import VSCode Theme",
            "",
            "JSON Files (*.json);;All Files (*)",
        )

        if file_path:
            try:
                theme = VSCodeThemeImporter.import_from_file(Path(file_path))
                if theme:
                    from core.commands.executor import execute_command

                    # Save imported theme using command
                    theme_data = theme.to_dict()
                    result = execute_command(
                        "theme.saveCustomTheme", theme_data=theme_data
                    )

                    if result.success:
                        QMessageBox.information(
                            self._parent,
                            "Success",
                            "VSCode theme imported successfully!",
                        )
                        self.theme_imported.emit(theme.id)
                        return theme.id
                    else:
                        self.operation_failed.emit(
                            result.error or "Failed to save imported theme"
                        )
                        return None
                else:
                    self.operation_failed.emit("Failed to parse VSCode theme file")
                    return None

            except Exception as e:
                logger.error(f"Failed to import VSCode theme: {e}")
                self.operation_failed.emit(f"Failed to import VSCode theme: {e}")
                return None

        return None

    def load_available_themes(self) -> tuple[list, Optional[Theme]]:
        """
        Load available themes and current theme.

        Returns:
            Tuple of (themes_list, current_theme)
        """
        try:
            from core.commands.executor import execute_command

            themes = []
            current_theme = None

            # Load available themes using command
            result = execute_command("theme.getAvailableThemes")
            if result.success and result.value:
                themes = result.value.get("themes", [])

            # Get current theme using command
            result = execute_command("theme.getCurrentTheme")
            if result.success and result.value:
                current_theme = result.value.get("theme")

            return themes, current_theme

        except Exception as e:
            logger.error(f"Failed to load themes: {e}")
            self.operation_failed.emit(f"Failed to load themes: {e}")
            return [], None

    def load_theme_by_id(self, theme_id: str) -> Optional[Theme]:
        """
        Load a specific theme by ID.

        Args:
            theme_id: Theme identifier

        Returns:
            Theme object if found, None otherwise
        """
        try:
            from core.commands.executor import execute_command

            result = execute_command("theme.getTheme", theme_id=theme_id)
            if result.success and result.value:
                return result.value.get("theme")
        except Exception as e:
            logger.error(f"Failed to load theme {theme_id}: {e}")
            self.operation_failed.emit(f"Failed to load theme: {e}")

        return None
