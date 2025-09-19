"""Editor widget factory."""

import logging
from typing import Optional, Dict, Any

from PySide6.QtWidgets import QWidget
from viloapp_sdk import IWidget, WidgetMetadata, WidgetPosition

from .editor import CodeEditor

logger = logging.getLogger(__name__)


class EditorWidgetFactory(IWidget):
    """Factory for creating editor widgets."""

    def get_metadata(self) -> WidgetMetadata:
        """Get widget metadata."""
        return WidgetMetadata(
            id="editor",
            title="Editor",
            position=WidgetPosition.MAIN,
            icon="file-text",
            closable=True,
            singleton=False
        )

    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """Create a new editor widget."""
        return CodeEditor(parent)

    def get_state(self) -> Dict[str, Any]:
        """Get widget state."""
        return {}

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore widget state."""
        pass