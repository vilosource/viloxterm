#!/usr/bin/env python3
"""
Comprehensive settings widget for managing application defaults.

This AppWidget provides a tabbed interface for configuring all application
settings including workspace defaults, appearance, keyboard shortcuts, and more.
"""

import json
import logging
from typing import Any, Optional, Set

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from viloapp.core.capabilities import WidgetCapability
from viloapp.core.settings.app_defaults import (
    get_app_default,
    get_app_defaults,
    set_app_default,
)
from viloapp.ui.widgets.app_widget import AppWidget
from viloapp.ui.widgets.shortcut_config_app_widget import ShortcutConfigAppWidget

# Widget ID defined in class

logger = logging.getLogger(__name__)


class SettingsAppWidget(AppWidget):
    """
    Comprehensive settings management widget.

    Provides a tabbed interface for configuring all application settings
    with validation, import/export, and reset capabilities.
    """

    # Widget ID for this widget type
    WIDGET_ID = "com.viloapp.settings"

    settings_changed = Signal(str, object)  # key, value

    def __init__(self, widget_id: str = None, parent: Optional[QWidget] = None):
        """
        Initialize settings widget.

        Args:
            widget_id: Unique widget identifier
            parent: Parent widget
        """
        if widget_id is None:
            import uuid

            widget_id = str(uuid.uuid4())[:8]

        super().__init__(widget_id, self.WIDGET_ID, parent)

        self._defaults_manager = get_app_defaults()
        self._modified_settings = {}
        self._theme_service = None
        self._theme_provider = None

        # Connect to theme service for theme updates
        self._connect_to_theme_service()

        self._setup_ui()
        self._apply_theme()
        self._load_current_settings()

    def _connect_to_theme_service(self):
        """Connect to theme service for theme updates."""
        # Theme updates will be handled through commands
        # No direct service access needed
        pass

    def _apply_theme(self):
        """Apply theme to the widget."""
        # Theme will be applied through the application's theming system
        # No need for direct style application here
        pass

    def get_title(self) -> str:
        """Get widget title."""
        return "Settings"

    def get_icon(self) -> Optional[QIcon]:
        """Get widget icon."""
        return None

    def can_close(self) -> bool:
        """Check if widget can be closed."""
        if self._modified_settings:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved settings. Do you want to save them?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            )

            if reply == QMessageBox.Save:
                return self._apply_settings()
            elif reply == QMessageBox.Cancel:
                return False

        return True

    def _setup_ui(self):
        """Set up the settings UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Tab widget for different setting categories
        self._tabs = QTabWidget()

        # Track which tabs have been loaded
        self._loaded_tabs = set()
        self._tab_creators = {}
        self._tab_placeholders = {}

        # Add tab placeholders with deferred content creation
        # Only create the General tab immediately (it's lightweight)
        general_tab = self._create_general_tab()
        self._tabs.addTab(general_tab, "General")
        self._loaded_tabs.add(0)

        # Add placeholders for heavy tabs
        for idx, (name, creator) in enumerate(
            [
                ("Appearance", self._create_appearance_tab),
                ("Keyboard", self._create_keyboard_tab),  # Heavy - loads all commands
                ("Terminal", self._create_terminal_tab),
                ("Advanced", self._create_advanced_tab),
            ],
            start=1,
        ):
            placeholder = self._create_loading_placeholder(f"Loading {name} settings...")
            self._tabs.addTab(placeholder, name)
            self._tab_creators[idx] = creator
            self._tab_placeholders[idx] = placeholder

        # Connect tab change signal for lazy loading
        self._tabs.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self._tabs)

        # Bottom button bar
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(8, 8, 8, 8)

        self._apply_button = QPushButton("Apply")
        self._apply_button.clicked.connect(self._apply_settings)
        self._apply_button.setEnabled(False)
        button_layout.addWidget(self._apply_button)

        self._save_button = QPushButton("Save")
        self._save_button.clicked.connect(self._save_settings)
        self._save_button.setEnabled(False)
        button_layout.addWidget(self._save_button)

        button_layout.addStretch()

        self._reset_button = QPushButton("Reset")
        self._reset_button.clicked.connect(self._reset_settings)
        button_layout.addWidget(self._reset_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _create_loading_placeholder(self, message: str = "Loading...") -> QWidget:
        """Create a loading placeholder widget."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Loading message
        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("QLabel { color: #888; font-size: 14px; }")
        layout.addWidget(label)

        # Progress bar (indeterminate)
        progress = QProgressBar()
        progress.setRange(0, 0)  # Indeterminate
        progress.setMaximumWidth(200)
        layout.addWidget(progress)

        widget.setLayout(layout)
        return widget

    def _on_tab_changed(self, index: int):
        """Handle tab change and load content if needed."""
        if index in self._loaded_tabs:
            return  # Already loaded

        if index not in self._tab_creators:
            return  # No creator for this tab (shouldn't happen)

        # Load the tab content asynchronously using QTimer
        QTimer.singleShot(0, lambda: self._load_tab_content(index))

    def _load_tab_content(self, index: int):
        """Load the actual content for a tab."""
        try:
            # Create the actual tab content
            creator = self._tab_creators.get(index)
            if not creator:
                return

            # Create the widget
            actual_widget = creator()

            # Replace the placeholder with the actual widget
            # Get the tab text BEFORE removing the tab
            tab_text = self._tabs.tabText(index)
            self._tabs.removeTab(index)
            self._tabs.insertTab(index, actual_widget, tab_text)
            self._tabs.setCurrentIndex(index)

            # Mark as loaded
            self._loaded_tabs.add(index)

            # Clean up
            if index in self._tab_placeholders:
                placeholder = self._tab_placeholders[index]
                placeholder.deleteLater()
                del self._tab_placeholders[index]

            # Load settings for this tab if needed
            self._load_tab_settings(index)

        except Exception as e:
            logger.error(f"Failed to load tab {index}: {e}")
            # Show error in the tab
            error_widget = QLabel(f"Failed to load settings: {str(e)}")
            error_widget.setAlignment(Qt.AlignCenter)
            self._tabs.removeTab(index)
            self._tabs.insertTab(index, error_widget, self._tabs.tabText(index))

    def _load_tab_settings(self, index: int):
        """Load settings for a specific tab after it's created."""
        # This will be called after each tab is loaded
        # We'll move the relevant parts of _load_current_settings here
        pass

    def _create_general_tab(self) -> QWidget:
        """Create the general settings tab."""
        container = QWidget()
        container.setObjectName("settingsTabContent")
        layout = QVBoxLayout()

        # Scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setObjectName("settingsScrollArea")

        scroll_content = QWidget()
        scroll_content.setObjectName("settingsScrollContent")
        content_layout = QVBoxLayout()

        # Workspace Defaults group
        workspace_group = QGroupBox("Workspace Defaults")
        workspace_layout = QVBoxLayout()

        # Default new tab widget
        tab_widget_layout = QHBoxLayout()
        tab_widget_layout.addWidget(QLabel("Default new tab:"))
        self._default_tab_combo = QComboBox()
        self._default_tab_combo.addItems(["Terminal", "Editor", "Theme Editor", "Explorer"])
        # Dynamically populate widget options from registry - NO HARDCODING
        from viloapp.core.app_widget_manager import app_widget_manager
        available_widgets = app_widget_manager.get_available_widgets()

        # Clear and repopulate combo with actual available widgets
        self._default_tab_combo.clear()
        for widget in available_widgets[:5]:  # Show up to 5 options
            self._default_tab_combo.addItem(widget.display_name, widget.widget_id)
        self._default_tab_combo.setItemData(3, "explorer")
        self._default_tab_combo.currentIndexChanged.connect(
            lambda: self._on_setting_changed(
                "workspace.default_new_tab_widget",
                self._default_tab_combo.currentData(),
            )
        )
        tab_widget_layout.addWidget(self._default_tab_combo)
        tab_widget_layout.addStretch()
        workspace_layout.addLayout(tab_widget_layout)

        # Tab naming pattern
        naming_layout = QHBoxLayout()
        naming_layout.addWidget(QLabel("Tab naming pattern:"))
        self._tab_naming_input = QLineEdit()
        self._tab_naming_input.setPlaceholderText("{type} {index}")
        self._tab_naming_input.textChanged.connect(
            lambda text: self._on_setting_changed("workspace.tab_auto_naming_pattern", text)
        )
        naming_layout.addWidget(self._tab_naming_input)
        workspace_layout.addLayout(naming_layout)

        # Max tabs
        max_tabs_layout = QHBoxLayout()
        max_tabs_layout.addWidget(QLabel("Maximum tabs:"))
        self._max_tabs_spin = QSpinBox()
        self._max_tabs_spin.setRange(0, 100)
        self._max_tabs_spin.setSpecialValueText("Unlimited")
        self._max_tabs_spin.valueChanged.connect(
            lambda value: self._on_setting_changed("workspace.max_tabs", value)
        )
        max_tabs_layout.addWidget(self._max_tabs_spin)
        max_tabs_layout.addWidget(QLabel("(0 = unlimited)"))
        max_tabs_layout.addStretch()
        workspace_layout.addLayout(max_tabs_layout)

        # Close last tab behavior
        close_tab_layout = QVBoxLayout()
        close_tab_layout.addWidget(QLabel("When closing last tab:"))
        self._close_tab_group = QButtonGroup()
        self._create_default_radio = QRadioButton("Create default tab")
        self._create_default_radio.toggled.connect(
            lambda checked: (
                self._on_setting_changed("workspace.close_last_tab_behavior", "create_default")
                if checked
                else None
            )
        )
        self._close_window_radio = QRadioButton("Close window")
        self._close_window_radio.toggled.connect(
            lambda checked: (
                self._on_setting_changed("workspace.close_last_tab_behavior", "close_window")
                if checked
                else None
            )
        )
        self._do_nothing_radio = QRadioButton("Do nothing")
        self._do_nothing_radio.toggled.connect(
            lambda checked: (
                self._on_setting_changed("workspace.close_last_tab_behavior", "do_nothing")
                if checked
                else None
            )
        )
        self._close_tab_group.addButton(self._create_default_radio)
        self._close_tab_group.addButton(self._close_window_radio)
        self._close_tab_group.addButton(self._do_nothing_radio)
        close_tab_layout.addWidget(self._create_default_radio)
        close_tab_layout.addWidget(self._close_window_radio)
        close_tab_layout.addWidget(self._do_nothing_radio)
        workspace_layout.addLayout(close_tab_layout)

        # Restore tabs on startup
        self._restore_tabs_check = QCheckBox("Restore tabs from last session")
        self._restore_tabs_check.stateChanged.connect(
            lambda state: self._on_setting_changed(
                "workspace.restore_tabs_on_startup", state == Qt.Checked
            )
        )
        workspace_layout.addWidget(self._restore_tabs_check)

        workspace_group.setLayout(workspace_layout)
        content_layout.addWidget(workspace_group)

        # Pane Management group
        pane_group = QGroupBox("Pane Management")
        pane_layout = QVBoxLayout()

        # Default split direction
        split_dir_layout = QHBoxLayout()
        split_dir_layout.addWidget(QLabel("Default split:"))
        self._split_dir_group = QButtonGroup()
        self._horizontal_radio = QRadioButton("Horizontal")
        self._horizontal_radio.toggled.connect(
            lambda checked: (
                self._on_setting_changed("pane.default_split_direction", "horizontal")
                if checked
                else None
            )
        )
        self._vertical_radio = QRadioButton("Vertical")
        self._vertical_radio.toggled.connect(
            lambda checked: (
                self._on_setting_changed("pane.default_split_direction", "vertical")
                if checked
                else None
            )
        )
        self._split_dir_group.addButton(self._horizontal_radio)
        self._split_dir_group.addButton(self._vertical_radio)
        split_dir_layout.addWidget(self._horizontal_radio)
        split_dir_layout.addWidget(self._vertical_radio)
        split_dir_layout.addStretch()
        pane_layout.addLayout(split_dir_layout)

        # Split ratio
        ratio_layout = QHBoxLayout()
        ratio_layout.addWidget(QLabel("Split ratio:"))
        self._split_ratio_slider = QSlider(Qt.Horizontal)
        self._split_ratio_slider.setRange(10, 90)
        self._split_ratio_slider.setValue(50)
        self._split_ratio_slider.setTickPosition(QSlider.TicksBelow)
        self._split_ratio_slider.setTickInterval(10)
        self._split_ratio_slider.valueChanged.connect(self._on_split_ratio_changed)
        ratio_layout.addWidget(self._split_ratio_slider)
        self._split_ratio_label = QLabel("50%")
        ratio_layout.addWidget(self._split_ratio_label)
        pane_layout.addLayout(ratio_layout)

        # Focus new pane
        self._focus_new_pane_check = QCheckBox("Focus new pane after split")
        self._focus_new_pane_check.stateChanged.connect(
            lambda state: self._on_setting_changed("pane.focus_new_on_split", state == Qt.Checked)
        )
        pane_layout.addWidget(self._focus_new_pane_check)

        pane_group.setLayout(pane_layout)
        content_layout.addWidget(pane_group)

        # Startup group
        startup_group = QGroupBox("Startup")
        startup_layout = QVBoxLayout()

        # Window state
        window_layout = QVBoxLayout()
        window_layout.addWidget(QLabel("Window state:"))
        self._window_state_group = QButtonGroup()
        self._normal_radio = QRadioButton("Normal")
        self._maximized_radio = QRadioButton("Maximized")
        self._fullscreen_radio = QRadioButton("Fullscreen")
        self._window_state_group.addButton(self._normal_radio)
        self._window_state_group.addButton(self._maximized_radio)
        self._window_state_group.addButton(self._fullscreen_radio)
        window_layout.addWidget(self._normal_radio)
        window_layout.addWidget(self._maximized_radio)
        window_layout.addWidget(self._fullscreen_radio)
        startup_layout.addLayout(window_layout)

        startup_group.setLayout(startup_layout)
        content_layout.addWidget(startup_group)

        content_layout.addStretch()
        scroll_content.setLayout(content_layout)
        scroll.setWidget(scroll_content)

        layout.addWidget(scroll)
        container.setLayout(layout)
        return container

    def _create_appearance_tab(self) -> QWidget:
        """Create the appearance settings tab."""
        logger.debug("Creating appearance tab with theme editor")

        # Theme editor functionality moved to plugin system
        # Create placeholder for theme settings
        theme_placeholder = QLabel("Theme editing is now provided by plugins.\n\nInstall a theme editor plugin to customize themes.")
        theme_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        theme_placeholder.setStyleSheet("color: #888; font-style: italic; padding: 40px;")
        self._theme_editor = theme_placeholder
        # No signal to connect for placeholder

        logger.debug(f"Theme editor created: {self._theme_editor}")

        return self._theme_editor

    def _create_keyboard_tab(self) -> QWidget:
        """Create the keyboard settings tab."""
        # For now, embed the existing Keyboard Shortcuts widget
        return ShortcutConfigAppWidget(widget_id=f"{self.widget_id}_shortcuts", parent=self)

    def _create_terminal_tab(self) -> QWidget:
        """Create the terminal settings tab."""
        container = QWidget()
        container.setObjectName("settingsTabContent")
        layout = QVBoxLayout()

        # Terminal Settings group
        terminal_group = QGroupBox("Terminal Settings")
        terminal_layout = QVBoxLayout()

        # Default shell
        shell_layout = QHBoxLayout()
        shell_layout.addWidget(QLabel("Default shell:"))
        self._shell_combo = QComboBox()
        self._shell_combo.addItems(["Auto", "Bash", "Zsh", "Fish", "PowerShell", "CMD"])
        self._shell_combo.setItemData(0, "auto")
        self._shell_combo.setItemData(1, "bash")
        self._shell_combo.setItemData(2, "zsh")
        self._shell_combo.setItemData(3, "fish")
        self._shell_combo.setItemData(4, "powershell")
        self._shell_combo.setItemData(5, "cmd")
        self._shell_combo.currentIndexChanged.connect(
            lambda: self._on_setting_changed(
                "terminal.default_shell", self._shell_combo.currentData()
            )
        )
        shell_layout.addWidget(self._shell_combo)
        shell_layout.addStretch()
        terminal_layout.addLayout(shell_layout)

        # Starting directory
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Starting directory:"))
        self._start_dir_combo = QComboBox()
        self._start_dir_combo.addItems(["Home", "Project Root", "Last Used"])
        self._start_dir_combo.setItemData(0, "home")
        self._start_dir_combo.setItemData(1, "project")
        self._start_dir_combo.setItemData(2, "last_used")
        self._start_dir_combo.currentIndexChanged.connect(
            lambda: self._on_setting_changed(
                "terminal.starting_directory", self._start_dir_combo.currentData()
            )
        )
        dir_layout.addWidget(self._start_dir_combo)
        dir_layout.addStretch()
        terminal_layout.addLayout(dir_layout)

        terminal_group.setLayout(terminal_layout)
        layout.addWidget(terminal_group)

        layout.addStretch()
        container.setLayout(layout)
        return container

    def _create_advanced_tab(self) -> QWidget:
        """Create the advanced settings tab."""
        container = QWidget()
        container.setObjectName("settingsTabContent")
        layout = QVBoxLayout()

        # Confirmations group
        confirm_group = QGroupBox("Confirmations")
        confirm_layout = QVBoxLayout()

        self._confirm_exit_check = QCheckBox("Confirm before exiting application")
        self._confirm_exit_check.stateChanged.connect(
            lambda state: self._on_setting_changed("ux.confirm_app_exit", state == Qt.Checked)
        )
        confirm_layout.addWidget(self._confirm_exit_check)

        self._confirm_reload_check = QCheckBox("Confirm before reloading window")
        self._confirm_reload_check.stateChanged.connect(
            lambda state: self._on_setting_changed("ux.confirm_reload_window", state == Qt.Checked)
        )
        confirm_layout.addWidget(self._confirm_reload_check)

        confirm_group.setLayout(confirm_layout)
        layout.addWidget(confirm_group)

        # Actions group
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()

        # Reset all button
        reset_all_button = QPushButton("Reset All to Defaults")
        reset_all_button.clicked.connect(self._reset_all_to_defaults)
        actions_layout.addWidget(reset_all_button)

        # Export/Import
        export_import_layout = QHBoxLayout()
        export_button = QPushButton("Export Settings...")
        export_button.clicked.connect(self._export_settings)
        export_import_layout.addWidget(export_button)

        import_button = QPushButton("Import Settings...")
        import_button.clicked.connect(self._import_settings)
        export_import_layout.addWidget(import_button)

        actions_layout.addLayout(export_import_layout)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        layout.addStretch()
        container.setLayout(layout)
        return container

    def _on_setting_changed(self, key: str, value: Any):
        """Handle setting change."""
        self._modified_settings[key] = value
        self._update_button_states()
        self.settings_changed.emit(key, value)

    def _on_theme_modified(self, is_modified: bool):
        """Handle theme modification signal."""
        # Theme editing now handled by plugins
        pass

    def _on_split_ratio_changed(self, value: int):
        """Handle split ratio slider change."""
        ratio = value / 100.0
        self._split_ratio_label.setText(f"{value}%")
        self._on_setting_changed("pane.default_split_ratio", ratio)

    def _update_button_states(self):
        """Update button enabled states."""
        # Check for regular setting changes
        has_changes = bool(self._modified_settings)

        # Also check if theme editor has unsaved changes
        if hasattr(self, "_theme_editor") and self._theme_editor:
            # Theme editor is now a placeholder - no changes to track
            pass

        self._apply_button.setEnabled(has_changes)
        self._save_button.setEnabled(has_changes)

    def _load_current_settings(self):  # noqa: C901
        """Load current settings into UI."""
        # Only load settings for tabs that have been created
        # General tab (always created)
        if hasattr(self, "_default_tab_combo"):
            widget_id = get_app_default("workspace.default_new_tab_widget", "terminal")
            index = self._default_tab_combo.findData(widget_id)
            if index >= 0:
                self._default_tab_combo.setCurrentIndex(index)

        if hasattr(self, "_tab_naming_input"):
            self._tab_naming_input.setText(
                get_app_default("workspace.tab_auto_naming_pattern", "{type} {index}")
            )

        if hasattr(self, "_max_tabs_spin"):
            self._max_tabs_spin.setValue(get_app_default("workspace.max_tabs", 20))

        if hasattr(self, "_create_default_radio"):
            close_behavior = get_app_default("workspace.close_last_tab_behavior", "create_default")
            if close_behavior == "create_default":
                self._create_default_radio.setChecked(True)
            elif close_behavior == "close_window":
                self._close_window_radio.setChecked(True)
            else:
                self._do_nothing_radio.setChecked(True)

        if hasattr(self, "_restore_tabs_check"):
            self._restore_tabs_check.setChecked(
                get_app_default("workspace.restore_tabs_on_startup", True)
            )

        # Pane settings
        if hasattr(self, "_horizontal_radio"):
            split_dir = get_app_default("pane.default_split_direction", "horizontal")
            if split_dir == "horizontal":
                self._horizontal_radio.setChecked(True)
            else:
                self._vertical_radio.setChecked(True)

        if hasattr(self, "_split_ratio_slider"):
            split_ratio = int(get_app_default("pane.default_split_ratio", 0.5) * 100)
            self._split_ratio_slider.setValue(split_ratio)
            self._split_ratio_label.setText(f"{split_ratio}%")

        if hasattr(self, "_focus_new_pane_check"):
            self._focus_new_pane_check.setChecked(get_app_default("pane.focus_new_on_split", True))

        # Terminal settings - only load if terminal tab has been created
        if hasattr(self, "_shell_combo"):
            shell = get_app_default("terminal.default_shell", "auto")
            index = self._shell_combo.findData(shell)
            if index >= 0:
                self._shell_combo.setCurrentIndex(index)

        if hasattr(self, "_start_dir_combo"):
            start_dir = get_app_default("terminal.starting_directory", "home")
            index = self._start_dir_combo.findData(start_dir)
            if index >= 0:
                self._start_dir_combo.setCurrentIndex(index)

        # Advanced settings - only load if advanced tab has been created
        if hasattr(self, "_confirm_exit_check"):
            self._confirm_exit_check.setChecked(get_app_default("ux.confirm_app_exit", True))
        if hasattr(self, "_confirm_reload_check"):
            self._confirm_reload_check.setChecked(get_app_default("ux.confirm_reload_window", True))

        # Clear modified settings after loading
        self._modified_settings.clear()
        self._update_button_states()

    def _apply_settings(self) -> bool:
        """Apply modified settings."""
        try:
            # Apply regular settings
            for key, value in self._modified_settings.items():
                if not set_app_default(key, value):
                    logger.warning(f"Failed to apply setting {key}={value}")

            # Apply theme editor changes if present
            if hasattr(self, "_theme_editor") and self._theme_editor:
                # Theme changes now handled by plugins
                if False:  # Placeholder condition
                        logger.warning("Failed to apply theme changes")

            self._modified_settings.clear()
            self._update_button_states()

            QMessageBox.information(self, "Success", "Settings applied successfully!")
            return True

        except Exception as e:
            logger.error(f"Failed to apply settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply settings: {e}")
            return False

    def _save_settings(self) -> bool:
        """Save settings permanently."""
        success = True

        # Save regular settings
        if self._modified_settings:
            if not self._apply_settings():
                success = False

        # Save theme editor changes if present
        if hasattr(self, "_theme_editor") and self._theme_editor:
            # Theme saving now handled by plugins
            if False:  # Placeholder condition
                    success = False

        if success:
            QMessageBox.information(self, "Success", "Settings saved successfully!")

        return success

    def _reset_settings(self):
        """Reset current tab settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Reset settings in current tab to defaults?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # Check which tab is currently active
            current_tab = self._tabs.currentIndex()

            # If on Appearance tab and theme editor exists, reset theme
            if current_tab == 1 and hasattr(self, "_theme_editor") and self._theme_editor:
                # Theme reset now handled by plugins
                pass
            else:
                # Reset regular settings
                self._load_current_settings()

    def _reset_all_to_defaults(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset All Settings",
            "This will reset ALL settings to their default values. Continue?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self._defaults_manager.reset_all()
            self._load_current_settings()
            QMessageBox.information(self, "Success", "All settings reset to defaults!")

    def _export_settings(self):
        """Export settings to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Settings", "settings.json", "JSON Files (*.json)"
        )

        if file_path:
            try:
                settings = self._defaults_manager.export_settings()
                with open(file_path, "w") as f:
                    json.dump(settings, f, indent=2)
                QMessageBox.information(self, "Success", "Settings exported successfully!")
            except Exception as e:
                logger.error(f"Failed to export settings: {e}")
                QMessageBox.critical(self, "Error", f"Failed to export settings: {e}")

    def _import_settings(self):
        """Import settings from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Settings", "", "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path) as f:
                    settings = json.load(f)

                imported = self._defaults_manager.import_settings(settings)
                self._load_current_settings()

                QMessageBox.information(
                    self, "Success", f"Imported {imported} settings successfully!"
                )
            except Exception as e:
                logger.error(f"Failed to import settings: {e}")
                QMessageBox.critical(self, "Error", f"Failed to import settings: {e}")

    # === Capability Implementation ===

    def get_capabilities(self) -> Set[WidgetCapability]:
        """
        Settings widget capabilities.

        Returns:
            Set of supported capabilities
        """
        return {
            WidgetCapability.SETTINGS_MANAGEMENT,
            WidgetCapability.CONFIGURATION_EDITING,
            WidgetCapability.PREFERENCES_HANDLING,
            WidgetCapability.STATE_PERSISTENCE,
            WidgetCapability.FOCUS_MANAGEMENT,
        }

    def execute_capability(
        self,
        capability: WidgetCapability,
        **kwargs: Any
    ) -> Any:
        """
        Execute capability-based actions.

        Args:
            capability: The capability to execute
            **kwargs: Capability-specific arguments

        Returns:
            Capability-specific return value
        """
        if capability == WidgetCapability.SETTINGS_MANAGEMENT:
            action = kwargs.get('action', 'get')
            if action == 'apply':
                # Apply pending changes
                self._apply_settings()
                return True
            elif action == 'save':
                # Save settings
                self._save_settings()
                return True
            elif action == 'reset':
                # Reset to defaults
                self._reset_settings()
                return True
        elif capability == WidgetCapability.STATE_PERSISTENCE:
            action = kwargs.get('action', 'save')
            if action == 'export':
                self._export_settings()
                return True
            elif action == 'import':
                self._import_settings()
                return True
        elif capability == WidgetCapability.FOCUS_MANAGEMENT:
            if kwargs.get('action') == 'focus':
                self.setFocus()
                return True
            return self.hasFocus()
        else:
            # Delegate to base class for unsupported capabilities
            return super().execute_capability(capability, **kwargs)
