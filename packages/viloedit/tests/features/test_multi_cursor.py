"""Tests for multi-cursor functionality."""

import pytest
from unittest.mock import Mock, patch

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QTextCursor, QKeyEvent
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False

from viloedit.features.multi_cursor import MultiCursor, CursorInfo


class TestCursorInfo:
    """Test CursorInfo class."""

    def test_initialization(self):
        """Test cursor info initialization."""
        cursor = CursorInfo(10)
        assert cursor.position == 10
        assert cursor.anchor == 10
        assert not cursor.has_selection

        cursor_with_selection = CursorInfo(10, 5)
        assert cursor_with_selection.position == 10
        assert cursor_with_selection.anchor == 5
        assert cursor_with_selection.has_selection

    def test_selection_properties(self):
        """Test selection properties."""
        cursor = CursorInfo(15, 5)  # Selection from 5 to 15

        assert cursor.has_selection
        assert cursor.selection_start == 5
        assert cursor.selection_end == 15

        # Test reverse selection
        cursor_reverse = CursorInfo(5, 15)  # Selection from 5 to 15 (same range)
        assert cursor_reverse.selection_start == 5
        assert cursor_reverse.selection_end == 15

    def test_selection_text(self):
        """Test getting selection text."""
        document_text = "Hello, World!"
        cursor = CursorInfo(7, 0)  # Select "Hello, "

        assert cursor.selection_text(document_text) == "Hello, "

        # Test no selection
        cursor_no_selection = CursorInfo(7)
        assert cursor_no_selection.selection_text(document_text) == ""


@pytest.mark.skipif(not QT_AVAILABLE, reason="Qt not available")
class TestMultiCursor:
    """Test multi-cursor functionality."""

    @classmethod
    def setup_class(cls):
        """Setup Qt application."""
        if not QApplication.instance():
            cls.app = QApplication([])

    def setup_method(self):
        """Setup test environment."""
        # Create multi-cursor without editor first to avoid shortcut issues
        self.multi_cursor = MultiCursor()
        self.mock_editor = Mock()

        # Mock the editor methods that might be called
        self.mock_text_cursor = Mock()
        self.mock_text_cursor.position.return_value = 0
        self.mock_text_cursor.anchor.return_value = 0
        self.mock_text_cursor.setPosition = Mock()

        self.mock_editor.textCursor = Mock(return_value=self.mock_text_cursor)
        self.mock_editor.setTextCursor = Mock()
        self.mock_editor.setExtraSelections = Mock()
        self.mock_editor.document = Mock()

        # Don't call setup_editor_integration in tests to avoid Qt widget issues
        self.multi_cursor.editor = self.mock_editor

        # Patch visual indicators method to avoid Qt issues
        self.multi_cursor.update_visual_indicators = Mock()
        self.multi_cursor.clear_visual_indicators = Mock()

        # Patch text manipulation methods to avoid Qt document issues
        self.multi_cursor.insert_text = Mock()
        self.multi_cursor.delete_selected_text = Mock()
        self.multi_cursor.delete_before_cursors = Mock()
        self.multi_cursor.delete_after_cursors = Mock()

    def teardown_method(self):
        """Cleanup test environment."""
        if hasattr(self.multi_cursor, 'clear_cursors'):
            self.multi_cursor.clear_cursors()

    def test_initialization(self):
        """Test multi-cursor initialization."""
        assert self.multi_cursor.editor == self.mock_editor
        assert self.multi_cursor.cursors == []
        assert self.multi_cursor.primary_cursor_index == 0
        assert self.multi_cursor.enabled is True

    def test_is_active(self):
        """Test is_active property."""
        # Not active with no cursors
        assert not self.multi_cursor.is_active()

        # Not active with one cursor
        self.multi_cursor.cursors = [CursorInfo(10)]
        assert not self.multi_cursor.is_active()

        # Active with multiple cursors
        self.multi_cursor.cursors = [CursorInfo(10), CursorInfo(20)]
        assert self.multi_cursor.is_active()

        # Not active when disabled
        self.multi_cursor.enabled = False
        assert not self.multi_cursor.is_active()

    def test_add_cursor_at_position(self):
        """Test adding cursor at position."""
        # Add first cursor
        result = self.multi_cursor.add_cursor_at_position(10)
        assert result is True
        assert len(self.multi_cursor.cursors) == 1
        assert self.multi_cursor.cursors[0].position == 10

        # Add second cursor
        result = self.multi_cursor.add_cursor_at_position(20)
        assert result is True
        assert len(self.multi_cursor.cursors) == 2

        # Try to add duplicate cursor
        result = self.multi_cursor.add_cursor_at_position(10)
        assert result is False
        assert len(self.multi_cursor.cursors) == 2

        # Test when disabled
        self.multi_cursor.enabled = False
        result = self.multi_cursor.add_cursor_at_position(30)
        assert result is False

    def test_get_primary_cursor(self):
        """Test getting primary cursor."""
        # No cursors
        assert self.multi_cursor.get_primary_cursor() is None

        # Add cursors
        self.multi_cursor.add_cursor_at_position(10)
        self.multi_cursor.add_cursor_at_position(20)

        primary = self.multi_cursor.get_primary_cursor()
        assert primary is not None
        assert primary.position == 10

    def test_clear_cursors(self):
        """Test clearing all cursors."""
        # Add some cursors
        self.multi_cursor.add_cursor_at_position(10)
        self.multi_cursor.add_cursor_at_position(20)
        assert len(self.multi_cursor.cursors) == 2

        # Clear cursors
        self.multi_cursor.clear_cursors()
        assert len(self.multi_cursor.cursors) == 0

    def test_cursor_count_and_positions(self):
        """Test getting cursor count and positions."""
        assert self.multi_cursor.get_cursor_count() == 0
        assert self.multi_cursor.get_cursor_positions() == []

        # Add cursors
        self.multi_cursor.add_cursor_at_position(10)
        self.multi_cursor.add_cursor_at_position(20)
        self.multi_cursor.add_cursor_at_position(5)

        assert self.multi_cursor.get_cursor_count() == 3
        # Should be sorted by position
        positions = self.multi_cursor.get_cursor_positions()
        assert positions == [5, 10, 20]

    def test_set_enabled(self):
        """Test enabling/disabling multi-cursor."""
        # Add cursors
        self.multi_cursor.add_cursor_at_position(10)
        self.multi_cursor.add_cursor_at_position(20)
        assert self.multi_cursor.is_active()

        # Disable
        self.multi_cursor.set_enabled(False)
        assert not self.multi_cursor.enabled
        assert not self.multi_cursor.is_active()
        assert len(self.multi_cursor.cursors) == 0  # Should clear cursors

        # Re-enable
        self.multi_cursor.set_enabled(True)
        assert self.multi_cursor.enabled

    @patch('viloedit.features.multi_cursor.QShortcut')
    def test_setup_editor_integration(self, mock_shortcut):
        """Test editor integration setup."""
        multi_cursor = MultiCursor()
        # Create a mock editor that behaves like a QWidget
        mock_editor = Mock()
        multi_cursor.set_editor(mock_editor)

        # Should have created shortcuts
        assert mock_shortcut.call_count > 0

    def test_handle_key_press_text_input(self):
        """Test handling text input in multi-cursor mode."""
        # Setup multi-cursor mode
        self.multi_cursor.add_cursor_at_position(10)
        self.multi_cursor.add_cursor_at_position(20)

        # Mock key event for text input
        mock_event = Mock()
        mock_event.text.return_value = "a"
        mock_event.key.return_value = Qt.Key_A
        mock_event.modifiers.return_value = Qt.NoModifier

        # Reset the mock since it was set in setup
        self.multi_cursor.insert_text.reset_mock()

        # Should handle the event in multi-cursor mode
        result = self.multi_cursor.handle_key_press(mock_event)
        assert result is True
        self.multi_cursor.insert_text.assert_called_with("a")

    def test_handle_key_press_backspace(self):
        """Test handling backspace in multi-cursor mode."""
        # Setup multi-cursor mode
        self.multi_cursor.add_cursor_at_position(10)
        self.multi_cursor.add_cursor_at_position(20)

        # Mock key event for backspace
        mock_event = Mock()
        mock_event.text.return_value = ""  # Backspace has empty text
        mock_event.key.return_value = Qt.Key_Backspace
        mock_event.modifiers.return_value = Qt.NoModifier

        # Reset the mock since it was set in setup
        self.multi_cursor.delete_before_cursors.reset_mock()

        # Should handle the event in multi-cursor mode
        result = self.multi_cursor.handle_key_press(mock_event)
        assert result is True
        self.multi_cursor.delete_before_cursors.assert_called()

    def test_handle_key_press_single_cursor(self):
        """Test that single cursor mode doesn't handle key presses."""
        # Single cursor mode
        assert not self.multi_cursor.is_active()

        mock_event = Mock()
        mock_event.text.return_value = "a"

        # Should not handle the event
        result = self.multi_cursor.handle_key_press(mock_event)
        assert result is False


@pytest.mark.skipif(QT_AVAILABLE, reason="Testing without Qt")
class TestMultiCursorWithoutQt:
    """Test multi-cursor without Qt dependencies."""

    def test_import_without_qt(self):
        """Test that module can be imported without Qt."""
        from viloedit.features import multi_cursor
        assert hasattr(multi_cursor, 'MultiCursor')
        assert hasattr(multi_cursor, 'CursorInfo')