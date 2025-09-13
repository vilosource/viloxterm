"""Main window implementation for the VSCode-style application."""

from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QMenuBar, QMessageBox
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QKeySequence, QKeyEvent
from ui.activity_bar import ActivityBar
from ui.sidebar import Sidebar
from ui.workspace import Workspace
from ui.status_bar import AppStatusBar
from ui.icon_manager import get_icon_manager
from ui.widgets.focus_sink import FocusSinkWidget

from services.theme_service import ThemeService
from ui.qt_compat import safe_splitter_collapse_setting, log_qt_versions


class MainWindow(QMainWindow):
    """Main application window with VSCode-style layout."""
    
    def __init__(self):
        super().__init__()
        # Log Qt version information for debugging
        log_qt_versions()
        self.setup_ui()
        self.initialize_services()
        self.initialize_commands()
        self.initialize_keyboard()
        self.initialize_command_palette()
        self.initialize_focus_sink()  # Add focus sink initialization
        self.restore_state()
        
    def setup_ui(self):
        """Initialize the UI components."""
        # Set window title with dev mode indicator if applicable
        from core.app_config import app_config
        dev_mode = app_config.dev_mode
        title = "ViloxTerm [DEV]" if dev_mode else "ViloxTerm"
        self.setWindowTitle(title)
        self.resize(1200, 800)

        # Note: Theme will be applied after services are initialized
        # We need ThemeProvider to be available first
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create activity bar
        self.activity_bar = ActivityBar()
        self.activity_bar.view_changed.connect(self.on_activity_view_changed)
        main_layout.addWidget(self.activity_bar)
        
        # Create main splitter for sidebar and workspace
        self.main_splitter = QSplitter(Qt.Horizontal)
        # Splitter styling will be applied with theme
        main_layout.addWidget(self.main_splitter)
        
        # Create sidebar
        self.sidebar = Sidebar()
        self.main_splitter.addWidget(self.sidebar)
        
        # Create workspace
        self.workspace = Workspace()
        self.main_splitter.addWidget(self.workspace)
        
        # Set initial splitter sizes (sidebar: 250px, workspace: rest)
        self.main_splitter.setSizes([250, 950])
        
        # Allow sidebar to be completely collapsed
        safe_splitter_collapse_setting(self.main_splitter, True)
        
        # Create status bar
        self.status_bar = AppStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Connect signals
        self.activity_bar.toggle_sidebar.connect(self.toggle_sidebar)
        
        # Note: Ctrl+Shift+M shortcut for menu bar toggle is handled by the command system
        # This ensures it works even when the menu bar is hidden
    
    def initialize_services(self):
        """Initialize and register all services."""
        from services import initialize_services
        
        # Initialize services with application components
        self.service_locator = initialize_services(
            main_window=self,
            workspace=self.workspace,
            sidebar=self.sidebar,
            activity_bar=self.activity_bar
        )
        
        # Setup theme system
        self.setup_theme()
        
        # Log service initialization
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Services initialized successfully")
    
    def initialize_commands(self):
        """Initialize all built-in commands."""
        from core.commands.builtin import register_all_builtin_commands
        
        # Register all built-in commands
        register_all_builtin_commands()
        
        # Log command initialization
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Commands initialized successfully")
    
    def initialize_keyboard(self):
        """Initialize keyboard service and shortcuts."""
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QAction
        from core.keyboard import KeyboardService
        from core.keyboard.keymaps import KeymapManager
        
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
        from core.commands.decorators import register_pending_shortcuts
        register_pending_shortcuts()
        
        # Install event filters on workspace widgets to catch shortcuts
        # This is needed because WebEngine widgets don't bubble events up
        self._install_workspace_filters()
        
        # Re-install filters when new panes are added
        if hasattr(self.workspace, 'split_widget'):
            self.workspace.split_widget.pane_added.connect(self._on_pane_added)
        
        # Register shortcuts for all commands with the keyboard service
        from core.commands.registry import command_registry
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
                    source="command"
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
        from ui.command_palette import CommandPaletteController
        from core.context.keys import ContextKey
        from core.context.manager import context_manager
        
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
        from services.workspace_service import WorkspaceService
        workspace_service = self.service_locator.get(WorkspaceService)
        
        if workspace_service:
            # First hide pane numbers (before switching)
            workspace_service.hide_pane_numbers()
            
            # Then switch to the pane with the given number
            # This ensures focus is set after UI updates
            success = workspace_service.switch_to_pane_by_number(number)
            
            # Note: FocusSink automatically exits command mode after digit press
            # No need to call exit_command_mode here
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Pane {number} selected in command mode")
    
    def _on_command_mode_cancelled(self):
        """Handle command mode cancellation."""
        # Hide pane numbers
        from services.workspace_service import WorkspaceService
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
        from core.commands.base import CommandContext
        
        return CommandContext(
            main_window=self,
            workspace=self.workspace,
            active_widget=self.workspace.get_current_split_widget() if self.workspace else None
        )
    
    def execute_command(self, command_id: str, **kwargs):
        """
        Execute a command by ID.
        
        Args:
            command_id: Command identifier
            **kwargs: Additional arguments for the command
            
        Returns:
            CommandResult from the executed command
        """
        from core.commands.executor import CommandExecutor
        
        # Get or create executor
        if not hasattr(self, '_command_executor'):
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
        if hasattr(self, 'workspace'):
            # Install on workspace itself
            self.workspace.installEventFilter(self)
            
            # Install on split pane widget if it exists
            if hasattr(self.workspace, 'split_widget'):
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
    
    def eventFilter(self, obj, event) -> bool:
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
            if hasattr(self, 'keyboard_service') and self.keyboard_service.handle_key_event(event):
                # Event was handled by keyboard service - stop propagation
                logger.debug("Event handled by keyboard service via eventFilter")
                return True
        
        # Let the event continue to the target widget
        return False
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events for keyboard shortcuts."""
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"MainWindow.keyPressEvent called with key: {event.key()}, modifiers: {event.modifiers()}")
        
        # Let keyboard service handle the event first
        if hasattr(self, 'keyboard_service') and self.keyboard_service.handle_key_event(event):
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
        if hasattr(self, 'status_bar'):
            self.status_bar.showMessage(f"Chord sequence: {sequence_str}...", 2000)
    
    def _on_chord_sequence_cancelled(self) -> None:
        """Handle chord sequence cancelled."""
        # Clear status message
        if hasattr(self, 'status_bar'):
            self.status_bar.clearMessage()
    
    def _get_ui_context(self) -> dict:
        """Get current UI context for keyboard shortcuts."""
        context = {}
        
        # Add basic UI state
        context['sidebarVisible'] = not self.sidebar.is_collapsed if hasattr(self, 'sidebar') else False
        context['editorFocus'] = self._has_editor_focus()
        context['terminalFocus'] = self._has_terminal_focus()
        context['menuBarVisible'] = self.menuBar().isVisible()
        
        # Add workspace context
        if hasattr(self, 'workspace'):
            try:
                context['paneCount'] = self.workspace.get_split_count()
                context['activeTabIndex'] = self.workspace.get_current_tab_index()
                context['hasActiveEditor'] = self.workspace.has_active_editor()
            except:
                pass  # Ignore errors getting workspace context
        
        return context
    
    def _has_editor_focus(self) -> bool:
        """Check if an editor has focus."""
        # Simple implementation - could be enhanced
        focused_widget = self.focusWidget()
        if not focused_widget:
            return False
        
        # Check if focused widget is in workspace
        return hasattr(focused_widget, 'toPlainText')  # Text editor check
    
    def _has_terminal_focus(self) -> bool:
        """Check if a terminal has focus."""
        # Simple implementation - could be enhanced
        focused_widget = self.focusWidget()
        if not focused_widget:
            return False
        
        # Check if focused widget is a terminal
        return 'terminal' in focused_widget.__class__.__name__.lower()
    
    def _create_application_shortcuts(self):
        """
        Create QActions with ApplicationShortcut context for critical shortcuts.
        
        This ensures these shortcuts work even when QWebEngineView has focus,
        as Qt's action system takes precedence over widget key handling when
        combined with our WebShortcutGuard event filter.
        """
        from PySide6.QtGui import QAction, QKeySequence
        
        # Alt+P - Toggle pane numbers
        # CRITICAL: We add this action to the MAIN WINDOW, not to a child widget
        # This ensures it's always active regardless of focus
        toggle_panes_action = QAction("Toggle Pane Numbers", self)
        toggle_panes_action.setShortcut(QKeySequence("Alt+P"))
        toggle_panes_action.setShortcutContext(Qt.ApplicationShortcut)
        toggle_panes_action.triggered.connect(lambda: self.execute_command("workbench.action.togglePaneNumbers"))
        self.addAction(toggle_panes_action)
        
        # Also ensure the action is enabled
        toggle_panes_action.setEnabled(True)
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Created QAction for Alt+P with ApplicationShortcut context")
        
    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # Ensure menu bar is visible by default on first run
        # (restore_state will override this if there are saved settings)
        menubar.setVisible(True)
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # New tab actions (now using commands)
        new_editor_tab_action = QAction("New Editor Tab", self)
        # Shortcut handled by command system, not QAction
        new_editor_tab_action.setToolTip("Create a new editor tab (Ctrl+N)")
        new_editor_tab_action.triggered.connect(lambda: self.execute_command("file.newEditorTab"))
        file_menu.addAction(new_editor_tab_action)
        
        new_terminal_tab_action = QAction("New Terminal Tab", self)
        # Shortcut handled by command system, not QAction
        new_terminal_tab_action.setToolTip("Create a new terminal tab (Ctrl+`)")
        new_terminal_tab_action.triggered.connect(lambda: self.execute_command("file.newTerminalTab"))
        file_menu.addAction(new_terminal_tab_action)

        file_menu.addSeparator()

        # Keyboard Shortcuts action (now using commands)
        keyboard_shortcuts_action = QAction("Keyboard Shortcuts...", self)
        keyboard_shortcuts_action.setToolTip("Configure keyboard shortcuts (Ctrl+K, Ctrl+S)")
        keyboard_shortcuts_action.triggered.connect(
            lambda: self.execute_command("settings.openKeyboardShortcuts")
        )
        file_menu.addAction(keyboard_shortcuts_action)

        file_menu.addSeparator()

        # About action
        about_action = QAction("About ViloxTerm", self)
        about_action.setToolTip("Show information about ViloxTerm")
        about_action.triggered.connect(lambda: self.execute_command("help.about"))
        file_menu.addAction(about_action)

        # View menu
        view_menu = menubar.addMenu("View")

        # Theme selection action (now using new theme system)
        theme_action = QAction("Select Theme", self)
        # Shortcut handled by command system, not QAction
        theme_action.setToolTip("Select a color theme (Ctrl+K, Ctrl+T)")
        theme_action.triggered.connect(lambda: self.execute_command("theme.selectTheme"))
        view_menu.addAction(theme_action)

        # Theme Editor action
        theme_editor_action = QAction("Theme Editor...", self)
        theme_editor_action.setToolTip("Open the theme editor to customize themes (Ctrl+K, Ctrl+M)")
        theme_editor_action.triggered.connect(lambda: self.execute_command("theme.openEditor"))
        view_menu.addAction(theme_editor_action)

        view_menu.addSeparator()

        # Import VSCode Theme action
        import_vscode_theme_action = QAction("Import VSCode Theme...", self)
        import_vscode_theme_action.setToolTip("Import a theme from VSCode JSON format")
        import_vscode_theme_action.triggered.connect(lambda: self.execute_command("theme.importVSCode"))
        view_menu.addAction(import_vscode_theme_action)
        
        # Sidebar toggle action (now using commands)
        sidebar_action = QAction("Toggle Sidebar", self)
        # Shortcut handled by command system, not QAction
        sidebar_action.setToolTip("Toggle sidebar visibility (Ctrl+B)")
        sidebar_action.triggered.connect(lambda: self.execute_command("view.toggleSidebar"))
        view_menu.addAction(sidebar_action)
        
        view_menu.addSeparator()
        
        # Split actions (now using commands)
        split_horizontal_action = QAction("Split Pane Right", self)
        # Shortcut handled by command system, not QAction
        split_horizontal_action.setToolTip("Split the active pane horizontally (Ctrl+\\)")
        split_horizontal_action.triggered.connect(lambda: self.execute_command("workbench.action.splitRight"))
        view_menu.addAction(split_horizontal_action)
        
        split_vertical_action = QAction("Split Pane Down", self)
        # Shortcut handled by command system, not QAction
        split_vertical_action.setToolTip("Split the active pane vertically (Ctrl+Shift+\\)")
        split_vertical_action.triggered.connect(lambda: self.execute_command("workbench.action.splitDown"))
        view_menu.addAction(split_vertical_action)
        
        close_pane_action = QAction("Close Pane", self)
        # Shortcut handled by command system, not QAction
        close_pane_action.setToolTip("Close the active pane (Ctrl+W)")
        close_pane_action.triggered.connect(lambda: self.execute_command("workbench.action.closeActivePane"))
        view_menu.addAction(close_pane_action)
        
        view_menu.addSeparator()
        
        # Menu bar toggle action (shortcut handled by global QShortcut)
        self.menubar_action = QAction("Toggle Menu Bar", self)
        self.menubar_action.setToolTip("Toggle menu bar visibility (Ctrl+Shift+M)")
        self.menubar_action.triggered.connect(lambda: self.execute_command("view.toggleMenuBar"))
        view_menu.addAction(self.menubar_action)
        
        # Auto-hide menu bar option
        self.auto_hide_menubar_action = QAction("Use Activity Bar Menu", self)
        self.auto_hide_menubar_action.setCheckable(True)
        self.auto_hide_menubar_action.setToolTip("Hide menu bar and use activity bar menu icon instead")
        self.auto_hide_menubar_action.toggled.connect(self.on_auto_hide_menubar_toggled)
        view_menu.addAction(self.auto_hide_menubar_action)
        
        view_menu.addSeparator()

        # Frameless mode toggle
        frameless_action = QAction("Frameless Mode", self)
        frameless_action.setCheckable(True)
        frameless_action.setToolTip("Use frameless window for maximum screen space (requires restart)")
        settings = QSettings("ViloxTerm", "ViloxTerm")
        frameless_action.setChecked(settings.value("UI/FramelessMode", False, type=bool))
        frameless_action.triggered.connect(lambda: self.execute_command("window.toggleFrameless"))
        view_menu.addAction(frameless_action)

        # Debug menu
        debug_menu = menubar.addMenu("Debug")
        
        # Reset app state action (now using commands)
        reset_state_action = QAction("Reset App State", self)
        # Shortcut handled by command system, not QAction
        reset_state_action.setToolTip("Reset application to default state, clearing all saved settings (Ctrl+Shift+R)")
        reset_state_action.triggered.connect(lambda: self.execute_command("debug.resetAppState"))
        debug_menu.addAction(reset_state_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        # Documentation action
        docs_action = QAction("Documentation", self)
        docs_action.setToolTip("Open ViloxTerm documentation")
        docs_action.triggered.connect(lambda: self.execute_command("help.documentation"))
        help_menu.addAction(docs_action)

        # Report issue action
        issue_action = QAction("Report Issue", self)
        issue_action.setToolTip("Report an issue on GitHub")
        issue_action.triggered.connect(lambda: self.execute_command("help.reportIssue"))
        help_menu.addAction(issue_action)

        help_menu.addSeparator()

        # Check for updates action
        updates_action = QAction("Check for Updates...", self)
        updates_action.setToolTip("Check for ViloxTerm updates")
        updates_action.triggered.connect(lambda: self.execute_command("help.checkForUpdates"))
        help_menu.addAction(updates_action)

        help_menu.addSeparator()

        # About action (also in Help menu)
        about_help_action = QAction("About ViloxTerm", self)
        about_help_action.setToolTip("Show information about ViloxTerm")
        about_help_action.triggered.connect(lambda: self.execute_command("help.about"))
        help_menu.addAction(about_help_action)

    def toggle_theme(self):
        """Toggle application theme - now routes through command system."""
        return self.execute_command("view.toggleTheme")
        
    def toggle_menu_bar(self):
        """Toggle menu bar visibility - now routes through command system."""
        return self.execute_command("view.toggleMenuBar")
        
    def on_activity_view_changed(self, view_name: str):
        """Handle activity bar view selection."""
        self.sidebar.set_current_view(view_name)
        if self.sidebar.is_collapsed:
            self.sidebar.expand()
            # Ensure splitter sizes are updated
            self.main_splitter.setSizes([250, self.main_splitter.width() - 250])
            # Update activity bar to reflect that sidebar is now visible
            self.activity_bar.set_sidebar_visible(True)
            
    def toggle_sidebar(self):
        """Toggle sidebar visibility - now routes through command system for consistency."""
        # Still handle the UI updates directly for now to maintain compatibility
        # This can be refactored later to be fully handled by the UIService
        self.sidebar.toggle()
        
        # Update splitter sizes when sidebar toggles
        if self.sidebar.is_collapsed:
            # Sidebar is now completely hidden (0 width)
            self.main_splitter.setSizes([0, self.main_splitter.width()])
            # Update activity bar to show current view as unchecked
            self.activity_bar.set_sidebar_visible(False)
        else:
            # Sidebar is now expanded
            self.main_splitter.setSizes([250, self.main_splitter.width() - 250])
            # Update activity bar to show current view as checked
            self.activity_bar.set_sidebar_visible(True)
    
    def toggle_activity_bar(self) -> bool:
        """Toggle activity bar visibility and adjust layout."""
        # Toggle visibility
        is_visible = not self.activity_bar.isVisible()
        self.activity_bar.setVisible(is_visible)
        
        # Adjust the main layout
        if is_visible:
            # Activity bar is now visible - restore normal layout
            self.activity_bar.show()
            # If sidebar was visible before, ensure it's properly sized
            if not self.sidebar.is_collapsed:
                self.main_splitter.setSizes([250, self.main_splitter.width() - 250])
        else:
            # Activity bar is now hidden - expand main content
            self.activity_bar.hide()
            # Optionally hide sidebar too when activity bar is hidden
            if not self.sidebar.is_collapsed:
                self.sidebar.collapse()
                self.main_splitter.setSizes([0, self.main_splitter.width()])
        
        return is_visible
    
    def on_auto_hide_menubar_toggled(self, checked: bool):
        """Handle the 'Use Activity Bar Menu' toggle."""
        if checked:
            # Hide menu bar when using activity bar menu
            self.menuBar().setVisible(False)
        else:
            # Show menu bar when not using activity bar menu
            self.menuBar().setVisible(True)
        
        # Save preference
        settings = QSettings()
        settings.setValue("MainWindow/useActivityBarMenu", checked)
        
    def reset_app_state(self):
        """Reset application to default state - now routes through command system."""
        return self.execute_command("debug.resetAppState")
        
    def reset_app_state_legacy(self):
        """Legacy reset method - kept for reference."""
        reply = QMessageBox.question(
            self,
            "Reset Application State",
            "This will reset the application to its default state and clear all saved settings including:\n\n"
            "• Window size and position\n"
            "• Split pane layouts\n"
            "• Menu bar visibility\n"
            "• Active pane selections\n\n"
            "The application will be restarted with default settings.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Clear all saved settings
                settings = QSettings()
                settings.clear()
                
                # Show success message
                self.status_bar.set_message("Application state reset successfully", 3000)
                
                # Reset to default state immediately
                self._reset_to_defaults()
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Reset Failed",
                    f"Failed to reset application state:\n{str(e)}"
                )
                
    def _reset_to_defaults(self):
        """Reset current application state to defaults without restarting."""
        try:
            # Reset window to default size and center it
            self.resize(1200, 800)
            
            # Center window on screen
            screen = self.screen().geometry()
            window_geometry = self.geometry()
            x = (screen.width() - window_geometry.width()) // 2
            y = (screen.height() - window_geometry.height()) // 2
            self.move(x, y)
            
            # Reset splitter to default sizes (sidebar: 250px, workspace: rest)
            self.main_splitter.setSizes([250, 950])
            
            # Ensure menu bar is visible
            self.menuBar().setVisible(True)
            
            # Ensure sidebar is visible and expanded
            if self.sidebar.is_collapsed:
                self.sidebar.expand()
                
            # Reset workspace to default single pane layout
            self.workspace.reset_to_default_layout()
            
            # Reset theme to system default
            icon_manager = get_icon_manager()
            icon_manager.detect_system_theme()
            
            self.status_bar.set_message("Application reset to default state", 2000)
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Reset Warning", 
                f"Some settings could not be reset:\n{str(e)}"
            )

    def setup_theme(self):
        """Setup theme system and apply initial theme."""
        try:
            # Get theme provider from service locator
            theme_service = self.service_locator.get(ThemeService)
            self.theme_provider = theme_service.get_theme_provider() if theme_service else None
            if not self.theme_provider:
                print("Warning: ThemeProvider not available")
                return

            # Connect to theme changes
            self.theme_provider.style_changed.connect(self.apply_theme)

            # Apply initial theme
            self.apply_theme()

            import logging
            logger = logging.getLogger(__name__)
            logger.info("Theme system initialized")
        except Exception as e:
            print(f"Failed to setup theme: {e}")
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to setup theme: {e}")

    def apply_theme(self):
        """Apply current theme to all components."""
        if not hasattr(self, 'theme_provider'):
            return

        try:
            # Apply main window theme
            self.setStyleSheet(self.theme_provider.get_stylesheet("main_window") +
                             self.theme_provider.get_stylesheet("menu"))

            # Apply splitter theme
            self.main_splitter.setStyleSheet(self.theme_provider.get_stylesheet("splitter"))

            # Let each component apply its own theme
            if hasattr(self, 'activity_bar'):
                self.activity_bar.apply_theme()
            if hasattr(self, 'sidebar'):
                self.sidebar.apply_theme()
            if hasattr(self, 'workspace'):
                self.workspace.apply_theme()
            if hasattr(self, 'status_bar'):
                self.status_bar.apply_theme()

            import logging
            logger = logging.getLogger(__name__)
            logger.debug("Theme applied to all components")
        except Exception as e:
            print(f"Failed to apply theme: {e}")
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to apply theme: {e}")

    def closeEvent(self, event):
        """Save state and clean up resources before closing."""
        self.save_state()
        
        # Clean up all terminal sessions before closing
        from ui.terminal.terminal_server import terminal_server
        terminal_server.cleanup_all_sessions()
        
        event.accept()
        
    def save_state(self):
        """Save window state and geometry."""
        settings = QSettings()
        settings.beginGroup("MainWindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        settings.setValue("splitterSizes", self.main_splitter.saveState())
        settings.setValue("menuBarVisible", self.menuBar().isVisible())
        settings.setValue("activityBarVisible", self.activity_bar.isVisible())
        settings.endGroup()
        
        # Save workspace state (new tab-based workspace)
        settings.beginGroup("Workspace")
        workspace_state = self.workspace.save_state()
        import json
        settings.setValue("state", json.dumps(workspace_state))
        settings.endGroup()
        
    def restore_state(self):
        """Restore window state and geometry."""
        settings = QSettings()
        settings.beginGroup("MainWindow")
        
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        window_state = settings.value("windowState")
        if window_state:
            self.restoreState(window_state)
            
        splitter_state = settings.value("splitterSizes")
        if splitter_state:
            self.main_splitter.restoreState(splitter_state)
            
        # Allow sidebar to be completely collapsed after restoration
        safe_splitter_collapse_setting(self.main_splitter, True)
            
        # Restore menu bar visibility and activity bar menu preference
        # Fix the path - it should be under MainWindow group
        use_activity_bar_menu = settings.value("MainWindow/useActivityBarMenu", False, type=bool)
        if hasattr(self, 'auto_hide_menubar_action'):
            if use_activity_bar_menu:
                self.auto_hide_menubar_action.setChecked(True)
                self.menuBar().setVisible(False)
            else:
                menu_visible = settings.value("menuBarVisible", True, type=bool)
                self.menuBar().setVisible(menu_visible)
        else:
            menu_visible = settings.value("menuBarVisible", True, type=bool)
            self.menuBar().setVisible(menu_visible)
        
        # Restore activity bar visibility
        activity_bar_visible = settings.value("activityBarVisible", True, type=bool)
        if not activity_bar_visible:
            self.activity_bar.hide()
            
        settings.endGroup()
        
        # Restore workspace state (new tab-based workspace)
        settings.beginGroup("Workspace")
        workspace_state_json = settings.value("state")
        if workspace_state_json:
            try:
                import json
                workspace_state = json.loads(workspace_state_json)
                self.workspace.restore_state(workspace_state)
            except (json.JSONDecodeError, Exception) as e:
                # If restoration fails, workspace will create default tab
                print(f"Failed to restore workspace state: {e}")
        settings.endGroup()