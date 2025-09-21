# Week 4: Terminal Plugin Completion and Editor Extraction

## Overview
Week 4 completes the terminal plugin integration and begins the extraction of the editor functionality into the viloedit plugin.

**Duration**: 5 days
**Goal**: Finalize terminal plugin, ensure full integration, and start editor plugin extraction

## Prerequisites
- [ ] Week 1-3 completed successfully
- [ ] Terminal plugin package created and tested
- [ ] Plugin host infrastructure working

## Day 1: Terminal Plugin Polish

### Morning (3 hours)

#### Task 1.1: Advanced Terminal Features

Create `/home/kuja/GitHub/viloapp/packages/viloxterm/src/viloxterm/features.py`:
```python
"""Advanced terminal features."""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TerminalProfile:
    """Terminal profile configuration."""
    name: str
    shell: str
    args: List[str] = None
    env: Dict[str, str] = None
    cwd: str = None
    icon: str = "terminal"
    color: str = None


class TerminalProfileManager:
    """Manages terminal profiles."""

    def __init__(self):
        self.profiles: Dict[str, TerminalProfile] = {}
        self._load_default_profiles()

    def _load_default_profiles(self):
        """Load default terminal profiles."""
        import platform

        if platform.system() == "Windows":
            self.profiles["powershell"] = TerminalProfile(
                name="PowerShell",
                shell="powershell.exe",
                icon="terminal-powershell"
            )
            self.profiles["cmd"] = TerminalProfile(
                name="Command Prompt",
                shell="cmd.exe",
                icon="terminal-cmd"
            )
            # Check for WSL
            try:
                import subprocess
                result = subprocess.run(["wsl", "--list"], capture_output=True)
                if result.returncode == 0:
                    self.profiles["wsl"] = TerminalProfile(
                        name="WSL",
                        shell="wsl.exe",
                        icon="terminal-linux"
                    )
            except:
                pass

        else:  # Unix-like systems
            self.profiles["bash"] = TerminalProfile(
                name="Bash",
                shell="/bin/bash",
                icon="terminal-bash"
            )
            self.profiles["zsh"] = TerminalProfile(
                name="Zsh",
                shell="/bin/zsh",
                icon="terminal-zsh"
            )
            self.profiles["sh"] = TerminalProfile(
                name="Shell",
                shell="/bin/sh",
                icon="terminal"
            )

            # Check for additional shells
            import os
            if os.path.exists("/usr/bin/fish"):
                self.profiles["fish"] = TerminalProfile(
                    name="Fish",
                    shell="/usr/bin/fish",
                    icon="terminal-fish"
                )

    def add_profile(self, profile_id: str, profile: TerminalProfile):
        """Add a custom profile."""
        self.profiles[profile_id] = profile

    def get_profile(self, profile_id: str) -> Optional[TerminalProfile]:
        """Get a profile by ID."""
        return self.profiles.get(profile_id)

    def list_profiles(self) -> List[TerminalProfile]:
        """List all available profiles."""
        return list(self.profiles.values())

    def get_default_profile(self) -> TerminalProfile:
        """Get the default profile for the current platform."""
        import platform

        if platform.system() == "Windows":
            return self.profiles.get("powershell", TerminalProfile("Default", "powershell.exe"))
        else:
            return self.profiles.get("bash", TerminalProfile("Default", "/bin/bash"))


class TerminalSessionManager:
    """Enhanced session management."""

    def __init__(self, server_manager):
        self.server = server_manager
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, profile: TerminalProfile = None, name: str = None) -> str:
        """Create a new session with profile."""
        if profile is None:
            manager = TerminalProfileManager()
            profile = manager.get_default_profile()

        session_id = self.server.create_session(
            command=profile.shell,
            cmd_args=" ".join(profile.args) if profile.args else "",
            cwd=profile.cwd
        )

        self.sessions[session_id] = {
            "name": name or f"Terminal {len(self.sessions) + 1}",
            "profile": profile,
            "created_at": time.time()
        }

        return session_id

    def rename_session(self, session_id: str, name: str):
        """Rename a session."""
        if session_id in self.sessions:
            self.sessions[session_id]["name"] = name

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        return self.sessions.get(session_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions with info."""
        result = []
        for session_id, info in self.sessions.items():
            result.append({
                "id": session_id,
                "name": info["name"],
                "profile": info["profile"].name,
                "created_at": info["created_at"]
            })
        return result


class TerminalSearch:
    """Terminal search functionality."""

    def __init__(self):
        self.search_history: List[str] = []

    def search_in_terminal(self, terminal_widget, pattern: str, case_sensitive: bool = False):
        """Search for pattern in terminal output."""
        if not terminal_widget or not terminal_widget.web_view:
            return

        # JavaScript for searching in xterm.js
        js_code = f"""
        (function() {{
            const searchAddon = term.searchAddon;
            if (searchAddon) {{
                searchAddon.findNext('{pattern}', {{
                    caseSensitive: {str(case_sensitive).lower()},
                    wholeWord: false,
                    regex: false
                }});
            }}
        }})();
        """

        terminal_widget.web_view.page().runJavaScript(js_code)

        # Add to history
        if pattern and pattern not in self.search_history:
            self.search_history.append(pattern)

    def find_next(self, terminal_widget):
        """Find next occurrence."""
        if terminal_widget and terminal_widget.web_view:
            terminal_widget.web_view.page().runJavaScript(
                "if (term.searchAddon) term.searchAddon.findNext();"
            )

    def find_previous(self, terminal_widget):
        """Find previous occurrence."""
        if terminal_widget and terminal_widget.web_view:
            terminal_widget.web_view.page().runJavaScript(
                "if (term.searchAddon) term.searchAddon.findPrevious();"
            )
```

#### Task 1.2: Terminal UI Enhancements

Create `/home/kuja/GitHub/viloapp/packages/viloxterm/src/viloxterm/ui_components.py`:
```python
"""Terminal UI components."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QToolBar,
    QAction, QComboBox, QLineEdit, QPushButton,
    QMenu, QLabel
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon, QKeySequence

from .features import TerminalProfileManager


class TerminalToolBar(QToolBar):
    """Terminal toolbar with controls."""

    # Signals
    new_terminal = Signal()
    clear_terminal = Signal()
    close_terminal = Signal()
    split_terminal = Signal()
    profile_changed = Signal(str)
    search_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup toolbar UI."""
        # New terminal action
        self.new_action = QAction("New Terminal", self)
        self.new_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        self.new_action.triggered.connect(self.new_terminal.emit)
        self.addAction(self.new_action)

        # Split terminal action
        self.split_action = QAction("Split Terminal", self)
        self.split_action.triggered.connect(self.split_terminal.emit)
        self.addAction(self.split_action)

        self.addSeparator()

        # Profile selector
        self.profile_combo = QComboBox()
        self.profile_combo.setToolTip("Select terminal profile")
        self._load_profiles()
        self.profile_combo.currentTextChanged.connect(self.profile_changed.emit)
        self.addWidget(self.profile_combo)

        self.addSeparator()

        # Clear action
        self.clear_action = QAction("Clear", self)
        self.clear_action.setShortcut(QKeySequence("Ctrl+L"))
        self.clear_action.triggered.connect(self.clear_terminal.emit)
        self.addAction(self.clear_action)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setMaximumWidth(200)
        self.search_input.returnPressed.connect(self._on_search)
        self.addWidget(self.search_input)

        # Close action
        self.addSeparator()
        self.close_action = QAction("Close", self)
        self.close_action.triggered.connect(self.close_terminal.emit)
        self.addAction(self.close_action)

    def _load_profiles(self):
        """Load terminal profiles into combo box."""
        manager = TerminalProfileManager()
        profiles = manager.list_profiles()

        self.profile_combo.clear()
        for profile in profiles:
            self.profile_combo.addItem(profile.name, userData=profile)

    def _on_search(self):
        """Handle search request."""
        text = self.search_input.text()
        if text:
            self.search_requested.emit(text)

    def get_selected_profile(self):
        """Get currently selected profile."""
        return self.profile_combo.currentData()


class TerminalTabWidget(QWidget):
    """Terminal tab widget for multiple sessions."""

    # Signals
    session_changed = Signal(str)  # session_id
    session_closed = Signal(str)  # session_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sessions = {}
        self.setup_ui()

    def setup_ui(self):
        """Setup tab widget UI."""
        from PySide6.QtWidgets import QTabWidget

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self._on_tab_close)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def add_terminal(self, widget, session_id: str, name: str = None):
        """Add a terminal tab."""
        if name is None:
            name = f"Terminal {self.tab_widget.count() + 1}"

        index = self.tab_widget.addTab(widget, name)
        self.sessions[index] = session_id

        # Switch to new tab
        self.tab_widget.setCurrentIndex(index)

    def remove_terminal(self, session_id: str):
        """Remove a terminal tab."""
        for index, sid in self.sessions.items():
            if sid == session_id:
                self.tab_widget.removeTab(index)
                del self.sessions[index]
                self.session_closed.emit(session_id)
                break

    def _on_tab_close(self, index: int):
        """Handle tab close request."""
        if index in self.sessions:
            session_id = self.sessions[index]
            self.session_closed.emit(session_id)

    def _on_tab_changed(self, index: int):
        """Handle tab change."""
        if index >= 0 and index in self.sessions:
            session_id = self.sessions[index]
            self.session_changed.emit(session_id)

    def get_current_terminal(self):
        """Get current terminal widget."""
        return self.tab_widget.currentWidget()

    def get_current_session_id(self) -> Optional[str]:
        """Get current session ID."""
        index = self.tab_widget.currentIndex()
        return self.sessions.get(index)
```

### Afternoon (3 hours)

#### Task 1.3: Terminal Settings Integration

Create `/home/kuja/GitHub/viloapp/packages/viloxterm/src/viloxterm/settings.py`:
```python
"""Terminal settings management."""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TerminalSettings:
    """Terminal settings configuration."""

    # Shell settings
    shell_linux: str = "/bin/bash"
    shell_osx: str = "/bin/zsh"
    shell_windows: str = "powershell.exe"

    # Font settings
    font_family: str = "monospace"
    font_size: int = 14
    font_weight: str = "normal"
    line_height: float = 1.2

    # Cursor settings
    cursor_style: str = "block"  # block, underline, bar
    cursor_blink: bool = True

    # Colors (will be synced with theme)
    use_theme_colors: bool = True
    background: str = "#1e1e1e"
    foreground: str = "#d4d4d4"
    cursor_color: str = "#ffffff"
    selection_background: str = "#264f78"

    # Scrollback
    scrollback_lines: int = 1000

    # Bell
    bell_style: str = "none"  # none, visual, sound, both

    # Copy/Paste
    copy_on_select: bool = False
    paste_on_middle_click: bool = True

    # Performance
    renderer_type: str = "canvas"  # canvas, dom, webgl

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TerminalSettings":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


class TerminalSettingsManager:
    """Manages terminal settings."""

    def __init__(self, config_service=None):
        self.config_service = config_service
        self.settings = TerminalSettings()
        self._load_settings()

    def _load_settings(self):
        """Load settings from configuration service."""
        if not self.config_service:
            return

        # Load each setting
        for field in TerminalSettings.__annotations__:
            key = f"terminal.{field}"
            value = self.config_service.get(key)
            if value is not None:
                setattr(self.settings, field, value)

    def save_settings(self):
        """Save settings to configuration service."""
        if not self.config_service:
            return

        for field, value in self.settings.to_dict().items():
            key = f"terminal.{field}"
            self.config_service.set(key, value)

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting."""
        return getattr(self.settings, key, default)

    def set_setting(self, key: str, value: Any):
        """Set a specific setting."""
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            self.save_settings()

    def apply_to_terminal(self, terminal_widget):
        """Apply settings to a terminal widget."""
        if not terminal_widget or not terminal_widget.web_view:
            return

        # Create JavaScript configuration
        js_config = f"""
        (function() {{
            if (typeof term !== 'undefined') {{
                // Font settings
                term.options.fontFamily = '{self.settings.font_family}';
                term.options.fontSize = {self.settings.font_size};
                term.options.lineHeight = {self.settings.line_height};

                // Cursor settings
                term.options.cursorStyle = '{self.settings.cursor_style}';
                term.options.cursorBlink = {str(self.settings.cursor_blink).lower()};

                // Scrollback
                term.options.scrollback = {self.settings.scrollback_lines};

                // Renderer
                term.options.rendererType = '{self.settings.renderer_type}';

                // Colors (if not using theme)
                if (!{str(self.settings.use_theme_colors).lower()}) {{
                    term.options.theme = {{
                        background: '{self.settings.background}',
                        foreground: '{self.settings.foreground}',
                        cursor: '{self.settings.cursor_color}',
                        selection: '{self.settings.selection_background}'
                    }};
                }}

                // Refresh
                term.refresh(0, term.rows - 1);
            }}
        }})();
        """

        terminal_widget.web_view.page().runJavaScript(js_config)

    def sync_with_theme(self, theme_colors: Dict[str, str]):
        """Sync terminal colors with application theme."""
        if not self.settings.use_theme_colors:
            return

        # Map theme colors to terminal colors
        color_mapping = {
            "terminal.background": "background",
            "terminal.foreground": "foreground",
            "terminal.cursor": "cursor_color",
            "terminal.selection": "selection_background"
        }

        for theme_key, setting_key in color_mapping.items():
            if theme_key in theme_colors:
                setattr(self.settings, setting_key, theme_colors[theme_key])
```

### Validation Checkpoint
- [ ] Terminal profiles working
- [ ] UI components created
- [ ] Settings management functional
- [ ] Features integrated

## Day 2: Editor Plugin Preparation

### Morning (3 hours)

#### Task 2.1: Analyze Editor Implementation

Document current editor implementation:
```bash
# Find editor-related files
find . -type f -name "*editor*" | grep -v __pycache__

# Expected files:
# ./ui/editor/editor_widget.py
# ./ui/editor/syntax_highlighter.py
# ./ui/editor/code_completer.py
# ./services/editor_service.py
# ./core/commands/builtin/editor_commands.py
```

#### Task 2.2: Create Editor Package Structure

```bash
cd /home/kuja/GitHub/viloapp/packages

# Create viloedit package structure
mkdir -p viloedit/{src/viloedit,tests,docs,assets}
mkdir -p viloedit/src/viloedit/{syntax,themes,languages,commands}

# Create package files
touch viloedit/README.md
touch viloedit/CHANGELOG.md
touch viloedit/src/viloedit/__init__.py
touch viloedit/src/viloedit/plugin.py
touch viloedit/src/viloedit/widget.py
touch viloedit/src/viloedit/editor.py
```

#### Task 2.3: Create Package Configuration

Create `/home/kuja/GitHub/viloapp/packages/viloedit/pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "viloedit"
version = "1.0.0"
description = "Code Editor Plugin for ViloxTerm"
authors = [{name = "ViloxTerm Team", email = "team@viloxterm.org"}]
readme = "README.md"
license = {text = "MIT"}
keywords = ["editor", "code", "syntax", "highlighting", "plugin"]
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: X11 Applications :: Qt",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Topic :: Text Editors",
]

dependencies = [
    "viloapp-sdk>=1.0.0",
    "PySide6>=6.5.0",
    "Pygments>=2.0.0",
    "tree-sitter>=0.20.0",
]

[project.optional-dependencies]
lsp = [
    "pylsp>=1.0.0",
    "python-lsp-jsonrpc>=1.0.0",
]
dev = [
    "pytest>=7.0",
    "pytest-qt>=4.2.0",
]

[project.entry-points."viloapp.plugins"]
editor = "viloedit.plugin:EditorPlugin"

[tool.setuptools]
package-dir = {"": "src"}
packages = ["viloedit"]

[tool.setuptools.package-data]
viloedit = [
    "themes/**/*",
    "languages/**/*",
]
```

### Afternoon (3 hours)

#### Task 2.4: Create Editor Widget Base

Create `/home/kuja/GitHub/viloapp/packages/viloedit/src/viloedit/editor.py`:
```python
"""Code editor widget implementation."""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from PySide6.QtWidgets import QPlainTextEdit, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Signal, Qt, QRect
from PySide6.QtGui import QTextOption, QPainter, QColor, QTextFormat, QFont

from Pygments import highlight
from Pygments.lexers import get_lexer_for_filename, TextLexer
from Pygments.formatters import HtmlFormatter

logger = logging.getLogger(__name__)


class LineNumberArea(QWidget):
    """Line number area for editor."""

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    """Code editor widget with syntax highlighting."""

    # Signals
    file_loaded = Signal(str)  # file_path
    file_saved = Signal(str)  # file_path
    modified_changed = Signal(bool)  # is_modified
    cursor_position_changed = Signal(int, int)  # line, column

    def __init__(self, parent=None):
        super().__init__(parent)

        self.file_path: Optional[Path] = None
        self.lexer = None
        self.line_number_area = LineNumberArea(self)

        self.setup_editor()
        self.update_line_number_area_width(0)

        # Connect signals
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.textChanged.connect(self._on_text_changed)

    def setup_editor(self):
        """Setup editor configuration."""
        # Font
        font = QFont("monospace")
        font.setPointSize(12)
        self.setFont(font)

        # Tab settings
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))

        # Word wrap
        self.setWordWrapMode(QTextOption.NoWrap)

        # Initial highlight
        self.highlight_current_line()

    def line_number_area_width(self):
        """Calculate line number area width."""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num /= 10
            digits += 1

        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        """Update line number area width."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """Update line number area on scroll."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(),
                                        self.line_number_area.width(),
                                        rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        """Handle resize event."""
        super().resizeEvent(event)

        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(),
                                                self.line_number_area_width(),
                                                cr.height()))

    def line_number_area_paint_event(self, event):
        """Paint line numbers."""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.line_number_area.width(),
                               self.fontMetrics().height(),
                               Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlight_current_line(self):
        """Highlight the current line."""
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            line_color = QColor(Qt.yellow).lighter(160)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()

            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

        # Emit cursor position
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        self.cursor_position_changed.emit(line, column)

    def load_file(self, file_path: str):
        """Load a file into the editor."""
        try:
            self.file_path = Path(file_path)

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.setPlainText(content)
            self.document().setModified(False)

            # Set lexer based on file extension
            try:
                self.lexer = get_lexer_for_filename(file_path)
            except:
                self.lexer = TextLexer()

            self.file_loaded.emit(file_path)

        except Exception as e:
            logger.error(f"Failed to load file {file_path}: {e}")

    def save_file(self, file_path: str = None):
        """Save the editor content to file."""
        if file_path:
            self.file_path = Path(file_path)

        if not self.file_path:
            return False

        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.toPlainText())

            self.document().setModified(False)
            self.file_saved.emit(str(self.file_path))
            return True

        except Exception as e:
            logger.error(f"Failed to save file {self.file_path}: {e}")
            return False

    def _on_text_changed(self):
        """Handle text change."""
        is_modified = self.document().isModified()
        self.modified_changed.emit(is_modified)
```

### Validation Checkpoint
- [ ] Editor package structure created
- [ ] Base editor widget implemented
- [ ] Configuration complete
- [ ] Ready for plugin implementation

## Day 3: Editor Plugin Implementation

### Morning (3 hours)

#### Task 3.1: Implement Editor Plugin

Create `/home/kuja/GitHub/viloapp/packages/viloedit/src/viloedit/plugin.py`:
```python
"""ViloEdit Code Editor Plugin."""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from viloapp_sdk import (
    IPlugin, PluginMetadata, PluginCapability,
    IPluginContext, EventType
)

from .widget import EditorWidgetFactory
from .editor import CodeEditor
from .syntax import SyntaxHighlighter
from .commands import register_editor_commands

logger = logging.getLogger(__name__)


class EditorPlugin(IPlugin):
    """Code editor plugin for ViloxTerm."""

    def __init__(self):
        self.context: Optional[IPluginContext] = None
        self.widget_factory = EditorWidgetFactory()
        self.open_editors: Dict[str, CodeEditor] = {}

    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            id="viloedit",
            name="ViloEdit",
            version="1.0.0",
            description="Professional code editor with syntax highlighting",
            author="ViloxTerm Team",
            homepage="https://github.com/viloxterm/viloedit",
            license="MIT",
            icon="file-text",
            categories=["Editor", "Development Tools"],
            keywords=["editor", "code", "syntax", "highlighting"],
            engines={"viloapp": ">=2.0.0"},
            dependencies=["viloapp-sdk@>=1.0.0"],
            activation_events=[
                "onCommand:editor.open",
                "onCommand:editor.new",
                "onLanguage:python",
                "onLanguage:javascript",
                "workspaceContains:**/*.py"
            ],
            capabilities=[PluginCapability.WIDGETS, PluginCapability.COMMANDS, PluginCapability.LANGUAGES],
            contributes={
                "widgets": [
                    {
                        "id": "editor",
                        "factory": "viloedit.widget:EditorWidgetFactory"
                    }
                ],
                "commands": [
                    {
                        "id": "editor.open",
                        "title": "Open File",
                        "category": "Editor"
                    },
                    {
                        "id": "editor.save",
                        "title": "Save File",
                        "category": "Editor"
                    },
                    {
                        "id": "editor.saveAs",
                        "title": "Save As...",
                        "category": "Editor"
                    },
                    {
                        "id": "editor.close",
                        "title": "Close Editor",
                        "category": "Editor"
                    }
                ],
                "languages": [
                    {
                        "id": "python",
                        "extensions": [".py", ".pyw"],
                        "aliases": ["Python", "py"]
                    },
                    {
                        "id": "javascript",
                        "extensions": [".js", ".jsx"],
                        "aliases": ["JavaScript", "js"]
                    }
                ],
                "keybindings": [
                    {
                        "command": "editor.save",
                        "key": "ctrl+s"
                    },
                    {
                        "command": "editor.open",
                        "key": "ctrl+o"
                    }
                ]
            }
        )

    def activate(self, context: IPluginContext) -> None:
        """Activate the plugin."""
        self.context = context
        logger.info("Activating ViloEdit plugin")

        # Register commands
        self._register_commands()

        # Register widget factory
        self._register_widget_factory()

        # Subscribe to events
        self._subscribe_to_events()

        # Notify activation
        notification_service = context.get_service("notification")
        if notification_service:
            notification_service.info("Editor plugin activated")

        logger.info("ViloEdit plugin activated successfully")

    def deactivate(self) -> None:
        """Deactivate the plugin."""
        logger.info("Deactivating ViloEdit plugin")

        # Close all open editors
        for editor in self.open_editors.values():
            editor.close()
        self.open_editors.clear()

        logger.info("ViloEdit plugin deactivated")

    def on_command(self, command_id: str, args: Dict[str, Any]) -> Any:
        """Handle command execution."""
        if command_id == "editor.open":
            return self._open_file(args)
        elif command_id == "editor.save":
            return self._save_file(args)
        elif command_id == "editor.saveAs":
            return self._save_file_as(args)
        elif command_id == "editor.close":
            return self._close_editor(args)

        return None

    def _register_commands(self):
        """Register editor commands."""
        command_service = self.context.get_service("command")
        if command_service:
            register_editor_commands(command_service)

    def _register_widget_factory(self):
        """Register widget factory."""
        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            workspace_service.register_widget_factory("editor", self.widget_factory)

    def _subscribe_to_events(self):
        """Subscribe to events."""
        self.context.subscribe_event(EventType.THEME_CHANGED, self._on_theme_changed)

    def _on_theme_changed(self, event):
        """Handle theme change."""
        # Update syntax highlighting colors
        for editor in self.open_editors.values():
            if hasattr(editor, 'update_theme'):
                editor.update_theme(event.data)

    def _open_file(self, args: Dict[str, Any]) -> Any:
        """Open a file in the editor."""
        file_path = args.get('path')
        if not file_path:
            # Show file dialog
            from PySide6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getOpenFileName(
                None, "Open File", "", "All Files (*.*)"
            )

        if file_path:
            # Create editor widget
            editor = self.widget_factory.create_widget()
            editor.load_file(file_path)

            # Track open editor
            self.open_editors[file_path] = editor

            # Add to workspace
            workspace_service = self.context.get_service("workspace")
            if workspace_service:
                workspace_service.add_widget(editor, Path(file_path).name, "main")

            return {"success": True, "path": file_path}

        return {"success": False, "error": "No file selected"}

    def _save_file(self, args: Dict[str, Any]) -> Any:
        """Save the current file."""
        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            editor = workspace_service.get_active_widget()
            if isinstance(editor, CodeEditor):
                if editor.save_file():
                    return {"success": True}

        return {"success": False, "error": "No active editor"}

    def _save_file_as(self, args: Dict[str, Any]) -> Any:
        """Save file with a new name."""
        from PySide6.QtWidgets import QFileDialog

        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            editor = workspace_service.get_active_widget()
            if isinstance(editor, CodeEditor):
                file_path, _ = QFileDialog.getSaveFileName(
                    None, "Save File As", "", "All Files (*.*)"
                )

                if file_path and editor.save_file(file_path):
                    return {"success": True, "path": file_path}

        return {"success": False, "error": "Save cancelled"}

    def _close_editor(self, args: Dict[str, Any]) -> Any:
        """Close the current editor."""
        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            editor = workspace_service.get_active_widget()
            if isinstance(editor, CodeEditor):
                # Check for unsaved changes
                if editor.document().isModified():
                    # Ask to save
                    from PySide6.QtWidgets import QMessageBox
                    reply = QMessageBox.question(
                        None, "Save Changes",
                        "Do you want to save changes before closing?",
                        QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                    )

                    if reply == QMessageBox.Save:
                        editor.save_file()
                    elif reply == QMessageBox.Cancel:
                        return {"success": False, "error": "Close cancelled"}

                # Remove from tracking
                if editor.file_path:
                    path_str = str(editor.file_path)
                    if path_str in self.open_editors:
                        del self.open_editors[path_str]

                # Remove from workspace
                workspace_service.remove_widget(editor)
                return {"success": True}

        return {"success": False, "error": "No active editor"}
```

### Afternoon (3 hours)

#### Task 3.2: Create Editor Widget Factory

Create `/home/kuja/GitHub/viloapp/packages/viloedit/src/viloedit/widget.py`:
```python
"""Editor widget factory."""

import logging
from typing import Optional, Dict, Any

from PySide6.QtWidgets import QWidget
from viloapp_sdk import IWidget, WidgetMetadata, WidgetPosition

from .editor import CodeEditor

logger = logging.getLogger(__name__)


class EditorWidgetFactory(IWidget):
    """Factory for creating editor widgets."""

    def get_metadata(self) -> WidgetMetadata:
        """Get widget metadata."""
        return WidgetMetadata(
            id="editor",
            title="Editor",
            position=WidgetPosition.MAIN,
            icon="file-text",
            closable=True,
            singleton=False
        )

    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """Create a new editor widget."""
        return CodeEditor(parent)

    def get_state(self) -> Dict[str, Any]:
        """Get widget state."""
        return {}

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore widget state."""
        pass
```

#### Task 3.3: Create Syntax Highlighter

Create `/home/kuja/GitHub/viloapp/packages/viloedit/src/viloedit/syntax.py`:
```python
"""Syntax highlighting for editor."""

import logging
from typing import Dict, Any

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont

logger = logging.getLogger(__name__)


class SyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter using Pygments."""

    def __init__(self, document, lexer=None):
        super().__init__(document)
        self.lexer = lexer
        self.setup_formats()

    def setup_formats(self):
        """Setup text formats for highlighting."""
        self.formats = {}

        # Keyword format
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keyword_format.setFontWeight(QFont.Bold)
        self.formats['keyword'] = keyword_format

        # String format
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.formats['string'] = string_format

        # Comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))
        comment_format.setFontItalic(True)
        self.formats['comment'] = comment_format

        # Function format
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.formats['function'] = function_format

        # Number format
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.formats['number'] = number_format

    def highlightBlock(self, text):
        """Highlight a block of text."""
        if not self.lexer:
            return

        # Use Pygments to tokenize
        from pygments import lex
        from pygments.token import Token

        tokens = lex(text, self.lexer)

        index = 0
        for token_type, token_text in tokens:
            length = len(token_text)

            # Map token type to format
            format = self.get_format_for_token(token_type)
            if format:
                self.setFormat(index, length, format)

            index += length

    def get_format_for_token(self, token_type):
        """Get format for a token type."""
        from pygments.token import Token

        if token_type in Token.Keyword:
            return self.formats['keyword']
        elif token_type in Token.String:
            return self.formats['string']
        elif token_type in Token.Comment:
            return self.formats['comment']
        elif token_type in Token.Name.Function:
            return self.formats['function']
        elif token_type in Token.Number:
            return self.formats['number']

        return None
```

### Validation Checkpoint
- [ ] Editor plugin implemented
- [ ] Widget factory created
- [ ] Syntax highlighting working
- [ ] Commands registered

## Day 4: Integration Testing

### Morning (3 hours)

#### Task 4.1: Create Plugin Tests

Create comprehensive test suites for both plugins:
```python
# Test terminal plugin integration
# Test editor plugin integration
# Test plugin interaction
# Test command execution
# Test widget creation
```

#### Task 4.2: Cross-Plugin Communication

Test that plugins can communicate:
```python
# Terminal opening files in editor
# Editor running code in terminal
# Shared workspace integration
```

### Afternoon (2 hours)

#### Task 4.3: Performance Testing

- [ ] Measure plugin loading time
- [ ] Test memory usage
- [ ] Verify no memory leaks
- [ ] Check startup performance

### Validation Checkpoint
- [ ] All tests pass
- [ ] Performance acceptable
- [ ] No regressions

## Day 5: Documentation and Polish

### Morning (3 hours)

#### Task 5.1: Complete Documentation

- Update main README
- Create plugin development guide
- Document migration process
- Create user guide

#### Task 5.2: Create Examples

- Example plugin using terminal
- Example plugin using editor
- Integration examples

### Afternoon (2 hours)

#### Task 5.3: Final Testing

- [ ] Full application test
- [ ] Plugin enable/disable
- [ ] Settings persistence
- [ ] Cross-platform testing

### Final Validation
- [ ] Both plugins working
- [ ] Full integration complete
- [ ] Documentation finished
- [ ] Ready for release

## Week 4 Summary

### Completed Deliverables
1. ✅ Terminal plugin polished with advanced features
2. ✅ Editor plugin extracted and implemented
3. ✅ Both plugins fully integrated
4. ✅ Cross-plugin communication working
5. ✅ Complete test coverage
6. ✅ Performance optimized
7. ✅ Documentation complete

### Key Achievements
- Terminal plugin with profiles, sessions, and search
- Editor plugin with syntax highlighting
- Full plugin lifecycle management
- Settings integration
- UI enhancements

### Ready for Week 5
Both major plugins are now extracted and working. Ready for:
- System integration
- Advanced features
- Plugin marketplace preparation