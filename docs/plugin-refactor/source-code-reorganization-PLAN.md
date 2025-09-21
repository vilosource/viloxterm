# Source Code Reorganization Plan

## Current State Analysis

### Problem Summary
The ViloxTerm project has evolved from a monolithic application to a plugin-based architecture, but the source code organization hasn't been properly restructured. This results in:
1. **Mixed paradigms**: Old monolithic code in root directories (ui/, core/, services/) alongside new package structure (packages/)
2. **Empty main package**: packages/viloapp/ exists but contains no source code
3. **Broken build commands**: `make dev` expects code in packages/viloapp but finds none
4. **Confusing imports**: Mix of imports from root directories and packages
5. **Unclear boundaries**: No clear separation between application core and plugins

### Current Structure Problems

```
viloapp/                          # Project root
├── main.py                       # Entry point imports from root dirs
├── ui/                          # UI components (should be in package)
├── core/                        # Core functionality (should be in package)
├── services/                    # Services (should be in package)
├── controllers/                 # Controllers (should be in package)
├── models/                      # Models (should be in package)
├── packages/                    # New package structure
│   ├── viloapp/                # EMPTY - should contain main app
│   │   └── src/                # No files here!
│   ├── viloapp-sdk/            # SDK package (properly structured)
│   ├── viloxterm/              # Terminal plugin (properly structured)
│   ├── viloedit/               # Editor plugin (properly structured)
│   └── viloapp-cli/            # CLI tools (properly structured)
└── tests/                       # Tests for root code (should move)
```

## Reorganization Goals

1. **Consolidate all application code** into packages/viloapp
2. **Establish clear boundaries** between core app, SDK, and plugins
3. **Fix import paths** to use package namespaces consistently
4. **Enable monorepo benefits**: independent versioning, clear dependencies
5. **Fix build/dev commands** to work with proper structure

## Target Structure

```
viloapp/                              # Project root (clean)
├── main.py                          # Minimal entry point
├── Makefile                         # Build commands
├── pyproject.toml                   # Root project config
├── packages/                        # All source code here
│   ├── viloapp/                    # Main application package
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   │   └── viloapp/
│   │   │       ├── __init__.py
│   │   │       ├── main.py         # App entry point
│   │   │       ├── ui/             # Moved from root
│   │   │       ├── core/           # Moved from root
│   │   │       ├── services/       # Moved from root
│   │   │       ├── controllers/    # Moved from root
│   │   │       └── models/         # Moved from root
│   │   └── tests/                  # App tests
│   ├── viloapp-sdk/                # SDK (already structured)
│   ├── viloxterm/                  # Terminal plugin
│   ├── viloedit/                   # Editor plugin
│   └── viloapp-cli/                # CLI tools
├── scripts/                         # Build/migration scripts
├── docs/                           # Documentation
└── resources/                      # Shared resources
```

## Implementation Phases

### Phase 1: Prepare Target Structure (Day 1)
1. Create packages/viloapp/src/viloapp/ directory structure
2. Set up packages/viloapp/pyproject.toml with dependencies
3. Create packages/viloapp/__init__.py with version info
4. Create migration tracking document

### Phase 2: Move Core Components (Day 2-3)
1. **Move core/** → packages/viloapp/src/viloapp/core/
   - Preserve plugin_system/ subdirectory
   - Update all relative imports
   - Maintain command registry structure

2. **Move services/** → packages/viloapp/src/viloapp/services/
   - Update service locator paths
   - Fix plugin service imports
   - Ensure service initialization works

3. **Move models/** → packages/viloapp/src/viloapp/models/
   - Simple move, fewer dependencies

### Phase 3: Move UI Components (Day 4-5)
1. **Move ui/** → packages/viloapp/src/viloapp/ui/
   - Complex due to many cross-references
   - Update widget imports carefully
   - Preserve resource paths

2. **Move controllers/** → packages/viloapp/src/viloapp/controllers/
   - Update command executor references
   - Fix keyboard handler paths

### Phase 4: Update Entry Points (Day 6)
1. **Create packages/viloapp/src/viloapp/main.py**
   - Move logic from root main.py
   - Set up proper app initialization
   - Configure plugin discovery paths

2. **Update root main.py**
   - Minimal launcher that imports from package
   - Handle development vs production modes

3. **Update Makefile**
   - Fix `make dev` to use new paths
   - Update test commands for new structure
   - Add migration helper commands

### Phase 5: Fix Imports Throughout (Day 7-8)
1. **Update all import statements**
   - Change `from ui.` → `from viloapp.ui.`
   - Change `from core.` → `from viloapp.core.`
   - Change `from services.` → `from viloapp.services.`
   - Change `from controllers.` → `from viloapp.controllers.`
   - Change `from models.` → `from viloapp.models.`

2. **Update plugin imports**
   - Ensure plugins import from viloapp-sdk
   - Fix any direct imports to app internals
   - Validate plugin discovery still works

### Phase 6: Move Tests (Day 9)
1. **Move tests/** → packages/viloapp/tests/
   - Update test imports
   - Fix test discovery paths
   - Ensure pytest configuration works

2. **Update test fixtures**
   - Fix paths in conftest.py files
   - Update mock paths
   - Validate all tests still pass

### Phase 7: Update Configuration (Day 10)
1. **Update pyproject.toml files**
   - Set proper dependencies
   - Configure namespace packages
   - Set up development dependencies

2. **Update .gitignore**
   - Add proper Python package ignores
   - Handle build artifacts correctly

3. **Update CI/CD**
   - Fix GitHub Actions workflows
   - Update build scripts
   - Ensure Docker builds work

### Phase 8: Documentation (Day 11)
1. **Create MONOREPO_PACKAGE_STRUCTURE.md**
   - Document package boundaries
   - Explain import conventions
   - Provide development guidelines

2. **Update README.md**
   - New quick start instructions
   - Updated development workflow
   - Package structure explanation

3. **Update CLAUDE.md**
   - New project structure notes
   - Updated command references
   - Import path guidelines

### Phase 9: Validation (Day 12)
1. **Test all functionality**
   - Run full test suite
   - Manual testing of app launch
   - Plugin loading verification
   - Command execution tests

2. **Performance validation**
   - Check import times
   - Verify no circular dependencies
   - Profile application startup

## Migration Script Overview

Create `scripts/migration/reorganize_source.py`:
```python
#!/usr/bin/env python3
"""
Source code reorganization script.
Moves code from root directories to packages/viloapp.
"""

MIGRATIONS = [
    ("core", "packages/viloapp/src/viloapp/core"),
    ("services", "packages/viloapp/src/viloapp/services"),
    ("models", "packages/viloapp/src/viloapp/models"),
    ("ui", "packages/viloapp/src/viloapp/ui"),
    ("controllers", "packages/viloapp/src/viloapp/controllers"),
    ("tests", "packages/viloapp/tests"),
]

IMPORT_REPLACEMENTS = [
    (r"from (core\.", "from viloapp.\\1"),
    (r"from (services\.", "from viloapp.\\1"),
    (r"from (ui\.", "from viloapp.\\1"),
    (r"from (controllers\.", "from viloapp.\\1"),
    (r"from (models\.", "from viloapp.\\1"),
    (r"import (core\.", "import viloapp.\\1"),
    (r"import (services\.", "import viloapp.\\1"),
    (r"import (ui\.", "import viloapp.\\1"),
    (r"import (controllers\.", "import viloapp.\\1"),
    (r"import (models\.", "import viloapp.\\1"),
]
```

## Risk Mitigation

1. **Backup Strategy**
   - Create full backup before starting
   - Use git branches for each phase
   - Keep rollback scripts ready

2. **Incremental Testing**
   - Test after each phase
   - Don't proceed if tests fail
   - Document any issues found

3. **Dependency Management**
   - Map all cross-dependencies first
   - Update imports systematically
   - Use automated tools where possible

4. **Plugin Compatibility**
   - Ensure SDK remains stable
   - Test plugins after each phase
   - Update plugin docs if needed

## Success Criteria

1. ✅ All code organized under packages/
2. ✅ No source code in root directories (except main.py launcher)
3. ✅ `make dev` command works
4. ✅ All tests pass
5. ✅ Plugins load and function correctly
6. ✅ Clean import structure (viloapp.* namespace)
7. ✅ Clear package boundaries documented
8. ✅ Development workflow simplified

## Timeline

- **Days 1-3**: Core structure migration
- **Days 4-6**: UI and entry points
- **Days 7-9**: Import fixes and tests
- **Days 10-11**: Configuration and documentation
- **Day 12**: Final validation and cleanup

## Next Steps

1. Review and approve this plan
2. Create backup of current state
3. Set up migration branch
4. Begin Phase 1 implementation
5. Create migration script
6. Execute migration systematically

## Notes

- This reorganization aligns with the plugin architecture implemented in Week 1-4
- Maintains compatibility with existing plugin system
- Enables proper monorepo benefits
- Simplifies development and testing workflow
- Makes project structure intuitive for new developers