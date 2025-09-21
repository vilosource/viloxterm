"""Plugin dependency resolution."""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

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
        parts1 = [int(x) for x in v1.split(".")]
        parts2 = [int(x) for x in v2.split(".")]

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
        self, plugin_ids: Optional[List[str]] = None
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

        # Initialize graph with all plugins
        for plugin in plugins:
            plugin_id = plugin.metadata.id
            graph[plugin_id] = set()

        # Build edges: dependency -> dependent
        # If B depends on A, create edge A -> B
        for plugin in plugins:
            plugin_id = plugin.metadata.id

            # Parse dependencies
            for dep_str in plugin.metadata.dependencies:
                dep = self._parse_dependency(dep_str)
                if dep and not dep.optional:
                    # dep.plugin_id should be loaded before plugin_id
                    # So create edge: dep.plugin_id -> plugin_id
                    if dep.plugin_id in graph:
                        graph[dep.plugin_id].add(plugin_id)

        return graph

    def _parse_dependency(self, dep_str: str) -> Optional[Dependency]:
        """Parse dependency string."""
        # Format: "plugin-id@version" or "plugin-id@>=version"
        match = re.match(r"^([a-zA-Z0-9\-]+)(?:@(.+))?$", dep_str)
        if not match:
            return None

        plugin_id = match.group(1)
        version_spec = match.group(2) or "*"

        # Check for optional marker
        optional = dep_str.endswith("?")
        if optional:
            dep_str = dep_str[:-1]

        return Dependency(plugin_id=plugin_id, version_spec=version_spec, optional=optional)

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
        in_degree = dict.fromkeys(graph, 0)
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
