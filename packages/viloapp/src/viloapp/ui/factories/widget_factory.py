"""
Widget factory - TEMPORARY STUB during Big Bang refactor.

TODO: Will be rebuilt to create widgets from WorkspaceModel.
"""

from typing import Optional

from viloapp.ui.widgets.split_pane_widget import SplitPaneWidget


class WidgetFactory:
    """TEMPORARY STUB - Will create widgets from model after refactor."""

    @staticmethod
    def create_split_pane_widget(
        initial_type=None,
        initial_widget_id: Optional[str] = None,
        parent=None,
    ) -> SplitPaneWidget:
        """
        TEMPORARY STUB - Returns minimal widget to prevent crashes.

        TODO: After refactor will:
        - Get tree from WorkspaceModel
        - Create pure view widgets
        - Set up observer connections
        """
        return SplitPaneWidget(parent=parent)

    @staticmethod
    def create_legacy_split_pane_widget(
        initial_widget_type=None,
        initial_widget_id: Optional[str] = None,
        parent=None,
    ) -> SplitPaneWidget:
        """TEMPORARY STUB - Legacy method disabled."""
        return SplitPaneWidget(parent=parent)
