#!/usr/bin/env python3
"""
Split pane widget - TEMPORARY STUB during Big Bang refactor.

TODO: This will be rebuilt as a pure view that renders from WorkspaceModel.
All model logic has been removed. This is just a minimal placeholder
to prevent import errors.
"""

import logging
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

logger = logging.getLogger(__name__)


class SplitPaneWidget(QWidget):
    """
    TEMPORARY STUB - Will be pure view after Big Bang refactor.

    This widget will:
    - Render tree structure from WorkspaceModel
    - Handle only UI events
    - Have NO state or model logic
    """

    # Signals needed by other components
    pane_added = Signal(str)
    pane_removed = Signal(str)
    active_pane_changed = Signal(str)
    layout_changed = Signal()

    def __init__(self, parent=None):
        """TODO: Will accept WorkspaceModel reference after refactor."""
        super().__init__(parent)

        # Minimal UI to prevent crashes
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        logger.warning("SplitPaneWidget is a stub - Big Bang refactor in progress")

    # Stub methods to prevent AttributeErrors
    def refresh_view(self):
        """TODO: Will render from model."""
        pass

    def get_active_pane_id(self) -> Optional[str]:
        """TODO: Will read from model."""
        return None

    def set_active_pane(self, pane_id: str):
        """TODO: Will update model."""
        pass

    def get_pane_widget(self, pane_id: str):
        """TODO: Will get from model."""
        return None

    def cleanup(self):
        """TODO: Cleanup when done."""
        pass
