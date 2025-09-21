"""Tests for autocomplete functionality."""

import pytest
from unittest.mock import Mock

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False

from viloedit.features.autocomplete import (
    AutoComplete, KeywordCompletionProvider, SnippetCompletionProvider,
    VariableCompletionProvider, CompletionPopup
)


@pytest.mark.skipif(not QT_AVAILABLE, reason="Qt not available")
class TestAutoComplete:
    """Test autocomplete functionality."""

    @classmethod
    def setup_class(cls):
        """Setup Qt application."""
        if not QApplication.instance():
            cls.app = QApplication([])

    def setup_method(self):
        """Setup test environment."""
        self.mock_editor = Mock()
        self.autocomplete = AutoComplete(self.mock_editor)

    def teardown_method(self):
        """Cleanup test environment."""
        if hasattr(self.autocomplete, 'completion_popup') and self.autocomplete.completion_popup:
            self.autocomplete.completion_popup.close()

    def test_initialization(self):
        """Test autocomplete initialization."""
        assert self.autocomplete.editor == self.mock_editor
        assert len(self.autocomplete.providers) > 0
        assert self.autocomplete.enabled is True
        assert self.autocomplete.min_chars == 2

    def test_should_trigger_completion(self):
        """Test completion trigger conditions."""
        # Should trigger with sufficient characters
        assert self.autocomplete.should_trigger_completion("hello wo", 8)

        # Should not trigger with insufficient characters
        assert not self.autocomplete.should_trigger_completion("h", 1)

        # Should trigger if at end of word with sufficient characters (position 5 is at "hello")
        assert self.autocomplete.should_trigger_completion("hello world", 5)

        # Should not trigger if not at word boundary
        assert not self.autocomplete.should_trigger_completion("hello world", 1)

    def test_add_remove_provider(self):
        """Test adding and removing providers."""
        initial_count = len(self.autocomplete.providers)

        # Add provider
        new_provider = KeywordCompletionProvider("javascript")
        self.autocomplete.add_provider(new_provider)
        assert len(self.autocomplete.providers) == initial_count + 1

        # Remove provider
        self.autocomplete.remove_provider(new_provider)
        assert len(self.autocomplete.providers) == initial_count

    def test_get_completions(self):
        """Test getting completions from providers."""
        text = "def hello_wo"
        completions = self.autocomplete.get_completions(text, len(text))

        # Should get some completions
        assert isinstance(completions, list)
        # Length could be 0 if no matching completions


class TestKeywordCompletionProvider:
    """Test keyword completion provider."""

    def setup_method(self):
        """Setup test environment."""
        self.provider = KeywordCompletionProvider("python")

    def test_initialization(self):
        """Test provider initialization."""
        assert self.provider.language == "python"
        assert len(self.provider.keywords) > 0
        assert "def" in self.provider.keywords
        assert "class" in self.provider.keywords

    def test_get_completions(self):
        """Test getting keyword completions."""
        # Test with 'de' should suggest 'def'
        completions = self.provider.get_completions("de", 2, {})
        assert "def" in completions

        # Test with 'cl' should suggest 'class'
        completions = self.provider.get_completions("cl", 2, {})
        assert "class" in completions

        # Test with non-matching prefix
        completions = self.provider.get_completions("xyz", 3, {})
        assert len(completions) == 0

        # Test with insufficient characters
        completions = self.provider.get_completions("d", 1, {})
        assert len(completions) == 0

    def test_provider_name(self):
        """Test provider name."""
        assert self.provider.get_provider_name() == "Keywords (python)"


class TestSnippetCompletionProvider:
    """Test snippet completion provider."""

    def setup_method(self):
        """Setup test environment."""
        self.provider = SnippetCompletionProvider("python")

    def test_initialization(self):
        """Test provider initialization."""
        assert self.provider.language == "python"
        assert len(self.provider.snippets) > 0
        assert "def" in self.provider.snippets
        assert "class" in self.provider.snippets

    def test_get_completions(self):
        """Test getting snippet completions."""
        # Test with 'de' should suggest 'def (snippet)'
        completions = self.provider.get_completions("de", 2, {})
        assert any("def (snippet)" in comp for comp in completions)

        # Test with 'cl' should suggest 'class (snippet)'
        completions = self.provider.get_completions("cl", 2, {})
        assert any("class (snippet)" in comp for comp in completions)

        # Test with non-matching prefix
        completions = self.provider.get_completions("xyz", 3, {})
        assert len(completions) == 0

    def test_provider_name(self):
        """Test provider name."""
        assert self.provider.get_provider_name() == "Snippets (python)"


class TestVariableCompletionProvider:
    """Test variable completion provider."""

    def setup_method(self):
        """Setup test environment."""
        self.provider = VariableCompletionProvider()

    def test_initialization(self):
        """Test provider initialization."""
        assert hasattr(self.provider, 'variable_cache')
        assert hasattr(self.provider, 'last_text')

    def test_extract_variables_python(self):
        """Test variable extraction for Python code."""
        python_code = """
def hello_world():
    my_variable = 42
    another_var = "test"
    return my_variable

class MyClass:
    def __init__(self):
        self.instance_var = True

for loop_var in range(10):
    pass
"""
        variables = self.provider._extract_variables(python_code, "python")

        assert "hello_world" in variables
        assert "my_variable" in variables
        assert "another_var" in variables
        assert "MyClass" in variables
        assert "loop_var" in variables

    def test_extract_variables_javascript(self):
        """Test variable extraction for JavaScript code."""
        js_code = """
function myFunction() {
    var oldVar = 1;
    let newVar = 2;
    const constVar = 3;
    someAssignment = 4;
}

class MyClass {
    constructor() {
        this.prop = true;
    }
}
"""
        variables = self.provider._extract_variables(js_code, "javascript")

        assert "myFunction" in variables
        assert "oldVar" in variables
        assert "newVar" in variables
        assert "constVar" in variables
        assert "someAssignment" in variables
        assert "MyClass" in variables

    def test_get_completions(self):
        """Test getting variable completions."""
        # Set up some variables in cache
        test_code = "my_variable = 42\nother_var = 'test'"
        self.provider.last_text = ""  # Force cache update

        # Test with 'my' should suggest 'my_variable'
        completions = self.provider.get_completions(
            test_code + "\nmy", len(test_code) + 3, {}
        )
        assert "my_variable" in completions

        # Test with 'ot' should suggest 'other_var'
        completions = self.provider.get_completions(
            test_code + "\not", len(test_code) + 3, {}
        )
        assert "other_var" in completions

    def test_provider_name(self):
        """Test provider name."""
        assert self.provider.get_provider_name() == "Variables"


@pytest.mark.skipif(not QT_AVAILABLE, reason="Qt not available")
class TestCompletionPopup:
    """Test completion popup widget."""

    @classmethod
    def setup_class(cls):
        """Setup Qt application."""
        if not QApplication.instance():
            cls.app = QApplication([])

    def setup_method(self):
        """Setup test environment."""
        self.popup = CompletionPopup()

    def teardown_method(self):
        """Cleanup test environment."""
        self.popup.close()

    def test_initialization(self):
        """Test popup initialization."""
        assert self.popup.list_widget is not None
        assert not self.popup.isVisible()

    def test_set_completions(self):
        """Test setting completions."""
        completions = ["test1", "test2", "test3"]
        self.popup.set_completions(completions)

        assert self.popup.list_widget.count() == 3
        assert self.popup.list_widget.item(0).text() == "test1"
        assert self.popup.list_widget.currentRow() == 0

    def test_accept_current(self):
        """Test accepting current completion."""
        completions = ["test1", "test2"]
        self.popup.set_completions(completions)

        # Mock the signal
        signal_received = []
        self.popup.completion_selected.connect(lambda text: signal_received.append(text))

        # Accept current
        self.popup.accept_current()

        assert len(signal_received) == 1
        assert signal_received[0] == "test1"


@pytest.mark.skipif(QT_AVAILABLE, reason="Testing without Qt")
class TestAutoCompleteWithoutQt:
    """Test autocomplete without Qt dependencies."""

    def test_import_without_qt(self):
        """Test that module can be imported without Qt."""
        from viloedit.features import autocomplete
        assert hasattr(autocomplete, 'AutoComplete')
        assert hasattr(autocomplete, 'CompletionProvider')
        assert hasattr(autocomplete, 'KeywordCompletionProvider')