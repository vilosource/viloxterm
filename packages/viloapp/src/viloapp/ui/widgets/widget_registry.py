"""
Stub for widget_registry.

This bridges to our new WidgetType in the model.
"""

# WidgetType removed - now using string widget_ids

__all__ = ["WidgetRegistry", "widget_registry"]


# For compatibility, create a stub registry
class WidgetRegistry:
    """Stub registry for widgets."""

    def __init__(self):
        self.widgets = {}

    def register(self, widget_id, widget):
        """Register a widget."""
        self.widgets[widget_id] = widget

    def unregister(self, widget_id):
        """Unregister a widget."""
        if widget_id in self.widgets:
            del self.widgets[widget_id]

    def get(self, widget_id):
        """Get a widget by ID."""
        return self.widgets.get(widget_id)

    def get_all(self):
        """Get all widgets."""
        return list(self.widgets.values())


# Singleton instance
widget_registry = WidgetRegistry()
