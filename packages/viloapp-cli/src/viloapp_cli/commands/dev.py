"""Development mode command implementation."""

import subprocess
import sys
import time
from pathlib import Path

import click
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from ..config import CLIConfig


class PluginReloadHandler(FileSystemEventHandler):
    """File system event handler for plugin reload."""

    def __init__(self, plugin_path: Path, reload_callback) -> None:
        """Initialize the handler.

        Args:
            plugin_path: Path to the plugin directory
            reload_callback: Callback function for reload
        """
        super().__init__()
        self.plugin_path = plugin_path
        self.reload_callback = reload_callback
        self.last_reload_time = 0
        self.debounce_delay = 1.0  # Seconds

    def on_modified(self, event) -> None:
        """Handle file modification events.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only watch relevant files
        if not self._should_watch_file(file_path):
            return

        # Debounce rapid file changes
        current_time = time.time()
        if current_time - self.last_reload_time < self.debounce_delay:
            return

        self.last_reload_time = current_time
        click.echo(f"🔄 File changed: {file_path.relative_to(self.plugin_path)}")
        self.reload_callback()

    def _should_watch_file(self, file_path: Path) -> bool:
        """Check if file should trigger reload.

        Args:
            file_path: Path to the file

        Returns:
            True if file should be watched
        """
        # Watch Python files, config files, and manifests
        watch_extensions = {".py", ".json", ".yaml", ".yml"}
        return file_path.suffix in watch_extensions


def run_dev_mode(
    config: CLIConfig, plugin_path: Path, port: int, reload: bool
) -> None:
    """Run plugin in development mode.

    Args:
        config: CLI configuration
        plugin_path: Path to plugin directory
        port: Development server port
        reload: Whether to enable hot reload
    """
    try:
        # Validate plugin directory
        _validate_plugin_directory(plugin_path)

        click.echo(f"🚀 Starting development mode for plugin at {plugin_path}")
        click.echo(f"   Port: {port}")
        click.echo(f"   Hot reload: {'enabled' if reload else 'disabled'}")

        if reload:
            _run_with_hot_reload(config, plugin_path, port)
        else:
            _run_development_server(config, plugin_path, port)

    except Exception as e:
        raise click.ClickException(f"Failed to start development mode: {e}")


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

    pyproject_toml = plugin_path / "pyproject.toml"
    if not pyproject_toml.exists():
        raise click.ClickException(f"pyproject.toml not found in {plugin_path}")


def _run_with_hot_reload(config: CLIConfig, plugin_path: Path, port: int) -> None:
    """Run development server with hot reload.

    Args:
        config: CLI configuration
        plugin_path: Path to plugin directory
        port: Development server port
    """
    server_process = None

    def reload_plugin():
        """Reload the plugin by restarting the server."""
        nonlocal server_process
        if server_process:
            click.echo("📦 Reloading plugin...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
                server_process.wait()

        server_process = _start_development_server(plugin_path, port)

    # Start initial server
    reload_plugin()

    # Set up file watcher
    event_handler = PluginReloadHandler(plugin_path, reload_plugin)
    observer = Observer()
    observer.schedule(event_handler, str(plugin_path), recursive=True)
    observer.start()

    try:
        click.echo("\n👀 Watching for file changes... Press Ctrl+C to stop")
        while True:
            time.sleep(1)
            if server_process and server_process.poll() is not None:
                # Server died, restart it
                click.echo("⚠️  Development server stopped, restarting...")
                reload_plugin()

    except KeyboardInterrupt:
        click.echo("\n🛑 Stopping development mode...")
    finally:
        observer.stop()
        observer.join()
        if server_process:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
                server_process.wait()


def _run_development_server(config: CLIConfig, plugin_path: Path, port: int) -> None:
    """Run development server without hot reload.

    Args:
        config: CLI configuration
        plugin_path: Path to plugin directory
        port: Development server port
    """
    server_process = _start_development_server(plugin_path, port)

    try:
        click.echo("\n🎯 Development server running... Press Ctrl+C to stop")
        server_process.wait()
    except KeyboardInterrupt:
        click.echo("\n🛑 Stopping development server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
            server_process.wait()


def _start_development_server(plugin_path: Path, port: int) -> subprocess.Popen:
    """Start the development server process.

    Args:
        plugin_path: Path to plugin directory
        port: Development server port

    Returns:
        Server process
    """
    # For now, we'll create a simple development runner
    # In a real implementation, this would start ViloxTerm with the plugin loaded

    # Create a simple development script
    dev_script = plugin_path / ".viloapp_dev.py"
    dev_script_content = f"""#!/usr/bin/env python3
\"\"\"Development server for plugin.\"\"\"

import sys
import json
from pathlib import Path

def main():
    plugin_path = Path(__file__).parent
    plugin_json = plugin_path / "plugin.json"

    print(f"🔧 Development server running on port {port}")
    print(f"📂 Plugin: {{plugin_path}}")

    if plugin_json.exists():
        with open(plugin_json) as f:
            manifest = json.load(f)
        print(f"📋 Plugin ID: {{manifest.get('id', 'unknown')}}")
        print(f"📋 Plugin Name: {{manifest.get('name', 'unknown')}}")
        print(f"📋 Version: {{manifest.get('version', 'unknown')}}")

    print("\\n🎯 Plugin loaded in development mode")
    print("   This is a mock development server.")
    print("   In a real implementation, ViloxTerm would be running with your plugin.")

    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\\n🛑 Development server stopped")

if __name__ == "__main__":
    main()
"""

    dev_script.write_text(dev_script_content)
    dev_script.chmod(0o755)

    # Start the development script
    return subprocess.Popen(
        [sys.executable, str(dev_script)],
        cwd=plugin_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
