"""Install command implementation."""

import json
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import click

from ..config import CLIConfig


def install_plugin(config: CLIConfig, plugin_path: Path, force: bool) -> None:
    """Install a plugin.

    Args:
        config: CLI configuration
        plugin_path: Path to plugin directory or package file
        force: Whether to force installation if plugin exists
    """
    try:
        config.ensure_directories()
        plugins_dir = config.get_plugins_directory()

        if plugin_path.is_file():
            # Installing from package file
            _install_from_package(plugin_path, plugins_dir, force, config)
        elif plugin_path.is_dir():
            # Installing from directory
            _install_from_directory(plugin_path, plugins_dir, force, config)
        else:
            raise click.ClickException(f"Invalid plugin path: {plugin_path}")

    except Exception as e:
        raise click.ClickException(f"Failed to install plugin: {e}")


def _install_from_package(
    package_path: Path, plugins_dir: Path, force: bool, config: CLIConfig
) -> None:
    """Install plugin from package file.

    Args:
        package_path: Path to package file
        plugins_dir: Plugins directory
        force: Whether to force installation
        config: CLI configuration
    """
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        extract_path = temp_path / "extracted"
        extract_path.mkdir()

        # Extract package
        if package_path.suffix == ".zip":
            with zipfile.ZipFile(package_path, "r") as zf:
                zf.extractall(extract_path)
        elif package_path.name.endswith(".tar.gz"):
            with tarfile.open(package_path, "r:gz") as tf:
                tf.extractall(extract_path)
        else:
            raise click.ClickException(f"Unsupported package format: {package_path.suffix}")

        # Find the plugin directory in extracted content
        plugin_dirs = [d for d in extract_path.iterdir() if d.is_dir()]
        if len(plugin_dirs) == 1:
            extracted_plugin = plugin_dirs[0]
        else:
            # Look for plugin.json in root
            if (extract_path / "plugin.json").exists():
                extracted_plugin = extract_path
            else:
                raise click.ClickException("Could not find plugin directory in package")

        # Install from extracted directory
        _install_from_directory(extracted_plugin, plugins_dir, force, config)


def _install_from_directory(
    plugin_path: Path, plugins_dir: Path, force: bool, config: CLIConfig
) -> None:
    """Install plugin from directory.

    Args:
        plugin_path: Path to plugin directory
        plugins_dir: Plugins directory
        force: Whether to force installation
        config: CLI configuration
    """
    # Validate plugin
    manifest = _validate_and_get_manifest(plugin_path)
    plugin_id = manifest["id"]
    plugin_name = manifest["name"]
    plugin_version = manifest["version"]

    click.echo(f"📦 Installing plugin: {plugin_name}")
    click.echo(f"   ID: {plugin_id}")
    click.echo(f"   Version: {plugin_version}")

    # Check if plugin already exists
    safe_name = plugin_name.replace(" ", "-").lower()
    target_dir = plugins_dir / safe_name

    if target_dir.exists():
        if force:
            click.echo(f"⚠️  Removing existing plugin at {target_dir}")
            shutil.rmtree(target_dir)
        else:
            raise click.ClickException(
                f"Plugin already exists at {target_dir}. Use --force to overwrite."
            )

    # Copy plugin files
    click.echo(f"📂 Copying plugin files to {target_dir}")
    shutil.copytree(plugin_path, target_dir)

    # Install dependencies if pyproject.toml exists
    pyproject_toml = target_dir / "pyproject.toml"
    if pyproject_toml.exists():
        click.echo("📋 Installing plugin dependencies...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", str(target_dir)],
                check=True,
                capture_output=True,
                text=True,
            )
            if config.verbose:
                click.echo(result.stdout)
        except subprocess.CalledProcessError as e:
            click.echo(f"⚠️  Warning: Failed to install dependencies: {e}")
            if config.verbose:
                click.echo(e.stdout)
                click.echo(e.stderr)

    # Create plugin registry entry
    _register_plugin(plugins_dir, manifest, target_dir)

    click.echo(f"✅ Plugin '{plugin_name}' installed successfully!")
    click.echo(f"   Location: {target_dir}")


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


def _register_plugin(plugins_dir: Path, manifest: dict, plugin_path: Path) -> None:
    """Register plugin in the plugin registry.

    Args:
        plugins_dir: Plugins directory
        manifest: Plugin manifest
        plugin_path: Path to installed plugin
    """
    registry_file = plugins_dir / "registry.json"

    # Load existing registry
    if registry_file.exists():
        try:
            with open(registry_file) as f:
                registry = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            registry = {"plugins": {}}
    else:
        registry = {"plugins": {}}

    # Add plugin to registry
    registry["plugins"][manifest["id"]] = {
        "name": manifest["name"],
        "version": manifest["version"],
        "path": str(plugin_path),
        "manifest": manifest,
    }

    # Save registry
    with open(registry_file, "w") as f:
        json.dump(registry, f, indent=2)
