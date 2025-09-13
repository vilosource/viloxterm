# ViloxTerm Deployment Plan

## Overview
This document outlines the plan for creating standalone executables of ViloxTerm using pyside6-deploy. The deployment will handle the complex requirements of our terminal server, frameless window mode, and resource management.

## Phase 1: Prepare Application Assets

### 1.1 Create Application Icons
- [ ] Design/obtain ViloxTerm icon in SVG format
- [ ] Convert to platform-specific formats:
  - Windows: .ico (16x16, 32x32, 48x48, 256x256)
  - macOS: .icns (multiple resolutions)
  - Linux: .png (multiple sizes for different contexts)
- [ ] Place in `resources/icons/app/` directory

### 1.2 Compile Resources
- [ ] Ensure all Qt resources are compiled via `make resources`
- [ ] Verify resources_rc.py includes all necessary assets
- [ ] Test resource loading in development environment

## Phase 2: Configure Deployment Structure

### 2.1 Directory Structure
```
deploy/
├── pysidedeploy.spec      # Main deployment configuration
├── requirements-deploy.txt # Deployment-specific dependencies
├── icons/
│   ├── viloxterm.ico      # Windows application icon
│   ├── viloxterm.icns     # macOS application icon
│   └── viloxterm.png      # Linux application icon
├── scripts/
│   ├── build.py           # Multi-platform build script
│   └── test_deployment.py # Deployment testing script
└── platforms/
    ├── windows/
    │   └── installer.nsi  # NSIS installer script (optional)
    ├── linux/
    │   ├── viloxterm.desktop
    │   └── AppImageBuilder.yml
    └── macos/
        └── Info.plist     # macOS metadata
```

### 2.2 Handle Terminal Server Architecture
The terminal server presents unique challenges:
- Flask/SocketIO server runs in background
- xterm.js assets must be bundled
- Dynamic port allocation needed
- Multiple terminal sessions supported

Solutions:
- Bundle all terminal assets with application
- Use fixed port with fallback to dynamic
- Ensure proper cleanup on application exit
- Test terminal functionality in deployed version

## Phase 3: Initial pysidedeploy.spec Configuration

```toml
[app]
title = "ViloxTerm"
project_dir = "."
input_file = "main.py"
exec_directory = "."
icon = "deploy/icons/viloxterm.ico"

[python]
python_path = ".direnv/python-3.12.3/bin/python"
packages = "Nuitka==2.1.0"

[qt]
# Only include required Qt modules
modules = ["Core", "Widgets", "WebEngineWidgets", "Network", "Svg"]
plugins = ["platforms", "styles", "imageformats"]
excluded_qml_plugins = "QtQuick3D,QtCharts,QtTest,QtSensors,QtMultimedia"

[nuitka]
# Start with standalone for debugging, switch to onefile for distribution
mode = "standalone"

# Critical: Include all necessary data files and modules
extra_args = """
--include-data-files=resources/icons/**/*.svg=resources/icons/
--include-data-dir=ui/terminal/assets=ui/terminal/assets
--include-module=flask
--include-module=flask_socketio
--include-module=engineio.async_drivers.threading
--include-module=core.environment_detector
--include-module=resources.resources_rc
--windows-disable-console
--enable-plugin=pyside6
"""

[deployment]
platforms = ["Windows", "Linux", "Darwin"]
```

## Phase 4: Handle Special Dependencies

### 4.1 Terminal Server Requirements
- [ ] Bundle Flask and SocketIO properly
- [ ] Include all xterm.js assets
- [ ] Handle threading for terminal server
- [ ] Test PTY functionality on all platforms
- [ ] Ensure proper signal handling

### 4.2 Environment Detection
- [ ] Include environment detector module
- [ ] Test GPU detection in deployed version
- [ ] Verify Wayland/X11 detection on Linux
- [ ] Check WSL detection functionality

### 4.3 Settings Persistence
- [ ] Verify QSettings paths in deployed app
- [ ] Test frameless mode toggle persistence
- [ ] Ensure workspace state saves correctly
- [ ] Check configuration file locations

## Phase 5: Platform-Specific Configuration

### 5.1 Windows
```toml
[nuitka]
extra_args = """
--windows-disable-console
--windows-icon-from-ico=deploy/icons/viloxterm.ico
--windows-company-name="ViloxTerm"
--windows-product-name="ViloxTerm Terminal"
--windows-file-version=1.0.0.0
--windows-product-version=1.0.0.0
--windows-file-description="Modern Terminal Emulator"
"""
```

### 5.2 Linux
- Create desktop entry file
- Consider AppImage for distribution
- Test on both X11 and Wayland
- Handle different distributions

### 5.3 macOS
- Configure Info.plist
- Handle code signing (future)
- Test on Apple Silicon and Intel
- Request necessary permissions

## Phase 6: Size and Performance Optimization

### 6.1 Reduce Executable Size
- [ ] Exclude unused Qt modules
- [ ] Strip debug symbols: `--strip`
- [ ] Enable LTO: `--lto=yes`
- [ ] Consider UPX compression (test carefully)
- [ ] Remove unnecessary Python modules

### 6.2 Improve Startup Performance
- [ ] Profile application startup
- [ ] Implement lazy imports where possible
- [ ] Optimize resource loading
- [ ] Consider standalone vs onefile tradeoffs

Target metrics:
- Executable size: < 50MB (without UPX)
- Startup time: < 2 seconds
- Memory usage: < 100MB initial

## Phase 7: Build Automation

### 7.1 Makefile Targets
```makefile
# First-time deployment setup
deploy-init:
	pyside6-deploy main.py --name ViloxTerm --icon deploy/icons/viloxterm.ico

# Build executable
deploy:
	pyside6-deploy -c deploy/pysidedeploy.spec

# Clean build artifacts
deploy-clean:
	rm -rf build/ dist/ *.bin *.exe *.app

# Build for all platforms
deploy-all:
	python deploy/scripts/build.py --all-platforms

# Test deployment
deploy-test:
	python deploy/scripts/test_deployment.py
```

### 7.2 CI/CD Integration
- GitHub Actions workflow for automated builds
- Build on push to release branch
- Upload artifacts for each platform
- Automated testing of executables

## Phase 8: Testing Strategy

### 8.1 Core Functionality Tests
- [ ] Application launches successfully
- [ ] Terminal server starts and accepts connections
- [ ] Multiple terminal sessions work
- [ ] Frameless window mode toggles correctly
- [ ] Settings persist between runs
- [ ] All keyboard shortcuts function
- [ ] Resource icons load properly
- [ ] Theme switching works

### 8.2 Platform-Specific Tests
- [ ] Windows: Console window hidden, UAC handling
- [ ] Linux: Works on X11 and Wayland
- [ ] macOS: Permissions granted, retina display support

### 8.3 Automated Testing Script
```python
# deploy/scripts/test_deployment.py
tests = [
    "test_executable_exists",
    "test_application_starts",
    "test_terminal_functionality",
    "test_settings_persistence",
    "test_resource_loading",
    "test_keyboard_shortcuts",
]
```

## Phase 9: Documentation

### 9.1 User Documentation
- [ ] Create DEPLOYMENT.md with build instructions
- [ ] Add troubleshooting section
- [ ] Include platform-specific notes
- [ ] Document known issues and workarounds

### 9.2 Developer Documentation
- [ ] Document build process
- [ ] Explain configuration options
- [ ] Provide debugging tips
- [ ] Include performance optimization guide

## Phase 10: Distribution

### 10.1 Release Artifacts
- Windows: Single .exe or installer
- Linux: AppImage and .tar.gz
- macOS: .app bundle or .dmg

### 10.2 Version Management
- Use semantic versioning
- Inject version into executable
- Tag releases in git
- Generate changelog

## Implementation Order

1. **Week 1: Foundation**
   - Create deployment directory structure
   - Generate application icons
   - Initial pysidedeploy.spec configuration
   - Basic deployment test

2. **Week 2: Terminal Server**
   - Handle Flask/SocketIO bundling
   - Include xterm.js assets
   - Test terminal functionality
   - Fix deployment issues

3. **Week 3: Platform Optimization**
   - Windows-specific configuration
   - Linux AppImage creation
   - macOS bundle preparation
   - Platform testing

4. **Week 4: Polish and Release**
   - Size optimization
   - Performance tuning
   - Documentation completion
   - CI/CD setup

## Success Criteria

- [ ] Executable runs on fresh system without Python installed
- [ ] File size under 50MB (100MB with UPX)
- [ ] Startup time under 2 seconds
- [ ] All features work as in development
- [ ] No missing dependencies or modules
- [ ] Professional appearance and behavior

## Known Challenges

1. **Terminal Server**: Complex architecture with Flask/SocketIO
2. **Resource Bundling**: Ensuring all assets are included
3. **Platform Differences**: Handling OS-specific behaviors
4. **Size Optimization**: Balancing size vs functionality
5. **Testing**: Automated testing of GUI application

## Next Steps

1. Create deployment directory structure
2. Generate ViloxTerm icon
3. Configure initial pysidedeploy.spec
4. Test basic deployment
5. Iterate and fix issues