"""List plugins command implementation."""

import json
from pathlib import Path
from typing import Dict, Any, List

import click

from ..config import CLIConfig


def list_installed_plugins(config: CLIConfig, verbose: bool, format: str) -> None:
    """List installed plugins.

    Args:
        config: CLI configuration
        verbose: Whether to show detailed information
        format: Output format (table or json)
    """
    try:
        config.ensure_directories()
        plugins_dir = config.get_plugins_directory()
        registry_file = plugins_dir / "registry.json"

        # Load plugin registry
        plugins = _load_plugin_registry(registry_file)

        if not plugins:
            click.echo("No plugins installed.")
            return

        # Output in requested format
        if format == "json":
            _output_json(plugins, verbose)
        else:
            _output_table(plugins, verbose)

    except Exception as e:
        raise click.ClickException(f"Failed to list plugins: {e}")


def _load_plugin_registry(registry_file: Path) -> Dict[str, Any]:
    """Load plugin registry from file.

    Args:
        registry_file: Path to registry file

    Returns:
        Dictionary of plugins
    """
    if not registry_file.exists():
        return {}

    try:
        with open(registry_file) as f:
            registry = json.load(f)
        return registry.get("plugins", {})
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _output_table(plugins: Dict[str, Any], verbose: bool) -> None:
    """Output plugins in table format.

    Args:
        plugins: Plugin data
        verbose: Whether to show detailed information
    """
    if verbose:
        click.echo("📦 Installed Plugins (Detailed)")
        click.echo("=" * 80)

        for plugin_id, plugin_data in plugins.items():
            click.echo(f"\n🔌 {plugin_data.get('name', 'Unknown')}")
            click.echo(f"   ID: {plugin_id}")
            click.echo(f"   Version: {plugin_data.get('version', 'Unknown')}")
            click.echo(f"   Path: {plugin_data.get('path', 'Unknown')}")

            manifest = plugin_data.get('manifest', {})
            if 'description' in manifest:
                click.echo(f"   Description: {manifest['description']}")

            if 'author' in manifest:
                author = manifest['author']
                if isinstance(author, dict):
                    author_str = author.get('name', 'Unknown')
                    if 'email' in author:
                        author_str += f" <{author['email']}>"
                else:
                    author_str = str(author)
                click.echo(f"   Author: {author_str}")

            # Show contributions
            contributes = manifest.get('contributes', {})
            if contributes:
                click.echo("   Contributes:")
                for contrib_type, items in contributes.items():
                    if items:
                        click.echo(f"     {contrib_type.title()}: {len(items)} item(s)")

            # Check if path exists
            plugin_path = Path(plugin_data.get('path', ''))
            if not plugin_path.exists():
                click.echo("   ⚠️  Plugin path does not exist!")

    else:
        # Simple table format
        click.echo("📦 Installed Plugins")
        click.echo("-" * 80)
        click.echo(f"{'Name':<25} {'ID':<30} {'Version':<15}")
        click.echo("-" * 80)

        for plugin_id, plugin_data in plugins.items():
            name = plugin_data.get('name', 'Unknown')
            version = plugin_data.get('version', 'Unknown')

            # Truncate long names
            if len(name) > 24:
                name = name[:21] + "..."
            if len(plugin_id) > 29:
                plugin_id = plugin_id[:26] + "..."

            click.echo(f"{name:<25} {plugin_id:<30} {version:<15}")

    click.echo(f"\nTotal: {len(plugins)} plugin(s)")


def _output_json(plugins: Dict[str, Any], verbose: bool) -> None:
    """Output plugins in JSON format.

    Args:
        plugins: Plugin data
        verbose: Whether to show detailed information
    """
    if verbose:
        # Full plugin data
        output = {
            "plugins": plugins,
            "total": len(plugins)
        }
    else:
        # Simplified data
        simplified = {}
        for plugin_id, plugin_data in plugins.items():
            simplified[plugin_id] = {
                "name": plugin_data.get("name", "Unknown"),
                "version": plugin_data.get("version", "Unknown"),
                "path": plugin_data.get("path", "Unknown")
            }

        output = {
            "plugins": simplified,
            "total": len(plugins)
        }

    click.echo(json.dumps(output, indent=2))