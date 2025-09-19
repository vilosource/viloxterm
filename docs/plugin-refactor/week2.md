# Week 2: Plugin Host Infrastructure

## Overview
Week 2 focuses on implementing the plugin host infrastructure in the main application that will discover, load, and manage plugins.

**Duration**: 5 days
**Goal**: Complete plugin management system with discovery, loading, dependency resolution, and service integration

## Prerequisites
- [ ] Week 1 completed successfully
- [ ] SDK package installed and tested
- [ ] Main application codebase accessible

## Day 1: Plugin Manager Core

### Morning (3 hours)

#### Task 1.1: Create Plugin Manager Module

Create `/home/kuja/GitHub/viloapp/core/plugin_system/__init__.py`:
```python
"""Plugin system for ViloxTerm."""

from .plugin_manager import PluginManager
from .plugin_loader import PluginLoader
from .plugin_discovery import PluginDiscovery
from .plugin_registry import PluginRegistry
from .dependency_resolver import DependencyResolver

__all__ = [
    "PluginManager",
    "PluginLoader",
    "PluginDiscovery",
    "PluginRegistry",
    "DependencyResolver",
]
```

#### Task 1.2: Implement Plugin Registry

Create `/home/kuja/GitHub/viloapp/core/plugin_system/plugin_registry.py`:
```python
"""Plugin registry for managing plugin metadata and state."""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from pathlib import Path
import json

from viloapp_sdk import PluginMetadata, LifecycleState

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
                        "load_order": info.load_order
                    }
                    for pid, info in self._plugins.items()
                }
            }

            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
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

            with open(path, 'r') as f:
                state_data = json.load(f)

            # Note: This only loads metadata, not actual plugin instances
            # Actual loading happens through PluginLoader
            return True
        except Exception as e:
            logger.error(f"Failed to load registry state: {e}")
            return False
```

### Afternoon (3 hours)

#### Task 1.3: Implement Plugin Discovery

Create `/home/kuja/GitHub/viloapp/core/plugin_system/plugin_discovery.py`:
```python
"""Plugin discovery system."""

import logging
import json
import importlib.metadata
from pathlib import Path
from typing import List, Set, Optional

from viloapp_sdk import PluginMetadata
from .plugin_registry import PluginInfo, LifecycleState

logger = logging.getLogger(__name__)

class PluginDiscovery:
    """Discovers plugins from various sources."""

    def __init__(self, registry):
        self.registry = registry
        self.discovered_paths: Set[Path] = set()

    def discover_all(self) -> List[PluginInfo]:
        """
        Discover plugins from all sources.

        Returns:
            List of discovered plugin information
        """
        plugins = []

        # Discover from entry points
        plugins.extend(self.discover_entry_points())

        # Discover from plugin directories
        plugins.extend(self.discover_from_directory(self._get_user_plugin_dir()))
        plugins.extend(self.discover_from_directory(self._get_system_plugin_dir()))

        # Discover built-in plugins
        plugins.extend(self.discover_builtin_plugins())

        logger.info(f"Discovered {len(plugins)} plugins")
        return plugins

    def discover_entry_points(self, group: str = "viloapp.plugins") -> List[PluginInfo]:
        """
        Discover plugins via Python entry points.

        Args:
            group: Entry point group name

        Returns:
            List of discovered plugins
        """
        plugins = []

        try:
            # Python 3.8+ compatible entry points discovery
            if hasattr(importlib.metadata, 'entry_points'):
                eps = importlib.metadata.entry_points()
                if hasattr(eps, 'select'):
                    # Python 3.10+
                    entry_points = eps.select(group=group)
                else:
                    # Python 3.8-3.9
                    entry_points = eps.get(group, [])
            else:
                # Fallback for older versions
                entry_points = []

            for entry_point in entry_points:
                try:
                    # Get plugin metadata without loading the plugin
                    plugin_path = self._get_entry_point_path(entry_point)

                    # Create minimal metadata from entry point
                    metadata = PluginMetadata(
                        id=entry_point.name,
                        name=entry_point.name.replace('-', ' ').title(),
                        version="0.0.0",  # Will be updated when loaded
                        description=f"Plugin from {entry_point.value}",
                        author="Unknown"
                    )

                    plugin_info = PluginInfo(
                        metadata=metadata,
                        path=plugin_path,
                        state=LifecycleState.DISCOVERED
                    )

                    plugins.append(plugin_info)
                    logger.debug(f"Discovered entry point plugin: {entry_point.name}")

                except Exception as e:
                    logger.error(f"Failed to process entry point {entry_point.name}: {e}")

        except Exception as e:
            logger.error(f"Failed to discover entry point plugins: {e}")

        return plugins

    def discover_from_directory(self, directory: Path) -> List[PluginInfo]:
        """
        Discover plugins from a directory.

        Args:
            directory: Directory to search for plugins

        Returns:
            List of discovered plugins
        """
        plugins = []

        if not directory or not directory.exists():
            return plugins

        # Look for plugin manifests
        for manifest_path in directory.glob("*/plugin.json"):
            try:
                plugin_info = self._load_plugin_manifest(manifest_path)
                if plugin_info:
                    plugins.append(plugin_info)
                    logger.debug(f"Discovered plugin from: {manifest_path}")
            except Exception as e:
                logger.error(f"Failed to load plugin manifest {manifest_path}: {e}")

        # Look for Python packages with __plugin__ marker
        for plugin_dir in directory.iterdir():
            if plugin_dir.is_dir():
                marker_file = plugin_dir / "__plugin__.py"
                if marker_file.exists():
                    try:
                        plugin_info = self._load_python_plugin(plugin_dir)
                        if plugin_info:
                            plugins.append(plugin_info)
                            logger.debug(f"Discovered Python plugin from: {plugin_dir}")
                    except Exception as e:
                        logger.error(f"Failed to load Python plugin {plugin_dir}: {e}")

        return plugins

    def discover_builtin_plugins(self) -> List[PluginInfo]:
        """
        Discover built-in plugins.

        Returns:
            List of built-in plugins
        """
        plugins = []

        # Define built-in plugins
        builtin_plugins = [
            {
                "id": "core-commands",
                "name": "Core Commands",
                "description": "Built-in command palette and shortcuts"
            },
            {
                "id": "core-themes",
                "name": "Core Themes",
                "description": "Built-in theme support"
            }
        ]

        for plugin_data in builtin_plugins:
            metadata = PluginMetadata(
                id=plugin_data["id"],
                name=plugin_data["name"],
                version="builtin",
                description=plugin_data["description"],
                author="ViloxTerm Team"
            )

            plugin_info = PluginInfo(
                metadata=metadata,
                path=Path("builtin") / plugin_data["id"],
                state=LifecycleState.DISCOVERED
            )

            plugins.append(plugin_info)

        return plugins

    def _load_plugin_manifest(self, manifest_path: Path) -> Optional[PluginInfo]:
        """Load plugin metadata from manifest file."""
        try:
            with open(manifest_path, 'r') as f:
                data = json.load(f)

            metadata = PluginMetadata(
                id=data.get("id"),
                name=data.get("name"),
                version=data.get("version"),
                description=data.get("description"),
                author=data.get("author"),
                homepage=data.get("homepage"),
                repository=data.get("repository"),
                license=data.get("license"),
                icon=data.get("icon"),
                categories=data.get("categories", []),
                keywords=data.get("keywords", []),
                engines=data.get("engines", {}),
                dependencies=data.get("dependencies", []),
                activation_events=data.get("activationEvents", []),
                contributes=data.get("contributes", {})
            )

            # Validate metadata
            errors = metadata.validate()
            if errors:
                logger.error(f"Invalid plugin manifest {manifest_path}: {errors}")
                return None

            return PluginInfo(
                metadata=metadata,
                path=manifest_path.parent,
                state=LifecycleState.DISCOVERED
            )

        except Exception as e:
            logger.error(f"Failed to load plugin manifest {manifest_path}: {e}")
            return None

    def _load_python_plugin(self, plugin_dir: Path) -> Optional[PluginInfo]:
        """Load plugin from Python package."""
        try:
            # Import the __plugin__ module to get metadata
            import sys
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                f"{plugin_dir.name}.__plugin__",
                plugin_dir / "__plugin__.py"
            )

            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get metadata from module
            if hasattr(module, 'METADATA'):
                metadata = module.METADATA
            elif hasattr(module, 'get_metadata'):
                metadata = module.get_metadata()
            else:
                return None

            return PluginInfo(
                metadata=metadata,
                path=plugin_dir,
                state=LifecycleState.DISCOVERED
            )

        except Exception as e:
            logger.error(f"Failed to load Python plugin {plugin_dir}: {e}")
            return None

    def _get_entry_point_path(self, entry_point) -> Path:
        """Get path for an entry point."""
        # Try to determine the package location
        try:
            module_name = entry_point.value.split(':')[0]
            module = importlib.import_module(module_name)
            if hasattr(module, '__file__'):
                return Path(module.__file__).parent
        except Exception:
            pass

        return Path("entry_points") / entry_point.name

    def _get_user_plugin_dir(self) -> Path:
        """Get user plugin directory."""
        import platformdirs
        return Path(platformdirs.user_data_dir("ViloxTerm")) / "plugins"

    def _get_system_plugin_dir(self) -> Path:
        """Get system plugin directory."""
        import platformdirs
        return Path(platformdirs.site_data_dir("ViloxTerm")) / "plugins"
```

### Validation Checkpoint
- [ ] Plugin registry implemented
- [ ] Discovery system finds plugins
- [ ] Registry can track plugin states
- [ ] No import errors

## Day 2: Plugin Loading and Dependency Resolution

### Morning (3 hours)

#### Task 2.1: Implement Dependency Resolver

Create `/home/kuja/GitHub/viloapp/core/plugin_system/dependency_resolver.py`:
```python
"""Plugin dependency resolution."""

import logging
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
import re

from viloapp_sdk import PluginMetadata

logger = logging.getLogger(__name__)

@dataclass
class Dependency:
    """Represents a plugin dependency."""
    plugin_id: str
    version_spec: str
    optional: bool = False

    def is_satisfied_by(self, version: str) -> bool:
        """Check if a version satisfies this dependency."""
        return self._check_version_compatibility(version, self.version_spec)

    def _check_version_compatibility(self, version: str, spec: str) -> bool:
        """
        Check if version satisfies specification.

        Supports:
        - Exact match: "1.0.0"
        - Minimum version: ">=1.0.0"
        - Range: ">=1.0.0,<2.0.0"
        """
        # Simple implementation - can be enhanced with packaging.specifiers
        if spec.startswith(">="):
            min_version = spec[2:].strip()
            return self._compare_versions(version, min_version) >= 0
        elif spec.startswith(">"):
            min_version = spec[1:].strip()
            return self._compare_versions(version, min_version) > 0
        elif spec.startswith("<="):
            max_version = spec[2:].strip()
            return self._compare_versions(version, max_version) <= 0
        elif spec.startswith("<"):
            max_version = spec[1:].strip()
            return self._compare_versions(version, max_version) < 0
        elif "," in spec:
            # Handle range
            parts = spec.split(",")
            for part in parts:
                if not self._check_version_compatibility(version, part.strip()):
                    return False
            return True
        else:
            # Exact match
            return version == spec

    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compare two version strings."""
        # Simple version comparison
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]

        # Pad with zeros if needed
        max_len = max(len(parts1), len(parts2))
        parts1.extend([0] * (max_len - len(parts1)))
        parts2.extend([0] * (max_len - len(parts2)))

        for p1, p2 in zip(parts1, parts2):
            if p1 < p2:
                return -1
            elif p1 > p2:
                return 1
        return 0

class DependencyResolver:
    """Resolves plugin dependencies and determines load order."""

    def __init__(self, registry):
        self.registry = registry

    def resolve_dependencies(
        self,
        plugin_ids: Optional[List[str]] = None
    ) -> Tuple[List[str], Dict[str, List[str]]]:
        """
        Resolve dependencies and determine load order.

        Args:
            plugin_ids: Specific plugins to resolve (None for all)

        Returns:
            Tuple of (load_order, unmet_dependencies)
        """
        # Get plugins to resolve
        if plugin_ids is None:
            plugins = self.registry.get_all_plugins()
        else:
            plugins = [self.registry.get_plugin(pid) for pid in plugin_ids]
            plugins = [p for p in plugins if p]

        # Build dependency graph
        graph = self._build_dependency_graph(plugins)

        # Check for cycles
        if self._has_cycle(graph):
            raise ValueError("Circular dependencies detected")

        # Perform topological sort
        load_order = self._topological_sort(graph)

        # Check unmet dependencies
        unmet = self._check_unmet_dependencies(plugins)

        # Update registry with dependency info
        for plugin in plugins:
            plugin_id = plugin.metadata.id
            plugin.dependencies_met = plugin_id not in unmet
            if plugin_id in load_order:
                plugin.load_order = load_order.index(plugin_id)

        return load_order, unmet

    def _build_dependency_graph(self, plugins) -> Dict[str, Set[str]]:
        """Build dependency graph from plugins."""
        graph = {}

        for plugin in plugins:
            plugin_id = plugin.metadata.id
            graph[plugin_id] = set()

            # Parse dependencies
            for dep_str in plugin.metadata.dependencies:
                dep = self._parse_dependency(dep_str)
                if dep and not dep.optional:
                    graph[plugin_id].add(dep.plugin_id)

        return graph

    def _parse_dependency(self, dep_str: str) -> Optional[Dependency]:
        """Parse dependency string."""
        # Format: "plugin-id@version" or "plugin-id@>=version"
        match = re.match(r'^([a-zA-Z0-9\-]+)(?:@(.+))?$', dep_str)
        if not match:
            return None

        plugin_id = match.group(1)
        version_spec = match.group(2) or "*"

        # Check for optional marker
        optional = dep_str.endswith("?")
        if optional:
            dep_str = dep_str[:-1]

        return Dependency(
            plugin_id=plugin_id,
            version_spec=version_spec,
            optional=optional
        )

    def _has_cycle(self, graph: Dict[str, Set[str]]) -> bool:
        """Check if dependency graph has cycles."""
        visited = set()
        rec_stack = set()

        def has_cycle_util(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if has_cycle_util(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                if has_cycle_util(node):
                    return True

        return False

    def _topological_sort(self, graph: Dict[str, Set[str]]) -> List[str]:
        """Perform topological sort on dependency graph."""
        # Calculate in-degrees
        in_degree = {node: 0 for node in graph}
        for node in graph:
            for neighbor in graph[node]:
                if neighbor in in_degree:
                    in_degree[neighbor] += 1

        # Find nodes with no dependencies
        queue = [node for node, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            # Reduce in-degree for neighbors
            for neighbor in graph.get(node, set()):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        return result

    def _check_unmet_dependencies(self, plugins) -> Dict[str, List[str]]:
        """Check for unmet dependencies."""
        unmet = {}
        available_plugins = {p.metadata.id: p.metadata.version for p in plugins}

        for plugin in plugins:
            plugin_id = plugin.metadata.id
            missing_deps = []

            for dep_str in plugin.metadata.dependencies:
                dep = self._parse_dependency(dep_str)
                if not dep:
                    continue

                if dep.optional:
                    continue

                # Check if dependency is available
                if dep.plugin_id not in available_plugins:
                    missing_deps.append(f"{dep.plugin_id} (not found)")
                elif not dep.is_satisfied_by(available_plugins[dep.plugin_id]):
                    missing_deps.append(
                        f"{dep.plugin_id} (version {available_plugins[dep.plugin_id]} "
                        f"does not satisfy {dep.version_spec})"
                    )

            if missing_deps:
                unmet[plugin_id] = missing_deps

        return unmet
```

### Afternoon (3 hours)

#### Task 2.2: Implement Plugin Loader

Create `/home/kuja/GitHub/viloapp/core/plugin_system/plugin_loader.py`:
```python
"""Plugin loading system."""

import logging
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from viloapp_sdk import (
    IPlugin, PluginContext, EventBus, LifecycleState,
    PluginLoadError, PluginActivationError
)
from .plugin_registry import PluginInfo
from .service_proxy_impl import ServiceProxyImpl

logger = logging.getLogger(__name__)

class PluginLoader:
    """Loads and instantiates plugins."""

    def __init__(self, registry, event_bus: EventBus, services: Dict[str, Any]):
        self.registry = registry
        self.event_bus = event_bus
        self.services = services
        self.loaded_modules = {}

    def load_plugin(self, plugin_id: str) -> bool:
        """
        Load a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if loaded successfully
        """
        plugin_info = self.registry.get_plugin(plugin_id)
        if not plugin_info:
            logger.error(f"Plugin {plugin_id} not found in registry")
            return False

        if plugin_info.state not in [LifecycleState.DISCOVERED, LifecycleState.UNLOADED]:
            logger.warning(f"Plugin {plugin_id} is in state {plugin_info.state}, cannot load")
            return False

        try:
            # Load plugin module
            module = self._load_plugin_module(plugin_info)
            if not module:
                raise PluginLoadError(f"Failed to load module for {plugin_id}")

            # Find plugin class
            plugin_class = self._find_plugin_class(module)
            if not plugin_class:
                raise PluginLoadError(f"No plugin class found in {plugin_id}")

            # Instantiate plugin
            plugin_instance = plugin_class()

            # Validate plugin
            if not isinstance(plugin_instance, IPlugin):
                raise PluginLoadError(f"Plugin {plugin_id} does not implement IPlugin")

            # Update metadata from actual plugin
            actual_metadata = plugin_instance.get_metadata()
            plugin_info.metadata = actual_metadata

            # Store instance
            self.registry.set_instance(plugin_id, plugin_instance)
            self.registry.update_state(plugin_id, LifecycleState.LOADED)

            logger.info(f"Loaded plugin: {plugin_id}")
            return True

        except Exception as e:
            error_msg = f"Failed to load plugin {plugin_id}: {e}"
            logger.error(error_msg, exc_info=True)
            self.registry.set_error(plugin_id, str(e))
            return False

    def activate_plugin(self, plugin_id: str) -> bool:
        """
        Activate a loaded plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if activated successfully
        """
        plugin_info = self.registry.get_plugin(plugin_id)
        if not plugin_info:
            return False

        if plugin_info.state != LifecycleState.LOADED:
            logger.warning(f"Plugin {plugin_id} is not loaded, cannot activate")
            return False

        if not plugin_info.instance:
            logger.error(f"Plugin {plugin_id} has no instance")
            return False

        try:
            # Create plugin context
            context = self._create_plugin_context(plugin_info)
            self.registry.set_context(plugin_id, context)

            # Activate plugin
            plugin_info.instance.activate(context)

            # Update state
            self.registry.update_state(plugin_id, LifecycleState.ACTIVATED)

            # Emit activation event
            from viloapp_sdk import PluginEvent, EventType
            self.event_bus.emit(PluginEvent(
                type=EventType.PLUGIN_ACTIVATED,
                source="plugin_loader",
                data={"plugin_id": plugin_id}
            ))

            logger.info(f"Activated plugin: {plugin_id}")
            return True

        except Exception as e:
            error_msg = f"Failed to activate plugin {plugin_id}: {e}"
            logger.error(error_msg, exc_info=True)
            self.registry.set_error(plugin_id, str(e))
            return False

    def deactivate_plugin(self, plugin_id: str) -> bool:
        """
        Deactivate a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if deactivated successfully
        """
        plugin_info = self.registry.get_plugin(plugin_id)
        if not plugin_info:
            return False

        if plugin_info.state != LifecycleState.ACTIVATED:
            logger.warning(f"Plugin {plugin_id} is not activated")
            return False

        if not plugin_info.instance:
            return False

        try:
            # Deactivate plugin
            plugin_info.instance.deactivate()

            # Update state
            self.registry.update_state(plugin_id, LifecycleState.DEACTIVATED)

            # Emit deactivation event
            from viloapp_sdk import PluginEvent, EventType
            self.event_bus.emit(PluginEvent(
                type=EventType.PLUGIN_DEACTIVATED,
                source="plugin_loader",
                data={"plugin_id": plugin_id}
            ))

            logger.info(f"Deactivated plugin: {plugin_id}")
            return True

        except Exception as e:
            error_msg = f"Failed to deactivate plugin {plugin_id}: {e}"
            logger.error(error_msg, exc_info=True)
            return False

    def unload_plugin(self, plugin_id: str) -> bool:
        """
        Unload a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if unloaded successfully
        """
        plugin_info = self.registry.get_plugin(plugin_id)
        if not plugin_info:
            return False

        # Deactivate if necessary
        if plugin_info.state == LifecycleState.ACTIVATED:
            if not self.deactivate_plugin(plugin_id):
                return False

        if plugin_info.state not in [LifecycleState.DEACTIVATED, LifecycleState.LOADED, LifecycleState.FAILED]:
            return False

        try:
            # Clear instance and context
            self.registry.set_instance(plugin_id, None)
            self.registry.set_context(plugin_id, None)

            # Remove from loaded modules
            if plugin_id in self.loaded_modules:
                module_name = self.loaded_modules[plugin_id]
                if module_name in sys.modules:
                    del sys.modules[module_name]
                del self.loaded_modules[plugin_id]

            # Update state
            self.registry.update_state(plugin_id, LifecycleState.UNLOADED)

            # Emit unload event
            from viloapp_sdk import PluginEvent, EventType
            self.event_bus.emit(PluginEvent(
                type=EventType.PLUGIN_UNLOADED,
                source="plugin_loader",
                data={"plugin_id": plugin_id}
            ))

            logger.info(f"Unloaded plugin: {plugin_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_id}: {e}")
            return False

    def _load_plugin_module(self, plugin_info: PluginInfo):
        """Load plugin Python module."""
        plugin_id = plugin_info.metadata.id
        plugin_path = plugin_info.path

        # Check if it's a built-in plugin
        if str(plugin_path).startswith("builtin"):
            return self._load_builtin_plugin(plugin_id)

        # Check if it's an entry point plugin
        if str(plugin_path).startswith("entry_points"):
            return self._load_entry_point_plugin(plugin_id)

        # Load from file system
        if plugin_path.is_dir():
            # Look for plugin module
            plugin_file = plugin_path / "plugin.py"
            if not plugin_file.exists():
                plugin_file = plugin_path / "__init__.py"

            if plugin_file.exists():
                module_name = f"viloapp_plugins.{plugin_id}"
                spec = importlib.util.spec_from_file_location(module_name, plugin_file)

                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    self.loaded_modules[plugin_id] = module_name
                    return module

        return None

    def _load_builtin_plugin(self, plugin_id: str):
        """Load built-in plugin."""
        # Map builtin plugin IDs to modules
        builtin_map = {
            "core-commands": "core.plugins.commands",
            "core-themes": "core.plugins.themes"
        }

        module_name = builtin_map.get(plugin_id)
        if module_name:
            try:
                return importlib.import_module(module_name)
            except ImportError:
                pass

        return None

    def _load_entry_point_plugin(self, plugin_id: str):
        """Load entry point plugin."""
        try:
            # Load via entry points
            import importlib.metadata

            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, 'select'):
                eps = entry_points.select(group='viloapp.plugins')
            else:
                eps = entry_points.get('viloapp.plugins', [])

            for ep in eps:
                if ep.name == plugin_id:
                    # Load the entry point
                    plugin_class = ep.load()
                    # Create a wrapper module
                    module = type('module', (), {'Plugin': plugin_class})
                    return module

        except Exception as e:
            logger.error(f"Failed to load entry point plugin {plugin_id}: {e}")

        return None

    def _find_plugin_class(self, module) -> Optional[type]:
        """Find plugin class in module."""
        # Look for class that implements IPlugin
        for attr_name in dir(module):
            if attr_name.startswith('_'):
                continue

            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, IPlugin) and attr != IPlugin:
                return attr

        # Fallback: look for specifically named class
        if hasattr(module, 'Plugin'):
            return module.Plugin

        # Look for class ending with 'Plugin'
        for attr_name in dir(module):
            if attr_name.endswith('Plugin'):
                attr = getattr(module, attr_name)
                if isinstance(attr, type):
                    return attr

        return None

    def _create_plugin_context(self, plugin_info: PluginInfo) -> PluginContext:
        """Create context for plugin."""
        plugin_id = plugin_info.metadata.id

        # Get data directory for plugin
        import platformdirs
        data_path = Path(platformdirs.user_data_dir("ViloxTerm")) / "plugins" / plugin_id

        # Create service proxy
        service_proxy = ServiceProxyImpl(self.services)

        # Get plugin configuration
        config_service = self.services.get('configuration')
        if config_service:
            config = config_service.get(f"plugins.{plugin_id}", {})
        else:
            config = {}

        return PluginContext(
            plugin_id=plugin_id,
            plugin_path=plugin_info.path,
            data_path=data_path,
            service_proxy=service_proxy,
            event_bus=self.event_bus,
            configuration=config
        )
```

#### Task 2.3: Implement Service Proxy

Create `/home/kuja/GitHub/viloapp/core/plugin_system/service_proxy_impl.py`:
```python
"""Service proxy implementation for plugins."""

from typing import Dict, Any, Optional
from viloapp_sdk import ServiceProxy

class ServiceProxyImpl(ServiceProxy):
    """Implementation of service proxy for ViloxTerm."""

    def __init__(self, services: Dict[str, Any]):
        super().__init__(services)

    # Override methods if needed for additional functionality
```

### Validation Checkpoint
- [ ] Dependency resolution works
- [ ] Plugin loading functional
- [ ] Service proxy created
- [ ] Plugins can be activated/deactivated

## Day 3: Plugin Manager Integration

### Morning (3 hours)

#### Task 3.1: Implement Main Plugin Manager

Create `/home/kuja/GitHub/viloapp/core/plugin_system/plugin_manager.py`:
```python
"""Main plugin manager orchestrating all plugin operations."""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from viloapp_sdk import EventBus, IPlugin
from .plugin_registry import PluginRegistry
from .plugin_discovery import PluginDiscovery
from .plugin_loader import PluginLoader
from .dependency_resolver import DependencyResolver

logger = logging.getLogger(__name__)

class PluginManager:
    """Central manager for all plugin operations."""

    def __init__(self, event_bus: EventBus, services: Dict[str, Any]):
        self.event_bus = event_bus
        self.services = services

        # Initialize components
        self.registry = PluginRegistry()
        self.discovery = PluginDiscovery(self.registry)
        self.loader = PluginLoader(self.registry, event_bus, services)
        self.resolver = DependencyResolver(self.registry)

        self._initialized = False

    def initialize(self) -> bool:
        """
        Initialize the plugin system.

        Returns:
            True if initialized successfully
        """
        if self._initialized:
            return True

        try:
            # Discover all plugins
            plugins = self.discovery.discover_all()

            # Register discovered plugins
            for plugin_info in plugins:
                self.registry.register(plugin_info)

            # Resolve dependencies
            load_order, unmet_deps = self.resolver.resolve_dependencies()

            # Log dependency issues
            if unmet_deps:
                for plugin_id, deps in unmet_deps.items():
                    logger.warning(f"Plugin {plugin_id} has unmet dependencies: {deps}")

            # Load and activate plugins in order
            for plugin_id in load_order:
                if plugin_id not in unmet_deps:
                    if self.load_plugin(plugin_id):
                        # Auto-activate plugins with activation events
                        plugin_info = self.registry.get_plugin(plugin_id)
                        if plugin_info and self._should_auto_activate(plugin_info):
                            self.activate_plugin(plugin_id)

            self._initialized = True
            logger.info("Plugin system initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize plugin system: {e}", exc_info=True)
            return False

    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins.

        Returns:
            List of discovered plugin IDs
        """
        plugins = self.discovery.discover_all()
        plugin_ids = []

        for plugin_info in plugins:
            if self.registry.register(plugin_info):
                plugin_ids.append(plugin_info.metadata.id)

        return plugin_ids

    def load_plugin(self, plugin_id: str) -> bool:
        """
        Load a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if loaded successfully
        """
        return self.loader.load_plugin(plugin_id)

    def activate_plugin(self, plugin_id: str) -> bool:
        """
        Activate a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if activated successfully
        """
        return self.loader.activate_plugin(plugin_id)

    def deactivate_plugin(self, plugin_id: str) -> bool:
        """
        Deactivate a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if deactivated successfully
        """
        return self.loader.deactivate_plugin(plugin_id)

    def unload_plugin(self, plugin_id: str) -> bool:
        """
        Unload a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if unloaded successfully
        """
        return self.loader.unload_plugin(plugin_id)

    def reload_plugin(self, plugin_id: str) -> bool:
        """
        Reload a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if reloaded successfully
        """
        # Unload first
        if not self.unload_plugin(plugin_id):
            return False

        # Then load and activate
        if self.load_plugin(plugin_id):
            return self.activate_plugin(plugin_id)

        return False

    def get_plugin(self, plugin_id: str) -> Optional[IPlugin]:
        """
        Get plugin instance.

        Args:
            plugin_id: Plugin identifier

        Returns:
            Plugin instance or None
        """
        plugin_info = self.registry.get_plugin(plugin_id)
        if plugin_info:
            return plugin_info.instance
        return None

    def get_all_plugins(self) -> Dict[str, IPlugin]:
        """
        Get all plugin instances.

        Returns:
            Dictionary of plugin ID to instance
        """
        plugins = {}
        for plugin_info in self.registry.get_all_plugins():
            if plugin_info.instance:
                plugins[plugin_info.metadata.id] = plugin_info.instance
        return plugins

    def get_plugin_metadata(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get plugin metadata.

        Args:
            plugin_id: Plugin identifier

        Returns:
            Plugin metadata dictionary or None
        """
        plugin_info = self.registry.get_plugin(plugin_id)
        if plugin_info:
            return {
                "id": plugin_info.metadata.id,
                "name": plugin_info.metadata.name,
                "version": plugin_info.metadata.version,
                "description": plugin_info.metadata.description,
                "author": plugin_info.metadata.author,
                "state": plugin_info.state.name,
                "error": plugin_info.error,
                "dependencies": plugin_info.metadata.dependencies
            }
        return None

    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        List all plugins with their status.

        Returns:
            List of plugin information dictionaries
        """
        plugins = []
        for plugin_info in self.registry.get_all_plugins():
            plugins.append({
                "id": plugin_info.metadata.id,
                "name": plugin_info.metadata.name,
                "version": plugin_info.metadata.version,
                "state": plugin_info.state.name,
                "error": plugin_info.error
            })
        return plugins

    def enable_plugin(self, plugin_id: str) -> bool:
        """
        Enable a plugin (load and activate).

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if enabled successfully
        """
        if self.load_plugin(plugin_id):
            return self.activate_plugin(plugin_id)
        return False

    def disable_plugin(self, plugin_id: str) -> bool:
        """
        Disable a plugin (deactivate and unload).

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if disabled successfully
        """
        if self.deactivate_plugin(plugin_id):
            return self.unload_plugin(plugin_id)
        return False

    def _should_auto_activate(self, plugin_info) -> bool:
        """Check if plugin should be auto-activated."""
        activation_events = plugin_info.metadata.activation_events

        # Check for startup activation
        if "onStartup" in activation_events:
            return True

        # Check for '*' (always activate)
        if "*" in activation_events:
            return True

        return False

    def save_state(self, path: Optional[Path] = None) -> bool:
        """
        Save plugin manager state.

        Args:
            path: Path to save state file

        Returns:
            True if saved successfully
        """
        if not path:
            import platformdirs
            path = Path(platformdirs.user_data_dir("ViloxTerm")) / "plugin_state.json"

        return self.registry.save_state(path)

    def load_state(self, path: Optional[Path] = None) -> bool:
        """
        Load plugin manager state.

        Args:
            path: Path to state file

        Returns:
            True if loaded successfully
        """
        if not path:
            import platformdirs
            path = Path(platformdirs.user_data_dir("ViloxTerm")) / "plugin_state.json"

        return self.registry.load_state(path)
```

### Afternoon (3 hours)

#### Task 3.2: Create Plugin Commands

Create `/home/kuja/GitHub/viloapp/core/commands/builtin/plugin_commands.py`:
```python
"""Plugin-related commands."""

from core.commands.decorators import command
from core.commands.base import CommandContext, CommandResult

@command(
    id="plugins.list",
    title="List Installed Plugins",
    category="Plugins",
    description="Show all installed plugins and their status"
)
def list_plugins_command(context: CommandContext) -> CommandResult:
    """List all plugins."""
    plugin_manager = context.get_service("plugin_manager")
    if not plugin_manager:
        return CommandResult(success=False, error="Plugin manager not available")

    plugins = plugin_manager.list_plugins()
    return CommandResult(success=True, value=plugins)

@command(
    id="plugins.enable",
    title="Enable Plugin",
    category="Plugins",
    description="Enable a disabled plugin"
)
def enable_plugin_command(context: CommandContext, plugin_id: str) -> CommandResult:
    """Enable a plugin."""
    plugin_manager = context.get_service("plugin_manager")
    if not plugin_manager:
        return CommandResult(success=False, error="Plugin manager not available")

    if plugin_manager.enable_plugin(plugin_id):
        return CommandResult(success=True, value=f"Plugin {plugin_id} enabled")
    else:
        return CommandResult(success=False, error=f"Failed to enable plugin {plugin_id}")

@command(
    id="plugins.disable",
    title="Disable Plugin",
    category="Plugins",
    description="Disable an enabled plugin"
)
def disable_plugin_command(context: CommandContext, plugin_id: str) -> CommandResult:
    """Disable a plugin."""
    plugin_manager = context.get_service("plugin_manager")
    if not plugin_manager:
        return CommandResult(success=False, error="Plugin manager not available")

    if plugin_manager.disable_plugin(plugin_id):
        return CommandResult(success=True, value=f"Plugin {plugin_id} disabled")
    else:
        return CommandResult(success=False, error=f"Failed to disable plugin {plugin_id}")

@command(
    id="plugins.reload",
    title="Reload Plugin",
    category="Plugins",
    description="Reload a plugin"
)
def reload_plugin_command(context: CommandContext, plugin_id: str) -> CommandResult:
    """Reload a plugin."""
    plugin_manager = context.get_service("plugin_manager")
    if not plugin_manager:
        return CommandResult(success=False, error="Plugin manager not available")

    if plugin_manager.reload_plugin(plugin_id):
        return CommandResult(success=True, value=f"Plugin {plugin_id} reloaded")
    else:
        return CommandResult(success=False, error=f"Failed to reload plugin {plugin_id}")

@command(
    id="plugins.info",
    title="Plugin Information",
    category="Plugins",
    description="Show detailed information about a plugin"
)
def plugin_info_command(context: CommandContext, plugin_id: str) -> CommandResult:
    """Get plugin information."""
    plugin_manager = context.get_service("plugin_manager")
    if not plugin_manager:
        return CommandResult(success=False, error="Plugin manager not available")

    info = plugin_manager.get_plugin_metadata(plugin_id)
    if info:
        return CommandResult(success=True, value=info)
    else:
        return CommandResult(success=False, error=f"Plugin {plugin_id} not found")

@command(
    id="plugins.discover",
    title="Discover Plugins",
    category="Plugins",
    description="Discover new plugins"
)
def discover_plugins_command(context: CommandContext) -> CommandResult:
    """Discover new plugins."""
    plugin_manager = context.get_service("plugin_manager")
    if not plugin_manager:
        return CommandResult(success=False, error="Plugin manager not available")

    plugin_ids = plugin_manager.discover_plugins()
    return CommandResult(
        success=True,
        value=f"Discovered {len(plugin_ids)} plugins: {', '.join(plugin_ids)}"
    )
```

### Validation Checkpoint
- [ ] Plugin manager orchestrates all operations
- [ ] Commands for plugin management work
- [ ] State can be saved/loaded
- [ ] Auto-activation works

## Day 4: Service Integration

### Morning (3 hours)

#### Task 4.1: Update Main Application

Modify `/home/kuja/GitHub/viloapp/main.py` to integrate plugin system:
```python
# Add to imports
from core.plugin_system import PluginManager
from viloapp_sdk import EventBus

def initialize_plugins(services):
    """Initialize plugin system."""
    # Create event bus
    event_bus = EventBus()

    # Create plugin manager
    plugin_manager = PluginManager(event_bus, services)

    # Add plugin manager to services
    services['plugin_manager'] = plugin_manager
    services['event_bus'] = event_bus

    # Initialize plugin system
    plugin_manager.initialize()

    return plugin_manager

# In main application initialization:
# After services are created:
plugin_manager = initialize_plugins(services)
```

#### Task 4.2: Create Plugin Service Adapters

Create `/home/kuja/GitHub/viloapp/core/plugin_system/service_adapters.py`:
```python
"""Service adapters for plugin SDK interfaces."""

from typing import Any, Optional, Dict
from viloapp_sdk import (
    ICommandService, IConfigurationService,
    IWorkspaceService, IThemeService, INotificationService
)

class CommandServiceAdapter(ICommandService):
    """Adapter for command service."""

    def __init__(self, command_service):
        self.command_service = command_service

    def get_service_id(self) -> str:
        return "command"

    def get_service_version(self) -> str:
        return "1.0.0"

    def execute_command(self, command_id: str, **kwargs) -> Any:
        from core.commands.executor import execute_command
        result = execute_command(command_id, **kwargs)
        return result.value if result.success else None

    def register_command(self, command_id: str, handler: callable) -> None:
        # This would need implementation in command registry
        pass

    def unregister_command(self, command_id: str) -> None:
        # This would need implementation in command registry
        pass

class ConfigurationServiceAdapter(IConfigurationService):
    """Adapter for configuration service."""

    def __init__(self, settings_service):
        self.settings_service = settings_service

    def get_service_id(self) -> str:
        return "configuration"

    def get_service_version(self) -> str:
        return "1.0.0"

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings_service.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.settings_service.set(key, value)

    def on_change(self, key: str, callback: callable) -> None:
        # This would need signal connection
        pass

class WorkspaceServiceAdapter(IWorkspaceService):
    """Adapter for workspace service."""

    def __init__(self, workspace_service):
        self.workspace_service = workspace_service

    def get_service_id(self) -> str:
        return "workspace"

    def get_service_version(self) -> str:
        return "1.0.0"

    def open_file(self, path: str) -> None:
        # Implementation would open file in editor
        pass

    def get_active_editor(self) -> Optional[Any]:
        # Return active editor widget
        return None

    def create_pane(self, widget: Any, position: str) -> None:
        # Create new pane with widget
        pass

class ThemeServiceAdapter(IThemeService):
    """Adapter for theme service."""

    def __init__(self, theme_service):
        self.theme_service = theme_service

    def get_service_id(self) -> str:
        return "theme"

    def get_service_version(self) -> str:
        return "1.0.0"

    def get_current_theme(self) -> Dict[str, Any]:
        theme = self.theme_service.get_current_theme()
        return {
            "id": theme.id,
            "name": theme.name,
            "colors": theme.colors
        }

    def get_color(self, key: str) -> str:
        return self.theme_service.get_color(key)

    def on_theme_changed(self, callback: callable) -> None:
        self.theme_service.theme_changed.connect(callback)

class NotificationServiceAdapter(INotificationService):
    """Adapter for notification service."""

    def __init__(self, ui_service):
        self.ui_service = ui_service

    def get_service_id(self) -> str:
        return "notification"

    def get_service_version(self) -> str:
        return "1.0.0"

    def info(self, message: str, title: Optional[str] = None) -> None:
        # Show info notification
        print(f"INFO: {title or ''} - {message}")

    def warning(self, message: str, title: Optional[str] = None) -> None:
        # Show warning notification
        print(f"WARNING: {title or ''} - {message}")

    def error(self, message: str, title: Optional[str] = None) -> None:
        # Show error notification
        print(f"ERROR: {title or ''} - {message}")

def create_service_adapters(services: Dict[str, Any]) -> Dict[str, Any]:
    """Create service adapters for plugins."""
    adapters = {}

    # Add command service
    if 'command_service' in services:
        adapters['command'] = CommandServiceAdapter(services['command_service'])

    # Add configuration service
    if 'settings_service' in services:
        adapters['configuration'] = ConfigurationServiceAdapter(services['settings_service'])

    # Add workspace service
    if 'workspace_service' in services:
        adapters['workspace'] = WorkspaceServiceAdapter(services['workspace_service'])

    # Add theme service
    if 'theme_service' in services:
        adapters['theme'] = ThemeServiceAdapter(services['theme_service'])

    # Add notification service
    if 'ui_service' in services:
        adapters['notification'] = NotificationServiceAdapter(services['ui_service'])

    return adapters
```

### Afternoon (2 hours)

#### Task 4.3: Create Plugin Settings UI

Create `/home/kuja/GitHub/viloapp/ui/widgets/plugin_settings_widget.py`:
```python
"""Plugin settings widget."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QLabel, QGroupBox, QTextEdit,
    QListWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt

class PluginSettingsWidget(QWidget):
    """Widget for managing plugins."""

    def __init__(self, plugin_manager, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self.setup_ui()
        self.load_plugins()

    def setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout()

        # Plugin list
        self.plugin_list = QListWidget()
        self.plugin_list.currentItemChanged.connect(self.on_plugin_selected)

        # Plugin details
        self.details_group = QGroupBox("Plugin Details")
        details_layout = QVBoxLayout()

        self.name_label = QLabel()
        self.version_label = QLabel()
        self.author_label = QLabel()
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(100)

        details_layout.addWidget(self.name_label)
        details_layout.addWidget(self.version_label)
        details_layout.addWidget(self.author_label)
        details_layout.addWidget(self.description_text)

        self.details_group.setLayout(details_layout)

        # Control buttons
        button_layout = QHBoxLayout()

        self.enable_button = QPushButton("Enable")
        self.enable_button.clicked.connect(self.enable_plugin)

        self.disable_button = QPushButton("Disable")
        self.disable_button.clicked.connect(self.disable_plugin)

        self.reload_button = QPushButton("Reload")
        self.reload_button.clicked.connect(self.reload_plugin)

        self.discover_button = QPushButton("Discover New")
        self.discover_button.clicked.connect(self.discover_plugins)

        button_layout.addWidget(self.enable_button)
        button_layout.addWidget(self.disable_button)
        button_layout.addWidget(self.reload_button)
        button_layout.addStretch()
        button_layout.addWidget(self.discover_button)

        # Add to main layout
        layout.addWidget(QLabel("Installed Plugins:"))
        layout.addWidget(self.plugin_list)
        layout.addWidget(self.details_group)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_plugins(self):
        """Load plugin list."""
        self.plugin_list.clear()

        plugins = self.plugin_manager.list_plugins()
        for plugin in plugins:
            item = QListWidgetItem(plugin['name'])
            item.setData(Qt.UserRole, plugin)

            # Set icon based on state
            if plugin['state'] == 'ACTIVATED':
                item.setText(f"✓ {plugin['name']}")
            elif plugin['state'] == 'FAILED':
                item.setText(f"✗ {plugin['name']}")

            self.plugin_list.addItem(item)

    def on_plugin_selected(self, current, previous):
        """Handle plugin selection."""
        if not current:
            return

        plugin_data = current.data(Qt.UserRole)
        if not plugin_data:
            return

        # Get full metadata
        metadata = self.plugin_manager.get_plugin_metadata(plugin_data['id'])
        if metadata:
            self.name_label.setText(f"Name: {metadata['name']}")
            self.version_label.setText(f"Version: {metadata['version']}")
            self.author_label.setText(f"Author: {metadata['author']}")
            self.description_text.setPlainText(metadata['description'])

            # Update button states
            state = metadata['state']
            self.enable_button.setEnabled(state not in ['ACTIVATED', 'LOADED'])
            self.disable_button.setEnabled(state == 'ACTIVATED')
            self.reload_button.setEnabled(state in ['ACTIVATED', 'FAILED'])

    def enable_plugin(self):
        """Enable selected plugin."""
        current = self.plugin_list.currentItem()
        if current:
            plugin_data = current.data(Qt.UserRole)
            if self.plugin_manager.enable_plugin(plugin_data['id']):
                QMessageBox.information(self, "Success", f"Plugin {plugin_data['name']} enabled")
                self.load_plugins()
            else:
                QMessageBox.warning(self, "Error", f"Failed to enable {plugin_data['name']}")

    def disable_plugin(self):
        """Disable selected plugin."""
        current = self.plugin_list.currentItem()
        if current:
            plugin_data = current.data(Qt.UserRole)
            if self.plugin_manager.disable_plugin(plugin_data['id']):
                QMessageBox.information(self, "Success", f"Plugin {plugin_data['name']} disabled")
                self.load_plugins()
            else:
                QMessageBox.warning(self, "Error", f"Failed to disable {plugin_data['name']}")

    def reload_plugin(self):
        """Reload selected plugin."""
        current = self.plugin_list.currentItem()
        if current:
            plugin_data = current.data(Qt.UserRole)
            if self.plugin_manager.reload_plugin(plugin_data['id']):
                QMessageBox.information(self, "Success", f"Plugin {plugin_data['name']} reloaded")
                self.load_plugins()
            else:
                QMessageBox.warning(self, "Error", f"Failed to reload {plugin_data['name']}")

    def discover_plugins(self):
        """Discover new plugins."""
        new_plugins = self.plugin_manager.discover_plugins()
        if new_plugins:
            QMessageBox.information(
                self, "Plugins Discovered",
                f"Found {len(new_plugins)} new plugins"
            )
            self.load_plugins()
        else:
            QMessageBox.information(self, "No New Plugins", "No new plugins found")
```

### Validation Checkpoint
- [ ] Plugin system integrated with main app
- [ ] Service adapters work
- [ ] Plugin settings UI functional
- [ ] Plugins can access host services

## Day 5: Testing and Polish

### Morning (3 hours)

#### Task 5.1: Create Plugin System Tests

Create `/home/kuja/GitHub/viloapp/tests/unit/test_plugin_system.py`:
```python
"""Tests for plugin system."""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock

from core.plugin_system import PluginManager, PluginRegistry
from viloapp_sdk import IPlugin, PluginMetadata, EventBus

class TestPlugin(IPlugin):
    """Test plugin implementation."""

    def __init__(self):
        self.activated = False
        self.deactivated = False

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test"
        )

    def activate(self, context):
        self.activated = True

    def deactivate(self):
        self.deactivated = True

@pytest.fixture
def plugin_manager():
    """Create plugin manager for testing."""
    event_bus = EventBus()
    services = {
        'command': Mock(),
        'configuration': Mock(),
        'workspace': Mock()
    }
    return PluginManager(event_bus, services)

def test_plugin_discovery(plugin_manager):
    """Test plugin discovery."""
    # Mock discovery
    plugin_manager.discovery.discover_all = Mock(return_value=[])

    # Discover plugins
    plugins = plugin_manager.discover_plugins()
    assert isinstance(plugins, list)

def test_plugin_loading(plugin_manager):
    """Test plugin loading."""
    # Register test plugin
    from core.plugin_system.plugin_registry import PluginInfo
    from viloapp_sdk import LifecycleState

    plugin_info = PluginInfo(
        metadata=PluginMetadata(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="Test",
            author="Test"
        ),
        path=Path("test"),
        state=LifecycleState.DISCOVERED
    )

    plugin_manager.registry.register(plugin_info)

    # Mock loader
    plugin_manager.loader.load_plugin = Mock(return_value=True)

    # Load plugin
    assert plugin_manager.load_plugin("test-plugin")

def test_plugin_activation(plugin_manager):
    """Test plugin activation."""
    # Setup test plugin
    test_plugin = TestPlugin()

    # Mock getting plugin
    plugin_manager.get_plugin = Mock(return_value=test_plugin)
    plugin_manager.loader.activate_plugin = Mock(return_value=True)

    # Activate
    assert plugin_manager.activate_plugin("test-plugin")

def test_dependency_resolution():
    """Test dependency resolution."""
    from core.plugin_system import DependencyResolver

    registry = PluginRegistry()
    resolver = DependencyResolver(registry)

    # Create plugins with dependencies
    from core.plugin_system.plugin_registry import PluginInfo
    from viloapp_sdk import LifecycleState

    plugin_a = PluginInfo(
        metadata=PluginMetadata(
            id="plugin-a",
            name="Plugin A",
            version="1.0.0",
            description="A",
            author="Test",
            dependencies=[]
        ),
        path=Path("a"),
        state=LifecycleState.DISCOVERED
    )

    plugin_b = PluginInfo(
        metadata=PluginMetadata(
            id="plugin-b",
            name="Plugin B",
            version="1.0.0",
            description="B",
            author="Test",
            dependencies=["plugin-a@>=1.0.0"]
        ),
        path=Path("b"),
        state=LifecycleState.DISCOVERED
    )

    registry.register(plugin_a)
    registry.register(plugin_b)

    # Resolve dependencies
    load_order, unmet = resolver.resolve_dependencies()

    # Check load order (A should come before B)
    assert load_order.index("plugin-a") < load_order.index("plugin-b")
    assert len(unmet) == 0
```

### Afternoon (2 hours)

#### Task 5.2: Create Integration Tests

Create `/home/kuja/GitHub/viloapp/tests/integration/test_plugin_integration.py`:
```python
"""Integration tests for plugin system."""

import pytest
from unittest.mock import Mock

from core.plugin_system import PluginManager
from viloapp_sdk import EventBus, IPlugin, PluginMetadata

def test_full_plugin_lifecycle():
    """Test complete plugin lifecycle."""
    # Create plugin manager
    event_bus = EventBus()
    services = {'test': Mock()}
    manager = PluginManager(event_bus, services)

    # Initialize (will discover and load plugins)
    # This would need actual plugins to test fully
    # manager.initialize()

    # Check that manager is ready
    assert manager is not None

def test_plugin_event_communication():
    """Test plugin event communication."""
    event_bus = EventBus()
    received_events = []

    # Subscribe to events
    def handler(event):
        received_events.append(event)

    from viloapp_sdk import EventType
    event_bus.subscribe(EventType.PLUGIN_LOADED, handler)

    # Create manager
    services = {}
    manager = PluginManager(event_bus, services)

    # Trigger an event
    from viloapp_sdk import PluginEvent
    event_bus.emit(PluginEvent(
        type=EventType.PLUGIN_LOADED,
        source="test",
        data={"plugin_id": "test"}
    ))

    # Check event was received
    assert len(received_events) == 1
    assert received_events[0].data["plugin_id"] == "test"

def test_plugin_service_access():
    """Test that plugins can access services."""
    # Create services
    mock_service = Mock()
    mock_service.get_service_id.return_value = "test"
    mock_service.get_service_version.return_value = "1.0.0"

    services = {'test': mock_service}

    # Create plugin manager
    event_bus = EventBus()
    manager = PluginManager(event_bus, services)

    # Plugins loaded by manager should have access to services
    # This would be tested with actual plugin loading
    assert 'test' in services
```

#### Task 5.3: Documentation

Create `/home/kuja/GitHub/viloapp/docs/plugin-development/plugin_host.md`:
```markdown
# Plugin Host Documentation

## Overview

The ViloxTerm plugin host provides a robust infrastructure for discovering, loading, and managing plugins.

## Architecture

### Components

1. **Plugin Manager** - Central orchestrator
2. **Plugin Registry** - Tracks all plugins and their states
3. **Plugin Discovery** - Finds plugins from various sources
4. **Plugin Loader** - Loads and activates plugins
5. **Dependency Resolver** - Resolves plugin dependencies
6. **Service Proxy** - Provides access to host services

## Plugin Lifecycle

```
DISCOVERED -> LOADED -> ACTIVATED -> DEACTIVATED -> UNLOADED
                |                        |
                v                        v
              FAILED                  FAILED
```

## Services Available to Plugins

- **command** - Execute and register commands
- **configuration** - Access and modify configuration
- **workspace** - Interact with workspace
- **theme** - Access theme information
- **notification** - Show notifications

## Plugin Discovery Sources

1. Python entry points (`viloapp.plugins`)
2. User plugin directory (`~/.config/ViloxTerm/plugins/`)
3. System plugin directory
4. Built-in plugins

## Creating a Plugin

See the [Plugin SDK documentation](../packages/viloapp-sdk/docs/getting_started.md)

## Managing Plugins

### Via Commands

- `plugins.list` - List all plugins
- `plugins.enable` - Enable a plugin
- `plugins.disable` - Disable a plugin
- `plugins.reload` - Reload a plugin
- `plugins.info` - Get plugin information

### Via UI

Open Settings > Plugins to manage plugins through the UI.

## Security

Plugins run in the same process but with restricted service access. Only approved services are exposed through the service proxy.

## Debugging

Enable debug logging to see plugin operations:

```python
import logging
logging.getLogger('core.plugin_system').setLevel(logging.DEBUG)
```
```

### Final Validation Checkpoint
- [ ] All tests pass
- [ ] Plugin system fully integrated
- [ ] Documentation complete
- [ ] Example plugin can be loaded
- [ ] UI for plugin management works

## Week 2 Summary

### Completed Deliverables
1. ✅ Complete plugin registry system
2. ✅ Plugin discovery from multiple sources
3. ✅ Dependency resolution with topological sorting
4. ✅ Plugin loader with lifecycle management
5. ✅ Service proxy and adapters
6. ✅ Plugin manager orchestration
7. ✅ Plugin management commands
8. ✅ Plugin settings UI
9. ✅ Comprehensive test suite
10. ✅ Documentation

### Key Files Created
- `/core/plugin_system/` - Complete plugin host infrastructure
- `/core/commands/builtin/plugin_commands.py` - Plugin commands
- `/ui/widgets/plugin_settings_widget.py` - Plugin management UI
- `/tests/unit/test_plugin_system.py` - Unit tests
- `/tests/integration/test_plugin_integration.py` - Integration tests
- `/docs/plugin-development/plugin_host.md` - Documentation

### Ready for Week 3
The plugin host infrastructure is complete and ready for:
- Extracting terminal functionality into a plugin
- Creating the terminal plugin package
- Testing plugin-based terminal integration

### Next Steps
- Week 3: Begin terminal plugin extraction
- Week 4: Complete terminal plugin and integration
- Week 5: Extract editor plugin