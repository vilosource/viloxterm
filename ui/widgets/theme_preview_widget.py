#!/usr/bin/env python3
"""
Theme preview widget for live visualization.

Shows a miniature representation of the application with theme colors applied.
"""

from typing import Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QTabWidget, QTextEdit,
    QListWidget, QListWidgetItem, QPushButton,
    QLineEdit, QComboBox, QMenuBar, QMenu
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPalette, QColor, QFont
import logging

logger = logging.getLogger(__name__)


class ThemePreviewWidget(QWidget):
    """
    Live preview of theme colors applied to UI elements.

    Shows a miniature version of the application layout with
    all major UI components styled according to the theme.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize theme preview widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._current_colors: Dict[str, str] = {}
        self._setup_ui()

    def _setup_ui(self):
        """Set up the preview UI."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create preview container with border
        preview_container = QFrame()
        preview_container.setFrameStyle(QFrame.Box)
        preview_container.setStyleSheet("""
            QFrame {
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
        """)

        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Title bar preview
        self._title_bar = self._create_title_bar()
        container_layout.addWidget(self._title_bar)

        # Menu bar preview
        self._menu_bar = self._create_menu_bar()
        container_layout.addWidget(self._menu_bar)

        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Activity bar
        self._activity_bar = self._create_activity_bar()
        content_layout.addWidget(self._activity_bar)

        # Sidebar
        self._sidebar = self._create_sidebar()
        content_layout.addWidget(self._sidebar)

        # Editor area with tabs
        self._editor_area = self._create_editor_area()
        content_layout.addWidget(self._editor_area, 1)

        # Panel (terminal)
        self._panel = self._create_panel()

        # Add content to container
        container_layout.addLayout(content_layout, 1)
        container_layout.addWidget(self._panel)

        # Status bar
        self._status_bar = self._create_status_bar()
        container_layout.addWidget(self._status_bar)

        preview_container.setLayout(container_layout)

        # Add to main layout
        main_layout.addWidget(preview_container)

        self.setLayout(main_layout)
        self.setMinimumHeight(400)

    def _create_title_bar(self) -> QWidget:
        """Create title bar preview."""
        title_bar = QFrame()
        title_bar.setFixedHeight(30)
        title_bar.setObjectName("titleBar")

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 0, 8, 0)

        title_label = QLabel("ViloxTerm - Theme Preview")
        title_label.setObjectName("titleBarText")
        layout.addWidget(title_label)

        layout.addStretch()

        # Window controls
        for text in ["─", "□", "✕"]:
            btn = QPushButton(text)
            btn.setFixedSize(30, 20)
            btn.setObjectName("windowControl")
            layout.addWidget(btn)

        title_bar.setLayout(layout)
        return title_bar

    def _create_menu_bar(self) -> QWidget:
        """Create menu bar preview."""
        menu_container = QFrame()
        menu_container.setFixedHeight(25)
        menu_container.setObjectName("menuBar")

        layout = QHBoxLayout()
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(8)

        for menu_text in ["File", "Edit", "View", "Terminal", "Help"]:
            menu_label = QLabel(menu_text)
            menu_label.setObjectName("menuItem")
            layout.addWidget(menu_label)

        layout.addStretch()
        menu_container.setLayout(layout)
        return menu_container

    def _create_activity_bar(self) -> QWidget:
        """Create activity bar preview."""
        activity_bar = QFrame()
        activity_bar.setFixedWidth(48)
        activity_bar.setObjectName("activityBar")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(4)

        # Activity icons
        for icon in ["📁", "🔍", "⚙️"]:
            btn = QPushButton(icon)
            btn.setFixedSize(36, 36)
            btn.setObjectName("activityButton")
            layout.addWidget(btn)

        layout.addStretch()
        activity_bar.setLayout(layout)
        return activity_bar

    def _create_sidebar(self) -> QWidget:
        """Create sidebar preview."""
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setObjectName("sidebar")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar header
        header = QLabel("EXPLORER")
        header.setFixedHeight(25)
        header.setObjectName("sidebarHeader")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # File list
        file_list = QListWidget()
        file_list.setObjectName("sidebarList")
        for item_text in ["main.py", "config.json", "README.md", "src/", "tests/"]:
            item = QListWidgetItem(item_text)
            file_list.addItem(item)
        if file_list.count() > 0:
            file_list.setCurrentRow(0)

        layout.addWidget(file_list)
        sidebar.setLayout(layout)
        return sidebar

    def _create_editor_area(self) -> QWidget:
        """Create editor area with tabs."""
        editor_container = QFrame()
        editor_container.setObjectName("editorContainer")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab bar
        tab_widget = QTabWidget()
        tab_widget.setObjectName("editorTabs")

        # Add editor tabs
        for i, (name, content) in enumerate([
            ("main.py", "#!/usr/bin/env python3\n\ndef main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()"),
            ("config.json", '{\n  "theme": "dark",\n  "fontSize": 14,\n  "autoSave": true\n}')
        ]):
            editor = QTextEdit()
            editor.setObjectName("editor")
            editor.setPlainText(content)
            editor.setReadOnly(True)

            # Set monospace font
            font = QFont("Courier New", 10)
            font.setStyleHint(QFont.Monospace)
            editor.setFont(font)

            tab_widget.addTab(editor, name)

        tab_widget.setCurrentIndex(0)
        layout.addWidget(tab_widget)

        editor_container.setLayout(layout)
        return editor_container

    def _create_panel(self) -> QWidget:
        """Create panel (terminal) preview."""
        panel = QFrame()
        panel.setFixedHeight(120)
        panel.setObjectName("panel")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Panel header
        header = QFrame()
        header.setFixedHeight(25)
        header.setObjectName("panelHeader")

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(8, 0, 8, 0)

        header_label = QLabel("TERMINAL")
        header_label.setObjectName("panelTitle")
        header_layout.addWidget(header_label)

        header_layout.addStretch()
        header.setLayout(header_layout)
        layout.addWidget(header)

        # Terminal content
        terminal = QTextEdit()
        terminal.setObjectName("terminal")
        terminal.setReadOnly(True)

        # Terminal text with ANSI colors preview
        terminal_text = """$ python main.py
\x1b[32m✓\x1b[0m Hello, World!
\x1b[33m⚠\x1b[0m Warning: Using default config
\x1b[31m✗\x1b[0m Error: File not found
$ _"""

        terminal.setPlainText(terminal_text)

        # Set monospace font
        font = QFont("Courier New", 9)
        font.setStyleHint(QFont.Monospace)
        terminal.setFont(font)

        layout.addWidget(terminal)
        panel.setLayout(layout)
        return panel

    def _create_status_bar(self) -> QWidget:
        """Create status bar preview."""
        status_bar = QFrame()
        status_bar.setFixedHeight(22)
        status_bar.setObjectName("statusBar")

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(16)

        # Status items
        for text in ["Ready", "Python 3.12", "UTF-8", "Ln 1, Col 1"]:
            label = QLabel(text)
            label.setObjectName("statusBarItem")
            layout.addWidget(label)

        layout.addStretch()
        status_bar.setLayout(layout)
        return status_bar

    def apply_theme_colors(self, colors: Dict[str, str]):
        """
        Apply theme colors to preview.

        Args:
            colors: Dictionary of color key-value pairs
        """
        self._current_colors = colors
        stylesheet = self._generate_stylesheet(colors)
        self.setStyleSheet(stylesheet)

    def _generate_stylesheet(self, colors: Dict[str, str]) -> str:
        """
        Generate stylesheet from theme colors.

        Args:
            colors: Theme colors dictionary

        Returns:
            CSS stylesheet string
        """
        # Helper to get color with fallback
        def get_color(key: str, fallback: str = "#000000") -> str:
            return colors.get(key, fallback)

        stylesheet = f"""
        /* Title Bar */
        #titleBar {{
            background-color: {get_color("titleBar.activeBackground", "#2d2d30")};
            border-bottom: 1px solid {get_color("titleBar.border", "#3c3c3c")};
        }}
        #titleBarText {{
            color: {get_color("titleBar.activeForeground", "#cccccc")};
        }}
        #windowControl {{
            background-color: transparent;
            color: {get_color("titleBar.activeForeground", "#cccccc")};
            border: none;
        }}
        #windowControl:hover {{
            background-color: {get_color("button.hoverBackground", "#3c3c3c")};
        }}

        /* Menu Bar */
        #menuBar {{
            background-color: {get_color("menu.background", "#252526")};
            border-bottom: 1px solid {get_color("menu.separatorBackground", "#3c3c3c")};
        }}
        #menuItem {{
            color: {get_color("menu.foreground", "#cccccc")};
            padding: 0 8px;
        }}

        /* Activity Bar */
        #activityBar {{
            background-color: {get_color("activityBar.background", "#333333")};
            border-right: 1px solid {get_color("activityBar.border", "#3c3c3c")};
        }}
        #activityButton {{
            background-color: transparent;
            color: {get_color("activityBar.foreground", "#ffffff")};
            border: none;
        }}
        #activityButton:hover {{
            background-color: {get_color("activityBar.activeBackground", "#3c3c3c")};
        }}

        /* Sidebar */
        #sidebar {{
            background-color: {get_color("sideBar.background", "#252526")};
            border-right: 1px solid {get_color("sideBar.border", "#3c3c3c")};
        }}
        #sidebarHeader {{
            background-color: {get_color("sideBarSectionHeader.background", "#252526")};
            color: {get_color("sideBarSectionHeader.foreground", "#cccccc")};
            font-weight: bold;
            border-bottom: 1px solid {get_color("sideBar.border", "#3c3c3c")};
        }}
        #sidebarList {{
            background-color: {get_color("sideBar.background", "#252526")};
            color: {get_color("sideBar.foreground", "#cccccc")};
            border: none;
        }}
        #sidebarList::item:selected {{
            background-color: {get_color("list.activeSelectionBackground", "#094771")};
            color: {get_color("list.activeSelectionForeground", "#ffffff")};
        }}
        #sidebarList::item:hover {{
            background-color: {get_color("list.hoverBackground", "#2a2d2e")};
        }}

        /* Editor */
        #editorContainer {{
            background-color: {get_color("editor.background", "#1e1e1e")};
        }}
        #editorTabs {{
            background-color: {get_color("tab.inactiveBackground", "#2d2d30")};
        }}
        #editorTabs::pane {{
            background-color: {get_color("editor.background", "#1e1e1e")};
            border: none;
        }}
        #editorTabs::tab-bar {{
            background-color: {get_color("tab.inactiveBackground", "#2d2d30")};
        }}
        QTabBar::tab {{
            background-color: {get_color("tab.inactiveBackground", "#2d2d30")};
            color: {get_color("tab.inactiveForeground", "#969696")};
            border: 1px solid {get_color("tab.border", "#252526")};
            padding: 4px 12px;
        }}
        QTabBar::tab:selected {{
            background-color: {get_color("tab.activeBackground", "#1e1e1e")};
            color: {get_color("tab.activeForeground", "#ffffff")};
            border-bottom: 2px solid {get_color("tab.activeBorder", "#007acc")};
        }}
        #editor {{
            background-color: {get_color("editor.background", "#1e1e1e")};
            color: {get_color("editor.foreground", "#d4d4d4")};
            selection-background-color: {get_color("editor.selectionBackground", "#264f78")};
            border: none;
        }}

        /* Panel/Terminal */
        #panel {{
            background-color: {get_color("panel.background", "#1e1e1e")};
            border-top: 1px solid {get_color("panel.border", "#3c3c3c")};
        }}
        #panelHeader {{
            background-color: {get_color("panel.background", "#1e1e1e")};
            border-bottom: 1px solid {get_color("panel.border", "#3c3c3c")};
        }}
        #panelTitle {{
            color: {get_color("panelTitle.activeForeground", "#e7e7e7")};
            font-weight: bold;
        }}
        #terminal {{
            background-color: {get_color("terminal.background", "#1e1e1e")};
            color: {get_color("terminal.foreground", "#d4d4d4")};
            selection-background-color: {get_color("terminal.selectionBackground", "#264f78")};
            border: none;
        }}

        /* Status Bar */
        #statusBar {{
            background-color: {get_color("statusBar.background", "#007acc")};
            border-top: 1px solid {get_color("statusBar.border", "#3c3c3c")};
        }}
        #statusBarItem {{
            color: {get_color("statusBar.foreground", "#ffffff")};
        }}

        /* Scrollbars */
        QScrollBar:vertical {{
            background-color: {get_color("editor.background", "#1e1e1e")};
            width: 12px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {get_color("scrollbarSlider.background", "#424242")};
            border-radius: 6px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {get_color("scrollbarSlider.hoverBackground", "#4e4e4e")};
        }}
        QScrollBar:horizontal {{
            background-color: {get_color("editor.background", "#1e1e1e")};
            height: 12px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {get_color("scrollbarSlider.background", "#424242")};
            border-radius: 6px;
            min-width: 20px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {get_color("scrollbarSlider.hoverBackground", "#4e4e4e")};
        }}
        """

        return stylesheet

    def get_current_colors(self) -> Dict[str, str]:
        """
        Get currently applied colors.

        Returns:
            Dictionary of current theme colors
        """
        return self._current_colors.copy()