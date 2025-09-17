#!/usr/bin/env python3
"""
Test application for recursive split pane functionality.
Demonstrates tree-based split model with QTextEdit widgets and context menu operations.
"""

import sys
import uuid
from dataclasses import dataclass, field
from typing import Optional, Union

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QSplitter,
    QTextEdit,
    QWidget,
)

# ============================================================================
# Tree Model Classes
# ============================================================================


@dataclass
class LeafNode:
    """Leaf node containing a widget."""

    type: str = "leaf"
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    widget: Optional[QWidget] = None
    parent: Optional["SplitNode"] = None


@dataclass
class SplitNode:
    """Split node containing two children."""

    type: str = "split"
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    orientation: str = "horizontal"  # "horizontal" or "vertical"
    ratio: float = 0.5
    first: Optional[Union[LeafNode, "SplitNode"]] = None
    second: Optional[Union[LeafNode, "SplitNode"]] = None
    parent: Optional["SplitNode"] = None
    splitter: Optional[QSplitter] = None  # View reference

    def __post_init__(self):
        if self.first:
            self.first.parent = self
        if self.second:
            self.second.parent = self


# ============================================================================
# Custom Text Editor Widget
# ============================================================================


class PaneTextEdit(QTextEdit):
    """Text editor with context menu for split operations."""

    split_horizontal_requested = Signal(str)
    split_vertical_requested = Signal(str)
    close_requested = Signal(str)

    def __init__(self, pane_id: str, parent=None):
        super().__init__(parent)
        self.pane_id = pane_id
        self.setup_ui()

    def setup_ui(self):
        """Initialize the text editor."""
        self.setPlainText(
            f"Pane {self.pane_id}\n\nRight-click for options:\n"
            "• Split Horizontal (left|right)\n"
            "• Split Vertical (top|bottom)\n"
            "• Close Pane"
        )

        # Style the editor
        self.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 10px;
            }
            QTextEdit:focus {
                border: 2px solid #007ACC;
            }
        """
        )

    def contextMenuEvent(self, event):
        """Show custom context menu."""
        menu = QMenu(self)

        # Split actions
        split_h = QAction("Split Horizontal", self)
        split_h.triggered.connect(
            lambda: self.split_horizontal_requested.emit(self.pane_id)
        )
        menu.addAction(split_h)

        split_v = QAction("Split Vertical", self)
        split_v.triggered.connect(
            lambda: self.split_vertical_requested.emit(self.pane_id)
        )
        menu.addAction(split_v)

        menu.addSeparator()

        # Close action
        close = QAction("Close Pane", self)
        close.triggered.connect(lambda: self.close_requested.emit(self.pane_id))
        menu.addAction(close)

        menu.exec(event.globalPos())


# ============================================================================
# Split Pane Manager
# ============================================================================


class SplitPaneManager(QObject):
    """Manages the tree-based split pane model and view."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.root: Union[LeafNode, SplitNode] = None
        self.leaves: dict[str, LeafNode] = {}
        self.widgets: dict[str, PaneTextEdit] = {}
        self.initialize_root()

    def initialize_root(self):
        """Create initial root leaf."""
        self.root = LeafNode()
        self.leaves[self.root.id] = self.root

    def create_view(self) -> QWidget:
        """Build Qt widget tree from model."""
        self.widgets.clear()
        return self._render_node(self.root)

    def _render_node(self, node: Union[LeafNode, SplitNode]) -> QWidget:
        """Recursively render a node to Qt widgets."""
        if isinstance(node, LeafNode):
            # Create text editor for leaf
            editor = PaneTextEdit(node.id)

            # Connect signals
            editor.split_horizontal_requested.connect(self.split_horizontal)
            editor.split_vertical_requested.connect(self.split_vertical)
            editor.close_requested.connect(self.close_pane)

            # Store references
            node.widget = editor
            self.widgets[node.id] = editor

            return editor

        elif isinstance(node, SplitNode):
            # Create splitter
            if node.orientation == "horizontal":
                # Horizontal split = left|right
                splitter = QSplitter(Qt.Horizontal)
            else:
                # Vertical split = top|bottom
                splitter = QSplitter(Qt.Vertical)

            # Render children
            if node.first:
                first_widget = self._render_node(node.first)
                splitter.addWidget(first_widget)

            if node.second:
                second_widget = self._render_node(node.second)
                splitter.addWidget(second_widget)

            # Apply ratio
            total_size = 1000
            first_size = int(total_size * node.ratio)
            second_size = total_size - first_size
            splitter.setSizes([first_size, second_size])

            # Track splitter movements
            splitter.splitterMoved.connect(lambda: self._update_ratio(node, splitter))

            # Store reference
            node.splitter = splitter

            return splitter

    def _update_ratio(self, node: SplitNode, splitter: QSplitter):
        """Update split ratio when user drags splitter."""
        sizes = splitter.sizes()
        total = sum(sizes)
        if total > 0:
            node.ratio = sizes[0] / total

    def split_horizontal(self, leaf_id: str):
        """Split leaf horizontally (left|right)."""
        self._split_leaf(leaf_id, "horizontal")

    def split_vertical(self, leaf_id: str):
        """Split leaf vertically (top|bottom)."""
        self._split_leaf(leaf_id, "vertical")

    def _split_leaf(self, leaf_id: str, orientation: str):
        """Split a leaf node."""
        leaf = self.leaves.get(leaf_id)
        if not leaf:
            print(f"Error: Leaf {leaf_id} not found!")
            return

        # Store the parent before creating split
        old_parent = leaf.parent

        # Create new leaf for right/bottom
        new_leaf = LeafNode()

        # Create split node WITHOUT setting children yet to avoid parent confusion
        split = SplitNode(
            orientation=orientation,
            ratio=0.5,
            first=None,  # Set these after
            second=None,
        )

        # Now set the children and their parents
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
            print(f"Setting split node as new root (was leaf {leaf_id})")
            self.root = split

        # Update tracking - keep existing leaf, add new one
        self.leaves[new_leaf.id] = new_leaf

        print(f"Split {orientation}: {leaf_id} -> {leaf_id} | {new_leaf.id}")
        print(f"Leaves in tree: {list(self.leaves.keys())}")

        # Trigger view update
        if self.parent() and hasattr(self.parent(), "refresh_view"):
            self.parent().refresh_view()

    def close_pane(self, leaf_id: str):
        """Close a leaf pane and promote its sibling."""
        leaf = self.leaves.get(leaf_id)
        if not leaf:
            return

        # Case 1: Leaf is root (only pane) - don't allow
        if leaf == self.root:
            print("Cannot close last pane")
            return

        print(f"Closing pane: {leaf_id}")

        # Case 2: Leaf has parent
        parent = leaf.parent
        if not parent:
            return

        # Find sibling
        sibling = parent.second if parent.first == leaf else parent.first
        if not sibling:
            return

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
        del self.leaves[leaf_id]

        # Clean up widget
        if leaf_id in self.widgets:
            self.widgets[leaf_id].deleteLater()
            del self.widgets[leaf_id]

        # Trigger view update
        if self.parent() and hasattr(self.parent(), "refresh_view"):
            self.parent().refresh_view()

    def print_tree(self, node=None, indent=0):
        """Debug: print tree structure."""
        if node is None:
            node = self.root
            print(f"Root type: {type(node).__name__}")

        prefix = "  " * indent

        if isinstance(node, LeafNode):
            print(f"{prefix}Leaf({node.id})")
        elif isinstance(node, SplitNode):
            orient = "H" if node.orientation == "horizontal" else "V"
            print(f"{prefix}Split({orient}, {node.ratio:.2f})")
            if node.first:
                self.print_tree(node.first, indent + 1)
            if node.second:
                self.print_tree(node.second, indent + 1)


# ============================================================================
# Main Window
# ============================================================================


class RecursiveSplitTestWindow(QMainWindow):
    """Main window for testing recursive split functionality."""

    def __init__(self):
        super().__init__()
        self.manager = SplitPaneManager()
        self.manager.setParent(self)  # Set parent explicitly
        self.setup_ui()

    def setup_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("Recursive Split Pane Test")
        self.setGeometry(100, 100, 1200, 800)

        # Dark theme for the window
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #1e1e1e;
            }
            QSplitter::handle {
                background-color: #3c3c3c;
            }
            QSplitter::handle:horizontal {
                width: 4px;
            }
            QSplitter::handle:vertical {
                height: 4px;
            }
            QSplitter::handle:hover {
                background-color: #007ACC;
            }
        """
        )

        # Create initial view
        self.refresh_view()

    def refresh_view(self):
        """Rebuild the view from the model."""
        # Get current central widget and clean it up
        old_central = self.centralWidget()
        if old_central:
            old_central.setParent(None)
            old_central.deleteLater()

        # Create new view from model
        central = self.manager.create_view()
        self.setCentralWidget(central)

        # Force update
        central.show()

        # Debug: print tree structure
        print("\nCurrent tree structure:")
        self.manager.print_tree()


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Run the test application."""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    # Create and show window
    window = RecursiveSplitTestWindow()
    window.show()

    # Add instructions
    print("=== Recursive Split Pane Test Application ===")
    print("Right-click on any pane to:")
    print("  • Split Horizontal (creates left|right split)")
    print("  • Split Vertical (creates top|bottom split)")
    print("  • Close Pane (removes pane and promotes sibling)")
    print("\nDrag splitter handles to resize panes")
    print("=" * 45)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
