"""Pytest configuration and fixtures."""

import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for entire test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()


@pytest.fixture
def main_window(qtbot):
    """Create main window fixture."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    return window


@pytest.fixture
def activity_bar(main_window):
    """Get activity bar from main window."""
    return main_window.activity_bar


@pytest.fixture
def sidebar(main_window):
    """Get sidebar from main window."""
    return main_window.sidebar


@pytest.fixture
def workspace(main_window):
    """Get workspace from main window."""
    return main_window.workspace


@pytest.fixture
def status_bar(main_window):
    """Get status bar from main window."""
    return main_window.status_bar