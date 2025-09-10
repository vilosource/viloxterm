#!/usr/bin/env python3
"""
Terminal implementation as an AppWidget.

This replaces the old TerminalWidget with a proper AppWidget implementation.
"""

import os
import logging
from typing import Dict, Any, Optional
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Slot, QUrl, Signal
from PySide6.QtGui import QColor

from ui.widgets.app_widget import AppWidget
from ui.widgets.widget_registry import WidgetType
from ui.terminal.terminal_server import terminal_server
from ui.terminal.terminal_config import TerminalConfig
from ui.terminal.terminal_themes import get_terminal_theme
from ui.terminal.terminal_assets import terminal_asset_bundler
from ui.terminal.terminal_bridge import TerminalBridge
from ui.icon_manager import get_icon_manager

logger = logging.getLogger(__name__)


class TerminalAppWidget(AppWidget):
    """
    Terminal widget that extends AppWidget.
    
    Manages its own terminal session and WebEngine view.
    """
    
    def __init__(self, widget_id: str, parent=None):
        """Initialize the terminal widget."""
        super().__init__(widget_id, WidgetType.TERMINAL, parent)
        self.session_id = None
        self.web_view = None
        self.config = TerminalConfig()
        self.current_theme = "dark"
        self.bridge = None  # Will be created in setup_terminal
        
        # Connect to theme changes from IconManager
        icon_manager = get_icon_manager()
        self.current_theme = icon_manager.theme
        icon_manager.theme_changed.connect(self.on_app_theme_changed)
        
        self.setup_terminal()
        
    def setup_terminal(self):
        """Set up the terminal UI and session."""
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create web view with optimized initialization
        self.web_view = QWebEngineView()
        
        # Set background color to match dark theme immediately
        self.web_view.setStyleSheet("""
            QWebEngineView {
                background-color: #1e1e1e;
                border: none;
            }
        """)
        
        # Set the page background color before any content loads
        self.web_view.page().setBackgroundColor(QColor("#1e1e1e"))
        
        # Allow local content to be loaded
        from PySide6.QtWebEngineCore import QWebEngineSettings
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.ErrorPageEnabled, True)
        
        # Don't hide the web view - let it show with dark background
        # self.web_view.hide()  # REMOVED - causes white flash on re-render
        
        # Create bridge object for clean QWebChannel communication
        self.bridge = TerminalBridge(self)
        
        # Connect bridge signals to our methods
        self.bridge.terminalClicked.connect(lambda: self.request_focus())
        self.bridge.terminalFocused.connect(lambda: self.request_focus())
        
        # Set initial theme in bridge
        theme_data = get_terminal_theme(self.current_theme)
        self.bridge.set_theme(theme_data)
        
        # Set up JavaScript communication channel with bridge
        from PySide6.QtWebChannel import QWebChannel
        self.channel = QWebChannel()
        self.channel.registerObject("terminal", self.bridge)  # Register bridge, not self
        self.web_view.page().setWebChannel(self.channel)
        
        # Connect to log when terminal loads (no longer need to show/hide)
        self.web_view.loadFinished.connect(self.on_terminal_loaded)
        
        # Add JavaScript console message handler for debugging
        from PySide6.QtWebEngineCore import QWebEnginePage
        page = self.web_view.page()
        page.javaScriptConsoleMessage = self.handle_console_message
        
        layout.addWidget(self.web_view)
        
        # Start terminal session
        self.start_terminal_session()
        
    def mousePressEvent(self, event):
        """Handle mouse press to focus this terminal."""
        logger.debug(f"TerminalAppWidget.mousePressEvent called for widget {self.widget_id}")
        # Request focus when user clicks anywhere on the terminal widget
        self.request_focus()
        logger.debug(f"request_focus() called for terminal {self.widget_id}")
        super().mousePressEvent(event)
        
    def focus_widget(self):
        """Set keyboard focus on the terminal web view."""
        if self.web_view:
            self.web_view.setFocus()
    
    def handle_console_message(self, level, msg, line, source):
        """Handle JavaScript console messages for debugging."""
        level_map = {
            0: "INFO",
            1: "WARNING", 
            2: "ERROR"
        }
        level_str = level_map.get(level, str(level))
        logger.info(f"JS Console [{level_str}] {source}:{line}: {msg}")
    
    def on_web_view_focus_in(self, event):
        """Handle web view focus in event - this should fire when user clicks on terminal."""
        logger.debug(f"WebView focusInEvent for terminal {self.widget_id}")
        # Request focus on the AppWidget when web view gets focus
        self.request_focus()
        # Call the original focusInEvent
        QWebEngineView.focusInEvent(self.web_view, event)
    
        
    def on_terminal_loaded(self, success: bool):
        """Called when the web view finishes loading terminal content."""
        if success:
            logger.info(f"Terminal content loaded successfully for widget {self.widget_id}")
            # Inject a test to see if JavaScript runs
            self.web_view.page().runJavaScript(
                "console.log('Page loaded, checking libraries...'); "
                "console.log('Terminal available:', typeof Terminal !== 'undefined'); "
                "console.log('Socket.io available:', typeof io !== 'undefined');"
            )
        else:
            logger.error(f"Terminal content FAILED to load for widget {self.widget_id}")
            # Try to get more info about the failure
            url = self.web_view.url().toString()
            logger.error(f"Failed URL was: {url}")
        
    def start_terminal_session(self):
        """Start a new terminal session."""
        try:
            # Get initial directory
            initial_dir = self.config.get_initial_directory()
            
            # Create session
            self.session_id = terminal_server.create_session(
                command=self.config.shell,
                cmd_args=self.config.shell_args,
                cwd=initial_dir
            )
            
            # Get bundled HTML instead of using URL
            bundled_html = terminal_asset_bundler.get_bundled_html(
                self.session_id, 
                terminal_server.port
            )
            
            # Set base URL for Socket.IO to work correctly
            base_url = QUrl(f"http://127.0.0.1:{terminal_server.port}/")
            
            logger.info(f"Loading bundled terminal HTML for session: {self.session_id}")
            self.web_view.setHtml(bundled_html, base_url)
            
            logger.info(f"Terminal session started: {self.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to start terminal: {e}")
            # Show error in the web view
            error_html = f"""
            <html>
            <body style="background: #1e1e1e; color: #ff6b6b; padding: 20px; font-family: monospace;">
                <h2>Failed to start terminal</h2>
                <p>{str(e)}</p>
                <p>Please check the terminal server configuration.</p>
            </body>
            </html>
            """
            self.web_view.setHtml(error_html)
            
    def cleanup(self):
        """Clean up terminal session when widget is destroyed."""
        if self.session_id:
            try:
                terminal_server.destroy_session(self.session_id)
                logger.info(f"Terminal session cleaned up: {self.session_id}")
            except Exception as e:
                logger.error(f"Error cleaning up terminal session: {e}")
            finally:
                self.session_id = None
                
    def get_state(self) -> Dict[str, Any]:
        """Get terminal state for persistence."""
        state = super().get_state()
        
        # Add terminal-specific state
        if self.session_id:
            # Try to get current working directory from terminal
            try:
                # This would need terminal server support to get CWD
                state["cwd"] = os.getcwd()  # Placeholder
            except:
                pass
                
        return state
        
    def set_state(self, state: Dict[str, Any]):
        """Restore terminal state."""
        super().set_state(state)
        
        # Could restore working directory if saved
        if "cwd" in state:
            # Would need to send cd command to terminal
            pass
            
    def get_title(self) -> str:
        """Get terminal title."""
        # Could enhance to show current directory or running command
        return "Terminal"
        
    def can_close(self) -> bool:
        """Check if terminal can be closed."""
        # Could check for running processes
        # For now, always allow close (with cleanup)
        return True
        
    def reload(self):
        """Reload the terminal (reconnect to session)."""
        if self.session_id and self.web_view:
            # Get bundled HTML
            bundled_html = terminal_asset_bundler.get_bundled_html(
                self.session_id, 
                terminal_server.port
            )
            # Set base URL for Socket.IO
            base_url = QUrl(f"http://127.0.0.1:{terminal_server.port}/")
            self.web_view.setHtml(bundled_html, base_url)
            
    def execute_command(self, command: str):
        """Execute a command in the terminal."""
        # This would require WebChannel or similar to communicate with xterm.js
        # For now, this is a placeholder
        pass
    
    def on_app_theme_changed(self, theme_name: str):
        """
        Handle theme change from IconManager.
        Push new theme to terminal via bridge.
        """
        logger.info(f"Terminal theme changing to: {theme_name}")
        self.current_theme = theme_name
        theme_data = get_terminal_theme(theme_name)
        
        # Update bridge with new theme
        if self.bridge:
            self.bridge.set_theme(theme_data)
        
        # Also try direct JavaScript injection as fallback
        if self.web_view:
            import json
            theme_json = json.dumps(theme_data)
            js_code = f"if (window.applyTerminalTheme) {{ window.applyTerminalTheme({theme_json}); }}"
            self.web_view.page().runJavaScript(js_code)