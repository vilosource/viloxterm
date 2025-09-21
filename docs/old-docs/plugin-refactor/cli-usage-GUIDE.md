# ViloxTerm Plugin CLI Usage Guide

## Overview

The ViloxTerm Plugin CLI (`viloapp`) is a comprehensive command-line tool for creating, developing, testing, and managing ViloxTerm plugins. This guide covers all commands with practical examples.

## Installation

The CLI tool is automatically installed with the `viloapp-cli` package:

```bash
pip install viloapp-cli
```

Verify installation:
```bash
viloapp --version
```

## Global Options

```bash
viloapp [OPTIONS] COMMAND [ARGS]...
```

**Global Options:**
- `--version`: Show the version and exit
- `--config PATH`: Path to configuration file
- `-v, --verbose`: Enable verbose output
- `--debug`: Enable debug output
- `--help`: Show help message

## Commands

### `create` - Create New Plugin

Create a new plugin from templates.

#### Basic Plugin
```bash
viloapp create my-plugin
```

Creates:
```
my-plugin/
├── plugin.json          # Plugin manifest
├── src/
│   └── my_plugin/
│       ├── __init__.py
│       └── plugin.py    # Main plugin class
├── tests/
│   └── test_plugin.py
├── README.md
└── pyproject.toml
```

#### Widget Plugin
```bash
viloapp create my-widget --type widget
```

Creates additional files:
```
my-widget/
├── src/
│   └── my_widget/
│       ├── plugin.py
│       ├── widget.py    # Widget implementation
│       └── ui/
│           └── widget.ui
└── resources/
    └── icons/
```

#### Command Plugin
```bash
viloapp create my-commands --type command
```

#### Service Plugin
```bash
viloapp create my-service --type service
```

#### Advanced Options
```bash
viloapp create my-plugin \
  --author "Your Name" \
  --email "your.email@example.com" \
  --license "MIT" \
  --description "Plugin description" \
  --keywords "keyword1,keyword2" \
  --template-dir ~/custom-templates
```

### `dev` - Development Mode

Run plugin in development mode with hot reload.

#### Basic Development
```bash
cd my-plugin
viloapp dev
```

#### Specify Plugin Path
```bash
viloapp dev --plugin /path/to/plugin
```

#### Development Options
```bash
viloapp dev \
  --plugin ./my-plugin \
  --host localhost \
  --port 8080 \
  --reload-delay 1.0 \
  --exclude "*.tmp,*.log" \
  --watch-extensions ".py,.json,.ui"
```

#### Hot Reload Features
- **File Watching**: Automatically detects changes
- **Plugin Reload**: Reloads plugin without restarting host
- **State Preservation**: Maintains plugin state during reload
- **Error Recovery**: Handles reload errors gracefully

### `test` - Run Tests

Execute plugin tests with various options.

#### Run All Tests
```bash
viloapp test my-plugin
```

#### Specific Test Categories
```bash
# Unit tests only
viloapp test my-plugin --unit

# Integration tests only
viloapp test my-plugin --integration

# GUI tests only
viloapp test my-plugin --gui
```

#### Test Options
```bash
viloapp test my-plugin \
  --coverage \
  --coverage-report html \
  --verbose \
  --parallel \
  --timeout 60
```

#### Test Configuration
```yaml
# .viloapp/test-config.yaml
test:
  parallel: true
  timeout: 30
  coverage:
    enabled: true
    threshold: 80
    format: ["term", "html"]

  paths:
    unit: "tests/unit"
    integration: "tests/integration"
    gui: "tests/gui"

  pytest_args: ["-v", "--tb=short"]
```

### `package` - Package Plugin

Create distributable plugin packages.

#### Basic Packaging
```bash
viloapp package my-plugin
```

Creates: `my-plugin-1.0.0.vpkg`

#### Package Options
```bash
viloapp package my-plugin \
  --output-dir ./dist \
  --format zip \
  --include-dev-deps \
  --compress \
  --sign
```

#### Package Formats
- **vpkg**: ViloxTerm package format (default)
- **zip**: Standard ZIP archive
- **tar.gz**: Compressed tar archive

#### Package Structure
```
my-plugin-1.0.0.vpkg
├── plugin.json
├── src/
├── resources/
├── MANIFEST.txt
├── CHECKSUM.sha256
└── signature.sig (if signed)
```

### `install` - Install Plugin

Install plugins from various sources.

#### Install from File
```bash
viloapp install my-plugin-1.0.0.vpkg
```

#### Install from URL
```bash
viloapp install https://github.com/user/plugin/releases/download/v1.0/plugin.vpkg
```

#### Install from Registry
```bash
viloapp install plugin-name
viloapp install plugin-name@1.2.3  # Specific version
```

#### Installation Options
```bash
viloapp install plugin.vpkg \
  --force \
  --no-deps \
  --user \
  --dev \
  --pre
```

### `list` - List Plugins

Display installed plugins with information.

#### Basic List
```bash
viloapp list
```

Output:
```
Installed Plugins:
┌─────────────┬─────────┬──────────┬─────────┬────────────┐
│ ID          │ Version │ Author   │ Status  │ Location   │
├─────────────┼─────────┼──────────┼─────────┼────────────┤
│ viloxterm   │ 1.0.0   │ Team     │ Active  │ Built-in   │
│ viloedit    │ 1.0.0   │ Team     │ Active  │ Built-in   │
│ my-plugin   │ 0.1.0   │ Me       │ Disabled│ User       │
└─────────────┴─────────┴──────────┴─────────┴────────────┘
```

#### List Options
```bash
# JSON format
viloapp list --format json

# Show disabled plugins
viloapp list --all

# Filter by status
viloapp list --status active

# Show detailed information
viloapp list --verbose
```

#### JSON Output
```json
{
  "plugins": [
    {
      "id": "viloxterm",
      "version": "1.0.0",
      "author": "ViloxTerm Team",
      "status": "active",
      "location": "built-in",
      "path": "/usr/share/viloapp/plugins/viloxterm"
    }
  ],
  "total": 1,
  "active": 1,
  "disabled": 0
}
```

## Configuration

### Global Configuration

Create `~/.viloapp/config.yaml`:

```yaml
# Default configuration
defaults:
  author: "Your Name"
  email: "your.email@example.com"
  license: "MIT"

# Plugin directories
directories:
  plugins: "~/.local/share/viloapp/plugins"
  templates: "~/.local/share/viloapp/templates"
  cache: "~/.cache/viloapp"

# Development settings
development:
  auto_reload: true
  reload_delay: 1.0
  host: "localhost"
  port: 8080

# Testing configuration
testing:
  parallel: true
  coverage_threshold: 80
  timeout: 30

# Package registry
registry:
  default: "https://registry.viloapp.com"
  mirrors:
    - "https://mirror1.viloapp.com"
    - "https://mirror2.viloapp.com"
```

### Project Configuration

Create `.viloapp/config.yaml` in plugin directory:

```yaml
# Plugin-specific configuration
plugin:
  type: "widget"
  main_class: "MyPlugin"
  hot_reload: true

# Development settings
dev:
  watch_paths: ["src", "resources"]
  ignore_patterns: ["*.pyc", "__pycache__"]
  reload_on_dependency_change: true

# Testing
test:
  pytest_args: ["-v", "--tb=short"]
  coverage_config: ".coveragerc"

# Packaging
package:
  exclude: ["tests", "docs", "*.log"]
  include_dev_deps: false
  sign: true
```

## Advanced Usage

### Template Customization

Create custom templates in `~/.local/share/viloapp/templates/`:

```
custom-widget/
├── template.yaml
├── plugin.json.j2
└── src/
    └── {{plugin_id}}/
        ├── __init__.py.j2
        └── widget.py.j2
```

Template configuration (`template.yaml`):
```yaml
name: "Custom Widget Plugin"
description: "Widget plugin with custom features"
variables:
  - name: "widget_title"
    description: "Widget display title"
    type: "string"
    default: "My Widget"
  - name: "enable_toolbar"
    description: "Enable widget toolbar"
    type: "boolean"
    default: true
```

Use custom template:
```bash
viloapp create my-widget --template custom-widget
```

### Plugin Registry

#### Publish Plugin
```bash
viloapp publish my-plugin \
  --registry https://registry.viloapp.com \
  --token $REGISTRY_TOKEN
```

#### Search Registry
```bash
viloapp search "terminal emulator"
viloapp search --category "editor"
viloapp search --author "viloapp-team"
```

#### Plugin Information
```bash
viloapp info viloxterm
viloapp info viloxterm@1.0.0
```

### Batch Operations

#### Install Multiple Plugins
```bash
viloapp install plugin1 plugin2 plugin3

# From file
viloapp install --requirements plugins.txt
```

plugins.txt:
```
viloxterm>=1.0.0
viloedit==1.0.0
my-custom-plugin
```

#### Bulk Package
```bash
viloapp package --all --output-dir ./packages
```

### Debugging

#### Enable Debug Logging
```bash
viloapp --debug dev my-plugin
```

#### Verbose Output
```bash
viloapp -v test my-plugin
```

#### Log Files
- `~/.local/share/viloapp/logs/cli.log` - CLI operations
- `~/.local/share/viloapp/logs/dev.log` - Development mode
- `~/.local/share/viloapp/logs/package.log` - Packaging operations

## Integration with IDEs

### Visual Studio Code

Install the ViloxTerm Plugin Development extension:

1. Open VS Code
2. Install "ViloxTerm Plugin Dev" extension
3. Open plugin project
4. Use Command Palette: "ViloxTerm: Create Plugin"

### IntelliJ IDEA / PyCharm

Configure external tools:

1. Go to File → Settings → Tools → External Tools
2. Add new tool:
   - Name: "ViloxTerm Dev"
   - Program: `viloapp`
   - Arguments: `dev --plugin $ProjectFileDir$`
   - Working directory: `$ProjectFileDir$`

## Troubleshooting

### Common Issues

#### Plugin Not Found
```
Error: Plugin 'my-plugin' not found
```

**Solutions:**
- Check plugin path is correct
- Ensure plugin.json exists
- Verify plugin is installed

#### Permission Denied
```
Error: Permission denied creating plugin directory
```

**Solutions:**
- Check directory permissions
- Run with appropriate privileges
- Use `--user` flag for user installation

#### Development Server Won't Start
```
Error: Address already in use: localhost:8080
```

**Solutions:**
- Use different port: `--port 8081`
- Kill existing processes on port
- Check firewall settings

#### Package Creation Failed
```
Error: Failed to create package: Missing required files
```

**Solutions:**
- Ensure plugin.json is valid
- Check all referenced files exist
- Run `viloapp validate my-plugin` first

### Getting Help

#### Command Help
```bash
viloapp --help
viloapp create --help
viloapp dev --help
```

#### Verbose Output
```bash
viloapp -v command args
```

#### Support Resources
- Documentation: https://docs.viloapp.com
- Issues: https://github.com/viloapp/viloapp/issues
- Community: https://discord.gg/viloapp

## Examples

### Complete Plugin Development Workflow

```bash
# 1. Create new plugin
viloapp create awesome-terminal --type widget

# 2. Enter directory
cd awesome-terminal

# 3. Start development
viloapp dev &

# 4. Edit plugin code
# ... make changes ...

# 5. Run tests
viloapp test --coverage

# 6. Package plugin
viloapp package --output-dir dist

# 7. Install locally for testing
viloapp install dist/awesome-terminal-1.0.0.vpkg

# 8. Publish to registry
viloapp publish --registry https://registry.viloapp.com
```

### Multi-Plugin Project

```bash
# Create workspace
mkdir my-plugins && cd my-plugins

# Create multiple plugins
viloapp create terminal-enhancer --type widget
viloapp create code-analyzer --type service
viloapp create build-tools --type command

# Development mode for all
for plugin in terminal-enhancer code-analyzer build-tools; do
  viloapp dev --plugin $plugin &
done

# Test all plugins
for plugin in terminal-enhancer code-analyzer build-tools; do
  viloapp test $plugin
done

# Package all plugins
viloapp package --all --output-dir packages
```

This guide covers the essential usage patterns for the ViloxTerm Plugin CLI. For more advanced features and API reference, see the [CLI API Documentation](./cli-api-REFERENCE.md).