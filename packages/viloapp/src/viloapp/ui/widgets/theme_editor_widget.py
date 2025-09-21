#!/usr/bin/env python3
"""
Theme editor widget for creating and customizing themes.

Provides a complete interface for editing, previewing, and managing themes.
"""

import logging
from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from viloapp.core.themes.theme import Theme
from viloapp.ui.widgets.app_widget import AppWidget
from viloapp.ui.widgets.theme_editor_controls import ThemeControlsWidget
from viloapp.ui.widgets.theme_persistence import ThemePersistenceManager
from viloapp.ui.widgets.theme_preview_widget import ThemePreviewWidget

logger = logging.getLogger(__name__)


class ThemeEditorAppWidget(AppWidget):
    """
    Complete theme editor as an app widget.

    Features:
    - Theme selection and management
    - Property editor with categorized color pickers
    - Live preview
    - Import/export functionality
    - Save/reset capabilities
    """

    # Signal emitted when theme is modified
    theme_modified = Signal(bool)  # True if modified, False if saved/reset

    def __init__(
        self,
        widget_id: str = None,
        parent: Optional[QWidget] = None,
        show_bottom_buttons: bool = True,
    ):
        """
        Initialize theme editor.

        Args:
            widget_id: Unique widget identifier (auto-generated if None)
            parent: Parent widget
            show_bottom_buttons: Whether to show Apply/Save/Reset buttons at bottom
        """
        # Generate widget ID if not provided
        if widget_id is None:
            import uuid

            widget_id = str(uuid.uuid4())[:8]

        # Import WidgetType here to avoid circular imports
        from viloapp.ui.widgets.widget_registry import WidgetType

        # Initialize AppWidget with SETTINGS type
        super().__init__(widget_id, WidgetType.SETTINGS, parent)

        self._current_theme: Optional[Theme] = None
        self._modified = False
        self._show_bottom_buttons = show_bottom_buttons
        self._preview_timer = QTimer()
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._apply_preview)

        self._updating = False  # Flag to prevent recursive updates

        # Initialize components
        self._controls_widget: Optional[ThemeControlsWidget] = None
        self._preview_widget: Optional[ThemePreviewWidget] = None
        self._persistence_manager: Optional[ThemePersistenceManager] = None

        self._setup_ui()
        self._setup_components()
        self._load_current_theme()
        self._connect_theme_signals()

    def get_title(self) -> str:
        """Get widget title for tab/pane."""
        return "Theme Editor"

    def get_icon(self) -> Optional[QIcon]:
        """Get widget icon."""
        # Return palette icon if available
        return None

    def can_close(self) -> bool:
        """Check if widget can be closed."""
        if self._modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            )

            if reply == QMessageBox.Save:
                return self._save_theme()
            elif reply == QMessageBox.Cancel:
                return False

        return True

    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return self._modified

    def apply_changes(self) -> bool:
        """Apply current theme changes. Public method for parent widgets."""
        return self._apply_theme()

    def save_changes(self) -> bool:
        """Save current theme changes. Public method for parent widgets."""
        return self._save_theme()

    def reset_changes(self):
        """Reset theme changes. Public method for parent widgets."""
        self._reset_changes()

    def showEvent(self, event):  # noqa: N802
        """Handle widget show event."""
        super().showEvent(event)
        # Ensure splitter is properly configured when shown
        if hasattr(self, "_splitter") and hasattr(self, "_controls_widget"):
            # Make sure both widgets are visible
            if self._controls_widget:
                self._controls_widget.show()
            if hasattr(self, "_preview_widget") and self._preview_widget:
                self._preview_widget.parent().show()  # Show the preview container
            # Reset splitter sizes
            self._splitter.setSizes([600, 900])
            logger.debug("ThemeEditor shown, splitter sizes reset")

    def _setup_ui(self):
        """Set up the editor UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Theme selector
        selector_layout = QHBoxLayout()
        selector_layout.setContentsMargins(8, 8, 8, 8)

        selector_layout.addWidget(QLabel("Theme:"))

        self._theme_combo = QComboBox()
        self._theme_combo.currentTextChanged.connect(self._on_theme_changed)
        selector_layout.addWidget(self._theme_combo, 1)

        self._new_button = QPushButton("New")
        self._new_button.clicked.connect(self._create_new_theme)
        selector_layout.addWidget(self._new_button)

        self._duplicate_button = QPushButton("Duplicate")
        self._duplicate_button.clicked.connect(self._duplicate_theme)
        selector_layout.addWidget(self._duplicate_button)

        layout.addLayout(selector_layout)

        # Main content splitter
        self._splitter = QSplitter(Qt.Horizontal)

        # Left: Controls (will be set up in _setup_components)
        self._controls_placeholder = QFrame()
        self._controls_placeholder.setMinimumWidth(500)  # Ensure enough space for color controls
        # Add a temporary label to make it visible
        placeholder_layout = QVBoxLayout()
        placeholder_layout.addWidget(QLabel("Loading color controls..."))
        self._controls_placeholder.setLayout(placeholder_layout)
        self._splitter.addWidget(self._controls_placeholder)

        # Right: Preview
        preview_container = QFrame()
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(8, 8, 8, 8)

        preview_label = QLabel("Preview")
        preview_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        preview_layout.addWidget(preview_label)

        # Preview (will be set up in _setup_components)
        self._preview_placeholder = QFrame()
        preview_layout.addWidget(self._preview_placeholder, 1)

        preview_container.setLayout(preview_layout)
        self._splitter.addWidget(preview_container)

        # Set splitter sizes for a better balance between controls and preview
        # 40% for controls (color editor), 60% for preview
        self._splitter.setSizes([600, 900])  # Total 1500px default
        self._splitter.setStretchFactor(0, 2)  # Controls panel can stretch
        self._splitter.setStretchFactor(1, 3)  # Preview panel stretches more

        layout.addWidget(self._splitter, 1)

        # Bottom buttons (only if requested)
        if self._show_bottom_buttons:
            button_layout = QHBoxLayout()
            button_layout.setContentsMargins(8, 8, 8, 8)

            self._apply_button = QPushButton("Apply")
            self._apply_button.clicked.connect(self._apply_theme)
            self._apply_button.setEnabled(False)
            button_layout.addWidget(self._apply_button)

            self._save_button = QPushButton("Save")
            self._save_button.clicked.connect(self._save_theme)
            self._save_button.setEnabled(False)
            button_layout.addWidget(self._save_button)

            button_layout.addStretch()

            self._reset_button = QPushButton("Reset")
            self._reset_button.clicked.connect(self._reset_changes)
            self._reset_button.setEnabled(False)
            button_layout.addWidget(self._reset_button)

            layout.addLayout(button_layout)
        else:
            # Initialize button references to None when not shown
            self._apply_button = None
            self._save_button = None
            self._reset_button = None

        self.setLayout(layout)

    def _setup_components(self):
        """Set up the component widgets after UI is created."""
        logger.debug("Setting up theme editor components")

        # Initialize persistence manager
        self._persistence_manager = ThemePersistenceManager(self)
        self._connect_persistence_signals()

        # Create and setup controls widget
        logger.debug("Creating ThemeControlsWidget")
        self._controls_widget = ThemeControlsWidget()
        self._connect_controls_signals()
        logger.debug(f"Controls widget created: {self._controls_widget}")

        # Replace placeholder with actual controls in the splitter
        if hasattr(self, "_splitter"):
            logger.debug(f"Splitter exists with {self._splitter.count()} widgets")
            index = self._splitter.indexOf(self._controls_placeholder)
            logger.debug(f"Placeholder index in splitter: {index}")
            if index >= 0:
                logger.debug(f"Replacing placeholder at index {index} with controls widget")
                self._splitter.replaceWidget(index, self._controls_widget)
                self._controls_placeholder.deleteLater()
                # Ensure the controls widget is visible
                self._controls_widget.show()
                logger.debug(f"Controls widget visible: {self._controls_widget.isVisible()}")
        else:
            logger.error("Splitter not found!")

        # Create and setup preview widget
        self._preview_widget = ThemePreviewWidget()

        # Replace placeholder with actual preview
        parent = self._preview_placeholder.parent()
        parent_layout = parent.layout()
        if parent_layout:
            index = parent_layout.indexOf(self._preview_placeholder)
            parent_layout.removeWidget(self._preview_placeholder)
            self._preview_placeholder.deleteLater()
            parent_layout.insertWidget(index, self._preview_widget, 1)

        # Re-set splitter sizes after replacing widgets
        if hasattr(self, "_splitter"):
            # Force update of splitter and ensure widgets are shown
            self._splitter.refresh()
            self._splitter.setSizes([600, 900])

            logger.debug(f"Splitter widget count: {self._splitter.count()}")
            for i in range(self._splitter.count()):
                widget = self._splitter.widget(i)
                widget.show()  # Force show each widget
                logger.debug(
                    f"  Widget {i}: {widget.__class__.__name__} (visible: {widget.isVisible()})"
                )

    def _connect_controls_signals(self):
        """Connect signals from controls widget."""
        if self._controls_widget:
            self._controls_widget.color_changed.connect(self._on_color_changed)
            self._controls_widget.typography_changed.connect(self._on_typography_changed)
            self._controls_widget.preset_changed.connect(self._on_preset_changed)

    def _connect_persistence_signals(self):
        """Connect signals from persistence manager."""
        if self._persistence_manager:
            self._persistence_manager.theme_imported.connect(self._on_theme_imported)
            self._persistence_manager.theme_saved.connect(self._on_theme_saved)
            self._persistence_manager.theme_created.connect(self._on_theme_created)
            self._persistence_manager.theme_deleted.connect(self._on_theme_deleted)
            self._persistence_manager.operation_failed.connect(self._on_operation_failed)

    def _create_toolbar(self) -> QToolBar:
        """Create editor toolbar."""
        toolbar = QToolBar()

        # Import action
        import_action = QAction("Import", self)
        import_action.setToolTip("Import theme from file")
        import_action.triggered.connect(
            lambda: (
                self._persistence_manager.import_theme() if self._persistence_manager else None
            )
        )
        toolbar.addAction(import_action)

        # Export action
        export_action = QAction("Export", self)
        export_action.setToolTip("Export current theme")
        export_action.triggered.connect(self._export_theme)
        toolbar.addAction(export_action)

        toolbar.addSeparator()

        # Import VSCode action
        vscode_action = QAction("Import VSCode", self)
        vscode_action.setToolTip("Import VSCode theme")
        vscode_action.triggered.connect(
            lambda: (
                self._persistence_manager.import_vscode_theme()
                if self._persistence_manager
                else None
            )
        )
        toolbar.addAction(vscode_action)

        toolbar.addSeparator()

        # Delete action
        delete_action = QAction("Delete", self)
        delete_action.setToolTip("Delete current theme")
        delete_action.triggered.connect(self._delete_theme)
        toolbar.addAction(delete_action)

        return toolbar

    def _load_current_theme(self):
        """Load current theme and available themes using commands."""
        try:
            from viloapp.core.commands.executor import execute_command

            # Load available themes using command
            result = execute_command("theme.getAvailableThemes")
            if result.success and result.value:
                themes = result.value.get("themes", [])
                self._theme_combo.clear()

                for theme_info in themes:
                    self._theme_combo.addItem(theme_info.name, theme_info.id)

            # Get current theme using command
            result = execute_command("theme.getCurrentTheme")
            if result.success and result.value:
                current_theme = result.value.get("theme")
                if current_theme:
                    index = self._theme_combo.findData(current_theme.id)
                    if index >= 0:
                        # Block signals to prevent triggering _on_theme_changed during initial load
                        self._theme_combo.blockSignals(True)
                        self._theme_combo.setCurrentIndex(index)
                        self._theme_combo.blockSignals(False)
                    self._load_theme(current_theme)

        except Exception as e:
            logger.error(f"Failed to load themes: {e}")

    def _load_theme(self, theme: Theme, mark_modified: bool = False):
        """Load theme into editor.

        Args:
            theme: Theme to load
            mark_modified: If True, mark the editor as modified (enables Apply button)
        """
        if self._updating:
            return  # Prevent recursive updates

        self._updating = True
        try:
            self._current_theme = theme

            # Update controls widget
            if self._controls_widget:
                # Load colors
                self._controls_widget.load_colors(theme.colors)

                # Load typography settings
                if theme.typography:
                    typography = theme.typography
                    self._controls_widget.load_typography_settings(
                        typography.font_family.split(",")[0].strip(),
                        typography.font_size_base,
                        typography.line_height,
                        "custom",
                    )
                else:
                    # Use defaults
                    self._controls_widget.load_typography_settings("Fira Code", 14, 1.5, "default")

            # Update preview
            if self._preview_widget:
                self._preview_widget.apply_theme_colors(theme.colors)

            # Set modified state based on parameter
            self._modified = mark_modified
            self._update_button_states()
        finally:
            self._updating = False

    def _on_theme_changed(self, theme_name: str):
        """Handle theme selection change."""
        if self._modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to discard them?",
                QMessageBox.Discard | QMessageBox.Cancel,
            )

            if reply == QMessageBox.Cancel:
                # Restore previous selection
                if self._current_theme:
                    index = self._theme_combo.findData(self._current_theme.id)
                    if index >= 0:
                        self._theme_combo.setCurrentIndex(index)
                return

        # Load selected theme using command
        theme_id = self._theme_combo.currentData()
        if theme_id:
            from viloapp.core.commands.executor import execute_command

            result = execute_command("theme.getTheme", theme_id=theme_id)
            if result.success and result.value:
                theme = result.value.get("theme")
                if theme:
                    # Check if this is a different theme than currently loaded
                    # Only mark as modified if we had a previous theme and it's different
                    theme_changed = (
                        self._current_theme is not None and theme.id != self._current_theme.id
                    )

                    # Load theme and mark as modified if it's a different theme
                    self._load_theme(theme, mark_modified=theme_changed)

    def _on_color_changed(self, key: str, value: str, is_preview: bool):
        """Handle color change from picker."""
        if self._updating:
            return  # Prevent recursive updates

        self._modified = True
        self._update_button_states()

        # Schedule preview update for the widget's preview pane
        self._preview_timer.stop()
        self._preview_timer.start(100)  # Debounce preview updates

        # Don't apply theme preview to the whole app during editing
        # The preview widget will be updated by the timer

        # Emit modified signal
        self.theme_modified.emit(True)

    def _apply_preview(self):
        """Apply preview colors."""
        colors = self._get_current_colors()
        self._preview_widget.apply_theme_colors(colors)

    def _get_current_colors(self) -> dict[str, str]:
        """Get current colors from controls widget."""
        if self._controls_widget:
            return self._controls_widget.get_current_colors()
        return {}

    def _apply_theme(self) -> bool:
        """Apply current theme changes using persistence manager."""
        if not self._persistence_manager or not self._current_theme:
            return False

        colors = self._get_current_colors()
        typography_data = (
            self._controls_widget.get_typography_settings() if self._controls_widget else {}
        )

        success = self._persistence_manager.apply_theme(
            self._current_theme, colors, typography_data
        )
        if success:
            self._modified = False
            self._update_button_states()
            # Emit signal that changes were applied
            self.theme_modified.emit(False)
        return success

    def _save_theme(self) -> bool:
        """Save current theme changes using persistence manager."""
        if not self._persistence_manager or not self._current_theme:
            return False

        colors = self._get_current_colors()
        typography_data = (
            self._controls_widget.get_typography_settings() if self._controls_widget else {}
        )

        success = self._persistence_manager.save_theme(self._current_theme, colors, typography_data)
        if success:
            self._modified = False
            self._update_button_states()
            # Emit signal that changes were saved
            self.theme_modified.emit(False)
        return success

    def _reset_changes(self):
        """Reset all changes to original theme."""
        if self._current_theme:
            self._load_theme(self._current_theme)
            self._modified = False
            self._update_button_states()
            # Emit signal that changes were reset
            self.theme_modified.emit(False)

    def _create_new_theme(self):
        """Create a new theme using persistence manager."""
        if self._persistence_manager:
            theme_id = self._persistence_manager.create_new_theme(self._current_theme)
            if theme_id:
                self._load_current_theme()
                # Select new theme
                index = self._theme_combo.findData(theme_id)
                if index >= 0:
                    self._theme_combo.setCurrentIndex(index)

    def _duplicate_theme(self):
        """Duplicate current theme using persistence manager."""
        if self._persistence_manager and self._current_theme:
            colors = self._get_current_colors()
            theme_id = self._persistence_manager.duplicate_theme(self._current_theme, colors)
            if theme_id:
                self._load_current_theme()
                # Select new theme
                index = self._theme_combo.findData(theme_id)
                if index >= 0:
                    self._theme_combo.setCurrentIndex(index)

    def _delete_theme(self):
        """Delete current theme using persistence manager."""
        if self._persistence_manager and self._current_theme:
            if self._persistence_manager.delete_theme(self._current_theme):
                self._load_current_theme()

    def _export_theme(self):
        """Export current theme using persistence manager."""
        if self._persistence_manager and self._current_theme:
            colors = self._get_current_colors()
            self._persistence_manager.export_theme(self._current_theme, colors)

    def _on_theme_imported(self, theme_id: str):
        """Handle theme imported signal."""
        self._load_current_theme()
        # Select imported theme
        index = self._theme_combo.findData(theme_id)
        if index >= 0:
            self._theme_combo.setCurrentIndex(index)

    def _on_theme_saved(self, theme_id: str):
        """Handle theme saved signal."""
        self._modified = False
        self._update_button_states()

    def _on_theme_created(self, theme_id: str):
        """Handle theme created signal."""
        self._load_current_theme()
        # Select new theme
        index = self._theme_combo.findData(theme_id)
        if index >= 0:
            self._theme_combo.setCurrentIndex(index)

    def _on_theme_deleted(self, theme_id: str):
        """Handle theme deleted signal."""
        self._load_current_theme()

    def _on_operation_failed(self, error_message: str):
        """Handle operation failed signal."""
        QMessageBox.critical(self, "Error", error_message)

    def _on_typography_changed(self):
        """Handle typography settings change from controls widget."""
        if self._updating:
            return

        self._modified = True
        self._update_button_states()

        # Emit modified signal so parent widgets know about the change
        self.theme_modified.emit(True)

        # Apply preview to the preview widget
        self._apply_preview()

    def _on_preset_changed(self, preset: str):
        """Handle typography preset change from controls widget."""
        if self._updating:
            return

        self._modified = True
        self._update_button_states()

        # Emit modified signal so parent widgets know about the change
        self.theme_modified.emit(True)

        # Apply preview
        self._apply_preview()

    def _update_button_states(self):
        """Update button enabled states."""
        if self._apply_button:
            self._apply_button.setEnabled(self._modified)
        if self._save_button:
            self._save_button.setEnabled(self._modified)
        if self._reset_button:
            self._reset_button.setEnabled(self._modified)

    def _connect_theme_signals(self):
        """Connect to theme service signals."""
        # Theme change signals are now handled through the theme provider
        # which is available through the UI service
        pass

    def _on_external_theme_change(self, colors: dict[str, str]):
        """Handle theme changes from outside the editor."""
        if self._updating:
            return  # Ignore if we're the ones updating

        # Only reload if not modified or if it's a different theme
        if not self._modified:
            from viloapp.core.commands.executor import execute_command

            result = execute_command("theme.getCurrentTheme")
            current_theme = result.value.get("theme") if result.success and result.value else None
            if current_theme and (
                not self._current_theme or current_theme.id != self._current_theme.id
            ):
                # Theme changed externally, reload
                index = self._theme_combo.findData(current_theme.id)
                if index >= 0:
                    self._theme_combo.blockSignals(True)
                    self._theme_combo.setCurrentIndex(index)
                    self._theme_combo.blockSignals(False)
                self._load_theme(current_theme)
