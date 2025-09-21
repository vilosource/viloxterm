"""Tests for terminal widget."""

import pytest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication

from viloxterm.widget import TerminalWidget, TerminalWidgetFactory


# Ensure QApplication exists for widget tests
@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_terminal_widget_creation(qapp):
    """Test terminal widget creation."""
    widget = TerminalWidget()
    assert widget is not None
    assert widget.web_view is not None


def test_terminal_widget_factory():
    """Test terminal widget factory."""
    factory = TerminalWidgetFactory()

    assert factory.get_widget_id() == "terminal"
    assert factory.get_title() == "Terminal"
    assert factory.get_icon() == "terminal"


@patch("viloxterm.widget.terminal_server")
def test_start_terminal(mock_server, qapp):
    """Test starting a terminal session."""
    widget = TerminalWidget()

    mock_server.create_session.return_value = "test-session-id"
    mock_server.get_terminal_url.return_value = "http://localhost:5000/terminal/test-session-id"

    widget.start_terminal(command="/bin/bash")

    mock_server.create_session.assert_called_once()
    assert widget.session_id == "test-session-id"


@patch("viloxterm.widget.terminal_server")
def test_stop_terminal(mock_server, qapp):
    """Test stopping a terminal session."""
    widget = TerminalWidget()
    widget.session_id = "test-session-id"

    widget.stop_terminal()

    mock_server.destroy_session.assert_called_with("test-session-id")
    assert widget.session_id is None
