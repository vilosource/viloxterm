#!/usr/bin/env python3
"""
About dialog for ViloxTerm.

Displays application version, license, and system information.
"""

import logging

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.version import (
    APP_COPYRIGHT,
    APP_DESCRIPTION,
    APP_NAME,
    APP_URL,
    get_full_version_info,
    get_version_string,
)

logger = logging.getLogger(__name__)


class AboutDialog(QDialog):
    """
    About dialog showing application information.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header section with logo and basic info
        header_widget = self.create_header()
        layout.addWidget(header_widget)

        # Tab widget for detailed information
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_general_tab(), "General")
        self.tab_widget.addTab(self.create_system_tab(), "System Info")
        self.tab_widget.addTab(self.create_license_tab(), "License")
        self.tab_widget.addTab(self.create_credits_tab(), "Credits")
        layout.addWidget(self.tab_widget)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # GitHub button
        github_button = QPushButton("View on GitHub")
        github_button.clicked.connect(self.open_github)
        button_layout.addWidget(github_button)

        # Copy info button
        copy_button = QPushButton("Copy Info")
        copy_button.clicked.connect(self.copy_info)
        button_layout.addWidget(copy_button)

        # Close button
        close_button = QPushButton("Close")
        close_button.setDefault(True)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def create_header(self) -> QWidget:
        """Create the header section with logo and basic info."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Logo/Icon placeholder
        logo_label = QLabel()
        logo_label.setText("VT")  # Simple text logo for now
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("""
            QLabel {
                background-color: #0e639c;
                color: #ffffff;
                font-size: 32px;
                font-weight: bold;
                padding: 20px;
                border-radius: 8px;
                min-width: 80px;
                max-width: 80px;
                min-height: 80px;
                max-height: 80px;
            }
        """)
        layout.addWidget(logo_label)

        # App info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)

        # App name
        name_label = QLabel(APP_NAME)
        name_font = QFont()
        name_font.setPointSize(18)
        name_font.setBold(True)
        name_label.setFont(name_font)
        info_layout.addWidget(name_label)

        # Version
        version_label = QLabel(get_version_string())
        version_font = QFont()
        version_font.setPointSize(12)
        version_label.setFont(version_font)
        info_layout.addWidget(version_label)

        # Description
        desc_label = QLabel(APP_DESCRIPTION)
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)

        # Copyright
        copyright_label = QLabel(APP_COPYRIGHT)
        copyright_label.setStyleSheet("color: #888888;")
        info_layout.addWidget(copyright_label)

        info_layout.addStretch()
        layout.addLayout(info_layout)
        layout.addStretch()

        return widget

    def create_general_tab(self) -> QWidget:
        """Create the general information tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info = get_full_version_info()

        # Create info text
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setPlainText(self.format_general_info(info))
        layout.addWidget(info_text)

        return widget

    def create_system_tab(self) -> QWidget:
        """Create the system information tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info = get_full_version_info()

        # System info grid
        grid = QGridLayout()
        grid.setSpacing(10)

        row = 0

        # Python version
        grid.addWidget(QLabel("Python:"), row, 0)
        grid.addWidget(QLabel(info['python_version']), row, 1)
        row += 1

        # Qt version
        grid.addWidget(QLabel("Qt Runtime:"), row, 0)
        grid.addWidget(QLabel(info['qt_version']['qt']), row, 1)
        row += 1

        # PySide6 version
        grid.addWidget(QLabel("PySide6:"), row, 0)
        grid.addWidget(QLabel(info['qt_version']['pyside']), row, 1)
        row += 1

        # Platform
        platform = info['platform']
        grid.addWidget(QLabel("OS:"), row, 0)
        grid.addWidget(QLabel(f"{platform['system']} {platform['release']}"), row, 1)
        row += 1

        # Machine
        grid.addWidget(QLabel("Architecture:"), row, 0)
        grid.addWidget(QLabel(platform['machine']), row, 1)
        row += 1

        # Git info if available
        if info['git']['commit']:
            grid.addWidget(QLabel("Git Commit:"), row, 0)
            commit_text = info['git']['commit_short']
            if info['git']['dirty']:
                commit_text += " (modified)"
            grid.addWidget(QLabel(commit_text), row, 1)
            row += 1

            grid.addWidget(QLabel("Git Branch:"), row, 0)
            grid.addWidget(QLabel(info['git']['branch']), row, 1)
            row += 1

        # Mode
        grid.addWidget(QLabel("Mode:"), row, 0)
        mode = "Development" if info['dev_mode'] else "Production"
        mode_label = QLabel(mode)
        if info['dev_mode']:
            mode_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        grid.addWidget(mode_label, row, 1)

        layout.addLayout(grid)
        layout.addStretch()

        return widget

    def create_license_tab(self) -> QWidget:
        """Create the license tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        license_text = QTextEdit()
        license_text.setReadOnly(True)
        license_text.setPlainText(self.get_license_text())
        layout.addWidget(license_text)

        return widget

    def create_credits_tab(self) -> QWidget:
        """Create the credits tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        credits_text = QTextEdit()
        credits_text.setReadOnly(True)
        credits_text.setHtml(self.get_credits_html())
        layout.addWidget(credits_text)

        return widget

    def format_general_info(self, info: dict) -> str:
        """Format general information for display."""
        lines = [
            f"Application: {info['app_name']}",
            f"Version: {info['version_string']}",
            f"Description: {info['app_description']}",
            "",
            f"Build Date: {info['build_date']} {info['build_time']}",
            f"License: {info['app_license']}",
            f"Website: {info['app_url']}",
            "",
            "This application is built with:",
            "• Python - Programming language",
            "• PySide6 - Qt bindings for Python",
            "• Flask - Web framework for terminal backend",
            "• xterm.js - Terminal emulator",
            "",
            "For more information, please visit our GitHub repository."
        ]

        if info['dev_mode']:
            lines.extend([
                "",
                "⚠️ Development Mode Active",
                "This is a development build and may contain unstable features."
            ])

        return "\n".join(lines)

    def get_license_text(self) -> str:
        """Get the license text."""
        return f"""MIT License

{APP_COPYRIGHT}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

    def get_credits_html(self) -> str:
        """Get credits in HTML format."""
        return f"""
        <h3>ViloxTerm Contributors</h3>
        <p>ViloxTerm is developed by a community of contributors.</p>

        <h4>Core Technologies</h4>
        <ul>
            <li><b>Python</b> - <a href="https://python.org">python.org</a></li>
            <li><b>Qt/PySide6</b> - <a href="https://qt.io">qt.io</a></li>
            <li><b>Flask</b> - <a href="https://flask.palletsprojects.com">flask.palletsprojects.com</a></li>
            <li><b>xterm.js</b> - <a href="https://xtermjs.org">xtermjs.org</a></li>
        </ul>

        <h4>Icons and Themes</h4>
        <ul>
            <li><b>VSCode Theme</b> - Inspired by Visual Studio Code</li>
            <li><b>Feather Icons</b> - Icon design inspiration</li>
        </ul>

        <h4>Special Thanks</h4>
        <p>To all contributors, testers, and users who have helped make ViloxTerm better!</p>

        <p style="margin-top: 20px;">
        <a href="{APP_URL}">Visit our GitHub repository</a> to contribute or report issues.
        </p>
        """

    def open_github(self):
        """Open the GitHub repository in browser."""
        QDesktopServices.openUrl(QUrl(APP_URL))

    def copy_info(self):
        """Copy system information to clipboard."""
        from PySide6.QtWidgets import QApplication

        info = get_full_version_info()
        text_lines = [
            f"{APP_NAME} {info['version_string']}",
            f"Python: {info['python_version']}",
            f"Qt: {info['qt_version']['qt']}",
            f"PySide6: {info['qt_version']['pyside']}",
            f"Platform: {info['platform']['system']} {info['platform']['release']}",
        ]

        if info['git']['commit']:
            text_lines.append(f"Git: {info['git']['branch']} @ {info['git']['commit_short']}")

        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(text_lines))

        # Show brief notification (could be improved with a toast notification)
        logger.info("System information copied to clipboard")

    def apply_theme(self):
        """Apply current theme to about dialog."""
        from core.commands.executor import execute_command

        # Get theme colors through command pattern
        result = execute_command("theme.getCurrentColors")
        if result and result.success:
            colors = result.value
        else:
            # Fallback colors
            colors = {
                "editor.background": "#252526",
                "editor.foreground": "#cccccc",
                "tab.inactiveBackground": "#2d2d30",
                "tab.activeBackground": "#1e1e1e",
                "button.background": "#0e639c",
                "button.foreground": "#ffffff",
                "button.hoverBackground": "#1177bb",
                "sideBar.background": "#252526"
            }

        self.setStyleSheet(f"""
                QDialog {{
                    background-color: {colors.get("editor.background", "#252526")};
                    color: {colors.get("editor.foreground", "#cccccc")};
                }}

                QTabWidget::pane {{
                    background-color: {colors.get("editor.background", "#252526")};
                    border: 1px solid {colors.get("tab.inactiveBackground", "#2d2d30")};
                }}

                QTabBar::tab {{
                    background-color: {colors.get("tab.inactiveBackground", "#2d2d30")};
                    color: {colors.get("editor.foreground", "#cccccc")};
                    padding: 8px 16px;
                    margin-right: 2px;
                }}

                QTabBar::tab:selected {{
                    background-color: {colors.get("tab.activeBackground", "#1e1e1e")};
                    border-bottom: 2px solid {colors.get("button.background", "#0e639c")};
                }}

                QTextEdit {{
                    background-color: {colors.get("sideBar.background", "#252526")};
                    color: {colors.get("editor.foreground", "#cccccc")};
                    border: 1px solid {colors.get("tab.inactiveBackground", "#2d2d30")};
                    padding: 10px;
                    font-family: monospace;
                }}

                QPushButton {{
                    background-color: {colors.get("button.background", "#0e639c")};
                    color: {colors.get("button.foreground", "#ffffff")};
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }}

                QPushButton:hover {{
                    background-color: {colors.get("button.hoverBackground", "#1177bb")};
                }}

                QPushButton:pressed {{
                    background-color: {colors.get("button.background", "#0e639c")};
                }}

                QLabel {{
                    color: {colors.get("editor.foreground", "#cccccc")};
                }}
            """)

        # Update app icon label if it exists
        if hasattr(self, 'app_icon_label'):
            self.app_icon_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {colors.get("button.background", "#0e639c")};
                    color: {colors.get("button.foreground", "#ffffff")};
                    font-size: 32px;
                    font-weight: bold;
                    border-radius: 8px;
                    padding: 20px;
                }}
            """)
