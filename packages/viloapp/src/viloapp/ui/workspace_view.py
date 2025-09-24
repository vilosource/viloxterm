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
from viloapp.core.widget_metadata import widget_metadata_registry
from viloapp.models.workspace_model import (
    Pane,
    PaneNode,
    Tab,
    WorkspaceModel,
)


class WidgetFactory:
    """Factory for creating actual widget instances through the plugin system."""

    @staticmethod
    def create(widget_id: str, pane_id: str) -> QWidget:
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
            widget = app_widget_manager.create_widget_by_id(widget_id, pane_id)

            if widget:
                logger.debug(f"Created widget {widget_id} with id {pane_id} via plugin system")
                return widget
            else:
                logger.warning(f"AppWidgetManager could not create widget for type {widget_id}")

        except ImportError as e:
            logger.error(f"Could not import AppWidgetManager: {e}")
        except Exception as e:
            logger.error(f"Error creating widget through plugin system: {e}")

        # Fallback to a placeholder widget if plugin system fails
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel(f"{widget_id.split('.')[-1].upper()}\n(Plugin not available)")
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
        self.content_widget = None  # The actual app widget (terminal, editor, etc.)

        # Comprehensive flicker prevention attributes
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_StaticContents, True)
        self.setAttribute(Qt.WA_DontCreateNativeAncestors, True)
        # No borders for clean appearance
        self.setStyleSheet(
            """
            PaneView {
                background-color: #252526;
                border: none;
            }
        """
        )

        self.setup_ui()

    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar with pane controls
        header = self.create_header()
        layout.addWidget(header)

        # Get widget from AppWidgetManager - it handles caching and lifecycle
        try:
            from viloapp.core.app_widget_manager import app_widget_manager

            self.content_widget = app_widget_manager.get_or_create_widget(
                self.pane.widget_id, self.pane.id
            )
        except ImportError:
            # Fallback if AppWidgetManager not available
            import logging

            logging.getLogger(__name__).warning(
                "AppWidgetManager not available, using WidgetFactory directly"
            )
            self.content_widget = WidgetFactory.create(self.pane.widget_id, self.pane.id)

        if not self.content_widget:
            # Create a placeholder if widget creation failed
            from PySide6.QtWidgets import QLabel

            self.content_widget = QLabel("Widget unavailable")
            self.content_widget.setAlignment(Qt.AlignCenter)
            self.content_widget.setStyleSheet("color: #999; background: #2d2d30;")

        layout.addWidget(self.content_widget)

        # Don't call update_style() here - style already set in __init__

    def create_header(self) -> QWidget:
        """Create pane header with controls."""
        header = QWidget()
        header.setFixedHeight(22)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(5, 1, 5, 1)
        layout.setSpacing(2)

        # Widget type label
        display_name = widget_metadata_registry.get_display_name(self.pane.widget_id)
        type_label = QLabel(display_name)
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
                    background-color: #252526;
                    border: 1px solid #007ACC;
                    outline: 1px solid #007ACC;
                }
                """
            )
        else:
            self.setStyleSheet(
                """
                PaneView {
                    background-color: #252526;
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
    Pure view for rendering a pane tree with widget preservation.

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
        self.current_root_widget = None
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI by rendering the tree."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Render the tree starting from root
        self.current_root_widget = self.render_node(self.root)
        if self.current_root_widget:
            layout.addWidget(self.current_root_widget)

    def refresh_tree(self, new_root: PaneNode, atomic_update=True):
        """Refresh tree preserving existing widgets.

        Args:
            atomic_update: Whether to use atomic updates (disable/enable updates)
        """
        import logging

        logger = logging.getLogger(__name__)

        logger.debug(f"TreeView.refresh_tree called with atomic_update={atomic_update}")
        self.root = new_root

        # Widget lifecycle is now managed by AppWidgetManager
        # Cleanup happens automatically when panes are closed

        # Conditionally disable all updates during tree reconstruction
        if atomic_update:
            self.setUpdatesEnabled(False)
            # Also prevent child widget updates
            if self.current_root_widget:
                self.current_root_widget.setUpdatesEnabled(False)

        try:
            # Build new tree completely off-screen
            logger.debug("Building new root widget from model tree")
            new_root_widget = self.render_node(self.root)
            logger.debug(
                f"render_node returned: {type(new_root_widget) if new_root_widget else None}"
            )

            if new_root_widget:
                layout = self.layout()
                logger.debug(f"Layout has {layout.count()} widgets before refresh")

                # For close operations, don't hide widget to prevent white flash
                if self.current_root_widget:
                    logger.debug("Removing old root widget")
                    if atomic_update:
                        self.current_root_widget.setVisible(False)
                    layout.removeWidget(self.current_root_widget)
                    # Don't delete immediately - let Qt handle it
                    self.current_root_widget.deleteLater()

                # Add new widget and make it visible
                logger.debug("Adding new root widget to layout")
                self.current_root_widget = new_root_widget
                layout.addWidget(new_root_widget)
                # Always ensure widget is visible
                new_root_widget.setVisible(True)
                new_root_widget.show()  # Force show the widget

                logger.debug(f"Layout has {layout.count()} widgets after refresh")

                # Force layout update
                layout.update()
                self.update()  # Update the TreeView itself
            else:
                logger.error("CRITICAL ERROR: render_node returned None! Layout will be empty!")
                logger.error("This is the cause of white tabs - attempting recovery...")

                # Attempt recovery by validating and cleaning registry
                # Validation handled by AppWidgetManager
                pass

                # Try to build a minimal fallback widget
                fallback_widget = self._create_fallback_widget()
                if fallback_widget:
                    logger.info("Created fallback widget to prevent empty layout")
                    layout = self.layout()
                    if self.current_root_widget:
                        layout.removeWidget(self.current_root_widget)
                        self.current_root_widget.deleteLater()

                    self.current_root_widget = fallback_widget
                    layout.addWidget(fallback_widget)
                else:
                    logger.error("Could not create fallback widget - tab will be white!")

        except Exception as e:
            logger.error(f"ERROR in refresh_tree: {e}")
            import traceback

            logger.error(traceback.format_exc())
            raise
        finally:
            # Re-enable updates only if we disabled them
            if atomic_update:
                self.setUpdatesEnabled(True)

        # Refresh complete

        logger.debug("TreeView.refresh_tree completed")

    def _create_fallback_widget(self):
        """Create a fallback widget when tree building fails.

        Returns:
            QWidget: A minimal widget to prevent empty layout
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            from PySide6.QtWidgets import QLabel, QVBoxLayout

            fallback = QWidget()
            layout = QVBoxLayout(fallback)
            layout.setContentsMargins(20, 20, 20, 20)

            label = QLabel(
                "Layout Error Recovery\n\nThe pane layout failed to build.\nTry creating a new split."
            )
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet(
                """
                QLabel {
                    background-color: #2d2d30;
                    color: #cccccc;
                    padding: 20px;
                    border: 2px dashed #555;
                    font-size: 14px;
                }
                """
            )
            layout.addWidget(label)

            fallback.setStyleSheet("QWidget { background-color: #252526; }")
            logger.info("Created fallback error recovery widget")
            return fallback

        except Exception as e:
            logger.error(f"Failed to create fallback widget: {e}")
            return None

    def render_node(self, node: PaneNode) -> Optional[QWidget]:
        """Recursively render a node preserving existing widgets."""
        import logging

        logger = logging.getLogger(__name__)

        if not node:
            logger.error("render_node called with None node!")
            return None

        logger.debug(f"render_node: processing node type={node.node_type.value}")

        if node.is_leaf() and node.pane:
            pane_id = node.pane.id
            logger.debug(f"render_node: leaf node with pane {pane_id[:8]}")

            # Create new PaneView - widget reuse is managed by AppWidgetManager
            # The PaneView itself is just a wrapper that gets recreated
            # The actual content widget (terminal, editor) is preserved
            logger.debug(f"render_node: creating PaneView for {pane_id[:8]}")
            pane_view = PaneView(node.pane, self.command_registry, self.model)
            return pane_view

        elif node.is_split() and node.first and node.second:
            logger.debug(f"render_node: split node with orientation={node.orientation}")

            # Always create new splitters - don't reuse them since tree structure changes
            # Only PaneViews should be reused, not structural widgets
            from viloapp.models.workspace_model import Orientation

            splitter = QSplitter(
                Qt.Horizontal if node.orientation == Orientation.HORIZONTAL else Qt.Vertical
            )

            # CRITICAL: Comprehensive QSplitter optimizations to prevent artifacts
            # 1. Prevent children collapsing - major source of border artifacts
            splitter.setChildrenCollapsible(False)

            # 2. Disable opaque resize to prevent intermediate redraws during dragging
            splitter.setOpaqueResize(False)

            # 3. Set handle width explicitly to prevent size calculation issues
            splitter.setHandleWidth(3)

            # 4. Qt rendering attributes for maximum flicker prevention
            splitter.setAttribute(Qt.WA_OpaquePaintEvent, True)
            splitter.setAttribute(Qt.WA_NoSystemBackground, True)
            splitter.setAttribute(Qt.WA_StaticContents, True)  # Hint that content is static
            splitter.setAttribute(Qt.WA_DontCreateNativeAncestors, True)  # Avoid native windows

            # 5. Complete styling with explicit dimensions to prevent ambiguity
            splitter.setAutoFillBackground(True)
            splitter.setStyleSheet(
                """
                QSplitter {
                    background-color: #252526;
                }
                QSplitter::handle {
                    background-color: #3c3c3c;
                    border: none;
                    margin: 0px;
                }
                QSplitter::handle:horizontal {
                    width: 3px;
                    min-width: 3px;
                    max-width: 3px;
                }
                QSplitter::handle:vertical {
                    height: 3px;
                    min-height: 3px;
                    max-height: 3px;
                }
                """
            )

            # Recursively render children
            logger.debug("render_node: rendering first child")
            first_widget = self.render_node(node.first)
            if first_widget:
                logger.debug(
                    f"render_node: adding first widget {type(first_widget).__name__} to splitter"
                )
                splitter.addWidget(first_widget)
            else:
                logger.error("render_node: first child returned None!")

            logger.debug("render_node: rendering second child")
            second_widget = self.render_node(node.second)
            if second_widget:
                logger.debug(
                    f"render_node: adding second widget {type(second_widget).__name__} to splitter"
                )
                splitter.addWidget(second_widget)
            else:
                logger.error("render_node: second child returned None!")

            # Validate splitter has children
            final_count = splitter.count()
            logger.debug(f"render_node: splitter has {final_count} children after building")
            if final_count == 0:
                logger.error("render_node: splitter has no children! This will cause empty layout!")
                return None

            # Set split ratio with minimum sizes to prevent collapse artifacts
            total = 1000
            first_size = max(50, int(total * node.ratio))  # Minimum 50px to prevent collapse
            second_size = max(50, total - first_size)
            splitter.setSizes([first_size, second_size])

            return splitter

        logger.error(
            f"render_node: Unknown node type or invalid node structure: type={node.node_type}, is_leaf={node.is_leaf()}, is_split={node.is_split()}"
        )
        return None

        return None


class TabView(QWidget):
    """
    Pure view for a single tab.

    Renders the tab's pane tree with widget preservation.
    """

    def __init__(self, tab: Tab, command_registry: CommandRegistry, model: WorkspaceModel):
        """Initialize tab view."""
        super().__init__()
        self.tab = tab
        self.command_registry = command_registry
        self.model = model
        self.tree_view = None
        # Widget registry removed - managed by AppWidgetManager
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Render the tree
        self.tree_view = TreeView(self.tab.tree.root, self.command_registry, self.model)
        layout.addWidget(self.tree_view)

    def refresh_content(self, atomic_update=True):
        """Refresh content preserving existing widgets.

        Args:
            atomic_update: Whether to use atomic updates (disable/enable updates)
        """
        import logging

        logger = logging.getLogger(__name__)

        logger.debug(f"TabView.refresh_content called with atomic_update={atomic_update}")
        logger.debug(f"Tab ID: {self.tab.id}, Tab name: {self.tab.name}")
        # Widget tracking moved to AppWidgetManager
        # Log current model panes for debugging
        model_panes = self.tab.tree.root.get_all_panes()
        logger.debug(f"Model has {len(model_panes)} panes: {[p.id[:8] for p in model_panes]}")

        # Proactively clean up orphaned entries before refresh
        if self.tree_view:
            # Widget tracking moved to AppWidgetManager
            pass

        if self.tree_view:
            # Conditionally ensure the entire TabView update is atomic
            if atomic_update:
                self.setUpdatesEnabled(False)

            try:
                logger.debug("Calling tree_view.refresh_tree()")
                self.tree_view.refresh_tree(self.tab.tree.root, atomic_update=atomic_update)
                logger.debug("tree_view.refresh_tree() completed")
            except Exception as e:
                logger.error(f"ERROR in tree_view.refresh_tree(): {e}")
                import traceback

                logger.error(traceback.format_exc())
                raise
            finally:
                if atomic_update:
                    self.setUpdatesEnabled(True)
        else:
            logger.warning("No tree_view available for refresh")


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
        # Only set structural styles here, let theme system handle colors
        self.setStyleSheet(
            """
            QTabBar::tab {
                padding: 2px 8px;
                margin-right: 1px;
                font-size: 13px;
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

        # Tab type buttons - get available widget types from app widget manager
        try:
            from viloapp.core.app_widget_manager import app_widget_manager

            available_widgets = app_widget_manager.get_available_widgets()

            for widget_id in available_widgets[:3]:  # Limit to first 3 for space
                display_name = widget_id.split(".")[-1].title()
                btn = QPushButton(f"+ {display_name}")
                btn.clicked.connect(lambda checked, wt=widget_id: self.create_new_tab(wt))
                layout.addWidget(btn)
        except (ImportError, AttributeError):
            # Fallback to basic widget types
            fallback_widgets = ["com.viloapp.terminal", "com.viloapp.editor", "com.viloapp.output"]
            for widget_id in fallback_widgets:
                display_name = widget_id.split(".")[-1].title()
                btn = QPushButton(f"+ {display_name}")
                btn.clicked.connect(lambda checked, wt=widget_id: self.create_new_tab(wt))
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

    def create_new_tab(self, widget_id: Optional[str] = None):
        """Create a new tab through command."""
        # Use provided widget_id or get default editor
        if not widget_id:
            from viloapp.core.app_widget_manager import app_widget_manager

            widget_id = app_widget_manager.get_default_editor_id()
            if not widget_id:
                widget_id = app_widget_manager.get_default_widget_id()
            if not widget_id:
                widget_id = "com.viloapp.placeholder"

        context = CommandContext(model=self.model)
        self.command_registry.execute(
            "tab.create",
            context,
            name=f"New {widget_id.split('.')[-1].title()}",
            widget_id=widget_id,
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

    # Create tabs through commands using proper widget IDs
    registry.execute("tab.create", context, name="Editor", widget_id="com.viloapp.editor")
    registry.execute("tab.create", context, name="Terminal", widget_id="com.viloapp.terminal")

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
