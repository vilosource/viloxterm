# Week 1-4 Plugin Refactoring Fixes Plan

## Executive Summary

This document details the critical components that were missed during the Week 1-4 plugin refactoring implementation and provides a step-by-step plan to complete them. The audit revealed that while core functionality was implemented (~60% complete), critical SDK components, security infrastructure, and developer tools were omitted.

## Gap Analysis

### Week 1 Gaps: Plugin SDK Foundation
- ❌ **IWidget Interface**: Wrong method signatures (doesn't match specification)
- ❌ **IMetadata Interface**: Completely missing
- ❌ **Testing Utilities**: mock_host.py, fixtures.py not created
- ❌ **SDK Utilities**: decorators.py, validators.py not implemented

### Week 2 Gaps: Plugin Host Infrastructure
- ❌ **Security System**: No permission management, sandboxing, or resource limits
- ❌ **Development Tools**: No CLI tool, plugin templates, or hot reload
- ❌ **Testing Framework**: No comprehensive mock services or plugin test harness

### Week 3-4 Gaps: Plugin Features
- ⚠️ **Editor Plugin**: Missing autocomplete, find/replace, multi-cursor
- ⚠️ **Migration Tools**: Documentation exists but no actual implementation
- ❌ **Performance Monitoring**: No metrics collection or optimization

## Implementation Plan

## Phase 1: SDK Foundation Fixes (3 days)

### Day 1: Fix Core Interfaces

#### Task 1.1: Fix IWidget Interface
**Location**: `packages/viloapp-sdk/src/viloapp_sdk/interfaces.py`
- [ ] Update IWidget with correct method signatures:
  ```python
  def get_widget_id() -> str
  def get_title() -> str
  def get_icon() -> Optional[str]
  def create_instance(instance_id: str) -> QWidget
  def destroy_instance(instance_id: str) -> None
  def handle_command(command: str, args: Dict[str, Any]) -> Any
  def get_state() -> Dict[str, Any]
  def restore_state(state: Dict[str, Any]) -> None
  ```
- [ ] Update all existing widget implementations (terminal, editor)
- [ ] Update widget factory to use new interface
- [ ] Write migration script for existing plugins

#### Task 1.2: Add IMetadata Interface
**Location**: `packages/viloapp-sdk/src/viloapp_sdk/interfaces.py`
- [ ] Create IMetadata interface:
  ```python
  class IMetadata(ABC):
      def get_id() -> str
      def get_name() -> str
      def get_version() -> str
      def get_description() -> str
      def get_author() -> Dict[str, str]
      def get_license() -> str
      def get_dependencies() -> Dict[str, str]
      def get_keywords() -> List[str]
  ```
- [ ] Implement in PluginMetadata class
- [ ] Add validation methods

### Day 2: SDK Testing Utilities

#### Task 2.1: Create mock_host.py
**Location**: `packages/viloapp-sdk/src/viloapp_sdk/testing/mock_host.py`
- [ ] Implement MockPluginHost class
- [ ] Add mock service registry
- [ ] Implement mock event bus
- [ ] Add state management mocks
- [ ] Create helper methods for common test scenarios

#### Task 2.2: Create fixtures.py
**Location**: `packages/viloapp-sdk/src/viloapp_sdk/testing/fixtures.py`
- [ ] Create pytest fixtures for plugin testing:
  - [ ] mock_plugin_context fixture
  - [ ] mock_services fixture
  - [ ] mock_event_bus fixture
  - [ ] sample_plugin fixture
  - [ ] temp_plugin_dir fixture
- [ ] Add fixture documentation

### Day 3: SDK Utilities

#### Task 3.1: Create decorators.py
**Location**: `packages/viloapp-sdk/src/viloapp_sdk/utils/decorators.py`
- [ ] Implement @plugin decorator for class registration
- [ ] Implement @command decorator for command registration
- [ ] Implement @widget decorator for widget registration
- [ ] Implement @service decorator for service registration
- [ ] Add @activation_event decorator
- [ ] Add @contribution decorator

#### Task 3.2: Create validators.py
**Location**: `packages/viloapp-sdk/src/viloapp_sdk/utils/validators.py`
- [ ] Implement manifest validator
- [ ] Add version compatibility checker
- [ ] Create dependency validator
- [ ] Add permission validator
- [ ] Implement configuration schema validator

#### Task 3.3: Update SDK Tests
- [ ] Write tests for new interfaces
- [ ] Write tests for utilities
- [ ] Update existing tests for interface changes

## Phase 2: Security & Permissions (2 days)

### Day 4: Permission System

#### Task 4.1: Create Permission Framework
**Location**: `core/plugin_system/security/`
- [ ] Create permissions.py with:
  ```python
  class Permission:
      category: str  # filesystem, network, system, ui
      scope: str     # read, write, execute
      resource: str  # specific resource identifier
  ```
- [ ] Implement PermissionManager class
- [ ] Add permission checking to service proxy
- [ ] Create default permission sets

#### Task 4.2: Implement Permission Enforcement
- [ ] Update ServiceProxy to check permissions
- [ ] Add permission validation to plugin loader
- [ ] Create permission request dialog UI
- [ ] Update plugin manifests with required permissions

### Day 5: Resource Management

#### Task 5.1: Create Resource Limiter
**Location**: `core/plugin_system/security/resources.py`
- [ ] Implement ResourceMonitor class
- [ ] Add memory usage tracking
- [ ] Add CPU usage monitoring
- [ ] Create resource limit enforcement
- [ ] Add graceful degradation on limit exceeded

#### Task 5.2: Basic Sandboxing
- [ ] Create PluginSandbox class
- [ ] Implement basic isolation mechanisms
- [ ] Add crash recovery system
- [ ] Create plugin restart policies
- [ ] Add error logging and telemetry

## Phase 3: Developer Tools (3 days)

### Day 6: Plugin CLI Tool

#### Task 6.1: Create CLI Framework
**Location**: `packages/viloapp-cli/`
- [ ] Set up new package with click
- [ ] Create main CLI entry point
- [ ] Add command structure
- [ ] Set up configuration management

#### Task 6.2: Implement Core Commands
- [ ] `viloapp create-plugin <name>` - Create new plugin from template
- [ ] `viloapp dev --plugin <path>` - Run plugin in development mode
- [ ] `viloapp test <plugin>` - Run plugin tests
- [ ] `viloapp package <plugin>` - Package plugin for distribution
- [ ] `viloapp install <plugin>` - Install a plugin
- [ ] `viloapp list` - List installed plugins

### Day 7: Plugin Templates & Hot Reload

#### Task 7.1: Create Plugin Templates
**Location**: `packages/viloapp-cli/templates/`
- [ ] Create basic plugin template
- [ ] Create widget plugin template
- [ ] Create service plugin template
- [ ] Create command plugin template
- [ ] Add template customization options

#### Task 7.2: Implement Hot Reload
**Location**: `core/plugin_system/development/`
- [ ] Create FileWatcher class
- [ ] Implement plugin reload mechanism
- [ ] Add state preservation during reload
- [ ] Create reload event notifications
- [ ] Add development mode flag

### Day 8: Development Testing Framework

#### Task 8.1: Create Plugin Test Harness
**Location**: `packages/viloapp-sdk/src/viloapp_sdk/testing/`
- [ ] Create PluginTestCase base class
- [ ] Add integration test utilities
- [ ] Create command testing helpers
- [ ] Add widget testing utilities
- [ ] Implement event testing helpers

#### Task 8.2: Mock Services
- [ ] Create comprehensive mock services:
  - [ ] MockThemeService
  - [ ] MockWorkspaceService
  - [ ] MockConfigurationService
  - [ ] MockStateService
  - [ ] MockCommandService
- [ ] Add service behavior customization

## Phase 4: Plugin Feature Completion (2 days)

### Day 9: Editor Plugin Features

#### Task 9.1: Implement Find/Replace
**Location**: `packages/viloedit/src/viloedit/features/`
- [ ] Create find_replace.py module
- [ ] Implement search functionality
- [ ] Add replace functionality
- [ ] Create UI components
- [ ] Add keyboard shortcuts
- [ ] Write tests

#### Task 9.2: Implement Basic Autocomplete
- [ ] Create autocomplete.py module
- [ ] Add language-specific completion providers
- [ ] Implement completion popup UI
- [ ] Add keyboard navigation
- [ ] Create completion caching
- [ ] Write tests

### Day 10: Editor Advanced Features

#### Task 10.1: Implement Multi-Cursor
**Location**: `packages/viloedit/src/viloedit/features/`
- [ ] Create multi_cursor.py module
- [ ] Implement cursor management
- [ ] Add multi-selection support
- [ ] Create keyboard shortcuts
- [ ] Add visual indicators
- [ ] Write tests

#### Task 10.2: Migration Tools
**Location**: `scripts/migration/`
- [ ] Create settings migrator
- [ ] Implement state migration
- [ ] Add plugin configuration migration
- [ ] Create backward compatibility layer
- [ ] Write migration tests

## Phase 5: Integration & Testing (2 days)

### Day 11: Integration

#### Task 11.1: Update All Plugins
- [ ] Update terminal plugin for new interfaces
- [ ] Update editor plugin for new interfaces
- [ ] Update core plugins
- [ ] Fix any breaking changes
- [ ] Update plugin manifests

#### Task 11.2: Update Documentation
- [ ] Update plugin development guide
- [ ] Create security documentation
- [ ] Document CLI usage
- [ ] Add migration guide
- [ ] Create troubleshooting guide

### Day 12: Comprehensive Testing & Audit

#### Task 12.1: Unit Testing
- [ ] Run all SDK unit tests
- [ ] Run plugin system tests
- [ ] Run individual plugin tests
- [ ] Verify test coverage > 80%
- [ ] Fix any failing tests

#### Task 12.2: Integration Testing
- [ ] Test plugin loading with new interfaces
- [ ] Test permission system
- [ ] Test resource limits
- [ ] Test CLI tool functionality
- [ ] Test hot reload
- [ ] Test migration tools

#### Task 12.3: End-to-End Testing
- [ ] Test complete plugin lifecycle
- [ ] Test plugin interactions
- [ ] Test error recovery
- [ ] Test development workflow
- [ ] Performance benchmarking

#### Task 12.4: Security Audit
- [ ] Verify permission enforcement
- [ ] Test resource limit enforcement
- [ ] Check for privilege escalation
- [ ] Test sandbox isolation
- [ ] Review error handling

#### Task 12.5: Final Audit Checklist
- [ ] All Week 1 SDK components implemented
- [ ] All Week 2 security features working
- [ ] All Week 3-4 plugin features complete
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Performance metrics acceptable
- [ ] No critical security issues
- [ ] Developer tools functional
- [ ] Migration tools tested
- [ ] Backward compatibility maintained

## Success Criteria

### Functional Requirements
- ✅ IWidget interface matches specification exactly
- ✅ IMetadata interface implemented and used
- ✅ All SDK utilities present and functional
- ✅ Permission system prevents unauthorized access
- ✅ Resource limits enforced
- ✅ CLI tool creates and manages plugins
- ✅ Hot reload works in development
- ✅ Editor has find/replace and autocomplete
- ✅ All tests pass with >80% coverage

### Performance Requirements
- Plugin load time < 100ms
- Hot reload time < 500ms
- Memory overhead < 10MB per plugin
- No memory leaks during reload

### Security Requirements
- Plugins cannot access unauthorized services
- Resource limits prevent runaway plugins
- Crashes are contained and recovered
- No privilege escalation possible

### Developer Experience Requirements
- Plugin creation < 1 minute with CLI
- Hot reload works reliably
- Mock framework enables easy testing
- Documentation is comprehensive

## Risk Mitigation

### High Risk Items
1. **Interface Changes**: May break existing plugins
   - Mitigation: Provide migration tool and compatibility layer

2. **Security Implementation**: May impact performance
   - Mitigation: Make optional in development mode

3. **Hot Reload**: Complex state management
   - Mitigation: Start with simple reload, enhance iteratively

### Dependencies
- Ensure all team members aware of interface changes
- Coordinate with any external plugin developers
- Update CI/CD pipelines for new tests

## Timeline Summary

**Total Duration**: 12 working days

- **Phase 1** (Days 1-3): SDK Foundation - Critical fixes
- **Phase 2** (Days 4-5): Security - Basic implementation
- **Phase 3** (Days 6-8): Developer Tools - CLI and templates
- **Phase 4** (Days 9-10): Plugin Features - Editor completion
- **Phase 5** (Days 11-12): Testing & Audit - Verification

## Conclusion

This plan addresses all critical gaps identified in the Week 1-4 plugin refactoring audit. Following this step-by-step approach will bring the implementation to 100% completion with all originally specified features. The final audit on Day 12 ensures everything is properly tested and working as designed.