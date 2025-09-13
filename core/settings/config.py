#!/usr/bin/env python3
"""
Settings configuration system for ViloxTerm.

Provides configurable settings storage locations and formats based on
command line arguments or environment variables.
"""

import os
import sys
import argparse
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Union
import logging
from PySide6.QtCore import QSettings

logger = logging.getLogger(__name__)


class SettingsConfig:
    """
    Centralized settings configuration manager.
    
    Handles custom settings locations, formats, and provides a consistent
    interface for all components to access settings.
    """
    
    _instance: Optional['SettingsConfig'] = None
    _initialized: bool = False
    
    def __init__(self):
        """Initialize settings configuration."""
        if SettingsConfig._initialized:
            raise RuntimeError("SettingsConfig is a singleton. Use get_instance()")
        
        self.settings_dir: Optional[Path] = None
        self.settings_file: Optional[Path] = None
        self.is_portable: bool = False
        self.is_temporary: bool = False
        self.temp_dir: Optional[Path] = None
        self.original_settings_dir: Optional[Path] = None
        
        SettingsConfig._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'SettingsConfig':
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def initialize_from_args(cls, args: Optional[argparse.Namespace] = None) -> 'SettingsConfig':
        """
        Initialize settings configuration from command line arguments.
        
        Args:
            args: Parsed command line arguments, or None to parse from sys.argv
            
        Returns:
            The singleton SettingsConfig instance
        """
        instance = cls.get_instance()
        
        if args is None:
            # Parse arguments ourselves
            parser = cls._create_argument_parser()
            args, _ = parser.parse_known_args()
        
        instance._configure_from_args(args)
        return instance
    
    @staticmethod
    def _create_argument_parser() -> argparse.ArgumentParser:
        """Create argument parser for settings options."""
        parser = argparse.ArgumentParser(add_help=False)  # Don't interfere with main arg parsing
        
        settings_group = parser.add_argument_group('Settings Options')
        
        settings_group.add_argument(
            '--settings-dir',
            type=Path,
            help='Custom directory for storing settings files'
        )
        
        settings_group.add_argument(
            '--settings-file',
            type=Path,
            help='Specific settings file path (INI format)'
        )
        
        settings_group.add_argument(
            '--portable',
            action='store_true',
            help='Use portable settings (store in application directory)'
        )
        
        settings_group.add_argument(
            '--temp-settings',
            action='store_true',
            help='Use temporary settings (don\'t persist after app closes)'
        )
        
        settings_group.add_argument(
            '--reset-settings',
            action='store_true',
            help='Reset all settings to defaults before starting'
        )
        
        return parser
    
    def _configure_from_args(self, args: argparse.Namespace) -> None:
        """Configure settings based on parsed arguments and environment variables."""
        # Handle reset first
        if getattr(args, 'reset_settings', False):
            self.reset_all_settings()
            logger.info("Settings reset to defaults")
        
        # Handle temporary settings
        if getattr(args, 'temp_settings', False) or os.getenv('VILOAPP_TEMP_SETTINGS'):
            self.is_temporary = True
            self.temp_dir = Path(tempfile.mkdtemp(prefix='viloapp_settings_'))
            source = "command line" if getattr(args, 'temp_settings', False) else "environment variable"
            logger.info(f"Using temporary settings in: {self.temp_dir} (from {source})")
            return
        
        # Handle portable mode
        if getattr(args, 'portable', False) or os.getenv('VILOAPP_PORTABLE'):
            self.is_portable = True
            app_dir = Path(__file__).parent.parent.parent  # Go up to project root
            self.settings_dir = app_dir / 'settings'
            self.settings_dir.mkdir(exist_ok=True)
            source = "command line" if getattr(args, 'portable', False) else "environment variable"
            logger.info(f"Using portable settings in: {self.settings_dir} (from {source})")
            return
        
        # Handle custom settings file (command line takes precedence over env var)
        settings_file = None
        if hasattr(args, 'settings_file') and args.settings_file:
            settings_file = args.settings_file
            source = "command line"
        elif os.getenv('VILOAPP_SETTINGS_FILE'):
            settings_file = Path(os.getenv('VILOAPP_SETTINGS_FILE'))
            source = "environment variable"
        
        if settings_file:
            self.settings_file = Path(settings_file).resolve()
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using custom settings file: {self.settings_file} (from {source})")
            return
        
        # Handle custom settings directory (command line takes precedence over env var)
        settings_dir = None
        if hasattr(args, 'settings_dir') and args.settings_dir:
            settings_dir = args.settings_dir
            source = "command line"
        elif os.getenv('VILOAPP_SETTINGS_DIR'):
            settings_dir = Path(os.getenv('VILOAPP_SETTINGS_DIR'))
            source = "environment variable"
        
        if settings_dir:
            self.settings_dir = Path(settings_dir).resolve()
            self.settings_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using custom settings directory: {self.settings_dir} (from {source})")
            return
        
        # Default behavior - use system default
        logger.info("Using system default settings location")
    
    def create_settings(self, organization: str = "ViloxTerm", application: str = "ViloxTerm") -> QSettings:
        """
        Create a QSettings instance with the configured location.
        
        Args:
            organization: Organization name for settings
            application: Application name for settings
            
        Returns:
            Configured QSettings instance
        """
        if self.is_temporary and self.temp_dir:
            # Use INI format in temporary directory
            settings_file = self.temp_dir / f"{organization}_{application}.ini"
            return QSettings(str(settings_file), QSettings.IniFormat)
        
        elif self.settings_file:
            # Use specific file
            return QSettings(str(self.settings_file), QSettings.IniFormat)
        
        elif self.settings_dir:
            # Use custom directory with INI format
            settings_file = self.settings_dir / f"{organization}_{application}.ini"
            return QSettings(str(settings_file), QSettings.IniFormat)
        
        else:
            # Use system default (registry on Windows, files on Linux/Mac)
            return QSettings(organization, application)
    
    def get_settings_location(self) -> str:
        """
        Get a human-readable description of where settings are stored.
        
        Returns:
            Description of settings location
        """
        if self.is_temporary and self.temp_dir:
            return f"Temporary directory: {self.temp_dir}"
        elif self.settings_file:
            return f"Custom file: {self.settings_file}"
        elif self.settings_dir:
            return f"Custom directory: {self.settings_dir}"
        else:
            # Try to determine system default location
            temp_settings = QSettings("ViloxTerm", "ViloxTerm")
            return f"System default: {temp_settings.fileName()}"
    
    def reset_all_settings(self) -> None:
        """Reset all application settings to defaults."""
        settings_domains = [
            ("ViloxTerm", "ViloxTerm"),      # Main application
            ("ViloxTerm", "State"),        # State service  
            ("ViloxTerm", "UI"),           # UI service
            ("ViloxTerm", "Editor"),       # Editor service
            ("ViloxTerm", "CommandPalette") # Command palette
        ]
        
        for org, app in settings_domains:
            settings = self.create_settings(org, app)
            settings.clear()
            settings.sync()
            logger.info(f"Cleared settings for {org}/{app}")
    
    def backup_settings(self, backup_dir: Union[str, Path]) -> None:
        """
        Create a backup of current settings.
        
        Args:
            backup_dir: Directory to store backup files
        """
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        settings_domains = [
            ("ViloxTerm", "ViloxTerm"),
            ("ViloxTerm", "State"),
            ("ViloxTerm", "UI"),
            ("ViloxTerm", "Editor"),
            ("ViloxTerm", "CommandPalette")
        ]
        
        for org, app in settings_domains:
            settings = self.create_settings(org, app)
            if settings.fileName():  # Only for file-based settings
                source_file = Path(settings.fileName())
                if source_file.exists():
                    dest_file = backup_path / f"{org}_{app}.ini.bak"
                    shutil.copy2(source_file, dest_file)
                    logger.info(f"Backed up {org}/{app} to {dest_file}")
    
    def cleanup(self) -> None:
        """Cleanup temporary resources."""
        if self.is_temporary and self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary settings directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary directory: {e}")


# Convenience functions for common usage patterns
def get_settings(organization: str = "ViloxTerm", application: str = "ViloxTerm") -> QSettings:
    """
    Get a QSettings instance using the configured settings location.
    
    This is the main function that all components should use instead of
    creating QSettings directly.
    
    Args:
        organization: Organization name
        application: Application name
        
    Returns:
        Configured QSettings instance
    """
    config = SettingsConfig.get_instance()
    return config.create_settings(organization, application)


def initialize_settings_from_cli() -> SettingsConfig:
    """
    Initialize settings configuration from command line arguments.
    
    Should be called early in application startup.
    
    Returns:
        The configured SettingsConfig instance
    """
    return SettingsConfig.initialize_from_args()


def get_settings_info() -> Dict[str, Any]:
    """
    Get information about current settings configuration.
    
    Returns:
        Dictionary with settings configuration details
    """
    config = SettingsConfig.get_instance()
    return {
        'location': config.get_settings_location(),
        'is_portable': config.is_portable,
        'is_temporary': config.is_temporary,
        'custom_dir': str(config.settings_dir) if config.settings_dir else None,
        'custom_file': str(config.settings_file) if config.settings_file else None,
    }