"""Tests for code editor widget."""

import pytest
from pathlib import Path
import tempfile

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtTest import QTest
    from PySide6.QtCore import Qt

    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False

from viloedit.editor import CodeEditor


@pytest.mark.skipif(not QT_AVAILABLE, reason="Qt not available")
class TestCodeEditor:
    """Test code editor functionality."""

    @classmethod
    def setup_class(cls):
        """Setup Qt application."""
        if not QApplication.instance():
            cls.app = QApplication([])

    def setup_method(self):
        """Setup test environment."""
        self.editor = CodeEditor()

    def teardown_method(self):
        """Cleanup test environment."""
        self.editor.close()

    def test_editor_initialization(self):
        """Test editor initialization."""
        assert self.editor is not None
        assert self.editor.line_number_area is not None
        assert self.editor.file_path is None

    def test_text_operations(self):
        """Test basic text operations."""
        test_text = "Hello, World!"

        # Set text
        self.editor.setPlainText(test_text)
        assert self.editor.toPlainText() == test_text

        # Test modification tracking
        self.editor.insertPlainText(" More text")
        assert self.editor.document().isModified()

    def test_file_operations(self):
        """Test file load/save operations."""
        test_content = "print('Hello, World!')\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_content)
            temp_file = f.name

        try:
            # Test load file
            self.editor.load_file(temp_file)
            assert self.editor.toPlainText() == test_content
            assert self.editor.file_path == Path(temp_file)

            # Test save file
            new_content = "print('Modified content')\n"
            self.editor.setPlainText(new_content)
            assert self.editor.save_file()

            # Verify saved content
            with open(temp_file, "r") as f:
                saved_content = f.read()
            assert saved_content == new_content

        finally:
            Path(temp_file).unlink()

    def test_line_number_area(self):
        """Test line number area functionality."""
        # Add some lines
        text = "Line 1\nLine 2\nLine 3\n"
        self.editor.setPlainText(text)

        # Check line number area width
        width = self.editor.line_number_area_width()
        assert width > 0

        # Check block count
        assert self.editor.blockCount() == 4  # 3 lines + 1 empty

    def test_cursor_position_signal(self):
        """Test cursor position changed signal."""
        signal_received = []

        def on_cursor_changed(line, column):
            signal_received.append((line, column))

        self.editor.cursor_position_changed.connect(on_cursor_changed)

        # Move cursor
        self.editor.setPlainText("Line 1\nLine 2")
        cursor = self.editor.textCursor()
        cursor.setPosition(7)  # Start of second line
        self.editor.setTextCursor(cursor)

        # Trigger signal
        self.editor.highlight_current_line()

        # Check signal was emitted
        assert len(signal_received) > 0

    def test_theme_update(self):
        """Test theme update functionality."""
        theme_data = {
            "editor.background": "#000000",
            "editor.foreground": "#ffffff",
            "editor.selectionBackground": "#333333",
        }

        # Should not raise exception
        self.editor.update_theme(theme_data)

        # Check if style was updated
        style = self.editor.styleSheet()
        assert "#000000" in style or "background-color" in style


@pytest.mark.skipif(QT_AVAILABLE, reason="Testing without Qt")
class TestCodeEditorWithoutQt:
    """Test code editor without Qt dependencies."""

    def test_import_without_qt(self):
        """Test that module can be imported without Qt."""
        # This test verifies the module handles missing Qt gracefully
        import viloedit.editor

        assert hasattr(viloedit.editor, "CodeEditor")
