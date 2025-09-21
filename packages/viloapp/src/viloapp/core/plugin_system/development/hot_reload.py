"""Hot reload system for plugin development."""

import sys
import time
from pathlib import Path
from typing import Dict, Set, Optional, Callable, Any

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from ..plugin_manager import PluginManager
from ..plugin_loader import PluginInfo


class PluginReloadHandler(FileSystemEventHandler):
    """File system event handler for plugin hot reload."""

    def __init__(
        self,
        plugin_path: Path,
        reload_callback: Callable[[Path], None],
        debounce_delay: float = 1.0
    ) -> None:
        """Initialize the handler.

        Args:
            plugin_path: Path to the plugin directory
            reload_callback: Callback function for reload
            debounce_delay: Delay in seconds to debounce rapid changes
        """
        super().__init__()
        self.plugin_path = plugin_path
        self.reload_callback = reload_callback
        self.debounce_delay = debounce_delay
        self.last_reload_time = 0
        self.pending_reload = False

    def on_modified(self, event) -> None:
        """Handle file modification events.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only watch relevant files
        if not self._should_watch_file(file_path):
            return

        # Debounce rapid file changes
        current_time = time.time()
        if current_time - self.last_reload_time < self.debounce_delay:
            self.pending_reload = True
            return

        self._trigger_reload(file_path)

    def on_created(self, event) -> None:
        """Handle file creation events."""
        self.on_modified(event)

    def on_deleted(self, event) -> None:
        """Handle file deletion events."""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if self._should_watch_file(file_path):
                self._trigger_reload(file_path)

    def _should_watch_file(self, file_path: Path) -> bool:
        """Check if file should trigger reload.

        Args:
            file_path: Path to the file

        Returns:
            True if file should be watched
        """
        # Watch Python files, config files, and manifests
        watch_extensions = {".py", ".json", ".yaml", ".yml"}

        # Skip temporary files and cache directories
        skip_patterns = {
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "htmlcov",
            ".coverage",
            ".git",
        }

        # Check if file is in a skip directory
        for part in file_path.parts:
            if part in skip_patterns:
                return False

        # Check if file has watched extension
        return file_path.suffix in watch_extensions

    def _trigger_reload(self, file_path: Path) -> None:
        """Trigger plugin reload.

        Args:
            file_path: Path to the changed file
        """
        self.last_reload_time = time.time()
        self.pending_reload = False

        try:
            relative_path = file_path.relative_to(self.plugin_path)
            print(f"🔄 File changed: {relative_path}")
            self.reload_callback(file_path)
        except Exception as e:
            print(f"❌ Reload failed: {e}")

    def check_pending_reload(self) -> None:
        """Check and execute pending reload if debounce time has passed."""
        if self.pending_reload:
            current_time = time.time()
            if current_time - self.last_reload_time >= self.debounce_delay:
                self._trigger_reload(self.plugin_path)


class HotReloadManager:
    """Manager for hot reloading plugins during development."""

    def __init__(self, plugin_manager: PluginManager) -> None:
        """Initialize the hot reload manager.

        Args:
            plugin_manager: Plugin manager instance
        """
        self.plugin_manager = plugin_manager
        self.observers: Dict[str, Observer] = {}
        self.handlers: Dict[str, PluginReloadHandler] = {}
        self.watched_plugins: Dict[str, PluginInfo] = {}
        self.development_mode = False

    def enable_development_mode(self) -> None:
        """Enable development mode."""
        self.development_mode = True

    def disable_development_mode(self) -> None:
        """Disable development mode and stop all watching."""
        self.development_mode = False
        self.stop_watching_all()

    def start_watching_plugin(self, plugin_id: str) -> bool:
        """Start watching a plugin for changes.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if watching started successfully
        """
        if not self.development_mode:
            return False

        if plugin_id in self.observers:
            # Already watching
            return True

        # Get plugin info
        plugin_info = self.plugin_manager.get_plugin_info(plugin_id)
        if not plugin_info:
            print(f"❌ Plugin not found: {plugin_id}")
            return False

        # Determine plugin path
        plugin_path = self._get_plugin_path(plugin_info)
        if not plugin_path or not plugin_path.exists():
            print(f"❌ Plugin path not found: {plugin_path}")
            return False

        try:
            # Create reload handler
            handler = PluginReloadHandler(
                plugin_path,
                lambda file_path: self._reload_plugin(plugin_id, file_path)
            )

            # Create observer
            observer = Observer()
            observer.schedule(handler, str(plugin_path), recursive=True)
            observer.start()

            # Store references
            self.observers[plugin_id] = observer
            self.handlers[plugin_id] = handler
            self.watched_plugins[plugin_id] = plugin_info

            print(f"👀 Watching plugin for changes: {plugin_id} at {plugin_path}")
            return True

        except Exception as e:
            print(f"❌ Failed to start watching plugin {plugin_id}: {e}")
            return False

    def stop_watching_plugin(self, plugin_id: str) -> bool:
        """Stop watching a plugin for changes.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if watching stopped successfully
        """
        if plugin_id not in self.observers:
            return False

        try:
            observer = self.observers[plugin_id]
            observer.stop()
            observer.join()

            # Clean up references
            del self.observers[plugin_id]
            del self.handlers[plugin_id]
            if plugin_id in self.watched_plugins:
                del self.watched_plugins[plugin_id]

            print(f"🛑 Stopped watching plugin: {plugin_id}")
            return True

        except Exception as e:
            print(f"❌ Failed to stop watching plugin {plugin_id}: {e}")
            return False

    def stop_watching_all(self) -> None:
        """Stop watching all plugins."""
        plugin_ids = list(self.observers.keys())
        for plugin_id in plugin_ids:
            self.stop_watching_plugin(plugin_id)

    def _get_plugin_path(self, plugin_info: PluginInfo) -> Optional[Path]:
        """Get the file system path for a plugin.

        Args:
            plugin_info: Plugin information

        Returns:
            Plugin path or None if not found
        """
        # For now, try to determine path from the plugin module
        if hasattr(plugin_info, 'module') and plugin_info.module:
            module = plugin_info.module
            if hasattr(module, '__file__') and module.__file__:
                module_path = Path(module.__file__)
                # Go up to find the plugin root directory
                for parent in module_path.parents:
                    if (parent / "plugin.json").exists():
                        return parent
                # If no plugin.json found, use the module's directory
                return module_path.parent

        # Fallback: try to find by plugin ID in common locations
        possible_paths = [
            Path.cwd(),
            Path.home() / ".viloapp" / "plugins",
        ]

        for base_path in possible_paths:
            if base_path.exists():
                for plugin_dir in base_path.iterdir():
                    if plugin_dir.is_dir() and (plugin_dir / "plugin.json").exists():
                        try:
                            import json
                            with open(plugin_dir / "plugin.json") as f:
                                manifest = json.load(f)
                            if manifest.get("id") == plugin_info.plugin_id:
                                return plugin_dir
                        except Exception:
                            continue

        return None

    def _reload_plugin(self, plugin_id: str, changed_file: Path) -> None:
        """Reload a plugin.

        Args:
            plugin_id: Plugin identifier
            changed_file: Path to the changed file
        """
        try:
            print(f"📦 Reloading plugin: {plugin_id}")

            # Get current plugin state
            plugin_info = self.watched_plugins.get(plugin_id)
            if not plugin_info:
                print(f"❌ Plugin info not found for reload: {plugin_id}")
                return

            # Preserve state if possible
            plugin_state = self._preserve_plugin_state(plugin_id)

            # Unload the plugin
            if self.plugin_manager.is_plugin_loaded(plugin_id):
                self.plugin_manager.unload_plugin(plugin_id)

            # Clear module cache for this plugin
            self._clear_plugin_modules(plugin_info)

            # Reload the plugin
            result = self.plugin_manager.load_plugin(plugin_info.manifest_path)
            if result:
                print(f"✅ Plugin reloaded successfully: {plugin_id}")

                # Restore state if possible
                self._restore_plugin_state(plugin_id, plugin_state)
            else:
                print(f"❌ Failed to reload plugin: {plugin_id}")

        except Exception as e:
            print(f"❌ Error reloading plugin {plugin_id}: {e}")

    def _preserve_plugin_state(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Preserve plugin state before reload.

        Args:
            plugin_id: Plugin identifier

        Returns:
            Plugin state or None
        """
        try:
            plugin = self.plugin_manager.get_plugin(plugin_id)
            if plugin and hasattr(plugin, 'get_state'):
                return plugin.get_state()
        except Exception as e:
            print(f"⚠️  Could not preserve state for {plugin_id}: {e}")
        return None

    def _restore_plugin_state(self, plugin_id: str, state: Optional[Dict[str, Any]]) -> None:
        """Restore plugin state after reload.

        Args:
            plugin_id: Plugin identifier
            state: Plugin state to restore
        """
        if not state:
            return

        try:
            plugin = self.plugin_manager.get_plugin(plugin_id)
            if plugin and hasattr(plugin, 'restore_state'):
                plugin.restore_state(state)
        except Exception as e:
            print(f"⚠️  Could not restore state for {plugin_id}: {e}")

    def _clear_plugin_modules(self, plugin_info: PluginInfo) -> None:
        """Clear plugin modules from sys.modules.

        Args:
            plugin_info: Plugin information
        """
        try:
            if hasattr(plugin_info, 'module') and plugin_info.module:
                module_name = plugin_info.module.__name__

                # Find all modules that belong to this plugin
                modules_to_remove = []
                for name in sys.modules:
                    if name.startswith(module_name):
                        modules_to_remove.append(name)

                # Remove modules
                for name in modules_to_remove:
                    del sys.modules[name]

        except Exception as e:
            print(f"⚠️  Could not clear modules for plugin: {e}")

    def get_watched_plugins(self) -> Set[str]:
        """Get set of currently watched plugin IDs.

        Returns:
            Set of plugin IDs being watched
        """
        return set(self.observers.keys())

    def is_watching_plugin(self, plugin_id: str) -> bool:
        """Check if a plugin is being watched.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if plugin is being watched
        """
        return plugin_id in self.observers