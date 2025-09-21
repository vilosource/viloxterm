"""Main CLI entry point for ViloxTerm Plugin Development Tool."""

import sys
from pathlib import Path

import click
from click import Context

from . import __version__
from .commands import create_plugin, dev, install, list_plugins, package, test
from .config import CLIConfig


@click.group()
@click.version_option(__version__)
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.pass_context
def cli(ctx: Context, config: Path | None, verbose: bool, debug: bool) -> None:
    """ViloxTerm Plugin Development CLI Tool.

    A comprehensive tool for creating, developing, testing, and managing
    ViloxTerm plugins.
    """
    # Initialize CLI configuration
    cli_config = CLIConfig(config_path=config)
    cli_config.verbose = verbose
    cli_config.debug = debug

    # Store config in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["config"] = cli_config


@cli.command()
@click.argument("name")
@click.option(
    "--template",
    type=click.Choice(["basic", "widget", "service", "command"]),
    default="basic",
    help="Plugin template to use"
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path.cwd(),
    help="Output directory for the new plugin"
)
@click.pass_context
def create(ctx: Context, name: str, template: str, output_dir: Path) -> None:
    """Create a new plugin from template."""
    config = ctx.obj["config"]
    create_plugin.create_plugin(config, name, template, output_dir)


@cli.command()
@click.option(
    "--plugin",
    type=click.Path(exists=True, path_type=Path),
    default=Path.cwd(),
    help="Path to plugin directory"
)
@click.option("--port", type=int, default=8080, help="Development server port")
@click.option("--reload/--no-reload", default=True, help="Enable hot reload")
@click.pass_context
def dev(ctx: Context, plugin: Path, port: int, reload: bool) -> None:
    """Run plugin in development mode with hot reload."""
    config = ctx.obj["config"]
    dev.run_dev_mode(config, plugin, port, reload)


@cli.command("test")
@click.argument("plugin", type=click.Path(exists=True, path_type=Path))
@click.option("--coverage", is_flag=True, help="Generate coverage report")
@click.option("--verbose", "-v", is_flag=True, help="Verbose test output")
@click.pass_context
def test_cmd(ctx: Context, plugin: Path, coverage: bool, verbose: bool) -> None:
    """Run tests for a plugin."""
    config = ctx.obj["config"]
    test.run_tests(config, plugin, coverage, verbose)


@cli.command()
@click.argument("plugin", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    help="Output file for the package"
)
@click.option("--format", type=click.Choice(["zip", "tar.gz"]), default="zip")
@click.pass_context
def package(ctx: Context, plugin: Path, output: Path | None, format: str) -> None:
    """Package a plugin for distribution."""
    config = ctx.obj["config"]
    package.package_plugin(config, plugin, output, format)


@cli.command()
@click.argument("plugin", type=click.Path(exists=True, path_type=Path))
@click.option("--force", is_flag=True, help="Force installation if plugin exists")
@click.pass_context
def install(ctx: Context, plugin: Path, force: bool) -> None:
    """Install a plugin."""
    config = ctx.obj["config"]
    install.install_plugin(config, plugin, force)


@cli.command("list")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.option("--format", type=click.Choice(["table", "json"]), default="table")
@click.pass_context
def list_cmd(ctx: Context, verbose: bool, format: str) -> None:
    """List installed plugins."""
    config = ctx.obj["config"]
    list_plugins.list_installed_plugins(config, verbose, format)


def main() -> int:
    """Main entry point for the CLI."""
    try:
        cli()
        return 0
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
