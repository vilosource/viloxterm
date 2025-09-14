#!/usr/bin/env python3
"""Quick test to verify widget menu intent system is working."""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from core.app_widget_manager import AppWidgetManager
from core.app_widget_registry import register_builtin_widgets
from ui.widgets.pane_header import PaneHeaderBar
from ui.widgets.split_pane_widget import SplitPaneWidget
from ui.widgets.widget_registry import WidgetType


def test_widget_menu():
    """Test the widget menu functionality."""
    app = QApplication(sys.argv)

    # Register widgets
    register_builtin_widgets()
    manager = AppWidgetManager.get_instance()

    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Widget Menu Test")
    window.resize(800, 600)

    # Create central widget
    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)

    # Add test info
    info = QTextEdit()
    info.setMaximumHeight(100)
    info.setPlainText("Test Instructions:\n"
                     "1. Click 'Show Menu' to open the pane header menu\n"
                     "2. Select 'Theme Editor' - it should replace content, not open new tab\n"
                     "3. Check console output for confirmation")
    layout.addWidget(info)

    # Create split pane widget
    split_widget = SplitPaneWidget(initial_widget_type=WidgetType.TEXT_EDITOR)
    layout.addWidget(split_widget)

    # Get the first pane's header
    if hasattr(split_widget, 'root_widget'):
        root = split_widget.root_widget
        if hasattr(root, 'header_bar'):
            header = root.header_bar

            # Add button to trigger menu
            btn = QPushButton("Show Pane Header Menu")
            btn.clicked.connect(lambda: header.show_widget_type_menu())
            layout.addWidget(btn)

            print("✅ Test setup complete!")
            print("📋 Registered widgets:")
            for widget in manager.get_menu_widgets():
                print(f"  - {widget.display_name}")
                if hasattr(widget, 'commands'):
                    print(f"    Commands: {widget.commands}")
                if hasattr(widget, 'supports_replacement'):
                    print(f"    Supports replacement: {widget.supports_replacement}")

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    test_widget_menu()