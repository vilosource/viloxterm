#!/usr/bin/env python3
"""
Theme validation schema.
"""

from typing import Dict, List, Any


class ThemeSchema:
    """Schema for validating theme structure."""

    @staticmethod
    def get_required_fields() -> List[str]:
        """Get list of required top-level fields."""
        return [
            "id",
            "name",
            "description",
            "version",
            "author",
            "colors"
        ]

    @staticmethod
    def get_required_colors() -> List[str]:
        """Get list of required color keys."""
        return [
            "editor.background",
            "editor.foreground",
            "activityBar.background",
            "activityBar.foreground",
            "sideBar.background",
            "sideBar.foreground",
            "statusBar.background",
            "statusBar.foreground",
            "tab.activeBackground",
            "tab.activeForeground",
            "tab.inactiveBackground",
            "tab.inactiveForeground",
        ]

    @staticmethod
    def validate_theme_data(data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate theme data structure.

        Args:
            data: Theme data dictionary

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required fields
        required_fields = ThemeSchema.get_required_fields()
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Check colors is a dictionary
        if "colors" in data and not isinstance(data["colors"], dict):
            errors.append("'colors' must be a dictionary")

        # Check required colors
        if "colors" in data and isinstance(data["colors"], dict):
            required_colors = ThemeSchema.get_required_colors()
            for color in required_colors:
                if color not in data["colors"]:
                    errors.append(f"Missing required color: {color}")

        # Validate color format
        if "colors" in data and isinstance(data["colors"], dict):
            for key, value in data["colors"].items():
                if not ThemeSchema._is_valid_color(value):
                    errors.append(f"Invalid color format for {key}: {value}")

        # Validate version format (should be semver-like)
        if "version" in data:
            if not ThemeSchema._is_valid_version(data["version"]):
                errors.append(f"Invalid version format: {data['version']}")

        return len(errors) == 0, errors

    @staticmethod
    def _is_valid_color(color: Any) -> bool:
        """Check if color is valid hex format."""
        if not isinstance(color, str):
            return False

        if not color.startswith("#"):
            return False

        hex_part = color[1:]
        if len(hex_part) not in [3, 6, 8]:
            return False

        try:
            int(hex_part, 16)
            return True
        except ValueError:
            return False

    @staticmethod
    def _is_valid_version(version: Any) -> bool:
        """Check if version string is valid."""
        if not isinstance(version, str):
            return False

        # Simple check for x.y.z format
        parts = version.split(".")
        if len(parts) < 2 or len(parts) > 3:
            return False

        for part in parts:
            try:
                int(part)
            except ValueError:
                return False

        return True