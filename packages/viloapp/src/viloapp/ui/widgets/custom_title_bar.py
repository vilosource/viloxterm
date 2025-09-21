#!/usr/bin/env python3
"""
Custom title bar widget for frameless window mode.
Provides window controls and drag functionality.
"""

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QToolButton,
    QWidget,
)

logger = logging.getLogger(__name__)


class CustomTitleBar(QWidget):
    """
    Custom title bar with integrated menu and window controls.
    Supports Wayland-compatible window dragging.
    """

    # Signals
    minimize_requested = Signal()
    maximize_requested = Signal()
    close_requested = Signal()
    menu_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setObjectName("customTitleBar")
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        """Initialize the title bar UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(8)

        # Menu button (hamburger icon)
        self.menu_button = QToolButton(self)
        self.menu_button.setText("☰")
        self.menu_button.setObjectName("menuButton")
        self.menu_button.setToolTip("Menu")
        self.menu_button.clicked.connect(self.on_menu_clicked)
        layout.addWidget(self.menu_button)

        # Application title with dev mode indicator
        from viloapp.core.app_config import app_config

        title_text = "ViloxTerm [DEV]" if app_config.dev_mode else "ViloxTerm"
        self.title_label = QLabel(title_text, self)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.title_label)

        # Spacer to push buttons to the right
        layout.addStretch()

        # Window control buttons
        self.min_button = QToolButton(self)
        self.min_button.setText("─")
        self.min_button.setObjectName("minimizeButton")
        self.min_button.setToolTip("Minimize")
        self.min_button.clicked.connect(self.minimize_requested.emit)
        layout.addWidget(self.min_button)

        self.max_button = QToolButton(self)
        self.max_button.setText("□")
        self.max_button.setObjectName("maximizeButton")
        self.max_button.setToolTip("Maximize")
        self.max_button.clicked.connect(self.on_maximize_clicked)
        layout.addWidget(self.max_button)

        self.close_button = QToolButton(self)
        self.close_button.setText("×")
        self.close_button.setObjectName("closeButton")
        self.close_button.setToolTip("Close")
        self.close_button.clicked.connect(self.close_requested.emit)
        layout.addWidget(self.close_button)

    def apply_styles(self):
        """Apply styling to the title bar."""
        from PySide6.QtGui import QColor, QPalette

        from viloapp.core.app_config import app_config

        # Use red background for dev mode
        title_bar_bg = "#8B0000" if app_config.dev_mode else "#2d2d30"
        logger.info(
            f"CustomTitleBar: dev_mode={app_config.dev_mode}, bg_color={title_bar_bg}"
        )

        # Set background using palette
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(title_bar_bg))
        self.setPalette(palette)

        self.setStyleSheet(
            """

            /* Title label */
            #titleLabel {
                color: #cccccc;
                font-size: 13px;
                padding: 0 8px;
            }

            /* Common button style */
            QToolButton {
                background-color: transparent;
                color: #cccccc;
                border: none;
                padding: 4px 8px;
                font-size: 14px;
                font-weight: bold;
            }

            QToolButton:hover {
                background-color: #3e3e42;
            }

            /* Close button special styling */
            #closeButton:hover {
                background-color: #e81123;
                color: white;
            }

            /* Menu button */
            #menuButton {
                font-size: 16px;
                padding: 4px 6px;
            }
        """
        )

    def on_menu_clicked(self):
        """Handle menu button click."""
        self.menu_requested.emit()

    def on_maximize_clicked(self):
        """Handle maximize button click."""
        if self.window().isMaximized():
            self.max_button.setText("□")
            self.max_button.setToolTip("Maximize")
        else:
            self.max_button.setText("❐")
            self.max_button.setToolTip("Restore")
        self.maximize_requested.emit()

    def update_maximize_button(self, is_maximized):
        """Update maximize button appearance based on window state."""
        if is_maximized:
            self.max_button.setText("❐")
            self.max_button.setToolTip("Restore")
        else:
            self.max_button.setText("□")
            self.max_button.setToolTip("Maximize")

    def set_title(self, title):
        """Set the window title."""
        self.title_label.setText(title)

    def mousePressEvent(self, event):
        """Handle mouse press for window dragging."""
        if event.button() == Qt.LeftButton:
            # Check if click is not on a button
            clicked_widget = self.childAt(event.position().toPoint())
            if not isinstance(clicked_widget, (QToolButton, QPushButton)):
                # Use Wayland-compatible window dragging
                window_handle = self.window().windowHandle()
                if window_handle:
                    try:
                        window_handle.startSystemMove()
                        event.accept()
                        return
                    except Exception as e:
                        logger.warning(f"startSystemMove not available: {e}")
                        # Fallback for older Qt versions or non-Wayland systems
                        self.drag_start_position = event.globalPosition().toPoint()
                        event.accept()
                        return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for fallback dragging."""
        if hasattr(self, "drag_start_position") and event.buttons() == Qt.LeftButton:
            # Fallback dragging for systems without startSystemMove
            delta = event.globalPosition().toPoint() - self.drag_start_position
            self.window().move(self.window().pos() + delta)
            self.drag_start_position = event.globalPosition().toPoint()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if hasattr(self, "drag_start_position"):
            del self.drag_start_position
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double-click to maximize/restore."""
        if event.button() == Qt.LeftButton:
            clicked_widget = self.childAt(event.position().toPoint())
            if not isinstance(clicked_widget, (QToolButton, QPushButton)):
                self.on_maximize_clicked()
                event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def attach_menu(self, menu):
        """Attach a QMenu to the menu button."""
        if isinstance(menu, QMenu):
            self.menu_button.setMenu(menu)
            self.menu_button.setPopupMode(QToolButton.InstantPopup)
            # Disconnect the clicked signal if menu is attached
            try:
                self.menu_button.clicked.disconnect(self.on_menu_clicked)
            except (TypeError, RuntimeError) as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.debug(f"Signal was not connected: {e}")
                # Signal was not connected, which is fine
