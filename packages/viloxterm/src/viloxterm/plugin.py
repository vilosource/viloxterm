"""ViloxTerm Terminal Plugin."""

import logging
from typing import Optional, Dict, Any

from viloapp_sdk import IPlugin, PluginMetadata, PluginCapability, IPluginContext, EventType

from .widget import TerminalWidgetFactory
from .server import terminal_server
from .features import TerminalProfileManager, TerminalSessionManager, TerminalSearch
from .settings import TerminalSettingsManager

logger = logging.getLogger(__name__)


class TerminalPlugin(IPlugin):
    """Terminal emulator plugin for ViloxTerm."""

    def __init__(self):
        self.context: Optional[IPluginContext] = None
        self.widget_factory = TerminalWidgetFactory()
        self.commands_registered = False
        self.profile_manager = TerminalProfileManager()
        self.session_manager = None
        self.search = TerminalSearch()
        self.settings_manager = None

    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            id="viloxterm",
            name="ViloxTerm Terminal",
            version="1.0.0",
            description="Professional terminal emulator with full xterm compatibility",
            author="ViloxTerm Team",
            homepage="https://github.com/viloxterm/viloxterm",
            repository="https://github.com/viloxterm/viloxterm",
            license="MIT",
            icon="terminal",
            categories=["Terminal", "Development Tools"],
            keywords=["terminal", "emulator", "xterm", "console", "shell"],
            engines={"viloapp": ">=2.0.0"},
            dependencies=["viloapp-sdk@>=1.0.0"],
            activation_events=[
                "onCommand:terminal.new",
                "onCommand:terminal.open",
                "onView:terminal",
                "onStartup",
            ],
            capabilities=[PluginCapability.WIDGETS, PluginCapability.COMMANDS],
            contributes={
                "widgets": [
                    {"id": "terminal", "factory": "viloxterm.widget:TerminalWidgetFactory"}
                ],
                "commands": [
                    {"id": "terminal.new", "title": "New Terminal", "category": "Terminal"},
                    {
                        "id": "terminal.newWithProfile",
                        "title": "New Terminal with Profile",
                        "category": "Terminal",
                    },
                    {"id": "terminal.clear", "title": "Clear Terminal", "category": "Terminal"},
                    {"id": "terminal.close", "title": "Close Terminal", "category": "Terminal"},
                    {"id": "terminal.split", "title": "Split Terminal", "category": "Terminal"},
                    {"id": "terminal.focus", "title": "Focus Terminal", "category": "Terminal"},
                    {
                        "id": "terminal.search",
                        "title": "Search in Terminal",
                        "category": "Terminal",
                    },
                    {
                        "id": "terminal.renameSession",
                        "title": "Rename Terminal Session",
                        "category": "Terminal",
                    },
                    {
                        "id": "terminal.listSessions",
                        "title": "List Terminal Sessions",
                        "category": "Terminal",
                    },
                ],
                "configuration": {
                    "terminal.shell.linux": {
                        "type": "string",
                        "default": "/bin/bash",
                        "description": "Path to shell executable on Linux",
                    },
                    "terminal.shell.windows": {
                        "type": "string",
                        "default": "powershell.exe",
                        "description": "Path to shell executable on Windows",
                    },
                    "terminal.fontSize": {
                        "type": "number",
                        "default": 14,
                        "description": "Terminal font size",
                    },
                },
                "keybindings": [
                    {"command": "terminal.new", "key": "ctrl+shift+`"},
                    {"command": "terminal.clear", "key": "ctrl+shift+k", "when": "terminalFocus"},
                ],
            },
        )

    def activate(self, context: IPluginContext) -> None:
        """Activate the plugin."""
        self.context = context
        logger.info("Activating ViloxTerm Terminal plugin")

        # Register commands
        self._register_commands()

        # Register widget factory
        self._register_widget_factory()

        # Subscribe to events
        self._subscribe_to_events()

        # Initialize terminal server
        terminal_server.start_server()

        # Initialize session manager
        self.session_manager = TerminalSessionManager(terminal_server)

        # Initialize settings manager
        config_service = context.get_service("config")
        self.settings_manager = TerminalSettingsManager(config_service)

        # Notify activation
        notification_service = context.get_service("notification")
        if notification_service:
            notification_service.info("Terminal plugin activated")

        logger.info("ViloxTerm Terminal plugin activated successfully")

    def deactivate(self) -> None:
        """Deactivate the plugin."""
        logger.info("Deactivating ViloxTerm Terminal plugin")

        # Cleanup terminal sessions
        terminal_server.cleanup_all_sessions()

        # Shutdown server
        terminal_server.shutdown()

        # Unregister commands
        self._unregister_commands()

        logger.info("ViloxTerm Terminal plugin deactivated")

    def on_configuration_changed(self, config: Dict[str, Any]) -> None:
        """Handle configuration changes."""
        # Update terminal settings
        if "terminal.fontSize" in config:
            # Update font size in active terminals
            pass

        if "terminal.shell.linux" in config or "terminal.shell.windows" in config:
            # Update default shell for new terminals
            pass

    def on_command(self, command_id: str, args: Dict[str, Any]) -> Any:
        """Handle command execution."""
        if command_id == "terminal.new":
            return self._create_new_terminal(args)
        elif command_id == "terminal.newWithProfile":
            return self._create_new_terminal_with_profile(args)
        elif command_id == "terminal.clear":
            return self._clear_terminal(args)
        elif command_id == "terminal.close":
            return self._close_terminal(args)
        elif command_id == "terminal.split":
            return self._split_terminal(args)
        elif command_id == "terminal.focus":
            return self._focus_terminal(args)
        elif command_id == "terminal.search":
            return self._search_in_terminal(args)
        elif command_id == "terminal.renameSession":
            return self._rename_session(args)
        elif command_id == "terminal.listSessions":
            return self._list_sessions(args)

        return None

    def _register_commands(self):
        """Register terminal commands."""
        if self.commands_registered:
            return

        command_service = self.context.get_service("command")
        if command_service:
            # Register command handlers
            command_service.register_command("terminal.new", self._create_new_terminal)
            command_service.register_command(
                "terminal.newWithProfile", self._create_new_terminal_with_profile
            )
            command_service.register_command("terminal.clear", self._clear_terminal)
            command_service.register_command("terminal.close", self._close_terminal)
            command_service.register_command("terminal.split", self._split_terminal)
            command_service.register_command("terminal.focus", self._focus_terminal)
            command_service.register_command("terminal.search", self._search_in_terminal)
            command_service.register_command("terminal.renameSession", self._rename_session)
            command_service.register_command("terminal.listSessions", self._list_sessions)

            self.commands_registered = True

    def _unregister_commands(self):
        """Unregister terminal commands."""
        if not self.commands_registered:
            return

        command_service = self.context.get_service("command")
        if command_service:
            command_service.unregister_command("terminal.new")
            command_service.unregister_command("terminal.clear")
            command_service.unregister_command("terminal.close")
            command_service.unregister_command("terminal.split")
            command_service.unregister_command("terminal.focus")

            self.commands_registered = False

    def _register_widget_factory(self):
        """Register widget factory with workspace service."""
        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            workspace_service.register_widget_factory("terminal", self.widget_factory)

    def _subscribe_to_events(self):
        """Subscribe to relevant events."""
        # Subscribe to theme changes to update terminal colors
        self.context.subscribe_event(EventType.THEME_CHANGED, self._on_theme_changed)

        # Subscribe to settings changes
        self.context.subscribe_event(EventType.SETTINGS_CHANGED, self._on_settings_changed)

    def _on_theme_changed(self, event):
        """Handle theme change event."""
        logger.debug(f"Theme changed: {event.data}")
        # Update terminal colors based on new theme
        if self.settings_manager:
            self.settings_manager.sync_with_theme(event.data)

    def _on_settings_changed(self, event):
        """Handle settings change event."""
        if "terminal" in event.data:
            self.on_configuration_changed(event.data)

    # Command implementations
    def _create_new_terminal(self, args: Dict[str, Any] = None) -> Any:
        """Create a new terminal."""
        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            # Create terminal widget
            widget = self.widget_factory.create_instance(f"terminal_{id(self)}")

            # Add to workspace
            workspace_service.add_widget(widget, "terminal", "main")

            return {"success": True, "widget_id": id(widget)}

        return {"success": False, "error": "Workspace service not available"}

    def _clear_terminal(self, args: Dict[str, Any] = None) -> Any:
        """Clear the active terminal."""
        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            # Get active terminal widget
            active_widget = workspace_service.get_active_widget()
            if active_widget and hasattr(active_widget, "clear_terminal"):
                active_widget.clear_terminal()
                return {"success": True}

        return {"success": False, "error": "No active terminal"}

    def _close_terminal(self, args: Dict[str, Any] = None) -> Any:
        """Close the active terminal."""
        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            # Get active terminal widget
            active_widget = workspace_service.get_active_widget()
            if active_widget and hasattr(active_widget, "stop_terminal"):
                active_widget.stop_terminal()
                workspace_service.remove_widget(active_widget)
                return {"success": True}

        return {"success": False, "error": "No active terminal"}

    def _split_terminal(self, args: Dict[str, Any] = None) -> Any:
        """Split the terminal."""
        # Implementation for split terminal
        return {"success": False, "error": "Not implemented"}

    def _focus_terminal(self, args: Dict[str, Any] = None) -> Any:
        """Focus the terminal."""
        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            # Get active terminal widget
            active_widget = workspace_service.get_active_widget()
            if active_widget and hasattr(active_widget, "focus_terminal"):
                active_widget.focus_terminal()
                return {"success": True}

        return {"success": False, "error": "No active terminal"}

    def _create_new_terminal_with_profile(self, args: Dict[str, Any] = None) -> Any:
        """Create a new terminal with a specific profile."""
        profile_name = args.get("profile") if args else None

        # Get profile
        if profile_name:
            profile = None
            for p in self.profile_manager.list_profiles():
                if p.name == profile_name:
                    profile = p
                    break
        else:
            profile = self.profile_manager.get_default_profile()

        if not profile:
            return {"success": False, "error": "Profile not found"}

        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            # Create session with profile
            session_id = self.session_manager.create_session(profile)

            # Create terminal widget
            widget = self.widget_factory.create_instance(f"terminal_{id(self)}")
            widget.session_id = session_id

            # Apply settings
            if self.settings_manager:
                self.settings_manager.apply_to_terminal(widget)

            # Add to workspace
            workspace_service.add_widget(widget, f"{profile.name} Terminal", "main")

            return {"success": True, "session_id": session_id}

        return {"success": False, "error": "Workspace service not available"}

    def _search_in_terminal(self, args: Dict[str, Any] = None) -> Any:
        """Search in the active terminal."""
        if not args or "pattern" not in args:
            return {"success": False, "error": "Search pattern required"}

        pattern = args["pattern"]
        case_sensitive = args.get("case_sensitive", False)

        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            active_widget = workspace_service.get_active_widget()
            if active_widget and hasattr(active_widget, "web_view"):
                self.search.search_in_terminal(active_widget, pattern, case_sensitive)
                return {"success": True, "pattern": pattern}

        return {"success": False, "error": "No active terminal"}

    def _rename_session(self, args: Dict[str, Any] = None) -> Any:
        """Rename a terminal session."""
        if not args or "session_id" not in args or "name" not in args:
            return {"success": False, "error": "Session ID and name required"}

        session_id = args["session_id"]
        name = args["name"]

        if self.session_manager:
            self.session_manager.rename_session(session_id, name)
            return {"success": True, "session_id": session_id, "name": name}

        return {"success": False, "error": "Session manager not available"}

    def _list_sessions(self, args: Dict[str, Any] = None) -> Any:
        """List all terminal sessions."""
        if self.session_manager:
            sessions = self.session_manager.list_sessions()
            return {"success": True, "sessions": sessions}

        return {"success": False, "error": "Session manager not available"}
