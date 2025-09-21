"""Tests to ensure models layer has no Qt dependencies."""

import ast
import os
import pytest
from pathlib import Path


def get_python_files(directory):
    """Get all Python files in a directory."""
    path = Path(directory)
    return list(path.rglob("*.py"))


def extract_imports(file_path):
    """Extract all imports from a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return imports
    except Exception as e:
        pytest.fail(f"Failed to parse {file_path}: {e}")


def is_qt_import(import_name):
    """Check if an import is Qt-related."""
    qt_patterns = [
        'PySide6',
        'PyQt5',
        'PyQt6',
        'qtpy',
        'Qt',
    ]

    for pattern in qt_patterns:
        if import_name.startswith(pattern):
            return True
    return False


class TestNoQtDependencies:
    """Test that models and interfaces have no Qt dependencies."""

    def test_models_package_no_qt_imports(self):
        """Test that models package has no Qt imports."""
        # Get the models directory path relative to current test file
        current_file = Path(__file__)
        package_root = current_file.parent.parent.parent / "src" / "viloapp" / "models"

        if not package_root.exists():
            pytest.skip(f"Models directory not found: {package_root}")

        python_files = get_python_files(package_root)

        for file_path in python_files:
            imports = extract_imports(file_path)
            qt_imports = [imp for imp in imports if is_qt_import(imp)]

            assert not qt_imports, f"Found Qt imports in {file_path}: {qt_imports}"

    def test_interfaces_package_no_qt_imports(self):
        """Test that interfaces package has no Qt imports."""
        # Get the interfaces directory path relative to current test file
        current_file = Path(__file__)
        package_root = current_file.parent.parent.parent / "src" / "viloapp" / "interfaces"

        if not package_root.exists():
            pytest.skip(f"Interfaces directory not found: {package_root}")

        python_files = get_python_files(package_root)

        for file_path in python_files:
            imports = extract_imports(file_path)
            qt_imports = [imp for imp in imports if is_qt_import(imp)]

            assert not qt_imports, f"Found Qt imports in {file_path}: {qt_imports}"

    def test_models_can_import_without_qt(self):
        """Test that models can be imported without Qt being available."""
        # This test ensures that importing models doesn't indirectly bring in Qt
        try:
            from viloapp.models import (
                OperationResult,
                WorkspaceState,
                PaneState,
                TabState,
                SplitPaneRequest,
            )

            # Try to create instances to ensure no hidden Qt dependencies
            result = OperationResult.success_result()
            workspace = WorkspaceState()

            assert result is not None
            assert workspace is not None

        except ImportError as e:
            if any(qt_lib in str(e) for qt_lib in ['PySide6', 'PyQt5', 'PyQt6']):
                pytest.fail(f"Models import failed due to Qt dependency: {e}")
            else:
                # Re-raise if it's a different import error
                raise

    def test_interfaces_can_import_without_qt(self):
        """Test that interfaces can be imported without Qt being available."""
        try:
            from viloapp.interfaces import (
                IWorkspaceModel,
                ITabModel,
                IPaneModel,
                IModelObserver,
            )

            # Ensure interfaces are properly defined
            assert IWorkspaceModel is not None
            assert ITabModel is not None
            assert IPaneModel is not None
            assert IModelObserver is not None

        except ImportError as e:
            if any(qt_lib in str(e) for qt_lib in ['PySide6', 'PyQt5', 'PyQt6']):
                pytest.fail(f"Interfaces import failed due to Qt dependency: {e}")
            else:
                # Re-raise if it's a different import error
                raise

    def test_no_widget_references_in_models(self):
        """Test that models don't reference Qt widget types."""
        current_file = Path(__file__)
        package_root = current_file.parent.parent.parent / "src" / "viloapp" / "models"

        if not package_root.exists():
            pytest.skip(f"Models directory not found: {package_root}")

        qt_widget_terms = [
            'QWidget',
            'QMainWindow',
            'QTabWidget',
            'QSplitter',
            'QVBoxLayout',
            'QHBoxLayout',
            'QPushButton',
            'QLabel',
            'QTextEdit',
            'QLineEdit',
        ]

        python_files = get_python_files(package_root)

        for file_path in python_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            for term in qt_widget_terms:
                assert term not in content, f"Found Qt widget reference '{term}' in {file_path}"

    def test_no_signal_slot_references_in_models(self):
        """Test that models don't use Qt signal/slot mechanism."""
        current_file = Path(__file__)
        package_root = current_file.parent.parent.parent / "src" / "viloapp" / "models"

        if not package_root.exists():
            pytest.skip(f"Models directory not found: {package_root}")

        qt_signal_terms = [
            'Signal(',
            'Slot(',
            'pyqtSignal',
            'emit(',
            'connect(',
            'disconnect(',
        ]

        python_files = get_python_files(package_root)

        for file_path in python_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            for term in qt_signal_terms:
                assert term not in content, f"Found Qt signal/slot reference '{term}' in {file_path}"