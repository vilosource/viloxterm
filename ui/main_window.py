"""Main window implementation for the VSCode-style application."""

from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QMenuBar, QMessageBox
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QKeySequence, QShortcut, QKeyEvent
from ui.activity_bar import ActivityBar
from ui.sidebar import Sidebar
from ui.workspace_simple import Workspace  # Using new tab-based workspace
from ui.status_bar import AppStatusBar
from ui.icon_manager import get_icon_manager
from ui.vscode_theme import *


class MainWindow(QMainWindow):
    """Main application window with VSCode-style layout."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.initialize_services()
        self.initialize_commands()
        self.initialize_keyboard()
        self.initialize_command_palette()
        self.restore_state()
        
    def setup_ui(self):
        """Initialize the UI components."""
        self.setWindowTitle("ViloApp")
        self.resize(1200, 800)
        
        # Apply VSCode theme to main window
        self.setStyleSheet(get_main_window_stylesheet() + get_menu_stylesheet())
        
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
        self.main_splitter.setStyleSheet(get_splitter_stylesheet())
        main_layout.addWidget(self.main_splitter)
        
        # Create sidebar
        self.sidebar = Sidebar()
        self.main_splitter.addWidget(self.sidebar)
        
        # Create workspace
        self.workspace = Workspace()
        self.main_splitter.addWidget(self.workspace)
        
        # Set initial splitter sizes (sidebar: 250px, workspace: rest)
        self.main_splitter.setSizes([250, 950])
        
        # Create status bar
        self.status_bar = AppStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Connect signals
        self.activity_bar.toggle_sidebar.connect(self.toggle_sidebar)
        
        # Create global shortcuts that work even when menu bar is hidden
        self.menu_toggle_shortcut = QShortcut(QKeySequence("Ctrl+Shift+M"), self)
        self.menu_toggle_shortcut.activated.connect(self.toggle_menu_bar)
    
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
        from core.keyboard import KeyboardService
        from core.keyboard.keymaps import KeymapManager
        
        # Create keyboard service
        self.keyboard_service = KeyboardService()
        self.keyboard_service.initialize({})
        
        # Create keymap manager
        self.keymap_manager = KeymapManager(self.keyboard_service._registry)
        
        # Set default keymap (VSCode style)
        self.keymap_manager.set_keymap("vscode")
        
        # Connect keyboard service signals
        self.keyboard_service.shortcut_triggered.connect(self._on_shortcut_triggered)
        self.keyboard_service.chord_sequence_started.connect(self._on_chord_sequence_started)
        self.keyboard_service.chord_sequence_cancelled.connect(self._on_chord_sequence_cancelled)
        
        # Add context providers
        self.keyboard_service.add_context_provider(self._get_ui_context)
        
        # Register with service locator
        self.service_locator.register(KeyboardService, self.keyboard_service)
        
        # Register any pending shortcuts from commands
        from core.commands.decorators import register_pending_shortcuts
        register_pending_shortcuts()
        
        # Log keyboard initialization
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Keyboard service initialized successfully")
    
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
        result = self._command_executor.execute(command_id, context, kwargs)
        
        # Log result if failed
        if not result.success:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Command {command_id} failed: {result.error}")
        
        return result
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events for keyboard shortcuts."""
        # Let keyboard service handle the event first
        if hasattr(self, 'keyboard_service') and self.keyboard_service.handle_key_event(event):
            # Event was handled by keyboard service
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
        
    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # New tab actions (now using commands)
        new_editor_tab_action = QAction("New Editor Tab", self)
        new_editor_tab_action.setShortcut(QKeySequence("Ctrl+N"))
        new_editor_tab_action.setToolTip("Create a new editor tab (Ctrl+N)")
        new_editor_tab_action.triggered.connect(lambda: self.execute_command("file.newEditorTab"))
        file_menu.addAction(new_editor_tab_action)
        
        new_terminal_tab_action = QAction("New Terminal Tab", self)
        new_terminal_tab_action.setShortcut(QKeySequence("Ctrl+`"))
        new_terminal_tab_action.setToolTip("Create a new terminal tab (Ctrl+`)")
        new_terminal_tab_action.triggered.connect(lambda: self.execute_command("file.newTerminalTab"))
        file_menu.addAction(new_terminal_tab_action)
        
        file_menu.addSeparator()
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        # Theme toggle action (now using commands)
        theme_action = QAction("Toggle Theme", self)
        theme_action.setShortcut(QKeySequence("Ctrl+T"))
        theme_action.setToolTip("Toggle between light and dark theme (Ctrl+T)")
        theme_action.triggered.connect(lambda: self.execute_command("view.toggleTheme"))
        view_menu.addAction(theme_action)
        
        # Sidebar toggle action (now using commands)
        sidebar_action = QAction("Toggle Sidebar", self)
        sidebar_action.setShortcut(QKeySequence("Ctrl+B"))
        sidebar_action.setToolTip("Toggle sidebar visibility (Ctrl+B)")
        sidebar_action.triggered.connect(lambda: self.execute_command("view.toggleSidebar"))
        view_menu.addAction(sidebar_action)
        
        view_menu.addSeparator()
        
        # Split actions (now using commands)
        split_horizontal_action = QAction("Split Pane Right", self)
        split_horizontal_action.setShortcut(QKeySequence("Ctrl+\\"))
        split_horizontal_action.setToolTip("Split the active pane horizontally (Ctrl+\\)")
        split_horizontal_action.triggered.connect(lambda: self.execute_command("workbench.action.splitRight"))
        view_menu.addAction(split_horizontal_action)
        
        split_vertical_action = QAction("Split Pane Down", self)
        split_vertical_action.setShortcut(QKeySequence("Ctrl+Shift+\\"))
        split_vertical_action.setToolTip("Split the active pane vertically (Ctrl+Shift+\\)")
        split_vertical_action.triggered.connect(lambda: self.execute_command("workbench.action.splitDown"))
        view_menu.addAction(split_vertical_action)
        
        close_pane_action = QAction("Close Pane", self)
        close_pane_action.setShortcut(QKeySequence("Ctrl+W"))
        close_pane_action.setToolTip("Close the active pane (Ctrl+W)")
        close_pane_action.triggered.connect(lambda: self.execute_command("workbench.action.closeActivePane"))
        view_menu.addAction(close_pane_action)
        
        view_menu.addSeparator()
        
        # Menu bar toggle action (shortcut handled by global QShortcut)
        self.menubar_action = QAction("Toggle Menu Bar", self)
        self.menubar_action.setToolTip("Toggle menu bar visibility (Ctrl+Shift+M)")
        self.menubar_action.triggered.connect(lambda: self.execute_command("view.toggleMenuBar"))
        view_menu.addAction(self.menubar_action)
        
        # Debug menu
        debug_menu = menubar.addMenu("Debug")
        
        # Reset app state action (now using commands)
        reset_state_action = QAction("Reset App State", self)
        reset_state_action.setShortcut(QKeySequence("Ctrl+Shift+R"))
        reset_state_action.setToolTip("Reset application to default state, clearing all saved settings (Ctrl+Shift+R)")
        reset_state_action.triggered.connect(lambda: self.execute_command("debug.resetAppState"))
        debug_menu.addAction(reset_state_action)
        
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
            # Sidebar is now collapsed
            self.main_splitter.setSizes([0, self.main_splitter.width()])
            # Update activity bar to show current view as unchecked
            self.activity_bar.set_sidebar_visible(False)
        else:
            # Sidebar is now expanded
            self.main_splitter.setSizes([250, self.main_splitter.width() - 250])
            # Update activity bar to show current view as checked
            self.activity_bar.set_sidebar_visible(True)
        
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
            
        # Restore menu bar visibility
        menu_visible = settings.value("menuBarVisible", True, type=bool)
        self.menuBar().setVisible(menu_visible)
            
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