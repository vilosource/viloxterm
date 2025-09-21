"""Tests for find and replace functionality."""

import pytest
from unittest.mock import Mock, patch

try:
    from PySide6.QtWidgets import QApplication, QTextEdit
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QTextCursor, QTextDocument
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False

from viloedit.features.find_replace import FindReplace, SearchDirection, FindReplaceResult


@pytest.mark.skipif(not QT_AVAILABLE, reason="Qt not available")
class TestFindReplace:
    """Test find and replace functionality."""

    @classmethod
    def setup_class(cls):
        """Setup Qt application."""
        if not QApplication.instance():
            cls.app = QApplication([])

    def setup_method(self):
        """Setup test environment."""
        self.find_replace = FindReplace()
        self.mock_editor = Mock()

        # Mock the textCursor and selectedText properly
        mock_cursor = Mock()
        mock_cursor.hasSelection.return_value = False
        mock_cursor.selectedText.return_value = ""
        self.mock_editor.textCursor.return_value = mock_cursor

        self.find_replace.set_editor(self.mock_editor)

    def teardown_method(self):
        """Cleanup test environment."""
        self.find_replace.close()

    def test_initialization(self):
        """Test find/replace widget initialization."""
        assert self.find_replace is not None
        assert self.find_replace.editor == self.mock_editor
        assert self.find_replace.last_search_position == 0
        assert isinstance(self.find_replace.search_history, list)
        assert isinstance(self.find_replace.replace_history, list)

    def test_ui_components(self):
        """Test UI components are created."""
        assert self.find_replace.find_input is not None
        assert self.find_replace.replace_input is not None
        assert self.find_replace.case_sensitive_cb is not None
        assert self.find_replace.whole_word_cb is not None
        assert self.find_replace.regex_cb is not None
        assert self.find_replace.wrap_search_cb is not None

    def test_search_options(self):
        """Test search options configuration."""
        # Default options
        options = self.find_replace.get_search_options()
        assert options['wrap_around'] is True  # Default
        assert options['case_sensitive'] is False  # Default
        assert options['whole_word'] is False  # Default
        assert options['regex'] is False  # Default

        # Set options
        self.find_replace.case_sensitive_cb.setChecked(True)
        self.find_replace.regex_cb.setChecked(True)

        options = self.find_replace.get_search_options()
        assert options['case_sensitive'] is True
        assert options['regex'] is True

    def test_add_to_history(self):
        """Test adding items to search history."""
        history = []
        self.find_replace.add_to_history("test1", history)
        self.find_replace.add_to_history("test2", history)

        assert len(history) == 2
        assert history[0] == "test2"  # Most recent first
        assert history[1] == "test1"

        # Test duplicate prevention
        self.find_replace.add_to_history("test1", history)
        assert len(history) == 2  # No duplicate added

    def test_text_matches_normal(self):
        """Test text matching in normal mode."""
        options = {'case_sensitive': False, 'whole_word': False, 'regex': False}

        # Case insensitive
        assert self.find_replace.text_matches("Hello", "hello", options)
        assert self.find_replace.text_matches("HELLO", "hello", options)

        # Case sensitive
        options['case_sensitive'] = True
        assert not self.find_replace.text_matches("Hello", "hello", options)
        assert self.find_replace.text_matches("hello", "hello", options)

    def test_text_matches_whole_word(self):
        """Test text matching with whole word option."""
        options = {'case_sensitive': False, 'whole_word': True, 'regex': False}

        assert self.find_replace.text_matches("hello", "hello", options)
        assert not self.find_replace.text_matches("hello world", "hello", options)

    def test_text_matches_regex(self):
        """Test text matching with regex option."""
        options = {'case_sensitive': False, 'whole_word': False, 'regex': True}

        assert self.find_replace.text_matches("hello123", r"hello\d+", options)
        assert not self.find_replace.text_matches("hello", r"hello\d+", options)

    def test_show_hide_widget(self):
        """Test showing and hiding the widget."""
        # Initially hidden
        assert not self.find_replace.isVisible()

        # Show find widget
        self.find_replace.show_find_widget()
        assert self.find_replace.isVisible()

        # Close widget
        self.find_replace.close_widget()
        assert not self.find_replace.isVisible()

    @patch('viloedit.features.find_replace.logger')
    def test_find_all_logging(self, mock_logger):
        """Test find all functionality with logging."""
        # Mock editor with document
        mock_document = Mock()
        mock_cursor = Mock()
        mock_cursor.isNull.return_value = True  # No matches found

        self.mock_editor.document.return_value = mock_document
        self.mock_editor.textCursor.return_value = mock_cursor
        mock_document.find.return_value = mock_cursor

        # Set find text
        self.find_replace.find_input.setCurrentText("test")

        # Call find_all
        self.find_replace.find_all()

        # Verify logging was called
        mock_logger.info.assert_called()


@pytest.mark.skipif(QT_AVAILABLE, reason="Testing without Qt")
class TestFindReplaceWithoutQt:
    """Test find/replace without Qt dependencies."""

    def test_import_without_qt(self):
        """Test that module can be imported without Qt."""
        from viloedit.features import find_replace
        assert hasattr(find_replace, 'FindReplace')
        assert hasattr(find_replace, 'SearchDirection')
        assert hasattr(find_replace, 'FindReplaceResult')


class TestFindReplaceResult:
    """Test FindReplaceResult class."""

    def test_default_values(self):
        """Test default values."""
        result = FindReplaceResult()
        assert result.found is False
        assert result.position == -1
        assert result.matches == 0
        assert result.replaced == 0

    def test_custom_values(self):
        """Test custom values."""
        result = FindReplaceResult(found=True, position=10, matches=5, replaced=3)
        assert result.found is True
        assert result.position == 10
        assert result.matches == 5
        assert result.replaced == 3


class TestSearchDirection:
    """Test SearchDirection enum."""

    def test_enum_values(self):
        """Test enum values."""
        assert SearchDirection.FORWARD.value == "forward"
        assert SearchDirection.BACKWARD.value == "backward"