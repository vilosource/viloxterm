"""Plugin system for ViloxTerm."""

# Import implemented components
from .dependency_resolver import DependencyResolver
from .plugin_discovery import PluginDiscovery
from .plugin_loader import PluginLoader
from .plugin_manager import PluginManager
from .plugin_registry import PluginRegistry

__all__ = [
    "PluginDiscovery",
    "PluginRegistry",
    "DependencyResolver",
    "PluginLoader",
    "PluginManager",
]
