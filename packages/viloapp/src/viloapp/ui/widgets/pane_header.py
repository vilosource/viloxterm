#!/usr/bin/env python3
"""
Pane header bar component for split operations.
Provides a minimal, unobtrusive header with split/close controls.
"""

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QBrush, QColor, QPainter
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QSizePolicy,
    QToolButton,
    QWidget,
)

from viloapp.core.commands.executor import execute_command
from viloapp.ui.widgets.widget_registry import WidgetType, widget_registry

logger = logging.getLogger(__name__)


class PaneHeaderBar(QWidget):
    """
    Minimal header bar for pane operations.
    Appears at the top of each pane with split/close controls.
    """

    # Signals
    split_horizontal_requested = Signal()
    split_vertical_requested = Signal()
    close_requested = Signal()
    type_menu_requested = Signal()

    def __init__(self, pane_id: str = "", show_type_menu: bool = True, parent=None):
        super().__init__(parent)
        self.pane_id = pane_id
        self.show_type_menu = show_type_menu
        self.is_active = False
        self.background_color = QColor("#252526")  # Default dark background
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        """Initialize the header UI."""
        # Set fixed height for minimal footprint
        self.setFixedHeight(18)  # Ultra-minimal height to save screen space
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Don't use palette or stylesheet for background - we'll paint it ourselves
        self.setAttribute(Qt.WA_StyledBackground, False)

        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)  # Minimal margins
        layout.setSpacing(1)  # Minimal spacing

        # Pane number label (shows 1-9 when enabled)
        self.number_label = QLabel()
        self.number_label.setStyleSheet(
            """
            QLabel {
                background-color: #007ACC;
                color: white;
                border-radius: 2px;
                padding: 0px 4px;
                font-weight: bold;
                font-size: 10px;
                min-width: 12px;
                max-width: 12px;
            }
        """
        )
        self.number_label.setAlignment(Qt.AlignCenter)
        self.number_label.hide()  # Hidden by default
        layout.addWidget(self.number_label)

        # Pane ID label (optional, for debugging)
        self.id_label = QLabel(self.pane_id)
        self.id_label.setStyleSheet(
            """
            QLabel {
                color: #969696;
                font-size: 10px;
                padding: 0 2px;
            }
        """
        )
        layout.addWidget(self.id_label)

        # Stretch to push buttons to the right
        layout.addStretch()

        # Type menu button (optional)
        if self.show_type_menu:
            self.type_button = self.create_tool_button("≡", "Change widget type")
            self.type_button.clicked.connect(self.show_widget_type_menu)
            layout.addWidget(self.type_button)

        # Split horizontal button
        self.split_h_button = self.create_tool_button(
            "↔", "Split horizontal (new pane on right)"
        )
        self.split_h_button.clicked.connect(
            lambda: execute_command(
                "workbench.action.splitPaneHorizontal", pane=self.parent()
            )
        )
        layout.addWidget(self.split_h_button)

        # Split vertical button
        self.split_v_button = self.create_tool_button(
            "↕", "Split vertical (new pane below)"
        )
        self.split_v_button.clicked.connect(
            lambda: execute_command(
                "workbench.action.splitPaneVertical", pane=self.parent()
            )
        )
        layout.addWidget(self.split_v_button)

        # Close button
        self.close_button = self.create_tool_button("×", "Close this pane")
        self.close_button.clicked.connect(
            lambda: execute_command("workbench.action.closePane", pane=self.parent())
        )
        # Style will be applied by theme
        layout.addWidget(self.close_button)

    def create_tool_button(self, text: str, tooltip: str) -> QToolButton:
        """Create a styled tool button."""
        button = QToolButton()
        button.setText(text)
        button.setToolTip(tooltip)
        button.setFixedSize(16, 16)  # Smaller buttons

        # Style will be applied by theme

        return button

    def show_widget_type_menu(self):
        """Show menu with available widget types dynamically from AppWidgetManager."""
        menu = QMenu(self)

        # Apply theme to menu using commands
        theme_result = execute_command("theme.getCurrentColors")
        colors = theme_result.value if theme_result and theme_result.success else {}

        if colors:
            menu.setStyleSheet(
                f"""
                QMenu {{
                    background-color: {colors.get("menu.background", "#252526")};
                    color: {colors.get("menu.foreground", "#cccccc")};
                    border: 1px solid {colors.get("menu.border", "#454545")};
                    padding: 4px;
                }}
                QMenu::item {{
                    padding: 4px 20px;
                    border-radius: 2px;
                }}
                QMenu::item:selected {{
                    background-color: {colors.get("menu.selectionBackground", "#094771")};
                    color: {colors.get("menu.selectionForeground", "#ffffff")};
                }}
                QMenu::separator {{
                    height: 1px;
                    background-color: {colors.get("menu.separatorBackground", "#454545")};
                    margin: 4px 10px;
                }}
            """
            )

        # Try to use AppWidgetManager for dynamic menu generation
        try:
            from viloapp.core.app_widget_manager import AppWidgetManager
            from viloapp.core.app_widget_metadata import WidgetCategory

            manager = AppWidgetManager.get_instance()

            # Group widgets by category
            categories = {}
            for widget in manager.get_menu_widgets():
                category_name = widget.category.value
                if category_name not in categories:
                    categories[category_name] = []
                categories[category_name].append(widget)

            # Sort categories for consistent ordering
            category_order = [
                "editor",
                "terminal",
                "viewer",
                "tools",
                "development",
                "system",
                "plugin",
            ]
            sorted_categories = sorted(
                categories.items(),
                key=lambda x: (
                    category_order.index(x[0]) if x[0] in category_order else 999
                ),
            )

            # Add widgets by category
            for category_name, widgets in sorted_categories:
                if widgets:
                    # Format category name for display
                    display_name = category_name.replace("_", " ").title()
                    menu.addSection(display_name)

                    for widget_meta in widgets:
                        # Create action with icon and display name
                        icon_emoji = self._get_widget_icon(widget_meta.icon)
                        action_text = f"{icon_emoji} {widget_meta.display_name}"
                        action = QAction(action_text, self)
                        action.setToolTip(widget_meta.description)

                        # Always use replacement behavior in pane header context
                        action.triggered.connect(
                            lambda checked, wm=widget_meta: self._handle_widget_selection(
                                wm
                            )
                        )
                        menu.addAction(action)

        except ImportError:
            # Fallback to legacy hardcoded menu if AppWidgetManager not available
            self._show_legacy_widget_menu(menu)
        except Exception as e:
            logger.error(f"Failed to generate dynamic menu: {e}")
            self._show_legacy_widget_menu(menu)

        # Show the menu at the button position
        menu.exec_(self.type_button.mapToGlobal(self.type_button.rect().bottomLeft()))

    def _get_widget_icon(self, icon_name: str) -> str:
        """Get emoji icon for widget based on icon name."""
        icon_map = {
            "terminal": "💻",
            "file-text": "📝",
            "palette": "🎨",
            "keyboard": "⌨️",
            "folder": "📁",
            "message-square": "📤",
            "layout": "⬜",
            "search": "🔍",
            "git-branch": "🌿",
            "settings": "⚙️",
        }
        return icon_map.get(icon_name, "📦")

    def _show_legacy_widget_menu(self, menu):
        """Show legacy hardcoded widget menu as fallback."""
        # Group widget types by category
        editor_types = []
        terminal_types = []
        view_types = []
        special_types = []

        # Get available widget types from registry
        for widget_type in WidgetType:
            config = widget_registry.get_config(widget_type)
            if not config or not config.allow_type_change:
                continue

            # Categorize widget types
            if widget_type in [WidgetType.TEXT_EDITOR, WidgetType.OUTPUT]:
                editor_types.append(widget_type)
            elif widget_type == WidgetType.TERMINAL:
                terminal_types.append(widget_type)
            elif widget_type in [
                WidgetType.EXPLORER,
                WidgetType.TABLE_VIEW,
                WidgetType.TREE_VIEW,
                WidgetType.IMAGE_VIEWER,
            ]:
                view_types.append(widget_type)
            elif widget_type in [WidgetType.SETTINGS, WidgetType.CUSTOM]:
                special_types.append(widget_type)

        # Add editor types
        if editor_types:
            menu.addSection("Editors")
            for widget_type in editor_types:
                action = QAction(self._get_widget_type_display_name(widget_type), self)
                action.triggered.connect(
                    lambda checked, wt=widget_type: self._change_widget_type(wt)
                )
                menu.addAction(action)

        # Add terminal
        if terminal_types:
            menu.addSection("Terminal")
            for widget_type in terminal_types:
                action = QAction(self._get_widget_type_display_name(widget_type), self)
                action.triggered.connect(
                    lambda checked, wt=widget_type: self._change_widget_type(wt)
                )
                menu.addAction(action)

        # Add view types
        if view_types:
            menu.addSection("Views")
            for widget_type in view_types:
                action = QAction(self._get_widget_type_display_name(widget_type), self)
                action.triggered.connect(
                    lambda checked, wt=widget_type: self._change_widget_type(wt)
                )
                menu.addAction(action)

        # Add special types
        if special_types:
            menu.addSection("Special")
            for widget_type in special_types:
                action = QAction(self._get_widget_type_display_name(widget_type), self)
                action.triggered.connect(
                    lambda checked, wt=widget_type: self._change_widget_type(wt)
                )
                menu.addAction(action)

        # Add Theme Editor as a special app widget
        menu.addSection("App Widgets")

        # Theme Editor
        theme_editor_action = QAction("🎨 Theme Editor", self)
        theme_editor_action.triggered.connect(
            lambda: execute_command("theme.openEditor")
        )
        menu.addAction(theme_editor_action)

        # Keyboard Shortcuts Editor (if available)
        shortcuts_action = QAction("⌨️ Keyboard Shortcuts", self)
        shortcuts_action.triggered.connect(
            lambda: execute_command("settings.openKeyboardShortcuts")
        )
        menu.addAction(shortcuts_action)

    def _get_widget_type_display_name(self, widget_type: WidgetType) -> str:
        """Get display name for widget type."""
        display_names = {
            WidgetType.TEXT_EDITOR: "📝 Text Editor",
            WidgetType.TERMINAL: "💻 Terminal",
            WidgetType.OUTPUT: "📤 Output",
            WidgetType.EXPLORER: "📁 Explorer",
            WidgetType.TABLE_VIEW: "📊 Table View",
            WidgetType.TREE_VIEW: "🌳 Tree View",
            WidgetType.IMAGE_VIEWER: "🖼️ Image Viewer",
            WidgetType.SETTINGS: "⚙️ Settings",
            WidgetType.CUSTOM: "🔧 Custom Widget",
            WidgetType.PLACEHOLDER: "⬜ Empty Pane",
        }
        return display_names.get(
            widget_type, widget_type.value.replace("_", " ").title()
        )

    def _handle_widget_selection(self, widget_meta):
        """
        Handle widget selection with proper placement intent.

        In pane header context, always replace the current pane content.
        """
        # Get the pane ID from the parent PaneContent
        pane = self.parent()
        pane_id = None
        if hasattr(pane, "leaf_node") and hasattr(pane.leaf_node, "id"):
            pane_id = pane.leaf_node.id

        # Check for replace command first
        if hasattr(widget_meta, "commands") and "replace_pane" in widget_meta.commands:
            execute_command(
                widget_meta.commands["replace_pane"],
                pane=pane,
                pane_id=pane_id,
                widget_id=widget_meta.widget_id,
            )
        elif (
            hasattr(widget_meta, "supports_replacement")
            and widget_meta.supports_replacement
        ):
            # Use generic replacement for widgets that support it
            execute_command(
                "workbench.action.replaceWidgetInPane",
                pane=pane,
                pane_id=pane_id,
                widget_id=widget_meta.widget_id,
            )
        else:
            # Fallback to type change for basic widgets
            if hasattr(widget_meta, "widget_type"):
                self._change_widget_type(widget_meta.widget_type)
            elif widget_meta.open_command:
                # Last resort: use open command (will create new tab)
                execute_command(widget_meta.open_command)

    def _change_widget_type(self, widget_type: WidgetType):
        """Change the widget type of the current pane."""
        execute_command(
            "workbench.action.changePaneType",
            pane=self.parent(),
            widget_type=widget_type,
        )

    def set_pane_id(self, pane_id: str):
        """Update the pane ID display."""
        self.pane_id = pane_id
        self.id_label.setText(pane_id)

    def set_pane_number(self, number: int = None, visible: bool = False):
        """
        Set the pane number display.

        Args:
            number: Pane number (1-9) or None
            visible: Whether to show the number
        """
        if number is not None:
            self.number_label.setText(str(number))
        self.number_label.setVisible(visible and number is not None)

    def paintEvent(self, event):
        """Custom paint event to draw the background."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QBrush(self.background_color))
        super().paintEvent(event)

    def set_active(self, active: bool):
        """Update visual state for active pane."""
        self.is_active = active

        if active:
            # Set active background color
            self.background_color = QColor("#2d2d30")  # Default active background
            self.update()  # Force repaint

            self.id_label.setStyleSheet(
                """
                QLabel {
                    color: #ffffff;
                    font-size: 10px;
                    padding: 0 2px;
                    font-weight: bold;
                }
            """
            )
            # Highlight number label for active pane
            if self.number_label.isVisible():
                self.number_label.setStyleSheet(
                    """
                    QLabel {
                        background-color: #007ACC;
                        color: white;
                        border-radius: 2px;
                        padding: 0px 4px;
                        font-weight: bold;
                        font-size: 10px;
                        min-width: 12px;
                        max-width: 12px;
                        border: 1px solid white;
                    }
                """
                )
        else:
            # Set inactive background color
            self.background_color = QColor("#252526")  # Default inactive background
            self.update()  # Force repaint

            self.id_label.setStyleSheet(
                """
                QLabel {
                    color: #969696;
                    font-size: 10px;
                    padding: 0 2px;
                }
            """
            )
            # Normal number label for inactive pane
            if self.number_label.isVisible():
                self.number_label.setStyleSheet(
                    """
                    QLabel {
                        background-color: #505050;
                        color: #969696;
                        border-radius: 2px;
                        padding: 0px 4px;
                        font-weight: bold;
                        font-size: 10px;
                        min-width: 12px;
                        max-width: 12px;
                    }
                """
                )

    def apply_theme(self):
        """Apply current theme to pane header."""
        # Get theme colors using command instead of ServiceLocator
        theme_result = execute_command("theme.getCurrentColors")
        colors = theme_result.value if theme_result and theme_result.success else {}

        if colors:

            # Update background color
            self.background_color = QColor(colors.get("editor.background", "#252526"))

            # Update button styles
            button_style = f"""
                QToolButton {{
                    background-color: transparent;
                    color: {colors.get("titleBar.activeForeground", "#cccccc")};
                    border: none;
                    padding: 0px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                QToolButton:hover {{
                    background-color: {colors.get("toolbar.hoverBackground", "#505050")};
                    border: 1px solid {colors.get("focusBorder", "#007ACC")};
                    border-radius: 2px;
                }}
                QToolButton:pressed {{
                    background-color: {colors.get("focusBorder", "#007ACC")};
                }}
            """

            if hasattr(self, "split_h_button"):
                self.split_h_button.setStyleSheet(button_style)
            if hasattr(self, "split_v_button"):
                self.split_v_button.setStyleSheet(button_style)

            # Close button special style
            if hasattr(self, "close_button"):
                self.close_button.setStyleSheet(
                    f"""
                    QToolButton {{
                        background-color: transparent;
                        color: {colors.get("titleBar.activeForeground", "#cccccc")};
                        border: none;
                        padding: 0px 2px;
                        font-size: 12px;
                        font-weight: bold;
                    }}
                    QToolButton:hover {{
                        background-color: {colors.get("editorGroupHeader.tabsBackground", "#252526")};
                        color: white;
                        border-radius: 2px;
                    }}
                """
                )

            # Update label styles based on active state
            self.set_active(self.is_active)
            self.update()  # Force repaint


class CompactPaneHeader(QWidget):
    """
    Even more minimal header - appears only on hover.
    """

    split_horizontal_requested = Signal()
    split_vertical_requested = Signal()
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

        # Auto-hide behavior
        self.setMouseTracking(True)
        self.hide_on_mouse_leave = True

    def setup_ui(self):
        """Initialize compact header."""
        self.setFixedHeight(18)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Semi-transparent by default
        self.setStyleSheet(
            """
            CompactPaneHeader {
                background-color: rgba(45, 45, 48, 180);
            }
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addStretch()

        # Mini buttons
        for text, signal, tooltip in [
            ("↔", self.split_horizontal_requested, "Split H"),
            ("↕", self.split_vertical_requested, "Split V"),
            ("×", self.close_requested, "Close"),
        ]:
            btn = QToolButton()
            btn.setText(text)
            btn.setToolTip(tooltip)
            btn.setFixedSize(18, 18)
            btn.clicked.connect(signal.emit)
            btn.setStyleSheet(
                """
                QToolButton {
                    background: transparent;
                    color: #969696;
                    border: none;
                    font-size: 12px;
                }
                QToolButton:hover {
                    background: #3c3c3c;
                    color: white;
                }
            """
            )
            layout.addWidget(btn)

    def enterEvent(self, event):
        """Show fully on mouse enter."""
        self.setStyleSheet(
            """
            CompactPaneHeader {
                background-color: rgba(45, 45, 48, 255);
            }
        """
        )
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Fade on mouse leave."""
        if self.hide_on_mouse_leave:
            self.setStyleSheet(
                """
                CompactPaneHeader {
                    background-color: rgba(45, 45, 48, 180);
                }
            """
            )
        super().leaveEvent(event)
