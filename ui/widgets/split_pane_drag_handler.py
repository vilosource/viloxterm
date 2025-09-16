#!/usr/bin/env python3
"""
Split pane drag and resize handler.

This module handles drag and resize operations for split pane widgets,
including splitter movement tracking and ratio updates.
"""

import logging
from typing import Optional, Callable, Dict, Any
from PySide6.QtWidgets import QSplitter
from PySide6.QtCore import Qt, QObject, Signal

logger = logging.getLogger(__name__)


class SplitPaneDragHandler(QObject):
    """
    Handles drag and resize operations for split pane widgets.

    Responsibilities:
    - Track splitter movements
    - Update split ratios in model
    - Configure splitter behavior
    - Handle resize events
    """

    # Signals
    ratio_changed = Signal(str, float)  # node_id, new_ratio

    def __init__(self, parent=None):
        """Initialize the drag handler."""
        super().__init__(parent)
        self._splitter_callbacks: Dict[str, Callable] = {}
        self._node_splitter_map: Dict[str, QSplitter] = {}

    def configure_splitter(self, splitter: QSplitter, node_id: str) -> None:
        """
        Configure a splitter for optimal drag behavior.

        Args:
            splitter: The QSplitter to configure
            node_id: ID of the split node this splitter represents
        """
        # Configure for optimal performance and user experience
        splitter.setOpaqueResize(True)  # Real-time resize (reduces flashing)
        splitter.setChildrenCollapsible(False)  # Prevent child widgets from collapsing

        # Store mapping for ratio updates
        self._node_splitter_map[node_id] = splitter

        # Connect splitter movement to ratio tracking
        def on_splitter_moved():
            self._handle_splitter_moved(node_id, splitter)

        splitter.splitterMoved.connect(on_splitter_moved)
        logger.debug(f"Configured splitter for node {node_id}")

    def _handle_splitter_moved(self, node_id: str, splitter: QSplitter):
        """
        Handle splitter movement and calculate new ratio.

        Args:
            node_id: ID of the split node
            splitter: The splitter that moved
        """
        try:
            sizes = splitter.sizes()
            total = sum(sizes)

            if total > 0 and len(sizes) >= 2:
                ratio = sizes[0] / total
                logger.debug(f"Splitter moved for node {node_id}: ratio={ratio:.3f}")

                # Emit signal for model update
                self.ratio_changed.emit(node_id, ratio)

                # Call registered callback if any
                if node_id in self._splitter_callbacks:
                    self._splitter_callbacks[node_id](ratio)

        except Exception as e:
            logger.error(f"Error handling splitter movement for {node_id}: {e}")

    def register_ratio_callback(self, node_id: str, callback: Callable[[float], None]):
        """
        Register a callback for ratio changes on a specific node.

        Args:
            node_id: ID of the split node
            callback: Function to call when ratio changes (receives new ratio as float)
        """
        self._splitter_callbacks[node_id] = callback
        logger.debug(f"Registered ratio callback for node {node_id}")

    def unregister_ratio_callback(self, node_id: str):
        """
        Unregister ratio callback for a node.

        Args:
            node_id: ID of the split node
        """
        if node_id in self._splitter_callbacks:
            del self._splitter_callbacks[node_id]
            logger.debug(f"Unregistered ratio callback for node {node_id}")

    def apply_ratio(self, splitter: QSplitter, ratio: float) -> bool:
        """
        Apply a specific ratio to a splitter.

        Args:
            splitter: The QSplitter to update
            ratio: Ratio to apply (0.0 to 1.0)

        Returns:
            True if ratio was applied successfully
        """
        try:
            if splitter.count() != 2:
                logger.warning(f"Cannot apply ratio to splitter with {splitter.count()} children")
                return False

            total = 1000  # Use fixed total for consistent calculations
            first_size = int(total * ratio)
            second_size = total - first_size

            splitter.setSizes([first_size, second_size])
            logger.debug(f"Applied ratio {ratio:.3f} to splitter: sizes=[{first_size}, {second_size}]")
            return True

        except Exception as e:
            logger.error(f"Failed to apply ratio {ratio}: {e}")
            return False

    def get_current_ratio(self, splitter: QSplitter) -> Optional[float]:
        """
        Get the current ratio of a splitter.

        Args:
            splitter: The QSplitter to query

        Returns:
            Current ratio (0.0 to 1.0) or None if cannot determine
        """
        try:
            if splitter.count() != 2:
                return None

            sizes = splitter.sizes()
            total = sum(sizes)

            if total > 0:
                ratio = sizes[0] / total
                return ratio

        except Exception as e:
            logger.error(f"Failed to get current ratio: {e}")

        return None

    def reset_to_equal_split(self, splitter: QSplitter) -> bool:
        """
        Reset splitter to equal 50/50 split.

        Args:
            splitter: The QSplitter to reset

        Returns:
            True if reset was successful
        """
        return self.apply_ratio(splitter, 0.5)

    def cleanup_splitter(self, node_id: str):
        """
        Clean up tracking for a splitter that's being removed.

        Args:
            node_id: ID of the split node being removed
        """
        # Remove from mappings
        if node_id in self._node_splitter_map:
            del self._node_splitter_map[node_id]

        self.unregister_ratio_callback(node_id)
        logger.debug(f"Cleaned up splitter tracking for node {node_id}")

    def get_splitter_for_node(self, node_id: str) -> Optional[QSplitter]:
        """
        Get the splitter widget for a given node ID.

        Args:
            node_id: ID of the split node

        Returns:
            QSplitter widget or None if not found
        """
        return self._node_splitter_map.get(node_id)

    def get_all_ratios(self) -> Dict[str, float]:
        """
        Get current ratios for all tracked splitters.

        Returns:
            Dictionary mapping node IDs to their current ratios
        """
        ratios = {}
        for node_id, splitter in self._node_splitter_map.items():
            ratio = self.get_current_ratio(splitter)
            if ratio is not None:
                ratios[node_id] = ratio
        return ratios

    def apply_ratios(self, ratios: Dict[str, float]) -> int:
        """
        Apply multiple ratios to their corresponding splitters.

        Args:
            ratios: Dictionary mapping node IDs to desired ratios

        Returns:
            Number of ratios successfully applied
        """
        applied_count = 0
        for node_id, ratio in ratios.items():
            splitter = self.get_splitter_for_node(node_id)
            if splitter and self.apply_ratio(splitter, ratio):
                applied_count += 1

        logger.debug(f"Applied {applied_count}/{len(ratios)} ratios")
        return applied_count

    def cleanup(self):
        """Clean up all tracking data."""
        self._splitter_callbacks.clear()
        self._node_splitter_map.clear()
        logger.debug("Drag handler cleanup complete")


# Global drag handler instance
_drag_handler_instance = None


def get_drag_handler() -> SplitPaneDragHandler:
    """
    Get the global drag handler instance.

    Returns:
        Global SplitPaneDragHandler instance
    """
    global _drag_handler_instance
    if _drag_handler_instance is None:
        _drag_handler_instance = SplitPaneDragHandler()
    return _drag_handler_instance