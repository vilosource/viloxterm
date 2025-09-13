#!/usr/bin/env python3
"""
Version management for ViloxTerm.

This module provides centralized version information for the application.
Following Semantic Versioning 2.0.0: MAJOR.MINOR.PATCH

Version Format:
- MAJOR: Incompatible API changes
- MINOR: Backwards-compatible functionality additions
- PATCH: Backwards-compatible bug fixes
- Additional labels for pre-release and build metadata
"""

import os
import subprocess
from typing import Optional, Dict, Any
from datetime import datetime

# Semantic Version
__version__ = "0.1.0"
__version_info__ = (0, 1, 0)

# Application Details
APP_NAME = "ViloxTerm"
APP_DESCRIPTION = "A modern, VSCode-inspired terminal application"
APP_AUTHOR = "ViloxTerm Contributors"
APP_URL = "https://github.com/viloapp/viloxterm"
APP_LICENSE = "MIT"
APP_COPYRIGHT = f"© {datetime.now().year} {APP_AUTHOR}"

# Build Information
BUILD_DATE = datetime.now().strftime("%Y-%m-%d")
BUILD_TIME = datetime.now().strftime("%H:%M:%S")


def get_git_info() -> Dict[str, Optional[str]]:
    """
    Get git repository information if available.

    Returns:
        Dictionary with git commit hash, branch, and dirty status
    """
    info = {
        'commit': None,
        'commit_short': None,
        'branch': None,
        'dirty': False,
        'tag': None
    }

    try:
        # Get commit hash
        commit = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        info['commit'] = commit
        info['commit_short'] = commit[:7]

        # Get branch name
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        info['branch'] = branch

        # Check if working directory is dirty
        status = subprocess.check_output(
            ['git', 'status', '--porcelain'],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        info['dirty'] = bool(status)

        # Get current tag if on a tag
        try:
            tag = subprocess.check_output(
                ['git', 'describe', '--exact-match', '--tags', 'HEAD'],
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
            info['tag'] = tag
        except subprocess.CalledProcessError:
            pass

    except (subprocess.CalledProcessError, FileNotFoundError):
        # Git not available or not in a git repository
        pass

    return info


def get_version_string(include_git: bool = True,
                       include_dev: bool = True) -> str:
    """
    Get a formatted version string.

    Args:
        include_git: Include git information if available
        include_dev: Include development mode indicator

    Returns:
        Formatted version string
    """
    from core.app_config import app_config

    version = f"v{__version__}"

    if include_dev and app_config.dev_mode:
        version += "-dev"

    if include_git:
        git_info = get_git_info()
        if git_info['commit_short']:
            version += f"+{git_info['commit_short']}"
            if git_info['dirty']:
                version += ".dirty"

    return version


def get_full_version_info() -> Dict[str, Any]:
    """
    Get complete version information including build and git details.

    Returns:
        Dictionary with all version information
    """
    from core.app_config import app_config

    git_info = get_git_info()

    return {
        'version': __version__,
        'version_tuple': __version_info__,
        'version_string': get_version_string(),
        'app_name': APP_NAME,
        'app_description': APP_DESCRIPTION,
        'app_author': APP_AUTHOR,
        'app_url': APP_URL,
        'app_license': APP_LICENSE,
        'app_copyright': APP_COPYRIGHT,
        'build_date': BUILD_DATE,
        'build_time': BUILD_TIME,
        'dev_mode': app_config.dev_mode,
        'production_mode': app_config.production_mode,
        'git': git_info,
        'python_version': get_python_version(),
        'qt_version': get_qt_version(),
        'platform': get_platform_info()
    }


def get_python_version() -> str:
    """Get Python version string."""
    import sys
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_qt_version() -> Dict[str, str]:
    """Get Qt and PySide6 version information."""
    try:
        from PySide6 import __version__ as pyside_version
        from PySide6.QtCore import qVersion
        return {
            'pyside': pyside_version,
            'qt': qVersion()
        }
    except ImportError:
        return {
            'pyside': 'Unknown',
            'qt': 'Unknown'
        }


def get_platform_info() -> Dict[str, str]:
    """Get platform information."""
    import platform
    return {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_implementation': platform.python_implementation()
    }


def format_version_for_display() -> str:
    """
    Format version information for display in UI.

    Returns:
        Multi-line string with version details
    """
    info = get_full_version_info()

    lines = [
        f"{info['app_name']} {info['version_string']}",
        f"{info['app_description']}",
        "",
        f"Build Date: {info['build_date']} {info['build_time']}"
    ]

    if info['git']['commit_short']:
        git_line = f"Git: {info['git']['branch']} @ {info['git']['commit_short']}"
        if info['git']['dirty']:
            git_line += " (modified)"
        lines.append(git_line)

    lines.extend([
        "",
        f"Python: {info['python_version']}",
        f"Qt: {info['qt_version']['qt']}",
        f"PySide6: {info['qt_version']['pyside']}",
        f"Platform: {info['platform']['system']} {info['platform']['release']}"
    ])

    if info['dev_mode']:
        lines.extend(["", "⚠️ Development Mode"])

    return "\n".join(lines)


# Version check utilities
def parse_version(version_str: str) -> tuple:
    """Parse a version string into a tuple."""
    try:
        parts = version_str.strip('v').split('.')
        return tuple(int(p) for p in parts[:3])
    except (ValueError, IndexError):
        return (0, 0, 0)


def compare_versions(v1: str, v2: str) -> int:
    """
    Compare two version strings.

    Returns:
        -1 if v1 < v2, 0 if equal, 1 if v1 > v2
    """
    t1 = parse_version(v1)
    t2 = parse_version(v2)

    if t1 < t2:
        return -1
    elif t1 > t2:
        return 1
    else:
        return 0