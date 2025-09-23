# ViloxTerm Platform Purity Refactoring - WIP PLAN

## 🎯 Executive Summary

Transform ViloxTerm from a widget-aware application into a **pure widget platform/host** that provides services to widgets without any knowledge of specific widget implementations. This aligns with the architectural vision of ViloxTerm as a generic platform for widget-based applications.

## 🚨 Current Architectural Problems

### Critical Violations of Plugin Architecture
1. **Widget implementations embedded in core** (`viloapp/ui/terminal/`, `viloapp/ui/widgets/editor_app_widget.py`)
2. **Widget-specific commands in core** (`terminal_commands.py`, `edit_commands.py`)
3. **Widget-specific services in core** (`editor_service.py`, `terminal_service.py`)
4. **Hardcoded widget categories** (`WidgetCategory.EDITOR`, `WidgetCategory.TERMINAL`)
5. **Direct widget dependencies** in registry and commands
6. **Competing implementations** (terminal widgets in both core and `viloxterm` package)

### Critical: Massive Code Duplication
- **Core terminal implementation**: ~76,000 lines in `viloapp/ui/terminal/`
- **Plugin terminal implementation**: ~2,893 lines in `viloxterm/`
- **Core editor implementation**: ~47,000 lines in `editor_app_widget.py`
- **Plugin editor implementation**: ~2,443 lines in `viloedit/`
- **Total duplication**: ~126,000+ lines of competing functionality

### Impact
- **Violates separation of concerns** - Core knows about implementations
- **Prevents true plugin extensibility** - New widget types require core changes
- **Creates massive duplication** - Two implementations of same functionality
- **Blocks future server architecture** - Can't move widgets to separate processes

## 🎯 Success Metrics

### Primary Goals
1. **Zero Widget-Specific Code in Core** - No terminal/editor-specific code in `viloapp`
2. **Zero Duplication** - Single source of truth for each widget type
3. **Pure Service Architecture** - Core provides generic services, widgets consume them
4. **Dynamic Plugin Registration** - Widgets register themselves without core changes
5. **Capability-Based Interactions** - Commands use capabilities, not widget types
6. **Clean Package Boundaries** - Widget implementations only in plugin packages

### Measurable Outcomes
- ✅ **Zero duplication**: No competing widget implementations
- ✅ **Zero core widget code**: `find packages/viloapp/src/viloapp/ui/ -name "*terminal*" -o -name "*editor*"` returns nothing
- ✅ **Zero widget services in core**: No `terminal_service.py`, `editor_service.py` in core
- ✅ **Zero widget commands in core**: No `terminal_commands.py`, `edit_commands.py` in core
- ✅ **Plugin-only widgets**: All functionality through plugin packages
- ✅ **Clean boundaries**: Core startup succeeds with zero widgets loaded

## 📋 Implementation Phases

### Phase 1: Core Cleanup Assessment & Preparation ✅
**Goal**: Understand current state and design capability architecture
- **Duration**: 1-2 days
- **Risk**: Low
- **Status**: COMPLETE

### Phase 2: Immediate Deduplication
**Goal**: Eliminate ALL competing implementations immediately
- **Duration**: 2-3 days
- **Risk**: Medium (breaking changes, but necessary)
- **Dependencies**: Phase 1 complete
- **Strategy**: Remove core widgets entirely, use only plugins

### Phase 3: Capability System Integration
**Goal**: Implement capability-based command system
- **Duration**: 3-4 days
- **Risk**: Medium (new architecture patterns)
- **Dependencies**: Phase 2 complete

### Phase 4: Final Validation & Testing
**Goal**: Ensure platform works without widget-specific knowledge
- **Duration**: 1-2 days
- **Risk**: Low
- **Dependencies**: Phase 3 complete
- **Strategy**: Comprehensive testing and validation

## 🔧 Technical Strategy

### Core Architecture Principles
1. **Platform Services Only** - Core provides generic services (clipboard, file system, IPC)
2. **Plugin Self-Registration** - Widgets register capabilities and commands themselves
3. **Capability-Based Commands** - Commands target capabilities, not specific widgets
4. **Service Discovery** - Widgets discover and connect to platform services
5. **Event-Driven Communication** - Loose coupling through events/messages

### Key Design Patterns
- **Service Locator Pattern** - For platform service discovery
- **Capability Pattern** - For widget interaction abstraction
- **Plugin Registry Pattern** - For dynamic widget registration
- **Command Delegation Pattern** - For capability-based command routing
- **Observer Pattern** - For loose coupling between platform and widgets

### Future-Proofing Considerations
- **Server-Based Services** - Design services to be extractable to separate processes
- **Cross-Process Communication** - Prepare for widgets in separate processes
- **Hot Plugin Loading** - Support runtime widget loading/unloading
- **Capability Negotiation** - Allow widgets to discover what platform provides

## ⚠️ Risk Management

### High Risk Areas
1. **Immediate Functionality Loss** - Removing core widgets before plugins ready
2. **Widget ID Conflicts** - Plugin widgets may not load due to ID mismatches
3. **Service Dependencies** - Widgets currently depend on specific services

### Mitigation Strategies
1. **Fix Plugin IDs First** - Ensure plugins can load before removing core widgets
2. **Immediate Deduplication** - Remove competing implementations in single phase
3. **Comprehensive Testing** - Validate each phase before proceeding
4. **Preserve Functionality** - Ensure all features work through plugins

### Testing Strategy
- **Unit Tests** - For each capability and service
- **Integration Tests** - For widget registration and command delegation
- **End-to-End Tests** - For complete user workflows
- **Performance Tests** - Ensure no degradation
- **Plugin Compatibility Tests** - Verify external plugins still work

## 📊 Progress Tracking

### Completion Criteria by Phase
- **Phase 1**: ✅ Documentation of current violations and capability architecture design
- **Phase 2**: Zero duplication - all competing implementations eliminated
- **Phase 3**: Capability-based commands and plugin integration
- **Phase 4**: Complete platform functionality validation

### Validation Gates
Each phase must pass before proceeding:
1. **Zero Duplication Validation** - No competing implementations exist
2. **Functionality Preservation** - All features work through plugins
3. **Architecture Compliance** - Core has no widget-specific knowledge
4. **Performance Validation** - No significant performance degradation

## 🔮 Future Vision

After completion, ViloxTerm will be a **pure widget platform** capable of:
- **Hosting any widget type** without core modifications
- **Running widgets in separate processes** for isolation and stability
- **Providing external services** via network/IPC for distributed architecture
- **Supporting dynamic widget ecosystems** with hot-loading and dependency management
- **Enabling widget marketplaces** where users can discover and install widgets dynamically

This transformation sets the foundation for ViloxTerm to become a **universal application platform** rather than just a terminal/editor application.

---

**Status**: ✅ PHASE 1 COMPLETE - Ready for Implementation
**Last Updated**: 2025-01-23
**Next Phase**: Phase 2 - Immediate Deduplication
**Key Change**: Removed backward compatibility strategy - focus on immediate clean architecture