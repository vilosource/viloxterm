"""GUI test specific fixtures and configuration."""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest
from ui.main_window import MainWindow


@pytest.fixture
def mock_icon_manager():
    """Mock icon manager for GUI tests to avoid resource loading issues."""
    from PySide6.QtGui import QIcon
    
    with patch('ui.activity_bar.get_icon_manager') as mock_activity_bar, \
         patch('ui.main_window.get_icon_manager') as mock_main_window:
        
        mock_manager = Mock()
        mock_manager.theme = "light"
        # Return a real QIcon object instead of Mock to avoid QAction constructor issues
        mock_manager.get_icon.return_value = QIcon()
        mock_manager.toggle_theme = Mock()
        mock_manager.detect_system_theme = Mock()
        
        mock_activity_bar.return_value = mock_manager
        mock_main_window.return_value = mock_manager
        
        yield mock_manager


@pytest.fixture
def gui_main_window(qtbot, mock_icon_manager):
    """Create a fully initialized main window for GUI testing."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    
    # Ensure the window is fully rendered
    qtbot.wait(100)
    
    return window


@pytest.fixture
def gui_activity_bar(gui_main_window):
    """Get activity bar from GUI main window."""
    return gui_main_window.activity_bar


@pytest.fixture
def gui_sidebar(gui_main_window):
    """Get sidebar from GUI main window."""
    return gui_main_window.sidebar


@pytest.fixture
def gui_workspace(gui_main_window):
    """Get workspace from GUI main window."""
    return gui_main_window.workspace


@pytest.fixture
def gui_status_bar(gui_main_window):
    """Get status bar from GUI main window."""
    return gui_main_window.status_bar


def wait_for_condition(qtbot, condition, timeout=5000, interval=100):
    """
    Helper function to wait for a condition with better error reporting.
    
    Args:
        qtbot: pytest-qt bot
        condition: Callable that returns True when condition is met
        timeout: Maximum wait time in milliseconds
        interval: Check interval in milliseconds
    """
    def check_condition():
        try:
            return condition()
        except Exception as e:
            pytest.fail(f"Condition check failed: {e}")
    
    qtbot.waitUntil(check_condition, timeout=timeout)


def simulate_key_sequence(qtbot, widget, key_sequence):
    """
    Simulate a keyboard shortcut sequence.
    
    Args:
        qtbot: pytest-qt bot
        widget: Target widget
        key_sequence: Key sequence string (e.g., "Ctrl+T")
    """
    # Use the compatibility function for safe key sequence conversion
    from ui.qt_compat import safe_key_sequence_to_key
    
    try:
        key, modifiers = safe_key_sequence_to_key(key_sequence)
        qtbot.keyClick(widget, key, modifiers)
    except ValueError as e:
        pytest.fail(f"Failed to simulate key sequence '{key_sequence}': {e}")


def get_widget_center(widget):
    """Get the center point of a widget for clicking."""
    from PySide6.QtCore import QPoint
    rect = widget.geometry()
    return QPoint(rect.width() // 2, rect.height() // 2)