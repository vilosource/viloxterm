#!/usr/bin/env python3
"""
Theme typography system for font customization.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class FontFamily(Enum):
    """Standard font family options."""

    MONOSPACE = "monospace"
    SANS_SERIF = "sans-serif"
    SERIF = "serif"
    SYSTEM_UI = "system-ui"


@dataclass
class ThemeTypography:
    """Typography configuration for a theme."""

    # Base font settings
    font_family: str = "Fira Code, Consolas, Monaco, monospace"
    font_size_base: int = 14  # Base font size in pixels
    line_height: float = 1.5  # Line height multiplier

    # Font weight variations
    font_weight_normal: int = 400
    font_weight_medium: int = 500
    font_weight_bold: int = 700

    # Size scale (relative to base)
    size_scale: dict[str, float] = field(
        default_factory=lambda: {
            "xs": 0.75,  # 75% of base
            "sm": 0.875,  # 87.5% of base
            "base": 1.0,  # 100% of base
            "lg": 1.125,  # 112.5% of base
            "xl": 1.25,  # 125% of base
            "2xl": 1.5,  # 150% of base
            "3xl": 1.875,  # 187.5% of base
        }
    )

    # Component-specific overrides
    overrides: dict[str, dict[str, any]] = field(default_factory=dict)

    def get_font_size(self, scale_key: str = "base") -> int:
        """
        Get font size for a specific scale.

        Args:
            scale_key: Size scale key (xs, sm, base, lg, xl, 2xl, 3xl)

        Returns:
            Font size in pixels
        """
        scale = self.size_scale.get(scale_key, 1.0)
        return int(self.font_size_base * scale)

    def get_line_height(self, font_size: Optional[int] = None) -> int:
        """
        Get line height for a font size.

        Args:
            font_size: Font size in pixels (uses base if not provided)

        Returns:
            Line height in pixels
        """
        if font_size is None:
            font_size = self.font_size_base
        return int(font_size * self.line_height)

    def get_component_style(self, component: str) -> dict[str, any]:
        """
        Get typography style for a specific component.

        Args:
            component: Component identifier (e.g., "editor", "terminal", "sidebar")

        Returns:
            Dictionary of typography properties for the component
        """
        # Start with base settings
        style = {
            "font-family": self.font_family,
            "font-size": f"{self.font_size_base}px",
            "line-height": str(self.line_height),
            "font-weight": self.font_weight_normal,
        }

        # Apply component-specific overrides
        if component in self.overrides:
            style.update(self.overrides[component])

        return style

    def to_dict(self) -> dict:
        """Convert typography to dictionary."""
        return {
            "fontFamily": self.font_family,
            "fontSizeBase": self.font_size_base,
            "lineHeight": self.line_height,
            "fontWeightNormal": self.font_weight_normal,
            "fontWeightMedium": self.font_weight_medium,
            "fontWeightBold": self.font_weight_bold,
            "sizeScale": self.size_scale,
            "overrides": self.overrides,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ThemeTypography":
        """
        Create typography from dictionary.

        Args:
            data: Typography data dictionary

        Returns:
            ThemeTypography instance
        """
        # Default size scale
        default_size_scale = {
            "xs": 0.75,
            "sm": 0.875,
            "base": 1.0,
            "lg": 1.125,
            "xl": 1.25,
            "2xl": 1.5,
            "3xl": 1.875,
        }

        return cls(
            font_family=data.get("fontFamily", "Fira Code, Consolas, Monaco, monospace"),
            font_size_base=data.get("fontSizeBase", 14),
            line_height=data.get("lineHeight", 1.5),
            font_weight_normal=data.get("fontWeightNormal", 400),
            font_weight_medium=data.get("fontWeightMedium", 500),
            font_weight_bold=data.get("fontWeightBold", 700),
            size_scale=data.get("sizeScale", default_size_scale),
            overrides=data.get("overrides", {}),
        )


# Default typography presets
TYPOGRAPHY_PRESETS = {
    "compact": ThemeTypography(font_size_base=12, line_height=1.4),
    "default": ThemeTypography(font_size_base=14, line_height=1.5),
    "comfortable": ThemeTypography(font_size_base=16, line_height=1.6),
    "large": ThemeTypography(font_size_base=18, line_height=1.7),
}
