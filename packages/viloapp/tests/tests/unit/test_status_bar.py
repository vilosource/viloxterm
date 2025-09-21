"""Unit tests for the status bar component."""

from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QLabel

from viloapp.ui.status_bar import AppStatusBar


@pytest.mark.unit
class TestAppStatusBar:
    """Test cases for AppStatusBar class."""

    def test_status_bar_initialization(self, qtbot):
        """Test status bar initializes correctly."""
        status_bar = AppStatusBar()
        qtbot.addWidget(status_bar)

        assert status_bar.objectName() == "appStatusBar"
        assert hasattr(status_bar, "status_label")
        assert hasattr(status_bar, "position_label")
        assert hasattr(status_bar, "encoding_label")

    def test_status_widgets_created(self, qtbot):
        """Test all status widgets are created."""
        status_bar = AppStatusBar()
        qtbot.addWidget(status_bar)

        # Check status label
        assert isinstance(status_bar.status_label, QLabel)
        assert status_bar.status_label.text() == "Ready"

        # Check position label
        assert isinstance(status_bar.position_label, QLabel)
        assert status_bar.position_label.text() == "Ln 1, Col 1"

        # Check encoding label
        assert isinstance(status_bar.encoding_label, QLabel)
        assert status_bar.encoding_label.text() == "UTF-8"

    def test_set_message_permanent(self, qtbot):
        """Test setting a permanent message."""
        status_bar = AppStatusBar()
        qtbot.addWidget(status_bar)

        # Set permanent message (timeout = 0)
        status_bar.set_message("File saved successfully", 0)

        # Check status label updated
        assert status_bar.status_label.text() == "File saved successfully"

    def test_set_message_with_timeout(self, qtbot):
        """Test setting a temporary message with timeout."""
        status_bar = AppStatusBar()
        qtbot.addWidget(status_bar)

        # Mock showMessage method
        status_bar.showMessage = Mock()

        # Set temporary message (timeout > 0)
        status_bar.set_message("Temporary message", 2000)

        # Check showMessage was called with correct parameters
        status_bar.showMessage.assert_called_once_with("Temporary message", 2000)

    def test_set_position(self, qtbot):
        """Test updating cursor position display."""
        status_bar = AppStatusBar()
        qtbot.addWidget(status_bar)

        # Update position
        status_bar.set_position(42, 15)

        # Check position label updated
        assert status_bar.position_label.text() == "Ln 42, Col 15"

    def test_set_position_zero_values(self, qtbot):
        """Test setting position with zero values."""
        status_bar = AppStatusBar()
        qtbot.addWidget(status_bar)

        # Update position with zeros
        status_bar.set_position(0, 0)

        # Check position label updated
        assert status_bar.position_label.text() == "Ln 0, Col 0"

    def test_set_position_large_values(self, qtbot):
        """Test setting position with large values."""
        status_bar = AppStatusBar()
        qtbot.addWidget(status_bar)

        # Update position with large numbers
        status_bar.set_position(9999, 1234)

        # Check position label updated
        assert status_bar.position_label.text() == "Ln 9999, Col 1234"

    def test_set_encoding(self, qtbot):
        """Test updating encoding display."""
        status_bar = AppStatusBar()
        qtbot.addWidget(status_bar)

        # Update encoding
        status_bar.set_encoding("UTF-16")

        # Check encoding label updated
        assert status_bar.encoding_label.text() == "UTF-16"

    def test_set_encoding_different_formats(self, qtbot):
        """Test setting various encoding formats."""
        status_bar = AppStatusBar()
        qtbot.addWidget(status_bar)

        # Test different encodings
        encodings = ["ASCII", "ISO-8859-1", "UTF-32", "Windows-1252"]

        for encoding in encodings:
            status_bar.set_encoding(encoding)
            assert status_bar.encoding_label.text() == encoding

    def test_widget_hierarchy(self, qtbot):
        """Test widgets are added to status bar correctly."""
        status_bar = AppStatusBar()
        qtbot.addWidget(status_bar)

        # Check status label is added as regular widget
        children = status_bar.children()
        assert status_bar.status_label in children

        # Check permanent widgets exist
        # Note: We can't easily test if widgets are permanent vs regular
        # in QStatusBar without more complex introspection
        assert status_bar.position_label in children
        assert status_bar.encoding_label in children

    def test_initial_state(self, qtbot):
        """Test initial state of status bar components."""
        status_bar = AppStatusBar()
        qtbot.addWidget(status_bar)

        # Check initial values
        assert status_bar.status_label.text() == "Ready"
        assert status_bar.position_label.text() == "Ln 1, Col 1"
        assert status_bar.encoding_label.text() == "UTF-8"

    def test_message_updates_dont_affect_permanent_widgets(self, qtbot):
        """Test that setting messages doesn't affect permanent widgets."""
        status_bar = AppStatusBar()
        qtbot.addWidget(status_bar)

        # Set initial values for permanent widgets
        status_bar.set_position(10, 5)
        status_bar.set_encoding("ASCII")

        # Set a message
        status_bar.set_message("New message")

        # Check permanent widgets unchanged
        assert status_bar.position_label.text() == "Ln 10, Col 5"
        assert status_bar.encoding_label.text() == "ASCII"
        assert status_bar.status_label.text() == "New message"

    def test_multiple_message_updates(self, qtbot):
        """Test multiple consecutive message updates."""
        status_bar = AppStatusBar()
        qtbot.addWidget(status_bar)

        # Set multiple messages
        messages = ["Message 1", "Message 2", "Message 3", "Final message"]

        for message in messages:
            status_bar.set_message(message)
            assert status_bar.status_label.text() == message

    def test_empty_message(self, qtbot):
        """Test setting empty message."""
        status_bar = AppStatusBar()
        qtbot.addWidget(status_bar)

        # Set empty message
        status_bar.set_message("")

        # Check message is set to empty string
        assert status_bar.status_label.text() == ""

    def test_unicode_messages(self, qtbot):
        """Test setting unicode messages and encodings."""
        status_bar = AppStatusBar()
        qtbot.addWidget(status_bar)

        # Test unicode message
        unicode_message = "操作完成 ✓"
        status_bar.set_message(unicode_message)
        assert status_bar.status_label.text() == unicode_message

        # Test unicode encoding
        unicode_encoding = "UTF-8 🔤"
        status_bar.set_encoding(unicode_encoding)
        assert status_bar.encoding_label.text() == unicode_encoding

    def test_object_name_set(self, qtbot):
        """Test object name is set for styling."""
        status_bar = AppStatusBar()
        qtbot.addWidget(status_bar)

        assert status_bar.objectName() == "appStatusBar"
