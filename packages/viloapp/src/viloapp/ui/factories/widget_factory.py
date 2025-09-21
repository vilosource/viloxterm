"""
Widget factory for creating and wiring up MVC components.

This factory ensures proper dependency injection and component wiring
following the MVC architectural pattern.
"""

from typing import Optional

from viloapp.ui.widgets.split_pane_controller import SplitPaneController
from viloapp.ui.widgets.split_pane_model import SplitPaneModel, WidgetType
from viloapp.ui.widgets.split_pane_widget import SplitPaneWidget


class WidgetFactory:
    """Creates and wires up MVC components."""

    @staticmethod
    def create_split_pane_widget(
        initial_type: WidgetType = WidgetType.TEXT_EDITOR,
        initial_widget_id: Optional[str] = None,
        parent=None
    ) -> SplitPaneWidget:
        """
        Create a properly wired SplitPaneWidget following MVC pattern.

        This method creates the model and controller components first,
        then injects them into the view component, ensuring proper
        MVC dependency injection.

        Args:
            initial_type: Type of widget for initial pane
            initial_widget_id: Optional ID for the initial widget (for singleton tracking)
            parent: Parent widget

        Returns:
            Fully wired SplitPaneWidget with injected dependencies
        """
        # Create model - owns all data and business logic (pass parent for Qt hierarchy)
        model = SplitPaneModel(initial_type, initial_widget_id, parent=parent)

        # Create controller with model reference
        controller = SplitPaneController(model, parent=parent)

        # Create view with injected model and controller
        view = SplitPaneWidget(model=model, controller=controller, parent=parent)

        # Complete the MVC wiring - controller now has view reference
        controller.set_view(view)

        # Connect model signals to view for observer pattern
        model.model_changed.connect(view.refresh_view)
        if hasattr(view, '_on_model_changed'):
            model.model_changed.connect(view._on_model_changed)

        return view

    @staticmethod
    def create_legacy_split_pane_widget(
        initial_widget_type: WidgetType = WidgetType.TEXT_EDITOR,
        initial_widget_id: Optional[str] = None,
        parent=None
    ) -> SplitPaneWidget:
        """
        Create SplitPaneWidget using legacy pattern for backward compatibility.

        This method maintains backward compatibility with existing code
        that expects the old constructor pattern.

        Args:
            initial_widget_type: Type of widget for initial pane
            initial_widget_id: Optional ID for the initial widget (for singleton tracking)
            parent: Parent widget

        Returns:
            SplitPaneWidget created using legacy internal instantiation
        """
        return SplitPaneWidget(
            initial_widget_type=initial_widget_type,
            initial_widget_id=initial_widget_id,
            parent=parent
        )