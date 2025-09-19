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
    def get_metadata(self) -> WidgetMetadata:
        """Get widget metadata."""
        pass

    @abstractmethod
    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """
        Create and return the Qt widget.

        Args:
            parent: Parent widget

        Returns:
            QWidget: The created widget
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