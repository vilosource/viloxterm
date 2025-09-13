# Building PySide6 Applications with Docker and AppImage

A comprehensive guide to building reproducible PySide6 executables using Docker containers and packaging them as AppImages for Linux distribution.

## Table of Contents
- [Overview](#overview)
- [Why Docker for Builds?](#why-docker-for-builds)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Docker Build Environment](#docker-build-environment)
- [Building Executables](#building-executables)
- [Creating AppImages](#creating-appimages)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Overview

This guide covers a production-ready build pipeline for PySide6 applications that:
- Uses **Docker** for reproducible builds across different developer machines
- Leverages **pyside6-deploy** for creating optimized executables
- Packages as **AppImage** for universal Linux distribution
- Avoids common pitfalls like environment corruption and dependency conflicts

### Build Pipeline Flow
```
Source Code → Docker Container → pyside6-deploy → Standalone Build → AppImage
```

### Why This Approach?

| Challenge | Solution |
|-----------|----------|
| **Environment Corruption** | Docker provides isolated, reproducible builds |
| **Dependency Conflicts** | Container includes exact versions needed |
| **Cross-distribution Linux** | AppImage runs on any Linux distro |
| **Build Reproducibility** | Same container = same output every time |
| **CI/CD Integration** | Docker works seamlessly in pipelines |

---

## Why Docker for Builds?

### The Problem
During development, you might encounter:
- `ModuleNotFoundError: No module named 'pip._internal.operations.build'`
- `ModuleNotFoundError: No module named 'nuitka.build'`
- Conflicting Python package versions
- System library mismatches
- "Works on my machine" syndrome

### The Solution
Docker containers provide:
- **Isolation**: Build environment separate from development
- **Reproducibility**: Same build every time, on any machine
- **Version Control**: Dockerfile defines exact environment
- **Team Collaboration**: Everyone uses the same build container
- **CI/CD Ready**: Deploy the same container in pipelines

---

## Prerequisites

### Required Software
```bash
# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose (optional but recommended)
sudo apt-get install docker-compose-plugin

# Git (for version control)
sudo apt-get install git
```

### Verify Installation
```bash
docker --version
docker compose version  # or docker-compose --version
```

---

## Project Structure

### Recommended Layout
```
my_pyside_app/
├── main.py                    # Application entry point
├── ui/                        # UI components
│   ├── main_window.py
│   └── widgets/
├── resources/                 # Icons, styles, QML
│   ├── icons/
│   └── resources.qrc
├── builder/                   # Build infrastructure
│   ├── Dockerfile            # Build environment definition
│   ├── entrypoint.sh         # Container build script
│   ├── build.sh              # Host build management script
│   ├── create-appimage.sh    # AppImage creation script
│   ├── AppRun                # AppImage launcher
│   └── MyApp.desktop         # Desktop entry file
├── pysidedeploy.spec         # pyside6-deploy configuration
└── requirements.txt          # Python dependencies
```

---

## Docker Build Environment

### 1. Create the Dockerfile

```dockerfile
# builder/Dockerfile
FROM ubuntu:22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Python and build tools
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-pip \
    build-essential \
    cmake \
    ninja-build \
    # Qt dependencies
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xkb1 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    # Additional tools
    patchelf \
    ccache \
    wget \
    file \
    zlib1g-dev \
    # AppImage tools
    fuse \
    libfuse2 \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.12 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1

# Create virtual environment
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Install Python packages
RUN pip install --upgrade pip setuptools wheel && \
    pip install \
        PySide6 \
        pyside6-addons \
        pyside6-essentials \
        Nuitka==2.7.11 \
        ordered-set \
        zstandard

# Download AppImageTool
RUN wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage \
    -O /usr/local/bin/appimagetool && \
    chmod +x /usr/local/bin/appimagetool

# Setup ccache for faster rebuilds
ENV CCACHE_DIR=/ccache
ENV PATH="/usr/lib/ccache:$PATH"

# Set working directory
WORKDIR /workspace

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

### 2. Create the Build Entrypoint

```bash
#!/bin/bash
# builder/entrypoint.sh
set -e

echo "========================================="
echo "PySide6 Docker Build Environment"
echo "Python: $(python3 --version)"
echo "PySide6: $(python3 -c 'import PySide6; print(PySide6.__version__)')"
echo "Nuitka: $(python3 -m nuitka --version | head -1)"
echo "========================================="

cd /workspace

case "$1" in
    build)
        echo "Starting build process..."

        # Copy source to build directory (preserve mounted volume)
        cp -r /workspace/* /build/ 2>/dev/null || true
        cd /build

        # Compile Qt resources if present
        if [ -f "resources/resources.qrc" ]; then
            echo "Compiling Qt resources..."
            pyside6-rcc resources/resources.qrc -o resources/resources_rc.py
        fi

        # Build with pyside6-deploy
        echo "Building with pyside6-deploy..."
        if [ "$2" = "standalone" ]; then
            # Ensure spec file has standalone mode
            sed -i 's/mode = "onefile"/mode = "standalone"/' pysidedeploy.spec 2>/dev/null || true
        fi

        # Run pyside6-deploy
        pyside6-deploy -v || {
            echo "pyside6-deploy failed, using direct Nuitka..."
            python3 -m nuitka \
                --standalone \
                --enable-plugin=pyside6 \
                --output-dir=/output \
                --assume-yes-for-downloads \
                main.py
        }

        # Copy output
        if [ -d "MyApp.dist" ]; then
            cp -r MyApp.dist /output/
        elif [ -d "main.dist" ]; then
            mv main.dist /output/MyApp.dist
        fi

        # Make executable
        chmod +x /output/MyApp.dist/*.bin 2>/dev/null || true

        echo "Build complete!"
        ;;

    appimage)
        echo "Creating AppImage..."

        # First build standalone if not exists
        if [ ! -d "/output/MyApp.dist" ]; then
            $0 build standalone
        fi

        # Create AppDir structure
        mkdir -p /output/MyApp.AppDir/usr/bin
        mkdir -p /output/MyApp.AppDir/usr/lib
        mkdir -p /output/MyApp.AppDir/usr/share/applications
        mkdir -p /output/MyApp.AppDir/usr/share/icons/hicolor/256x256/apps

        # Copy distribution
        cp -r /output/MyApp.dist/* /output/MyApp.AppDir/usr/lib/

        # Create wrapper script
        cat > /output/MyApp.AppDir/usr/bin/MyApp << 'EOF'
#!/bin/bash
BIN_DIR="$(dirname "$(readlink -f "$0")")"
exec "$BIN_DIR/../lib/main.bin" "$@"
EOF
        chmod +x /output/MyApp.AppDir/usr/bin/MyApp

        # Create AppRun
        cat > /output/MyApp.AppDir/AppRun << 'EOF'
#!/bin/bash
APPDIR="$(dirname "$(readlink -f "$0")")"
exec "$APPDIR/usr/bin/MyApp" "$@"
EOF
        chmod +x /output/MyApp.AppDir/AppRun

        # Copy desktop file and icon
        cp /workspace/builder/MyApp.desktop /output/MyApp.AppDir/
        cp /workspace/builder/MyApp.desktop /output/MyApp.AppDir/usr/share/applications/

        if [ -f "/workspace/resources/icon.png" ]; then
            cp /workspace/resources/icon.png /output/MyApp.AppDir/myapp.png
            cp /workspace/resources/icon.png /output/MyApp.AppDir/usr/share/icons/hicolor/256x256/apps/
        fi

        # Build AppImage
        cd /output
        ARCH=x86_64 appimagetool --appimage-extract-and-run MyApp.AppDir MyApp-x86_64.AppImage

        if [ -f "MyApp-x86_64.AppImage" ]; then
            chmod +x MyApp-x86_64.AppImage
            echo "AppImage created successfully!"
            ls -lh MyApp-x86_64.AppImage
        fi
        ;;

    shell)
        echo "Starting interactive shell..."
        exec /bin/bash
        ;;

    clean)
        echo "Cleaning build artifacts..."
        rm -rf /build/* /output/*
        ;;

    *)
        echo "Usage: $0 {build|appimage|shell|clean}"
        exit 1
        ;;
esac
```

### 3. Create Host Build Script

```bash
#!/bin/bash
# builder/build.sh
set -e

# Configuration
IMAGE_NAME="pyside-builder"
CONTAINER_NAME="pyside-build"
PROJECT_ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
OUTPUT_DIR="${PROJECT_ROOT}/build-output"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

print_msg() {
    echo -e "${GREEN}[Builder]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker not installed"
        exit 1
    fi
}

# Build Docker image
build_image() {
    print_msg "Building Docker image..."
    docker build -t "${IMAGE_NAME}" -f "${PROJECT_ROOT}/builder/Dockerfile" "${PROJECT_ROOT}/builder"
}

# Run build
run_build() {
    print_msg "Running build in Docker..."
    mkdir -p "${OUTPUT_DIR}"

    docker run --rm \
        -v "${PROJECT_ROOT}:/workspace:ro" \
        -v "${OUTPUT_DIR}:/output" \
        -v "pyside-ccache:/ccache" \
        "${IMAGE_NAME}" \
        build "$1"
}

# Build AppImage
build_appimage() {
    print_msg "Building AppImage..."
    mkdir -p "${OUTPUT_DIR}"

    docker run --rm \
        -v "${PROJECT_ROOT}:/workspace:ro" \
        -v "${OUTPUT_DIR}:/output" \
        -v "pyside-ccache:/ccache" \
        "${IMAGE_NAME}" \
        appimage
}

# Main
check_docker

case "$1" in
    setup)
        build_image
        ;;
    build)
        run_build standalone
        ;;
    appimage)
        build_appimage
        ;;
    clean)
        rm -rf "${OUTPUT_DIR}"
        docker volume rm pyside-ccache 2>/dev/null || true
        ;;
    *)
        echo "Usage: $0 {setup|build|appimage|clean}"
        exit 1
        ;;
esac
```

---

## Building Executables

### 1. Configure pyside6-deploy

Create `pysidedeploy.spec` in your project root:

```toml
# pysidedeploy.spec
[app]
title = "My PySide App"
project_dir = "."
input_file = "main.py"
exec_directory = "."
icon = "resources/icon.ico"

[python]
packages = "Nuitka==2.7.11"

[qt]
modules = ["Core", "Widgets", "Gui", "Network"]
plugins = ["platforms", "styles", "imageformats"]
excluded_qml_plugins = "QtQuick3D,QtCharts,QtWebEngine,QtTest,QtSensors"

[nuitka]
mode = "standalone"  # Use standalone for AppImage conversion

# Include your application's specific modules and data
extra_args = """
--quiet
--noinclude-qt-translations
--enable-plugin=pyside6
--include-data-dir=resources=resources
--assume-yes-for-downloads
"""

[deployment]
platforms = ["Linux"]
```

### 2. Build Process

```bash
# One-time setup
cd your_project
mkdir builder
# Copy Dockerfile, entrypoint.sh, build.sh from examples above

# Build Docker image (first time only)
./builder/build.sh setup

# Build standalone executable
./builder/build.sh build

# Create AppImage
./builder/build.sh appimage

# Output will be in build-output/MyApp-x86_64.AppImage
```

---

## Creating AppImages

### Desktop Entry File

```ini
# builder/MyApp.desktop
[Desktop Entry]
Name=My PySide App
Exec=MyApp
Icon=myapp
Type=Application
Categories=Development;Utility;
Comment=Description of your application
Terminal=false
StartupNotify=true
MimeType=text/plain;
Keywords=keyword1;keyword2;
```

### AppImage Benefits

- **Universal**: Runs on any Linux distribution
- **Portable**: Single file, no installation needed
- **Self-contained**: All dependencies included
- **Desktop Integration**: Works with app launchers
- **Update System**: Can integrate with AppImageUpdate

### Testing AppImage

```bash
# Make executable
chmod +x MyApp-x86_64.AppImage

# Run directly
./MyApp-x86_64.AppImage

# With arguments
./MyApp-x86_64.AppImage --help

# Desktop integration (optional)
./MyApp-x86_64.AppImage --install-desktop-file
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/build.yml
name: Build AppImage

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Build Docker Image
      run: |
        cd builder
        docker build -t pyside-builder .

    - name: Build AppImage
      run: |
        docker run --rm \
          -v $PWD:/workspace:ro \
          -v $PWD/output:/output \
          pyside-builder appimage

    - name: Upload AppImage
      uses: actions/upload-artifact@v3
      with:
        name: AppImage
        path: output/*.AppImage
```

### GitLab CI Example

```yaml
# .gitlab-ci.yml
stages:
  - build

build-appimage:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t pyside-builder builder/
    - docker run --rm -v $PWD:/workspace:ro -v $PWD/output:/output pyside-builder appimage
  artifacts:
    paths:
      - output/*.AppImage
    expire_in: 1 week
```

---

## Troubleshooting

### Common Issues and Solutions

#### Environment Corruption
**Problem**: `ModuleNotFoundError` for pip or nuitka modules

**Solution**: Always use Docker for builds
```bash
# Never run pyside6-deploy directly on host
# Always use:
./builder/build.sh build
```

#### Missing Libraries in AppImage
**Problem**: Application fails to start with library errors

**Solution**: Check ldd output and include missing libraries
```bash
# Inside container
ldd /output/MyApp.dist/main.bin | grep "not found"

# Add to Dockerfile if system library missing
RUN apt-get install -y libmissing-library
```

#### Resources Not Found
**Problem**: Icons, QML, or data files missing in build

**Solution**: Include in pysidedeploy.spec
```toml
[nuitka]
extra_args = """
--include-data-dir=resources=resources
--include-data-files=config.json=config.json
"""
```

#### Large AppImage Size
**Problem**: AppImage over 200MB

**Solution**: Exclude unnecessary Qt modules
```toml
[qt]
modules = ["Core", "Widgets"]  # Only what you need
excluded_qml_plugins = "QtQuick3D,QtCharts,QtWebEngine,QtTest"
```

#### Build Failures
**Problem**: pyside6-deploy fails in container

**Solution**: Use fallback to direct Nuitka (already in entrypoint.sh)
```bash
python3 -m nuitka \
    --standalone \
    --enable-plugin=pyside6 \
    --output-dir=/output \
    main.py
```

---

## Best Practices

### 1. Version Control
- Keep `builder/` directory in git
- Track `pysidedeploy.spec`
- Use `.gitignore` for build outputs:
```gitignore
build-output/
*.AppImage
*.dist/
```

### 2. Development Workflow
```bash
# Development (local Python)
python main.py

# Testing build
./builder/build.sh build
./build-output/MyApp.dist/main.bin

# Production release
./builder/build.sh appimage
```

### 3. Resource Management
```python
# Proper resource loading
import sys
import os

def get_resource_path(relative_path):
    """Get absolute path to resource, works in dev and deployed"""
    if getattr(sys, 'frozen', False):
        # Running in Nuitka bundle
        base_path = os.path.dirname(sys.executable)
    else:
        # Running in normal Python
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Usage
icon_path = get_resource_path("resources/icon.png")
```

### 4. Docker Image Optimization
```dockerfile
# Use multi-stage builds for smaller images
FROM ubuntu:22.04 as builder
# ... build steps ...

FROM ubuntu:22.04
COPY --from=builder /output /output
```

### 5. Caching for Faster Builds
- Use ccache volume (included in examples)
- Cache pip packages:
```yaml
# docker-compose.yml
services:
  builder:
    volumes:
      - pip-cache:/root/.cache/pip
      - ccache:/ccache
volumes:
  pip-cache:
  ccache:
```

### 6. Testing Builds
```python
# test_build.py
import subprocess
import os

def test_appimage_runs():
    """Test that AppImage executes"""
    appimage = "build-output/MyApp-x86_64.AppImage"
    assert os.path.exists(appimage)

    result = subprocess.run(
        [appimage, "--version"],
        capture_output=True,
        timeout=10
    )
    assert result.returncode == 0
```

### 7. Security Considerations
- Regularly update base Docker image
- Scan for vulnerabilities:
```bash
docker scan pyside-builder
```
- Sign AppImages for distribution:
```bash
# Using appimagetool with signing
appimagetool --sign MyApp.AppDir MyApp-x86_64.AppImage
```

---

## Conclusion

Using Docker for PySide6 builds ensures:
- **Reproducibility**: Same build on any machine
- **Isolation**: No environment corruption
- **Portability**: AppImage runs everywhere
- **Team Collaboration**: Shared build environment
- **CI/CD Ready**: Easy automation

This approach eliminates the "works on my machine" problem and provides a professional distribution format for Linux applications.

### Quick Reference

```bash
# Complete build workflow
git clone your-repo
cd your-repo
./builder/build.sh setup    # Build Docker image (once)
./builder/build.sh appimage  # Create AppImage
./build-output/MyApp-x86_64.AppImage  # Run it!
```

### Next Steps

1. Adapt the Docker and build scripts to your project
2. Test the AppImage on different Linux distributions
3. Set up CI/CD pipelines for automated builds
4. Consider code signing for production releases
5. Implement auto-update functionality with AppImageUpdate

For more details on specific components:
- [PySide6 Deployment](https://doc.qt.io/qtforpython-6/deployment/index.html)
- [Nuitka Documentation](https://nuitka.net/doc/user-manual.html)
- [AppImage Documentation](https://appimage.org/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)