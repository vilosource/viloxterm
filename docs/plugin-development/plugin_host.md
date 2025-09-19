# Plugin Host Documentation

## Overview

The ViloxTerm plugin host provides a robust infrastructure for discovering, loading, and managing plugins.

## Architecture

### Components

1. **Plugin Manager** - Central orchestrator
2. **Plugin Registry** - Tracks all plugins and their states
3. **Plugin Discovery** - Finds plugins from various sources
4. **Plugin Loader** - Loads and activates plugins
5. **Dependency Resolver** - Resolves plugin dependencies
6. **Service Proxy** - Provides access to host services

## Plugin Lifecycle

```
DISCOVERED -> LOADED -> ACTIVATED -> DEACTIVATED -> UNLOADED
                |                        |
                v                        v
              FAILED                  FAILED
```

## Services Available to Plugins

- **command** - Execute and register commands
- **configuration** - Access and modify configuration
- **workspace** - Interact with workspace
- **theme** - Access theme information
- **notification** - Show notifications

## Plugin Discovery Sources

1. Python entry points (`viloapp.plugins`)
2. User plugin directory (`~/.config/ViloxTerm/plugins/`)
3. System plugin directory
4. Built-in plugins

## Creating a Plugin

See the [Plugin SDK documentation](../packages/viloapp-sdk/docs/getting_started.md)

## Managing Plugins

### Via Commands

- `plugins.list` - List all plugins
- `plugins.enable` - Enable a plugin
- `plugins.disable` - Disable a plugin
- `plugins.reload` - Reload a plugin
- `plugins.info` - Get plugin information

### Via UI

Open Settings > Plugins to manage plugins through the UI.

## Security

Plugins run in the same process but with restricted service access. Only approved services are exposed through the service proxy.

## Debugging

Enable debug logging to see plugin operations:

```python
import logging
logging.getLogger('core.plugin_system').setLevel(logging.DEBUG)
```