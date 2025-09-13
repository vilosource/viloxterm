#!/usr/bin/env python3
"""
Theme data model and related classes.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Tuple
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class ThemeInfo:
    """Theme metadata information."""
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    author: str = "ViloxTerm"
    extends: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'author': self.author,
            'extends': self.extends
        }


@dataclass
class Theme:
    """Complete theme with colors and metadata."""

    id: str
    name: str
    description: str
    version: str
    author: str
    extends: Optional[str] = None
    colors: Dict[str, str] = field(default_factory=dict)

    def get_color(self, key: str, fallback: str = "#000000") -> str:
        """
        Get a color value with fallback.

        Args:
            key: Color key to look up
            fallback: Fallback color if key not found

        Returns:
            Color value as hex string
        """
        return self.colors.get(key, fallback)

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate theme has required colors.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Required base colors
        required_colors = [
            "editor.background",
            "editor.foreground",
            "activityBar.background",
            "activityBar.foreground",
            "sideBar.background",
            "sideBar.foreground",
            "statusBar.background",
            "statusBar.foreground",
        ]

        for color_key in required_colors:
            if color_key not in self.colors:
                errors.append(f"Missing required color: {color_key}")

        # Validate color format (should be hex)
        for key, value in self.colors.items():
            if not self._is_valid_color(value):
                errors.append(f"Invalid color format for {key}: {value}")

        return len(errors) == 0, errors

    def _is_valid_color(self, color: str) -> bool:
        """Check if color is valid hex format."""
        if not color.startswith("#"):
            return False

        # Check if it's a valid hex color (3, 6, or 8 characters)
        hex_part = color[1:]
        if len(hex_part) not in [3, 6, 8]:
            return False

        try:
            int(hex_part, 16)
            return True
        except ValueError:
            return False

    def merge_with_parent(self, parent: 'Theme') -> None:
        """
        Merge parent theme colors into this theme.

        Args:
            parent: Parent theme to inherit from
        """
        if not parent:
            return

        # Start with parent colors
        merged_colors = parent.colors.copy()

        # Override with this theme's colors
        merged_colors.update(self.colors)

        # Update colors
        self.colors = merged_colors

    def to_dict(self) -> Dict:
        """Convert theme to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'author': self.author,
            'extends': self.extends,
            'colors': self.colors
        }

    def to_json(self) -> str:
        """Convert theme to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Theme':
        """
        Create theme from dictionary.

        Args:
            data: Theme data dictionary

        Returns:
            Theme instance
        """
        return cls(
            id=data.get('id', 'unknown'),
            name=data.get('name', 'Unknown Theme'),
            description=data.get('description', ''),
            version=data.get('version', '1.0.0'),
            author=data.get('author', 'Unknown'),
            extends=data.get('extends'),
            colors=data.get('colors', {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'Theme':
        """
        Create theme from JSON string.

        Args:
            json_str: JSON string containing theme data

        Returns:
            Theme instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def from_json_file(cls, path: Path) -> 'Theme':
        """
        Load theme from JSON file.

        Args:
            path: Path to JSON file

        Returns:
            Theme instance
        """
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_json_file(self, path: Path) -> None:
        """
        Save theme to JSON file.

        Args:
            path: Path to save file
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

    def get_info(self) -> ThemeInfo:
        """Get theme metadata as ThemeInfo."""
        return ThemeInfo(
            id=self.id,
            name=self.name,
            description=self.description,
            version=self.version,
            author=self.author,
            extends=self.extends
        )