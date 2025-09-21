"""Terminal UI components."""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QToolBar,
    QComboBox, QLineEdit, QTabWidget
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QKeySequence, QAction

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