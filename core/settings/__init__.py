#!/usr/bin/env python3
"""
Settings package for centralized application configuration management.

This package provides a type-safe, schema-validated settings system built on top
of QSettings with integration to the existing StateService.
"""

from .defaults import DEFAULT_SETTINGS, get_default_keyboard_shortcuts
from .schema import SettingsSchema, validate_settings
from .service import SettingsService

__all__ = [
    'DEFAULT_SETTINGS',
    'get_default_keyboard_shortcuts',
    'SettingsSchema',
    'validate_settings',
    'SettingsService'
]