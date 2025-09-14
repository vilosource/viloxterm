#!/usr/bin/env python3
"""
Comprehensive settings widget for managing application defaults.

This AppWidget provides a tabbed interface for configuring all application
settings including workspace defaults, appearance, keyboard shortcuts, and more.
"""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QGroupBox, QLabel, QComboBox, QSpinBox, QCheckBox,
    QSlider, QRadioButton, QButtonGroup, QPushButton,
    QLineEdit, QScrollArea, QFrame, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
import json
import logging

from ui.widgets.app_widget import AppWidget
from ui.widgets.widget_registry import WidgetType
from ui.widgets.theme_editor_widget import ThemeEditorAppWidget
from ui.widgets.shortcut_config_app_widget import ShortcutConfigAppWidget
from core.settings.app_defaults import (
    get_app_defaults,
    get_app_default,
    set_app_default,
    AppDefaultsValidator
)
from services.service_locator import ServiceLocator

logger = logging.getLogger(__name__)


class SettingsAppWidget(AppWidget):
    """
    Comprehensive settings management widget.

    Provides a tabbed interface for configuring all application settings
    with validation, import/export, and reset capabilities.
    """

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

        super().__init__(widget_id, WidgetType.SETTINGS, parent)

        self._defaults_manager = get_app_defaults()
        self._modified_settings = {}
        self._setup_ui()
        self._load_current_settings()

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
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
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

        # Add setting tabs
        self._tabs.addTab(self._create_general_tab(), "General")
        self._tabs.addTab(self._create_appearance_tab(), "Appearance")
        self._tabs.addTab(self._create_keyboard_tab(), "Keyboard")
        self._tabs.addTab(self._create_terminal_tab(), "Terminal")
        self._tabs.addTab(self._create_advanced_tab(), "Advanced")

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

    def _create_general_tab(self) -> QWidget:
        """Create the general settings tab."""
        container = QWidget()
        layout = QVBoxLayout()

        # Scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        content_layout = QVBoxLayout()

        # Workspace Defaults group
        workspace_group = QGroupBox("Workspace Defaults")
        workspace_layout = QVBoxLayout()

        # Default new tab widget
        tab_widget_layout = QHBoxLayout()
        tab_widget_layout.addWidget(QLabel("Default new tab:"))
        self._default_tab_combo = QComboBox()
        self._default_tab_combo.addItems([
            "Terminal", "Editor", "Theme Editor", "Explorer"
        ])
        self._default_tab_combo.setItemData(0, "terminal")
        self._default_tab_combo.setItemData(1, "editor")
        self._default_tab_combo.setItemData(2, "theme_editor")
        self._default_tab_combo.setItemData(3, "explorer")
        self._default_tab_combo.currentIndexChanged.connect(
            lambda: self._on_setting_changed("workspace.default_new_tab_widget",
                                            self._default_tab_combo.currentData())
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
            lambda checked: self._on_setting_changed("workspace.close_last_tab_behavior",
                                                    "create_default") if checked else None
        )
        self._close_window_radio = QRadioButton("Close window")
        self._close_window_radio.toggled.connect(
            lambda checked: self._on_setting_changed("workspace.close_last_tab_behavior",
                                                    "close_window") if checked else None
        )
        self._do_nothing_radio = QRadioButton("Do nothing")
        self._do_nothing_radio.toggled.connect(
            lambda checked: self._on_setting_changed("workspace.close_last_tab_behavior",
                                                    "do_nothing") if checked else None
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
            lambda state: self._on_setting_changed("workspace.restore_tabs_on_startup",
                                                  state == Qt.Checked)
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
            lambda checked: self._on_setting_changed("pane.default_split_direction",
                                                    "horizontal") if checked else None
        )
        self._vertical_radio = QRadioButton("Vertical")
        self._vertical_radio.toggled.connect(
            lambda checked: self._on_setting_changed("pane.default_split_direction",
                                                    "vertical") if checked else None
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
            lambda state: self._on_setting_changed("pane.focus_new_on_split",
                                                  state == Qt.Checked)
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
        # For now, embed the existing Theme Editor
        return ThemeEditorAppWidget(parent=self)

    def _create_keyboard_tab(self) -> QWidget:
        """Create the keyboard settings tab."""
        # For now, embed the existing Keyboard Shortcuts widget
        return ShortcutConfigAppWidget(parent=self)

    def _create_terminal_tab(self) -> QWidget:
        """Create the terminal settings tab."""
        container = QWidget()
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
            lambda: self._on_setting_changed("terminal.default_shell",
                                            self._shell_combo.currentData())
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
            lambda: self._on_setting_changed("terminal.starting_directory",
                                            self._start_dir_combo.currentData())
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
        layout = QVBoxLayout()

        # Confirmations group
        confirm_group = QGroupBox("Confirmations")
        confirm_layout = QVBoxLayout()

        self._confirm_exit_check = QCheckBox("Confirm before exiting application")
        self._confirm_exit_check.stateChanged.connect(
            lambda state: self._on_setting_changed("ux.confirm_app_exit",
                                                  state == Qt.Checked)
        )
        confirm_layout.addWidget(self._confirm_exit_check)

        self._confirm_reload_check = QCheckBox("Confirm before reloading window")
        self._confirm_reload_check.stateChanged.connect(
            lambda state: self._on_setting_changed("ux.confirm_reload_window",
                                                  state == Qt.Checked)
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

    def _on_split_ratio_changed(self, value: int):
        """Handle split ratio slider change."""
        ratio = value / 100.0
        self._split_ratio_label.setText(f"{value}%")
        self._on_setting_changed("pane.default_split_ratio", ratio)

    def _update_button_states(self):
        """Update button enabled states."""
        has_changes = bool(self._modified_settings)
        self._apply_button.setEnabled(has_changes)
        self._save_button.setEnabled(has_changes)

    def _load_current_settings(self):
        """Load current settings into UI."""
        # General tab
        widget_type = get_app_default("workspace.default_new_tab_widget", "terminal")
        index = self._default_tab_combo.findData(widget_type)
        if index >= 0:
            self._default_tab_combo.setCurrentIndex(index)

        self._tab_naming_input.setText(
            get_app_default("workspace.tab_auto_naming_pattern", "{type} {index}")
        )

        self._max_tabs_spin.setValue(get_app_default("workspace.max_tabs", 20))

        close_behavior = get_app_default("workspace.close_last_tab_behavior", "create_default")
        if close_behavior == "create_default":
            self._create_default_radio.setChecked(True)
        elif close_behavior == "close_window":
            self._close_window_radio.setChecked(True)
        else:
            self._do_nothing_radio.setChecked(True)

        self._restore_tabs_check.setChecked(
            get_app_default("workspace.restore_tabs_on_startup", True)
        )

        # Pane settings
        split_dir = get_app_default("pane.default_split_direction", "horizontal")
        if split_dir == "horizontal":
            self._horizontal_radio.setChecked(True)
        else:
            self._vertical_radio.setChecked(True)

        split_ratio = int(get_app_default("pane.default_split_ratio", 0.5) * 100)
        self._split_ratio_slider.setValue(split_ratio)
        self._split_ratio_label.setText(f"{split_ratio}%")

        self._focus_new_pane_check.setChecked(
            get_app_default("pane.focus_new_on_split", True)
        )

        # Terminal settings
        shell = get_app_default("terminal.default_shell", "auto")
        index = self._shell_combo.findData(shell)
        if index >= 0:
            self._shell_combo.setCurrentIndex(index)

        start_dir = get_app_default("terminal.starting_directory", "home")
        index = self._start_dir_combo.findData(start_dir)
        if index >= 0:
            self._start_dir_combo.setCurrentIndex(index)

        # Advanced settings
        self._confirm_exit_check.setChecked(
            get_app_default("ux.confirm_app_exit", True)
        )
        self._confirm_reload_check.setChecked(
            get_app_default("ux.confirm_reload_window", True)
        )

        # Clear modified settings after loading
        self._modified_settings.clear()
        self._update_button_states()

    def _apply_settings(self) -> bool:
        """Apply modified settings."""
        try:
            for key, value in self._modified_settings.items():
                if not set_app_default(key, value):
                    logger.warning(f"Failed to apply setting {key}={value}")

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
        if self._apply_settings():
            # Settings are automatically persisted by QSettings
            return True
        return False

    def _reset_settings(self):
        """Reset current tab settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Reset settings in current tab to defaults?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._load_current_settings()

    def _reset_all_to_defaults(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset All Settings",
            "This will reset ALL settings to their default values. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._defaults_manager.reset_all()
            self._load_current_settings()
            QMessageBox.information(self, "Success", "All settings reset to defaults!")

    def _export_settings(self):
        """Export settings to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Settings",
            "settings.json",
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                settings = self._defaults_manager.export_settings()
                with open(file_path, 'w') as f:
                    json.dump(settings, f, indent=2)
                QMessageBox.information(self, "Success", "Settings exported successfully!")
            except Exception as e:
                logger.error(f"Failed to export settings: {e}")
                QMessageBox.critical(self, "Error", f"Failed to export settings: {e}")

    def _import_settings(self):
        """Import settings from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Settings",
            "",
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    settings = json.load(f)

                imported = self._defaults_manager.import_settings(settings)
                self._load_current_settings()

                QMessageBox.information(
                    self,
                    "Success",
                    f"Imported {imported} settings successfully!"
                )
            except Exception as e:
                logger.error(f"Failed to import settings: {e}")
                QMessageBox.critical(self, "Error", f"Failed to import settings: {e}")