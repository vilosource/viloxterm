"""Widget interface and related definitions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple, List
from enum import Enum
from PySide6.QtWidgets import QWidget

class WidgetPosition(Enum):
    """Available widget positions."""
    MAIN = "main"  # Main workspace area
    SIDEBAR = "sidebar"  # Left sidebar
    PANEL = "panel"  # Bottom panel
    AUXILIARY = "auxiliary"  # Right sidebar
    FLOATING = "floating"  # Floating window

@dataclass
class WidgetMetadata:
    """Widget metadata."""
    id: str
    title: str
    position: WidgetPosition = WidgetPosition.MAIN
    icon: Optional[str] = None
    closable: bool = True
    singleton: bool = False  # Only one instance allowed
    priority: int = 0  # Higher priority shown first
    default_size: Optional[Tuple[int, int]] = None
    min_size: Optional[Tuple[int, int]] = None
    max_size: Optional[Tuple[int, int]] = None

class IWidget(ABC):
    """Interface for plugin-provided widgets."""

    @abstractmethod
    def get_widget_id(self) -> str:
        """
        Get unique widget identifier.

        Returns:
            str: Unique identifier for this widget type
        """
        pass

    @abstractmethod
    def get_title(self) -> str:
        """
        Get widget display title.

        Returns:
            str: Human-readable title for the widget
        """
        pass

    @abstractmethod
    def get_icon(self) -> Optional[str]:
        """
        Get widget icon identifier.

        Returns:
            Optional[str]: Icon identifier or None if no icon
        """
        pass

    @abstractmethod
    def create_instance(self, instance_id: str) -> QWidget:
        """
        Create widget instance with unique ID.

        Args:
            instance_id: Unique identifier for this widget instance

        Returns:
            QWidget: The created widget instance
        """
        pass

    @abstractmethod
    def destroy_instance(self, instance_id: str) -> None:
        """
        Destroy widget instance and clean up resources.

        Args:
            instance_id: ID of the instance to destroy
        """
        pass

    @abstractmethod
    def handle_command(self, command: str, args: Dict[str, Any]) -> Any:
        """
        Handle widget-specific commands.

        Args:
            command: Command identifier
            args: Command arguments

        Returns:
            Any: Command result or None
        """
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """
        Get widget state for persistence.

        Returns:
            Dict containing widget state
        """
        pass

    @abstractmethod
    def restore_state(self, state: Dict[str, Any]) -> None:
        """
        Restore widget state.

        Args:
            state: Previously saved state
        """
        pass

    def on_focus(self) -> None:
        """Called when widget receives focus."""
        pass

    def on_blur(self) -> None:
        """Called when widget loses focus."""
        pass

    def on_resize(self, width: int, height: int) -> None:
        """
        Called when widget is resized.

        Args:
            width: New width
            height: New height
        """
        pass

    def on_close(self) -> bool:
        """
        Called when widget is about to close.

        Returns:
            True to allow closing, False to prevent
        """
        return True

    def get_toolbar_actions(self) -> List[Dict[str, Any]]:
        """
        Get toolbar actions for this widget.

        Returns:
            List of action definitions
        """
        return []

    def get_context_menu_actions(self) -> List[Dict[str, Any]]:
        """
        Get context menu actions for this widget.

        Returns:
            List of action definitions
        """
        return []


class LegacyWidgetAdapter(IWidget):
    """
    Adapter to provide backward compatibility for widgets using the old interface.

    This adapter wraps old-style widget implementations that use get_metadata()
    and create_widget() to work with the new interface.
    """

    def __init__(self, legacy_widget: 'IWidget'):
        """
        Initialize adapter with legacy widget implementation.

        Args:
            legacy_widget: Widget implementation using old interface
        """
        self.legacy_widget = legacy_widget
        self._instances = {}  # Track instances for legacy widgets

    def get_widget_id(self) -> str:
        """Get widget ID from legacy metadata."""
        if hasattr(self.legacy_widget, 'get_metadata'):
            metadata = self.legacy_widget.get_metadata()
            return metadata.id
        # Fallback to class name if no metadata
        return self.legacy_widget.__class__.__name__.lower().replace('widget', '').replace('factory', '')

    def get_title(self) -> str:
        """Get widget title from legacy metadata."""
        if hasattr(self.legacy_widget, 'get_metadata'):
            metadata = self.legacy_widget.get_metadata()
            return metadata.title
        # Fallback to class name
        return self.legacy_widget.__class__.__name__.replace('Widget', '').replace('Factory', '')

    def get_icon(self) -> Optional[str]:
        """Get widget icon from legacy metadata."""
        if hasattr(self.legacy_widget, 'get_metadata'):
            metadata = self.legacy_widget.get_metadata()
            return metadata.icon
        return None

    def create_instance(self, instance_id: str) -> QWidget:
        """Create instance using legacy create_widget method."""
        if hasattr(self.legacy_widget, 'create_widget'):
            widget = self.legacy_widget.create_widget()
            self._instances[instance_id] = widget
            return widget
        else:
            raise NotImplementedError("Legacy widget does not implement create_widget")

    def destroy_instance(self, instance_id: str) -> None:
        """Destroy instance and clean up."""
        if instance_id in self._instances:
            widget = self._instances[instance_id]
            # Call close method if available
            if hasattr(widget, 'close'):
                widget.close()
            widget.deleteLater()
            del self._instances[instance_id]

    def handle_command(self, command: str, args: Dict[str, Any]) -> Any:
        """Handle commands - legacy widgets don't support this, return None."""
        # Legacy widgets don't have command handling
        return None

    def get_state(self) -> Dict[str, Any]:
        """Delegate to legacy widget's get_state method."""
        if hasattr(self.legacy_widget, 'get_state'):
            return self.legacy_widget.get_state()
        return {}

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Delegate to legacy widget's restore_state method."""
        if hasattr(self.legacy_widget, 'restore_state'):
            self.legacy_widget.restore_state(state)