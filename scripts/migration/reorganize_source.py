#!/usr/bin/env python3
"""
Source code reorganization script for ViloxTerm.
Moves code from root directories to packages/viloapp structure.

Usage:
    python scripts/migration/reorganize_source.py [--dry-run] [--phase PHASE]

Options:
    --dry-run    Show what would be done without making changes
    --phase N    Run specific phase (1-9)
"""

import re
import shutil
import argparse
from pathlib import Path
from typing import Dict
import json
import subprocess

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Migration mapping
MIGRATIONS = [
    ("core", "packages/viloapp/src/viloapp/core"),
    ("services", "packages/viloapp/src/viloapp/services"),
    ("models", "packages/viloapp/src/viloapp/models"),
    ("ui", "packages/viloapp/src/viloapp/ui"),
    ("controllers", "packages/viloapp/src/viloapp/controllers"),
    ("tests", "packages/viloapp/tests"),
]

# Import replacements
IMPORT_REPLACEMENTS = [
    # From imports
    (r"from (core\.)", r"from viloapp.\1"),
    (r"from (services\.)", r"from viloapp.\1"),
    (r"from (ui\.)", r"from viloapp.\1"),
    (r"from (controllers\.)", r"from viloapp.\1"),
    (r"from (models\.)", r"from viloapp.\1"),
    # Import statements
    (r"import (core\.)", r"import viloapp.\1"),
    (r"import (services\.)", r"import viloapp.\1"),
    (r"import (ui\.)", r"import viloapp.\1"),
    (r"import (controllers\.)", r"import viloapp.\1"),
    (r"import (models\.)", r"import viloapp.\1"),
    # Relative imports in docstrings and comments
    (r'"(core\.)', r'"viloapp.\1'),
    (r'"(services\.)', r'"viloapp.\1'),
    (r'"(ui\.)', r'"viloapp.\1'),
    (r'"(controllers\.)', r'"viloapp.\1'),
    (r'"(models\.)', r'"viloapp.\1'),
]

class SourceReorganizer:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.project_root = PROJECT_ROOT
        self.backup_dir = self.project_root / ".migration_backup"
        self.log_file = self.project_root / "migration.log"
        self.migration_state_file = self.project_root / ".migration_state.json"
        self.migration_state = self.load_state()

    def log(self, message: str):
        """Log message to console and file."""
        print(message)
        if not self.dry_run:
            with open(self.log_file, "a") as f:
                f.write(f"{message}\n")

    def load_state(self) -> Dict:
        """Load migration state from file."""
        if self.migration_state_file.exists():
            with open(self.migration_state_file, "r") as f:
                return json.load(f)
        return {"completed_phases": [], "moved_files": {}}

    def save_state(self):
        """Save migration state to file."""
        if not self.dry_run:
            with open(self.migration_state_file, "w") as f:
                json.dump(self.migration_state, f, indent=2)

    def phase_1_prepare_structure(self):
        """Phase 1: Prepare target structure."""
        self.log("\n=== Phase 1: Prepare Target Structure ===")

        # Create viloapp package structure
        viloapp_dir = self.project_root / "packages" / "viloapp"
        src_dir = viloapp_dir / "src" / "viloapp"
        tests_dir = viloapp_dir / "tests"

        dirs_to_create = [
            src_dir,
            tests_dir,
            src_dir / "core",
            src_dir / "services",
            src_dir / "models",
            src_dir / "ui",
            src_dir / "controllers",
        ]

        for dir_path in dirs_to_create:
            if not dir_path.exists():
                self.log(f"Creating directory: {dir_path}")
                if not self.dry_run:
                    dir_path.mkdir(parents=True, exist_ok=True)

        # Create pyproject.toml for viloapp package
        pyproject_path = viloapp_dir / "pyproject.toml"
        if not pyproject_path.exists():
            self.log(f"Creating {pyproject_path}")
            if not self.dry_run:
                pyproject_content = '''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "viloapp"
version = "0.1.0"
description = "ViloxTerm - Terminal IDE Application"
requires-python = ">=3.12"
dependencies = [
    "PySide6>=6.5.0",
    "viloapp-sdk>=0.1.0",
    "pyte>=0.8.1",
    "pygments>=2.15.0",
    "psutil>=5.9.5",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.3.1",
    "pytest-qt>=4.2.0",
    "pytest-cov>=4.1.0",
    "black>=23.3.0",
    "ruff>=0.0.270",
    "mypy>=1.3.0",
]

[project.scripts]
viloapp = "viloapp.main:main"
'''
                pyproject_path.write_text(pyproject_content)

        # Create __init__.py files
        init_files = [
            src_dir / "__init__.py",
            tests_dir / "__init__.py",
        ]

        for init_file in init_files:
            if not init_file.exists():
                self.log(f"Creating {init_file}")
                if not self.dry_run:
                    init_file.write_text('"""ViloxTerm application package."""\n\n__version__ = "0.1.0"\n')

        self.migration_state["completed_phases"].append(1)
        self.save_state()

    def move_directory(self, source: str, target: str):
        """Move a directory from source to target."""
        source_path = self.project_root / source
        target_path = self.project_root / target

        if not source_path.exists():
            self.log(f"Warning: Source directory does not exist: {source_path}")
            return

        self.log(f"Moving {source} -> {target}")

        if not self.dry_run:
            # Create backup
            backup_path = self.backup_dir / source
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source_path, backup_path, dirs_exist_ok=True)

            # Move directory
            if target_path.exists():
                # Merge with existing
                for item in source_path.iterdir():
                    target_item = target_path / item.name
                    if item.is_dir():
                        shutil.copytree(item, target_item, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, target_item)
            else:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source_path), str(target_path))

            # Remove source
            shutil.rmtree(source_path)

            # Track moved files
            self.migration_state["moved_files"][source] = target

    def phase_2_move_core(self):
        """Phase 2: Move core components."""
        self.log("\n=== Phase 2: Move Core Components ===")

        self.move_directory("core", "packages/viloapp/src/viloapp/core")
        self.move_directory("services", "packages/viloapp/src/viloapp/services")
        self.move_directory("models", "packages/viloapp/src/viloapp/models")

        self.migration_state["completed_phases"].append(2)
        self.save_state()

    def phase_3_move_ui(self):
        """Phase 3: Move UI components."""
        self.log("\n=== Phase 3: Move UI Components ===")

        self.move_directory("ui", "packages/viloapp/src/viloapp/ui")
        self.move_directory("controllers", "packages/viloapp/src/viloapp/controllers")

        self.migration_state["completed_phases"].append(3)
        self.save_state()

    def phase_4_update_entry_points(self):
        """Phase 4: Update entry points."""
        self.log("\n=== Phase 4: Update Entry Points ===")

        # Read current main.py
        main_py_path = self.project_root / "main.py"
        if main_py_path.exists():
            main_content = main_py_path.read_text()

            # Create new viloapp main.py
            new_main_path = self.project_root / "packages" / "viloapp" / "src" / "viloapp" / "main.py"
            self.log(f"Creating {new_main_path}")

            if not self.dry_run:
                # Update imports in main content
                for pattern, replacement in IMPORT_REPLACEMENTS:
                    main_content = re.sub(pattern, replacement, main_content)

                # Add main function if not present
                if "def main():" not in main_content:
                    main_content += "\n\ndef main():\n    app = ViloxTermApplication()\n    app.run()\n"

                new_main_path.write_text(main_content)

                # Create minimal root main.py
                root_main_content = '''#!/usr/bin/env python3
"""ViloxTerm application entry point."""

import sys
import os

# Add packages to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'viloapp', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'viloapp-sdk', 'src'))

from viloapp.main import main

if __name__ == "__main__":
    main()
'''
                main_py_path.write_text(root_main_content)

        self.migration_state["completed_phases"].append(4)
        self.save_state()

    def fix_imports_in_file(self, file_path: Path):
        """Fix imports in a single file."""
        try:
            content = file_path.read_text()
            original_content = content

            for pattern, replacement in IMPORT_REPLACEMENTS:
                content = re.sub(pattern, replacement, content)

            if content != original_content:
                self.log(f"Updating imports in {file_path}")
                if not self.dry_run:
                    file_path.write_text(content)

        except Exception as e:
            self.log(f"Error processing {file_path}: {e}")

    def phase_5_fix_imports(self):
        """Phase 5: Fix imports throughout."""
        self.log("\n=== Phase 5: Fix Imports Throughout ===")

        # Fix imports in all Python files
        packages_dir = self.project_root / "packages"

        for py_file in packages_dir.rglob("*.py"):
            self.fix_imports_in_file(py_file)

        # Also fix imports in root test files if any remain
        root_tests = self.project_root / "tests"
        if root_tests.exists():
            for py_file in root_tests.rglob("*.py"):
                self.fix_imports_in_file(py_file)

        self.migration_state["completed_phases"].append(5)
        self.save_state()

    def phase_6_move_tests(self):
        """Phase 6: Move tests."""
        self.log("\n=== Phase 6: Move Tests ===")

        self.move_directory("tests", "packages/viloapp/tests")

        self.migration_state["completed_phases"].append(6)
        self.save_state()

    def phase_7_update_config(self):
        """Phase 7: Update configuration."""
        self.log("\n=== Phase 7: Update Configuration ===")

        # Update Makefile
        makefile_path = self.project_root / "Makefile"
        if makefile_path.exists():
            self.log(f"Updating {makefile_path}")
            if not self.dry_run:
                makefile_content = makefile_path.read_text()

                # Update dev command
                makefile_content = makefile_content.replace(
                    "cd packages/viloapp && python -m viloapp.main --dev",
                    "python main.py --dev"
                )

                # Update test commands
                makefile_content = makefile_content.replace(
                    "pytest packages/viloapp/tests -v",
                    "pytest packages/viloapp/tests -v"
                )

                makefile_path.write_text(makefile_content)

        # Update .gitignore if needed
        gitignore_path = self.project_root / ".gitignore"
        if gitignore_path.exists():
            self.log(f"Checking {gitignore_path}")
            if not self.dry_run:
                gitignore_content = gitignore_path.read_text()
                if ".migration_backup/" not in gitignore_content:
                    gitignore_content += "\n# Migration backup\n.migration_backup/\n.migration_state.json\nmigration.log\n"
                    gitignore_path.write_text(gitignore_content)

        self.migration_state["completed_phases"].append(7)
        self.save_state()

    def phase_8_documentation(self):
        """Phase 8: Update documentation."""
        self.log("\n=== Phase 8: Documentation ===")

        # Update CLAUDE.md
        claude_md_path = self.project_root / "CLAUDE.md"
        if claude_md_path.exists():
            self.log(f"Updating {claude_md_path}")
            if not self.dry_run:
                content = claude_md_path.read_text()

                # Update import examples
                for pattern, replacement in IMPORT_REPLACEMENTS:
                    content = re.sub(pattern, replacement, content)

                # Add note about new structure
                if "## Package Structure" not in content:
                    structure_note = '''
## Package Structure

The application now follows a proper monorepo structure:
- All application code is in `packages/viloapp/`
- SDK is in `packages/viloapp-sdk/`
- Plugins are in `packages/viloxterm/` and `packages/viloedit/`
- Use `from viloapp.` prefix for all application imports
'''
                    content = content.replace("## Project Structure", structure_note + "\n## Project Structure")

                claude_md_path.write_text(content)

        self.migration_state["completed_phases"].append(8)
        self.save_state()

    def phase_9_validation(self):
        """Phase 9: Validation."""
        self.log("\n=== Phase 9: Validation ===")

        issues = []

        # Check that old directories are gone
        for old_dir, _ in MIGRATIONS:
            old_path = self.project_root / old_dir
            if old_path.exists() and old_path.is_dir():
                issues.append(f"Old directory still exists: {old_path}")

        # Check that new directories exist
        viloapp_src = self.project_root / "packages" / "viloapp" / "src" / "viloapp"
        for subdir in ["core", "services", "models", "ui", "controllers"]:
            new_path = viloapp_src / subdir
            if not new_path.exists():
                issues.append(f"New directory missing: {new_path}")

        # Check for Python syntax errors
        self.log("Checking Python syntax...")
        if not self.dry_run:
            result = subprocess.run(
                ["python", "-m", "py_compile", "-"],
                input="import viloapp",
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            if result.returncode != 0:
                issues.append(f"Import check failed: {result.stderr}")

        # Report results
        if issues:
            self.log("\n❌ Validation Failed:")
            for issue in issues:
                self.log(f"  - {issue}")
        else:
            self.log("\n✅ Validation Passed!")

        self.migration_state["completed_phases"].append(9)
        self.save_state()

        return len(issues) == 0

    def run_phase(self, phase: int):
        """Run a specific phase."""
        phases = {
            1: self.phase_1_prepare_structure,
            2: self.phase_2_move_core,
            3: self.phase_3_move_ui,
            4: self.phase_4_update_entry_points,
            5: self.phase_5_fix_imports,
            6: self.phase_6_move_tests,
            7: self.phase_7_update_config,
            8: self.phase_8_documentation,
            9: self.phase_9_validation,
        }

        if phase in phases:
            if phase in self.migration_state["completed_phases"] and not self.dry_run:
                self.log(f"Phase {phase} already completed. Skipping.")
                return

            phases[phase]()
        else:
            self.log(f"Invalid phase: {phase}")

    def run_all(self):
        """Run all phases."""
        for phase in range(1, 10):
            self.run_phase(phase)

    def rollback(self):
        """Rollback migration using backup."""
        if not self.backup_dir.exists():
            self.log("No backup found. Cannot rollback.")
            return

        self.log("\n=== Rolling Back Migration ===")

        for source, target in self.migration_state["moved_files"].items():
            backup_path = self.backup_dir / source
            original_path = self.project_root / source

            if backup_path.exists():
                self.log(f"Restoring {source}")
                if not self.dry_run:
                    if original_path.exists():
                        shutil.rmtree(original_path)
                    shutil.copytree(backup_path, original_path)

        # Clean up viloapp package if it's empty
        viloapp_pkg = self.project_root / "packages" / "viloapp"
        if viloapp_pkg.exists():
            # Check if it only has our created structure
            src_dir = viloapp_pkg / "src" / "viloapp"
            if not any(src_dir.glob("*.py")):
                self.log(f"Removing empty {viloapp_pkg}")
                if not self.dry_run:
                    shutil.rmtree(viloapp_pkg)

        # Clear state
        if not self.dry_run:
            self.migration_state = {"completed_phases": [], "moved_files": {}}
            self.save_state()

        self.log("Rollback completed.")


def main():
    parser = argparse.ArgumentParser(description="Reorganize ViloxTerm source code")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--phase", type=int, help="Run specific phase (1-9)")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration using backup")

    args = parser.parse_args()

    reorganizer = SourceReorganizer(dry_run=args.dry_run)

    if args.rollback:
        reorganizer.rollback()
    elif args.phase:
        reorganizer.run_phase(args.phase)
    else:
        reorganizer.run_all()


if __name__ == "__main__":
    main()