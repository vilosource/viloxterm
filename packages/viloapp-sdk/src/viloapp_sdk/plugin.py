"""Plugin interface and metadata definitions."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from .interfaces import IPlugin, IMetadata

class PluginCapability(Enum):
    """Plugin capabilities that can be declared."""
    WIDGETS = "widgets"
    COMMANDS = "commands"
    THEMES = "themes"
    LANGUAGES = "languages"
    DEBUGGERS = "debuggers"
    TERMINALS = "terminals"
    EDITORS = "editors"
    VIEWS = "views"
    SETTINGS = "settings"

@dataclass
class PluginMetadata(IMetadata):
    """Plugin metadata and manifest information implementing IMetadata interface."""
    # Required fields
    id: str
    name: str
    version: str
    description: str
    author: str  # Can be string for backward compatibility

    # Optional fields
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = "MIT"  # Default license
    icon: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)

    # Technical fields
    engines: Dict[str, str] = field(default_factory=dict)  # {"viloapp": ">=2.0.0"}
    dependencies: List[str] = field(default_factory=list)  # Legacy format
    dependencies_dict: Dict[str, str] = field(default_factory=dict)  # New format
    activation_events: List[str] = field(default_factory=list)
    capabilities: List[PluginCapability] = field(default_factory=list)

    # Contributions
    contributes: Dict[str, Any] = field(default_factory=dict)

    # IMetadata interface implementation
    def get_id(self) -> str:
        """Get unique plugin identifier."""
        return self.id

    def get_name(self) -> str:
        """Get plugin display name."""
        return self.name

    def get_version(self) -> str:
        """Get plugin version."""
        return self.version

    def get_description(self) -> str:
        """Get plugin description."""
        return self.description

    def get_author(self) -> Dict[str, str]:
        """Get plugin author information."""
        if isinstance(self.author, str):
            # Backward compatibility - convert string to dict
            return {"name": self.author}
        elif isinstance(self.author, dict):
            return self.author
        else:
            return {"name": str(self.author)}

    def get_license(self) -> str:
        """Get plugin license."""
        return self.license or "MIT"

    def get_dependencies(self) -> Dict[str, str]:
        """Get plugin dependencies."""
        # Prefer new dict format, fall back to converting list format
        if self.dependencies_dict:
            return self.dependencies_dict

        # Convert legacy list format to dict format
        deps = {}
        for dep in self.dependencies:
            if isinstance(dep, str):
                # Simple string dependency
                deps[dep] = "*"  # Any version
            elif isinstance(dep, dict) and "name" in dep:
                # Dict format: {"name": "package", "version": ">=1.0.0"}
                deps[dep["name"]] = dep.get("version", "*")

        # Add engines as dependencies
        deps.update(self.engines)
        return deps

    def get_keywords(self) -> List[str]:
        """Get plugin keywords."""
        return self.keywords

    def get_homepage(self) -> Optional[str]:
        """Get plugin homepage URL."""
        return self.homepage

    def get_repository(self) -> Optional[str]:
        """Get plugin repository URL."""
        return self.repository

    def get_icon(self) -> Optional[str]:
        """Get plugin icon identifier."""
        return self.icon

    def get_categories(self) -> List[str]:
        """Get plugin categories."""
        return self.categories

    def validate(self) -> List[str]:
        """Validate metadata using IMetadata interface."""
        # Use the interface validation, then add plugin-specific checks
        errors = super().validate()

        # Add plugin-specific validation
        if self.dependencies and not isinstance(self.dependencies, list):
            errors.append("Dependencies must be a list")

        if self.capabilities:
            for cap in self.capabilities:
                if not isinstance(cap, PluginCapability):
                    errors.append(f"Invalid capability: {cap}")

        return errors

