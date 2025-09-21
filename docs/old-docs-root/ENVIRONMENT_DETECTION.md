# Environment Detection and Auto-Configuration System

## Overview

This application includes an automatic environment detection system that configures Qt and rendering settings based on the runtime environment. This solves common issues like OpenGL errors in WSL, performance problems in Docker, and display issues over SSH.

## Problem Solved

When running Qt/PySide6 applications in different environments, various issues can occur:
- **WSL**: OpenGL/GPU errors due to limited GPU passthrough
- **Docker**: Shared memory and display issues
- **SSH**: X11 forwarding and rendering problems
- **Remote Desktop**: Graphics acceleration conflicts

Previously, users had to manually set environment variables like:
```bash
export LIBGL_ALWAYS_SOFTWARE=1
export QT_QUICK_BACKEND=software
export QTWEBENGINE_DISABLE_SANDBOX=1
```

## Solution Architecture

The system uses the **Strategy Pattern** to apply platform-specific configurations automatically:

```
main.py
  ├─> EnvironmentConfigurator (before Qt imports!)
      ├─> EnvironmentDetector.detect()
      │     ├─> Detect OS type
      │     ├─> Check for WSL/Docker/SSH
      │     └─> Detect GPU availability
      └─> Select & Apply Strategy
            ├─> WSLStrategy
            ├─> DockerStrategy
            ├─> SSHStrategy
            ├─> NativeLinuxStrategy
            ├─> MacOSStrategy
            └─> WindowsStrategy
```

## How It Works

### 1. Detection Phase
The `EnvironmentDetector` checks for:
- **Operating System**: Linux, macOS, Windows
- **WSL Detection**: Checks `/proc/version` for "microsoft" or WSL env vars
- **Docker Detection**: Looks for `/.dockerenv` or docker in cgroups
- **SSH Detection**: Checks for `SSH_CLIENT` or `SSH_TTY` env vars
- **Display Server**: X11, Wayland, or WSLg
- **GPU Availability**: Runs `glxinfo` to check for hardware acceleration

### 2. Configuration Phase
Based on detection, appropriate strategy is selected and applied:

#### WSL Configuration
```python
{
    'LIBGL_ALWAYS_SOFTWARE': '1',           # Force software rendering
    'QTWEBENGINE_DISABLE_SANDBOX': '1',     # Sandbox issues in WSL
    'QT_QUICK_BACKEND': 'software',         # Software Qt Quick backend
    'QTWEBENGINE_CHROMIUM_FLAGS': '--disable-gpu --no-sandbox'
}
```

#### Docker Configuration
```python
{
    'QT_QUICK_BACKEND': 'software',
    'QT_XCB_GL_INTEGRATION': 'none',
    'LIBGL_ALWAYS_SOFTWARE': '1',
    'QT_X11_NO_MITSHM': '1'                # Disable shared memory
}
```

#### Native Linux Configuration
- Only disables GPU if not available
- Respects Wayland vs X11 display server
- Enables full hardware acceleration when possible

### 3. Application Phase
Configuration is applied **before** Qt modules are imported:
```python
# main.py structure
import sys
import logging

# Configure environment FIRST
from core.environment_detector import EnvironmentConfigurator
env_configurator = EnvironmentConfigurator()
env_configurator.apply_configuration()

# THEN import Qt
from PySide6.QtWidgets import QApplication
```

## Usage

### Automatic (Default)
Simply run the application normally:
```bash
python main.py
```

The system automatically detects and configures the environment.

### Manual Override
You can still set environment variables manually if needed:
```bash
# Force specific platform
export QT_QPA_PLATFORM=xcb
python main.py

# Disable auto-configuration
export DISABLE_ENV_DETECTION=1
python main.py
```

### Check Detection
To see what environment was detected:
```python
from core.environment_detector import EnvironmentDetector
info = EnvironmentDetector.detect()
print(f"OS: {info.os_type}")
print(f"WSL: {info.is_wsl}")
print(f"GPU: {info.gpu_available}")
```

## Troubleshooting

### Application doesn't show in WSL
- Ensure WSLg is installed: `wsl --update`
- Check DISPLAY variable: `echo $DISPLAY`
- Try running with X410 or VcXsrv

### OpenGL errors still occurring
- The detector may not have run before Qt import
- Check that `main.py` imports environment detector first
- Verify with: `python -c "import os; print(os.environ.get('LIBGL_ALWAYS_SOFTWARE'))"`

### Performance issues
- Software rendering is slower but more compatible
- For better performance, use native Linux or WSL2 with GPU support
- Consider using Windows Terminal + SSH instead of GUI in WSL

### Docker specific issues
```bash
# Run with X11 socket mounted
docker run -e DISPLAY=$DISPLAY \
           -v /tmp/.X11-unix:/tmp/.X11-unix \
           your-app

# Or use x11docker for better integration
x11docker your-app
```

## Platform Configuration Reference

### WSL/WSL2
| Setting | Value | Purpose |
|---------|-------|---------|
| LIBGL_ALWAYS_SOFTWARE | 1 | Forces Mesa software rendering |
| QTWEBENGINE_DISABLE_SANDBOX | 1 | Chromium sandbox incompatible |
| QT_QUICK_BACKEND | software | Disables OpenGL in Qt Quick |
| QTWEBENGINE_CHROMIUM_FLAGS | --disable-gpu | Disables GPU in web engine |

### Docker
| Setting | Value | Purpose |
|---------|-------|---------|
| QT_X11_NO_MITSHM | 1 | Disables MIT-SHM (shared memory) |
| QT_XCB_GL_INTEGRATION | none | Disables GL integration |
| LIBGL_ALWAYS_SOFTWARE | 1 | Software rendering |

### SSH Sessions
| Setting | Value | Purpose |
|---------|-------|---------|
| QT_X11_NO_MITSHM | 1 | Better X11 forwarding |
| LIBGL_ALWAYS_SOFTWARE | 1 | Avoids GL over network |

### Native Linux
| Setting | Value | Purpose |
|---------|-------|---------|
| QT_AUTO_SCREEN_SCALE_FACTOR | 1 | HiDPI support |
| QT_QPA_PLATFORM | wayland/xcb | Auto-detected |

### macOS
| Setting | Value | Purpose |
|---------|-------|---------|
| QT_MAC_WANTS_LAYER | 1 | Metal layer rendering |

### Windows
| Setting | Value | Purpose |
|---------|-------|---------|
| QT_OPENGL | angle | ANGLE for compatibility |
| QT_ENABLE_HIGHDPI_SCALING | 1 | HiDPI support |

## Extending the System

### Adding a New Platform
Create a new strategy class:
```python
class MyPlatformStrategy(EnvironmentStrategy):
    def configure(self) -> Dict[str, str]:
        return {
            'MY_SETTING': 'value'
        }
    
    def get_qt_flags(self) -> Dict[str, str]:
        return {
            'QT_SOME_FLAG': '1'
        }
    
    def get_recommendations(self) -> str:
        return "Platform-specific recommendations"
```

### Adding Detection Logic
Extend `EnvironmentDetector`:
```python
@staticmethod
def _is_my_platform() -> bool:
    # Detection logic
    return 'MY_PLATFORM' in os.environ
```

### Custom Configuration
In your project:
```python
from core.environment_detector import EnvironmentConfigurator

# Before Qt imports
configurator = EnvironmentConfigurator()

# Add custom settings
env_vars = configurator.strategy.configure()
env_vars['MY_CUSTOM_VAR'] = 'value'

# Apply all
for key, value in env_vars.items():
    os.environ[key] = value
```

## Benefits

1. **Zero Configuration**: Works out of the box on all platforms
2. **Automatic Optimization**: Chooses best settings for each environment
3. **Fallback Safety**: Defaults to compatible settings when uncertain
4. **Debugging Support**: Logs detection results and applied settings
5. **Extensible**: Easy to add new platforms or modify settings
6. **Cross-Platform**: Single codebase works everywhere

## Related Files

- `/core/environment_detector.py` - Main detection and configuration module
- `/main.py` - Integration point (configures before Qt import)
- `/.envrc` - Can still override with direnv if needed

## Testing

Run tests on different platforms:
```bash
# Test detection
python -m pytest tests/test_environment_detector.py

# Test on WSL
wsl python main.py

# Test in Docker
docker build -t app . && docker run app

# Test over SSH
ssh -X user@host 'cd /path/to/app && python main.py'
```