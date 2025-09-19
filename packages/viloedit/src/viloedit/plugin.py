"""ViloEdit Code Editor Plugin."""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from viloapp_sdk import (
    IPlugin, PluginMetadata, PluginCapability,
    IPluginContext, EventType
)

from .widget import EditorWidgetFactory
from .editor import CodeEditor
from .syntax import SyntaxHighlighter
from .commands import register_editor_commands

logger = logging.getLogger(__name__)


class EditorPlugin(IPlugin):
    """Code editor plugin for ViloxTerm."""

    def __init__(self):
        self.context: Optional[IPluginContext] = None
        self.widget_factory = EditorWidgetFactory()
        self.open_editors: Dict[str, CodeEditor] = {}

    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            id="viloedit",
            name="ViloEdit",
            version="1.0.0",
            description="Professional code editor with syntax highlighting",
            author="ViloxTerm Team",
            homepage="https://github.com/viloxterm/viloedit",
            license="MIT",
            icon="file-text",
            categories=["Editor", "Development Tools"],
            keywords=["editor", "code", "syntax", "highlighting"],
            engines={"viloapp": ">=2.0.0"},
            dependencies=["viloapp-sdk@>=1.0.0"],
            activation_events=[
                "onCommand:editor.open",
                "onCommand:editor.new",
                "onLanguage:python",
                "onLanguage:javascript",
                "workspaceContains:**/*.py"
            ],
            capabilities=[PluginCapability.WIDGETS, PluginCapability.COMMANDS, PluginCapability.LANGUAGES],
            contributes={
                "widgets": [
                    {
                        "id": "editor",
                        "factory": "viloedit.widget:EditorWidgetFactory"
                    }
                ],
                "commands": [
                    {
                        "id": "editor.open",
                        "title": "Open File",
                        "category": "Editor"
                    },
                    {
                        "id": "editor.save",
                        "title": "Save File",
                        "category": "Editor"
                    },
                    {
                        "id": "editor.saveAs",
                        "title": "Save As...",
                        "category": "Editor"
                    },
                    {
                        "id": "editor.close",
                        "title": "Close Editor",
                        "category": "Editor"
                    },
                    {
                        "id": "editor.new",
                        "title": "New File",
                        "category": "Editor"
                    }
                ],
                "languages": [
                    {
                        "id": "python",
                        "extensions": [".py", ".pyw"],
                        "aliases": ["Python", "py"]
                    },
                    {
                        "id": "javascript",
                        "extensions": [".js", ".jsx"],
                        "aliases": ["JavaScript", "js"]
                    },
                    {
                        "id": "json",
                        "extensions": [".json"],
                        "aliases": ["JSON"]
                    },
                    {
                        "id": "markdown",
                        "extensions": [".md", ".markdown"],
                        "aliases": ["Markdown"]
                    }
                ],
                "keybindings": [
                    {
                        "command": "editor.save",
                        "key": "ctrl+s"
                    },
                    {
                        "command": "editor.open",
                        "key": "ctrl+o"
                    },
                    {
                        "command": "editor.new",
                        "key": "ctrl+n"
                    }
                ]
            }
        )

    def activate(self, context: IPluginContext) -> None:
        """Activate the plugin."""
        self.context = context
        logger.info("Activating ViloEdit plugin")

        # Register commands
        self._register_commands()

        # Register widget factory
        self._register_widget_factory()

        # Subscribe to events
        self._subscribe_to_events()

        # Notify activation
        notification_service = context.get_service("notification")
        if notification_service:
            notification_service.info("Editor plugin activated")

        logger.info("ViloEdit plugin activated successfully")

    def deactivate(self) -> None:
        """Deactivate the plugin."""
        logger.info("Deactivating ViloEdit plugin")

        # Close all open editors
        for editor in self.open_editors.values():
            editor.close()
        self.open_editors.clear()

        logger.info("ViloEdit plugin deactivated")

    def on_command(self, command_id: str, args: Dict[str, Any]) -> Any:
        """Handle command execution."""
        if command_id == "editor.open":
            return self._open_file(args)
        elif command_id == "editor.save":
            return self._save_file(args)
        elif command_id == "editor.saveAs":
            return self._save_file_as(args)
        elif command_id == "editor.close":
            return self._close_editor(args)
        elif command_id == "editor.new":
            return self._new_file(args)

        return None

    def _register_commands(self):
        """Register editor commands."""
        command_service = self.context.get_service("command")
        if command_service:
            register_editor_commands(command_service, self)

    def _register_widget_factory(self):
        """Register widget factory."""
        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            workspace_service.register_widget_factory("editor", self.widget_factory)

    def _subscribe_to_events(self):
        """Subscribe to events."""
        self.context.subscribe_event(EventType.THEME_CHANGED, self._on_theme_changed)

    def _on_theme_changed(self, event):
        """Handle theme change."""
        # Update syntax highlighting colors
        for editor in self.open_editors.values():
            if hasattr(editor, 'update_theme'):
                editor.update_theme(event.data)

    def _new_file(self, args: Dict[str, Any]) -> Any:
        """Create a new file."""
        # Create editor widget
        editor = self.widget_factory.create_widget()

        # Add to workspace
        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            workspace_service.add_widget(editor, "Untitled", "main")
            return {"success": True}

        return {"success": False, "error": "Workspace service not available"}

    def _open_file(self, args: Dict[str, Any]) -> Any:
        """Open a file in the editor."""
        file_path = args.get('path')
        if not file_path:
            # Show file dialog
            from PySide6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getOpenFileName(
                None, "Open File", "", "All Files (*.*)"
            )

        if file_path:
            # Create editor widget
            editor = self.widget_factory.create_widget()
            editor.load_file(file_path)

            # Track open editor
            self.open_editors[file_path] = editor

            # Add to workspace
            workspace_service = self.context.get_service("workspace")
            if workspace_service:
                workspace_service.add_widget(editor, Path(file_path).name, "main")

            return {"success": True, "path": file_path}

        return {"success": False, "error": "No file selected"}

    def _save_file(self, args: Dict[str, Any]) -> Any:
        """Save the current file."""
        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            editor = workspace_service.get_active_widget()
            if isinstance(editor, CodeEditor):
                if editor.save_file():
                    return {"success": True}

        return {"success": False, "error": "No active editor"}

    def _save_file_as(self, args: Dict[str, Any]) -> Any:
        """Save file with a new name."""
        from PySide6.QtWidgets import QFileDialog

        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            editor = workspace_service.get_active_widget()
            if isinstance(editor, CodeEditor):
                file_path, _ = QFileDialog.getSaveFileName(
                    None, "Save File As", "", "All Files (*.*)"
                )

                if file_path and editor.save_file(file_path):
                    return {"success": True, "path": file_path}

        return {"success": False, "error": "Save cancelled"}

    def _close_editor(self, args: Dict[str, Any]) -> Any:
        """Close the current editor."""
        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            editor = workspace_service.get_active_widget()
            if isinstance(editor, CodeEditor):
                # Check for unsaved changes
                if editor.document().isModified():
                    # Ask to save
                    from PySide6.QtWidgets import QMessageBox
                    reply = QMessageBox.question(
                        None, "Save Changes",
                        "Do you want to save changes before closing?",
                        QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                    )

                    if reply == QMessageBox.Save:
                        if not editor.save_file():
                            return {"success": False, "error": "Save failed"}
                    elif reply == QMessageBox.Cancel:
                        return {"success": False, "error": "Close cancelled"}

                # Remove from tracking
                if editor.file_path:
                    path_str = str(editor.file_path)
                    if path_str in self.open_editors:
                        del self.open_editors[path_str]

                # Remove from workspace
                workspace_service.remove_widget(editor)
                return {"success": True}

        return {"success": False, "error": "No active editor"}