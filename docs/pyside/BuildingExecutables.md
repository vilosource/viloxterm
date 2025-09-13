# Building Executables with PySide6-Deploy

A comprehensive guide to deploying PySide6 applications as standalone executables across Windows, Linux, and macOS platforms using the official `pyside6-deploy` tool.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Platform-Specific Considerations](#platform-specific-considerations)
- [Optimization Techniques](#optimization-techniques)
- [Troubleshooting](#troubleshooting)
- [Alternative Deployment Methods](#alternative-deployment-methods)

---

## Overview

`pyside6-deploy` is the official deployment tool for PySide6 applications, introduced in PySide6 6.5+. It simplifies the process of creating standalone executables by:

- **Wrapping Nuitka** - Compiles Python to C++ for better performance and smaller executables
- **Managing dependencies** - Automatically detects and bundles required modules
- **Cross-platform support** - Creates `.exe` (Windows), `.bin` (Linux), `.app` (macOS)
- **Optimizing Qt modules** - Smart detection and exclusion of unused Qt components

### Why Use pyside6-deploy?

| Feature | pyside6-deploy | PyInstaller | cx_Freeze |
|---------|---------------|-------------|-----------|
| **Executable Size** | ✅ Smallest | ❌ Larger | ❌ Larger |
| **Performance** | ✅ Best (compiled) | ⚠️ Good | ⚠️ Good |
| **Qt Integration** | ✅ Native | ⚠️ Manual | ⚠️ Manual |
| **Setup Complexity** | ✅ Simple | ⚠️ Moderate | ❌ Complex |
| **Build Time** | ❌ Slower | ✅ Fast | ✅ Fast |

---

## Prerequisites

### Installation

```bash
# PySide6 includes pyside6-deploy by default
pip install PySide6>=6.5.0

# Verify installation
pyside6-deploy --help
```

### System Requirements

#### Windows
```bash
# Install Visual Studio Build Tools (for dumpbin)
# Download from: https://visualstudio.microsoft.com/downloads/
# Select "Desktop development with C++"
```

#### Linux
```bash
# Install required tools
sudo apt-get update
sudo apt-get install patchelf  # For binary patching
sudo apt-get install binutils  # For readelf
```

#### macOS
```bash
# Xcode Command Line Tools (includes dyld_info)
xcode-select --install
```

### Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv deploy_env

# Activate
# Windows
deploy_env\Scripts\activate
# Linux/macOS
source deploy_env/bin/activate

# Install dependencies
pip install PySide6 nuitka
```

---

## Quick Start

### Basic Deployment

#### 1. Simple Application Structure
```
my_app/
├── main.py           # Entry point with if __name__ == "__main__"
├── ui/
│   ├── main_window.py
│   └── resources.qrc
└── utils/
    └── helpers.py
```

#### 2. Deploy Command
```bash
# Navigate to project directory
cd my_app

# Deploy (first time - creates pysidedeploy.spec)
pyside6-deploy main.py

# Subsequent deployments (uses existing spec)
pyside6-deploy
```

#### 3. Output
```
my_app/
├── main.exe          # Windows
├── main.bin          # Linux
└── main.app/         # macOS
    └── Contents/
        └── MacOS/
            └── main
```

### Minimal Example Application

```python
# main.py
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 Deploy Example")

        button = QPushButton("Click Me!")
        button.clicked.connect(self.on_click)
        self.setCentralWidget(button)

    def on_click(self):
        print("Button clicked!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

Deploy:
```bash
pyside6-deploy main.py --name "MyApp"
```

---

## Configuration

### The pysidedeploy.spec File

Generated automatically on first run, controls all deployment parameters:

```toml
# pysidedeploy.spec

[app]
# Application name and metadata
title = "My Application"
project_dir = "."
input_file = "main.py"
exec_directory = "."
icon = "resources/icon.ico"  # .ico for Windows, .icns for macOS

[python]
# Python configuration
python_path = "/path/to/python"
packages = "Nuitka==2.6.8"  # Nuitka version

[qt]
# Qt modules and resources
qml_files = "qml/"
excluded_qml_plugins = "QtQuick3D,QtCharts,QtWebEngine,QtTest"

# Explicitly include modules if not auto-detected
modules = ["Network", "Svg", "Widgets"]

# Include specific plugins
plugins = ["platforms", "styles", "imageformats"]

[nuitka]
# Deployment mode
# - onefile: Single executable (default)
# - standalone: Folder with executable and libraries
mode = "onefile"

# Extra Nuitka arguments
extra_args = "--quiet --assume-yes-for-downloads"

[deployment]
# Platform-specific settings
platforms = ["Windows", "Linux", "Darwin"]
```

### Advanced Configuration Options

#### Including Additional Files

```toml
[nuitka]
# Include data files
extra_args = """
--include-data-files=config.json=config.json
--include-data-files=assets/*.png=assets/
--include-data-dir=resources=resources
"""
```

#### Excluding Unnecessary Modules

```toml
[qt]
# Exclude heavy modules if not needed
excluded_qml_plugins = "QtQuick3D,QtCharts,QtWebEngine,QtTest,QtSensors"

[nuitka]
# Exclude Python modules
extra_args = """
--nofollow-import-to=tkinter
--nofollow-import-to=matplotlib
"""
```

#### Custom Icon and Version Info (Windows)

```toml
[app]
icon = "resources/app.ico"

[nuitka]
extra_args = """
--windows-icon-from-ico=resources/app.ico
--windows-company-name="My Company"
--windows-product-name="My Product"
--windows-file-version=1.0.0.0
--windows-product-version=1.0.0.0
--windows-file-description="My Application"
"""
```

---

## Platform-Specific Considerations

### Windows

#### Console Window
```toml
[nuitka]
# Hide console window for GUI apps
extra_args = "--windows-disable-console"
```

#### Code Signing
```bash
# After building, sign the executable
signtool sign /f certificate.pfx /p password /t http://timestamp.server.com myapp.exe
```

#### Antivirus Issues
- Add executable to Windows Defender exclusions during development
- Submit false positives to antivirus vendors
- Consider code signing certificate for production

### Linux

#### Desktop Integration
Create `.desktop` file for application menu:

```ini
# myapp.desktop
[Desktop Entry]
Type=Application
Name=My Application
Exec=/opt/myapp/myapp.bin
Icon=/opt/myapp/icon.png
Categories=Utility;
```

#### AppImage Creation
```bash
# After pyside6-deploy
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# Create AppDir structure
mkdir -p MyApp.AppDir/usr/bin
cp main.bin MyApp.AppDir/usr/bin/
cp myapp.desktop MyApp.AppDir/
cp icon.png MyApp.AppDir/

# Build AppImage
./appimagetool-x86_64.AppImage MyApp.AppDir
```

### macOS

#### App Bundle Structure
```
MyApp.app/
├── Contents/
│   ├── Info.plist
│   ├── MacOS/
│   │   └── MyApp
│   ├── Resources/
│   │   └── icon.icns
│   └── Frameworks/
│       └── (Qt frameworks)
```

#### Code Signing and Notarization
```bash
# Sign the app
codesign --deep --force --verify --verbose --sign "Developer ID" MyApp.app

# Notarize (required for distribution)
xcrun altool --notarize-app --primary-bundle-id "com.company.myapp" \
  --username "apple@id.com" --password "@keychain:AC_PASSWORD" \
  --file MyApp.zip
```

#### Permissions (macOS 10.14+)
Add to Info.plist for required permissions:
```xml
<key>NSCameraUsageDescription</key>
<string>This app needs camera access</string>
```

---

## Optimization Techniques

### 1. Reduce Executable Size

#### Exclude Unused Qt Modules
```toml
[qt]
# Only include what you use
modules = ["Core", "Widgets"]  # Don't include "all"
excluded_qml_plugins = "QtQuick3D,QtCharts,QtWebEngine,QtTest,QtSensors"
```

#### Strip Debug Symbols
```toml
[nuitka]
extra_args = "--lto=yes --strip"
```

#### Use UPX Compression (Optional)
```bash
# Download UPX: https://upx.github.io/
upx --best myapp.exe  # Can reduce size by 50-70%
```

### 2. Improve Startup Time

#### Use Standalone Mode for Faster Startup
```toml
[nuitka]
mode = "standalone"  # Faster startup than onefile
```

#### Lazy Import Heavy Modules
```python
# Instead of
import heavy_module

# Use
def use_heavy_feature():
    import heavy_module
    heavy_module.do_something()
```

### 3. Handle Resources Properly

#### Compile Qt Resources
```bash
# Compile .qrc to Python module
pyside6-rcc resources.qrc -o resources_rc.py

# Import in main.py
import resources_rc
```

#### Access Bundled Files
```python
import sys
import os

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and deployed"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller path
        return os.path.join(sys._MEIPASS, relative_path)
    elif hasattr(sys, 'frozen'):
        # Nuitka path
        return os.path.join(os.path.dirname(sys.executable), relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Usage
icon_path = resource_path("icons/app.png")
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Module not found" after deployment
```toml
# Solution: Explicitly include the module
[qt]
modules = ["Network", "WebEngineWidgets"]

[nuitka]
extra_args = "--include-module=requests"
```

#### Issue: QML files not loading
```toml
# Solution: Include QML files
[qt]
qml_files = "qml/"

[nuitka]
extra_args = "--include-data-dir=qml=qml"
```

#### Issue: Icons/Images not showing
```python
# Solution: Use resource system or bundle files
# Option 1: Qt Resource System (.qrc)
icon = QIcon(":/icons/app.png")

# Option 2: Bundle with executable
icon = QIcon(resource_path("icons/app.png"))
```

#### Issue: Large executable size
```bash
# Check what's included
pyside6-deploy --dry-run  # See Nuitka command

# Analyze with tools
# Windows: dumpbin /dependents myapp.exe
# Linux: ldd myapp.bin
# macOS: otool -L myapp.app/Contents/MacOS/myapp
```

### Debug Deployment Issues

#### Enable Verbose Output
```bash
pyside6-deploy -v main.py
```

#### Keep Build Files for Inspection
```bash
pyside6-deploy --keep-deployment-files main.py
```

#### Test Nuitka Command Directly
```bash
# See generated command
pyside6-deploy --dry-run

# Run Nuitka directly for debugging
python -m nuitka --standalone --enable-plugin=pyside6 main.py
```

---

## Alternative Deployment Methods

### PyInstaller (Faster Builds)

```bash
pip install pyinstaller

# Basic usage
pyinstaller --onefile --windowed main.py

# With icon and name
pyinstaller --onefile --windowed --icon=icon.ico --name="MyApp" main.py
```

**Pros:**
- Faster build times
- Simpler configuration
- Good for development/testing

**Cons:**
- Larger executables
- Slower startup
- Less optimization

### Manual Nuitka (Full Control)

```bash
pip install nuitka

# Full control over options
python -m nuitka \
    --standalone \
    --onefile \
    --enable-plugin=pyside6 \
    --windows-disable-console \
    --windows-icon-from-ico=icon.ico \
    --include-data-files=config.json=config.json \
    --output-dir=build \
    main.py
```

### Comparison for a Sample PySide6 App

| Method | Build Time | Exe Size | Startup Time |
|--------|------------|----------|--------------|
| pyside6-deploy | 5-10 min | 15-30 MB | Fast |
| PyInstaller | 1-2 min | 40-80 MB | Moderate |
| cx_Freeze | 2-3 min | 35-70 MB | Moderate |
| Manual Nuitka | 5-15 min | 12-25 MB | Fastest |

---

## Best Practices

### 1. Development Workflow

```bash
# Development structure
project/
├── src/              # Source code
├── resources/        # Icons, QML, etc.
├── tests/           # Test files
├── deploy/          # Deployment configs
│   ├── pysidedeploy.spec
│   ├── windows/     # Platform-specific
│   ├── linux/
│   └── macos/
└── requirements.txt
```

### 2. CI/CD Integration

```yaml
# GitHub Actions example
name: Build Executables

on: [push, pull_request]

jobs:
  build:
    strategy:
      matrix:
        os: [windows-latest, ubuntu-latest, macos-latest]

    runs-on: ${{ matrix.os }}

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install PySide6 nuitka
        pip install -r requirements.txt

    - name: Build executable
      run: pyside6-deploy -c deploy/pysidedeploy.spec

    - name: Upload artifacts
      uses: actions/upload-artifact@v2
      with:
        name: ${{ matrix.os }}-executable
        path: |
          *.exe
          *.bin
          *.app
```

### 3. Version Management

```python
# version.py
__version__ = "1.0.0"

# main.py
from version import __version__

app = QApplication(sys.argv)
app.setApplicationVersion(__version__)
```

### 4. Testing Deployment

```python
# test_deployment.py
import subprocess
import sys
import os

def test_executable():
    """Test that executable runs without errors"""
    if sys.platform == "win32":
        exe = "myapp.exe"
    elif sys.platform == "darwin":
        exe = "myapp.app/Contents/MacOS/myapp"
    else:
        exe = "myapp.bin"

    result = subprocess.run([exe, "--version"], capture_output=True)
    assert result.returncode == 0
```

---

## Conclusion

`pyside6-deploy` provides a robust solution for deploying PySide6 applications across platforms. While it requires more build time than alternatives, the resulting executables are smaller, faster, and more professional.

### Key Takeaways

1. **Start early** - Test deployment from the beginning of development
2. **Use virtual environments** - Ensures clean, reproducible builds
3. **Optimize carefully** - Balance size vs functionality
4. **Test on target platforms** - Each OS has unique requirements
5. **Keep spec file in version control** - Ensures consistent builds

### Next Steps

- Experiment with the examples in this guide
- Create a simple test application and deploy it
- Customize the configuration for your specific needs
- Set up automated builds in your CI/CD pipeline

For more information, consult the [official Qt for Python deployment documentation](https://doc.qt.io/qtforpython-6/deployment/index.html).