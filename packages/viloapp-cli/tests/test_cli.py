"""Tests for CLI commands."""

import pytest
import tempfile
import json
from pathlib import Path
from click.testing import CliRunner

from viloapp_cli.cli import cli


class TestCLI:
    """Test CLI commands."""

    def test_cli_help(self):
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'ViloxTerm Plugin Development CLI Tool' in result.output

    def test_cli_version(self):
        """Test CLI version command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert '0.1.0' in result.output


class TestCreateCommand:
    """Test create command."""

    def test_create_basic_plugin(self):
        """Test creating a basic plugin."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = runner.invoke(cli, [
                'create', 'test-plugin',
                '--template', 'basic',
                '--output-dir', str(temp_path)
            ])

            assert result.exit_code == 0
            assert 'Plugin \'test-plugin\' created successfully' in result.output

            # Check that plugin directory was created
            plugin_dir = temp_path / 'test-plugin'
            assert plugin_dir.exists()

            # Check essential files
            assert (plugin_dir / 'plugin.json').exists()
            assert (plugin_dir / 'pyproject.toml').exists()
            assert (plugin_dir / 'README.md').exists()
            assert (plugin_dir / 'src' / 'test-plugin' / '__init__.py').exists()
            assert (plugin_dir / 'src' / 'test-plugin' / 'plugin.py').exists()
            assert (plugin_dir / 'tests' / 'test_plugin.py').exists()

    def test_create_widget_plugin(self):
        """Test creating a widget plugin."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = runner.invoke(cli, [
                'create', 'widget-plugin',
                '--template', 'widget',
                '--output-dir', str(temp_path)
            ])

            assert result.exit_code == 0

            plugin_dir = temp_path / 'widget-plugin'
            assert plugin_dir.exists()

            # Check widget-specific files
            assert (plugin_dir / 'src' / 'widget-plugin' / 'widget.py').exists()
            assert (plugin_dir / 'tests' / 'test_widget.py').exists()
            assert (plugin_dir / 'resources').exists()

    def test_create_plugin_already_exists(self):
        """Test creating plugin when directory already exists."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create the first plugin
            result1 = runner.invoke(cli, [
                'create', 'test-plugin',
                '--output-dir', str(temp_path)
            ])
            assert result1.exit_code == 0

            # Try to create the same plugin again
            result2 = runner.invoke(cli, [
                'create', 'test-plugin',
                '--output-dir', str(temp_path)
            ])
            assert result2.exit_code != 0
            assert 'already exists' in result2.output

    def test_create_plugin_manifest_content(self):
        """Test that plugin manifest is created with correct content."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = runner.invoke(cli, [
                'create', 'my-awesome-plugin',
                '--template', 'basic',
                '--output-dir', str(temp_path)
            ])

            assert result.exit_code == 0

            plugin_dir = temp_path / 'my-awesome-plugin'
            manifest_file = plugin_dir / 'plugin.json'

            with open(manifest_file) as f:
                manifest = json.load(f)

            assert manifest['id'] == 'viloapp.my-awesome-plugin'
            assert manifest['name'] == 'my-awesome-plugin'
            assert manifest['version'] == '0.1.0'


class TestListCommand:
    """Test list command."""

    def test_list_no_plugins(self):
        """Test list command when no plugins are installed."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Set custom config directory
            config_file = Path(temp_dir) / "config.yaml"
            config_file.write_text(f"""
plugins:
  directory: {temp_dir}/plugins
""")

            result = runner.invoke(cli, [
                '--config', str(config_file),
                'list'
            ])

            assert result.exit_code == 0
            assert 'No plugins installed' in result.output

    def test_list_json_format(self):
        """Test list command with JSON format."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            config_file.write_text(f"""
plugins:
  directory: {temp_dir}/plugins
""")

            result = runner.invoke(cli, [
                '--config', str(config_file),
                'list',
                '--format', 'json'
            ])

            assert result.exit_code == 0
            # Should be valid JSON even with no plugins
            import json
            try:
                json.loads(result.output)
            except json.JSONDecodeError:
                pytest.fail("Output is not valid JSON")


class TestPackageCommand:
    """Test package command."""

    def test_package_nonexistent_plugin(self):
        """Test packaging a plugin that doesn't exist."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_path = Path(temp_dir) / "nonexistent"
            result = runner.invoke(cli, [
                'package', str(nonexistent_path)
            ])

            assert result.exit_code != 0
            assert 'does not exist' in result.output

    def test_package_invalid_plugin(self):
        """Test packaging a directory without plugin.json."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            invalid_dir = temp_path / "invalid-plugin"
            invalid_dir.mkdir()

            result = runner.invoke(cli, [
                'package', str(invalid_dir)
            ])

            assert result.exit_code != 0
            assert 'plugin.json not found' in result.output


class TestTestCommand:
    """Test test command."""

    def test_test_nonexistent_plugin(self):
        """Test running tests for a plugin that doesn't exist."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_path = Path(temp_dir) / "nonexistent"
            result = runner.invoke(cli, [
                'test', str(nonexistent_path)
            ])

            assert result.exit_code != 0
            assert 'does not exist' in result.output


class TestDevCommand:
    """Test dev command."""

    def test_dev_nonexistent_plugin(self):
        """Test dev mode for a plugin that doesn't exist."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_path = Path(temp_dir) / "nonexistent"
            result = runner.invoke(cli, [
                'dev',
                '--plugin', str(nonexistent_path)
            ])

            assert result.exit_code != 0
            assert 'does not exist' in result.output