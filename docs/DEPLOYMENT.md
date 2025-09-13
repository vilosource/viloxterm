# ViloxTerm Deployment Guide

This guide explains how to build and deploy ViloxTerm as a standalone executable for Windows, Linux, and macOS.

## Prerequisites

1. **Python 3.8+** with PySide6 installed
2. **pyside6-deploy** (included with PySide6 6.5+)
3. **Nuitka** (automatically installed by pyside6-deploy)
4. **Platform tools**:
   - Linux: `patchelf` (auto-installed)
   - Windows: Visual Studio Build Tools
   - macOS: Xcode Command Line Tools

## Quick Start

### 1. Generate Icons (First Time Only)
```bash
make deploy-icons
```

This creates application icons in various formats for all platforms.

### 2. Build Executable
```bash
make deploy
```

This builds a standalone executable using the configuration in `pysidedeploy.spec`.

### 3. Test Deployment
```bash
make deploy-test
```

Runs automated tests on the built executable.

## Build Options

### Standalone Build (Default)
Creates a folder with the executable and all dependencies:
```bash
make deploy
```

Output: `deployment/main.dist/` folder containing the executable and libraries.

### Single-File Build
Creates a single executable file (larger, slower to start):
```bash
make deploy-onefile
```

Output: Single `main.bin` (Linux), `main.exe` (Windows), or `main.app` (macOS).

### Clean Build
Remove all build artifacts and start fresh:
```bash
make deploy-clean
make deploy
```

## Configuration

The deployment is configured in `pysidedeploy.spec`. Key settings:

- **title**: Application name (ViloxTerm)
- **icon**: Path to application icon
- **modules**: Qt modules to include
- **mode**: `standalone` or `onefile`
- **extra_args**: Additional Nuitka arguments

### Customizing the Build

Edit `pysidedeploy.spec` to:
- Change included Qt modules
- Add/remove Python packages
- Modify Nuitka optimization settings
- Include additional data files

## Platform-Specific Notes

### Linux
- Executable: `main.bin`
- Tested on Ubuntu 22.04+
- Works on both X11 and Wayland
- Consider creating an AppImage for distribution

### Windows
- Executable: `main.exe`
- Console window is hidden by default
- May trigger antivirus warnings (false positive)
- Consider code signing for production

### macOS
- App bundle: `main.app`
- Requires notarization for distribution
- Test on both Intel and Apple Silicon

## Troubleshooting

### Build Fails
1. Check Python version (3.8+ required)
2. Ensure all dependencies installed: `pip install -r requirements.txt`
3. Run with verbose mode: `pyside6-deploy -v`
4. Check for missing system tools

### Executable Won't Run
1. Check file permissions (Linux/macOS): `chmod +x main.bin`
2. Verify all data files included
3. Test in standalone mode first (easier to debug)
4. Check terminal output for errors

### Missing Icons/Resources
1. Compile resources first: `make resources`
2. Verify paths in `pysidedeploy.spec`
3. Check `--include-data-dir` arguments

### Terminal Server Issues
The terminal server (Flask/SocketIO) requires special handling:
1. Ensure all Flask modules included
2. Terminal assets must be bundled
3. Port 5000 must be available

### Large File Size
To reduce size:
1. Exclude unused Qt modules in spec file
2. Use UPX compression (optional, may trigger antivirus)
3. Strip debug symbols
4. Remove test files from bundle

## Deployment Checklist

Before distributing:

- [ ] Test on fresh system without Python
- [ ] Verify all features work
- [ ] Check file size is reasonable
- [ ] Test on target platforms
- [ ] Sign executable (Windows/macOS)
- [ ] Create installer (optional)
- [ ] Document system requirements
- [ ] Prepare release notes

## Advanced Topics

### Continuous Integration
See `.github/workflows/deploy.yml` for automated builds (when created).

### Code Signing
- Windows: Use `signtool` with certificate
- macOS: Use `codesign` with Developer ID

### Creating Installers
- Windows: NSIS or WiX
- macOS: DMG with `create-dmg`
- Linux: AppImage or Snap

### Version Management
Version is set in:
1. `pysidedeploy.spec` (deployment metadata)
2. `main.py` (application version)
3. Git tags (release versions)

## Support

For deployment issues:
1. Check the [deployment plan](DEPLOYMENT_PLAN.md)
2. Review [PySide6 deployment docs](https://doc.qt.io/qtforpython-6/deployment/)
3. Open an issue on GitHub