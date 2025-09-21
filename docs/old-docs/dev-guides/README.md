# Developer Guides

This directory contains comprehensive developer guides for implementing and extending ViloxTerm functionality. These guides provide step-by-step instructions, best practices, and real-world examples based on lessons learned during development.

## Purpose

Developer guides bridge the gap between high-level architecture documentation and code implementation. They provide:
- **Practical tutorials** for common development tasks
- **Best practices** discovered through implementation
- **Common pitfalls** and how to avoid them
- **Real examples** from the codebase
- **Troubleshooting tips** for typical issues

## Available Guides

### Core Development

#### [AppWidget Development Guide](./appwidget-development-guide.md)
A comprehensive guide to creating new AppWidgets - the fundamental content components in ViloxTerm's architecture. This guide covers:
- Complete implementation walkthrough
- Theme system integration
- Widget registry and factory patterns
- State persistence and signal communication
- Common pitfalls with solutions
- Full example implementation (ShortcutConfigAppWidget)

*Essential reading for anyone implementing new UI components or content widgets.*

## Guide Categories

### 🏗️ Architecture & Patterns
- AppWidget system and base classes
- Command pattern implementation
- Service layer integration

### 🎨 UI & Theming
- VSCode theme system usage
- Dynamic styling without hardcoding
- Widget state management

### 🔧 Integration
- Factory registration patterns
- Command system integration
- Signal/slot communication

## Contributing

When adding new guides:
1. Use clear, descriptive filenames (kebab-case)
2. Include a comprehensive table of contents
3. Provide working code examples
4. Document common mistakes and solutions
5. Reference related documentation
6. Update this index with a description

## Related Documentation

- **[Architecture Docs](../architecture/)** - System design and architecture
- **[Testing Guides](../testing/)** - Testing strategies and patterns
- **[Project Docs](../project/)** - Project specifications and plans
- **[Feature Designs](../features/)** - Feature specifications