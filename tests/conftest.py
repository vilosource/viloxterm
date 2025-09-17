"""Pytest configuration and fixtures."""

import os
import warnings

import pytest

# Set test mode environment variable BEFORE importing any app modules
os.environ['VILOAPP_TEST_MODE'] = '1'
os.environ['VILOAPP_SHOW_CONFIRMATIONS'] = '0'

from PySide6.QtWidgets import QApplication

from core.app_config import app_config
from ui.main_window import MainWindow


def pytest_configure(config):
    """Configure pytest with warning filters and GUI test markers."""
    # Suppress specific warnings that occur during testing
    warnings.filterwarnings("ignore", message=".*is multi-threaded, use of forkpty.*", category=DeprecationWarning)
    warnings.filterwarnings("ignore", message=".*Release of profile requested.*", category=UserWarning)
    # Note: RuntimeError cannot be filtered as it's not a Warning subclass

    # Register custom markers for test organization
    config.addinivalue_line("markers", "gui: GUI interaction tests using pytest-qt")
    config.addinivalue_line("markers", "animation: Tests that involve animations or transitions")
    config.addinivalue_line("markers", "keyboard: Tests that involve keyboard shortcuts and input")
    config.addinivalue_line("markers", "mouse: Tests that involve mouse interactions")
    config.addinivalue_line("markers", "theme: Tests related to theme switching and visual states")
    config.addinivalue_line("markers", "slow: Slow running tests (e.g., with animations)")
    config.addinivalue_line("markers", "performance: Performance and load testing")
    config.addinivalue_line("markers", "accessibility: Accessibility and keyboard navigation tests")
    config.addinivalue_line("markers", "state: State management and persistence tests")


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for entire test session."""
    # Ensure test mode is enabled
    app_config.set_test_mode(True)
    app_config.set_show_confirmations(False)

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()


@pytest.fixture(autouse=True)
def ensure_test_mode():
    """Auto-use fixture that ensures test mode is enabled for all tests."""
    app_config.set_test_mode(True)
    app_config.set_show_confirmations(False)
    yield


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
