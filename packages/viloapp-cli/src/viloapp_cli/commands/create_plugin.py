"""Create plugin command implementation."""

from pathlib import Path
from typing import Any

import click
from jinja2 import Environment

from ..config import CLIConfig


def create_plugin(config: CLIConfig, name: str, template: str, output_dir: Path) -> None:
    """Create a new plugin from template.

    Args:
        config: CLI configuration
        name: Plugin name
        template: Template type (basic, widget, service, command)
        output_dir: Output directory for the plugin
    """
    try:
        plugin_dir = output_dir / name

        if plugin_dir.exists():
            raise click.ClickException(f"Plugin directory '{plugin_dir}' already exists")

        # Create plugin directory structure
        _create_plugin_structure(plugin_dir, name, template)

        # Generate files from templates
        _generate_plugin_files(config, plugin_dir, name, template)

        click.echo(f"✅ Plugin '{name}' created successfully at {plugin_dir}")
        click.echo(f"   Template: {template}")
        click.echo("\nNext steps:")
        click.echo(f"  cd {plugin_dir}")
        click.echo("  viloapp dev --plugin .")

    except Exception as e:
        raise click.ClickException(f"Failed to create plugin: {e}")


def _create_plugin_structure(plugin_dir: Path, name: str, template: str) -> None:
    """Create the basic plugin directory structure.

    Args:
        plugin_dir: Plugin directory path
        name: Plugin name
        template: Template type
    """
    python_name = name.replace("-", "_")  # Convert to valid Python package name

    # Create main directories
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "src" / python_name).mkdir(parents=True)
    (plugin_dir / "tests").mkdir(parents=True)
    (plugin_dir / "docs").mkdir(parents=True)

    # Create template-specific directories
    if template == "widget":
        (plugin_dir / "src" / python_name / "widgets").mkdir(parents=True)
        (plugin_dir / "resources").mkdir(parents=True)
    elif template == "service":
        (plugin_dir / "src" / python_name / "services").mkdir(parents=True)
    elif template == "command":
        (plugin_dir / "src" / python_name / "commands").mkdir(parents=True)


def _generate_plugin_files(config: CLIConfig, plugin_dir: Path, name: str, template: str) -> None:
    """Generate plugin files from templates.

    Args:
        config: CLI configuration
        plugin_dir: Plugin directory path
        name: Plugin name
        template: Template type
    """
    # Use bundled templates for now (embedded in the CLI)
    templates = _get_embedded_templates()

    # Template context
    python_name = name.replace("-", "_")  # Convert hyphens to underscores for Python
    context = {
        "plugin_name": name,
        "python_name": python_name,
        "plugin_class": _to_class_name(name),
        "plugin_id": f"viloapp.{name}",
        "template_type": template,
        "author": "Plugin Developer",
        "email": "developer@example.com",
    }

    # Generate base files
    _generate_file(plugin_dir / "pyproject.toml", templates["pyproject.toml"], context)
    _generate_file(plugin_dir / "plugin.json", templates["plugin.json"], context)
    _generate_file(plugin_dir / "README.md", templates["README.md"], context)
    _generate_file(
        plugin_dir / "src" / python_name / "__init__.py", templates["__init__.py"], context
    )
    _generate_file(plugin_dir / "src" / python_name / "plugin.py", templates["plugin.py"], context)
    _generate_file(plugin_dir / "tests" / "__init__.py", templates["test_init.py"], context)
    _generate_file(plugin_dir / "tests" / "test_plugin.py", templates["test_plugin.py"], context)

    # Generate template-specific files
    if template == "widget":
        _generate_file(
            plugin_dir / "src" / python_name / "widget.py", templates["widget.py"], context
        )
        _generate_file(
            plugin_dir / "tests" / "test_widget.py", templates["test_widget.py"], context
        )
    elif template == "service":
        _generate_file(
            plugin_dir / "src" / python_name / "service.py", templates["service.py"], context
        )
        _generate_file(
            plugin_dir / "tests" / "test_service.py", templates["test_service.py"], context
        )
    elif template == "command":
        _generate_file(
            plugin_dir / "src" / python_name / "commands.py", templates["commands.py"], context
        )
        _generate_file(
            plugin_dir / "tests" / "test_commands.py", templates["test_commands.py"], context
        )


def _generate_file(file_path: Path, template_content: str, context: dict[str, Any]) -> None:
    """Generate a file from template content.

    Args:
        file_path: Target file path
        template_content: Template content
        context: Template context variables
    """
    env = Environment()
    template = env.from_string(template_content)
    content = template.render(**context)

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)


def _to_class_name(name: str) -> str:
    """Convert plugin name to class name.

    Args:
        name: Plugin name

    Returns:
        Class name in PascalCase
    """
    return "".join(word.capitalize() for word in name.replace("-", "_").split("_"))


def _get_embedded_templates() -> dict[str, str]:
    """Get embedded template content.

    Returns:
        Dictionary of template name to content
    """
    return {
        "pyproject.toml": """[project]
name = "{{ plugin_name }}"
version = "0.1.0"
description = "{{ plugin_name }} plugin for ViloxTerm"
readme = "README.md"
requires-python = ">=3.10"
authors = [
    { name = "{{ author }}", email = "{{ email }}" }
]
dependencies = [
    "viloapp-sdk>=0.1.0",
    "PySide6>=6.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-qt>=4.2.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
]

[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
""",
        "plugin.json": """{
    "id": "{{ plugin_id }}",
    "name": "{{ plugin_name }}",
    "version": "0.1.0",
    "description": "{{ plugin_name }} plugin for ViloxTerm",
    "author": {
        "name": "{{ author }}",
        "email": "{{ email }}"
    },
    "license": "MIT",
    "main": "{{ python_name }}.plugin:{{ plugin_class }}Plugin",
    "activation": "onStartup",
    "contributes": {
        {% if template_type == "widget" -%}
        "widgets": [
            {
                "id": "{{ plugin_id }}.widget",
                "title": "{{ plugin_class }} Widget",
                "factory": "{{ python_name }}.widget:{{ plugin_class }}WidgetFactory"
            }
        ]
        {%- elif template_type == "command" -%}
        "commands": [
            {
                "id": "{{ plugin_id }}.hello",
                "title": "Hello Command",
                "description": "Example command"
            }
        ]
        {%- elif template_type == "service" -%}
        "services": [
            {
                "id": "{{ plugin_id }}.service",
                "interface": "{{ python_name }}.service:I{{ plugin_class }}Service",
                "implementation": "{{ python_name }}.service:{{ plugin_class }}Service"
            }
        ]
        {%- else -%}
        "commands": [],
        "widgets": [],
        "services": []
        {%- endif %}
    },
    "dependencies": {},
    "permissions": [
        "viloapp.ui.read"
    ]
}
""",
        "README.md": """# {{ plugin_name }}

{{ plugin_name }} plugin for ViloxTerm.

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

```bash
viloapp install .
```

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run in development mode
viloapp dev --plugin .
```

## Usage

Describe how to use your plugin here.
""",
        "__init__.py": '''"""{{ plugin_name }} plugin for ViloxTerm."""

__version__ = "0.1.0"
''',
        "plugin.py": '''"""Main plugin class for {{ plugin_name }}."""

from viloapp_sdk import IPlugin, PluginContext
from viloapp_sdk.decorators import plugin


@plugin(
    id="{{ plugin_id }}",
    name="{{ plugin_name }}",
    version="0.1.0"
)
class {{ plugin_class }}Plugin(IPlugin):
    """{{ plugin_name }} plugin implementation."""

    def __init__(self) -> None:
        """Initialize the plugin."""
        self._context: PluginContext | None = None

    def activate(self, context: PluginContext) -> None:
        """Activate the plugin.

        Args:
            context: Plugin context
        """
        self._context = context
        # Initialize your plugin here

    def deactivate(self) -> None:
        """Deactivate the plugin."""
        # Clean up resources here
        self._context = None

    def get_id(self) -> str:
        """Get plugin ID."""
        return "{{ plugin_id }}"

    def get_name(self) -> str:
        """Get plugin name."""
        return "{{ plugin_name }}"

    def get_version(self) -> str:
        """Get plugin version."""
        return "0.1.0"
''',
        "widget.py": '''"""Widget implementation for {{ plugin_name }}."""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

from viloapp_sdk import IWidget
from viloapp_sdk.decorators import widget


@widget(
    id="{{ plugin_id }}.widget",
    title="{{ plugin_class }} Widget"
)
class {{ plugin_class }}WidgetFactory(IWidget):
    """Widget factory for {{ plugin_name }}."""

    def get_widget_id(self) -> str:
        """Get widget ID."""
        return "{{ plugin_id }}.widget"

    def get_title(self) -> str:
        """Get widget title."""
        return "{{ plugin_class }} Widget"

    def get_icon(self) -> Optional[str]:
        """Get widget icon."""
        return None

    def create_instance(self, instance_id: str) -> QWidget:
        """Create widget instance.

        Args:
            instance_id: Unique instance identifier

        Returns:
            Widget instance
        """
        return {{ plugin_class }}Widget(instance_id)

    def destroy_instance(self, instance_id: str) -> None:
        """Destroy widget instance.

        Args:
            instance_id: Instance identifier
        """
        # Clean up instance resources
        pass

    def handle_command(self, command: str, args: Dict[str, Any]) -> Any:
        """Handle widget command.

        Args:
            command: Command to execute
            args: Command arguments

        Returns:
            Command result
        """
        # Handle widget-specific commands
        return None

    def get_state(self) -> Dict[str, Any]:
        """Get widget state."""
        return {}

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore widget state.

        Args:
            state: State to restore
        """
        pass


class {{ plugin_class }}Widget(QWidget):
    """{{ plugin_name }} widget implementation."""

    def __init__(self, instance_id: str, parent: Optional[QWidget] = None) -> None:
        """Initialize widget.

        Args:
            instance_id: Unique instance identifier
            parent: Parent widget
        """
        super().__init__(parent)
        self.instance_id = instance_id
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        label = QLabel(f"{{ plugin_class }} Widget\\nInstance: {self.instance_id}")
        layout.addWidget(label)
''',
        "service.py": '''"""Service implementation for {{ plugin_name }}."""

from abc import ABC, abstractmethod
from viloapp_sdk import IService
from viloapp_sdk.decorators import service


class I{{ plugin_class }}Service(ABC):
    """Interface for {{ plugin_class }} service."""

    @abstractmethod
    def do_something(self) -> str:
        """Do something useful.

        Returns:
            Result of the operation
        """
        pass


@service(
    id="{{ plugin_id }}.service",
    interface=I{{ plugin_class }}Service
)
class {{ plugin_class }}Service(IService, I{{ plugin_class }}Service):
    """{{ plugin_name }} service implementation."""

    def do_something(self) -> str:
        """Do something useful.

        Returns:
            Result of the operation
        """
        return "{{ plugin_class }} service did something!"

    def get_service_id(self) -> str:
        """Get service ID."""
        return "{{ plugin_id }}.service"
''',
        "commands.py": '''"""Commands implementation for {{ plugin_name }}."""

from viloapp_sdk import CommandContext, CommandResult
from viloapp_sdk.decorators import command


@command(
    id="{{ plugin_id }}.hello",
    title="Hello Command",
    description="Example command from {{ plugin_name }}"
)
def hello_command(context: CommandContext) -> CommandResult:
    """Example hello command.

    Args:
        context: Command execution context

    Returns:
        Command result
    """
    return CommandResult(
        success=True,
        message="Hello from {{ plugin_name }}!",
        value="Hello World"
    )
''',
        "test_init.py": '''"""Tests package for {{ plugin_name }}."""
''',
        "test_plugin.py": '''"""Tests for {{ plugin_name }} plugin."""

import pytest
from viloapp_sdk.testing import MockPluginHost

from {{ python_name }}.plugin import {{ plugin_class }}Plugin


class Test{{ plugin_class }}Plugin:
    """Tests for {{ plugin_class }}Plugin."""

    def test_plugin_creation(self):
        """Test plugin can be created."""
        plugin = {{ plugin_class }}Plugin()
        assert plugin is not None

    def test_plugin_id(self):
        """Test plugin ID."""
        plugin = {{ plugin_class }}Plugin()
        assert plugin.get_id() == "{{ plugin_id }}"

    def test_plugin_name(self):
        """Test plugin name."""
        plugin = {{ plugin_class }}Plugin()
        assert plugin.get_name() == "{{ plugin_name }}"

    def test_plugin_version(self):
        """Test plugin version."""
        plugin = {{ plugin_class }}Plugin()
        assert plugin.get_version() == "0.1.0"

    def test_plugin_activation(self):
        """Test plugin activation."""
        plugin = {{ plugin_class }}Plugin()
        host = MockPluginHost()
        context = host.create_context("{{ plugin_id }}")

        plugin.activate(context)
        assert plugin._context is not None

    def test_plugin_deactivation(self):
        """Test plugin deactivation."""
        plugin = {{ plugin_class }}Plugin()
        host = MockPluginHost()
        context = host.create_context("{{ plugin_id }}")

        plugin.activate(context)
        plugin.deactivate()
        assert plugin._context is None
''',
        "test_widget.py": '''"""Tests for {{ plugin_name }} widget."""

import pytest
from PySide6.QtWidgets import QApplication
from viloapp_sdk.testing import MockPluginHost

from {{ python_name }}.widget import {{ plugin_class }}WidgetFactory, {{ plugin_class }}Widget


class Test{{ plugin_class }}WidgetFactory:
    """Tests for {{ plugin_class }}WidgetFactory."""

    def test_widget_factory_creation(self):
        """Test widget factory can be created."""
        factory = {{ plugin_class }}WidgetFactory()
        assert factory is not None

    def test_widget_id(self):
        """Test widget ID."""
        factory = {{ plugin_class }}WidgetFactory()
        assert factory.get_widget_id() == "{{ plugin_id }}.widget"

    def test_widget_title(self):
        """Test widget title."""
        factory = {{ plugin_class }}WidgetFactory()
        assert factory.get_title() == "{{ plugin_class }} Widget"

    def test_create_instance(self, qtbot):
        """Test widget instance creation."""
        factory = {{ plugin_class }}WidgetFactory()
        widget = factory.create_instance("test-instance")
        qtbot.addWidget(widget)

        assert isinstance(widget, {{ plugin_class }}Widget)
        assert widget.instance_id == "test-instance"


class Test{{ plugin_class }}Widget:
    """Tests for {{ plugin_class }}Widget."""

    def test_widget_creation(self, qtbot):
        """Test widget can be created."""
        widget = {{ plugin_class }}Widget("test-instance")
        qtbot.addWidget(widget)
        assert widget is not None
        assert widget.instance_id == "test-instance"
''',
        "test_service.py": '''"""Tests for {{ plugin_name }} service."""

import pytest
from {{ python_name }}.service import {{ plugin_class }}Service


class Test{{ plugin_class }}Service:
    """Tests for {{ plugin_class }}Service."""

    def test_service_creation(self):
        """Test service can be created."""
        service = {{ plugin_class }}Service()
        assert service is not None

    def test_service_id(self):
        """Test service ID."""
        service = {{ plugin_class }}Service()
        assert service.get_service_id() == "{{ plugin_id }}.service"

    def test_do_something(self):
        """Test service functionality."""
        service = {{ plugin_class }}Service()
        result = service.do_something()
        assert result == "{{ plugin_class }} service did something!"
''',
        "test_commands.py": '''"""Tests for {{ plugin_name }} commands."""

import pytest
from viloapp_sdk.testing import MockPluginHost

from {{ python_name }}.commands import hello_command


class TestCommands:
    """Tests for {{ plugin_name }} commands."""

    def test_hello_command(self):
        """Test hello command."""
        host = MockPluginHost()
        context = host.create_context("{{ plugin_id }}")

        result = hello_command(context)
        assert result.success is True
        assert "Hello from {{ plugin_name }}!" in result.message
        assert result.value == "Hello World"
''',
    }
