#!/usr/bin/env python3
"""
Theme data model and related classes.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .typography import ThemeTypography

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

    def to_dict(self) -> dict:
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
    colors: dict[str, str] = field(default_factory=dict)
    typography: Optional[ThemeTypography] = None

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

    def get_typography(self) -> ThemeTypography:
        """
        Get typography configuration with fallback to default.

        Returns:
            ThemeTypography instance
        """
        if self.typography:
            return self.typography
        return ThemeTypography()  # Return default typography

    def validate(self) -> tuple[bool, list[str]]:
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

        # Merge typography if parent has it
        if parent.typography and not self.typography:
            self.typography = parent.typography
        elif parent.typography and self.typography:
            # Merge typography settings (child overrides parent)
            parent_typography_dict = parent.typography.to_dict()
            child_typography_dict = self.typography.to_dict()

            # Deep merge typography
            for key, value in parent_typography_dict.items():
                if key not in child_typography_dict:
                    child_typography_dict[key] = value
                elif isinstance(value, dict) and key in child_typography_dict:
                    # Merge nested dicts like overrides
                    merged_dict = value.copy()
                    merged_dict.update(child_typography_dict[key])
                    child_typography_dict[key] = merged_dict

            self.typography = ThemeTypography.from_dict(child_typography_dict)

    def to_dict(self) -> dict:
        """Convert theme to dictionary."""
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'author': self.author,
            'extends': self.extends,
            'colors': self.colors
        }

        if self.typography:
            result['typography'] = self.typography.to_dict()

        return result

    def to_json(self) -> str:
        """Convert theme to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> 'Theme':
        """
        Create theme from dictionary.

        Args:
            data: Theme data dictionary

        Returns:
            Theme instance
        """
        typography = None
        if 'typography' in data:
            typography = ThemeTypography.from_dict(data['typography'])

        return cls(
            id=data.get('id', 'unknown'),
            name=data.get('name', 'Unknown Theme'),
            description=data.get('description', ''),
            version=data.get('version', '1.0.0'),
            author=data.get('author', 'Unknown'),
            extends=data.get('extends'),
            colors=data.get('colors', {}),
            typography=typography
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
        with open(path, encoding='utf-8') as f:
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
