"""Plugin registry for managing plugin metadata and state."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

from viloapp_sdk import LifecycleState, PluginMetadata

logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    """Complete plugin information."""

    metadata: PluginMetadata
    path: Path
    state: LifecycleState = LifecycleState.DISCOVERED
    instance: Optional[object] = None
    context: Optional[object] = None
    error: Optional[str] = None
    dependencies_met: bool = False
    load_order: int = 0


class PluginRegistry:
    """Registry for all discovered and loaded plugins."""

    def __init__(self):
        self._plugins: Dict[str, PluginInfo] = {}
        self._state_index: Dict[LifecycleState, Set[str]] = {}
        self._capability_index: Dict[str, Set[str]] = {}

    def register(self, plugin_info: PluginInfo) -> bool:
        """
        Register a plugin.

        Args:
            plugin_info: Plugin information

        Returns:
            True if registered successfully
        """
        plugin_id = plugin_info.metadata.id

        if plugin_id in self._plugins:
            logger.warning(f"Plugin {plugin_id} already registered")
            return False

        # Add to main registry
        self._plugins[plugin_id] = plugin_info

        # Update indices
        self._update_state_index(plugin_id, plugin_info.state)
        self._update_capability_index(plugin_id, plugin_info.metadata)

        logger.info(f"Registered plugin: {plugin_id}")
        return True

    def unregister(self, plugin_id: str) -> bool:
        """
        Unregister a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if unregistered successfully
        """
        if plugin_id not in self._plugins:
            return False

        plugin_info = self._plugins[plugin_id]

        # Remove from indices
        self._remove_from_state_index(plugin_id, plugin_info.state)
        self._remove_from_capability_index(plugin_id, plugin_info.metadata)

        # Remove from registry
        del self._plugins[plugin_id]

        logger.info(f"Unregistered plugin: {plugin_id}")
        return True

    def get_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """Get plugin information by ID."""
        return self._plugins.get(plugin_id)

    def get_all_plugins(self) -> List[PluginInfo]:
        """Get all registered plugins."""
        return list(self._plugins.values())

    def get_plugins_by_state(self, state: LifecycleState) -> List[PluginInfo]:
        """Get plugins in a specific state."""
        plugin_ids = self._state_index.get(state, set())
        return [self._plugins[pid] for pid in plugin_ids]

    def get_plugins_by_capability(self, capability: str) -> List[PluginInfo]:
        """Get plugins with a specific capability."""
        plugin_ids = self._capability_index.get(capability, set())
        return [self._plugins[pid] for pid in plugin_ids]

    def update_state(self, plugin_id: str, new_state: LifecycleState) -> bool:
        """
        Update plugin state.

        Args:
            plugin_id: Plugin identifier
            new_state: New lifecycle state

        Returns:
            True if updated successfully
        """
        if plugin_id not in self._plugins:
            return False

        plugin_info = self._plugins[plugin_id]
        old_state = plugin_info.state

        # Update indices
        self._remove_from_state_index(plugin_id, old_state)
        self._update_state_index(plugin_id, new_state)

        # Update plugin info
        plugin_info.state = new_state

        logger.debug(f"Plugin {plugin_id} state: {old_state} -> {new_state}")
        return True

    def set_instance(self, plugin_id: str, instance: object) -> bool:
        """Set plugin instance."""
        if plugin_id not in self._plugins:
            return False

        self._plugins[plugin_id].instance = instance
        return True

    def set_context(self, plugin_id: str, context: object) -> bool:
        """Set plugin context."""
        if plugin_id not in self._plugins:
            return False

        self._plugins[plugin_id].context = context
        return True

    def set_error(self, plugin_id: str, error: str) -> bool:
        """Set plugin error message."""
        if plugin_id not in self._plugins:
            return False

        self._plugins[plugin_id].error = error
        self.update_state(plugin_id, LifecycleState.FAILED)
        return True

    def clear_error(self, plugin_id: str) -> bool:
        """Clear plugin error message."""
        if plugin_id not in self._plugins:
            return False

        self._plugins[plugin_id].error = None
        return True

    def _update_state_index(self, plugin_id: str, state: LifecycleState):
        """Update state index."""
        if state not in self._state_index:
            self._state_index[state] = set()
        self._state_index[state].add(plugin_id)

    def _remove_from_state_index(self, plugin_id: str, state: LifecycleState):
        """Remove from state index."""
        if state in self._state_index:
            self._state_index[state].discard(plugin_id)

    def _update_capability_index(self, plugin_id: str, metadata: PluginMetadata):
        """Update capability index."""
        for capability in metadata.capabilities:
            if capability.value not in self._capability_index:
                self._capability_index[capability.value] = set()
            self._capability_index[capability.value].add(plugin_id)

    def _remove_from_capability_index(self, plugin_id: str, metadata: PluginMetadata):
        """Remove from capability index."""
        for capability in metadata.capabilities:
            if capability.value in self._capability_index:
                self._capability_index[capability.value].discard(plugin_id)

    def save_state(self, path: Path) -> bool:
        """
        Save registry state to file.

        Args:
            path: Path to save file

        Returns:
            True if saved successfully
        """
        try:
            state_data = {
                "plugins": {
                    pid: {
                        "path": str(info.path),
                        "state": info.state.name,
                        "error": info.error,
                        "load_order": info.load_order,
                    }
                    for pid, info in self._plugins.items()
                }
            }

            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                json.dump(state_data, f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Failed to save registry state: {e}")
            return False

    def load_state(self, path: Path) -> bool:
        """
        Load registry state from file.

        Args:
            path: Path to save file

        Returns:
            True if loaded successfully
        """
        try:
            if not path.exists():
                return False

            with open(path) as f:
                state_data = json.load(f)

            # Note: This only loads metadata, not actual plugin instances
            # Actual loading happens through PluginLoader
            return True
        except Exception as e:
            logger.error(f"Failed to load registry state: {e}")
            return False
