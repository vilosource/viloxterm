#!/usr/bin/env python3
"""
Centralized logging configuration for ViloxTerm.

This module provides dictionary-based logging configuration that automatically
adjusts based on whether the application is running in development or production mode.

Usage:
    from logging_config import setup_logging
    setup_logging()
"""

import logging.config
import os
import sys
from pathlib import Path
from typing import Any, Optional


def get_log_level(production_mode: bool = False) -> str:
    """
    Determine the default log level based on mode.

    Args:
        production_mode: Whether running in production mode

    Returns:
        Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Check environment variable override first
    env_level = os.environ.get('VILOAPP_LOG_LEVEL', '').upper()
    if env_level in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
        return env_level

    # Default based on mode
    return 'INFO' if production_mode else 'DEBUG'


def get_log_file_path() -> Optional[Path]:
    """
    Get the path for log files.

    Returns:
        Path to log directory or None if file logging is disabled
    """
    # Check if file logging is disabled
    if os.environ.get('VILOAPP_NO_FILE_LOG', '').lower() in ('1', 'true', 'yes'):
        return None

    # Check for custom log directory
    log_dir = os.environ.get('VILOAPP_LOG_DIR')
    if log_dir:
        return Path(log_dir)

    # Default log directory
    if sys.platform == 'win32':
        log_dir = Path(os.environ.get('LOCALAPPDATA', '')) / 'ViloxTerm' / 'logs'
    else:
        log_dir = Path.home() / '.local' / 'share' / 'ViloxTerm' / 'logs'

    return log_dir


def get_logging_config(production_mode: bool = False) -> dict[str, Any]:
    """
    Generate logging configuration dictionary.

    Args:
        production_mode: Whether running in production mode

    Returns:
        Dictionary configuration for logging.config.dictConfig()
    """
    log_level = get_log_level(production_mode)
    log_file_path = get_log_file_path()

    # Base configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s - %(name)s - %(message)s'
            },
            'production': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'production' if production_mode else 'detailed',
                'stream': 'ext://sys.stdout'
            }
        },
        'loggers': {
            # Core modules
            'core': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'core.commands': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'core.keyboard': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'core.settings': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'core.context': {
                'level': 'INFO' if production_mode else 'DEBUG',
                'handlers': ['console'],
                'propagate': False
            },

            # UI modules
            'ui': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'ui.terminal': {
                'level': 'INFO' if production_mode else 'DEBUG',
                'handlers': ['console'],
                'propagate': False
            },
            'ui.widgets': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'ui.command_palette': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },

            # Services
            'services': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },

            # Silence noisy third-party libraries in production
            'werkzeug': {
                'level': 'WARNING' if production_mode else 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'engineio': {
                'level': 'WARNING' if production_mode else 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'socketio': {
                'level': 'WARNING' if production_mode else 'INFO',
                'handlers': ['console'],
                'propagate': False
            }
        },
        'root': {
            'level': log_level,
            'handlers': ['console']
        }
    }

    # Add file handler if enabled
    if log_file_path:
        # Create log directory if it doesn't exist
        log_file_path.mkdir(parents=True, exist_ok=True)
        log_file = log_file_path / 'viloxterm.log'

        config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': 'detailed',
            'filename': str(log_file),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8'
        }

        # Add file handler to all loggers
        for logger_config in config['loggers'].values():
            if 'file' not in logger_config['handlers']:
                logger_config['handlers'].append('file')
        config['root']['handlers'].append('file')

    # Try to use colorlog for colored console output in development
    if not production_mode:
        try:
            import colorlog
            config['formatters']['colored'] = {
                '()': 'colorlog.ColoredFormatter',
                'format': '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
                'log_colors': {
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            }
            config['handlers']['console']['formatter'] = 'colored'
        except ImportError:
            # colorlog not available, use regular formatter
            pass

    return config


def setup_logging(production_mode: Optional[bool] = None):
    """
    Set up logging configuration for the application.

    Args:
        production_mode: Whether running in production mode.
                        If None, will be auto-detected from app_config.
    """
    # Auto-detect production mode if not specified
    if production_mode is None:
        try:
            from core.app_config import app_config
            production_mode = app_config.production_mode
        except ImportError:
            # Fallback to environment variable check
            production_mode = os.environ.get('VILOAPP_PRODUCTION', '').lower() in ('1', 'true', 'yes')

    # Get and apply configuration
    config = get_logging_config(production_mode)
    logging.config.dictConfig(config)

    # Log the configuration being used
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured: mode=%s, level=%s, file_logging=%s",
        'PRODUCTION' if production_mode else 'DEVELOPMENT',
        get_log_level(production_mode),
        'ENABLED' if get_log_file_path() else 'DISABLED'
    )


def set_module_log_level(module_name: str, level: str):
    """
    Set log level for a specific module at runtime.

    Args:
        module_name: Name of the module (e.g., 'core.commands')
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger = logging.getLogger(module_name)
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Also update handlers if they exist
    for handler in logger.handlers:
        handler.setLevel(numeric_level)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    This is a convenience wrapper around logging.getLogger that ensures
    the logging system is properly configured.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Environment variable documentation
"""
Environment Variables for Logging Configuration:

VILOAPP_LOG_LEVEL: Set the default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
VILOAPP_LOG_DIR: Custom directory for log files
VILOAPP_NO_FILE_LOG: Set to 1/true/yes to disable file logging
VILOAPP_PRODUCTION: Set to 1/true/yes to use production logging configuration

Examples:
    # Enable debug logging in production
    VILOAPP_PRODUCTION=1 VILOAPP_LOG_LEVEL=DEBUG ./ViloxTerm

    # Disable file logging
    VILOAPP_NO_FILE_LOG=1 ./ViloxTerm

    # Custom log directory
    VILOAPP_LOG_DIR=/var/log/viloxterm ./ViloxTerm
"""
