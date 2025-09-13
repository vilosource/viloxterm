# PySide6-Deploy Configuration for ViloxTerm
# This file configures how pyside6-deploy builds the standalone executable

[app]
# Application metadata
title = "ViloxTerm"
project_dir = "."
input_file = "main.py"
exec_directory = "."
icon = "deploy/icons/viloxterm.ico"  # Windows icon, will be adapted per platform

[python]
# Python configuration
python_path = ".direnv/python-3.12.3/bin/python"
packages = "Nuitka==2.1.0"

[qt]
# Qt modules to include (only what we actually use)
modules = [
    "Core",
    "Widgets",
    "WebEngineWidgets",  # For terminal widget
    "Network",           # For terminal server
    "Svg"               # For SVG icons
]

# Qt plugins to include
plugins = [
    "platforms",      # Platform integration
    "styles",        # Qt styles
    "imageformats"   # Image format support
]

# Exclude unused QML plugins to reduce size
excluded_qml_plugins = [
    "QtQuick3D",
    "QtCharts",
    "QtTest",
    "QtSensors",
    "QtMultimedia",
    "QtBluetooth",
    "QtNfc",
    "QtPositioning"
]

[nuitka]
# Deployment mode
# - standalone: Creates a folder with executable and libraries (easier to debug)
# - onefile: Single executable file (better for distribution)
mode = "standalone"

# Nuitka compiler options
extra_args = """
--enable-plugin=pyside6
--include-module=flask
--include-module=flask_socketio
--include-module=socketio
--include-module=engineio
--include-module=engineio.async_drivers.threading
--include-module=simple_websocket
--include-module=core.environment_detector
--include-module=resources.resources_rc
--include-data-files=resources/icons/**/*.svg=resources/icons/
--include-data-dir=ui/terminal/assets=ui/terminal/assets
--include-data-files=deploy/icons/*.png=deploy/icons/
--include-data-files=deploy/icons/*.ico=deploy/icons/
--windows-disable-console
--assume-yes-for-downloads
--remove-output
--quiet
"""

[deployment]
# Target platforms for deployment
platforms = ["Windows", "Linux", "Darwin"]

# Platform-specific settings can be added here
[deployment.windows]
# Windows-specific options
console = false
uac_admin = false
version = "1.0.0.0"
company_name = "ViloxTerm"
product_name = "ViloxTerm Terminal"
file_description = "Modern Terminal Emulator with VSCode-style UI"

[deployment.linux]
# Linux-specific options
desktop_file = "deploy/platforms/linux/viloxterm.desktop"
icon = "deploy/icons/viloxterm.png"

[deployment.macos]
# macOS-specific options
bundle_identifier = "com.viloxterm.app"
icon = "deploy/icons/viloxterm.icns"  # Will need to generate this
info_plist = "deploy/platforms/macos/Info.plist"