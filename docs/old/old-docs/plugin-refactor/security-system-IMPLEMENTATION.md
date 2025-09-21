# Plugin Security System Implementation Guide

## Overview

The ViloxTerm plugin security system provides comprehensive protection against malicious plugins while maintaining ease of development. The system includes permission management, resource monitoring, and sandboxing capabilities.

## Permission System

### Permission Categories

Plugins can request permissions in four main categories:

#### 1. Filesystem Permissions
```json
{
  "category": "filesystem",
  "scope": "read|write|execute",
  "resource": "/path/pattern/*"
}
```

**Scopes:**
- `read`: Read files and directories
- `write`: Create, modify, delete files and directories
- `execute`: Execute files as programs

**Resource Patterns:**
- `/home/*` - User home directory
- `/tmp/*` - Temporary files
- `/usr/share/applications/*` - Application files
- `workspace://` - Current workspace files

**Examples:**
```json
// Read access to user files
{
  "category": "filesystem",
  "scope": "read",
  "resource": "/home/*"
}

// Write access to project files
{
  "category": "filesystem",
  "scope": "write",
  "resource": "workspace://*"
}
```

#### 2. Network Permissions
```json
{
  "category": "network",
  "scope": "read|write",
  "resource": "domain_or_ip:port"
}
```

**Scopes:**
- `read`: Make HTTP requests, download data
- `write`: Upload data, send requests with payloads

**Resource Patterns:**
- `localhost:*` - Local services
- `*.github.com:443` - GitHub API
- `registry.npmjs.org:443` - NPM registry

#### 3. System Permissions
```json
{
  "category": "system",
  "scope": "read|write|execute",
  "resource": "system_component"
}
```

**System Components:**
- `shell_commands` - Execute shell commands
- `environment_variables` - Access/modify environment
- `clipboard` - Read/write clipboard content
- `notifications` - Show system notifications

#### 4. UI Permissions
```json
{
  "category": "ui",
  "scope": "read|write",
  "resource": "ui_component"
}
```

**UI Components:**
- `workspace` - Workspace management
- `dialogs` - Show dialogs and prompts
- `menus` - Add context menus
- `status_bar` - Status bar access

### Permission Declaration

Declare permissions in your plugin manifest (`plugin.json`):

```json
{
  "id": "my-plugin",
  "permissions": [
    {
      "category": "filesystem",
      "scope": "read",
      "resource": "/home/*",
      "description": "Read user files for processing"
    },
    {
      "category": "network",
      "scope": "read",
      "resource": "api.github.com:443",
      "description": "Fetch repository information"
    }
  ]
}
```

### Permission Checking

The plugin host automatically checks permissions when accessing protected resources:

```python
from viloapp_sdk import IPlugin

class MyPlugin(IPlugin):
    def do_file_operation(self):
        # Permission automatically checked by service proxy
        content = self.context.get_service("filesystem").read_file("/home/user/file.txt")
        return content
```

### Runtime Permission Requests

For dynamic permissions, use the permission service:

```python
def request_network_access(self):
    permission_service = self.context.get_service("permissions")

    # Request permission at runtime
    granted = permission_service.request_permission(
        category="network",
        scope="read",
        resource="api.example.com:443",
        reason="Fetch latest data from API"
    )

    if granted:
        # Permission granted, proceed
        pass
    else:
        # Permission denied, handle gracefully
        pass
```

## Resource Monitoring

### Resource Limits

Set resource limits in your plugin manifest:

```json
{
  "id": "my-plugin",
  "resource_limits": {
    "memory": 100,      // MB
    "cpu": 50,          // Percentage
    "disk": 500,        // MB
    "network": 10       // MB/s
  }
}
```

### Monitoring API

Monitor resource usage programmatically:

```python
from core.plugin_system.security.resources import ResourceMonitor, ResourceType

class MyPlugin(IPlugin):
    def __init__(self):
        self.monitor = ResourceMonitor(self.get_metadata().id)

    def activate(self, context):
        self.monitor.start_monitoring()

        # Check current usage
        memory_usage = self.monitor.get_resource_usage(ResourceType.MEMORY)
        print(f"Memory usage: {memory_usage:.2f} MB")

    def deactivate(self):
        self.monitor.stop_monitoring()
```

### Resource Violations

When limits are exceeded, the system can:

1. **Log violations** - Record in system logs
2. **Throttle operations** - Reduce allowed operations
3. **Suspend plugin** - Temporarily disable plugin
4. **Terminate plugin** - Force shutdown for severe violations

Configure violation handling:

```python
def violation_handler(violation):
    print(f"Resource violation: {violation}")
    # Custom handling logic

limiter = ResourceLimiter(
    plugin_id="my-plugin",
    limits={ResourceType.MEMORY: 100},
    violation_callback=violation_handler
)
```

## Sandboxing

### Process Isolation

Plugins run in isolated processes to prevent interference:

```python
from core.plugin_system.security.sandbox import PluginSandbox

# Create sandbox for plugin
sandbox = PluginSandbox(
    plugin_id="my-plugin",
    isolation_level="strict"  # strict|moderate|minimal
)

# Run plugin in sandbox
sandbox.execute_plugin(plugin_instance)
```

### Sandbox Levels

#### Strict Isolation
- Separate process
- Limited filesystem access
- Restricted network access
- No direct system calls

#### Moderate Isolation
- Shared process space
- Filtered API access
- Resource monitoring
- Permission enforcement

#### Minimal Isolation
- Same process
- Permission checking only
- Basic resource monitoring

### Crash Recovery

Sandboxed plugins that crash are automatically recovered:

```python
sandbox.set_crash_policy(
    auto_restart=True,
    max_restarts=3,
    restart_delay=5  # seconds
)
```

## Security Best Practices

### For Plugin Developers

1. **Request minimal permissions**
   ```json
   // Good: Specific path
   {"category": "filesystem", "scope": "read", "resource": "workspace://config/*"}

   // Bad: Overly broad
   {"category": "filesystem", "scope": "write", "resource": "/*"}
   ```

2. **Handle permission denials gracefully**
   ```python
   try:
       data = service.read_file(path)
   except PermissionError:
       # Provide fallback or inform user
       self.show_error("Cannot access file: permission denied")
   ```

3. **Monitor resource usage**
   ```python
   if self.monitor.get_resource_usage(ResourceType.MEMORY) > 80:  # 80MB
       self.cleanup_caches()
   ```

4. **Use secure coding practices**
   ```python
   # Validate inputs
   if not os.path.abspath(file_path).startswith("/home/"):
       raise ValueError("Invalid file path")

   # Escape shell commands
   safe_command = shlex.quote(user_input)
   ```

### For Plugin Host

1. **Review plugin permissions before installation**
2. **Monitor resource usage regularly**
3. **Keep security system updated**
4. **Use strict sandboxing for untrusted plugins**

## Configuration

### System Configuration

Configure security settings in `viloapp.conf`:

```ini
[security]
# Enable/disable security features
permissions_enabled = true
resource_monitoring = true
sandboxing = true

# Default resource limits
default_memory_limit = 100MB
default_cpu_limit = 50%

# Permission prompt behavior
prompt_for_permissions = true
remember_permission_choices = true

# Logging
log_permission_checks = true
log_resource_violations = true
```

### Per-Plugin Configuration

Override settings for specific plugins:

```json
{
  "plugin_security": {
    "my-trusted-plugin": {
      "sandboxing": "minimal",
      "auto_grant_permissions": true
    },
    "untrusted-plugin": {
      "sandboxing": "strict",
      "resource_limits": {
        "memory": 50,
        "cpu": 25
      }
    }
  }
}
```

## Troubleshooting

### Common Issues

#### Permission Denied Errors
```
ERROR: Permission denied for filesystem:read:/home/user/file.txt
```

**Solutions:**
1. Add permission to plugin manifest
2. Request permission at runtime
3. Use alternative API that doesn't require permission

#### Resource Limit Violations
```
WARN: Plugin 'my-plugin' exceeded memory limit (150MB > 100MB)
```

**Solutions:**
1. Optimize memory usage
2. Increase limit in configuration
3. Implement memory cleanup

#### Sandbox Crashes
```
ERROR: Plugin sandbox crashed: Segmentation fault
```

**Solutions:**
1. Check plugin code for memory errors
2. Review native dependencies
3. Enable debug logging for more details

### Debug Logging

Enable detailed security logging:

```ini
[logging]
level = DEBUG
loggers = security,permissions,resources,sandbox
```

View logs:
```bash
tail -f ~/.local/share/viloapp/logs/security.log
```

## API Reference

### Permission Classes

```python
from core.plugin_system.security.permissions import (
    Permission,
    PermissionManager,
    PermissionCategory,
    PermissionScope
)

# Create permission
perm = Permission(
    PermissionCategory.FILESYSTEM,
    PermissionScope.READ,
    "/home/*"
)

# Check permission
manager = PermissionManager()
if manager.has_permission("plugin-id", perm):
    # Permission granted
    pass
```

### Resource Monitoring Classes

```python
from core.plugin_system.security.resources import (
    ResourceMonitor,
    ResourceLimiter,
    ResourceType,
    ResourceViolation
)

# Monitor resources
monitor = ResourceMonitor("plugin-id")
monitor.start_monitoring()

usage = monitor.get_resource_usage(ResourceType.MEMORY)
history = monitor.get_usage_history(ResourceType.CPU)
```

### Sandbox Classes

```python
from core.plugin_system.security.sandbox import (
    PluginSandbox,
    SandboxConfig,
    IsolationLevel
)

# Create sandbox
config = SandboxConfig(
    isolation_level=IsolationLevel.STRICT,
    resource_limits={"memory": 100},
    allowed_paths=["/home/user/workspace"]
)

sandbox = PluginSandbox("plugin-id", config)
```

## Conclusion

The ViloxTerm plugin security system provides robust protection while maintaining developer productivity. By following the guidelines in this document, you can create secure plugins that users can trust.

For additional security resources:
- [Plugin Development Security Guide](./plugin-security-guide-IMPLEMENTATION.md)
- [Security Audit Checklist](./security-audit-CHECKLIST.md)
- [Incident Response Guide](./security-incident-response-GUIDE.md)