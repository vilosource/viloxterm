"""
Stub for WorkspaceWidgetRegistry.

This is a temporary stub to make the app runnable while we transition to the new architecture.
"""


class WorkspaceWidgetRegistry:
    """Stub for the old widget registry."""

    def __init__(self):
        """Initialize the stub registry."""
        pass

    def register_widget(self, widget_type, widget_id, widget):
        """Stub method."""
        pass

    def unregister_widget(self, widget_id):
        """Stub method."""
        pass

    def get_widget(self, widget_id):
        """Stub method."""
        return None

    def get_widgets_by_type(self, widget_type):
        """Stub method."""
        return []

    def clear(self):
        """Stub method."""
        pass
