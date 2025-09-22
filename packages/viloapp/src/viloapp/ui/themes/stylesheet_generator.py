#!/usr/bin/env python3
"""
Stylesheet generator for theme system.

This module generates Qt stylesheets dynamically based on the current theme.
"""

import logging
from typing import Callable

logger = logging.getLogger(__name__)


class StylesheetGenerator:
    """
    Generates Qt stylesheets from theme colors.

    Each component has its own generator method that creates
    appropriate stylesheets using the current theme colors.
    """

    def __init__(self, theme_service):
        """
        Initialize stylesheet generator.

        Args:
            theme_service: ThemeService instance
        """
        self._theme_service = theme_service

        # Map component names to generator methods
        self._generators: dict[str, Callable] = {
            "main_window": self._main_window_style,
            "editor": self._editor_style,
            "terminal": self._terminal_style,
            "sidebar": self._sidebar_style,
            "activity_bar": self._activity_bar_style,
            "status_bar": self._status_bar_style,
            "tab_widget": self._tab_widget_style,
            "menu": self._menu_style,
            "splitter": self._splitter_style,
            "settings_widget": self._settings_widget_style,
            "pane_header": self._pane_header_style,
            "command_palette": self._command_palette_style,
        }

    def generate(self, component: str) -> str:
        """
        Generate stylesheet for a component.

        Args:
            component: Component name

        Returns:
            Stylesheet string
        """
        generator = self._generators.get(component, self._default_style)
        try:
            return generator()
        except Exception as e:
            logger.error(f"Failed to generate stylesheet for {component}: {e}")
            return self._default_style()

    def _get_color(self, key: str, fallback: str = "#000000") -> str:
        """Helper to get color from theme service."""
        return self._theme_service.get_color(key, fallback)

    def _get_font_size(self, scale: str = "base") -> int:
        """Helper to get font size from theme service."""
        return self._theme_service.get_font_size(scale)

    def _get_font_family(self) -> str:
        """Helper to get font family from theme service."""
        return self._theme_service.get_font_family()

    def _get_component_typography(self, component: str) -> dict:
        """Helper to get component-specific typography."""
        return self._theme_service.get_component_typography(component)

    def _main_window_style(self) -> str:
        """Generate main window stylesheet."""
        from viloapp.core.app_config import app_config

        # Check if in dev mode for special styling
        dev_mode = app_config.dev_mode
        menu_bar_bg = "#8B0000" if dev_mode else self._get_color("titleBar.activeBackground")
        menu_bar_fg = "#FFFFFF" if dev_mode else self._get_color("titleBar.activeForeground")
        menu_bar_hover = "#A52A2A" if dev_mode else self._get_color("button.secondaryBackground")

        return f"""
            QMainWindow {{
                background-color: {self._get_color("editor.background")};
            }}
            QToolBar {{
                background-color: {self._get_color("titleBar.activeBackground")};
                border: none;
                spacing: 5px;
                padding: 5px;
            }}
            QToolBar QToolButton {{
                background-color: transparent;
                color: {self._get_color("titleBar.activeForeground")};
                border: none;
                padding: 5px;
                margin: 2px;
            }}
            QToolBar QToolButton:hover {{
                background-color: {self._get_color("button.secondaryBackground")};
            }}
            QToolBar QToolButton:pressed {{
                background-color: {self._get_color("button.background")};
            }}
            QMenuBar {{
                background-color: {menu_bar_bg};
                color: {menu_bar_fg};
                border: none;
            }}
            QMenuBar::item {{
                padding: 4px 8px;
                background-color: transparent;
            }}
            QMenuBar::item:selected {{
                background-color: {menu_bar_hover};
            }}
            QMenuBar::item:pressed {{
                background-color: {self._get_color("menu.background")};
            }}
        """

    def _editor_style(self) -> str:
        """Generate editor stylesheet."""
        # Get typography settings for editor component
        typography = self._get_component_typography("editor")
        font_family = typography.get("font-family", self._get_font_family())
        font_size = typography.get("font-size", f"{self._get_font_size('base')}px")

        return f"""
            QPlainTextEdit, QTextEdit {{
                background-color: {self._get_color("editor.background")};
                color: {self._get_color("editor.foreground")};
                border: none;
                font-family: {font_family};
                font-size: {font_size};
                selection-background-color: {self._get_color("editor.selectionBackground")};
                selection-color: {self._get_color("editor.foreground")};
            }}
        """

    def _terminal_style(self) -> str:
        """Generate terminal stylesheet."""
        # Get typography settings for terminal component
        typography = self._get_component_typography("terminal")
        font_family = typography.get("font-family", self._get_font_family())
        font_size = typography.get("font-size", f"{self._get_font_size('base')}px")

        return f"""
            QTextEdit {{
                background-color: {self._get_color("terminal.background")};
                color: {self._get_color("terminal.foreground")};
                border: none;
                font-family: {font_family};
                font-size: {font_size};
                selection-background-color: {self._get_color("terminal.selectionBackground")};
            }}
        """

    def _sidebar_style(self) -> str:
        """Generate sidebar stylesheet."""
        # Use slightly smaller font for sidebar
        font_size = self._get_font_size("sm")

        return f"""
            QWidget#sidebar {{
                background-color: {self._get_color("sideBar.background")};
                border-right: 1px solid {self._get_color("sideBar.border")};
            }}
            QTreeWidget {{
                background-color: {self._get_color("sideBar.background")};
                color: {self._get_color("sideBar.foreground")};
                border: none;
                outline: none;
                font-size: {font_size}px;
            }}
            QTreeWidget::item {{
                padding: 4px;
            }}
            QTreeWidget::item:hover {{
                background-color: {self._get_color("list.hoverBackground")};
            }}
            QTreeWidget::item:selected {{
                background-color: {self._get_color("list.activeSelectionBackground")};
                color: {self._get_color("list.activeSelectionForeground")};
            }}
        """

    def _activity_bar_style(self) -> str:
        """Generate activity bar stylesheet."""
        return f"""
            QToolBar#activityBar {{
                background-color: {self._get_color("activityBar.background")};
                border: none;
                padding: 5px 0;
            }}
            QToolBar#activityBar QToolButton {{
                background-color: transparent;
                border: none;
                padding: 8px;
                margin: 2px 0;
            }}
            QToolBar#activityBar QToolButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QToolBar#activityBar QToolButton:checked {{
                background-color: rgba(255, 255, 255, 0.15);
                border-left: 2px solid {self._get_color("activityBar.activeBorder")};
            }}
            QToolBar#activityBar QToolButton:pressed {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
        """

    def _status_bar_style(self) -> str:
        """Generate status bar stylesheet."""
        # Use extra small font for status bar
        font_size = self._get_font_size("xs")

        return f"""
            QStatusBar {{
                background-color: {self._get_color("statusBar.background")};
                color: {self._get_color("statusBar.foreground")};
                border: none;
                padding: 2px 10px;
                font-size: {font_size}px;
            }}
            QStatusBar::item {{
                border: none;
            }}
        """

    def _tab_widget_style(self) -> str:
        """Generate tab widget stylesheet."""
        # Get font settings for tabs
        font_family = self._get_font_family()
        font_size = self._get_font_size("base")

        return f"""
            QTabWidget::pane {{
                background-color: {self._get_color("editor.background")};
                border: none;
            }}
            QTabWidget::tab-bar {{
                background-color: {self._get_color("tab.border")};
            }}
            QTabBar {{
                background-color: {self._get_color("tab.border")};
            }}
            QTabBar::tab {{
                background-color: {self._get_color("tab.inactiveBackground")};
                color: {self._get_color("tab.inactiveForeground")};
                padding: 2px 8px;
                border: none;
                border-right: 1px solid {self._get_color("tab.border")};
                min-width: 80px;
                margin: 0;
                font-family: {font_family};
                font-size: {font_size}px;
            }}
            QTabBar::tab:selected {{
                background-color: {self._get_color("tab.activeBackground")};
                color: {self._get_color("tab.activeForeground")};
                border-top: 1px solid {self._get_color("tab.activeBorderTop")};
                margin-top: 0;
                padding-top: 2px;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {self._get_color("list.hoverBackground")};
                color: {self._get_color("list.hoverForeground")};
            }}
            QTabBar::close-button {{
                width: 14px;
                height: 14px;
                background-color: transparent;
                border: none;
                border-radius: 2px;
                margin: 0px;
                padding: 0px;
            }}
            QTabBar::close-button:hover {{
                background-color: rgba(90, 93, 94, 0.8);
            }}
            QTabBar::close-button:pressed {{
                background-color: rgba(90, 93, 94, 1.0);
            }}
        """

    def _menu_style(self) -> str:
        """Generate menu stylesheet."""
        return f"""
            QMenu {{
                background-color: {self._get_color("menu.background")};
                color: {self._get_color("menu.foreground")};
                border: 1px solid {self._get_color("splitter.background")};
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 20px;
                border-radius: 3px;
            }}
            QMenu::item:selected {{
                background-color: {self._get_color("menu.selectionBackground")};
                color: {self._get_color("menu.selectionForeground")};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {self._get_color("menu.separatorBackground")};
                margin: 4px 0;
            }}
        """

    def _splitter_style(self) -> str:
        """Generate splitter stylesheet."""
        return f"""
            QSplitter {{
                background-color: {self._get_color("editor.background")};
            }}
            QSplitter::handle {{
                background-color: {self._get_color("splitter.background")};
            }}
            QSplitter::handle:horizontal {{
                width: 1px;
            }}
            QSplitter::handle:vertical {{
                height: 1px;
            }}
            QSplitter::handle:hover {{
                background-color: {self._get_color("splitter.hoverBackground")};
            }}
        """

    def _settings_widget_style(self) -> str:
        """Generate settings widget stylesheet."""
        # Use base font size for settings
        font_size = self._get_font_size("base")
        font_family = self._get_font_family()

        return f"""
            /* Main container */
            QWidget {{
                background-color: {self._get_color("editor.background")};
                color: {self._get_color("editor.foreground")};
            }}

            /* Specific settings tab content */
            QWidget#settingsTabContent {{
                background-color: {self._get_color("editor.background")};
                color: {self._get_color("editor.foreground")};
            }}

            QScrollArea#settingsScrollArea {{
                background-color: {self._get_color("editor.background")};
                border: none;
            }}

            QWidget#settingsScrollContent {{
                background-color: {self._get_color("editor.background")};
            }}

            /* Tree/Table widgets */
            QTreeWidget, QTableWidget {{
                background-color: {self._get_color("editor.background")};
                color: {self._get_color("editor.foreground")};
                border: 1px solid {self._get_color("panel.border")};
                outline: none;
                font-family: {font_family};
                font-size: {font_size}px;
                alternate-background-color: {self._get_color("editor.background")};
            }}

            QTreeWidget::item, QTableWidget::item {{
                padding: 6px;
                border: none;
                background-color: transparent;
            }}

            QTreeWidget::item:hover, QTableWidget::item:hover {{
                background-color: {self._get_color("list.hoverBackground")};
            }}

            QTreeWidget::item:selected, QTableWidget::item:selected {{
                background-color: {self._get_color("list.activeSelectionBackground")};
                color: {self._get_color("list.activeSelectionForeground")};
            }}

            /* Headers */
            QHeaderView::section {{
                background-color: {self._get_color("panel.background")};
                color: {self._get_color("editor.foreground")};
                border: none;
                border-bottom: 1px solid {self._get_color("panel.border")};
                padding: 8px;
                font-weight: 600;
            }}

            /* Line edits */
            QLineEdit {{
                background-color: {self._get_color("input.background")};
                color: {self._get_color("input.foreground")};
                border: 1px solid {self._get_color("input.border")};
                border-radius: 2px;
                padding: 4px 8px;
                font-family: {font_family};
                font-size: {font_size}px;
            }}

            QLineEdit:focus {{
                border-color: {self._get_color("focusBorder")};
                outline: none;
            }}

            /* Buttons */
            QPushButton {{
                background-color: {self._get_color("button.background")};
                color: {self._get_color("button.foreground")};
                border: 1px solid {self._get_color("button.border")};
                border-radius: 2px;
                padding: 6px 14px;
                font-family: {font_family};
                font-size: {font_size}px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background-color: {self._get_color("button.hoverBackground")};
            }}

            QPushButton:pressed {{
                background-color: {self._get_color("button.secondaryBackground")};
            }}

            /* Labels */
            QLabel {{
                color: {self._get_color("editor.foreground")};
                font-family: {font_family};
                font-size: {font_size}px;
            }}

            /* ComboBox */
            QComboBox {{
                background-color: {self._get_color("input.background")};
                color: {self._get_color("input.foreground")};
                border: 1px solid {self._get_color("input.border")};
                border-radius: 2px;
                padding: 4px 8px;
                font-family: {font_family};
                font-size: {font_size}px;
            }}

            QComboBox:focus {{
                border-color: {self._get_color("focusBorder")};
            }}

            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}

            QComboBox::down-arrow {{
                image: none;
                border-style: solid;
                border-width: 4px;
                border-color: transparent;
                border-top-color: {self._get_color("input.foreground")};
                margin-top: 4px;
            }}

            QComboBox QAbstractItemView {{
                background-color: {self._get_color("dropdown.background")};
                color: {self._get_color("dropdown.foreground")};
                border: 1px solid {self._get_color("input.border")};
                selection-background-color: {self._get_color("list.activeSelectionBackground")};
                selection-color: {self._get_color("list.activeSelectionForeground")};
            }}

            /* Group boxes */
            QGroupBox {{
                color: {self._get_color("editor.foreground")};
                border: 1px solid {self._get_color("panel.border")};
                border-radius: 4px;
                margin-top: 1ex;
                padding-top: 1ex;
                font-family: {font_family};
                font-size: {font_size}px;
            }}

            QGroupBox::title {{
                color: {self._get_color("editor.foreground")};
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                left: 10px;
            }}

            /* Scroll areas */
            QScrollArea {{
                background-color: {self._get_color("editor.background")};
                border: none;
            }}

            QScrollArea > QWidget > QWidget {{
                background-color: {self._get_color("editor.background")};
            }}

            /* CheckBoxes */
            QCheckBox {{
                color: {self._get_color("editor.foreground")};
                font-family: {font_family};
                font-size: {font_size}px;
            }}

            QCheckBox::indicator {{
                width: 13px;
                height: 13px;
                border: 1px solid {self._get_color("input.border")};
                background-color: {self._get_color("input.background")};
                border-radius: 2px;
            }}

            QCheckBox::indicator:checked {{
                background-color: {self._get_color("focusBorder")};
                border-color: {self._get_color("focusBorder")};
            }}

            /* RadioButtons */
            QRadioButton {{
                color: {self._get_color("editor.foreground")};
                font-family: {font_family};
                font-size: {font_size}px;
            }}

            QRadioButton::indicator {{
                width: 13px;
                height: 13px;
                border: 1px solid {self._get_color("input.border")};
                background-color: {self._get_color("input.background")};
                border-radius: 7px;
            }}

            QRadioButton::indicator:checked {{
                background-color: {self._get_color("focusBorder")};
                border-color: {self._get_color("focusBorder")};
            }}

            /* SpinBox */
            QSpinBox {{
                background-color: {self._get_color("input.background")};
                color: {self._get_color("input.foreground")};
                border: 1px solid {self._get_color("input.border")};
                border-radius: 2px;
                padding: 4px;
                font-family: {font_family};
                font-size: {font_size}px;
            }}

            QSpinBox:focus {{
                border-color: {self._get_color("focusBorder")};
            }}

            /* Slider */
            QSlider::groove:horizontal {{
                background-color: {self._get_color("input.background")};
                border: 1px solid {self._get_color("input.border")};
                height: 4px;
                border-radius: 2px;
            }}

            QSlider::handle:horizontal {{
                background-color: {self._get_color("button.background")};
                border: 1px solid {self._get_color("button.border")};
                width: 14px;
                height: 14px;
                border-radius: 7px;
                margin: -6px 0;
            }}

            QSlider::handle:horizontal:hover {{
                background-color: {self._get_color("button.hoverBackground")};
            }}

            /* Tab widget */
            QTabWidget::pane {{
                background-color: {self._get_color("editor.background")};
                border: 1px solid {self._get_color("panel.border")};
                border-top: none;
            }}

            QTabWidget::tab-bar {{
                alignment: left;
            }}

            QTabBar {{
                background-color: {self._get_color("editor.background")};
            }}

            QTabBar::tab {{
                background-color: {self._get_color("tab.inactiveBackground")};
                color: {self._get_color("tab.inactiveForeground")};
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid {self._get_color("panel.border")};
                border-bottom: none;
                font-family: {font_family};
                font-size: {font_size}px;
            }}

            QTabBar::tab:selected {{
                background-color: {self._get_color("editor.background")};
                color: {self._get_color("editor.foreground")};
                border-bottom: 1px solid {self._get_color("editor.background")};
            }}

            QTabBar::tab:hover:!selected {{
                background-color: {self._get_color("tab.hoverBackground")};
            }}

            /* Scroll bars */
            QScrollBar:vertical {{
                background-color: {self._get_color("editor.background")};
                width: 14px;
                border: none;
            }}

            QScrollBar::handle:vertical {{
                background-color: {self._get_color("scrollbarSlider.background")};
                border-radius: 7px;
                min-height: 20px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {self._get_color("scrollbarSlider.hoverBackground")};
            }}

            QScrollBar::handle:vertical:pressed {{
                background-color: {self._get_color("scrollbarSlider.activeBackground")};
            }}

            QScrollBar:horizontal {{
                background-color: {self._get_color("editor.background")};
                height: 14px;
                border: none;
            }}

            QScrollBar::handle:horizontal {{
                background-color: {self._get_color("scrollbarSlider.background")};
                border-radius: 7px;
                min-width: 20px;
            }}

            QScrollBar::handle:horizontal:hover {{
                background-color: {self._get_color("scrollbarSlider.hoverBackground")};
            }}

            QScrollBar::handle:horizontal:pressed {{
                background-color: {self._get_color("scrollbarSlider.activeBackground")};
            }}

            QScrollBar::add-line, QScrollBar::sub-line {{
                border: none;
                background: none;
            }}
        """

    def _pane_header_style(self) -> str:
        """Generate pane header stylesheet."""
        # Use extra small font for pane headers
        font_size_xs = self._get_font_size("xs")
        font_size_sm = self._get_font_size("sm")

        return f"""
            PaneHeaderBar {{
                background-color: {self._get_color("paneHeader.background")};
                border-bottom: 2px solid rgba(255, 255, 255, 0.1);
            }}
            PaneHeaderBar[active="true"] {{
                background-color: {self._get_color("paneHeader.activeBackground")};
                border-bottom: 2px solid rgba(255, 255, 255, 0.15);
            }}
            PaneHeaderBar QLabel {{
                color: {self._get_color("paneHeader.foreground")};
                font-size: {font_size_xs}px;
                padding: 0 4px;
            }}
            PaneHeaderBar[active="true"] QLabel {{
                color: {self._get_color("paneHeader.activeForeground")};
                font-weight: bold;
            }}
            PaneHeaderBar QToolButton {{
                background-color: transparent;
                color: {self._get_color("paneHeader.foreground")};
                border: none;
                padding: 2px;
                font-size: {font_size_sm}px;
            }}
            PaneHeaderBar QToolButton:hover {{
                background-color: {self._get_color("paneHeader.buttonHoverBackground")};
                border-radius: 2px;
            }}
            PaneHeaderBar QToolButton#closeButton:hover {{
                background-color: {self._get_color("paneHeader.closeButtonHoverBackground")};
                color: white;
            }}
        """

    def _command_palette_style(self) -> str:
        """Generate command palette stylesheet."""
        # Use base font size for command palette
        font_size = self._get_font_size("base")

        return f"""
            QDialog {{
                background-color: {self._get_color("dropdown.background")};
                border: 1px solid {self._get_color("dropdown.border")};
            }}
            QLineEdit {{
                background-color: {self._get_color("input.background")};
                color: {self._get_color("input.foreground")};
                border: 1px solid {self._get_color("input.border")};
                padding: 8px;
                font-size: {font_size}px;
            }}
            QListWidget {{
                background-color: {self._get_color("dropdown.background")};
                color: {self._get_color("dropdown.foreground")};
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px;
                border: none;
            }}
            QListWidget::item:hover {{
                background-color: {self._get_color("list.hoverBackground")};
            }}
            QListWidget::item:selected {{
                background-color: {self._get_color("list.activeSelectionBackground")};
                color: {self._get_color("list.activeSelectionForeground")};
            }}
        """

    def _default_style(self) -> str:
        """Generate default stylesheet as fallback."""
        return f"""
            QWidget {{
                background-color: {self._get_color("editor.background")};
                color: {self._get_color("editor.foreground")};
            }}
        """
