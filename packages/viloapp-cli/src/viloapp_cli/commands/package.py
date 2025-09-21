"""Package command implementation."""

import json
import tarfile
import zipfile
from pathlib import Path

import click

from ..config import CLIConfig


def package_plugin(
    config: CLIConfig, plugin_path: Path, output: Path | None, format: str
) -> None:
    """Package a plugin for distribution.

    Args:
        config: CLI configuration
        plugin_path: Path to plugin directory
        output: Output file path (optional)
        format: Package format (zip or tar.gz)
    """
    try:
        # Validate plugin directory
        manifest = _validate_and_get_manifest(plugin_path)

        # Determine output file name
        if output is None:
            plugin_name = manifest.get("name", plugin_path.name)
            plugin_version = manifest.get("version", "0.1.0")
            safe_name = plugin_name.replace(" ", "-").lower()
            extension = "zip" if format == "zip" else "tar.gz"
            output = plugin_path.parent / f"{safe_name}-{plugin_version}.{extension}"

        click.echo(f"📦 Packaging plugin: {manifest.get('name', 'Unknown')}")
        click.echo(f"   Version: {manifest.get('version', 'Unknown')}")
        click.echo(f"   Format: {format}")
        click.echo(f"   Output: {output}")

        # Create package
        if format == "zip":
            _create_zip_package(plugin_path, output, config)
        elif format == "tar.gz":
            _create_tar_package(plugin_path, output, config)

        click.echo(f"✅ Package created successfully: {output}")
        click.echo(f"   Size: {_format_size(output.stat().st_size)}")

    except Exception as e:
        raise click.ClickException(f"Failed to package plugin: {e}")


def _validate_and_get_manifest(plugin_path: Path) -> dict:
    """Validate plugin directory and return manifest.

    Args:
        plugin_path: Path to plugin directory

    Returns:
        Plugin manifest data

    Raises:
        click.ClickException: If validation fails
    """
    if not plugin_path.exists():
        raise click.ClickException(f"Plugin directory does not exist: {plugin_path}")

    plugin_json = plugin_path / "plugin.json"
    if not plugin_json.exists():
        raise click.ClickException(f"plugin.json not found in {plugin_path}")

    try:
        with open(plugin_json) as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid plugin.json: {e}")

    # Validate required fields
    required_fields = ["id", "name", "version"]
    for field in required_fields:
        if field not in manifest:
            raise click.ClickException(f"Missing required field in plugin.json: {field}")

    return manifest


def _get_files_to_package(plugin_path: Path, config: CLIConfig) -> list[Path]:
    """Get list of files to include in package.

    Args:
        plugin_path: Path to plugin directory
        config: CLI configuration

    Returns:
        List of file paths to package
    """
    include_patterns = config.get("packaging.include_patterns", [
        "*.py", "*.json", "*.yaml", "*.yml", "*.md", "*.txt", "*.toml"
    ])
    exclude_patterns = config.get("packaging.exclude_patterns", [
        "__pycache__", "*.pyc", ".git", ".pytest_cache", "htmlcov",
        ".coverage", ".mypy_cache", ".ruff_cache", "*.egg-info",
        "build", "dist", ".viloapp_dev.py"
    ])

    files_to_package = []

    for file_path in plugin_path.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(plugin_path)

            # Check exclude patterns
            should_exclude = False
            for pattern in exclude_patterns:
                if _matches_pattern(relative_path, pattern):
                    should_exclude = True
                    break

            if should_exclude:
                continue

            # Check include patterns
            should_include = False
            for pattern in include_patterns:
                if _matches_pattern(relative_path, pattern):
                    should_include = True
                    break

            if should_include:
                files_to_package.append(file_path)

    return files_to_package


def _matches_pattern(path: Path, pattern: str) -> bool:
    """Check if path matches a pattern.

    Args:
        path: Path to check
        pattern: Glob pattern

    Returns:
        True if path matches pattern
    """
    import fnmatch
    return any(
        fnmatch.fnmatch(str(part), pattern)
        for part in [path] + list(path.parents)
    )


def _create_zip_package(plugin_path: Path, output: Path, config: CLIConfig) -> None:
    """Create ZIP package.

    Args:
        plugin_path: Path to plugin directory
        output: Output file path
        config: CLI configuration
    """
    files_to_package = _get_files_to_package(plugin_path, config)

    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in files_to_package:
            arc_name = file_path.relative_to(plugin_path)
            zf.write(file_path, arc_name)

            if config.verbose:
                click.echo(f"   Added: {arc_name}")


def _create_tar_package(plugin_path: Path, output: Path, config: CLIConfig) -> None:
    """Create TAR.GZ package.

    Args:
        plugin_path: Path to plugin directory
        output: Output file path
        config: CLI configuration
    """
    files_to_package = _get_files_to_package(plugin_path, config)

    with tarfile.open(output, 'w:gz') as tf:
        for file_path in files_to_package:
            arc_name = file_path.relative_to(plugin_path)
            tf.add(file_path, arc_name)

            if config.verbose:
                click.echo(f"   Added: {arc_name}")


def _format_size(size_bytes: int) -> str:
    """Format file size in human readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
