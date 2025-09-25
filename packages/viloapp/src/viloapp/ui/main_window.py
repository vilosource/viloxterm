"""Main window implementation for the VSCode-style application."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QKeySequence
from PySide6.QtWidgets import QMainWindow

from viloapp.ui.main_window_actions import MainWindowActionManager
from viloapp.ui.main_window_layout import MainWindowLayoutManager
from viloapp.ui.main_window_state import MainWindowStateManager
from viloapp.ui.qt_compat import log_qt_versions
from viloapp.ui.widgets.focus_sink import FocusSinkWidget


class MainWindow(QMainWindow):
    """Main application window with VSCode-style layout."""

    def __init__(self):
        super().__init__()
        # Log Qt version information for debugging
        log_qt_versions()

        # Initialize managers
        self.layout_manager = MainWindowLayoutManager(self)
        self.action_manager = MainWindowActionManager(self)
        self.state_manager = MainWindowStateManager(self)

        # Initialize commands FIRST so UI components can use them
        self.initialize_commands()

        # Setup UI and initialize components
        self.setup_ui()
        self.initialize_services()
        self.initialize_keyboard()
        self.initialize_command_palette()
        self.initialize_focus_sink()  # Add focus sink initialization
        # Don't restore state here - it will be called from main.py after plugins are loaded

    def setup_ui(self):
        """Initialize the UI components."""
        # Set window title with dev mode indicator if applicable
        from viloapp.core.app_config import app_config

        dev_mode = app_config.dev_mode
        title = "ViloxTerm [DEV]" if dev_mode else "ViloxTerm"
        self.setWindowTitle(title)
        self.resize(1200, 800)

        # Note: Theme will be applied after services are initialized
        # We need ThemeProvider to be available first

        # Setup layout through layout manager
        self.layout_manager.setup_ui_layout()

        # Create menu bar through action manager
        self.action_manager.create_menu_bar()

        # Note: Ctrl+Shift+M shortcut for menu bar toggle is handled by the command system
        # This ensures it works even when the menu bar is hidden

    def initialize_services(self):
        """Initialize and register all services."""
        from viloapp.services import initialize_services

        # Initialize services with application components
        self.service_locator = initialize_services(
            main_window=self,
            workspace=self.workspace,
            sidebar=self.sidebar,
            activity_bar=self.activity_bar,
        )

        # Setup theme system through layout manager
        self.layout_manager.setup_theme()

        # Log service initialization
        import logging

        logger = logging.getLogger(__name__)
        logger.info("Services initialized successfully")

    def initialize_commands(self):
        """Initialize all built-in commands."""
        from viloapp.core.commands.builtin import register_all_builtin_commands

        # Register all built-in commands
        register_all_builtin_commands()

        # Log command initialization
        import logging

        logger = logging.getLogger(__name__)
        logger.info("Commands initialized successfully")

    def initialize_keyboard(self):
        """Initialize keyboard service and shortcuts."""
        from viloapp.core.keyboard import KeyboardService
        from viloapp.core.keyboard.keymaps import KeymapManager

        # Create keyboard service
        self.keyboard_service = KeyboardService()
        self.keyboard_service.initialize({})

        # Create keymap manager
        self.keymap_manager = KeymapManager(self.keyboard_service._registry)

        # Set default keymap (VSCode style)
        self.keymap_manager.set_keymap("vscode")

        # Add critical shortcuts as QActions with ApplicationShortcut context
        # This ensures they work even when WebEngine has focus
        self._create_application_shortcuts()

        # Connect keyboard service signals
        self.keyboard_service.shortcut_triggered.connect(self._on_shortcut_triggered)
        self.keyboard_service.chord_sequence_started.connect(self._on_chord_sequence_started)
        self.keyboard_service.chord_sequence_cancelled.connect(self._on_chord_sequence_cancelled)

        # Add context providers
        self.keyboard_service.add_context_provider(self._get_ui_context)

        # Register with service locator
        self.service_locator.register(KeyboardService, self.keyboard_service)

        # Install event filter on MainWindow instead of QApplication
        # to avoid segfaults with Qt WebEngine
        self.installEventFilter(self)

        # Register any pending shortcuts from commands
        from viloapp.core.commands.decorators import register_pending_shortcuts

        register_pending_shortcuts()

        # Install event filters on workspace widgets to catch shortcuts
        # This is needed because WebEngine widgets don't bubble events up
        self._install_workspace_filters()

        # Re-install filters when new panes are added
        if hasattr(self.workspace, "split_widget"):
            self.workspace.split_widget.pane_added.connect(self._on_pane_added)

        # Register shortcuts for all commands with the keyboard service
        from viloapp.core.commands.registry import command_registry

        commands_with_shortcuts = 0
        for command in command_registry.get_all_commands():
            if command.shortcut:
                # Register the shortcut with the keyboard service
                success = self.keyboard_service.register_shortcut_from_string(
                    shortcut_id=f"cmd_{command.id}",
                    sequence_str=command.shortcut,
                    command_id=command.id,
                    when=command.when,
                    description=command.title,
                    source="command",
                )
                if success:
                    commands_with_shortcuts += 1

        # Log keyboard initialization
        import logging

        logger = logging.getLogger(__name__)
        logger.info("Keyboard service initialized successfully")
        logger.info(f"Registered {commands_with_shortcuts} command shortcuts with keyboard service")

    def initialize_command_palette(self):
        """Initialize the command palette controller."""
        from viloapp.core.context.keys import ContextKey
        from viloapp.core.context.manager import context_manager
        from viloapp.ui.command_palette import CommandPaletteController

        # Create command palette controller
        self.command_palette_controller = CommandPaletteController(parent=self, main_window=self)

        # Connect palette signals to context updates
        self.command_palette_controller.palette_shown.connect(
            lambda: context_manager.set(ContextKey.COMMAND_PALETTE_VISIBLE, True)
        )
        self.command_palette_controller.palette_hidden.connect(
            lambda: context_manager.set(ContextKey.COMMAND_PALETTE_VISIBLE, False)
        )

        # Set initial context state
        context_manager.set(ContextKey.COMMAND_PALETTE_VISIBLE, False)

        # Log initialization
        import logging

        logger = logging.getLogger(__name__)
        logger.info("Command palette initialized successfully")

    def initialize_focus_sink(self):
        """Initialize the focus sink widget for command mode."""
        # Create focus sink widget (invisible, 0x0 size)
        self.focus_sink = FocusSinkWidget(self)

        # Connect signals to handle pane navigation
        self.focus_sink.digitPressed.connect(self._on_pane_number_pressed)
        self.focus_sink.cancelled.connect(self._on_command_mode_cancelled)
        self.focus_sink.commandModeExited.connect(self._on_command_mode_exited)

        import logging

        logger = logging.getLogger(__name__)
        logger.info("Focus sink initialized successfully")

    def _on_pane_number_pressed(self, number: int):
        """Handle pane number selection in command mode."""
        # Get workspace service to switch panes
        from viloapp.services.workspace_service import WorkspaceService

        workspace_service = self.service_locator.get(WorkspaceService)

        if workspace_service:
            # First hide pane numbers (before switching)
            workspace_service.hide_pane_numbers()

            # Then switch to the pane with the given number
            # This ensures focus is set after UI updates
            workspace_service.switch_to_pane_by_number(number)

            # Note: FocusSink automatically exits command mode after digit press
            # No need to call exit_command_mode here

        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Pane {number} selected in command mode")

    def _on_command_mode_cancelled(self):
        """Handle command mode cancellation."""
        # Hide pane numbers
        from viloapp.services.workspace_service import WorkspaceService

        workspace_service = self.service_locator.get(WorkspaceService)

        if workspace_service:
            workspace_service.hide_pane_numbers()

        import logging

        logger = logging.getLogger(__name__)
        logger.info("Command mode cancelled")

    def _on_command_mode_exited(self):
        """Handle command mode exit."""
        # Note: Pane numbers are already hidden in _on_pane_number_pressed
        # or _on_command_mode_cancelled, so we don't need to hide them here
        # This prevents double-hiding which can interfere with focus

        import logging

        logger = logging.getLogger(__name__)
        logger.info("Command mode exited")

    def create_command_context(self):
        """Create command context for execution."""
        from viloapp.core.commands.base import CommandContext

        # Get the model from workspace if available
        model = self.workspace.model if self.workspace else None

        # Create context with model as primary
        context = CommandContext(
            model=model,
            main_window=self,
            workspace=self.workspace,
        )

        # Set active tab and pane IDs if available
        if model and model.state:
            context.active_tab_id = model.state.active_tab_id
            active_tab = model.state.get_active_tab()
            if active_tab:
                context.active_pane_id = active_tab.active_pane_id

        return context

    def execute_command(self, command_id: str, **kwargs):
        """
        Execute a command by ID.

        Args:
            command_id: Command identifier
            **kwargs: Additional arguments for the command

        Returns:
            CommandResult from the executed command
        """
        from viloapp.core.commands.executor import CommandExecutor

        # Get or create executor
        if not hasattr(self, "_command_executor"):
            self._command_executor = CommandExecutor()

        # Create context and execute
        context = self.create_command_context()
        result = self._command_executor.execute(command_id, context, **kwargs)

        # Log result if failed
        if not result.success:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Command {command_id} failed: {result.error}")

        return result

    def _on_pane_added(self, pane_id: str):
        """Handle new pane being added - install event filters."""
        # Re-install filters to include the new pane
        self._install_workspace_filters()

    def _install_workspace_filters(self):
        """
        Install event filters on workspace and its children.
        This ensures keyboard shortcuts work even when terminal has focus.
        """
        if hasattr(self, "workspace"):
            # Install on workspace itself
            self.workspace.installEventFilter(self)

            # Install on split pane widget if it exists
            if hasattr(self.workspace, "split_widget"):
                self._install_filters_recursively(self.workspace.split_widget)

    def _install_filters_recursively(self, widget):
        """Recursively install event filters on widget and its children."""
        if widget is None:
            return

        # Install on the widget first (including WebEngineView)
        # This is safe now that we're not using QApplication filter
        widget.installEventFilter(self)

        # For WebEngineView, also try to install on focus proxy
        from PySide6.QtWebEngineWidgets import QWebEngineView

        if isinstance(widget, QWebEngineView):
            focus_proxy = widget.focusProxy()
            if focus_proxy:
                focus_proxy.installEventFilter(self)

        # Recursively install on children
        from PySide6.QtWidgets import QWidget

        for child in widget.findChildren(QWidget):
            # Skip WebEngine internal widgets to avoid recursion issues
            if "RenderWidgetHostViewQtDelegateWidget" not in child.__class__.__name__:
                self._install_filters_recursively(child)

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        """
        Filter events to intercept shortcuts.
        This ensures shortcuts work even when other widgets have focus.
        """
        from PySide6.QtCore import QEvent

        # Skip WebEngine internal widgets to avoid issues
        if "RenderWidgetHostViewQtDelegateWidget" in obj.__class__.__name__:
            return False

        # Only handle KeyPress events
        if event.type() == QEvent.KeyPress:
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"eventFilter received KeyPress from {obj.__class__.__name__}")

            # Let keyboard service handle the event first
            if hasattr(self, "keyboard_service") and self.keyboard_service.handle_key_event(event):
                # Event was handled by keyboard service - stop propagation
                logger.debug("Event handled by keyboard service via eventFilter")
                return True

        # Let the event continue to the target widget
        return False

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        """Handle key press events for keyboard shortcuts."""
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(
            f"MainWindow.keyPressEvent called with key: {event.key()}, modifiers: {event.modifiers()}"
        )

        # Let keyboard service handle the event first
        if hasattr(self, "keyboard_service") and self.keyboard_service.handle_key_event(event):
            # Event was handled by keyboard service
            logger.debug("Event handled by keyboard service")
            return

        # If not handled, pass to parent
        super().keyPressEvent(event)

    def _on_shortcut_triggered(self, command_id: str, context: dict) -> None:
        """Handle shortcut triggered by keyboard service."""
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(f"Shortcut triggered: {command_id}")

        # Execute the command
        self.execute_command(command_id)

    def _on_chord_sequence_started(self, sequence_str: str) -> None:
        """Handle chord sequence started."""
        # Could show status in status bar
        if hasattr(self, "status_bar"):
            self.status_bar.showMessage(f"Chord sequence: {sequence_str}...", 2000)

    def _on_chord_sequence_cancelled(self) -> None:
        """Handle chord sequence cancelled."""
        # Clear status message
        if hasattr(self, "status_bar"):
            self.status_bar.clearMessage()

    def _get_ui_context(self) -> dict:
        """Get current UI context for keyboard shortcuts."""
        context = {}

        # Add basic UI state
        context["sidebarVisible"] = (
            not self.sidebar.is_collapsed if hasattr(self, "sidebar") else False
        )
        context["editorFocus"] = self._has_editor_focus()
        context["terminalFocus"] = self._has_terminal_focus()
        context["menuBarVisible"] = self.menuBar().isVisible()

        # Add workspace context
        if hasattr(self, "workspace"):
            try:
                context["paneCount"] = self.workspace.get_split_count()
                context["activeTabIndex"] = self.workspace.get_current_tab_index()
                context["hasActiveEditor"] = self.workspace.has_active_editor()
            except (AttributeError, RuntimeError) as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.debug(f"Failed to get workspace context: {e}")
                # Set safe defaults
                context["paneCount"] = 0
                context["activeTabIndex"] = -1
                context["hasActiveEditor"] = False

        return context

    def _has_editor_focus(self) -> bool:
        """Check if an editor has focus."""
        # Simple implementation - could be enhanced
        focused_widget = self.focusWidget()
        if not focused_widget:
            return False

        # Check if focused widget is in workspace
        return hasattr(focused_widget, "toPlainText")  # Text editor check

    def _has_terminal_focus(self) -> bool:
        """Check if a terminal has focus."""
        # Simple implementation - could be enhanced
        focused_widget = self.focusWidget()
        if not focused_widget:
            return False

        # Check if focused widget is a terminal
        return "terminal" in focused_widget.__class__.__name__.lower()

    def _create_application_shortcuts(self):
        """
        Create QActions with ApplicationShortcut context for critical shortcuts.

        This ensures these shortcuts work even when QWebEngineView has focus,
        as Qt's action system takes precedence over widget key handling when
        combined with our WebShortcutGuard event filter.
        """
        from PySide6.QtGui import QAction

        # Alt+P - Toggle pane numbers
        # CRITICAL: We add this action to the MAIN WINDOW, not to a child widget
        # This ensures it's always active regardless of focus
        toggle_panes_action = QAction("Toggle Pane Numbers", self)
        toggle_panes_action.setShortcut(QKeySequence("Alt+P"))
        toggle_panes_action.setShortcutContext(Qt.ApplicationShortcut)
        toggle_panes_action.triggered.connect(
            lambda: self.execute_command("workbench.action.togglePaneNumbers")
        )
        self.addAction(toggle_panes_action)

        # Also ensure the action is enabled
        toggle_panes_action.setEnabled(True)

        import logging

        logger = logging.getLogger(__name__)
        logger.info("Created QAction for Alt+P with ApplicationShortcut context")

    def toggle_theme(self):
        """Toggle application theme - delegate to action manager."""
        return self.action_manager.toggle_theme()

    def toggle_menu_bar(self):
        """Toggle menu bar visibility - delegate to action manager."""
        return self.action_manager.toggle_menu_bar()

    def on_activity_view_changed(self, view_name: str):
        """Handle activity bar view selection - delegate to layout manager."""
        self.layout_manager.on_activity_view_changed(view_name)

    def toggle_sidebar(self):
        """Toggle sidebar visibility - delegate to layout manager."""
        self.layout_manager.toggle_sidebar()

    def toggle_activity_bar(self) -> bool:
        """Toggle activity bar visibility - delegate to layout manager."""
        return self.layout_manager.toggle_activity_bar()

    def on_auto_hide_menubar_toggled(self, checked: bool):
        """Handle the 'Use Activity Bar Menu' toggle - delegate to action manager."""
        self.action_manager.on_auto_hide_menubar_toggled(checked)

    def reset_app_state(self):
        """Reset application to default state - delegate to action manager."""
        return self.action_manager.reset_app_state()

    def closeEvent(self, event):  # noqa: N802
        """Handle close event - delegate to state manager."""
        self.state_manager.close_event_handler(event)

    def save_state(self):
        """Save window state - delegate to state manager."""
        self.state_manager.save_state()

    def restore_state(self):
        """Restore window state - delegate to state manager."""
        self.state_manager.restore_state()

    def restore_workspace_state(self):
        """Restore workspace state (tabs) - should be called after plugins are loaded."""
        self.state_manager.restore_workspace_state()
