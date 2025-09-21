"""Test command implementation."""

import subprocess
import sys
from pathlib import Path

import click

from ..config import CLIConfig


def run_tests(
    config: CLIConfig, plugin_path: Path, coverage: bool, verbose: bool
) -> None:
    """Run tests for a plugin.

    Args:
        config: CLI configuration
        plugin_path: Path to plugin directory
        coverage: Whether to generate coverage report
        verbose: Whether to enable verbose output
    """
    try:
        # Validate plugin directory
        _validate_plugin_directory(plugin_path)

        click.echo(f"🧪 Running tests for plugin at {plugin_path}")

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]

        # Add test directory
        tests_dir = plugin_path / "tests"
        if tests_dir.exists():
            cmd.append(str(tests_dir))
        else:
            click.echo("⚠️  No tests directory found, running pytest in plugin root")
            cmd.append(str(plugin_path))

        # Add options
        if verbose:
            cmd.append("-v")

        if coverage:
            # Determine package name for coverage
            src_dir = plugin_path / "src"
            if src_dir.exists():
                package_dirs = [d for d in src_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
                if package_dirs:
                    package_name = package_dirs[0].name
                    cmd.extend([
                        "--cov", package_name,
                        "--cov-report", "term-missing",
                        "--cov-report", f"html:{plugin_path}/htmlcov"
                    ])

        # Run tests
        click.echo(f"📋 Command: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=plugin_path)

        if result.returncode == 0:
            click.echo("✅ All tests passed!")
            if coverage:
                htmlcov_dir = plugin_path / "htmlcov"
                if htmlcov_dir.exists():
                    click.echo(f"📊 Coverage report generated at {htmlcov_dir}/index.html")
        else:
            raise click.ClickException(f"Tests failed with exit code {result.returncode}")

    except FileNotFoundError:
        raise click.ClickException(
            "pytest not found. Install it with: pip install pytest"
        )
    except Exception as e:
        raise click.ClickException(f"Failed to run tests: {e}")


def _validate_plugin_directory(plugin_path: Path) -> None:
    """Validate that the plugin directory is valid.

    Args:
        plugin_path: Path to plugin directory

    Raises:
        click.ClickException: If directory is invalid
    """
    if not plugin_path.exists():
        raise click.ClickException(f"Plugin directory does not exist: {plugin_path}")

    plugin_json = plugin_path / "plugin.json"
    if not plugin_json.exists():
        raise click.ClickException(f"plugin.json not found in {plugin_path}")

    # Check if there are any test files
    test_patterns = ["test_*.py", "*_test.py", "tests/"]
    has_tests = False

    for pattern in test_patterns:
        if pattern.endswith("/"):
            # Directory pattern
            if (plugin_path / pattern).exists():
                has_tests = True
                break
        else:
            # File pattern
            if list(plugin_path.rglob(pattern)):
                has_tests = True
                break

    if not has_tests:
        click.echo("⚠️  No test files found. Consider adding tests to ensure plugin quality.")
