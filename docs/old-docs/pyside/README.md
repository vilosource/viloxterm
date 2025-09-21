# PySide6/Qt6 Development Documentation

This directory contains practical guides and documentation for developing GUI applications with PySide6/Qt6. These documents are based on real-world implementation experience and cover common challenges developers face when building modern desktop applications.

## Available Guides

### 📖 [Custom Frameless Windows](CustomFramelessWindows.md)
**Complete guide for implementing frameless windows with cross-platform support**

Learn how to create modern, custom-styled windows that work reliably across Windows, macOS, and Linux (including Wayland). This comprehensive guide covers:

- **Platform considerations** - Understanding Wayland restrictions and solutions
- **Complete implementation** - Full working code for frameless windows with custom title bars
- **Edge detection and resizing** - Implementing resize borders with visual feedback
- **Window controls** - Custom minimize, maximize, and close buttons
- **Menu bar integration** - Handling native menus in frameless mode
- **Testing strategies** - Automated testing patterns and common test cases
- **Common pitfalls** - Quick reference table for debugging issues
- **Best practices** - Guidelines based on production experience

*Perfect for: Developers wanting to maximize screen real estate, create branded experiences, or implement modern UI patterns like Chrome-style tabs.*

---

### 📦 [Building Executables with Docker and AppImage](BuildingExecutables.md)
**Production-ready build pipeline using Docker containers and AppImage packaging**

Learn how to create reproducible builds for PySide6 applications using Docker containers and package them as AppImages for universal Linux distribution. This guide addresses real-world challenges like environment corruption and dependency conflicts:

- **Docker build environment** - Isolated, reproducible builds that work every time
- **pyside6-deploy integration** - Leveraging the official tool within containers
- **AppImage creation** - Single portable file that runs on any Linux distribution
- **Build automation** - Complete scripts for setup, build, and packaging
- **Troubleshooting guide** - Solutions to environment corruption and build failures
- **CI/CD integration** - GitHub Actions and GitLab CI examples
- **Best practices** - Resource management, caching, and security
- **Quick reference** - Get started in minutes with proven patterns

*Perfect for: Teams needing reproducible builds, developers tired of "works on my machine" issues, anyone distributing Linux applications, or projects requiring consistent CI/CD pipelines.*

---

## Guide Structure

Each document in this collection follows a consistent structure:

1. **Overview** - What the guide covers and why it's important
2. **Platform Considerations** - OS-specific behavior and limitations
3. **Complete Implementation** - Full working code examples
4. **Edge Cases** - Real-world problems and their solutions
5. **Testing** - How to test the implementation
6. **Best Practices** - Recommendations from experience
7. **Common Pitfalls** - Things to watch out for

## Contributing

When adding new documentation:

1. **Be practical** - Base guides on actual implementation experience
2. **Be complete** - Include full working examples, not just snippets
3. **Be generic** - Make guides reusable for any PySide6 project
4. **Include tests** - Show how to test the implementation
5. **Document pitfalls** - Share what went wrong and how to fix it

## Prerequisites

These guides assume:
- PySide6 6.5+ or Qt6 equivalent
- Python 3.8+
- Basic familiarity with Qt concepts (signals/slots, widgets, layouts)

## Platform Testing

Code in these guides has been tested on:
- **Windows 11** - Native
- **macOS** - 12+ (Monterey and later)
- **Linux** - Ubuntu 22.04+ with both X11 and Wayland

## Quick Tips

### Environment Setup
```bash
# Install PySide6
pip install PySide6

# For development
pip install pytest pytest-qt  # Testing
pip install black ruff mypy   # Code quality
```

### Testing on Wayland
```bash
# Force Wayland backend
export QT_QPA_PLATFORM=wayland

# Force X11 backend (for comparison)
export QT_QPA_PLATFORM=xcb
```

### Debug Mode
```python
# Enable Qt debug output
import os
os.environ['QT_LOGGING_RULES'] = '*.debug=true'
```

## Resources

### Official Documentation
- [PySide6 Documentation](https://doc.qt.io/qtforpython-6/)
- [Qt6 Documentation](https://doc.qt.io/qt-6/)
- [Qt Widget Gallery](https://doc.qt.io/qt-6/gallery.html)

### Community
- [Qt Forum](https://forum.qt.io/)
- [PySide6 Examples](https://github.com/pyside/pyside6-examples)
- [Qt Wiki](https://wiki.qt.io/)

### Tools
- [Qt Designer](https://doc.qt.io/qt-6/qtdesigner-manual.html) - Visual UI design
- [Qt Creator](https://www.qt.io/product/development-tools) - IDE with Qt integration
- [Pytest-qt](https://pytest-qt.readthedocs.io/) - Testing Qt applications

---

## License

These documentation files are provided as learning resources. Code examples are free to use and modify for your own projects.

## Feedback

Found an issue or have a suggestion? Please contribute improvements to help future developers!