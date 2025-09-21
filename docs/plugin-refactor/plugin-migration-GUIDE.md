# Plugin Migration Guide: Legacy to New Interface

## Overview

This guide helps developers migrate existing ViloxTerm plugins from the legacy interface to the new plugin architecture. The new system provides better type safety, cleaner APIs, and enhanced functionality.

## Interface Changes Summary

### IWidget Interface Migration

The `IWidget` interface has been completely redesigned for better lifecycle management and functionality.

#### Legacy Interface (OLD)
```python
class IWidget(ABC):
    @abstractmethod
    def get_metadata(self) -> WidgetMetadata: pass

    @abstractmethod
    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget: pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]: pass

    @abstractmethod
    def restore_state(self, state: Dict[str, Any]) -> None: pass
```

#### New Interface (NEW)
```python
class IWidget(ABC):
    @abstractmethod
    def get_widget_id(self) -> str: pass

    @abstractmethod
    def get_title(self) -> str: pass

    @abstractmethod
    def get_icon(self) -> Optional[str]: pass

    @abstractmethod
    def create_instance(self, instance_id: str) -> QWidget: pass

    @abstractmethod
    def destroy_instance(self, instance_id: str) -> None: pass

    @abstractmethod
    def handle_command(self, command: str, args: Dict[str, Any]) -> Any: pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]: pass

    @abstractmethod
    def restore_state(self, state: Dict[str, Any]) -> None: pass
```

### IMetadata Interface Addition

A new `IMetadata` interface has been added for standardized metadata handling:

```python
class IMetadata(ABC):
    @abstractmethod
    def get_id(self) -> str: pass

    @abstractmethod
    def get_name(self) -> str: pass

    @abstractmethod
    def get_version(self) -> str: pass

    @abstractmethod
    def get_description(self) -> str: pass

    @abstractmethod
    def get_author(self) -> Dict[str, str]: pass

    @abstractmethod
    def get_license(self) -> str: pass

    @abstractmethod
    def get_dependencies(self) -> Dict[str, str]: pass

    @abstractmethod
    def get_keywords(self) -> List[str]: pass
```

## Migration Steps

### Step 1: Update Widget Implementation

#### Before (Legacy)
```python
from viloapp_sdk import IWidget, WidgetMetadata, WidgetPosition

class MyWidgetFactory(IWidget):
    def get_metadata(self) -> WidgetMetadata:
        return WidgetMetadata(
            id="my-widget",
            title="My Widget",
            position=WidgetPosition.MAIN,
            icon="widget-icon"
        )

    def create_widget(self, parent=None) -> QWidget:
        widget = MyWidget(parent)
        return widget

    def get_state(self) -> Dict[str, Any]:
        return {"config": self.config}

    def restore_state(self, state: Dict[str, Any]) -> None:
        self.config = state.get("config", {})
```

#### After (New Interface)
```python
from viloapp_sdk import IWidget
from typing import Dict, Any, Optional
from PySide6.QtWidgets import QWidget

class MyWidgetFactory(IWidget):
    def __init__(self):
        self._instances = {}  # Track widget instances

    def get_widget_id(self) -> str:
        return "my-widget"

    def get_title(self) -> str:
        return "My Widget"

    def get_icon(self) -> Optional[str]:
        return "widget-icon"

    def create_instance(self, instance_id: str) -> QWidget:
        widget = MyWidget()
        self._instances[instance_id] = widget
        return widget

    def destroy_instance(self, instance_id: str) -> None:
        if instance_id in self._instances:
            widget = self._instances[instance_id]
            widget.close()
            widget.deleteLater()
            del self._instances[instance_id]

    def handle_command(self, command: str, args: Dict[str, Any]) -> Any:
        if command == "focus_widget":
            instance_id = args.get("instance_id")
            if instance_id in self._instances:
                self._instances[instance_id].setFocus()
                return True
        return None

    def get_state(self) -> Dict[str, Any]:
        return {
            "instance_count": len(self._instances),
            "config": getattr(self, 'config', {})
        }

    def restore_state(self, state: Dict[str, Any]) -> None:
        self.config = state.get("config", {})
        # Note: Instances are not restored automatically
        # They should be recreated by the host as needed
```

### Step 2: Update Plugin Metadata

#### Before (Legacy)
```python
from viloapp_sdk import IPlugin, PluginMetadata

class MyPlugin(IPlugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="my-plugin",
            name="My Plugin",
            version="1.0.0",
            description="Example plugin",
            author="Developer",
            # ... other fields
        )
```

#### After (New Interface)
```python
from viloapp_sdk import IPlugin, IMetadata, PluginMetadata
from typing import Dict, List

class MyPlugin(IPlugin, IMetadata):
    def get_metadata(self) -> PluginMetadata:
        # Keep for backward compatibility
        return PluginMetadata(
            id=self.get_id(),
            name=self.get_name(),
            version=self.get_version(),
            # ... other fields
        )

    # New IMetadata methods
    def get_id(self) -> str:
        return "my-plugin"

    def get_name(self) -> str:
        return "My Plugin"

    def get_version(self) -> str:
        return "1.0.0"

    def get_description(self) -> str:
        return "Example plugin"

    def get_author(self) -> Dict[str, str]:
        return {
            "name": "Developer",
            "email": "dev@example.com",
            "url": "https://example.com"
        }

    def get_license(self) -> str:
        return "MIT"

    def get_dependencies(self) -> Dict[str, str]:
        return {
            "viloapp-sdk": ">=1.0.0",
            "python": ">=3.8"
        }

    def get_keywords(self) -> List[str]:
        return ["example", "demo", "widget"]
```

### Step 3: Update Plugin Calls

#### Before (Legacy)
```python
# In plugin implementation
def create_new_widget(self):
    workspace_service = self.context.get_service("workspace")
    widget = self.widget_factory.create_widget()
    workspace_service.add_widget(widget, "my-widget", "main")
```

#### After (New Interface)
```python
# In plugin implementation
def create_new_widget(self):
    workspace_service = self.context.get_service("workspace")
    instance_id = f"my-widget-{uuid.uuid4()}"
    widget = self.widget_factory.create_instance(instance_id)
    workspace_service.add_widget(widget, instance_id, "main")
```

### Step 4: Update Plugin Manifest

Update your `plugin.json` to include permissions and new structure:

#### Before (Legacy)
```json
{
  "id": "my-plugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "main": "plugin.py",
  "dependencies": {
    "viloapp-sdk": ">=0.9.0"
  }
}
```

#### After (New Structure)
```json
{
  "id": "my-plugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "description": "Example plugin",
  "author": "Developer",
  "license": "MIT",
  "main": "src/my_plugin/plugin.py",
  "entry_point": "my_plugin.plugin:MyPlugin",
  "dependencies": {
    "viloapp-sdk": ">=1.0.0"
  },
  "permissions": [
    {
      "category": "ui",
      "scope": "read",
      "resource": "*",
      "description": "Access UI components"
    },
    {
      "category": "ui",
      "scope": "write",
      "resource": "*",
      "description": "Modify UI elements"
    }
  ],
  "activation_events": [
    "onCommand:my-plugin.activate",
    "onStartupFinished"
  ],
  "contributes": {
    "widgets": [
      {
        "id": "my-widget",
        "factory": "my_plugin.widget:MyWidgetFactory"
      }
    ],
    "commands": [
      {
        "id": "my-plugin.activate",
        "title": "Activate My Plugin",
        "category": "My Plugin"
      }
    ]
  }
}
```

## Automated Migration Tool

Use the CLI migration tool to automate most changes:

```bash
# Install migration tool
pip install viloapp-migration-tool

# Migrate plugin
viloapp-migrate /path/to/old-plugin /path/to/migrated-plugin

# Review changes
viloapp-migrate --dry-run /path/to/old-plugin

# Fix specific issues
viloapp-migrate --fix-interfaces /path/to/plugin
viloapp-migrate --update-manifest /path/to/plugin
```

### Migration Tool Features

- **Interface Updates**: Automatically converts old interface methods
- **Manifest Updates**: Updates plugin.json structure and permissions
- **Import Fixes**: Updates import statements
- **Code Style**: Applies consistent formatting
- **Validation**: Checks for common migration issues

## Backward Compatibility

### Legacy Adapter

The system includes a `LegacyWidgetAdapter` for gradual migration:

```python
from viloapp_sdk.widget import LegacyWidgetAdapter

# Wrap legacy widget automatically
legacy_widget = OldWidgetFactory()
adapted_widget = LegacyWidgetAdapter(legacy_widget)

# Use adapted widget with new interface
widget_id = adapted_widget.get_widget_id()
instance = adapted_widget.create_instance("instance-1")
```

### Compatibility Mode

Enable compatibility mode in configuration:

```yaml
# viloapp.conf
[compatibility]
legacy_interface_support = true
warn_deprecated_usage = true
auto_adapt_widgets = true
```

## Common Migration Issues

### Issue 1: Widget Instance Management

**Problem**: Legacy widgets didn't track instances
```python
# Old way - no instance tracking
def create_widget(self):
    return MyWidget()
```

**Solution**: Implement instance tracking
```python
# New way - track instances
def __init__(self):
    self._instances = {}

def create_instance(self, instance_id: str) -> QWidget:
    widget = MyWidget()
    self._instances[instance_id] = widget
    return widget

def destroy_instance(self, instance_id: str) -> None:
    if instance_id in self._instances:
        self._instances[instance_id].deleteLater()
        del self._instances[instance_id]
```

### Issue 2: Metadata Access

**Problem**: Metadata was returned as object
```python
# Old way
metadata = widget_factory.get_metadata()
title = metadata.title
```

**Solution**: Use direct methods
```python
# New way
title = widget_factory.get_title()
icon = widget_factory.get_icon()
widget_id = widget_factory.get_widget_id()
```

### Issue 3: Command Handling

**Problem**: No command handling in widgets
```python
# Old interface had no command handling
```

**Solution**: Implement command handling
```python
def handle_command(self, command: str, args: Dict[str, Any]) -> Any:
    if command == "focus":
        instance_id = args.get("instance_id")
        if instance_id in self._instances:
            self._instances[instance_id].setFocus()
            return True
    elif command == "get_content":
        instance_id = args.get("instance_id")
        if instance_id in self._instances:
            return self._instances[instance_id].toPlainText()

    return None
```

### Issue 4: Permission Requirements

**Problem**: Old plugins had unrestricted access
```python
# Old way - direct access
file_content = open("/some/file").read()
```

**Solution**: Request permissions and use services
```json
// In plugin.json
"permissions": [
  {
    "category": "filesystem",
    "scope": "read",
    "resource": "/home/*"
  }
]
```

```python
# New way - use service
file_service = self.context.get_service("filesystem")
file_content = file_service.read_file("/some/file")
```

## Testing Migration

### Automated Tests

Create tests to verify migration:

```python
import pytest
from viloapp_sdk.testing import mock_plugin_context

def test_widget_interface_compliance():
    """Test that widget implements new interface correctly."""
    factory = MyWidgetFactory()

    # Test new interface methods
    assert factory.get_widget_id() == "my-widget"
    assert factory.get_title() == "My Widget"
    assert factory.get_icon() is not None

    # Test instance management
    instance_id = "test-instance"
    widget = factory.create_instance(instance_id)
    assert widget is not None

    # Test command handling
    result = factory.handle_command("focus", {"instance_id": instance_id})
    assert result is not None

    # Test cleanup
    factory.destroy_instance(instance_id)

def test_plugin_metadata_compliance():
    """Test that plugin implements IMetadata correctly."""
    plugin = MyPlugin()

    # Test IMetadata methods
    assert plugin.get_id() == "my-plugin"
    assert plugin.get_name() == "My Plugin"
    assert plugin.get_version() == "1.0.0"
    assert isinstance(plugin.get_author(), dict)
    assert isinstance(plugin.get_dependencies(), dict)
    assert isinstance(plugin.get_keywords(), list)

@pytest.fixture
def migrated_plugin(mock_plugin_context):
    """Fixture for testing migrated plugin."""
    plugin = MyPlugin()
    plugin.activate(mock_plugin_context)
    return plugin

def test_plugin_activation(migrated_plugin):
    """Test that migrated plugin activates correctly."""
    # Plugin should be activated without errors
    assert migrated_plugin.context is not None
```

### Manual Testing

1. **Install migrated plugin**
   ```bash
   viloapp install ./migrated-plugin
   ```

2. **Test basic functionality**
   - Create widget instances
   - Execute commands
   - Check state persistence

3. **Test permissions**
   - Verify required permissions are requested
   - Test permission denial handling

4. **Test resource usage**
   - Monitor memory and CPU usage
   - Check resource limits

## Migration Checklist

### Pre-Migration
- [ ] Backup original plugin code
- [ ] Review new interface documentation
- [ ] Identify custom functionality that needs adaptation
- [ ] Plan for testing and validation

### During Migration
- [ ] Update widget interface implementation
- [ ] Add IMetadata interface implementation
- [ ] Update instance management
- [ ] Add command handling
- [ ] Update plugin manifest
- [ ] Add permission declarations
- [ ] Update import statements
- [ ] Fix deprecated API usage

### Post-Migration
- [ ] Run automated migration validation
- [ ] Test all plugin functionality
- [ ] Verify permission system integration
- [ ] Check resource usage compliance
- [ ] Update documentation
- [ ] Test with different ViloxTerm versions
- [ ] Performance testing

### Validation
- [ ] All tests pass
- [ ] Plugin loads without errors
- [ ] Widget creation/destruction works
- [ ] Command handling responds correctly
- [ ] State persistence functions
- [ ] Permissions are properly enforced
- [ ] No memory leaks detected

## Support Resources

### Documentation
- [New Plugin Architecture Guide](./plugin-architecture-DESIGN.md)
- [Security System Documentation](./security-system-IMPLEMENTATION.md)
- [CLI Usage Guide](./cli-usage-GUIDE.md)

### Tools
- **Migration CLI**: `viloapp-migrate`
- **Validation Tool**: `viloapp validate`
- **Testing Framework**: `viloapp test`

### Community
- **Discord**: https://discord.gg/viloapp
- **GitHub Issues**: https://github.com/viloapp/viloapp/issues
- **Migration Forum**: https://forum.viloapp.com/migration

### Professional Support
- **Migration Services**: Available for complex plugins
- **Code Review**: Expert review of migrated code
- **Training**: Team training on new architecture

## Conclusion

Migrating to the new plugin interface provides significant benefits:

- **Better Type Safety**: Explicit interfaces and type hints
- **Enhanced Security**: Permission system and resource monitoring
- **Improved Lifecycle**: Proper instance management
- **Command Integration**: Built-in command handling
- **Future-Proof**: Compatible with upcoming features

While migration requires effort, the automated tools and backward compatibility features minimize disruption. The new architecture provides a solid foundation for future plugin development.

For additional help with migration, consult the resources above or contact the ViloxTerm development team.