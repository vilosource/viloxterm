"""Configuration management for ViloxTerm Plugin CLI."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class CLIConfig:
    """Configuration manager for the CLI tool."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """Initialize configuration.

        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path or self._get_default_config_path()
        self.verbose = False
        self.debug = False
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _get_default_config_path(self) -> Path:
        """Get the default configuration file path."""
        config_dir = Path.home() / ".viloapp"
        config_dir.mkdir(exist_ok=True)
        return config_dir / "cli-config.yaml"

    def _load_config(self) -> None:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    self._config = yaml.safe_load(f) or {}
            except Exception as e:
                if self.debug:
                    print(f"Warning: Could not load config file: {e}")
                self._config = self._get_default_config()
        else:
            self._config = self._get_default_config()
            self._save_config()

    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                yaml.dump(self._config, f, default_flow_style=False)
        except Exception as e:
            if self.debug:
                print(f"Warning: Could not save config file: {e}")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "plugins": {
                "directory": str(Path.home() / ".viloapp" / "plugins"),
                "templates_directory": str(Path.home() / ".viloapp" / "templates"),
            },
            "development": {
                "default_port": 8080,
                "hot_reload": True,
                "watch_patterns": ["*.py", "*.json", "*.yaml", "*.yml"],
            },
            "testing": {
                "default_coverage": True,
                "test_patterns": ["test_*.py", "*_test.py"],
            },
            "packaging": {
                "default_format": "zip",
                "include_patterns": ["*.py", "*.json", "*.yaml", "*.yml", "*.md"],
                "exclude_patterns": ["__pycache__", "*.pyc", ".git", ".pytest_cache"],
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        self._save_config()

    def get_plugins_directory(self) -> Path:
        """Get the plugins directory path."""
        return Path(self.get("plugins.directory"))

    def get_templates_directory(self) -> Path:
        """Get the templates directory path."""
        return Path(self.get("plugins.templates_directory"))

    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.get_plugins_directory().mkdir(parents=True, exist_ok=True)
        self.get_templates_directory().mkdir(parents=True, exist_ok=True)