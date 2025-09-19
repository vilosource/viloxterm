"""ViloEdit - Code Editor Plugin for ViloxTerm."""

__version__ = "1.0.0"
__author__ = "ViloxTerm Team"
__email__ = "team@viloxterm.org"

from .plugin import EditorPlugin
from .editor import CodeEditor
from .widget import EditorWidgetFactory
from .syntax import SyntaxHighlighter

__all__ = [
    "EditorPlugin",
    "CodeEditor",
    "EditorWidgetFactory",
    "SyntaxHighlighter"
]