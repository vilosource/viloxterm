"""Type definitions for plugin SDK."""

from typing import Any, List, Optional, Union
from dataclasses import dataclass


@dataclass
class CommandContribution:
    """Command contribution from a plugin."""

    id: str
    title: str
    category: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    enablement: Optional[str] = None  # When condition


@dataclass
class MenuContribution:
    """Menu contribution from a plugin."""

    command_id: str
    group: str
    order: Optional[int] = None
    when: Optional[str] = None  # Context expression


@dataclass
class KeybindingContribution:
    """Keybinding contribution from a plugin."""

    command_id: str
    key: str
    when: Optional[str] = None
    mac: Optional[str] = None  # Mac-specific binding
    linux: Optional[str] = None  # Linux-specific binding
    win: Optional[str] = None  # Windows-specific binding


@dataclass
class ConfigurationContribution:
    """Configuration contribution from a plugin."""

    key: str
    title: str
    description: str
    type: str  # "string", "number", "boolean", "array", "object"
    default: Any
    enum: Optional[List[Any]] = None
    minimum: Optional[Union[int, float]] = None
    maximum: Optional[Union[int, float]] = None
