# Week 5: System Integration and Core Plugins

## Overview
Week 5 focuses on integrating the plugin system with the main application, creating core plugins for existing functionality, and ensuring seamless operation.

**Duration**: 5 days
**Goal**: Complete system integration, create core plugins, and ensure all functionality works through the plugin system

## Prerequisites
- [ ] Weeks 1-4 completed successfully
- [ ] Terminal and Editor plugins working
- [ ] Plugin infrastructure stable

## Day 1: Core Application Refactoring

### Morning (3 hours)

#### Task 1.1: Update Main Application Entry Point

Modify `/home/kuja/GitHub/viloapp/main.py`:
```python
#!/usr/bin/env python3
"""
ViloxTerm - Extensible Terminal Application
Plugin-based architecture version.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QSettings

from core.plugin_system import PluginManager
from viloapp_sdk import EventBus
from ui.main_window import MainWindow
from services import initialize_services, get_all_services

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ViloxTermApplication:
    """Main application class with plugin support."""

    def __init__(self):
        self.app: Optional[QApplication] = None
        self.window: Optional[MainWindow] = None
        self.plugin_manager: Optional[PluginManager] = None
        self.services = {}

    def initialize(self, args):
        """Initialize the application."""
        # Create Qt application
        self.app = QApplication(args)
        self.app.setApplicationName("ViloxTerm")
        self.app.setOrganizationName("ViloxTerm")

        # Initialize services
        self.services = initialize_services()

        # Initialize plugin system
        self._initialize_plugins()

        # Create main window
        self.window = MainWindow(self.services)

        # Load application state
        self._load_state()

        # Apply initial theme
        self._apply_theme()

        return True

    def _initialize_plugins(self):
        """Initialize the plugin system."""
        logger.info("Initializing plugin system...")

        # Create event bus
        event_bus = EventBus()

        # Create plugin manager
        self.plugin_manager = PluginManager(event_bus, self.services)

        # Add plugin manager to services
        self.services['plugin_manager'] = self.plugin_manager
        self.services['event_bus'] = event_bus

        # Initialize plugins
        self.plugin_manager.initialize()

        # Load plugin state
        state_path = self._get_plugin_state_path()
        self.plugin_manager.load_state(state_path)

        logger.info(f"Loaded {len(self.plugin_manager.list_plugins())} plugins")

    def _get_plugin_state_path(self) -> Path:
        """Get plugin state file path."""
        import platformdirs
        data_dir = Path(platformdirs.user_data_dir("ViloxTerm"))
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "plugin_state.json"

    def _load_state(self):
        """Load application state."""
        settings = QSettings()

        # Restore window geometry
        if settings.contains("MainWindow/geometry"):
            self.window.restoreGeometry(settings.value("MainWindow/geometry"))
        if settings.contains("MainWindow/state"):
            self.window.restoreState(settings.value("MainWindow/state"))

    def _apply_theme(self):
        """Apply the initial theme."""
        theme_service = self.services.get('theme_service')
        if theme_service:
            theme_service.apply_current_theme()

    def run(self):
        """Run the application."""
        if not self.window:
            return 1

        self.window.show()

        # Run Qt event loop
        result = self.app.exec()

        # Cleanup
        self._cleanup()

        return result

    def _cleanup(self):
        """Clean up before exit."""
        logger.info("Shutting down ViloxTerm...")

        # Save application state
        self._save_state()

        # Save plugin state
        if self.plugin_manager:
            state_path = self._get_plugin_state_path()
            self.plugin_manager.save_state(state_path)

            # Deactivate all plugins
            for plugin_id in self.plugin_manager.list_plugins():
                try:
                    self.plugin_manager.deactivate_plugin(plugin_id['id'])
                except Exception as e:
                    logger.error(f"Failed to deactivate plugin {plugin_id}: {e}")

    def _save_state(self):
        """Save application state."""
        if not self.window:
            return

        settings = QSettings()
        settings.setValue("MainWindow/geometry", self.window.saveGeometry())
        settings.setValue("MainWindow/state", self.window.saveState())
        settings.sync()


def main():
    """Main entry point."""
    app = ViloxTermApplication()

    if not app.initialize(sys.argv):
        return 1

    return app.run()


if __name__ == "__main__":
    sys.exit(main())
```

#### Task 1.2: Update Main Window

Modify `/home/kuja/GitHub/viloapp/ui/main_window.py`:
```python
"""Main window with plugin support."""

import logging
from typing import Dict, Any

from PySide6.QtWidgets import QMainWindow, QMenuBar, QStatusBar, QDockWidget
from PySide6.QtCore import Qt, Signal

from ui.activity_bar import ActivityBar
from ui.sidebar import Sidebar
from ui.workspace import Workspace
from ui.status_bar import StatusBar

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window with plugin support."""

    # Signals
    plugin_loaded = Signal(str)  # plugin_id
    plugin_unloaded = Signal(str)  # plugin_id

    def __init__(self, services: Dict[str, Any], parent=None):
        super().__init__(parent)

        self.services = services
        self.plugin_manager = services.get('plugin_manager')
        self.plugins_initialized = False

        self.setup_ui()
        self.setup_plugins()

    def setup_ui(self):
        """Setup the main window UI."""
        self.setWindowTitle("ViloxTerm")
        self.resize(1200, 800)

        # Create menu bar
        self.create_menus()

        # Create activity bar
        self.activity_bar = ActivityBar(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._create_dock(self.activity_bar, "Activity"))

        # Create sidebar
        self.sidebar = Sidebar(self)
        self.sidebar_dock = self._create_dock(self.sidebar, "Sidebar")
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sidebar_dock)

        # Create workspace
        self.workspace = Workspace(self.services, self)
        self.setCentralWidget(self.workspace)

        # Create status bar
        self.status_bar = StatusBar(self)
        self.setStatusBar(self.status_bar)

    def _create_dock(self, widget, title):
        """Create a dock widget."""
        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        return dock

    def create_menus(self):
        """Create application menus."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        self._add_plugin_actions(file_menu, "file")

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        self._add_plugin_actions(edit_menu, "edit")

        # View menu
        view_menu = menubar.addMenu("&View")
        self._add_plugin_actions(view_menu, "view")

        # Terminal menu (if terminal plugin loaded)
        if self._is_plugin_loaded("viloxterm"):
            terminal_menu = menubar.addMenu("&Terminal")
            self._add_plugin_actions(terminal_menu, "terminal")

        # Plugins menu
        plugins_menu = menubar.addMenu("&Plugins")
        self._create_plugin_menu(plugins_menu)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        self._add_plugin_actions(help_menu, "help")

    def _is_plugin_loaded(self, plugin_id: str) -> bool:
        """Check if a plugin is loaded."""
        if not self.plugin_manager:
            return False

        plugin_info = self.plugin_manager.get_plugin_metadata(plugin_id)
        return plugin_info and plugin_info.get('state') == 'ACTIVATED'

    def _add_plugin_actions(self, menu, category):
        """Add plugin-contributed actions to a menu."""
        if not self.plugin_manager:
            return

        # Get commands from all plugins for this category
        for plugin_id, plugin in self.plugin_manager.get_all_plugins().items():
            metadata = plugin.get_metadata()
            if metadata.contributes:
                commands = metadata.contributes.get('commands', [])
                for command in commands:
                    if command.get('category', '').lower() == category:
                        action = menu.addAction(command['title'])
                        action.triggered.connect(
                            lambda checked, cmd=command['id']: self._execute_command(cmd)
                        )

    def _create_plugin_menu(self, menu):
        """Create the plugins menu."""
        # Manage plugins action
        manage_action = menu.addAction("Manage Plugins...")
        manage_action.triggered.connect(self._show_plugin_manager)

        menu.addSeparator()

        # Installed plugins submenu
        installed_menu = menu.addMenu("Installed Plugins")
        self._populate_installed_plugins(installed_menu)

        menu.addSeparator()

        # Reload plugins action
        reload_action = menu.addAction("Reload All Plugins")
        reload_action.triggered.connect(self._reload_all_plugins)

    def _populate_installed_plugins(self, menu):
        """Populate installed plugins menu."""
        if not self.plugin_manager:
            return

        plugins = self.plugin_manager.list_plugins()
        for plugin_info in plugins:
            plugin_menu = menu.addMenu(plugin_info['name'])

            # Enable/disable action
            if plugin_info['state'] == 'ACTIVATED':
                action = plugin_menu.addAction("Disable")
                action.triggered.connect(
                    lambda checked, pid=plugin_info['id']: self._disable_plugin(pid)
                )
            else:
                action = plugin_menu.addAction("Enable")
                action.triggered.connect(
                    lambda checked, pid=plugin_info['id']: self._enable_plugin(pid)
                )

            # Reload action
            reload_action = plugin_menu.addAction("Reload")
            reload_action.triggered.connect(
                lambda checked, pid=plugin_info['id']: self._reload_plugin(pid)
            )

            # Info action
            info_action = plugin_menu.addAction("Information")
            info_action.triggered.connect(
                lambda checked, pid=plugin_info['id']: self._show_plugin_info(pid)
            )

    def setup_plugins(self):
        """Setup plugin integration."""
        if not self.plugin_manager or self.plugins_initialized:
            return

        logger.info("Setting up plugin integration...")

        # Register workspace widget factories
        for plugin_id, plugin in self.plugin_manager.get_all_plugins().items():
            metadata = plugin.get_metadata()

            # Register widget factories
            widgets = metadata.contributes.get('widgets', [])
            for widget_config in widgets:
                widget_id = widget_config['id']
                factory_path = widget_config.get('factory')

                if factory_path:
                    # Import and register factory
                    try:
                        module_name, class_name = factory_path.rsplit(':', 1)
                        module = __import__(module_name, fromlist=[class_name])
                        factory_class = getattr(module, class_name)
                        factory = factory_class()

                        workspace_service = self.services.get('workspace_service')
                        if workspace_service:
                            workspace_service.register_widget_factory(widget_id, factory)

                    except Exception as e:
                        logger.error(f"Failed to register widget factory {factory_path}: {e}")

        self.plugins_initialized = True

    def _execute_command(self, command_id: str):
        """Execute a command."""
        from core.commands.executor import execute_command
        result = execute_command(command_id)

        if not result.success:
            logger.error(f"Command {command_id} failed: {result.error}")

    def _show_plugin_manager(self):
        """Show plugin manager dialog."""
        from ui.widgets.plugin_settings_widget import PluginSettingsWidget

        dialog = QDialog(self)
        dialog.setWindowTitle("Plugin Manager")
        dialog.setModal(True)

        widget = PluginSettingsWidget(self.plugin_manager)
        layout = QVBoxLayout()
        layout.addWidget(widget)
        dialog.setLayout(layout)

        dialog.exec()

    def _enable_plugin(self, plugin_id: str):
        """Enable a plugin."""
        if self.plugin_manager:
            if self.plugin_manager.enable_plugin(plugin_id):
                logger.info(f"Enabled plugin: {plugin_id}")
                self.plugin_loaded.emit(plugin_id)
                # Refresh menus
                self.create_menus()

    def _disable_plugin(self, plugin_id: str):
        """Disable a plugin."""
        if self.plugin_manager:
            if self.plugin_manager.disable_plugin(plugin_id):
                logger.info(f"Disabled plugin: {plugin_id}")
                self.plugin_unloaded.emit(plugin_id)
                # Refresh menus
                self.create_menus()

    def _reload_plugin(self, plugin_id: str):
        """Reload a plugin."""
        if self.plugin_manager:
            if self.plugin_manager.reload_plugin(plugin_id):
                logger.info(f"Reloaded plugin: {plugin_id}")

    def _reload_all_plugins(self):
        """Reload all plugins."""
        if not self.plugin_manager:
            return

        plugins = self.plugin_manager.list_plugins()
        for plugin_info in plugins:
            if plugin_info['state'] == 'ACTIVATED':
                self._reload_plugin(plugin_info['id'])

    def _show_plugin_info(self, plugin_id: str):
        """Show plugin information."""
        if not self.plugin_manager:
            return

        info = self.plugin_manager.get_plugin_metadata(plugin_id)
        if info:
            from PySide6.QtWidgets import QMessageBox

            message = f"""
            Plugin: {info['name']}
            Version: {info['version']}
            Author: {info['author']}
            Description: {info['description']}
            State: {info['state']}
            """

            QMessageBox.information(self, "Plugin Information", message)
```

### Afternoon (3 hours)

#### Task 1.3: Update Workspace for Plugin Widgets

Modify `/home/kuja/GitHub/viloapp/ui/workspace.py`:
```python
"""Workspace with plugin widget support."""

import logging
from typing import Dict, Any, Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PySide6.QtCore import Qt, Signal

logger = logging.getLogger(__name__)


class Workspace(QWidget):
    """Workspace with plugin widget support."""

    # Signals
    widget_added = Signal(str, object)  # widget_id, widget
    widget_removed = Signal(str, object)  # widget_id, widget
    widget_focused = Signal(str, object)  # widget_id, widget

    def __init__(self, services: Dict[str, Any], parent=None):
        super().__init__(parent)

        self.services = services
        self.plugin_manager = services.get('plugin_manager')
        self.widget_factories = {}
        self.active_widgets = {}

        self.setup_ui()

    def setup_ui(self):
        """Setup workspace UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Create main splitter
        self.splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.splitter)

        self.setLayout(layout)

        # Create default panes
        self._create_default_layout()

    def _create_default_layout(self):
        """Create default workspace layout."""
        # Left pane (for file explorer, etc.)
        left_pane = QWidget()
        self.splitter.addWidget(left_pane)

        # Main pane (for editors/terminals)
        self.main_pane = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.main_pane)

        # Set initial sizes
        self.splitter.setSizes([200, 1000])

    def register_widget_factory(self, widget_id: str, factory):
        """Register a widget factory from a plugin."""
        self.widget_factories[widget_id] = factory
        logger.info(f"Registered widget factory: {widget_id}")

    def create_widget(self, widget_type: str, **kwargs) -> Optional[QWidget]:
        """Create a widget using registered factory."""
        factory = self.widget_factories.get(widget_type)
        if not factory:
            logger.error(f"No factory registered for widget type: {widget_type}")
            return None

        try:
            widget = factory.create_widget(self)

            # Track widget
            widget_id = str(id(widget))
            self.active_widgets[widget_id] = {
                'type': widget_type,
                'widget': widget,
                'factory': factory
            }

            # Emit signal
            self.widget_added.emit(widget_id, widget)

            return widget

        except Exception as e:
            logger.error(f"Failed to create widget {widget_type}: {e}")
            return None

    def add_widget(self, widget: QWidget, title: str = None, position: str = "main"):
        """Add a widget to the workspace."""
        if position == "main":
            self.main_pane.addWidget(widget)
        elif position == "left":
            # Add to left pane
            pass
        elif position == "right":
            # Add to right pane
            pass
        elif position == "bottom":
            # Add to bottom pane
            pass

        # Track widget
        widget_id = str(id(widget))
        if widget_id not in self.active_widgets:
            self.active_widgets[widget_id] = {
                'type': 'custom',
                'widget': widget,
                'title': title
            }

        self.widget_added.emit(widget_id, widget)

    def remove_widget(self, widget: QWidget):
        """Remove a widget from the workspace."""
        widget_id = str(id(widget))

        # Remove from tracking
        if widget_id in self.active_widgets:
            del self.active_widgets[widget_id]

        # Remove from UI
        widget.setParent(None)
        widget.deleteLater()

        self.widget_removed.emit(widget_id, widget)

    def get_active_widget(self) -> Optional[QWidget]:
        """Get the currently active widget."""
        # Return the widget with focus
        focused_widget = QApplication.focusWidget()

        # Check if it's one of our tracked widgets
        for widget_info in self.active_widgets.values():
            if widget_info['widget'] == focused_widget:
                return focused_widget

        return None

    def get_widgets_by_type(self, widget_type: str) -> list:
        """Get all widgets of a specific type."""
        widgets = []
        for widget_info in self.active_widgets.values():
            if widget_info.get('type') == widget_type:
                widgets.append(widget_info['widget'])
        return widgets

    def save_state(self) -> Dict[str, Any]:
        """Save workspace state."""
        state = {
            'splitter_sizes': self.splitter.sizes(),
            'main_pane_sizes': self.main_pane.sizes(),
            'widgets': []
        }

        # Save widget states
        for widget_id, widget_info in self.active_widgets.items():
            factory = widget_info.get('factory')
            if factory and hasattr(factory, 'get_state'):
                widget_state = {
                    'type': widget_info['type'],
                    'state': factory.get_state()
                }
                state['widgets'].append(widget_state)

        return state

    def restore_state(self, state: Dict[str, Any]):
        """Restore workspace state."""
        if 'splitter_sizes' in state:
            self.splitter.setSizes(state['splitter_sizes'])

        if 'main_pane_sizes' in state:
            self.main_pane.setSizes(state['main_pane_sizes'])

        # Restore widgets
        for widget_state in state.get('widgets', []):
            widget_type = widget_state['type']
            widget = self.create_widget(widget_type)

            if widget:
                factory = self.widget_factories.get(widget_type)
                if factory and hasattr(factory, 'restore_state'):
                    factory.restore_state(widget_state['state'])
```

### Validation Checkpoint
- [ ] Main application refactored
- [ ] Plugin integration in main window
- [ ] Workspace supports plugin widgets
- [ ] Commands routed through plugins

## Day 2: Core Plugins Creation

### Morning (3 hours)

#### Task 2.1: Create Command Palette Plugin

Create `/home/kuja/GitHub/viloapp/core/plugins/command_palette/plugin.py`:
```python
"""Command Palette core plugin."""

import logging
from typing import Optional

from viloapp_sdk import IPlugin, PluginMetadata, IPluginContext
from .command_palette_widget import CommandPaletteWidget

logger = logging.getLogger(__name__)


class CommandPalettePlugin(IPlugin):
    """Core plugin providing command palette functionality."""

    def __init__(self):
        self.context: Optional[IPluginContext] = None
        self.palette_widget: Optional[CommandPaletteWidget] = None

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="core-command-palette",
            name="Command Palette",
            version="1.0.0",
            description="Quick command execution interface",
            author="ViloxTerm Core",
            contributes={
                "commands": [
                    {
                        "id": "workbench.action.showCommands",
                        "title": "Show All Commands",
                        "category": "View"
                    }
                ],
                "keybindings": [
                    {
                        "command": "workbench.action.showCommands",
                        "key": "ctrl+shift+p"
                    }
                ]
            }
        )

    def activate(self, context: IPluginContext) -> None:
        self.context = context
        self._register_commands()

    def deactivate(self) -> None:
        if self.palette_widget:
            self.palette_widget.close()

    def _register_commands(self):
        command_service = self.context.get_service("command")
        if command_service:
            command_service.register_command(
                "workbench.action.showCommands",
                self._show_command_palette
            )

    def _show_command_palette(self, **kwargs):
        if not self.palette_widget:
            self.palette_widget = CommandPaletteWidget()

        self.palette_widget.show()
        self.palette_widget.raise_()
        self.palette_widget.activateWindow()
```

#### Task 2.2: Create Theme Plugin

Create `/home/kuja/GitHub/viloapp/core/plugins/themes/plugin.py`:
```python
"""Theme management core plugin."""

import logging
from typing import Optional

from viloapp_sdk import IPlugin, PluginMetadata, IPluginContext, EventType

logger = logging.getLogger(__name__)


class ThemePlugin(IPlugin):
    """Core plugin providing theme management."""

    def __init__(self):
        self.context: Optional[IPluginContext] = None

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="core-themes",
            name="Theme Support",
            version="1.0.0",
            description="Built-in theme management",
            author="ViloxTerm Core",
            contributes={
                "themes": [
                    {
                        "id": "vscode-dark",
                        "label": "VSCode Dark+",
                        "path": "themes/vscode-dark.json"
                    },
                    {
                        "id": "vscode-light",
                        "label": "VSCode Light",
                        "path": "themes/vscode-light.json"
                    }
                ],
                "commands": [
                    {
                        "id": "theme.selectTheme",
                        "title": "Select Color Theme",
                        "category": "Preferences"
                    }
                ]
            }
        )

    def activate(self, context: IPluginContext) -> None:
        self.context = context
        self._register_commands()
        self._load_themes()

    def deactivate(self) -> None:
        pass

    def _register_commands(self):
        command_service = self.context.get_service("command")
        if command_service:
            command_service.register_command(
                "theme.selectTheme",
                self._select_theme
            )

    def _load_themes(self):
        """Load contributed themes."""
        theme_service = self.context.get_service("theme")
        if not theme_service:
            return

        # Load themes from contributions
        for theme_config in self.get_metadata().contributes.get("themes", []):
            theme_path = self.context.get_plugin_path() / theme_config["path"]
            if theme_path.exists():
                # Load and register theme
                pass

    def _select_theme(self, **kwargs):
        """Show theme selection dialog."""
        # Implementation
        pass
```

### Afternoon (3 hours)

#### Task 2.3: Create Settings Plugin

Create `/home/kuja/GitHub/viloapp/core/plugins/settings/plugin.py`:
```python
"""Settings management core plugin."""

import logging
from typing import Optional

from viloapp_sdk import IPlugin, PluginMetadata, IPluginContext

logger = logging.getLogger(__name__)


class SettingsPlugin(IPlugin):
    """Core plugin providing settings management."""

    def __init__(self):
        self.context: Optional[IPluginContext] = None

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="core-settings",
            name="Settings",
            version="1.0.0",
            description="Application settings management",
            author="ViloxTerm Core",
            contributes={
                "commands": [
                    {
                        "id": "workbench.action.openSettings",
                        "title": "Preferences",
                        "category": "File"
                    },
                    {
                        "id": "workbench.action.openSettingsJson",
                        "title": "Preferences (JSON)",
                        "category": "File"
                    }
                ],
                "keybindings": [
                    {
                        "command": "workbench.action.openSettings",
                        "key": "ctrl+,"
                    }
                ]
            }
        )

    def activate(self, context: IPluginContext) -> None:
        self.context = context
        self._register_commands()

    def deactivate(self) -> None:
        pass

    def _register_commands(self):
        command_service = self.context.get_service("command")
        if command_service:
            command_service.register_command(
                "workbench.action.openSettings",
                self._open_settings
            )
            command_service.register_command(
                "workbench.action.openSettingsJson",
                self._open_settings_json
            )

    def _open_settings(self, **kwargs):
        """Open settings UI."""
        from ui.widgets.settings_app_widget import SettingsAppWidget

        workspace_service = self.context.get_service("workspace")
        if workspace_service:
            widget = SettingsAppWidget()
            workspace_service.add_widget(widget, "Settings", "main")

    def _open_settings_json(self, **kwargs):
        """Open settings.json file."""
        # Implementation
        pass
```

### Validation Checkpoint
- [ ] Core plugins created
- [ ] Command palette working
- [ ] Theme support integrated
- [ ] Settings accessible

## Day 3: Migration and Compatibility

### Morning (3 hours)

#### Task 3.1: Create Migration Scripts

Create `/home/kuja/GitHub/viloapp/scripts/migrate_to_plugins.py`:
```python
#!/usr/bin/env python3
"""Migrate existing ViloxTerm configuration to plugin architecture."""

import json
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_settings():
    """Migrate old settings to new format."""
    import platformdirs

    old_config_dir = Path.home() / ".config" / "ViloxTerm"
    new_config_dir = Path(platformdirs.user_config_dir("ViloxTerm"))

    if old_config_dir.exists() and old_config_dir != new_config_dir:
        logger.info(f"Migrating settings from {old_config_dir} to {new_config_dir}")

        # Copy settings files
        new_config_dir.mkdir(parents=True, exist_ok=True)

        # Migrate settings.json
        old_settings = old_config_dir / "settings.json"
        if old_settings.exists():
            with open(old_settings, 'r') as f:
                settings = json.load(f)

            # Transform settings for plugin architecture
            new_settings = transform_settings(settings)

            new_settings_file = new_config_dir / "settings.json"
            with open(new_settings_file, 'w') as f:
                json.dump(new_settings, f, indent=2)

            logger.info("Settings migrated successfully")


def transform_settings(old_settings):
    """Transform old settings to new format."""
    new_settings = {}

    # Map old settings to plugin settings
    if "terminal" in old_settings:
        new_settings["viloxterm"] = old_settings["terminal"]

    if "editor" in old_settings:
        new_settings["viloedit"] = old_settings["editor"]

    # Core settings remain the same
    for key in ["theme", "window", "workspace"]:
        if key in old_settings:
            new_settings[key] = old_settings[key]

    return new_settings


def migrate_themes():
    """Migrate custom themes."""
    import platformdirs

    old_themes_dir = Path.home() / ".config" / "ViloxTerm" / "themes"
    new_themes_dir = Path(platformdirs.user_data_dir("ViloxTerm")) / "themes"

    if old_themes_dir.exists():
        logger.info(f"Migrating themes from {old_themes_dir} to {new_themes_dir}")

        new_themes_dir.mkdir(parents=True, exist_ok=True)

        for theme_file in old_themes_dir.glob("*.json"):
            shutil.copy2(theme_file, new_themes_dir / theme_file.name)
            logger.info(f"Migrated theme: {theme_file.name}")


def create_plugin_config():
    """Create initial plugin configuration."""
    import platformdirs

    config_dir = Path(platformdirs.user_config_dir("ViloxTerm"))
    plugin_config = config_dir / "plugins.json"

    if not plugin_config.exists():
        default_config = {
            "enabled": [
                "core-command-palette",
                "core-themes",
                "core-settings",
                "viloxterm",
                "viloedit"
            ],
            "disabled": [],
            "config": {
                "viloxterm": {
                    "autoStart": True
                },
                "viloedit": {
                    "autoSave": False
                }
            }
        }

        with open(plugin_config, 'w') as f:
            json.dump(default_config, f, indent=2)

        logger.info("Created default plugin configuration")


def main():
    """Run migration."""
    logger.info("Starting ViloxTerm migration to plugin architecture")

    migrate_settings()
    migrate_themes()
    create_plugin_config()

    logger.info("Migration complete!")
    logger.info("Please restart ViloxTerm to use the new plugin-based version")


if __name__ == "__main__":
    main()
```

### Afternoon (2 hours)

#### Task 3.2: Create Compatibility Layer

Create `/home/kuja/GitHub/viloapp/core/compat.py`:
```python
"""Compatibility layer for legacy code."""

import logging

logger = logging.getLogger(__name__)


class CompatibilityLayer:
    """Provides backward compatibility for legacy code."""

    @staticmethod
    def get_terminal_widget():
        """Get terminal widget (legacy compatibility)."""
        from core.commands.executor import execute_command

        result = execute_command("terminal.new")
        if result.success:
            return result.value.get('widget')
        return None

    @staticmethod
    def open_editor(file_path):
        """Open file in editor (legacy compatibility)."""
        from core.commands.executor import execute_command

        return execute_command("editor.open", path=file_path)

    @staticmethod
    def get_theme_service():
        """Get theme service (legacy compatibility)."""
        # Return adapter that uses plugin system
        return ThemeServiceAdapter()


class ThemeServiceAdapter:
    """Adapter for legacy theme service usage."""

    def apply_theme(self, theme_id):
        from core.commands.executor import execute_command
        execute_command("theme.selectTheme", theme_id=theme_id)

    def get_current_theme(self):
        from core.commands.executor import execute_command
        result = execute_command("theme.getCurrentTheme")
        return result.value if result.success else None
```

### Validation Checkpoint
- [ ] Migration scripts working
- [ ] Settings migrated correctly
- [ ] Themes migrated
- [ ] Compatibility layer functional

## Day 4: Testing and Debugging

### Morning (3 hours)

#### Task 4.1: Integration Testing

Create `/home/kuja/GitHub/viloapp/tests/integration/test_plugin_system_integration.py`:
```python
"""Integration tests for complete plugin system."""

import pytest
from unittest.mock import Mock, patch

def test_application_startup_with_plugins():
    """Test that application starts with plugins."""
    # Test application initialization
    # Test plugin loading
    # Test UI creation
    pass

def test_plugin_command_execution():
    """Test command execution through plugins."""
    # Test terminal commands
    # Test editor commands
    # Test core commands
    pass

def test_plugin_widget_creation():
    """Test widget creation from plugins."""
    # Test terminal widget
    # Test editor widget
    # Test settings widget
    pass

def test_plugin_communication():
    """Test inter-plugin communication."""
    # Test event passing
    # Test service access
    pass
```

### Afternoon (2 hours)

#### Task 4.2: Performance Optimization

- Profile plugin loading time
- Optimize startup sequence
- Lazy load plugins when possible
- Cache plugin metadata

### Validation Checkpoint
- [ ] All integration tests pass
- [ ] Performance acceptable
- [ ] No memory leaks
- [ ] Startup time reasonable

## Day 5: Documentation and Release Preparation

### Morning (3 hours)

#### Task 5.1: Update Documentation

Create `/home/kuja/GitHub/viloapp/docs/PLUGIN_SYSTEM.md`:
```markdown
# ViloxTerm Plugin System

## Overview

ViloxTerm now uses a plugin-based architecture for extensibility.

## Core Concepts

### Plugins
- Self-contained modules
- Loaded dynamically
- Can contribute widgets, commands, themes

### Plugin Types
1. **Core Plugins** - Built-in functionality
2. **Official Plugins** - Terminal, Editor
3. **Community Plugins** - User-created

## For Users

### Installing Plugins

```bash
# From PyPI
pip install viloxterm-plugin-name

# From source
cd plugin-directory
pip install -e .
```

### Managing Plugins

- Open Plugin Manager: `Plugins > Manage Plugins`
- Enable/disable plugins
- Configure plugin settings

## For Developers

### Creating a Plugin

1. Install SDK:
```bash
pip install viloapp-sdk
```

2. Create plugin:
```python
from viloapp_sdk import IPlugin, PluginMetadata

class MyPlugin(IPlugin):
    def get_metadata(self):
        return PluginMetadata(...)

    def activate(self, context):
        # Plugin logic
```

3. Register plugin:
```toml
[project.entry-points."viloapp.plugins"]
my-plugin = "my_plugin:MyPlugin"
```

## Migration from Legacy

Run migration script:
```bash
python scripts/migrate_to_plugins.py
```

This will:
- Migrate settings
- Migrate themes
- Create plugin configuration
```

### Afternoon (2 hours)

#### Task 5.2: Create Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] Migration guide complete
- [ ] Performance benchmarked
- [ ] Changelog updated
- [ ] Version bumped
- [ ] Release notes written

### Final Validation
- [ ] Complete system working
- [ ] All plugins integrated
- [ ] Migration successful
- [ ] Documentation complete

## Week 5 Summary

### Completed Deliverables
1. ✅ Main application refactored for plugins
2. ✅ Core plugins created
3. ✅ Migration tools implemented
4. ✅ Compatibility layer added
5. ✅ Full integration testing
6. ✅ Performance optimization
7. ✅ Documentation updated

### Key Achievements
- Complete plugin-based architecture
- Backward compatibility maintained
- Smooth migration path
- Core functionality as plugins
- Extensible system ready

### Ready for Week 6
System integration complete. Ready for:
- Advanced features
- Plugin marketplace
- Development tools