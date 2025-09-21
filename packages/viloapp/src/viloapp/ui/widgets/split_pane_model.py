#!/usr/bin/env python3
"""
Pure model for split pane tree structure with AppWidget management.

This is the MODEL layer - it manages the tree structure and AppWidget lifecycle.
No view concerns, no Qt widgets except the AppWidgets themselves (which are content/data).
"""

import logging
import uuid
from dataclasses import dataclass, field
from typing import Callable, Optional, Union

from viloapp.ui.terminal.terminal_app_widget import TerminalAppWidget
from viloapp.ui.widgets.app_widget import AppWidget
from viloapp.ui.widgets.editor_app_widget import EditorAppWidget
from viloapp.ui.widgets.placeholder_app_widget import PlaceholderAppWidget
from viloapp.ui.widgets.widget_registry import WidgetType

logger = logging.getLogger(__name__)


@dataclass
class LeafNode:
    """
    Leaf node containing an AppWidget.

    The AppWidget is the actual content (terminal, editor, etc.).
    This node owns the widget and manages its lifecycle.
    """

    type: str = "leaf"
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    widget_type: WidgetType = WidgetType.PLACEHOLDER
    app_widget: Optional[AppWidget] = None  # The actual content widget
    parent: Optional["SplitNode"] = None

    def cleanup(self):
        """Clean up the AppWidget."""
        if self.app_widget:
            logger.info(f"Cleaning up AppWidget in leaf {self.id}")
            self.app_widget.cleanup()
            self.app_widget = None


@dataclass
class SplitNode:
    """
    Split node containing two children.

    Pure data structure - no view widgets here.
    """

    type: str = "split"
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    orientation: str = "horizontal"  # "horizontal" or "vertical"
    ratio: float = 0.5
    first: Optional[Union[LeafNode, "SplitNode"]] = None
    second: Optional[Union[LeafNode, "SplitNode"]] = None
    parent: Optional["SplitNode"] = None


class SplitPaneModel:
    """
    Model managing the split pane tree structure and AppWidgets.

    This is the single source of truth for:
    - Tree structure (nodes and relationships)
    - AppWidget instances and lifecycle
    - Active pane tracking

    All operations go through this model.
    """

    def __init__(
        self,
        initial_widget_type: WidgetType = WidgetType.PLACEHOLDER,
        initial_widget_id: Optional[str] = None,
    ):
        """
        Initialize with a single root leaf containing an AppWidget.

        Args:
            initial_widget_type: Type of widget for initial pane
            initial_widget_id: Optional ID for the initial widget (for singleton tracking)
        """
        # Use provided ID or generate a new one
        widget_id = initial_widget_id or str(uuid.uuid4())[:8]

        # Create root node with the specific ID
        self.root = LeafNode(
            widget_type=initial_widget_type,
            id=widget_id,  # Use the same ID for both leaf and widget
        )
        self.leaves: dict[str, LeafNode] = {self.root.id: self.root}
        self.active_pane_id: str = self.root.id

        # Pane numbering state
        self.show_pane_numbers = False
        self.pane_indices: dict[str, int] = {}

        # Callback for when a terminal requests pane closure
        self.terminal_close_callback: Optional[Callable[[str], None]] = None

        # Create initial AppWidget with the same ID
        self.root.app_widget = self.create_app_widget(initial_widget_type, widget_id)
        self.root.app_widget.leaf_node = self.root  # Set back-reference

        # Initialize pane indices
        self.update_pane_indices()

        logger.info(f"SplitPaneModel initialized with root leaf {self.root.id}")

    def create_app_widget(self, widget_type: WidgetType, widget_id: str) -> AppWidget:
        """
        Factory method to create AppWidgets using AppWidgetManager.

        Args:
            widget_type: Type of widget to create
            widget_id: Unique ID for the widget

        Returns:
            New AppWidget instance
        """
        logger.info(f"Creating AppWidget: type={widget_type}, id={widget_id}")

        # Try to use AppWidgetManager first
        try:
            from viloapp.core.app_widget_manager import AppWidgetManager

            manager = AppWidgetManager.get_instance()

            # Try to create widget through manager
            widget = manager.create_widget_by_type(widget_type, widget_id)

            if widget:
                # Special handling for terminal (needs signal connection)
                if widget_type == WidgetType.TERMINAL:
                    if hasattr(widget, "pane_close_requested"):
                        widget.pane_close_requested.connect(
                            lambda: self.on_terminal_close_requested(widget_id)
                        )
                return widget
        except ImportError:
            logger.warning("AppWidgetManager not available, falling back to legacy creation")
        except Exception as e:
            logger.error(f"Failed to create widget via AppWidgetManager: {e}")

        # Legacy fallback - Try widget registry
        from viloapp.ui.widgets.widget_registry import widget_registry

        config = widget_registry.get_config(widget_type)

        if config and config.factory:
            try:
                logger.debug(f"Using factory from registry for {widget_type}")
                widget = config.factory(widget_id)
                if isinstance(widget, AppWidget):
                    # Special handling for terminal
                    if widget_type == WidgetType.TERMINAL and hasattr(
                        widget, "pane_close_requested"
                    ):
                        widget.pane_close_requested.connect(
                            lambda: self.on_terminal_close_requested(widget_id)
                        )
                    return widget
            except Exception as e:
                logger.error(f"Factory failed for {widget_type}: {e}")

        # Try plugin widget factories
        try:
            from viloapp.services.service_locator import ServiceLocator
            from viloapp.services.workspace_service import WorkspaceService

            service_locator = ServiceLocator.get_instance()
            workspace_service = service_locator.get(WorkspaceService)

            if workspace_service:
                # Map widget types to plugin widget IDs
                plugin_widget_id = None
                if widget_type == WidgetType.TERMINAL:
                    plugin_widget_id = "terminal"
                elif widget_type == WidgetType.TEXT_EDITOR:
                    plugin_widget_id = "editor"

                if plugin_widget_id:
                    plugin_widget = workspace_service.create_widget(plugin_widget_id, widget_id)
                    if plugin_widget:
                        logger.info(f"Created plugin widget: {plugin_widget_id} -> {widget_id}")
                        # Special handling for terminal signals
                        if widget_type == WidgetType.TERMINAL and hasattr(
                            plugin_widget, "pane_close_requested"
                        ):
                            plugin_widget.pane_close_requested.connect(
                                lambda: self.on_terminal_close_requested(widget_id)
                            )
                        return plugin_widget

        except Exception as e:
            logger.debug(f"Plugin widget creation failed: {e}")

        # Final fallback to built-in types (temporary)
        if widget_type == WidgetType.TERMINAL:
            terminal_widget = TerminalAppWidget(widget_id)
            terminal_widget.pane_close_requested.connect(
                lambda: self.on_terminal_close_requested(widget_id)
            )
            return terminal_widget
        elif widget_type == WidgetType.TEXT_EDITOR:
            return EditorAppWidget(widget_id)
        elif widget_type == WidgetType.PLACEHOLDER:
            return PlaceholderAppWidget(widget_id, widget_type)
        else:
            # Default fallback
            logger.warning(f"No handler for widget type {widget_type}, using placeholder")
            return PlaceholderAppWidget(widget_id, widget_type)

    def set_terminal_close_callback(self, callback: Callable[[str], None]):
        """
        Set the callback to be called when a terminal requests pane closure.

        Args:
            callback: Function to call with pane_id when terminal exits
        """
        self.terminal_close_callback = callback

    def on_terminal_close_requested(self, pane_id: str):
        """
        Handle terminal close request.

        Args:
            pane_id: ID of the pane containing the terminal that exited
        """
        logger.info(f"Terminal in pane {pane_id} requested closure")
        if self.terminal_close_callback:
            self.terminal_close_callback(pane_id)
        else:
            logger.warning(f"No terminal close callback set - cannot close pane {pane_id}")

    def traverse_tree(
        self,
        node: Optional[Union[LeafNode, SplitNode]] = None,
        callback: Optional[Callable[[LeafNode], None]] = None,
    ) -> list[LeafNode]:
        """
        Traverse the tree and optionally apply a callback to each leaf.

        Args:
            node: Starting node (defaults to root)
            callback: Optional function to call on each leaf

        Returns:
            List of all leaf nodes encountered
        """
        if node is None:
            node = self.root

        leaves = []

        if isinstance(node, LeafNode):
            leaves.append(node)
            if callback:
                callback(node)
        elif isinstance(node, SplitNode):
            if node.first:
                leaves.extend(self.traverse_tree(node.first, callback))
            if node.second:
                leaves.extend(self.traverse_tree(node.second, callback))

        return leaves

    def find_leaf(self, leaf_id: str) -> Optional[LeafNode]:
        """Find a leaf node by ID."""
        return self.leaves.get(leaf_id)

    def find_node(self, node_id: str) -> Optional[Union[LeafNode, SplitNode]]:
        """
        Find any node by ID using tree traversal.

        Args:
            node_id: ID to search for

        Returns:
            Node if found, None otherwise
        """

        def search(
            node: Optional[Union[LeafNode, SplitNode]],
        ) -> Optional[Union[LeafNode, SplitNode]]:
            if not node:
                return None
            if node.id == node_id:
                return node
            if isinstance(node, SplitNode):
                result = search(node.first)
                if result:
                    return result
                return search(node.second)
            return None

        return search(self.root)

    def split_pane(self, pane_id: str, orientation: str) -> Optional[str]:
        """
        Split a pane, creating a new AppWidget.

        Args:
            pane_id: ID of pane to split
            orientation: "horizontal" or "vertical"

        Returns:
            ID of the new pane, or None if split failed
        """
        leaf = self.find_leaf(pane_id)
        if not leaf:
            logger.error(f"Cannot split: leaf {pane_id} not found")
            return None

        logger.info(f"Splitting pane {pane_id} {orientation}ly")

        # Store the parent before creating split
        old_parent = leaf.parent

        # Create new leaf with same widget type
        new_leaf = LeafNode(widget_type=leaf.widget_type)

        # Create AppWidget for new leaf
        new_leaf.app_widget = self.create_app_widget(leaf.widget_type, new_leaf.id)
        new_leaf.app_widget.leaf_node = new_leaf  # Set back-reference

        # Create split node
        split = SplitNode(orientation=orientation, ratio=0.5)

        # Set up the tree structure
        split.first = leaf
        split.second = new_leaf
        leaf.parent = split
        new_leaf.parent = split

        # Update tree structure
        if old_parent:
            # Replace leaf with split in parent
            if old_parent.first == leaf:
                old_parent.first = split
            else:
                old_parent.second = split
            split.parent = old_parent
        else:
            # Leaf is root - split becomes new root
            self.root = split

        # Update tracking
        self.leaves[new_leaf.id] = new_leaf

        # Update pane indices after structural change
        self.update_pane_indices()

        logger.info(f"Split complete: created new pane {new_leaf.id}")
        return new_leaf.id

    def close_pane(self, pane_id: str) -> bool:
        """
        Close a pane, cleaning up its AppWidget.

        Args:
            pane_id: ID of pane to close

        Returns:
            True if successful, False otherwise
        """
        leaf = self.find_leaf(pane_id)
        if not leaf:
            logger.error(f"Cannot close: leaf {pane_id} not found")
            return False

        # Don't close the last pane
        if leaf == self.root:
            logger.warning("Cannot close the last remaining pane")
            return False

        parent = leaf.parent
        if not parent:
            logger.error(f"Cannot close: leaf {pane_id} has no parent")
            return False

        logger.info(f"Closing pane {pane_id}")

        # Clean up AppWidget
        leaf.cleanup()

        # Find sibling
        sibling = parent.second if parent.first == leaf else parent.first
        if not sibling:
            logger.error("Cannot close: no sibling found")
            return False

        # Promote sibling
        grandparent = parent.parent

        if grandparent:
            # Replace parent with sibling in grandparent
            if grandparent.first == parent:
                grandparent.first = sibling
            else:
                grandparent.second = sibling
            sibling.parent = grandparent
        else:
            # Parent is root - sibling becomes new root
            self.root = sibling
            sibling.parent = None

        # Clean up
        del self.leaves[pane_id]

        # Update active pane if necessary
        if self.active_pane_id == pane_id:
            # Find first available leaf
            if self.leaves:
                self.active_pane_id = next(iter(self.leaves.keys()))
                logger.info(f"Active pane changed to {self.active_pane_id}")

        # Update pane indices after structural change
        self.update_pane_indices()

        logger.info(f"Pane {pane_id} closed successfully")
        return True

    def set_active_pane(self, pane_id: str) -> bool:
        """
        Set the active pane.

        Args:
            pane_id: ID of pane to activate

        Returns:
            True if successful, False if pane not found
        """
        if pane_id in self.leaves:
            self.active_pane_id = pane_id
            logger.debug(f"Active pane set to {pane_id}")
            return True
        return False

    def get_active_pane_id(self) -> str:
        """Get the currently active pane ID."""
        return self.active_pane_id

    def get_active_leaf(self) -> Optional[LeafNode]:
        """Get the currently active leaf node."""
        return self.find_leaf(self.active_pane_id)

    def toggle_pane_numbers(self) -> bool:
        """
        Toggle pane number visibility.

        Returns:
            New visibility state
        """
        self.show_pane_numbers = not self.show_pane_numbers
        self.update_pane_indices()
        logger.info(f"Pane numbers {'shown' if self.show_pane_numbers else 'hidden'}")
        return self.show_pane_numbers

    def update_pane_indices(self):
        """
        Update pane numbering using reading order (left-to-right, top-to-bottom).
        Numbers are assigned 1-9 based on tree traversal order.
        """
        numbers = {}
        counter = [1]  # Use list to maintain reference in nested function

        def traverse(node):
            if isinstance(node, LeafNode):
                if counter[0] <= 9:  # Max 9 for future keyboard shortcuts
                    numbers[node.id] = counter[0]
                    counter[0] += 1
            elif isinstance(node, SplitNode):
                # First child is left/top, second is right/bottom
                if node.first:
                    traverse(node.first)
                if node.second:
                    traverse(node.second)

        traverse(self.root)
        self.pane_indices = numbers
        logger.debug(f"Updated pane indices: {self.pane_indices}")

    def get_pane_index(self, pane_id: str) -> Optional[int]:
        """
        Get the display index for a pane.

        Args:
            pane_id: ID of the pane

        Returns:
            Pane number (1-9) or None if not numbered
        """
        return self.pane_indices.get(pane_id)

    def change_pane_type(self, pane_id: str, new_type: WidgetType) -> bool:
        """
        Change the widget type of a pane.

        Args:
            pane_id: ID of pane to change
            new_type: New widget type

        Returns:
            True if successful
        """
        leaf = self.find_leaf(pane_id)
        if not leaf:
            return False

        logger.info(f"Changing pane {pane_id} type from {leaf.widget_type} to {new_type}")

        # Clean up old widget
        leaf.cleanup()

        # Update type
        leaf.widget_type = new_type

        # Create new widget
        leaf.app_widget = self.create_app_widget(new_type, leaf.id)
        leaf.app_widget.leaf_node = leaf

        return True

    def update_split_ratio(self, split_node: SplitNode, ratio: float):
        """
        Update the split ratio for a split node.

        Args:
            split_node: Split node to update
            ratio: New ratio (0.0 to 1.0)
        """
        split_node.ratio = max(0.1, min(0.9, ratio))  # Clamp between 10% and 90%

    def cleanup_all_widgets(self):
        """Clean up all AppWidgets by traversing the tree."""
        logger.info("Cleaning up all AppWidgets")

        def cleanup_leaf(leaf: LeafNode):
            leaf.cleanup()

        self.traverse_tree(callback=cleanup_leaf)

    def get_all_app_widgets(self) -> list[AppWidget]:
        """
        Get all AppWidgets from the tree.

        Returns:
            List of all AppWidget instances
        """
        widgets = []

        def collect_widget(leaf: LeafNode):
            if leaf.app_widget:
                widgets.append(leaf.app_widget)

        self.traverse_tree(callback=collect_widget)
        return widgets

    def move_widget(self, from_pane_id: str, to_pane_id: str) -> bool:
        """
        Move an AppWidget from one pane to another.

        Args:
            from_pane_id: Source pane ID
            to_pane_id: Destination pane ID

        Returns:
            True if successful
        """
        from_leaf = self.find_leaf(from_pane_id)
        to_leaf = self.find_leaf(to_pane_id)

        if not from_leaf or not to_leaf:
            return False

        logger.info(f"Moving widget from {from_pane_id} to {to_pane_id}")

        # Swap AppWidgets
        from_leaf.app_widget, to_leaf.app_widget = (
            to_leaf.app_widget,
            from_leaf.app_widget,
        )

        # Update back-references
        if from_leaf.app_widget:
            from_leaf.app_widget.leaf_node = from_leaf
        if to_leaf.app_widget:
            to_leaf.app_widget.leaf_node = to_leaf

        # Swap widget types
        from_leaf.widget_type, to_leaf.widget_type = (
            to_leaf.widget_type,
            from_leaf.widget_type,
        )

        return True

    def to_dict(self) -> dict:
        """
        Serialize model to dictionary for persistence.

        Returns:
            Dictionary representation of the model
        """

        def node_to_dict(node):
            if isinstance(node, LeafNode):
                return {
                    "type": "leaf",
                    "id": node.id,
                    "widget_type": node.widget_type.value,
                    "widget_state": (node.app_widget.get_state() if node.app_widget else {}),
                }
            elif isinstance(node, SplitNode):
                return {
                    "type": "split",
                    "id": node.id,
                    "orientation": node.orientation,
                    "ratio": node.ratio,
                    "first": node_to_dict(node.first) if node.first else None,
                    "second": node_to_dict(node.second) if node.second else None,
                }
            return None

        return {
            "root": node_to_dict(self.root),
            "active_pane_id": self.active_pane_id,
            "show_pane_numbers": self.show_pane_numbers,
        }

    def from_dict(self, data: dict):
        """
        Restore model from dictionary.

        Args:
            data: Dictionary representation of the model

        Raises:
            ValueError: If the data format is invalid
            RuntimeError: If widget creation fails
        """
        if not data or "root" not in data:
            raise ValueError("Invalid state data: missing root node")

        # Clean up existing widgets first
        self.cleanup_all_widgets()

        def dict_to_node(node_dict, parent=None):
            if not node_dict:
                return None

            try:
                if node_dict["type"] == "leaf":
                    leaf = LeafNode(
                        id=node_dict["id"],
                        widget_type=WidgetType(node_dict["widget_type"]),
                        parent=parent,
                    )

                    # Create AppWidget
                    logger.debug(
                        f"Creating AppWidget for leaf {leaf.id} of type {leaf.widget_type}"
                    )
                    leaf.app_widget = self.create_app_widget(leaf.widget_type, leaf.id)
                    if not leaf.app_widget:
                        logger.error(
                            f"Failed to create widget for leaf {leaf.id} of type {leaf.widget_type}"
                        )
                        # Create a placeholder editor widget as fallback
                        leaf.widget_type = WidgetType.TEXT_EDITOR
                        logger.info(f"Attempting fallback to TEXT_EDITOR for leaf {leaf.id}")
                        leaf.app_widget = self.create_app_widget(leaf.widget_type, leaf.id)
                        if not leaf.app_widget:
                            logger.critical(
                                f"Even fallback widget creation failed for leaf {leaf.id}"
                            )

                    if leaf.app_widget:
                        leaf.app_widget.leaf_node = leaf
                        logger.debug(
                            f"Successfully created AppWidget {leaf.app_widget.widget_id} for leaf {leaf.id}"
                        )

                    # Restore widget state
                    if "widget_state" in node_dict and leaf.app_widget:
                        try:
                            leaf.app_widget.set_state(node_dict["widget_state"])
                        except Exception as e:
                            logger.warning(f"Failed to restore widget state for {leaf.id}: {e}")

                    self.leaves[leaf.id] = leaf
                    return leaf

                elif node_dict["type"] == "split":
                    split = SplitNode(
                        id=node_dict["id"],
                        orientation=node_dict["orientation"],
                        ratio=node_dict.get("ratio", 0.5),
                        parent=parent,
                    )
                    split.first = dict_to_node(node_dict.get("first"), split)
                    split.second = dict_to_node(node_dict.get("second"), split)

                    # Validate split node has at least one valid child
                    if not split.first and not split.second:
                        logger.error(f"Split node {split.id} has no valid children")
                        return None

                    return split

            except Exception as e:
                logger.error(f"Failed to restore node: {e}")
                # Return a default leaf node as fallback
                if parent is None:  # Only create fallback for root level
                    fallback_id = f"fallback_{uuid.uuid4().hex[:8]}"
                    leaf = LeafNode(
                        id=fallback_id,
                        widget_type=WidgetType.TEXT_EDITOR,
                        parent=parent,
                    )
                    leaf.app_widget = self.create_app_widget(leaf.widget_type, leaf.id)
                    leaf.app_widget.leaf_node = leaf
                    self.leaves[leaf.id] = leaf
                    return leaf
                return None

            return None

        self.leaves.clear()
        self.root = dict_to_node(data["root"])

        # If root restoration failed completely, create a default root
        if not self.root:
            logger.error("Failed to restore root node, creating default")
            default_id = f"default_{uuid.uuid4().hex[:8]}"
            self.root = LeafNode(id=default_id, widget_type=WidgetType.TEXT_EDITOR)
            self.root.app_widget = self.create_app_widget(self.root.widget_type, default_id)
            self.root.app_widget.leaf_node = self.root
            self.leaves[default_id] = self.root

        self.active_pane_id = data.get("active_pane_id", "")

        # Validate active pane
        if self.active_pane_id not in self.leaves and self.leaves:
            self.active_pane_id = next(iter(self.leaves.keys()))
            logger.warning(
                f"Active pane {self.active_pane_id} not found, using {self.active_pane_id}"
            )

        # Restore pane numbering state
        self.show_pane_numbers = data.get("show_pane_numbers", False)
        self.update_pane_indices()

    def calculate_pane_bounds(
        self,
        pane_id: str,
        node: Optional[Union[LeafNode, SplitNode]] = None,
        bounds: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0),
    ) -> Optional[tuple[float, float, float, float]]:
        """
        Calculate the normalized bounds [x1, y1, x2, y2] of a pane.

        Args:
            pane_id: ID of the pane to find bounds for
            node: Current node in traversal (defaults to root)
            bounds: Current bounds during traversal

        Returns:
            Tuple of (x1, y1, x2, y2) in range [0.0, 1.0], or None if not found
        """
        if node is None:
            node = self.root

        x1, y1, x2, y2 = bounds

        if isinstance(node, LeafNode):
            if node.id == pane_id:
                return bounds
            return None

        elif isinstance(node, SplitNode):
            if node.orientation == "horizontal":
                # Split horizontally: first is left, second is right
                split_x = x1 + (x2 - x1) * node.ratio

                # Check first (left) child
                result = self.calculate_pane_bounds(pane_id, node.first, (x1, y1, split_x, y2))
                if result:
                    return result

                # Check second (right) child
                return self.calculate_pane_bounds(pane_id, node.second, (split_x, y1, x2, y2))

            else:  # vertical split
                # Split vertically: first is top, second is bottom
                split_y = y1 + (y2 - y1) * node.ratio

                # Check first (top) child
                result = self.calculate_pane_bounds(pane_id, node.first, (x1, y1, x2, split_y))
                if result:
                    return result

                # Check second (bottom) child
                return self.calculate_pane_bounds(pane_id, node.second, (x1, split_y, x2, y2))

        return None

    def find_pane_in_direction(self, from_pane_id: str, direction: str) -> Optional[str]:
        """
        Find the best pane to navigate to in the given direction.

        Uses tree structure and position overlap to find the most intuitive target.

        Args:
            from_pane_id: ID of the source pane
            direction: One of "left", "right", "up", "down"

        Returns:
            ID of the target pane, or None if no valid target
        """
        # Get bounds of source pane
        source_bounds = self.calculate_pane_bounds(from_pane_id)
        if not source_bounds:
            logger.warning(f"Could not calculate bounds for pane {from_pane_id}")
            return None

        sx1, sy1, sx2, sy2 = source_bounds
        source_center_x = (sx1 + sx2) / 2
        source_center_y = (sy1 + sy2) / 2

        # Find all candidate panes
        candidates = []

        for leaf_id, _leaf in self.leaves.items():
            if leaf_id == from_pane_id:
                continue

            target_bounds = self.calculate_pane_bounds(leaf_id)
            if not target_bounds:
                continue

            tx1, ty1, tx2, ty2 = target_bounds
            target_center_x = (tx1 + tx2) / 2
            target_center_y = (ty1 + ty2) / 2

            # Check if pane is in the target direction
            is_candidate = False

            if direction == "left" and target_center_x < source_center_x:
                is_candidate = True
            elif direction == "right" and target_center_x > source_center_x:
                is_candidate = True
            elif direction == "up" and target_center_y < source_center_y:
                is_candidate = True
            elif direction == "down" and target_center_y > source_center_y:
                is_candidate = True

            if is_candidate:
                # Calculate overlap for scoring
                if direction in ["left", "right"]:
                    # For horizontal movement, check Y-axis overlap
                    overlap = max(0, min(sy2, ty2) - max(sy1, ty1))
                    # Distance in the movement direction
                    distance = abs(target_center_x - source_center_x)
                else:  # up/down
                    # For vertical movement, check X-axis overlap
                    overlap = max(0, min(sx2, tx2) - max(sx1, tx1))
                    # Distance in the movement direction
                    distance = abs(target_center_y - source_center_y)

                candidates.append(
                    {
                        "id": leaf_id,
                        "overlap": overlap,
                        "distance": distance,
                        "center_x": target_center_x,
                        "center_y": target_center_y,
                    }
                )

        if not candidates:
            return None

        # Sort candidates by overlap (descending) then distance (ascending)
        # Prefer maximum overlap, then minimum distance
        candidates.sort(key=lambda c: (-c["overlap"], c["distance"]))

        # If there's a tie in overlap and distance, use position as tiebreaker
        if len(candidates) > 1:
            first = candidates[0]
            tied = [
                c
                for c in candidates
                if c["overlap"] == first["overlap"]
                and abs(c["distance"] - first["distance"]) < 0.001
            ]

            if len(tied) > 1:
                # Apply directional tiebreaker
                if direction == "left":
                    # Prefer rightmost of tied candidates
                    tied.sort(key=lambda c: -c["center_x"])
                elif direction == "right":
                    # Prefer leftmost of tied candidates
                    tied.sort(key=lambda c: c["center_x"])
                elif direction == "up":
                    # Prefer bottommost of tied candidates
                    tied.sort(key=lambda c: -c["center_y"])
                elif direction == "down":
                    # Prefer topmost of tied candidates
                    tied.sort(key=lambda c: c["center_y"])

                return tied[0]["id"]

        return candidates[0]["id"]
