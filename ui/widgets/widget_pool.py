#!/usr/bin/env python3
"""
Widget pooling system for efficient widget reuse.

This module provides a pooling mechanism to reuse widgets instead of
constantly creating and destroying them, which helps eliminate white flash
and improves performance.
"""

import logging
from collections import defaultdict
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QWidget

logger = logging.getLogger(__name__)


class WidgetPool:
    """
    Manages pools of reusable widgets to avoid creation/destruction overhead.

    Benefits:
    - Reduced memory allocation/deallocation
    - Faster split operations
    - Less garbage collection pressure
    - Smoother visual transitions
    """

    def __init__(self, max_pool_size: int = 10):
        """
        Initialize the widget pool.

        Args:
            max_pool_size: Maximum number of widgets to keep in each pool
        """
        self.max_pool_size = max_pool_size

        # Pools organized by widget type
        self._pools: dict[type[QWidget], list[QWidget]] = defaultdict(list)

        # Track widgets currently in use (not in pool)
        self._in_use: set = set()

        # Statistics for monitoring
        self._stats = {
            'acquisitions': 0,
            'releases': 0,
            'creations': 0,
            'reuses': 0,
            'destructions': 0
        }

        logger.info(f"WidgetPool initialized with max_pool_size={max_pool_size}")

    def acquire_splitter(self, orientation: Qt.Orientation) -> QSplitter:
        """
        Acquire a QSplitter from the pool or create a new one.

        Args:
            orientation: Qt.Horizontal or Qt.Vertical

        Returns:
            A configured QSplitter ready for use
        """
        self._stats['acquisitions'] += 1

        # Try to get from pool
        pool = self._pools[QSplitter]

        splitter = None
        # Look for a splitter with matching orientation
        for i, widget in enumerate(pool):
            if isinstance(widget, QSplitter) and widget.orientation() == orientation:
                splitter = pool.pop(i)
                self._stats['reuses'] += 1
                logger.debug(f"Reusing QSplitter from pool (orientation={orientation})")
                break

        if not splitter:
            # Create new splitter
            splitter = QSplitter(orientation)
            self._stats['creations'] += 1
            logger.debug(f"Creating new QSplitter (orientation={orientation})")

        # Configure splitter for optimal performance
        splitter.setOpaqueResize(True)
        splitter.setChildrenCollapsible(False)

        # Clear any existing widgets (in case of reuse)
        while splitter.count() > 0:
            widget = splitter.widget(0)
            widget.setParent(None)

        # Make sure the splitter is visible (it was hidden when pooled)
        splitter.show()

        # Track as in-use
        self._in_use.add(splitter)

        return splitter

    def acquire_widget(self, widget_type: type[QWidget], *args, **kwargs) -> QWidget:
        """
        Acquire a widget from the pool or create a new one.

        Args:
            widget_type: Type of widget to acquire
            *args: Arguments for widget constructor (if creating new)
            **kwargs: Keyword arguments for widget constructor

        Returns:
            A widget ready for use
        """
        self._stats['acquisitions'] += 1

        # Try to get from pool
        pool = self._pools[widget_type]

        if pool:
            widget = pool.pop()
            self._stats['reuses'] += 1
            logger.debug(f"Reusing {widget_type.__name__} from pool")

            # Reset widget state
            self._reset_widget(widget)
        else:
            # Create new widget
            widget = widget_type(*args, **kwargs)
            self._stats['creations'] += 1
            logger.debug(f"Creating new {widget_type.__name__}")

        # Track as in-use
        self._in_use.add(widget)

        return widget

    def release(self, widget: QWidget) -> bool:
        """
        Release a widget back to the pool for reuse.

        Args:
            widget: Widget to release

        Returns:
            True if widget was pooled, False if destroyed
        """
        if widget not in self._in_use:
            logger.warning(f"Attempting to release widget not tracked as in-use: {widget}")
            return False

        self._stats['releases'] += 1
        self._in_use.discard(widget)

        # Get the appropriate pool
        widget_type = type(widget)
        pool = self._pools[widget_type]

        # Check if pool is full
        if len(pool) >= self.max_pool_size:
            # Pool is full, destroy the widget
            logger.debug(f"Pool full for {widget_type.__name__}, destroying widget")
            self._destroy_widget(widget)
            return False

        # Reset and pool the widget
        self._reset_widget(widget)
        widget.hide()  # Hide pooled widgets
        widget.setParent(None)  # Remove from parent

        pool.append(widget)
        logger.debug(f"Released {widget_type.__name__} to pool (pool size: {len(pool)})")

        return True

    def _reset_widget(self, widget: QWidget):
        """
        Reset a widget to a clean state for reuse.

        Args:
            widget: Widget to reset
        """
        if isinstance(widget, QSplitter):
            # Clear splitter children
            while widget.count() > 0:
                child = widget.widget(0)
                child.setParent(None)

            # Reset splitter properties
            widget.setHandleWidth(1)

        # Clear any signals/slots (if needed)
        try:
            widget.disconnect()
        except (TypeError, RuntimeError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"No connections to disconnect for widget: {e}")
            # No connections to disconnect, which is fine

        # Reset common properties
        widget.setEnabled(True)
        widget.show()  # Make sure widget is shown
        widget.setStyleSheet("")

    def _destroy_widget(self, widget: QWidget):
        """
        Properly destroy a widget.

        Args:
            widget: Widget to destroy
        """
        self._stats['destructions'] += 1
        widget.setParent(None)
        widget.deleteLater()

    def clear_pool(self, widget_type: Optional[type[QWidget]] = None):
        """
        Clear widgets from pool(s).

        Args:
            widget_type: Specific type to clear, or None for all
        """
        if widget_type:
            pools_to_clear = {widget_type: self._pools[widget_type]}
        else:
            pools_to_clear = self._pools

        for wtype, pool in pools_to_clear.items():
            count = len(pool)
            for widget in pool:
                self._destroy_widget(widget)
            pool.clear()
            logger.info(f"Cleared {count} widgets of type {wtype.__name__} from pool")

    def get_stats(self) -> dict[str, int]:
        """
        Get pool statistics.

        Returns:
            Dictionary of statistics
        """
        stats = self._stats.copy()
        stats['total_pooled'] = sum(len(pool) for pool in self._pools.values())
        stats['total_in_use'] = len(self._in_use)
        stats['pool_efficiency'] = (
            self._stats['reuses'] / self._stats['acquisitions'] * 100
            if self._stats['acquisitions'] > 0 else 0
        )
        return stats

    def log_stats(self):
        """Log current pool statistics."""
        stats = self.get_stats()
        logger.info(
            f"WidgetPool stats: "
            f"Pooled={stats['total_pooled']}, "
            f"InUse={stats['total_in_use']}, "
            f"Reuses={stats['reuses']}, "
            f"Creates={stats['creations']}, "
            f"Efficiency={stats['pool_efficiency']:.1f}%"
        )

    def cleanup(self):
        """Clean up all pooled widgets."""
        logger.info("Cleaning up widget pool")

        # Clear all pools
        self.clear_pool()

        # Log final stats
        self.log_stats()


# Global widget pool instance
_widget_pool: Optional[WidgetPool] = None


def get_widget_pool() -> WidgetPool:
    """
    Get the global widget pool instance.

    Returns:
        The global WidgetPool instance
    """
    global _widget_pool
    if _widget_pool is None:
        _widget_pool = WidgetPool()
    return _widget_pool


def cleanup_widget_pool():
    """Clean up the global widget pool."""
    global _widget_pool
    if _widget_pool:
        _widget_pool.cleanup()
        _widget_pool = None
