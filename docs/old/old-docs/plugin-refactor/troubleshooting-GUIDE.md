# Plugin System Troubleshooting Guide

## Overview

This guide helps diagnose and resolve common issues with the ViloxTerm plugin system. It covers problems from plugin development to deployment and runtime issues.

## Quick Diagnosis

### Health Check Commands

```bash
# Check plugin system status
viloapp status

# Validate specific plugin
viloapp validate my-plugin

# Check permissions
viloapp permissions my-plugin

# Monitor resources
viloapp monitor my-plugin

# View system logs
viloapp logs --follow
```

### System Status Indicators

**Green**: All systems operational
**Yellow**: Minor issues detected
**Red**: Critical problems requiring attention

## Common Issues and Solutions

### Plugin Loading Issues

#### Issue: Plugin Not Found
```
Error: Plugin 'my-plugin' not found in any plugin directory
```

**Diagnosis:**
```bash
viloapp list --all
viloapp search my-plugin
ls -la ~/.local/share/viloapp/plugins/
```

**Solutions:**
1. **Install plugin**: `viloapp install my-plugin`
2. **Check plugin path**: Verify plugin is in correct directory
3. **Verify manifest**: Ensure `plugin.json` exists and is valid
4. **Check permissions**: Ensure read access to plugin directory

#### Issue: Invalid Plugin Manifest
```
Error: Invalid plugin manifest: missing required field 'id'
```

**Diagnosis:**
```bash
viloapp validate my-plugin --verbose
cat my-plugin/plugin.json | jq .
```

**Solutions:**
1. **Fix JSON syntax**: Use JSON validator to check format
2. **Add required fields**: id, name, version, main are required
3. **Check field types**: Ensure values match expected types
4. **Update schema**: Use latest manifest schema version

**Example Fix:**
```json
{
  "id": "my-plugin",          // Required
  "name": "My Plugin",        // Required
  "version": "1.0.0",         // Required
  "main": "plugin.py",        // Required
  "description": "Description", // Recommended
  "author": "Author Name"     // Recommended
}
```

#### Issue: Plugin Import Error
```
Error: Cannot import plugin module: No module named 'my_plugin'
```

**Diagnosis:**
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Test import manually
cd plugin-directory
python -c "from my_plugin import plugin"
```

**Solutions:**
1. **Fix import path**: Ensure module structure is correct
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Check entry point**: Verify entry_point in manifest
4. **Python environment**: Ensure correct Python environment

### Interface Compatibility Issues

#### Issue: Legacy Interface Methods
```
AttributeError: 'MyWidget' object has no attribute 'create_widget'
```

**Diagnosis:**
Check which interface version your plugin implements:
```bash
grep -r "create_widget\|create_instance" my-plugin/src/
```

**Solutions:**
1. **Use migration tool**: `viloapp-migrate my-plugin`
2. **Manual update**: Implement new interface methods
3. **Legacy adapter**: Enable backward compatibility

**Migration Example:**
```python
# Old interface
def create_widget(self, parent=None):
    return MyWidget(parent)

# New interface
def create_instance(self, instance_id: str) -> QWidget:
    widget = MyWidget()
    self._instances[instance_id] = widget
    return widget
```

#### Issue: Missing Interface Methods
```
TypeError: Can't instantiate abstract class with abstract methods handle_command
```

**Solution:** Implement all required interface methods:
```python
class MyWidgetFactory(IWidget):
    def handle_command(self, command: str, args: Dict[str, Any]) -> Any:
        # Implement command handling or return None
        if command == "focus":
            # Handle focus command
            return True
        return None
```

### Permission Issues

#### Issue: Permission Denied
```
PermissionError: Plugin 'my-plugin' does not have permission for filesystem:write:/home/user/file.txt
```

**Diagnosis:**
```bash
viloapp permissions my-plugin
viloapp logs --filter permission --plugin my-plugin
```

**Solutions:**
1. **Add permission to manifest**:
   ```json
   "permissions": [
     {
       "category": "filesystem",
       "scope": "write",
       "resource": "/home/*",
       "description": "Write user files"
     }
   ]
   ```

2. **Request permission at runtime**:
   ```python
   permission_service = self.context.get_service("permissions")
   granted = permission_service.request_permission(
       category="filesystem",
       scope="write",
       resource="/home/user/file.txt"
   )
   ```

3. **Use alternative API**: Find API that doesn't require permission

#### Issue: Overly Broad Permissions
```
Warning: Plugin requests overly broad permissions: filesystem:write:/*
```

**Solution:** Use more specific resource patterns:
```json
// Bad - too broad
{"category": "filesystem", "scope": "write", "resource": "/*"}

// Good - specific
{"category": "filesystem", "scope": "write", "resource": "/home/*/workspace/*"}
```

### Resource Limit Issues

#### Issue: Memory Limit Exceeded
```
ResourceViolation: Plugin 'my-plugin' exceeded memory limit (150MB > 100MB)
```

**Diagnosis:**
```bash
viloapp monitor my-plugin --resource memory
viloapp profile my-plugin --memory
```

**Solutions:**
1. **Optimize memory usage**:
   ```python
   # Clear caches periodically
   if self.monitor.get_resource_usage(ResourceType.MEMORY) > 80:
       self.clear_caches()

   # Use weak references
   import weakref
   self._cache = weakref.WeakValueDictionary()
   ```

2. **Increase limit** (if justified):
   ```json
   "resource_limits": {
     "memory": 200  // MB
   }
   ```

3. **Implement cleanup**:
   ```python
   def cleanup_resources(self):
       # Release large objects
       self.large_data = None
       # Force garbage collection
       import gc
       gc.collect()
   ```

#### Issue: CPU Limit Exceeded
```
ResourceViolation: Plugin 'my-plugin' exceeded CPU limit (75% > 50%)
```

**Solutions:**
1. **Optimize CPU-intensive operations**:
   ```python
   # Use threading for background tasks
   import threading
   threading.Thread(target=self.background_task, daemon=True).start()

   # Add delays in loops
   import time
   for item in large_list:
       process_item(item)
       time.sleep(0.001)  # Small delay
   ```

2. **Profile CPU usage**:
   ```bash
   viloapp profile my-plugin --cpu --duration 60
   ```

### Development Issues

#### Issue: Hot Reload Not Working
```
Warning: Hot reload failed - plugin changes not detected
```

**Diagnosis:**
```bash
viloapp dev my-plugin --debug
ls -la my-plugin/  # Check file timestamps
```

**Solutions:**
1. **Check file watching**:
   ```yaml
   # .viloapp/config.yaml
   dev:
     watch_paths: ["src", "resources"]
     reload_delay: 1.0
   ```

2. **Exclude problematic files**:
   ```yaml
   dev:
     ignore_patterns: ["*.pyc", "__pycache__", "*.log"]
   ```

3. **Manual reload**: `viloapp dev my-plugin --force-reload`

#### Issue: Test Failures
```
FAILED tests/test_plugin.py::test_widget_creation - AssertionError
```

**Diagnosis:**
```bash
viloapp test my-plugin --verbose --tb=long
viloapp test my-plugin --debug
```

**Solutions:**
1. **Use proper test fixtures**:
   ```python
   from viloapp_sdk.testing import mock_plugin_context

   def test_widget_creation(mock_plugin_context):
       plugin = MyPlugin()
       plugin.activate(mock_plugin_context)
       # Test implementation
   ```

2. **Mock external dependencies**:
   ```python
   @patch('my_plugin.external_service')
   def test_with_mock(mock_service):
       mock_service.return_value = "expected_value"
       # Test implementation
   ```

### Runtime Issues

#### Issue: Plugin Crashes
```
ERROR: Plugin 'my-plugin' crashed with segmentation fault
```

**Diagnosis:**
```bash
viloapp logs --plugin my-plugin --level error
gdb --args python -c "import my_plugin"
```

**Solutions:**
1. **Check native dependencies**:
   ```bash
   ldd ~/.local/share/viloapp/plugins/my-plugin/lib/native.so
   ```

2. **Enable core dumps**:
   ```bash
   ulimit -c unlimited
   viloapp dev my-plugin
   # Check for core files after crash
   ```

3. **Use address sanitizer**:
   ```bash
   export ASAN_OPTIONS=detect_leaks=1
   viloapp dev my-plugin
   ```

#### Issue: Memory Leaks
```
Warning: Plugin 'my-plugin' memory usage continuously increasing
```

**Diagnosis:**
```bash
viloapp profile my-plugin --memory --duration 300
python -m tracemalloc my_plugin
```

**Solutions:**
1. **Fix reference cycles**:
   ```python
   # Use weak references
   import weakref
   self.parent_ref = weakref.ref(parent)

   # Explicit cleanup
   def cleanup(self):
       self.callbacks.clear()
       self.cache.clear()
   ```

2. **Check Qt object cleanup**:
   ```python
   def destroy_instance(self, instance_id: str):
       if instance_id in self._instances:
           widget = self._instances[instance_id]
           widget.close()
           widget.deleteLater()  # Important for Qt cleanup
           del self._instances[instance_id]
   ```

### Performance Issues

#### Issue: Slow Plugin Loading
```
Warning: Plugin 'my-plugin' took 5.2s to load (expected < 1s)
```

**Diagnosis:**
```bash
viloapp profile my-plugin --startup
python -m cProfile -o profile.out -c "import my_plugin"
```

**Solutions:**
1. **Lazy imports**:
   ```python
   # Bad - import at module level
   import heavy_module

   # Good - import when needed
   def use_heavy_feature(self):
       import heavy_module
       return heavy_module.function()
   ```

2. **Defer heavy initialization**:
   ```python
   def activate(self, context):
       self.context = context
       # Don't do heavy work here

   def on_first_use(self):
       if not hasattr(self, '_initialized'):
           self._initialize_heavy_components()
           self._initialized = True
   ```

#### Issue: UI Freezing
```
Warning: UI thread blocked for 2.1s by plugin 'my-plugin'
```

**Solutions:**
1. **Use background threads**:
   ```python
   import threading
   from PySide6.QtCore import QObject, Signal

   class Worker(QObject):
       finished = Signal(object)

       def run(self):
           result = self.heavy_computation()
           self.finished.emit(result)

   def start_heavy_work(self):
       worker = Worker()
       thread = threading.Thread(target=worker.run)
       thread.start()
   ```

2. **Use Qt's async features**:
   ```python
   from PySide6.QtCore import QTimer

   def process_in_chunks(self):
       if self.data_to_process:
           chunk = self.data_to_process[:100]
           self.data_to_process = self.data_to_process[100:]
           self.process_chunk(chunk)

           # Continue later
           QTimer.singleShot(10, self.process_in_chunks)
   ```

## Diagnostic Tools

### Built-in Tools

#### System Status
```bash
viloapp status --detailed
viloapp status --json  # Machine-readable output
```

#### Plugin Validation
```bash
viloapp validate my-plugin --check-all
viloapp validate my-plugin --fix-issues
```

#### Resource Monitoring
```bash
viloapp monitor --all-plugins
viloapp monitor my-plugin --resource memory,cpu
viloapp monitor my-plugin --alert-threshold 80
```

#### Performance Profiling
```bash
viloapp profile my-plugin --startup
viloapp profile my-plugin --runtime --duration 60
viloapp profile my-plugin --memory --track-allocations
```

### External Tools

#### Python Debugging
```bash
# Memory profiling
pip install memory-profiler
python -m memory_profiler my_plugin.py

# Line profiling
pip install line-profiler
kernprof -l -v my_plugin.py

# Call graph profiling
pip install pycallgraph
pycallgraph graphviz -- python my_plugin.py
```

#### System Monitoring
```bash
# Process monitoring
htop -p $(pgrep viloapp)

# File system monitoring
inotifywait -m -r ~/.local/share/viloapp/plugins/

# Network monitoring
netstat -tulpn | grep viloapp
```

## Log Analysis

### Log Locations
- **System logs**: `~/.local/share/viloapp/logs/system.log`
- **Plugin logs**: `~/.local/share/viloapp/logs/plugins/`
- **Security logs**: `~/.local/share/viloapp/logs/security.log`
- **Performance logs**: `~/.local/share/viloapp/logs/performance.log`

### Log Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General information
- **WARNING**: Warning conditions
- **ERROR**: Error conditions
- **CRITICAL**: Critical problems

### Log Analysis Commands
```bash
# View recent errors
viloapp logs --level error --since "1 hour ago"

# Filter by plugin
viloapp logs --plugin my-plugin --level warning

# Follow logs in real-time
viloapp logs --follow --format json

# Search for specific patterns
viloapp logs --grep "permission denied" --context 3
```

### Log Configuration
```yaml
# ~/.viloapp/logging.yaml
version: 1
formatters:
  detailed:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

handlers:
  file:
    class: logging.FileHandler
    filename: ~/.local/share/viloapp/logs/debug.log
    formatter: detailed
    level: DEBUG

loggers:
  my_plugin:
    level: DEBUG
    handlers: [file]
```

## Prevention Strategies

### Development Best Practices

1. **Use type hints**:
   ```python
   def create_instance(self, instance_id: str) -> QWidget:
       # Type hints help catch errors early
   ```

2. **Implement proper error handling**:
   ```python
   try:
       result = risky_operation()
   except SpecificException as e:
       self.logger.error(f"Operation failed: {e}")
       return fallback_value()
   ```

3. **Add comprehensive logging**:
   ```python
   import logging
   logger = logging.getLogger(__name__)

   def important_function(self):
       logger.debug("Starting important operation")
       try:
           result = self.do_work()
           logger.info(f"Operation completed: {result}")
           return result
       except Exception as e:
           logger.error(f"Operation failed: {e}", exc_info=True)
           raise
   ```

4. **Write tests for edge cases**:
   ```python
   def test_widget_creation_with_invalid_id():
       factory = MyWidgetFactory()
       with pytest.raises(ValueError):
           factory.create_instance("")  # Empty instance ID
   ```

### Monitoring and Alerting

1. **Set up automated monitoring**:
   ```yaml
   # monitoring.yaml
   alerts:
     memory_usage:
       threshold: 80%
       action: log_warning

     cpu_usage:
       threshold: 70%
       action: throttle_plugin

     permission_violations:
       threshold: 5
       timeframe: 1h
       action: disable_plugin
   ```

2. **Use health checks**:
   ```python
   def health_check(self) -> Dict[str, Any]:
       return {
           "status": "healthy",
           "memory_usage": self.get_memory_usage(),
           "active_instances": len(self._instances),
           "last_error": self.last_error_time
       }
   ```

## Emergency Procedures

### Plugin Crashes System
1. **Disable problematic plugin**:
   ```bash
   viloapp disable my-plugin --force
   ```

2. **Start in safe mode**:
   ```bash
   viloapp --safe-mode
   ```

3. **Reset plugin system**:
   ```bash
   viloapp reset --plugins --keep-data
   ```

### System Won't Start
1. **Check logs for errors**:
   ```bash
   tail -n 100 ~/.local/share/viloapp/logs/system.log
   ```

2. **Start with minimal plugins**:
   ```bash
   viloapp --minimal-plugins
   ```

3. **Repair plugin database**:
   ```bash
   viloapp repair --plugin-database
   ```

### Data Recovery
1. **Backup plugin data**:
   ```bash
   viloapp backup --plugins --output ~/viloapp-backup.tar.gz
   ```

2. **Restore from backup**:
   ```bash
   viloapp restore ~/viloapp-backup.tar.gz --verify
   ```

## Getting Help

### Self-Help Resources
- **Documentation**: https://docs.viloapp.com/troubleshooting
- **FAQ**: https://docs.viloapp.com/faq
- **Video Tutorials**: https://videos.viloapp.com/troubleshooting

### Community Support
- **Discord**: https://discord.gg/viloapp
- **Forum**: https://forum.viloapp.com
- **Stack Overflow**: Tag questions with `viloapp`

### Professional Support
- **Bug Reports**: https://github.com/viloapp/viloapp/issues
- **Enterprise Support**: support@viloapp.com
- **Paid Consulting**: Available for complex issues

### When Reporting Issues

Include the following information:
1. **ViloxTerm version**: `viloapp --version`
2. **Plugin version**: From plugin manifest
3. **Operating system**: OS version and architecture
4. **Error messages**: Complete error messages and stack traces
5. **Reproduction steps**: Minimal steps to reproduce the issue
6. **System logs**: Relevant log entries
7. **Configuration**: Relevant configuration files

**Example Bug Report Template**:
```
**Environment:**
- ViloxTerm: 2.1.0
- Plugin: my-plugin 1.0.0
- OS: Ubuntu 22.04 x64
- Python: 3.10.8

**Issue:**
Plugin crashes when creating second widget instance

**Steps to Reproduce:**
1. Install my-plugin
2. Create first widget: viloapp create-widget my-plugin
3. Create second widget: viloapp create-widget my-plugin
4. Application crashes with segmentation fault

**Expected Behavior:**
Both widgets should be created successfully

**Actual Behavior:**
Application crashes on second widget creation

**Logs:**
[Include relevant log entries]

**Additional Context:**
Issue started after upgrading from ViloxTerm 2.0.0
```

This troubleshooting guide should help you diagnose and resolve most plugin-related issues. Remember that prevention through good development practices and monitoring is always better than debugging problems after they occur.