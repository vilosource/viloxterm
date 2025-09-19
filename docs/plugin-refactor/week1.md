# Week 1: Foundation and SDK Development

## Overview
Week 1 focuses on establishing the monorepo structure and developing the Plugin SDK that will serve as the foundation for all plugins.

**Duration**: 5 days
**Goal**: Complete monorepo setup and functional Plugin SDK with tests

## Day 1: Monorepo Structure Setup

### Morning (2-3 hours)

#### Task 1.1: Create Base Directory Structure
```bash
cd /home/kuja/GitHub/viloapp

# Create packages directory structure
mkdir -p packages/{viloapp-sdk,viloxterm,viloedit,viloapp}/{src,tests,docs}

# Create scripts directory
mkdir -p scripts

# Create plugin development docs
mkdir -p docs/plugin-development/{guides,api,examples}

# Create build directory
mkdir -p build
```

#### Task 1.2: Setup Git Configuration
```bash
# Create .gitignore for monorepo
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
.direnv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.coverage
.pytest_cache/
htmlcov/

# Package specific
packages/*/dist/
packages/*/build/
EOF
```

#### Task 1.3: Create Root Configuration Files

Create `/home/kuja/GitHub/viloapp/pyproject.toml`:
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "viloapp-workspace"
version = "0.0.1"
description = "ViloxTerm monorepo workspace"
readme = "README.md"
requires-python = ">=3.8"

[tool.hatch]
# Workspace configuration
[tool.hatch.build]
packages = [
    "packages/viloapp-sdk",
    "packages/viloxterm",
    "packages/viloedit",
    "packages/viloapp"
]

[tool.pytest]
testpaths = ["packages/*/tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

[tool.ruff]
src = ["packages/*/src"]
extend-include = ["packages/*/tests/*.py"]
line-length = 100
target-version = "py38"

[tool.mypy]
packages = ["viloapp", "viloapp_sdk", "viloxterm", "viloedit"]
namespace_packages = true
explicit_package_bases = true
python_version = "3.8"

[tool.black]
line-length = 100
target-version = ['py38']
include = 'packages/.*\.py$'
```

### Afternoon (3-4 hours)

#### Task 1.4: Create Development Scripts

Create `/home/kuja/GitHub/viloapp/scripts/dev-setup.py`:
```python
#!/usr/bin/env python3
"""Setup development environment for ViloxTerm monorepo."""

import subprocess
import sys
import os
from pathlib import Path
from typing import List, Tuple

# Package installation order (respecting dependencies)
PACKAGES = [
    ("viloapp-sdk", []),
    ("viloxterm", ["viloapp-sdk"]),
    ("viloedit", ["viloapp-sdk"]),
    ("viloapp", ["viloapp-sdk"])
]

def run_command(cmd: List[str], cwd: Path = None) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr

def install_package(package_dir: Path, editable: bool = True) -> bool:
    """Install a single package."""
    print(f"Installing {package_dir.name}...")

    install_cmd = [sys.executable, "-m", "pip", "install"]
    if editable:
        install_cmd.append("-e")
    install_cmd.append(str(package_dir))

    returncode, stdout, stderr = run_command(install_cmd)

    if returncode != 0:
        print(f"Error installing {package_dir.name}:")
        print(stderr)
        return False

    print(f"✓ {package_dir.name} installed successfully")
    return True

def main():
    """Main setup function."""
    root = Path(__file__).parent.parent
    packages_dir = root / "packages"

    print("ViloxTerm Development Environment Setup")
    print("=" * 40)

    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: Python 3.8+ is required")
        sys.exit(1)

    # Install development dependencies
    print("\nInstalling development dependencies...")
    dev_deps = ["pytest", "pytest-qt", "pytest-cov", "black", "ruff", "mypy"]
    run_command([sys.executable, "-m", "pip", "install"] + dev_deps)

    # Install packages in order
    print("\nInstalling packages...")
    success = True
    for package_name, _ in PACKAGES:
        package_path = packages_dir / package_name
        if package_path.exists():
            if not install_package(package_path):
                success = False
                break

    if success:
        print("\n✅ Development environment setup complete!")
        print("\nYou can now run:")
        print("  make test     - Run all tests")
        print("  make format   - Format code")
        print("  make lint     - Lint code")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

Create `/home/kuja/GitHub/viloapp/scripts/build.py`:
```python
#!/usr/bin/env python3
"""Build all packages in the monorepo."""

import subprocess
import sys
import shutil
from pathlib import Path
from typing import List

PACKAGES = [
    "viloapp-sdk",
    "viloxterm",
    "viloedit",
    "viloapp"
]

def clean_package(package_dir: Path):
    """Clean build artifacts from a package."""
    dirs_to_remove = ["build", "dist", "*.egg-info"]
    for pattern in dirs_to_remove:
        for path in package_dir.glob(pattern):
            if path.is_dir():
                print(f"  Removing {path}")
                shutil.rmtree(path)

def build_package(package_dir: Path) -> bool:
    """Build a single package."""
    print(f"Building {package_dir.name}...")

    # Clean first
    clean_package(package_dir)

    # Build
    result = subprocess.run(
        [sys.executable, "-m", "build"],
        cwd=package_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Failed to build {package_dir.name}")
        print(result.stderr)
        return False

    print(f"✓ {package_dir.name} built successfully")

    # List built files
    dist_dir = package_dir / "dist"
    if dist_dir.exists():
        for file in dist_dir.iterdir():
            print(f"    - {file.name}")

    return True

def main():
    """Build all packages."""
    root = Path(__file__).parent.parent
    packages_dir = root / "packages"

    print("Building ViloxTerm Packages")
    print("=" * 40)

    # Install build dependencies
    print("Installing build dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "build"])

    # Build each package
    all_success = True
    for package in PACKAGES:
        package_dir = packages_dir / package
        if package_dir.exists():
            if not build_package(package_dir):
                all_success = False
                break
        else:
            print(f"Warning: Package {package} does not exist yet")

    if all_success:
        print("\n✅ All packages built successfully!")
    else:
        print("\n❌ Build failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### Task 1.5: Create Makefile for Common Tasks

Create `/home/kuja/GitHub/viloapp/Makefile`:
```makefile
.PHONY: help setup dev test test-sdk test-terminal test-editor test-app build format lint typecheck clean

help:
	@echo "ViloxTerm Monorepo Commands"
	@echo "============================"
	@echo "  setup        - Setup development environment"
	@echo "  dev          - Run in development mode"
	@echo "  test         - Run all tests"
	@echo "  test-sdk     - Test SDK package"
	@echo "  test-terminal- Test terminal plugin"
	@echo "  test-editor  - Test editor plugin"
	@echo "  test-app     - Test main application"
	@echo "  build        - Build all packages"
	@echo "  format       - Format code with black"
	@echo "  lint         - Lint code with ruff"
	@echo "  typecheck    - Type check with mypy"
	@echo "  clean        - Clean build artifacts"

setup:
	python scripts/dev-setup.py

dev:
	cd packages/viloapp && python -m viloapp.main --dev

test:
	pytest packages/*/tests -v

test-sdk:
	pytest packages/viloapp-sdk/tests -v

test-terminal:
	pytest packages/viloxterm/tests -v

test-editor:
	pytest packages/viloedit/tests -v

test-app:
	pytest packages/viloapp/tests -v

build:
	python scripts/build.py

format:
	black packages/*/src packages/*/tests

lint:
	ruff check packages/*/src packages/*/tests

typecheck:
	mypy packages/*/src

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -path "*/packages/*" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -path "*/packages/*" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov
```

### Validation Checkpoint
- [ ] All directories created successfully
- [ ] Configuration files in place
- [ ] Scripts are executable
- [ ] Makefile works (`make help` shows commands)

## Day 2: SDK Package Structure

### Morning (3 hours)

#### Task 2.1: Create SDK Package Configuration

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "viloapp-sdk"
version = "1.0.0"
description = "ViloxTerm Plugin SDK - Build powerful plugins for ViloxTerm"
authors = [{name = "ViloxTerm Team", email = "team@viloxterm.org"}]
readme = "README.md"
license = {text = "MIT"}
keywords = ["plugin", "sdk", "terminal", "editor", "extensibility"]
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Software Development :: Libraries :: Application Frameworks",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

dependencies = [
    "PySide6>=6.5.0",
    "typing-extensions>=4.0.0;python_version<'3.10'",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-qt>=4.2.0",
    "pytest-cov>=4.0",
    "mypy>=1.0",
    "black>=23.0",
    "ruff>=0.1.0",
]
docs = [
    "sphinx>=5.0",
    "sphinx-autodoc-typehints>=1.0",
    "sphinx-rtd-theme>=1.0",
]

[project.urls]
Homepage = "https://github.com/viloxterm/viloapp"
Documentation = "https://viloxterm.readthedocs.io"
Repository = "https://github.com/viloxterm/viloapp"
Issues = "https://github.com/viloxterm/viloapp/issues"

[tool.setuptools]
package-dir = {"": "src"}
packages = ["viloapp_sdk"]

[tool.setuptools.package-data]
viloapp_sdk = ["py.typed"]
```

#### Task 2.2: Create SDK README

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/README.md`:
```markdown
# ViloxTerm Plugin SDK

Build powerful plugins for ViloxTerm with the official Plugin SDK.

## Installation

```bash
pip install viloapp-sdk
```

## Quick Start

```python
from viloapp_sdk import IPlugin, PluginMetadata

class MyPlugin(IPlugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="my-plugin",
            name="My Plugin",
            version="1.0.0",
            description="A sample plugin"
        )

    def activate(self, context):
        print("Plugin activated!")

    def deactivate(self):
        print("Plugin deactivated!")
```

## Documentation

Full documentation available at: https://viloxterm.readthedocs.io

## License

MIT
```

#### Task 2.3: Create SDK Package Structure

```bash
cd /home/kuja/GitHub/viloapp/packages/viloapp-sdk/src/viloapp_sdk

# Create type stub file for type checking
touch py.typed

# Create package structure
touch __init__.py plugin.py widget.py service.py events.py lifecycle.py types.py exceptions.py context.py
```

### Afternoon (3 hours)

#### Task 2.4: Implement Core Module

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/src/viloapp_sdk/__init__.py`:
```python
"""
ViloxTerm Plugin SDK.

Build powerful plugins for ViloxTerm terminal emulator and editor.
"""

from .plugin import IPlugin, PluginMetadata, PluginCapability
from .widget import IWidget, WidgetMetadata, WidgetPosition
from .service import IService, ServiceProxy, ServiceNotAvailableError
from .events import EventBus, PluginEvent, EventType, EventPriority
from .lifecycle import ILifecycle, LifecycleState, LifecycleHook
from .context import PluginContext, IPluginContext
from .types import (
    CommandContribution,
    MenuContribution,
    KeybindingContribution,
    ConfigurationContribution
)
from .exceptions import (
    PluginError,
    PluginLoadError,
    PluginActivationError,
    PluginDependencyError
)

__version__ = "1.0.0"

__all__ = [
    # Plugin interfaces
    "IPlugin",
    "PluginMetadata",
    "PluginCapability",

    # Widget interfaces
    "IWidget",
    "WidgetMetadata",
    "WidgetPosition",

    # Service interfaces
    "IService",
    "ServiceProxy",
    "ServiceNotAvailableError",

    # Event system
    "EventBus",
    "PluginEvent",
    "EventType",
    "EventPriority",

    # Lifecycle
    "ILifecycle",
    "LifecycleState",
    "LifecycleHook",

    # Context
    "PluginContext",
    "IPluginContext",

    # Types
    "CommandContribution",
    "MenuContribution",
    "KeybindingContribution",
    "ConfigurationContribution",

    # Exceptions
    "PluginError",
    "PluginLoadError",
    "PluginActivationError",
    "PluginDependencyError",
]
```

#### Task 2.5: Create Type Definitions

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/src/viloapp_sdk/types.py`:
```python
"""Type definitions for plugin SDK."""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

@dataclass
class CommandContribution:
    """Command contribution from a plugin."""
    id: str
    title: str
    category: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    enablement: Optional[str] = None  # When condition

@dataclass
class MenuContribution:
    """Menu contribution from a plugin."""
    command_id: str
    group: str
    order: Optional[int] = None
    when: Optional[str] = None  # Context expression

@dataclass
class KeybindingContribution:
    """Keybinding contribution from a plugin."""
    command_id: str
    key: str
    when: Optional[str] = None
    mac: Optional[str] = None  # Mac-specific binding
    linux: Optional[str] = None  # Linux-specific binding
    win: Optional[str] = None  # Windows-specific binding

@dataclass
class ConfigurationContribution:
    """Configuration contribution from a plugin."""
    key: str
    title: str
    description: str
    type: str  # "string", "number", "boolean", "array", "object"
    default: Any
    enum: Optional[List[Any]] = None
    minimum: Optional[Union[int, float]] = None
    maximum: Optional[Union[int, float]] = None
```

### Validation Checkpoint
- [ ] SDK package structure created
- [ ] Configuration files complete
- [ ] Type definitions in place
- [ ] Package can be imported (after basic implementation)

## Day 3: Core Interfaces Implementation

### Morning (3-4 hours)

#### Task 3.1: Implement Plugin Interface

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/src/viloapp_sdk/plugin.py`:
```python
"""Plugin interface and metadata definitions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

class PluginCapability(Enum):
    """Plugin capabilities that can be declared."""
    WIDGETS = "widgets"
    COMMANDS = "commands"
    THEMES = "themes"
    LANGUAGES = "languages"
    DEBUGGERS = "debuggers"
    TERMINALS = "terminals"
    EDITORS = "editors"
    VIEWS = "views"
    SETTINGS = "settings"

@dataclass
class PluginMetadata:
    """Plugin metadata and manifest information."""
    # Required fields
    id: str
    name: str
    version: str
    description: str
    author: str

    # Optional fields
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = None
    icon: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)

    # Technical fields
    engines: Dict[str, str] = field(default_factory=dict)  # {"viloapp": ">=2.0.0"}
    dependencies: List[str] = field(default_factory=list)
    activation_events: List[str] = field(default_factory=list)
    capabilities: List[PluginCapability] = field(default_factory=list)

    # Contributions
    contributes: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Validate metadata and return list of errors."""
        errors = []

        if not self.id:
            errors.append("Plugin ID is required")
        if not self.name:
            errors.append("Plugin name is required")
        if not self.version:
            errors.append("Plugin version is required")
        if not self.description:
            errors.append("Plugin description is required")
        if not self.author:
            errors.append("Plugin author is required")

        # Validate ID format (alphanumeric with hyphens)
        if self.id and not all(c.isalnum() or c == '-' for c in self.id):
            errors.append("Plugin ID must be alphanumeric with hyphens only")

        return errors

class IPlugin(ABC):
    """Base interface for all plugins."""

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """
        Get plugin metadata.

        Returns:
            PluginMetadata: The plugin's metadata
        """
        pass

    @abstractmethod
    def activate(self, context: 'IPluginContext') -> None:
        """
        Called when the plugin is activated.

        Args:
            context: Plugin context providing access to host services
        """
        pass

    @abstractmethod
    def deactivate(self) -> None:
        """
        Called when the plugin is deactivated.

        Should clean up resources, unregister handlers, etc.
        """
        pass

    def on_configuration_changed(self, config: Dict[str, Any]) -> None:
        """
        Called when plugin configuration changes.

        Args:
            config: Updated configuration dictionary
        """
        pass

    def on_command(self, command_id: str, args: Dict[str, Any]) -> Any:
        """
        Handle command execution.

        Args:
            command_id: The command ID to execute
            args: Command arguments

        Returns:
            Command result
        """
        pass
```

#### Task 3.2: Implement Widget Interface

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/src/viloapp_sdk/widget.py`:
```python
"""Widget interface and related definitions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple
from enum import Enum
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal

class WidgetPosition(Enum):
    """Available widget positions."""
    MAIN = "main"  # Main workspace area
    SIDEBAR = "sidebar"  # Left sidebar
    PANEL = "panel"  # Bottom panel
    AUXILIARY = "auxiliary"  # Right sidebar
    FLOATING = "floating"  # Floating window

@dataclass
class WidgetMetadata:
    """Widget metadata."""
    id: str
    title: str
    position: WidgetPosition = WidgetPosition.MAIN
    icon: Optional[str] = None
    closable: bool = True
    singleton: bool = False  # Only one instance allowed
    priority: int = 0  # Higher priority shown first
    default_size: Optional[Tuple[int, int]] = None
    min_size: Optional[Tuple[int, int]] = None
    max_size: Optional[Tuple[int, int]] = None

class IWidget(ABC):
    """Interface for plugin-provided widgets."""

    @abstractmethod
    def get_metadata(self) -> WidgetMetadata:
        """Get widget metadata."""
        pass

    @abstractmethod
    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """
        Create and return the Qt widget.

        Args:
            parent: Parent widget

        Returns:
            QWidget: The created widget
        """
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """
        Get widget state for persistence.

        Returns:
            Dict containing widget state
        """
        pass

    @abstractmethod
    def restore_state(self, state: Dict[str, Any]) -> None:
        """
        Restore widget state.

        Args:
            state: Previously saved state
        """
        pass

    def on_focus(self) -> None:
        """Called when widget receives focus."""
        pass

    def on_blur(self) -> None:
        """Called when widget loses focus."""
        pass

    def on_resize(self, width: int, height: int) -> None:
        """
        Called when widget is resized.

        Args:
            width: New width
            height: New height
        """
        pass

    def on_close(self) -> bool:
        """
        Called when widget is about to close.

        Returns:
            True to allow closing, False to prevent
        """
        return True

    def get_toolbar_actions(self) -> List[Dict[str, Any]]:
        """
        Get toolbar actions for this widget.

        Returns:
            List of action definitions
        """
        return []

    def get_context_menu_actions(self) -> List[Dict[str, Any]]:
        """
        Get context menu actions for this widget.

        Returns:
            List of action definitions
        """
        return []
```

### Afternoon (3 hours)

#### Task 3.3: Implement Event System

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/src/viloapp_sdk/events.py`:
```python
"""Event system for plugin communication."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum, auto
import time
import uuid
from threading import Lock

class EventType(Enum):
    """Standard event types."""
    # Lifecycle events
    PLUGIN_LOADED = "plugin.loaded"
    PLUGIN_UNLOADED = "plugin.unloaded"
    PLUGIN_ACTIVATED = "plugin.activated"
    PLUGIN_DEACTIVATED = "plugin.deactivated"

    # Widget events
    WIDGET_CREATED = "widget.created"
    WIDGET_DESTROYED = "widget.destroyed"
    WIDGET_FOCUSED = "widget.focused"
    WIDGET_BLURRED = "widget.blurred"
    WIDGET_STATE_CHANGED = "widget.state_changed"

    # System events
    SETTINGS_CHANGED = "settings.changed"
    THEME_CHANGED = "theme.changed"
    LANGUAGE_CHANGED = "language.changed"

    # Command events
    COMMAND_EXECUTED = "command.executed"
    COMMAND_REGISTERED = "command.registered"
    COMMAND_UNREGISTERED = "command.unregistered"

    # Service events
    SERVICE_REGISTERED = "service.registered"
    SERVICE_UNREGISTERED = "service.unregistered"

    # Custom events
    CUSTOM = "custom"

class EventPriority(Enum):
    """Event priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class PluginEvent:
    """Event data structure."""
    type: EventType
    source: str  # Plugin ID or system component
    data: Dict[str, Any] = field(default_factory=dict)
    target: Optional[str] = None  # Target plugin ID or None for broadcast
    priority: EventPriority = EventPriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def is_broadcast(self) -> bool:
        """Check if this is a broadcast event."""
        return self.target is None

    def matches_filter(self, filter_func: Optional[Callable]) -> bool:
        """Check if event matches a filter function."""
        if filter_func is None:
            return True
        try:
            return filter_func(self)
        except Exception:
            return False

class EventSubscription:
    """Represents an event subscription."""

    def __init__(
        self,
        event_type: EventType,
        handler: Callable[[PluginEvent], None],
        filter_func: Optional[Callable[[PluginEvent], bool]] = None,
        priority: EventPriority = EventPriority.NORMAL,
        subscriber_id: Optional[str] = None
    ):
        self.event_type = event_type
        self.handler = handler
        self.filter_func = filter_func
        self.priority = priority
        self.subscriber_id = subscriber_id or str(uuid.uuid4())
        self.active = True

    def handle(self, event: PluginEvent) -> None:
        """Handle an event if it matches the filter."""
        if self.active and event.matches_filter(self.filter_func):
            self.handler(event)

    def unsubscribe(self) -> None:
        """Mark subscription as inactive."""
        self.active = False

class EventBus:
    """Central event bus for plugin communication."""

    def __init__(self):
        self._subscriptions: Dict[EventType, List[EventSubscription]] = {}
        self._lock = Lock()
        self._event_history: List[PluginEvent] = []
        self._history_limit = 1000

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[PluginEvent], None],
        filter_func: Optional[Callable[[PluginEvent], bool]] = None,
        priority: EventPriority = EventPriority.NORMAL,
        subscriber_id: Optional[str] = None
    ) -> EventSubscription:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Function to call when event occurs
            filter_func: Optional filter function
            priority: Subscription priority
            subscriber_id: Optional subscriber ID

        Returns:
            EventSubscription object
        """
        subscription = EventSubscription(
            event_type, handler, filter_func, priority, subscriber_id
        )

        with self._lock:
            if event_type not in self._subscriptions:
                self._subscriptions[event_type] = []

            # Insert sorted by priority (highest first)
            subscriptions = self._subscriptions[event_type]
            insert_idx = len(subscriptions)
            for i, sub in enumerate(subscriptions):
                if sub.priority.value < subscription.priority.value:
                    insert_idx = i
                    break
            subscriptions.insert(insert_idx, subscription)

        return subscription

    def unsubscribe(self, subscription: EventSubscription) -> None:
        """
        Unsubscribe from events.

        Args:
            subscription: Subscription to remove
        """
        subscription.unsubscribe()

        with self._lock:
            if subscription.event_type in self._subscriptions:
                self._subscriptions[subscription.event_type] = [
                    sub for sub in self._subscriptions[subscription.event_type]
                    if sub.subscriber_id != subscription.subscriber_id
                ]

    def emit(self, event: PluginEvent) -> None:
        """
        Emit an event to all subscribers.

        Args:
            event: Event to emit
        """
        # Add to history
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._history_limit:
                self._event_history.pop(0)

        # Get relevant subscriptions
        subscriptions = []
        with self._lock:
            if event.type in self._subscriptions:
                subscriptions = list(self._subscriptions[event.type])

        # Handle event with each subscription
        for subscription in subscriptions:
            if subscription.active:
                try:
                    subscription.handle(event)
                except Exception as e:
                    # Log error but don't stop processing
                    print(f"Error handling event {event.event_id}: {e}")

    def emit_async(self, event: PluginEvent) -> None:
        """
        Emit an event asynchronously.

        Args:
            event: Event to emit
        """
        # This would be implemented with threading or asyncio
        # For now, just emit synchronously
        self.emit(event)

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[PluginEvent]:
        """
        Get event history.

        Args:
            event_type: Filter by event type
            source: Filter by source
            limit: Maximum number of events

        Returns:
            List of events matching criteria
        """
        with self._lock:
            events = list(self._event_history)

        # Apply filters
        if event_type:
            events = [e for e in events if e.type == event_type]
        if source:
            events = [e for e in events if e.source == source]

        return events[-limit:]
```

### Validation Checkpoint
- [ ] All interfaces implemented
- [ ] Event system functional
- [ ] No import errors
- [ ] Type hints complete

## Day 4: Service Layer and Context

### Morning (3 hours)

#### Task 4.1: Implement Service Interface

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/src/viloapp_sdk/service.py`:
```python
"""Service interface and proxy for plugin-host communication."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from dataclasses import dataclass

T = TypeVar('T')

class ServiceNotAvailableError(Exception):
    """Raised when a requested service is not available."""
    pass

class IService(ABC):
    """Base interface for services exposed to plugins."""

    @abstractmethod
    def get_service_id(self) -> str:
        """Get unique service identifier."""
        pass

    @abstractmethod
    def get_service_version(self) -> str:
        """Get service version."""
        pass

@dataclass
class ServiceDescriptor:
    """Describes a service available to plugins."""
    id: str
    version: str
    interface: Type[IService]
    description: str
    optional: bool = False

class ServiceProxy:
    """Proxy for accessing host services from plugins."""

    def __init__(self, services: Dict[str, IService]):
        self._services = services
        self._service_cache = {}

    def get_service(self, service_id: str) -> Optional[IService]:
        """
        Get a service by ID.

        Args:
            service_id: Service identifier

        Returns:
            Service instance or None
        """
        if service_id in self._service_cache:
            return self._service_cache[service_id]

        service = self._services.get(service_id)
        if service:
            self._service_cache[service_id] = service

        return service

    def require_service(self, service_id: str) -> IService:
        """
        Get a required service by ID.

        Args:
            service_id: Service identifier

        Returns:
            Service instance

        Raises:
            ServiceNotAvailableError: If service is not available
        """
        service = self.get_service(service_id)
        if not service:
            raise ServiceNotAvailableError(f"Service '{service_id}' is not available")
        return service

    def get_service_typed(self, service_type: Type[T]) -> Optional[T]:
        """
        Get a service by type.

        Args:
            service_type: Service class type

        Returns:
            Service instance or None
        """
        for service in self._services.values():
            if isinstance(service, service_type):
                return service
        return None

    def has_service(self, service_id: str) -> bool:
        """
        Check if a service is available.

        Args:
            service_id: Service identifier

        Returns:
            True if service is available
        """
        return service_id in self._services

    def list_services(self) -> List[str]:
        """
        List all available service IDs.

        Returns:
            List of service IDs
        """
        return list(self._services.keys())

# Standard service interfaces

class ICommandService(IService):
    """Service for executing commands."""

    @abstractmethod
    def execute_command(self, command_id: str, **kwargs) -> Any:
        """Execute a command."""
        pass

    @abstractmethod
    def register_command(self, command_id: str, handler: callable) -> None:
        """Register a command handler."""
        pass

    @abstractmethod
    def unregister_command(self, command_id: str) -> None:
        """Unregister a command."""
        pass

class IConfigurationService(IService):
    """Service for accessing configuration."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        pass

    @abstractmethod
    def on_change(self, key: str, callback: callable) -> None:
        """Register configuration change listener."""
        pass

class IWorkspaceService(IService):
    """Service for workspace operations."""

    @abstractmethod
    def open_file(self, path: str) -> None:
        """Open a file in the workspace."""
        pass

    @abstractmethod
    def get_active_editor(self) -> Optional[Any]:
        """Get the active editor."""
        pass

    @abstractmethod
    def create_pane(self, widget: Any, position: str) -> None:
        """Create a new pane with a widget."""
        pass

class IThemeService(IService):
    """Service for theme operations."""

    @abstractmethod
    def get_current_theme(self) -> Dict[str, Any]:
        """Get current theme."""
        pass

    @abstractmethod
    def get_color(self, key: str) -> str:
        """Get theme color."""
        pass

    @abstractmethod
    def on_theme_changed(self, callback: callable) -> None:
        """Register theme change listener."""
        pass

class INotificationService(IService):
    """Service for showing notifications."""

    @abstractmethod
    def info(self, message: str, title: Optional[str] = None) -> None:
        """Show info notification."""
        pass

    @abstractmethod
    def warning(self, message: str, title: Optional[str] = None) -> None:
        """Show warning notification."""
        pass

    @abstractmethod
    def error(self, message: str, title: Optional[str] = None) -> None:
        """Show error notification."""
        pass
```

#### Task 4.2: Implement Plugin Context

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/src/viloapp_sdk/context.py`:
```python
"""Plugin context for accessing host functionality."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

from .service import ServiceProxy, IService
from .events import EventBus

class IPluginContext(ABC):
    """Interface for plugin context."""

    @abstractmethod
    def get_plugin_id(self) -> str:
        """Get the plugin ID."""
        pass

    @abstractmethod
    def get_plugin_path(self) -> Path:
        """Get plugin installation path."""
        pass

    @abstractmethod
    def get_data_path(self) -> Path:
        """Get plugin data storage path."""
        pass

    @abstractmethod
    def get_service_proxy(self) -> ServiceProxy:
        """Get service proxy for accessing host services."""
        pass

    @abstractmethod
    def get_event_bus(self) -> EventBus:
        """Get event bus for plugin communication."""
        pass

    @abstractmethod
    def get_configuration(self) -> Dict[str, Any]:
        """Get plugin configuration."""
        pass

class PluginContext(IPluginContext):
    """Implementation of plugin context."""

    def __init__(
        self,
        plugin_id: str,
        plugin_path: Path,
        data_path: Path,
        service_proxy: ServiceProxy,
        event_bus: EventBus,
        configuration: Optional[Dict[str, Any]] = None
    ):
        self._plugin_id = plugin_id
        self._plugin_path = plugin_path
        self._data_path = data_path
        self._service_proxy = service_proxy
        self._event_bus = event_bus
        self._configuration = configuration or {}

    def get_plugin_id(self) -> str:
        return self._plugin_id

    def get_plugin_path(self) -> Path:
        return self._plugin_path

    def get_data_path(self) -> Path:
        """Get plugin data path, creating if necessary."""
        self._data_path.mkdir(parents=True, exist_ok=True)
        return self._data_path

    def get_service_proxy(self) -> ServiceProxy:
        return self._service_proxy

    def get_event_bus(self) -> EventBus:
        return self._event_bus

    def get_configuration(self) -> Dict[str, Any]:
        return self._configuration.copy()

    # Convenience methods

    def get_service(self, service_id: str) -> Optional[IService]:
        """Shortcut to get a service."""
        return self._service_proxy.get_service(service_id)

    def emit_event(self, event_type, data: Dict[str, Any] = None) -> None:
        """Shortcut to emit an event."""
        from .events import PluginEvent

        event = PluginEvent(
            type=event_type,
            source=self._plugin_id,
            data=data or {}
        )
        self._event_bus.emit(event)

    def subscribe_event(self, event_type, handler) -> None:
        """Shortcut to subscribe to an event."""
        self._event_bus.subscribe(
            event_type,
            handler,
            subscriber_id=self._plugin_id
        )
```

### Afternoon (3 hours)

#### Task 4.3: Implement Lifecycle Management

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/src/viloapp_sdk/lifecycle.py`:
```python
"""Plugin lifecycle management."""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional, List, Callable
from dataclasses import dataclass, field

class LifecycleState(Enum):
    """Plugin lifecycle states."""
    DISCOVERED = auto()  # Plugin found but not loaded
    LOADED = auto()      # Plugin code loaded
    ACTIVATED = auto()   # Plugin activated and running
    DEACTIVATED = auto() # Plugin deactivated
    FAILED = auto()      # Plugin failed to load/activate
    UNLOADED = auto()    # Plugin unloaded from memory

class LifecycleHook(Enum):
    """Lifecycle hook points."""
    BEFORE_LOAD = "before_load"
    AFTER_LOAD = "after_load"
    BEFORE_ACTIVATE = "before_activate"
    AFTER_ACTIVATE = "after_activate"
    BEFORE_DEACTIVATE = "before_deactivate"
    AFTER_DEACTIVATE = "after_deactivate"
    BEFORE_UNLOAD = "before_unload"
    AFTER_UNLOAD = "after_unload"

@dataclass
class LifecycleTransition:
    """Represents a state transition."""
    from_state: LifecycleState
    to_state: LifecycleState
    timestamp: float
    reason: Optional[str] = None
    error: Optional[Exception] = None

class ILifecycle(ABC):
    """Interface for lifecycle management."""

    @abstractmethod
    def get_state(self) -> LifecycleState:
        """Get current lifecycle state."""
        pass

    @abstractmethod
    def can_transition_to(self, state: LifecycleState) -> bool:
        """Check if transition to state is valid."""
        pass

    @abstractmethod
    def add_hook(self, hook: LifecycleHook, callback: Callable) -> None:
        """Add a lifecycle hook."""
        pass

    @abstractmethod
    def remove_hook(self, hook: LifecycleHook, callback: Callable) -> None:
        """Remove a lifecycle hook."""
        pass

    @abstractmethod
    def get_transition_history(self) -> List[LifecycleTransition]:
        """Get state transition history."""
        pass

class PluginLifecycle(ILifecycle):
    """Implementation of plugin lifecycle management."""

    # Valid state transitions
    VALID_TRANSITIONS = {
        LifecycleState.DISCOVERED: [LifecycleState.LOADED, LifecycleState.FAILED],
        LifecycleState.LOADED: [LifecycleState.ACTIVATED, LifecycleState.FAILED, LifecycleState.UNLOADED],
        LifecycleState.ACTIVATED: [LifecycleState.DEACTIVATED, LifecycleState.FAILED],
        LifecycleState.DEACTIVATED: [LifecycleState.ACTIVATED, LifecycleState.UNLOADED],
        LifecycleState.FAILED: [LifecycleState.UNLOADED],
        LifecycleState.UNLOADED: [LifecycleState.LOADED]
    }

    def __init__(self):
        self._state = LifecycleState.DISCOVERED
        self._hooks: Dict[LifecycleHook, List[Callable]] = {}
        self._history: List[LifecycleTransition] = []

    def get_state(self) -> LifecycleState:
        return self._state

    def can_transition_to(self, state: LifecycleState) -> bool:
        """Check if transition is valid."""
        return state in self.VALID_TRANSITIONS.get(self._state, [])

    def transition_to(
        self,
        state: LifecycleState,
        reason: Optional[str] = None,
        error: Optional[Exception] = None
    ) -> bool:
        """
        Transition to a new state.

        Returns:
            True if transition was successful
        """
        if not self.can_transition_to(state):
            return False

        # Create transition record
        import time
        transition = LifecycleTransition(
            from_state=self._state,
            to_state=state,
            timestamp=time.time(),
            reason=reason,
            error=error
        )

        # Execute hooks
        self._execute_hooks_for_transition(self._state, state)

        # Update state
        self._state = state
        self._history.append(transition)

        return True

    def add_hook(self, hook: LifecycleHook, callback: Callable) -> None:
        """Add a lifecycle hook."""
        if hook not in self._hooks:
            self._hooks[hook] = []
        self._hooks[hook].append(callback)

    def remove_hook(self, hook: LifecycleHook, callback: Callable) -> None:
        """Remove a lifecycle hook."""
        if hook in self._hooks:
            self._hooks[hook] = [h for h in self._hooks[hook] if h != callback]

    def get_transition_history(self) -> List[LifecycleTransition]:
        """Get state transition history."""
        return list(self._history)

    def _execute_hooks_for_transition(
        self,
        from_state: LifecycleState,
        to_state: LifecycleState
    ) -> None:
        """Execute relevant hooks for a state transition."""
        # Map transitions to hooks
        hook_mapping = {
            (LifecycleState.DISCOVERED, LifecycleState.LOADED): [
                LifecycleHook.BEFORE_LOAD, LifecycleHook.AFTER_LOAD
            ],
            (LifecycleState.LOADED, LifecycleState.ACTIVATED): [
                LifecycleHook.BEFORE_ACTIVATE, LifecycleHook.AFTER_ACTIVATE
            ],
            (LifecycleState.ACTIVATED, LifecycleState.DEACTIVATED): [
                LifecycleHook.BEFORE_DEACTIVATE, LifecycleHook.AFTER_DEACTIVATE
            ],
            (LifecycleState.DEACTIVATED, LifecycleState.UNLOADED): [
                LifecycleHook.BEFORE_UNLOAD, LifecycleHook.AFTER_UNLOAD
            ],
        }

        hooks_to_execute = hook_mapping.get((from_state, to_state), [])

        for hook in hooks_to_execute:
            if hook in self._hooks:
                for callback in self._hooks[hook]:
                    try:
                        callback()
                    except Exception as e:
                        # Log but don't fail the transition
                        print(f"Hook {hook} failed: {e}")
```

#### Task 4.4: Implement Exceptions

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/src/viloapp_sdk/exceptions.py`:
```python
"""Exception types for plugin SDK."""

class PluginError(Exception):
    """Base exception for plugin-related errors."""
    pass

class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""
    pass

class PluginActivationError(PluginError):
    """Raised when a plugin fails to activate."""
    pass

class PluginDependencyError(PluginError):
    """Raised when plugin dependencies are not met."""
    pass

class PluginVersionError(PluginError):
    """Raised when plugin version requirements are not met."""
    pass

class PluginConfigurationError(PluginError):
    """Raised when plugin configuration is invalid."""
    pass

class PluginSecurityError(PluginError):
    """Raised when plugin violates security constraints."""
    pass

class WidgetCreationError(PluginError):
    """Raised when widget creation fails."""
    pass

class ServiceNotFoundError(PluginError):
    """Raised when a required service is not found."""
    pass
```

### Validation Checkpoint
- [ ] Service layer complete
- [ ] Context implementation working
- [ ] Lifecycle management functional
- [ ] All exceptions defined

## Day 5: Testing and Documentation

### Morning (3 hours)

#### Task 5.1: Create SDK Tests

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/tests/test_plugin.py`:
```python
"""Tests for plugin interface."""

import pytest
from viloapp_sdk import IPlugin, PluginMetadata, PluginCapability
from viloapp_sdk.context import PluginContext
from viloapp_sdk.service import ServiceProxy
from viloapp_sdk.events import EventBus
from pathlib import Path

class TestPlugin(IPlugin):
    """Test plugin implementation."""

    def __init__(self):
        self.activated = False
        self.deactivated = False

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            capabilities=[PluginCapability.WIDGETS]
        )

    def activate(self, context):
        self.activated = True
        self.context = context

    def deactivate(self):
        self.deactivated = True

def test_plugin_metadata():
    """Test plugin metadata."""
    plugin = TestPlugin()
    metadata = plugin.get_metadata()

    assert metadata.id == "test-plugin"
    assert metadata.name == "Test Plugin"
    assert metadata.version == "1.0.0"
    assert metadata.description == "A test plugin"
    assert metadata.author == "Test Author"
    assert PluginCapability.WIDGETS in metadata.capabilities

def test_plugin_lifecycle():
    """Test plugin lifecycle."""
    plugin = TestPlugin()

    assert not plugin.activated
    assert not plugin.deactivated

    # Create mock context
    context = PluginContext(
        plugin_id="test-plugin",
        plugin_path=Path("/tmp/test-plugin"),
        data_path=Path("/tmp/test-plugin-data"),
        service_proxy=ServiceProxy({}),
        event_bus=EventBus(),
        configuration={}
    )

    # Activate plugin
    plugin.activate(context)
    assert plugin.activated
    assert plugin.context == context

    # Deactivate plugin
    plugin.deactivate()
    assert plugin.deactivated

def test_metadata_validation():
    """Test metadata validation."""
    # Valid metadata
    metadata = PluginMetadata(
        id="valid-plugin",
        name="Valid Plugin",
        version="1.0.0",
        description="A valid plugin",
        author="Author"
    )

    errors = metadata.validate()
    assert len(errors) == 0

    # Invalid metadata (empty ID)
    metadata = PluginMetadata(
        id="",
        name="Invalid Plugin",
        version="1.0.0",
        description="An invalid plugin",
        author="Author"
    )

    errors = metadata.validate()
    assert len(errors) > 0
    assert "Plugin ID is required" in errors

    # Invalid metadata (bad ID format)
    metadata = PluginMetadata(
        id="invalid_plugin",  # Underscore not allowed
        name="Invalid Plugin",
        version="1.0.0",
        description="An invalid plugin",
        author="Author"
    )

    errors = metadata.validate()
    assert any("alphanumeric with hyphens" in error for error in errors)
```

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/tests/test_events.py`:
```python
"""Tests for event system."""

import pytest
from viloapp_sdk.events import EventBus, PluginEvent, EventType, EventPriority
import time

def test_event_bus_subscribe_emit():
    """Test basic event subscription and emission."""
    bus = EventBus()
    received_events = []

    def handler(event):
        received_events.append(event)

    # Subscribe to event
    subscription = bus.subscribe(EventType.PLUGIN_LOADED, handler)

    # Emit event
    event = PluginEvent(
        type=EventType.PLUGIN_LOADED,
        source="test",
        data={"plugin_id": "test-plugin"}
    )
    bus.emit(event)

    # Check event was received
    assert len(received_events) == 1
    assert received_events[0].data["plugin_id"] == "test-plugin"

def test_event_filtering():
    """Test event filtering."""
    bus = EventBus()
    received_events = []

    def handler(event):
        received_events.append(event)

    # Subscribe with filter
    def filter_func(event):
        return event.data.get("important", False)

    bus.subscribe(
        EventType.CUSTOM,
        handler,
        filter_func=filter_func
    )

    # Emit non-matching event
    event1 = PluginEvent(
        type=EventType.CUSTOM,
        source="test",
        data={"important": False}
    )
    bus.emit(event1)

    # Emit matching event
    event2 = PluginEvent(
        type=EventType.CUSTOM,
        source="test",
        data={"important": True}
    )
    bus.emit(event2)

    # Only matching event should be received
    assert len(received_events) == 1
    assert received_events[0].data["important"] == True

def test_event_priority():
    """Test event priority handling."""
    bus = EventBus()
    call_order = []

    def handler_low(event):
        call_order.append("low")

    def handler_normal(event):
        call_order.append("normal")

    def handler_high(event):
        call_order.append("high")

    # Subscribe with different priorities
    bus.subscribe(EventType.CUSTOM, handler_low, priority=EventPriority.LOW)
    bus.subscribe(EventType.CUSTOM, handler_normal, priority=EventPriority.NORMAL)
    bus.subscribe(EventType.CUSTOM, handler_high, priority=EventPriority.HIGH)

    # Emit event
    event = PluginEvent(type=EventType.CUSTOM, source="test")
    bus.emit(event)

    # Check call order (high priority first)
    assert call_order == ["high", "normal", "low"]

def test_event_unsubscribe():
    """Test event unsubscription."""
    bus = EventBus()
    received_count = 0

    def handler(event):
        nonlocal received_count
        received_count += 1

    # Subscribe to event
    subscription = bus.subscribe(EventType.CUSTOM, handler)

    # Emit event
    event = PluginEvent(type=EventType.CUSTOM, source="test")
    bus.emit(event)
    assert received_count == 1

    # Unsubscribe
    bus.unsubscribe(subscription)

    # Emit event again
    bus.emit(event)
    assert received_count == 1  # Should not increase

def test_event_history():
    """Test event history."""
    bus = EventBus()

    # Emit some events
    for i in range(5):
        event = PluginEvent(
            type=EventType.CUSTOM,
            source="test",
            data={"index": i}
        )
        bus.emit(event)
        time.sleep(0.01)  # Ensure different timestamps

    # Get history
    history = bus.get_history(limit=3)
    assert len(history) == 3

    # Check filtering
    event = PluginEvent(
        type=EventType.PLUGIN_LOADED,
        source="other"
    )
    bus.emit(event)

    history = bus.get_history(event_type=EventType.CUSTOM)
    assert all(e.type == EventType.CUSTOM for e in history)

    history = bus.get_history(source="other")
    assert all(e.source == "other" for e in history)
```

### Afternoon (2 hours)

#### Task 5.2: Create SDK Documentation

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/docs/getting_started.md`:
```markdown
# Getting Started with ViloxTerm Plugin SDK

## Installation

```bash
pip install viloapp-sdk
```

## Creating Your First Plugin

### 1. Basic Plugin Structure

Create a new directory for your plugin:

```
my-plugin/
├── pyproject.toml
├── src/
│   └── my_plugin/
│       ├── __init__.py
│       └── plugin.py
└── tests/
```

### 2. Define Your Plugin

Create `src/my_plugin/plugin.py`:

```python
from viloapp_sdk import IPlugin, PluginMetadata

class MyPlugin(IPlugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="my-plugin",
            name="My Plugin",
            version="1.0.0",
            description="My first ViloxTerm plugin",
            author="Your Name"
        )

    def activate(self, context):
        print(f"Plugin {self.get_metadata().name} activated!")
        self.context = context

    def deactivate(self):
        print(f"Plugin {self.get_metadata().name} deactivated!")
```

### 3. Configure Package

Create `pyproject.toml`:

```toml
[project]
name = "my-plugin"
version = "1.0.0"
dependencies = ["viloapp-sdk>=1.0.0"]

[project.entry-points."viloapp.plugins"]
my-plugin = "my_plugin.plugin:MyPlugin"
```

### 4. Adding a Widget

```python
from viloapp_sdk import IWidget, WidgetMetadata, WidgetPosition
from PySide6.QtWidgets import QWidget, QLabel

class MyWidget(IWidget):
    def get_metadata(self) -> WidgetMetadata:
        return WidgetMetadata(
            id="my-widget",
            title="My Widget",
            position=WidgetPosition.SIDEBAR
        )

    def create_widget(self, parent=None) -> QWidget:
        widget = QLabel("Hello from my plugin!", parent)
        return widget

    def get_state(self):
        return {}

    def restore_state(self, state):
        pass
```

### 5. Accessing Services

```python
def activate(self, context):
    # Get notification service
    notify_service = context.get_service("notification")
    if notify_service:
        notify_service.info("Plugin activated!")

    # Execute a command
    command_service = context.get_service("command")
    if command_service:
        command_service.execute_command("workbench.action.openSettings")
```

### 6. Using Events

```python
from viloapp_sdk.events import EventType

def activate(self, context):
    # Subscribe to theme changes
    def on_theme_changed(event):
        print(f"Theme changed: {event.data}")

    context.subscribe_event(EventType.THEME_CHANGED, on_theme_changed)

    # Emit custom event
    context.emit_event(EventType.CUSTOM, {
        "message": "Plugin initialized"
    })
```

## Testing Your Plugin

```python
import pytest
from my_plugin.plugin import MyPlugin

def test_plugin_metadata():
    plugin = MyPlugin()
    metadata = plugin.get_metadata()
    assert metadata.id == "my-plugin"
    assert metadata.version == "1.0.0"
```

## Installing Your Plugin

```bash
# Install in development mode
pip install -e .

# Or build and install
python -m build
pip install dist/*.whl
```

## Next Steps

- Read the [API Reference](api_reference.md)
- Check out [Example Plugins](examples/)
- Learn about [Advanced Features](advanced.md)
```

#### Task 5.3: Create Example Plugin

Create `/home/kuja/GitHub/viloapp/packages/viloapp-sdk/examples/hello-world/plugin.py`:
```python
"""Example Hello World plugin."""

from viloapp_sdk import (
    IPlugin, PluginMetadata, IWidget, WidgetMetadata,
    WidgetPosition, EventType
)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit

class HelloWorldWidget(IWidget):
    """Hello World widget."""

    def get_metadata(self) -> WidgetMetadata:
        return WidgetMetadata(
            id="hello-world",
            title="Hello World",
            position=WidgetPosition.MAIN,
            icon="smile"
        )

    def create_widget(self, parent=None) -> QWidget:
        """Create the widget."""
        widget = QWidget(parent)
        layout = QVBoxLayout()

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText("Hello from ViloxTerm Plugin!")

        button = QPushButton("Click Me!")
        button.clicked.connect(self._on_button_click)

        layout.addWidget(self.text_edit)
        layout.addWidget(button)
        widget.setLayout(layout)

        return widget

    def _on_button_click(self):
        """Handle button click."""
        self.text_edit.append("Button clicked!")

    def get_state(self):
        """Get widget state."""
        return {"text": self.text_edit.toPlainText()}

    def restore_state(self, state):
        """Restore widget state."""
        if "text" in state:
            self.text_edit.setPlainText(state["text"])

class HelloWorldPlugin(IPlugin):
    """Hello World plugin."""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="hello-world",
            name="Hello World Plugin",
            version="1.0.0",
            description="A simple Hello World plugin for ViloxTerm",
            author="ViloxTerm Team",
            homepage="https://github.com/viloxterm/hello-world",
            contributes={
                "widgets": [
                    {
                        "id": "hello-world",
                        "factory": "HelloWorldWidget"
                    }
                ],
                "commands": [
                    {
                        "id": "hello.sayHello",
                        "title": "Say Hello",
                        "category": "Hello World"
                    }
                ]
            }
        )

    def activate(self, context):
        """Activate the plugin."""
        self.context = context

        # Register command handler
        command_service = context.get_service("command")
        if command_service:
            command_service.register_command(
                "hello.sayHello",
                self._say_hello
            )

        # Subscribe to events
        context.subscribe_event(
            EventType.THEME_CHANGED,
            self._on_theme_changed
        )

        # Show notification
        notify_service = context.get_service("notification")
        if notify_service:
            notify_service.info("Hello World plugin activated!")

    def deactivate(self):
        """Deactivate the plugin."""
        # Unregister command
        command_service = self.context.get_service("command")
        if command_service:
            command_service.unregister_command("hello.sayHello")

    def _say_hello(self):
        """Say hello command handler."""
        notify_service = self.context.get_service("notification")
        if notify_service:
            notify_service.info("Hello from the plugin!")

    def _on_theme_changed(self, event):
        """Handle theme change."""
        print(f"Theme changed: {event.data}")
```

### Final Validation Checkpoint
- [ ] All tests pass
- [ ] SDK can be imported without errors
- [ ] Example plugin works
- [ ] Documentation is complete
- [ ] Package can be built (`python -m build`)

## Week 1 Summary

### Completed Deliverables
1. ✅ Monorepo structure with proper configuration
2. ✅ Development scripts and tooling
3. ✅ Complete Plugin SDK package
4. ✅ Core interfaces (IPlugin, IWidget, IService)
5. ✅ Event system implementation
6. ✅ Service proxy layer
7. ✅ Plugin context and lifecycle management
8. ✅ Comprehensive test suite
9. ✅ Documentation and examples

### Key Files Created
- `/pyproject.toml` - Workspace configuration
- `/scripts/dev-setup.py` - Development setup
- `/scripts/build.py` - Build script
- `/Makefile` - Common commands
- `/packages/viloapp-sdk/` - Complete SDK package
- SDK interfaces and implementations
- Test suite for SDK
- Documentation and examples

### Ready for Week 2
The Plugin SDK is now complete and ready to be used for:
- Creating the plugin host infrastructure
- Implementing plugin discovery and loading
- Building the terminal and editor plugins

### Next Steps
- Week 2: Implement plugin host infrastructure in the main application
- Week 3: Begin terminal plugin extraction
- Week 4: Complete terminal plugin integration