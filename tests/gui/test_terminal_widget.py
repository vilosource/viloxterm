#!/usr/bin/env python3
"""
Test Terminal Widget - Comprehensive tests for terminal widget functionality.

This test suite validates the TerminalWidget class following Test Monkey principles:
- Test session lifecycle (create, ready, close)
- Test input/output operations
- Test signal emissions (terminal_closed, ready)
- Test cleanup and resource management
- Test error handling and edge cases
- Test widget state management
- Test theme management

Uses qtbot for Qt testing and proper mocking of external dependencies.
"""

import warnings
from unittest.mock import Mock, patch

import pytest
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QLabel, QVBoxLayout

from ui.terminal.terminal_config import (
    VSCODE_DARK_THEME,
    TerminalConfig,
)
from ui.terminal.terminal_widget import TerminalWebPage, TerminalWidget


class TestTerminalWebPage:
    """Test TerminalWebPage custom functionality."""

    def test_terminal_web_page_logs_javascript_error_messages(self, qtbot):
        """Test that TerminalWebPage logs JavaScript error messages."""
        # ARRANGE - Create web page (no need to add to qtbot since it's not a widget)
        web_page = TerminalWebPage()

        # ACT & ASSERT - Test error logging
        with patch("ui.terminal.terminal_widget.logger") as mock_logger:
            web_page.javaScriptConsoleMessage(
                QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel,
                "Test error message",
                42,
                "test.js",
            )

            mock_logger.error.assert_called_once_with(
                "JS Error: Test error message (line 42 in test.js)"
            )

    def test_terminal_web_page_logs_javascript_warning_messages(self, qtbot):
        """Test that TerminalWebPage logs JavaScript warning messages."""
        # ARRANGE - Create web page (no need to add to qtbot since it's not a widget)
        web_page = TerminalWebPage()

        # ACT & ASSERT - Test warning logging
        with patch("ui.terminal.terminal_widget.logger") as mock_logger:
            web_page.javaScriptConsoleMessage(
                QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel,
                "Test warning",
                0,
                "",
            )

            mock_logger.warning.assert_called_once_with("JS Warning: Test warning")

    def test_terminal_web_page_logs_javascript_debug_messages(self, qtbot):
        """Test that TerminalWebPage logs JavaScript debug messages."""
        # ARRANGE - Create web page (no need to add to qtbot since it's not a widget)
        web_page = TerminalWebPage()

        # ACT & ASSERT - Test debug logging
        with patch("ui.terminal.terminal_widget.logger") as mock_logger:
            web_page.javaScriptConsoleMessage(
                QWebEnginePage.JavaScriptConsoleMessageLevel.InfoMessageLevel,
                "Test info",
                0,
                "",
            )

            mock_logger.debug.assert_called_once_with("JS: Test info")


class TestTerminalWidget:
    """Test TerminalWidget functionality."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Setup common mocks for terminal widget tests."""
        # Mock terminal server
        self.mock_terminal_server = Mock()
        self.mock_terminal_server.create_session.return_value = "test_session_123"
        self.mock_terminal_server.get_session_url.return_value = (
            "http://localhost:8000/terminal/test_session_123"
        )

        # Mock terminal config
        self.mock_config = Mock(spec=TerminalConfig)
        self.mock_config.get_shell_command.return_value = "/bin/bash"
        self.mock_config.shell_args = ""
        self.mock_config.get_color_scheme.return_value = VSCODE_DARK_THEME
        self.mock_config.font_size = 16
        self.mock_config.font_family = "Consolas"
        self.mock_config.line_height = 1.2

        # Patch the terminal server import
        with patch(
            "ui.terminal.terminal_widget.terminal_server", self.mock_terminal_server
        ):
            with patch("ui.terminal.terminal_widget.terminal_config", self.mock_config):
                yield

    def test_terminal_widget_creation_shows_deprecation_warning(self, qtbot):
        """Test that TerminalWidget shows deprecation warning on creation."""
        # ARRANGE & ACT - Create widget and capture warnings
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")

            widget = TerminalWidget()
            qtbot.addWidget(widget)

        # ASSERT - Deprecation warning was shown
        assert len(warning_list) == 1
        assert issubclass(warning_list[0].category, DeprecationWarning)
        assert "TerminalWidget is deprecated" in str(warning_list[0].message)
        assert "TerminalAppWidget" in str(warning_list[0].message)

    def test_terminal_widget_initializes_with_default_config(self, qtbot):
        """Test that TerminalWidget initializes with default configuration."""
        # ARRANGE & ACT - Create widget
        widget = TerminalWidget()
        qtbot.addWidget(widget)

        # ASSERT - Widget initialized correctly
        assert widget.config == self.mock_config
        assert widget.command == "/bin/bash"
        assert widget.args == ""
        assert widget.session_id == "test_session_123"
        assert widget.is_ready is False
        assert widget.is_dark_theme is True
        assert widget.web_view is not None
        assert isinstance(widget.web_view, QWebEngineView)

    def test_terminal_widget_initializes_with_custom_config(self, qtbot):
        """Test that TerminalWidget initializes with custom configuration."""
        # ARRANGE - Create custom config
        custom_config = Mock(spec=TerminalConfig)
        custom_config.get_shell_command.return_value = "/bin/zsh"
        custom_config.shell_args = "-l"

        # ACT - Create widget with custom config
        widget = TerminalWidget(
            config=custom_config, command="/usr/bin/fish", args="--login"
        )
        qtbot.addWidget(widget)

        # ASSERT - Widget uses custom settings
        assert widget.config == custom_config
        assert widget.command == "/usr/bin/fish"
        assert widget.args == "--login"

    def test_terminal_widget_creates_session_on_initialization(self, qtbot):
        """Test that TerminalWidget creates terminal session on initialization."""
        # ARRANGE & ACT - Create widget
        widget = TerminalWidget()
        qtbot.addWidget(widget)

        # ASSERT - Session was created
        self.mock_terminal_server.create_session.assert_called_once_with(
            command="/bin/bash", cmd_args=""
        )
        self.mock_terminal_server.get_session_url.assert_called_once_with(
            "test_session_123"
        )

    def test_terminal_widget_loads_session_url_in_web_view(self, qtbot):
        """Test that TerminalWidget loads session URL in web view."""
        # ARRANGE - Mock web view load method
        with patch.object(QWebEngineView, "load") as mock_load:
            # ACT - Create widget
            widget = TerminalWidget()
            qtbot.addWidget(widget)

            # ASSERT - Web view loaded with correct URL
            mock_load.assert_called_once()
            loaded_url = mock_load.call_args[0][0]
            assert isinstance(loaded_url, QUrl)
            assert (
                loaded_url.toString()
                == "http://localhost:8000/terminal/test_session_123"
            )

    def test_terminal_widget_web_view_load_finished_success_emits_ready_signal(
        self, qtbot
    ):
        """Test that web view load finished success emits ready signal."""
        # ARRANGE - Create widget and connect signal
        widget = TerminalWidget()
        qtbot.addWidget(widget)

        # ACT & ASSERT - Simulate successful load
        with qtbot.waitSignal(widget.ready, timeout=1000):
            widget._on_load_finished(True)

        # ASSERT - Widget is ready
        assert widget.is_ready is True

    def test_terminal_widget_web_view_load_finished_failure_shows_error(self, qtbot):
        """Test that web view load finished failure shows error message."""
        # ARRANGE - Create widget
        widget = TerminalWidget()
        qtbot.addWidget(widget)

        # ACT - Simulate failed load
        widget._on_load_finished(False)

        # ASSERT - Error message displayed
        layout = widget.layout()
        error_widgets = [
            layout.itemAt(i).widget()
            for i in range(layout.count())
            if isinstance(layout.itemAt(i).widget(), QLabel)
        ]

        assert len(error_widgets) > 0
        error_label = error_widgets[-1]  # Last added widget should be error
        assert "Failed to load terminal interface" in error_label.text()
        assert widget.is_ready is False

    def test_terminal_widget_applies_theme_on_load_finished(self, qtbot):
        """Test that terminal widget applies theme on successful load."""
        # ARRANGE - Create widget and mock JavaScript execution
        widget = TerminalWidget()
        qtbot.addWidget(widget)

        # Mock the web page runJavaScript method
        mock_run_js = Mock()
        widget.web_view.page().runJavaScript = mock_run_js

        # ACT - Simulate successful load
        widget._on_load_finished(True)

        # ASSERT - Theme JavaScript was executed
        mock_run_js.assert_called()
        js_call = mock_run_js.call_args[0][0]
        assert "term.setOption('theme'" in js_call
        assert "background" in js_call
        assert "foreground" in js_call

    def test_terminal_widget_focus_terminal_sets_focus_and_runs_javascript(self, qtbot):
        """Test that focus_terminal sets focus and runs JavaScript."""
        # ARRANGE - Create widget
        widget = TerminalWidget()
        qtbot.addWidget(widget)

        # Mock methods
        mock_set_focus = Mock()
        mock_run_js = Mock()
        widget.web_view.setFocus = mock_set_focus
        widget.web_view.page().runJavaScript = mock_run_js

        # ACT - Focus terminal
        widget.focus_terminal()

        # ASSERT - Focus was set and JavaScript executed
        mock_set_focus.assert_called_once()
        mock_run_js.assert_called_once_with(
            "if (typeof term !== 'undefined') { term.focus(); }"
        )

    def test_terminal_widget_clear_terminal_runs_javascript_when_ready(self, qtbot):
        """Test that clear_terminal runs JavaScript when terminal is ready."""
        # ARRANGE - Create widget and mark as ready
        widget = TerminalWidget()
        qtbot.addWidget(widget)
        widget.is_ready = True

        # Mock JavaScript execution
        mock_run_js = Mock()
        widget.web_view.page().runJavaScript = mock_run_js

        # ACT - Clear terminal
        widget.clear_terminal()

        # ASSERT - Clear JavaScript was executed
        mock_run_js.assert_called_once_with(
            "if (typeof term !== 'undefined') { term.clear(); }"
        )

    def test_terminal_widget_clear_terminal_does_nothing_when_not_ready(self, qtbot):
        """Test that clear_terminal does nothing when terminal is not ready."""
        # ARRANGE - Create widget (not ready by default)
        widget = TerminalWidget()
        qtbot.addWidget(widget)

        # Mock JavaScript execution
        mock_run_js = Mock()
        widget.web_view.page().runJavaScript = mock_run_js

        # ACT - Clear terminal
        widget.clear_terminal()

        # ASSERT - No JavaScript was executed
        mock_run_js.assert_not_called()

    def test_terminal_widget_reset_terminal_runs_javascript_when_ready(self, qtbot):
        """Test that reset_terminal runs JavaScript when terminal is ready."""
        # ARRANGE - Create widget and mark as ready
        widget = TerminalWidget()
        qtbot.addWidget(widget)
        widget.is_ready = True

        # Mock JavaScript execution
        mock_run_js = Mock()
        widget.web_view.page().runJavaScript = mock_run_js

        # ACT - Reset terminal
        widget.reset_terminal()

        # ASSERT - Reset JavaScript was executed
        mock_run_js.assert_called_once_with(
            "if (typeof term !== 'undefined') { term.reset(); }"
        )

    def test_terminal_widget_write_to_terminal_escapes_text_correctly(self, qtbot):
        """Test that write_to_terminal properly escapes text for JavaScript."""
        # ARRANGE - Create widget and mark as ready
        widget = TerminalWidget()
        qtbot.addWidget(widget)
        widget.is_ready = True

        # Mock JavaScript execution
        mock_run_js = Mock()
        widget.web_view.page().runJavaScript = mock_run_js

        # ACT - Write text with special characters
        test_text = "Hello 'world'\nNew line\\backslash"
        widget.write_to_terminal(test_text)

        # ASSERT - Text was properly escaped
        mock_run_js.assert_called_once()
        js_call = mock_run_js.call_args[0][0]
        assert "term.write('Hello \\'world\\'\\nNew line\\\\backslash')" in js_call

    def test_terminal_widget_write_to_terminal_handles_none_input(self, qtbot):
        """Test that write_to_terminal handles None input gracefully."""
        # ARRANGE - Create widget and mark as ready
        widget = TerminalWidget()
        qtbot.addWidget(widget)
        widget.is_ready = True

        # Mock JavaScript execution
        mock_run_js = Mock()
        widget.web_view.page().runJavaScript = mock_run_js

        # ACT - Write None text
        widget.write_to_terminal(None)

        # ASSERT - No JavaScript was executed
        mock_run_js.assert_not_called()

    def test_terminal_widget_paste_to_terminal_escapes_text_correctly(self, qtbot):
        """Test that paste_to_terminal properly escapes text for JavaScript."""
        # ARRANGE - Create widget and mark as ready
        widget = TerminalWidget()
        qtbot.addWidget(widget)
        widget.is_ready = True

        # Mock JavaScript execution
        mock_run_js = Mock()
        widget.web_view.page().runJavaScript = mock_run_js

        # ACT - Paste text with special characters
        test_text = "paste 'content'\\backslash"
        widget.paste_to_terminal(test_text)

        # ASSERT - Text was properly escaped
        mock_run_js.assert_called_once()
        js_call = mock_run_js.call_args[0][0]
        assert "term.paste('paste \\'content\\'\\\\backslash')" in js_call

    def test_terminal_widget_set_theme_applies_dark_theme(self, qtbot):
        """Test that set_theme applies dark theme correctly."""
        # ARRANGE - Create widget and mark as ready
        widget = TerminalWidget()
        qtbot.addWidget(widget)
        widget.is_ready = True

        # Mock JavaScript execution
        mock_run_js = Mock()
        widget.web_view.page().runJavaScript = mock_run_js

        # ACT - Set dark theme
        widget.set_theme(True)

        # ASSERT - Dark theme was applied
        assert widget.is_dark_theme is True
        self.mock_config.get_color_scheme.assert_called_with(True)
        mock_run_js.assert_called_once()

    def test_terminal_widget_set_theme_applies_light_theme(self, qtbot):
        """Test that set_theme applies light theme correctly."""
        # ARRANGE - Create widget and mark as ready
        widget = TerminalWidget()
        qtbot.addWidget(widget)
        widget.is_ready = True

        # Mock JavaScript execution
        mock_run_js = Mock()
        widget.web_view.page().runJavaScript = mock_run_js

        # ACT - Set light theme
        widget.set_theme(False)

        # ASSERT - Light theme was applied
        assert widget.is_dark_theme is False
        self.mock_config.get_color_scheme.assert_called_with(False)
        mock_run_js.assert_called_once()

    def test_terminal_widget_get_session_id_returns_correct_id(self, qtbot):
        """Test that get_session_id returns correct session ID."""
        # ARRANGE - Create widget
        widget = TerminalWidget()
        qtbot.addWidget(widget)

        # ACT - Get session ID
        session_id = widget.get_session_id()

        # ASSERT - Correct session ID returned
        assert session_id == "test_session_123"

    def test_terminal_widget_get_state_returns_serializable_state(self, qtbot):
        """Test that get_state returns serializable state dictionary."""
        # ARRANGE - Create widget with custom settings
        widget = TerminalWidget(command="/bin/zsh", args="--login")
        qtbot.addWidget(widget)
        widget.is_dark_theme = False

        # ACT - Get state
        state = widget.get_state()

        # ASSERT - State contains expected values
        assert isinstance(state, dict)
        assert state["session_id"] == "test_session_123"
        assert state["command"] == "/bin/zsh"
        assert state["args"] == "--login"
        assert state["is_dark_theme"] is False

    def test_terminal_widget_restore_state_recreates_session(self, qtbot):
        """Test that restore_state recreates session with restored settings."""
        # ARRANGE - Create widget
        widget = TerminalWidget()
        qtbot.addWidget(widget)

        # Mock close_terminal to avoid actual server calls
        widget.close_terminal = Mock()

        # Prepare state to restore
        state = {
            "command": "/bin/fish",
            "args": "--interactive",
            "is_dark_theme": False,
        }

        # ACT - Restore state
        widget.restore_state(state)

        # ASSERT - State was restored
        assert widget.command == "/bin/fish"
        assert widget.args == "--interactive"
        assert widget.is_dark_theme is False
        widget.close_terminal.assert_called_once()

    def test_terminal_widget_close_terminal_destroys_session_and_emits_signal(
        self, qtbot
    ):
        """Test that close_terminal destroys session and emits terminal_closed signal."""
        # ARRANGE - Create widget
        widget = TerminalWidget()
        qtbot.addWidget(widget)

        # ACT & ASSERT - Close terminal and wait for signal
        with qtbot.waitSignal(widget.terminal_closed, timeout=1000) as blocker:
            widget.close_terminal()

        # ASSERT - Session was destroyed and signal emitted
        self.mock_terminal_server.destroy_session.assert_called_once_with(
            "test_session_123"
        )
        assert blocker.args[0] == "test_session_123"
        assert widget.session_id is None

    def test_terminal_widget_close_terminal_handles_no_session(self, qtbot):
        """Test that close_terminal handles case where no session exists."""
        # ARRANGE - Create widget and clear session
        widget = TerminalWidget()
        qtbot.addWidget(widget)

        # Reset the mock to have a clean call count
        self.mock_terminal_server.destroy_session.reset_mock()
        widget.session_id = None

        # ACT - Close terminal (should not raise)
        widget.close_terminal()

        # ASSERT - No server calls were made
        assert self.mock_terminal_server.destroy_session.call_count == 0

    def test_terminal_widget_close_event_calls_close_terminal(self, qtbot):
        """Test that closeEvent calls close_terminal for cleanup."""
        # ARRANGE - Create widget
        widget = TerminalWidget()
        qtbot.addWidget(widget)

        # Mock close_terminal to verify it's called
        widget.close_terminal = Mock()

        # Create a close event
        from PySide6.QtGui import QCloseEvent

        close_event = QCloseEvent()

        # ACT - Call closeEvent
        widget.closeEvent(close_event)

        # ASSERT - close_terminal was called
        widget.close_terminal.assert_called_once()

    def test_terminal_widget_destructor_cleanup_handles_exceptions(self, qtbot):
        """Test that destructor cleanup handles exceptions gracefully."""
        # ARRANGE - Create widget
        widget = TerminalWidget()
        qtbot.addWidget(widget)

        # Mock the terminal server to raise an exception during cleanup
        original_destroy = self.mock_terminal_server.destroy_session
        self.mock_terminal_server.destroy_session = Mock(
            side_effect=RuntimeError("Server error")
        )

        # ACT & ASSERT - Destructor should not raise exceptions
        try:
            widget.__del__()
        except Exception as e:
            pytest.fail(f"Destructor raised exception: {e}")
        finally:
            # Reset the mock for other tests
            self.mock_terminal_server.destroy_session = original_destroy

    def test_terminal_widget_error_handling_during_session_creation(self, qtbot):
        """Test that terminal widget handles errors during session creation."""
        # ARRANGE - Create fresh mocks for this test to avoid interference
        with patch("ui.terminal.terminal_widget.terminal_server") as mock_server:
            with patch("ui.terminal.terminal_widget.terminal_config") as mock_config:
                # Setup mocks
                mock_config.get_shell_command.return_value = "/bin/bash"
                mock_config.shell_args = ""
                mock_server.create_session.side_effect = RuntimeError(
                    "Server not available"
                )

                # ACT - Create widget (should not crash)
                widget = TerminalWidget()
                qtbot.addWidget(widget)

                # ASSERT - Error was handled gracefully
                assert widget.session_id is None

                # Should show error message in layout
                layout = widget.layout()
                error_widgets = [
                    layout.itemAt(i).widget()
                    for i in range(layout.count())
                    if isinstance(layout.itemAt(i).widget(), QLabel)
                ]

                assert len(error_widgets) > 0
                error_label = error_widgets[-1]
                assert "Failed to start terminal" in error_label.text()

    def test_terminal_widget_minimum_size_is_set(self, qtbot):
        """Test that terminal widget has minimum size set."""
        # ARRANGE & ACT - Create widget
        widget = TerminalWidget()
        qtbot.addWidget(widget)

        # ASSERT - Minimum size is set
        assert widget.minimumSize().width() == 400
        assert widget.minimumSize().height() == 300

    def test_terminal_widget_web_view_configuration(self, qtbot):
        """Test that web view is configured correctly."""
        # ARRANGE & ACT - Create widget
        widget = TerminalWidget()
        qtbot.addWidget(widget)

        # ASSERT - Web view configuration
        assert widget.web_view.contextMenuPolicy() == Qt.NoContextMenu
        assert widget.web_view.focusPolicy() == Qt.StrongFocus
        assert isinstance(widget.web_view.page(), TerminalWebPage)

    def test_terminal_widget_layout_configuration(self, qtbot):
        """Test that widget layout is configured correctly."""
        # ARRANGE & ACT - Create widget
        widget = TerminalWidget()
        qtbot.addWidget(widget)

        # ASSERT - Layout configuration
        layout = widget.layout()
        assert isinstance(layout, QVBoxLayout)
        assert layout.contentsMargins().left() == 0
        assert layout.contentsMargins().top() == 0
        assert layout.contentsMargins().right() == 0
        assert layout.contentsMargins().bottom() == 0
        assert layout.spacing() == 0


class TestTerminalWidgetEdgeCases:
    """Test edge cases and error conditions for TerminalWidget."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Setup mocks for edge case tests."""
        self.mock_terminal_server = Mock()
        self.mock_config = Mock(spec=TerminalConfig)

        with patch(
            "ui.terminal.terminal_widget.terminal_server", self.mock_terminal_server
        ):
            with patch("ui.terminal.terminal_widget.terminal_config", self.mock_config):
                yield

    @pytest.mark.parametrize(
        "command,args,expected_command,expected_args",
        [
            (None, None, "mock_shell", ""),
            ("", "", "mock_shell", ""),
            ("/custom/shell", "", "/custom/shell", ""),
            (None, "--login", "mock_shell", "--login"),
            ("/bin/zsh", "-l --interactive", "/bin/zsh", "-l --interactive"),
        ],
    )
    def test_terminal_widget_handles_various_command_configurations(
        self, qtbot, command, args, expected_command, expected_args
    ):
        """Test terminal widget handles various command configurations."""
        # ARRANGE - Setup mock to return specific shell
        self.mock_config.get_shell_command.return_value = "mock_shell"
        self.mock_config.shell_args = ""
        self.mock_terminal_server.create_session.return_value = "test_session"
        self.mock_terminal_server.get_session_url.return_value = "http://test"

        # ACT - Create widget with various configurations
        widget = TerminalWidget(command=command, args=args)
        qtbot.addWidget(widget)

        # ASSERT - Widget uses expected command and args
        assert widget.command == expected_command
        assert widget.args == expected_args

    @pytest.mark.parametrize(
        "text_input",
        [
            "",  # Empty string
            "simple text",  # Normal text
            "text with 'quotes'",  # Single quotes
            'text with "double quotes"',  # Double quotes
            "text with\nnewlines\n",  # Newlines
            "text with\\backslashes\\",  # Backslashes
            "complex 'text' with \"quotes\" and\nnewlines\\backslashes",  # Complex
            "unicode: ñáéíóú 🚀 💻",  # Unicode characters
        ],
    )
    def test_terminal_widget_handles_various_text_inputs(self, qtbot, text_input):
        """Test terminal widget handles various text inputs correctly."""
        # ARRANGE - Create widget and mark as ready
        self.mock_config.get_shell_command.return_value = "bash"
        self.mock_terminal_server.create_session.return_value = "test_session"
        self.mock_terminal_server.get_session_url.return_value = "http://test"

        widget = TerminalWidget()
        qtbot.addWidget(widget)
        widget.is_ready = True

        # Mock JavaScript execution
        mock_run_js = Mock()
        widget.web_view.page().runJavaScript = mock_run_js

        # ACT - Write text to terminal
        widget.write_to_terminal(text_input)

        # ASSERT - JavaScript was called (we don't validate exact escaping here)
        if text_input is not None:
            mock_run_js.assert_called_once()
            js_call = mock_run_js.call_args[0][0]
            assert "term.write(" in js_call
        else:
            mock_run_js.assert_not_called()

    def test_terminal_widget_web_view_creation_failure_raises_exception(self, qtbot):
        """Test terminal widget raises exception when web view creation fails."""
        # ARRANGE - Mock terminal server and config, then mock QWebEngineView to raise exception
        with patch("ui.terminal.terminal_widget.terminal_server") as mock_server:
            with patch("ui.terminal.terminal_widget.terminal_config") as mock_config:
                mock_config.get_shell_command.return_value = "/bin/bash"
                mock_config.shell_args = ""
                mock_server.create_session.return_value = "test_session"
                mock_server.get_session_url.return_value = "http://test"

                with patch(
                    "ui.terminal.terminal_widget.QWebEngineView",
                    side_effect=RuntimeError("Web engine not available"),
                ):
                    # ACT & ASSERT - Widget creation should raise the web engine exception
                    with pytest.raises(RuntimeError, match="Web engine not available"):
                        widget = TerminalWidget()
                        qtbot.addWidget(widget)

    def test_terminal_widget_handles_theme_application_when_not_ready(self, qtbot):
        """Test that theme application is skipped when terminal is not ready."""
        # ARRANGE - Create widget (not ready by default)
        self.mock_config.get_shell_command.return_value = "bash"
        self.mock_terminal_server.create_session.return_value = "test_session"
        self.mock_terminal_server.get_session_url.return_value = "http://test"

        widget = TerminalWidget()
        qtbot.addWidget(widget)

        # Ensure it's not ready
        widget.is_ready = False

        # Mock JavaScript execution
        mock_run_js = Mock()
        widget.web_view.page().runJavaScript = mock_run_js

        # ACT - Try to apply theme
        widget._apply_theme()

        # ASSERT - No JavaScript was executed
        mock_run_js.assert_not_called()

    def test_terminal_widget_handles_missing_web_view_during_operations(self, qtbot):
        """Test terminal widget handles missing web view during operations."""
        # ARRANGE - Create widget and remove web view
        self.mock_config.get_shell_command.return_value = "bash"
        self.mock_terminal_server.create_session.return_value = "test_session"
        self.mock_terminal_server.get_session_url.return_value = "http://test"

        widget = TerminalWidget()
        qtbot.addWidget(widget)
        widget.is_ready = True
        widget.web_view = None  # Simulate missing web view

        # ACT & ASSERT - Operations should not crash
        try:
            widget.focus_terminal()
            widget.clear_terminal()
            widget.reset_terminal()
            widget.write_to_terminal("test")
            widget.paste_to_terminal("test")
            widget._apply_theme()
        except AttributeError as e:
            pytest.fail(f"Operations should handle missing web view: {e}")


@pytest.mark.integration
class TestTerminalWidgetIntegration:
    """Integration tests for TerminalWidget with real dependencies."""

    def test_terminal_widget_with_real_config(self, qtbot):
        """Test terminal widget works with real terminal configuration."""
        # ARRANGE - Import real config
        from ui.terminal.terminal_config import terminal_config

        # Mock only the server to avoid actual server startup
        with patch("ui.terminal.terminal_widget.terminal_server") as mock_server:
            mock_server.create_session.return_value = "integration_test_session"
            mock_server.get_session_url.return_value = (
                "http://localhost:8080/terminal/integration_test_session"
            )

            # ACT - Create widget with real config
            widget = TerminalWidget(config=terminal_config)
            qtbot.addWidget(widget)

            # ASSERT - Widget was created successfully
            assert widget.config == terminal_config
            assert widget.command == terminal_config.get_shell_command()
            assert widget.session_id == "integration_test_session"

    def test_terminal_widget_color_scheme_integration(self, qtbot):
        """Test terminal widget integrates correctly with color schemes."""
        # ARRANGE - Create widget with real color schemes
        with patch("ui.terminal.terminal_widget.terminal_server") as mock_server:
            mock_server.create_session.return_value = "color_test_session"
            mock_server.get_session_url.return_value = (
                "http://localhost:8080/terminal/color_test_session"
            )

            widget = TerminalWidget()
            qtbot.addWidget(widget)
            widget.is_ready = True

            # Mock JavaScript execution to capture theme data
            theme_js_calls = []

            def capture_js(js_code):
                theme_js_calls.append(js_code)

            widget.web_view.page().runJavaScript = capture_js

            # ACT - Apply both themes
            widget.set_theme(True)  # Dark theme
            widget.set_theme(False)  # Light theme

            # ASSERT - Both themes were applied
            assert len(theme_js_calls) == 2

            # Check dark theme contains expected colors
            dark_js = theme_js_calls[0]
            assert "background: '#1e1e1e'" in dark_js or "#1e1e1e" in dark_js

            # Check light theme contains expected colors
            light_js = theme_js_calls[1]
            assert "background: '#ffffff'" in light_js or "#ffffff" in light_js
