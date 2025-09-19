# Plugin Architecture Extended Considerations

This document covers additional technical considerations and implementation details for the plugin architecture refactoring that complement the main refactoring strategy.

## Table of Contents
1. [Security and Sandboxing](#security-and-sandboxing)
2. [Plugin Dependencies and Conflicts](#plugin-dependencies-and-conflicts)
3. [Data Migration Strategy](#data-migration-strategy)
4. [Plugin Marketplace and Registry](#plugin-marketplace-and-registry)
5. [Testing Framework](#testing-framework)
6. [Development Tooling](#development-tooling)
7. [Backward Compatibility](#backward-compatibility)
8. [Performance Monitoring](#performance-monitoring)
9. [Internationalization](#internationalization)
10. [Distribution Formats](#distribution-formats)
11. [Error Recovery and Resilience](#error-recovery-and-resilience)
12. [Documentation Generation](#documentation-generation)

## Security and Sandboxing

### Permission System

The plugin security model is based on capability-based permissions with fine-grained access control.

#### Permission Categories

```python
from enum import Enum
from dataclasses import dataclass
from typing import Set, Dict, Any

class PermissionCategory(Enum):
    """Permission categories for plugins."""
    SYSTEM = "system"          # OS-level operations
    FILESYSTEM = "filesystem"  # File system access
    NETWORK = "network"        # Network operations
    PROCESS = "process"        # Process management
    UI = "ui"                  # UI manipulation
    SERVICES = "services"      # Core service access
    PLUGINS = "plugins"        # Inter-plugin communication

@dataclass
class Permission:
    """Individual permission definition."""
    category: PermissionCategory
    scope: str  # e.g., "read", "write", "execute"
    resource: str  # e.g., "home_directory", "temp_files"

    def __str__(self):
        return f"{self.category.value}.{self.scope}.{self.resource}"

class PermissionManager:
    """Manages plugin permissions."""

    def __init__(self):
        self._granted_permissions: Dict[str, Set[Permission]] = {}
        self._permission_callbacks = {}

    def grant_permission(self, plugin_id: str, permission: Permission):
        """Grant a permission to a plugin."""
        if plugin_id not in self._granted_permissions:
            self._granted_permissions[plugin_id] = set()
        self._granted_permissions[plugin_id].add(permission)

    def check_permission(self, plugin_id: str, permission: Permission) -> bool:
        """Check if plugin has a specific permission."""
        if plugin_id not in self._granted_permissions:
            return False

        # Check exact match
        if permission in self._granted_permissions[plugin_id]:
            return True

        # Check wildcard permissions
        for granted in self._granted_permissions[plugin_id]:
            if self._matches_wildcard(granted, permission):
                return True

        return False

    def request_permission(self, plugin_id: str, permission: Permission) -> bool:
        """Request a permission at runtime."""
        # Show user dialog for permission grant
        if self._show_permission_dialog(plugin_id, permission):
            self.grant_permission(plugin_id, permission)
            return True
        return False
```

### Sandboxing Mechanism

```python
import multiprocessing
import resource
import signal
from typing import Optional, Any

class PluginSandbox:
    """Sandbox environment for plugin execution."""

    def __init__(self, plugin_id: str):
        self.plugin_id = plugin_id
        self.process: Optional[multiprocessing.Process] = None
        self.communication_pipe = None
        self.resource_limits = {
            'memory_mb': 100,
            'cpu_percent': 25,
            'file_handles': 50,
            'execution_time': 30  # seconds
        }

    def run_sandboxed(self, plugin_class, *args, **kwargs):
        """Run plugin in sandboxed process."""
        parent_conn, child_conn = multiprocessing.Pipe()
        self.communication_pipe = parent_conn

        self.process = multiprocessing.Process(
            target=self._sandboxed_execution,
            args=(child_conn, plugin_class, args, kwargs)
        )

        # Set process nice level (lower priority)
        self.process.start()

        # Monitor process
        self._start_monitoring()

        return self.process

    def _sandboxed_execution(self, conn, plugin_class, args, kwargs):
        """Execute plugin in restricted environment."""
        # Apply resource limits
        self._apply_resource_limits()

        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._handle_termination)

        try:
            # Create and run plugin
            plugin = plugin_class(*args, **kwargs)

            # Main execution loop
            while True:
                if conn.poll():
                    message = conn.recv()
                    if message['type'] == 'command':
                        result = plugin.handle_command(
                            message['command'],
                            message['args']
                        )
                        conn.send({'type': 'result', 'data': result})
                    elif message['type'] == 'shutdown':
                        break

        except Exception as e:
            conn.send({'type': 'error', 'error': str(e)})
        finally:
            conn.close()

    def _apply_resource_limits(self):
        """Apply resource limits to current process."""
        # Memory limit
        memory_bytes = self.resource_limits['memory_mb'] * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))

        # File handle limit
        resource.setrlimit(
            resource.RLIMIT_NOFILE,
            (self.resource_limits['file_handles'],
             self.resource_limits['file_handles'])
        )

        # CPU time limit
        resource.setrlimit(
            resource.RLIMIT_CPU,
            (self.resource_limits['execution_time'],
             self.resource_limits['execution_time'])
        )
```

### Code Signing and Verification

```python
import hashlib
import json
from pathlib import Path
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import serialization

class PluginVerifier:
    """Verifies plugin authenticity and integrity."""

    def __init__(self, trusted_keys_dir: Path):
        self.trusted_keys = self._load_trusted_keys(trusted_keys_dir)

    def verify_plugin(self, plugin_path: Path) -> bool:
        """Verify plugin signature and integrity."""
        manifest_path = plugin_path / "plugin.json"
        signature_path = plugin_path / "plugin.sig"

        if not signature_path.exists():
            return False  # Unsigned plugin

        # Read manifest
        with open(manifest_path, 'rb') as f:
            manifest_data = f.read()

        # Read signature
        with open(signature_path, 'rb') as f:
            signature = f.read()

        # Verify signature
        manifest_json = json.loads(manifest_data)
        author_id = manifest_json.get('author', {}).get('id')

        if author_id not in self.trusted_keys:
            return False  # Unknown author

        public_key = self.trusted_keys[author_id]

        try:
            public_key.verify(
                signature,
                manifest_data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    def _load_trusted_keys(self, keys_dir: Path) -> dict:
        """Load trusted public keys."""
        keys = {}
        for key_file in keys_dir.glob("*.pub"):
            author_id = key_file.stem
            with open(key_file, 'rb') as f:
                public_key = serialization.load_pem_public_key(f.read())
                keys[author_id] = public_key
        return keys
```

## Plugin Dependencies and Conflicts

### Dependency Resolution

```python
from typing import Dict, List, Set, Tuple
from packaging import version
import networkx as nx

class DependencyResolver:
    """Resolves plugin dependencies and load order."""

    def __init__(self):
        self.dependency_graph = nx.DiGraph()
        self.version_constraints = {}
        self.conflicts = {}

    def add_plugin(self, plugin_id: str, manifest: dict):
        """Add plugin to dependency graph."""
        self.dependency_graph.add_node(plugin_id)

        # Add dependencies
        if 'dependencies' in manifest:
            for dep_type, deps in manifest['dependencies'].items():
                if dep_type == 'plugins':
                    for dep_id, version_spec in deps.items():
                        self.dependency_graph.add_edge(plugin_id, dep_id)
                        self.version_constraints[(plugin_id, dep_id)] = version_spec

        # Add conflicts
        if 'conflicts' in manifest:
            self.conflicts[plugin_id] = set(manifest['conflicts'])

        # Add load order hints
        if 'load_after' in manifest:
            for other_id in manifest['load_after']:
                self.dependency_graph.add_edge(other_id, plugin_id)

        if 'load_before' in manifest:
            for other_id in manifest['load_before']:
                self.dependency_graph.add_edge(plugin_id, other_id)

    def resolve_load_order(self) -> List[str]:
        """Resolve plugin load order using topological sort."""
        try:
            return list(nx.topological_sort(self.dependency_graph))
        except nx.NetworkXUnfeasible:
            # Cycle detected
            cycles = list(nx.simple_cycles(self.dependency_graph))
            raise DependencyCycleError(f"Dependency cycles detected: {cycles}")

    def check_conflicts(self, enabled_plugins: Set[str]) -> List[Tuple[str, str]]:
        """Check for conflicts between enabled plugins."""
        conflicts_found = []

        for plugin_id in enabled_plugins:
            if plugin_id in self.conflicts:
                for conflict_id in self.conflicts[plugin_id]:
                    if conflict_id in enabled_plugins:
                        conflicts_found.append((plugin_id, conflict_id))

        return conflicts_found

    def verify_version_constraints(self, available_plugins: Dict[str, str]) -> bool:
        """Verify all version constraints are satisfied."""
        for (plugin_id, dep_id), version_spec in self.version_constraints.items():
            if dep_id not in available_plugins:
                return False

            dep_version = available_plugins[dep_id]
            if not self._satisfies_version(dep_version, version_spec):
                return False

        return True

    def _satisfies_version(self, current: str, spec: str) -> bool:
        """Check if version satisfies specification."""
        # Parse version specification (e.g., ">=1.0.0", "<2.0.0")
        import re

        operators = {
            '>=': lambda v1, v2: version.parse(v1) >= version.parse(v2),
            '<=': lambda v1, v2: version.parse(v1) <= version.parse(v2),
            '>': lambda v1, v2: version.parse(v1) > version.parse(v2),
            '<': lambda v1, v2: version.parse(v1) < version.parse(v2),
            '==': lambda v1, v2: version.parse(v1) == version.parse(v2),
        }

        for op, func in operators.items():
            if spec.startswith(op):
                required = spec[len(op):].strip()
                return func(current, required)

        # No operator means exact match
        return version.parse(current) == version.parse(spec)

class DependencyCycleError(Exception):
    """Raised when circular dependencies are detected."""
    pass
```

### Virtual Environment Isolation

```python
import venv
import subprocess
from pathlib import Path

class PluginEnvironmentManager:
    """Manages isolated Python environments for plugins."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.environments = {}

    def create_environment(self, plugin_id: str, requirements: List[str]):
        """Create isolated environment for plugin."""
        env_path = self.base_dir / plugin_id

        # Create virtual environment
        venv.create(env_path, with_pip=True)

        # Install requirements
        pip_path = env_path / "bin" / "pip"
        for requirement in requirements:
            subprocess.run(
                [str(pip_path), "install", requirement],
                check=True
            )

        self.environments[plugin_id] = env_path
        return env_path

    def get_python_executable(self, plugin_id: str) -> Path:
        """Get Python executable for plugin environment."""
        if plugin_id not in self.environments:
            raise ValueError(f"No environment for plugin {plugin_id}")

        return self.environments[plugin_id] / "bin" / "python"
```

## Data Migration Strategy

### Settings Migration

```python
import json
from pathlib import Path
from typing import Dict, Any

class SettingsMigrator:
    """Migrates settings from monolithic to plugin architecture."""

    VERSION_MAP = {
        '1.0': 'migrate_v1_to_v2',
        '2.0': 'migrate_v2_to_v3',
    }

    def __init__(self):
        self.migration_log = []

    def migrate(self, settings_path: Path) -> Dict[str, Any]:
        """Migrate settings to latest format."""
        # Load existing settings
        with open(settings_path) as f:
            old_settings = json.load(f)

        # Detect version
        version = old_settings.get('version', '1.0')

        # Apply migrations sequentially
        current_settings = old_settings
        for from_version, method_name in self.VERSION_MAP.items():
            if version <= from_version:
                method = getattr(self, method_name)
                current_settings = method(current_settings)
                self.migration_log.append(f"Migrated from {from_version}")

        return current_settings

    def migrate_v1_to_v2(self, settings: Dict) -> Dict:
        """Migrate from monolithic v1 to plugin-based v2."""
        new_settings = {
            'version': '2.0',
            'core': {},
            'plugins': {}
        }

        # Migrate terminal settings
        if 'terminal' in settings:
            new_settings['plugins']['viloxterm'] = {
                'shell': settings['terminal'].get('shell', 'auto'),
                'fontSize': settings['terminal'].get('font_size', 14),
                'fontFamily': settings['terminal'].get('font_family', 'monospace'),
                'theme': settings['terminal'].get('theme', 'dark'),
                'cursorStyle': settings['terminal'].get('cursor_style', 'block'),
                'scrollback': settings['terminal'].get('scrollback', 1000)
            }

        # Migrate editor settings
        if 'editor' in settings:
            new_settings['plugins']['viloedit'] = {
                'fontSize': settings['editor'].get('font_size', 14),
                'fontFamily': settings['editor'].get('font_family', 'monospace'),
                'tabSize': settings['editor'].get('tab_size', 4),
                'wordWrap': settings['editor'].get('word_wrap', False),
                'lineNumbers': settings['editor'].get('line_numbers', True),
                'theme': settings['editor'].get('theme', 'dark')
            }

        # Migrate core settings
        for key in ['theme', 'layout', 'keybindings', 'workspace']:
            if key in settings:
                new_settings['core'][key] = settings[key]

        return new_settings

    def backup_original(self, settings_path: Path):
        """Create backup of original settings."""
        backup_path = settings_path.with_suffix('.backup')
        import shutil
        shutil.copy2(settings_path, backup_path)
        self.migration_log.append(f"Backup created at {backup_path}")
```

### State Migration

```python
class StateMigrator:
    """Migrates application state during refactoring."""

    def migrate_terminal_sessions(self, old_state: Dict) -> Dict:
        """Migrate terminal session state."""
        new_state = {
            'plugin': 'viloxterm',
            'version': '1.0',
            'sessions': []
        }

        for session in old_state.get('terminals', []):
            new_state['sessions'].append({
                'id': session['id'],
                'title': session.get('title', 'Terminal'),
                'cwd': session.get('working_directory'),
                'shell': session.get('shell'),
                'environment': session.get('env_vars', {}),
                'history': session.get('command_history', [])
            })

        return new_state

    def migrate_editor_buffers(self, old_state: Dict) -> Dict:
        """Migrate editor buffer state."""
        new_state = {
            'plugin': 'viloedit',
            'version': '1.0',
            'buffers': []
        }

        for buffer in old_state.get('editors', []):
            new_state['buffers'].append({
                'id': buffer['id'],
                'file_path': buffer.get('path'),
                'content': buffer.get('content', ''),
                'cursor_position': buffer.get('cursor', {'line': 0, 'column': 0}),
                'selection': buffer.get('selection'),
                'modified': buffer.get('is_modified', False),
                'syntax': buffer.get('syntax_mode', 'plain')
            })

        return new_state
```

## Plugin Marketplace and Registry

### Registry Structure

```python
from dataclasses import dataclass
from typing import List, Optional
import requests

@dataclass
class PluginRegistryEntry:
    """Entry in plugin registry."""
    id: str
    name: str
    version: str
    author: str
    description: str
    homepage: str
    download_url: str
    icon_url: Optional[str]
    rating: float
    downloads: int
    tags: List[str]
    dependencies: Dict[str, str]
    verified: bool

class PluginRegistry:
    """Central registry for plugin discovery."""

    DEFAULT_REGISTRY = "https://plugins.viloapp.com/registry.json"

    def __init__(self, registry_urls: List[str] = None):
        self.registry_urls = registry_urls or [self.DEFAULT_REGISTRY]
        self.cache = {}
        self.refresh_interval = 3600  # 1 hour

    def search(self, query: str, tags: List[str] = None) -> List[PluginRegistryEntry]:
        """Search for plugins."""
        results = []

        for entry in self.get_all_plugins():
            # Search in name and description
            if query.lower() in entry.name.lower() or \
               query.lower() in entry.description.lower():

                # Filter by tags if specified
                if tags:
                    if any(tag in entry.tags for tag in tags):
                        results.append(entry)
                else:
                    results.append(entry)

        # Sort by relevance (rating * log(downloads))
        import math
        results.sort(
            key=lambda e: e.rating * math.log(e.downloads + 1),
            reverse=True
        )

        return results

    def get_plugin_info(self, plugin_id: str) -> Optional[PluginRegistryEntry]:
        """Get detailed information about a plugin."""
        for entry in self.get_all_plugins():
            if entry.id == plugin_id:
                return entry
        return None

    def get_all_plugins(self) -> List[PluginRegistryEntry]:
        """Get all plugins from registries."""
        plugins = []

        for url in self.registry_urls:
            if url in self.cache:
                # Check cache age
                if self._is_cache_valid(url):
                    plugins.extend(self.cache[url])
                    continue

            # Fetch from registry
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                registry_data = response.json()

                entries = [
                    PluginRegistryEntry(**entry)
                    for entry in registry_data['plugins']
                ]

                self.cache[url] = entries
                plugins.extend(entries)

            except Exception as e:
                print(f"Failed to fetch registry {url}: {e}")

        return plugins
```

### Auto-Update System

```python
class PluginUpdater:
    """Handles plugin updates."""

    def __init__(self, registry: PluginRegistry, install_dir: Path):
        self.registry = registry
        self.install_dir = install_dir
        self.update_policy = {
            'auto_update': True,
            'check_interval': 86400,  # 24 hours
            'notify_only': False
        }

    def check_updates(self, installed_plugins: Dict[str, str]) -> Dict[str, str]:
        """Check for available updates."""
        updates = {}

        for plugin_id, current_version in installed_plugins.items():
            registry_entry = self.registry.get_plugin_info(plugin_id)

            if registry_entry:
                if version.parse(registry_entry.version) > version.parse(current_version):
                    updates[plugin_id] = registry_entry.version

        return updates

    def update_plugin(self, plugin_id: str) -> bool:
        """Update a plugin to latest version."""
        registry_entry = self.registry.get_plugin_info(plugin_id)
        if not registry_entry:
            return False

        try:
            # Download new version
            response = requests.get(registry_entry.download_url)
            response.raise_for_status()

            # Extract to temporary directory
            import tempfile
            import zipfile

            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = Path(temp_dir) / "plugin.zip"

                with open(zip_path, 'wb') as f:
                    f.write(response.content)

                # Verify signature
                if not self._verify_plugin(zip_path):
                    return False

                # Backup current version
                self._backup_plugin(plugin_id)

                # Extract new version
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(self.install_dir / plugin_id)

                return True

        except Exception as e:
            print(f"Failed to update plugin {plugin_id}: {e}")
            self._restore_backup(plugin_id)
            return False
```

## Testing Framework

### Plugin Test Framework

```python
import unittest
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict

class PluginTestCase(unittest.TestCase):
    """Base test class for plugin testing."""

    def setUp(self):
        """Set up test environment."""
        self.mock_host = self.create_mock_host()
        self.mock_services = {}
        self.mock_event_bus = Mock()

    def create_mock_host(self) -> Mock:
        """Create mock plugin host."""
        host = Mock()
        host.get_service = MagicMock(side_effect=self._get_mock_service)
        host.emit_event = self.mock_event_bus.emit
        host.subscribe_event = self.mock_event_bus.subscribe
        return host

    def create_mock_service(self, service_name: str) -> Mock:
        """Create mock service."""
        if service_name not in self.mock_services:
            self.mock_services[service_name] = Mock()
        return self.mock_services[service_name]

    def _get_mock_service(self, service_name: str):
        """Get or create mock service."""
        return self.create_mock_service(service_name)

    def simulate_event(self, event_type: str, data: Dict[str, Any]):
        """Simulate plugin event."""
        from viloapp_sdk.communication import PluginEvent

        event = PluginEvent(
            type=event_type,
            source='test',
            data=data
        )

        self.mock_event_bus.emit(event)

    def assert_command_handled(self, plugin, command: str, expected_result: Any):
        """Assert command is handled correctly."""
        result = plugin.handle_command(command, {})
        self.assertEqual(result, expected_result)

    def assert_event_emitted(self, event_type: str):
        """Assert specific event was emitted."""
        calls = self.mock_event_bus.emit.call_args_list
        event_types = [call[0][0].type for call in calls]
        self.assertIn(event_type, event_types)

class PluginIntegrationTest(PluginTestCase):
    """Base class for plugin integration tests."""

    def create_plugin_context(self) -> Dict[str, Any]:
        """Create plugin context for testing."""
        return {
            'plugin_id': 'test_plugin',
            'version': '1.0.0',
            'host': self.mock_host,
            'services': self.mock_services,
            'event_bus': self.mock_event_bus,
            'resource_path': Path('./test_resources')
        }

    def test_plugin_lifecycle(self):
        """Test plugin initialization and shutdown."""
        # Override in subclasses
        pass
```

### Mock Services

```python
class MockThemeService:
    """Mock theme service for testing."""

    def __init__(self):
        self.current_theme = 'dark'
        self.colors = {
            'background': '#1e1e1e',
            'foreground': '#ffffff'
        }

    def get_current_theme(self) -> str:
        return self.current_theme

    def get_color(self, key: str) -> str:
        return self.colors.get(key, '#000000')

    def subscribe_theme_change(self, callback):
        # Mock subscription
        pass

class MockWorkspaceService:
    """Mock workspace service for testing."""

    def __init__(self):
        self.widgets = {}
        self.active_widget = None

    def add_widget(self, widget_id: str, widget: Any):
        self.widgets[widget_id] = widget
        self.active_widget = widget_id

    def get_active_widget(self):
        if self.active_widget:
            return self.widgets[self.active_widget]
        return None

    def remove_widget(self, widget_id: str):
        if widget_id in self.widgets:
            del self.widgets[widget_id]
```

## Development Tooling

### Plugin CLI Tool

```python
import click
import json
from pathlib import Path
from typing import Optional

@click.group()
def cli():
    """ViloxApp Plugin Development CLI."""
    pass

@cli.command()
@click.argument('name')
@click.option('--template', default='basic', help='Plugin template to use')
@click.option('--author', prompt=True, help='Plugin author name')
@click.option('--description', prompt=True, help='Plugin description')
def create_plugin(name: str, template: str, author: str, description: str):
    """Create a new plugin from template."""
    plugin_dir = Path(name)

    if plugin_dir.exists():
        click.echo(f"Directory {name} already exists", err=True)
        return

    # Create directory structure
    plugin_dir.mkdir()
    (plugin_dir / 'src').mkdir()
    (plugin_dir / 'tests').mkdir()
    (plugin_dir / 'resources').mkdir()

    # Create plugin.json
    manifest = {
        'id': f'com.{author.lower().replace(" ", "")}.{name}',
        'name': name.title(),
        'version': '0.1.0',
        'api_version': '1.0',
        'author': author,
        'description': description,
        'main': f'{name}.Plugin',
        'dependencies': {
            'viloapp-sdk': '>=1.0.0'
        }
    }

    with open(plugin_dir / 'plugin.json', 'w') as f:
        json.dump(manifest, f, indent=2)

    # Create main plugin file
    plugin_code = f'''"""
{name.title()} Plugin for ViloxApp
"""

from viloapp_sdk import IPlugin, IWidget, PluginContext

class Plugin(IPlugin):
    """Main plugin class for {name}."""

    def __init__(self):
        self.context = None
        self.widgets = []

    def get_plugin_id(self) -> str:
        return "{manifest['id']}"

    def get_version(self) -> str:
        return "{manifest['version']}"

    def initialize(self, context: PluginContext):
        """Initialize the plugin."""
        self.context = context
        # Initialize your plugin here

    def shutdown(self):
        """Clean up plugin resources."""
        # Cleanup code here
        pass

    def get_widgets(self):
        """Return widgets provided by this plugin."""
        return self.widgets

    def get_commands(self):
        """Return commands provided by this plugin."""
        return []
'''

    with open(plugin_dir / 'src' / f'{name}.py', 'w') as f:
        f.write(plugin_code)

    # Create pyproject.toml
    pyproject = f'''[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
version = "0.1.0"
description = "{description}"
authors = [{{name = "{author}"}}]
dependencies = [
    "viloapp-sdk>=1.0.0"
]

[tool.setuptools.packages.find]
where = ["src"]
'''

    with open(plugin_dir / 'pyproject.toml', 'w') as f:
        f.write(pyproject)

    click.echo(f"Plugin {name} created successfully!")
    click.echo(f"Next steps:")
    click.echo(f"  cd {name}")
    click.echo(f"  viloapp dev --plugin .")

@cli.command()
@click.option('--plugin', required=True, help='Path to plugin directory')
@click.option('--host', default='localhost', help='Dev server host')
@click.option('--port', default=5000, help='Dev server port')
def dev(plugin: str, host: str, port: int):
    """Run plugin in development mode with hot reload."""
    from viloapp.dev_server import DevelopmentServer

    plugin_path = Path(plugin).resolve()

    if not plugin_path.exists():
        click.echo(f"Plugin directory not found: {plugin}", err=True)
        return

    # Create development server
    server = DevelopmentServer(plugin_path)

    # Enable hot reload
    server.enable_hot_reload()

    # Start server
    click.echo(f"Starting development server for {plugin_path.name}")
    click.echo(f"Plugin available at http://{host}:{port}")

    server.run(host=host, port=port)

@cli.command()
@click.argument('plugin_path')
def test(plugin_path: str):
    """Run plugin tests."""
    import subprocess

    plugin_dir = Path(plugin_path)

    if not plugin_dir.exists():
        click.echo(f"Plugin directory not found: {plugin_path}", err=True)
        return

    # Run tests
    result = subprocess.run(
        ['python', '-m', 'pytest', 'tests/'],
        cwd=plugin_dir,
        capture_output=True,
        text=True
    )

    click.echo(result.stdout)

    if result.returncode != 0:
        click.echo(result.stderr, err=True)
        return result.returncode

@cli.command()
@click.argument('plugin_path')
@click.option('--output', '-o', help='Output directory')
def package(plugin_path: str, output: Optional[str]):
    """Package plugin for distribution."""
    import zipfile

    plugin_dir = Path(plugin_path)
    output_dir = Path(output) if output else plugin_dir.parent

    # Read manifest
    with open(plugin_dir / 'plugin.json') as f:
        manifest = json.load(f)

    # Create package name
    package_name = f"{manifest['id']}-{manifest['version']}.viloplugin"
    package_path = output_dir / package_name

    # Create zip archive
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in plugin_dir.rglob('*'):
            if file.is_file() and '.git' not in str(file):
                arcname = file.relative_to(plugin_dir.parent)
                zipf.write(file, arcname)

    click.echo(f"Plugin packaged: {package_path}")

if __name__ == '__main__':
    cli()
```

### Hot Reload System

```python
import watchdog.observers
import watchdog.events
from pathlib import Path
import importlib
import sys

class PluginHotReloader:
    """Hot reload system for plugin development."""

    def __init__(self, plugin_path: Path, host_app):
        self.plugin_path = plugin_path
        self.host_app = host_app
        self.observer = watchdog.observers.Observer()
        self.plugin_instance = None

    def start(self):
        """Start watching for changes."""
        event_handler = PluginChangeHandler(self)
        self.observer.schedule(
            event_handler,
            str(self.plugin_path),
            recursive=True
        )
        self.observer.start()

    def reload_plugin(self):
        """Reload the plugin."""
        try:
            # Unload current plugin
            if self.plugin_instance:
                self.plugin_instance.shutdown()
                self.host_app.unload_plugin(self.plugin_instance.get_plugin_id())

            # Clear module cache
            modules_to_remove = [
                mod for mod in sys.modules
                if str(self.plugin_path) in str(getattr(sys.modules[mod], '__file__', ''))
            ]

            for mod in modules_to_remove:
                del sys.modules[mod]

            # Reload plugin
            manifest_path = self.plugin_path / 'plugin.json'
            with open(manifest_path) as f:
                manifest = json.load(f)

            # Import and instantiate
            sys.path.insert(0, str(self.plugin_path / 'src'))

            module_name = manifest['main'].rsplit('.', 1)[0]
            class_name = manifest['main'].rsplit('.', 1)[1]

            module = importlib.import_module(module_name)
            plugin_class = getattr(module, class_name)

            # Create new instance
            self.plugin_instance = plugin_class()

            # Load in host
            self.host_app.load_plugin(self.plugin_instance)

            print(f"Plugin reloaded successfully")

        except Exception as e:
            print(f"Failed to reload plugin: {e}")
        finally:
            sys.path.remove(str(self.plugin_path / 'src'))

class PluginChangeHandler(watchdog.events.FileSystemEventHandler):
    """Handle file system changes for hot reload."""

    def __init__(self, reloader):
        self.reloader = reloader
        self.debounce_timer = None

    def on_modified(self, event):
        if event.src_path.endswith(('.py', '.json')):
            self._debounced_reload()

    def _debounced_reload(self):
        """Debounce reload calls."""
        if self.debounce_timer:
            self.debounce_timer.cancel()

        import threading
        self.debounce_timer = threading.Timer(0.5, self.reloader.reload_plugin)
        self.debounce_timer.start()
```

## Backward Compatibility

### Legacy API Adapter

```python
from typing import Any
import warnings

class LegacyWidgetAdapter:
    """Adapter for old widget API to new plugin API."""

    def __init__(self, legacy_widget):
        self.legacy_widget = legacy_widget
        self._setup_compatibility()

    def _setup_compatibility(self):
        """Set up compatibility mappings."""
        # Map old methods to new
        self.get_widget_id = self.legacy_widget.widget_id
        self.get_title = lambda: getattr(
            self.legacy_widget,
            'title',
            self.legacy_widget.__class__.__name__
        )

    @property
    def widget_id(self):
        """Legacy property access."""
        warnings.warn(
            "widget_id is deprecated, use get_widget_id()",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_widget_id()

    def setup_widget(self, *args, **kwargs):
        """Legacy setup method."""
        warnings.warn(
            "setup_widget() is deprecated, use initialize()",
            DeprecationWarning,
            stacklevel=2
        )
        return self.initialize(*args, **kwargs)

    def initialize(self, context):
        """Initialize with new API."""
        # Convert new context to old format
        if hasattr(self.legacy_widget, 'initialize'):
            return self.legacy_widget.initialize(context)
        elif hasattr(self.legacy_widget, 'setup_widget'):
            # Convert context to old format
            old_context = self._convert_context(context)
            return self.legacy_widget.setup_widget(old_context)

    def _convert_context(self, new_context):
        """Convert new context format to old."""
        return {
            'workspace': new_context.get_service('workspace'),
            'theme': new_context.get_service('theme'),
            'commands': new_context.get_service('commands')
        }

def create_compatibility_shim(widget_class):
    """Create compatibility shim for old widget class."""

    class CompatibilityShim(widget_class):
        """Shim class with compatibility layer."""

        def __init__(self, *args, **kwargs):
            # Filter out new arguments
            filtered_kwargs = {
                k: v for k, v in kwargs.items()
                if k in self._get_old_init_params()
            }
            super().__init__(*args, **filtered_kwargs)

        def _get_old_init_params(self):
            """Get parameters expected by old __init__."""
            import inspect
            sig = inspect.signature(widget_class.__init__)
            return list(sig.parameters.keys())

    return CompatibilityShim
```

## Performance Monitoring

### Plugin Metrics Collection

```python
import time
import psutil
import threading
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class PluginMetrics:
    """Performance metrics for a plugin."""
    plugin_id: str
    startup_time: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0
    command_count: int = 0
    command_avg_time: float = 0.0
    error_count: int = 0
    last_error: str = ""
    active_time: float = 0.0
    resource_violations: List[str] = field(default_factory=list)

class PerformanceMonitor:
    """Monitors plugin performance."""

    def __init__(self):
        self.metrics: Dict[str, PluginMetrics] = {}
        self.monitoring_thread = None
        self.stop_monitoring = threading.Event()

    def start_monitoring(self, plugin_id: str):
        """Start monitoring a plugin."""
        if plugin_id not in self.metrics:
            self.metrics[plugin_id] = PluginMetrics(plugin_id)

        if not self.monitoring_thread:
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()

    def record_startup(self, plugin_id: str, duration: float):
        """Record plugin startup time."""
        if plugin_id in self.metrics:
            self.metrics[plugin_id].startup_time = duration

    def record_command(self, plugin_id: str, duration: float):
        """Record command execution."""
        if plugin_id in self.metrics:
            metrics = self.metrics[plugin_id]
            metrics.command_count += 1

            # Update average
            total_time = metrics.command_avg_time * (metrics.command_count - 1)
            metrics.command_avg_time = (total_time + duration) / metrics.command_count

    def record_error(self, plugin_id: str, error: str):
        """Record plugin error."""
        if plugin_id in self.metrics:
            self.metrics[plugin_id].error_count += 1
            self.metrics[plugin_id].last_error = error[:100]  # Truncate

    def _monitoring_loop(self):
        """Main monitoring loop."""
        while not self.stop_monitoring.is_set():
            for plugin_id in self.metrics:
                self._update_resource_usage(plugin_id)

            time.sleep(5)  # Update every 5 seconds

    def _update_resource_usage(self, plugin_id: str):
        """Update resource usage for plugin."""
        # This would need actual process tracking
        # For now, use system-wide metrics as placeholder

        metrics = self.metrics[plugin_id]

        # Update memory usage
        process = psutil.Process()
        metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024

        # Update CPU usage
        metrics.cpu_percent = process.cpu_percent(interval=0.1)

    def get_report(self, plugin_id: str = None) -> Dict:
        """Generate performance report."""
        if plugin_id:
            return self.metrics[plugin_id].__dict__ if plugin_id in self.metrics else {}

        return {
            pid: metrics.__dict__
            for pid, metrics in self.metrics.items()
        }

    def check_violations(self, plugin_id: str, limits: Dict) -> List[str]:
        """Check for resource limit violations."""
        violations = []

        if plugin_id not in self.metrics:
            return violations

        metrics = self.metrics[plugin_id]

        if 'memory_mb' in limits and metrics.memory_usage_mb > limits['memory_mb']:
            violations.append(f"Memory limit exceeded: {metrics.memory_usage_mb:.1f}MB > {limits['memory_mb']}MB")

        if 'cpu_percent' in limits and metrics.cpu_percent > limits['cpu_percent']:
            violations.append(f"CPU limit exceeded: {metrics.cpu_percent:.1f}% > {limits['cpu_percent']}%")

        if 'startup_time' in limits and metrics.startup_time > limits['startup_time']:
            violations.append(f"Slow startup: {metrics.startup_time:.2f}s > {limits['startup_time']}s")

        return violations
```

## Internationalization

### Plugin Localization

```python
import json
from pathlib import Path
from typing import Dict, Optional

class PluginI18n:
    """Internationalization support for plugins."""

    def __init__(self, plugin_path: Path, default_locale: str = 'en'):
        self.plugin_path = plugin_path
        self.default_locale = default_locale
        self.current_locale = default_locale
        self.translations = {}
        self._load_translations()

    def _load_translations(self):
        """Load all available translations."""
        locales_dir = self.plugin_path / 'locales'

        if not locales_dir.exists():
            return

        for locale_file in locales_dir.glob('*.json'):
            locale = locale_file.stem

            with open(locale_file, encoding='utf-8') as f:
                self.translations[locale] = json.load(f)

    def set_locale(self, locale: str):
        """Set current locale."""
        if locale in self.translations:
            self.current_locale = locale
        else:
            print(f"Locale {locale} not available, using {self.default_locale}")

    def t(self, key: str, **kwargs) -> str:
        """Translate a key."""
        # Try current locale
        if self.current_locale in self.translations:
            if key in self.translations[self.current_locale]:
                translation = self.translations[self.current_locale][key]
                return self._interpolate(translation, kwargs)

        # Fall back to default locale
        if self.default_locale in self.translations:
            if key in self.translations[self.default_locale]:
                translation = self.translations[self.default_locale][key]
                return self._interpolate(translation, kwargs)

        # Return key if no translation found
        return key

    def _interpolate(self, text: str, variables: Dict) -> str:
        """Interpolate variables in translation."""
        for key, value in variables.items():
            text = text.replace(f'{{{key}}}', str(value))
        return text

# Example locale file: viloxterm/locales/en.json
{
    "terminal.new": "New Terminal",
    "terminal.clear": "Clear Terminal",
    "terminal.copy": "Copy",
    "terminal.paste": "Paste",
    "terminal.session_ended": "Terminal session ended",
    "terminal.connection_error": "Failed to connect to terminal: {error}",
    "terminal.settings.shell": "Shell",
    "terminal.settings.font_size": "Font Size",
    "terminal.settings.cursor_style": "Cursor Style"
}
```

## Distribution Formats

### Single-file Plugin Format

```python
import zipfile
import json
from pathlib import Path
from typing import Optional

class ViloPlugin:
    """Single-file plugin format (.viloplugin)."""

    REQUIRED_FILES = ['plugin.json', 'src/']
    OPTIONAL_FILES = ['resources/', 'locales/', 'README.md']

    @classmethod
    def create(cls, plugin_dir: Path, output_path: Path) -> Path:
        """Create .viloplugin file from directory."""
        # Validate structure
        if not cls._validate_structure(plugin_dir):
            raise ValueError("Invalid plugin structure")

        # Read and validate manifest
        manifest_path = plugin_dir / 'plugin.json'
        with open(manifest_path) as f:
            manifest = json.load(f)

        # Create archive
        plugin_file = output_path / f"{manifest['id']}-{manifest['version']}.viloplugin"

        with zipfile.ZipFile(plugin_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files
            for file in plugin_dir.rglob('*'):
                if file.is_file() and not cls._should_exclude(file):
                    arcname = file.relative_to(plugin_dir)
                    zipf.write(file, arcname)

            # Add metadata
            metadata = {
                'format_version': '1.0',
                'created_at': time.time(),
                'plugin_id': manifest['id'],
                'plugin_version': manifest['version']
            }
            zipf.writestr('.viloplugin', json.dumps(metadata))

        return plugin_file

    @classmethod
    def extract(cls, plugin_file: Path, target_dir: Path) -> Path:
        """Extract .viloplugin file."""
        with zipfile.ZipFile(plugin_file, 'r') as zipf:
            # Verify format
            if '.viloplugin' not in zipf.namelist():
                raise ValueError("Not a valid .viloplugin file")

            # Read metadata
            metadata = json.loads(zipf.read('.viloplugin'))

            # Extract to target directory
            plugin_dir = target_dir / metadata['plugin_id']
            zipf.extractall(plugin_dir)

        return plugin_dir

    @classmethod
    def _validate_structure(cls, plugin_dir: Path) -> bool:
        """Validate plugin directory structure."""
        for required in cls.REQUIRED_FILES:
            if not (plugin_dir / required).exists():
                return False
        return True

    @classmethod
    def _should_exclude(cls, file: Path) -> bool:
        """Check if file should be excluded from archive."""
        exclude_patterns = [
            '__pycache__',
            '.pyc',
            '.git',
            '.gitignore',
            '.pytest_cache',
            '.coverage'
        ]

        return any(pattern in str(file) for pattern in exclude_patterns)
```

## Error Recovery and Resilience

### Plugin Crash Recovery

```python
import traceback
from enum import Enum
from typing import Optional, Dict, Any

class RestartPolicy(Enum):
    """Plugin restart policies."""
    NEVER = "never"
    ON_FAILURE = "on_failure"
    ALWAYS = "always"
    EXPONENTIAL_BACKOFF = "exponential_backoff"

class PluginSupervisor:
    """Supervises plugin execution and handles failures."""

    def __init__(self):
        self.plugins = {}
        self.failure_counts = {}
        self.restart_policies = {}
        self.restart_delays = {}
        self.max_retries = 3

    def supervise(self, plugin_id: str, plugin_instance,
                 policy: RestartPolicy = RestartPolicy.ON_FAILURE):
        """Start supervising a plugin."""
        self.plugins[plugin_id] = plugin_instance
        self.restart_policies[plugin_id] = policy
        self.failure_counts[plugin_id] = 0
        self.restart_delays[plugin_id] = 1000  # Initial delay in ms

    def handle_crash(self, plugin_id: str, error: Exception):
        """Handle plugin crash."""
        # Log error
        error_info = {
            'plugin_id': plugin_id,
            'error': str(error),
            'traceback': traceback.format_exc(),
            'timestamp': time.time()
        }
        self._log_error(error_info)

        # Update failure count
        self.failure_counts[plugin_id] += 1

        # Determine if we should restart
        if self._should_restart(plugin_id):
            delay = self._get_restart_delay(plugin_id)
            self._schedule_restart(plugin_id, delay)
        else:
            self._disable_plugin(plugin_id)

    def _should_restart(self, plugin_id: str) -> bool:
        """Determine if plugin should be restarted."""
        policy = self.restart_policies.get(plugin_id, RestartPolicy.NEVER)
        failure_count = self.failure_counts[plugin_id]

        if policy == RestartPolicy.NEVER:
            return False

        if policy == RestartPolicy.ALWAYS:
            return True

        if policy in [RestartPolicy.ON_FAILURE, RestartPolicy.EXPONENTIAL_BACKOFF]:
            return failure_count <= self.max_retries

        return False

    def _get_restart_delay(self, plugin_id: str) -> int:
        """Calculate restart delay based on policy."""
        policy = self.restart_policies[plugin_id]

        if policy == RestartPolicy.EXPONENTIAL_BACKOFF:
            # Exponential backoff: 1s, 2s, 4s, 8s...
            delay = self.restart_delays[plugin_id]
            self.restart_delays[plugin_id] = min(delay * 2, 30000)  # Cap at 30s
            return delay

        return 1000  # Default 1 second

    def _schedule_restart(self, plugin_id: str, delay: int):
        """Schedule plugin restart."""
        import threading

        def restart():
            try:
                # Get plugin class and context
                plugin_class = self.plugins[plugin_id].__class__
                context = self.plugins[plugin_id].context

                # Create new instance
                new_instance = plugin_class()
                new_instance.initialize(context)

                # Update reference
                self.plugins[plugin_id] = new_instance

                # Reset failure count on successful restart
                self.failure_counts[plugin_id] = 0

                print(f"Plugin {plugin_id} restarted successfully")

            except Exception as e:
                # Restart failed, handle as new crash
                self.handle_crash(plugin_id, e)

        timer = threading.Timer(delay / 1000.0, restart)
        timer.start()

    def _disable_plugin(self, plugin_id: str):
        """Disable a plugin that can't be recovered."""
        if plugin_id in self.plugins:
            try:
                self.plugins[plugin_id].shutdown()
            except:
                pass  # Ignore errors during shutdown

            del self.plugins[plugin_id]

        print(f"Plugin {plugin_id} disabled after {self.failure_counts[plugin_id]} failures")

    def _log_error(self, error_info: Dict[str, Any]):
        """Log error for analysis."""
        # Would write to error log file or telemetry service
        import json

        error_log_path = Path.home() / '.viloapp' / 'plugin_errors.log'
        error_log_path.parent.mkdir(parents=True, exist_ok=True)

        with open(error_log_path, 'a') as f:
            f.write(json.dumps(error_info) + '\n')

class PluginHealthCheck:
    """Health monitoring for plugins."""

    def __init__(self, supervisor: PluginSupervisor):
        self.supervisor = supervisor
        self.health_status = {}
        self.check_interval = 30  # seconds

    def start_health_checks(self):
        """Start periodic health checks."""
        import threading

        def check_loop():
            while True:
                self._check_all_plugins()
                time.sleep(self.check_interval)

        thread = threading.Thread(target=check_loop, daemon=True)
        thread.start()

    def _check_all_plugins(self):
        """Check health of all plugins."""
        for plugin_id, plugin in self.supervisor.plugins.items():
            if self._is_healthy(plugin):
                self.health_status[plugin_id] = 'healthy'
            else:
                self.health_status[plugin_id] = 'unhealthy'
                # Trigger recovery
                self.supervisor.handle_crash(
                    plugin_id,
                    Exception("Health check failed")
                )

    def _is_healthy(self, plugin) -> bool:
        """Check if plugin is healthy."""
        try:
            # Call health check method if available
            if hasattr(plugin, 'health_check'):
                return plugin.health_check()

            # Basic check - can handle a ping command
            result = plugin.handle_command('ping', {})
            return result == 'pong'

        except:
            return False
```

## Documentation Generation

### Automatic API Documentation

```python
import ast
import inspect
from pathlib import Path
from typing import List, Dict

class PluginDocGenerator:
    """Generates documentation for plugins."""

    def __init__(self, plugin_path: Path):
        self.plugin_path = plugin_path
        self.docs = {
            'commands': [],
            'widgets': [],
            'settings': [],
            'api': []
        }

    def generate(self) -> str:
        """Generate complete documentation."""
        # Parse manifest
        manifest = self._parse_manifest()

        # Parse source code
        self._parse_source_files()

        # Generate markdown
        return self._generate_markdown(manifest)

    def _parse_manifest(self) -> dict:
        """Parse plugin.json."""
        with open(self.plugin_path / 'plugin.json') as f:
            return json.load(f)

    def _parse_source_files(self):
        """Parse Python source files."""
        src_dir = self.plugin_path / 'src'

        for py_file in src_dir.rglob('*.py'):
            with open(py_file) as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self._parse_class(node)
                elif isinstance(node, ast.FunctionDef):
                    self._parse_function(node)

    def _parse_class(self, node: ast.ClassDef):
        """Parse class definition."""
        # Extract docstring
        docstring = ast.get_docstring(node)

        # Check if it's a widget
        for base in node.bases:
            if hasattr(base, 'id') and base.id == 'IWidget':
                self.docs['widgets'].append({
                    'name': node.name,
                    'docstring': docstring,
                    'methods': self._get_class_methods(node)
                })

    def _parse_function(self, node: ast.FunctionDef):
        """Parse function definition."""
        # Check for command decorator
        for decorator in node.decorator_list:
            if hasattr(decorator, 'id') and decorator.id == 'command':
                self.docs['commands'].append({
                    'name': node.name,
                    'docstring': ast.get_docstring(node),
                    'args': self._get_function_args(node)
                })

    def _generate_markdown(self, manifest: dict) -> str:
        """Generate markdown documentation."""
        md = f"""# {manifest['name']} Plugin Documentation

## Overview
{manifest.get('description', '')}

- **Version**: {manifest['version']}
- **Author**: {manifest['author']}
- **License**: {manifest.get('license', 'Unknown')}

## Installation

```bash
viloapp install {manifest['id']}
```

## Commands

"""
        # Add commands
        for cmd in self.docs['commands']:
            md += f"### `{cmd['name']}`\n\n"
            md += f"{cmd['docstring']}\n\n"
            if cmd['args']:
                md += "**Arguments:**\n"
                for arg in cmd['args']:
                    md += f"- `{arg['name']}`: {arg.get('type', 'Any')}\n"
            md += "\n"

        # Add widgets
        if self.docs['widgets']:
            md += "## Widgets\n\n"
            for widget in self.docs['widgets']:
                md += f"### {widget['name']}\n\n"
                md += f"{widget['docstring']}\n\n"

        # Add configuration
        if 'configuration' in manifest:
            md += "## Configuration\n\n"
            for key, config in manifest['configuration'].items():
                md += f"### `{key}`\n\n"
                md += f"- **Type**: {config['type']}\n"
                md += f"- **Default**: {config.get('default', 'None')}\n"
                md += f"- **Description**: {config.get('description', '')}\n\n"

        return md
```

## Conclusion

These extended considerations provide comprehensive coverage of the technical challenges and solutions for implementing a robust plugin architecture. Key areas addressed include:

1. **Security**: Multi-layered security with permissions, sandboxing, and code signing
2. **Dependencies**: Sophisticated dependency resolution and isolation
3. **Migration**: Comprehensive data and settings migration strategies
4. **Marketplace**: Full plugin discovery and distribution system
5. **Testing**: Complete testing framework for plugin developers
6. **Tooling**: Rich development tools including CLI and hot reload
7. **Compatibility**: Extensive backward compatibility support
8. **Performance**: Detailed monitoring and optimization capabilities
9. **Internationalization**: Full i18n support for global plugins
10. **Distribution**: Multiple distribution formats and channels
11. **Resilience**: Robust error recovery and health monitoring
12. **Documentation**: Automatic documentation generation

Together with the main refactoring document, this provides a complete blueprint for transforming ViloxTerm into a modern, extensible application platform.