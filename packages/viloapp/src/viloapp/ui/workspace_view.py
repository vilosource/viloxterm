"""
Pure view layer for ViloxTerm.

Views are stateless and render purely from the model.
They observe model changes and re-render as needed.
NO business logic, NO state storage, just presentation.
"""

from typing import Any, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from viloapp.core.commands.base import CommandContext
from viloapp.core.commands.registry import CommandRegistry
from viloapp.models.workspace_model import Pane, PaneNode, Tab, WidgetType, WorkspaceModel


class WidgetFactory:
    """Factory for creating actual widget instances through the plugin system."""

    @staticmethod
    def create(widget_type: WidgetType, pane_id: str) -> QWidget:
        """
        Create a widget instance based on type using the plugin system.

        This properly uses AppWidgetManager to create widgets through plugins.
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Get the AppWidgetManager instance
            from viloapp.core.app_widget_manager import app_widget_manager

            # Create widget through the plugin system
            widget = app_widget_manager.create_widget_by_type(widget_type, pane_id)

            if widget:
                logger.debug(
                    f"Created widget {widget_type.value} with id {pane_id} via plugin system"
                )
                return widget
            else:
                logger.warning(f"AppWidgetManager could not create widget for type {widget_type}")

        except ImportError as e:
            logger.error(f"Could not import AppWidgetManager: {e}")
        except Exception as e:
            logger.error(f"Error creating widget through plugin system: {e}")

        # Fallback to a placeholder widget if plugin system fails
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel(f"{widget_type.value.upper()}\n(Plugin not available)")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(
            """
            QLabel {
                background-color: #2d2d30;
                color: #cccccc;
                padding: 20px;
                border: 1px dashed #555;
            }
            """
        )
        layout.addWidget(label)
        widget.setObjectName(f"placeholder_{pane_id[:8]}")
        return widget


class PaneView(QWidget):
    """
    Pure view for a single pane.

    Renders a pane from the model. Has NO state.
    """

    # Signals
    split_requested = Signal(str, str)  # pane_id, orientation
    close_requested = Signal(str)  # pane_id
    focus_requested = Signal(str)  # pane_id
    widget_change_requested = Signal(str, str)  # pane_id, widget_type

    def __init__(self, pane: Pane, command_registry: CommandRegistry, model: WorkspaceModel):
        """Initialize pane view."""
        super().__init__()
        self.pane = pane
        self.command_registry = command_registry
        self.model = model
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)

        # Header bar with pane controls
        header = self.create_header()
        layout.addWidget(header)

        # Actual widget content
        widget = WidgetFactory.create(self.pane.widget_type, self.pane.id)
        layout.addWidget(widget)

        # Style based on focus
        self.update_style()

    def create_header(self) -> QWidget:
        """Create pane header with controls."""
        header = QWidget()
        header.setFixedHeight(22)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(5, 1, 5, 1)
        layout.setSpacing(2)

        # Widget type label
        type_label = QLabel(self.pane.widget_type.value.title())
        type_label.setStyleSheet("color: #cccccc; font-weight: bold; font-size: 12px;")
        layout.addWidget(type_label)

        layout.addStretch()

        # Action buttons
        # Split horizontal (creates left-right panes)
        split_h_btn = QPushButton("│")
        split_h_btn.setFixedSize(18, 18)
        split_h_btn.setToolTip("Split Right")
        split_h_btn.clicked.connect(lambda: self.request_split("horizontal"))
        layout.addWidget(split_h_btn)

        # Split vertical (creates top-bottom panes)
        split_v_btn = QPushButton("─")
        split_v_btn.setFixedSize(18, 18)
        split_v_btn.setToolTip("Split Down")
        split_v_btn.clicked.connect(lambda: self.request_split("vertical"))
        layout.addWidget(split_v_btn)

        # Close
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(18, 18)
        close_btn.setToolTip("Close Pane")
        close_btn.clicked.connect(lambda: self.request_close())
        layout.addWidget(close_btn)

        header.setStyleSheet(
            """
            QWidget {
                background-color: #2d2d30;
                border-bottom: 1px solid #3c3c3c;
            }
            QPushButton {
                background-color: transparent;
                color: #cccccc;
                border: none;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
            }
            """
        )

        return header

    def update_style(self):
        """Update style based on focus state."""
        if self.pane.focused:
            self.setStyleSheet(
                """
                PaneView {
                    border: 2px solid #007ACC;
                }
                """
            )
        else:
            self.setStyleSheet(
                """
                PaneView {
                    border: 1px solid #3c3c3c;
                }
                """
            )

    def request_split(self, orientation: str):
        """Request pane split through command."""
        context = CommandContext(model=self.model)
        self.command_registry.execute(
            "pane.split", context, pane_id=self.pane.id, orientation=orientation
        )

    def request_close(self):
        """Request pane close through command."""
        context = CommandContext(model=self.model)
        self.command_registry.execute("pane.close", context, pane_id=self.pane.id)

    def mousePressEvent(self, event):  # noqa: N802
        """Handle mouse click for focus."""
        if event.button() == Qt.LeftButton:
            context = CommandContext(model=self.model)
            self.command_registry.execute("pane.focus", context, pane_id=self.pane.id)
        super().mousePressEvent(event)


class TreeView(QWidget):
    """
    Pure view for rendering a pane tree.

    Recursively renders the tree structure as Qt widgets.
    """

    def __init__(
        self,
        root: PaneNode,
        command_registry: CommandRegistry,
        model: WorkspaceModel,
    ):
        """Initialize tree view."""
        super().__init__()
        self.root = root
        self.command_registry = command_registry
        self.model = model
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI by rendering the tree."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Render the tree starting from root
        widget = self.render_node(self.root)
        if widget:
            layout.addWidget(widget)

    def render_node(self, node: PaneNode) -> Optional[QWidget]:
        """Recursively render a node."""
        if node.is_leaf() and node.pane:
            # Render leaf as PaneView
            return PaneView(node.pane, self.command_registry, self.model)

        elif node.is_split() and node.first and node.second:
            # Render split as QSplitter
            from viloapp.models.workspace_model import Orientation

            splitter = QSplitter(
                Qt.Horizontal if node.orientation == Orientation.HORIZONTAL else Qt.Vertical
            )

            # Recursively render children
            first_widget = self.render_node(node.first)
            if first_widget:
                splitter.addWidget(first_widget)

            second_widget = self.render_node(node.second)
            if second_widget:
                splitter.addWidget(second_widget)

            # Set split ratio
            total = 1000
            first_size = int(total * node.ratio)
            second_size = total - first_size
            splitter.setSizes([first_size, second_size])

            # Style the splitter
            splitter.setStyleSheet(
                """
                QSplitter::handle {
                    background-color: #3c3c3c;
                }
                QSplitter::handle:horizontal {
                    width: 2px;
                }
                QSplitter::handle:vertical {
                    height: 2px;
                }
                """
            )

            return splitter

        return None


class TabView(QWidget):
    """
    Pure view for a single tab.

    Renders the tab's pane tree.
    """

    def __init__(self, tab: Tab, command_registry: CommandRegistry, model: WorkspaceModel):
        """Initialize tab view."""
        super().__init__()
        self.tab = tab
        self.command_registry = command_registry
        self.model = model
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Render the tree
        tree_view = TreeView(self.tab.tree.root, self.command_registry, self.model)
        layout.addWidget(tree_view)


class WorkspaceView(QWidget):
    """
    Main workspace view.

    Renders all tabs and observes model changes.
    This is the top-level view component.
    """

    def __init__(self, model: WorkspaceModel, command_registry: Optional[CommandRegistry] = None):
        """Initialize workspace view."""
        super().__init__()
        self.model = model
        self.command_registry = command_registry or CommandRegistry()

        # Subscribe to model changes
        model.add_observer(self.on_model_change)

        # Tab widget
        self.tab_widget = None

        # Set up initial UI
        self.setup_ui()
        self.render()

    def setup_ui(self):
        """Set up the UI structure."""
        self.setStyleSheet(
            """
            WorkspaceView {
                background-color: #1e1e1e;
            }
            QTabWidget::pane {
                border: 1px solid #3c3c3c;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d30;
                color: #cccccc;
                padding: 8px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #3c3c3c;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.on_tab_close_requested)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        layout.addWidget(self.tab_widget)

        # Add toolbar
        toolbar = self.create_toolbar()
        layout.insertWidget(0, toolbar)

    def create_toolbar(self) -> QWidget:
        """Create toolbar with actions."""
        toolbar = QWidget()
        toolbar.setFixedHeight(35)
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(5, 2, 5, 2)

        # New tab button
        new_tab_btn = QPushButton("+ New Tab")
        new_tab_btn.clicked.connect(self.create_new_tab)
        layout.addWidget(new_tab_btn)

        # Tab type buttons
        for widget_type in [WidgetType.EDITOR, WidgetType.TERMINAL, WidgetType.OUTPUT]:
            btn = QPushButton(f"+ {widget_type.value.title()}")
            btn.clicked.connect(lambda checked, wt=widget_type: self.create_new_tab(wt))
            layout.addWidget(btn)

        layout.addStretch()

        toolbar.setStyleSheet(
            """
            QWidget {
                background-color: #252526;
                border-bottom: 1px solid #3c3c3c;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 5px 10px;
                margin: 0 2px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            """
        )

        return toolbar

    def render(self):
        """Render the entire workspace from model."""
        # Clear existing tabs
        self.tab_widget.clear()

        # Render each tab
        for tab in self.model.state.tabs:
            tab_view = TabView(tab, self.command_registry, self.model)
            index = self.tab_widget.addTab(tab_view, tab.name)

            # Set active tab
            if tab.id == self.model.state.active_tab_id:
                self.tab_widget.setCurrentIndex(index)

    def on_model_change(self, event: str, data: Any):
        """Handle model change events."""
        # For now, just re-render everything
        # In production, we'd do more efficient updates
        if event in [
            "tab_created",
            "tab_closed",
            "tab_renamed",
            "pane_split",
            "pane_closed",
            "pane_focused",
            "state_restored",
        ]:
            self.render()

    def create_new_tab(self, widget_type: WidgetType = WidgetType.EDITOR):
        """Create a new tab through command."""
        context = CommandContext(model=self.model)
        self.command_registry.execute(
            "tab.create",
            context,
            name=f"New {widget_type.value.title()}",
            widget_type=widget_type,
        )

    def on_tab_close_requested(self, index: int):
        """Handle tab close request."""
        if index >= 0 and index < len(self.model.state.tabs):
            tab = self.model.state.tabs[index]
            context = CommandContext(model=self.model)
            self.command_registry.execute("tab.close", context, tab_id=tab.id)

    def on_tab_changed(self, index: int):
        """Handle tab change."""
        if index >= 0 and index < len(self.model.state.tabs):
            tab = self.model.state.tabs[index]
            context = CommandContext(model=self.model)
            self.command_registry.execute("tab.switch", context, tab_id=tab.id)


# Helper function for testing
def create_test_app():
    """Create a test application with the view layer."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])

    # Create model
    model = WorkspaceModel()

    # Create command registry for test
    from viloapp.core.commands.registry import CommandRegistry

    registry = CommandRegistry()

    # Create some test data using commands
    context = CommandContext(model=model)

    # Create tabs through commands
    registry.execute("tab.create", context, name="Editor", widget_type=WidgetType.EDITOR)
    registry.execute("tab.create", context, name="Terminal", widget_type=WidgetType.TERMINAL)

    # Switch to first tab and split panes through commands
    if model.state.tabs:
        tab1 = model.state.tabs[0]
        registry.execute("tab.switch", context, tab_id=tab1.id)

        # Split panes through commands
        registry.execute("pane.split", context, orientation="horizontal")
        if tab1.tree.root.first and tab1.tree.root.first.pane:
            registry.execute(
                "pane.split", context, pane_id=tab1.tree.root.first.pane.id, orientation="vertical"
            )

    # Create view
    view = WorkspaceView(model)
    view.resize(1200, 800)
    view.show()

    return app, view
