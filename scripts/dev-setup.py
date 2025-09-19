#!/usr/bin/env python3
"""Setup development environment for ViloxTerm monorepo."""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

# Package installation order (respecting dependencies)
PACKAGES = [
    ("viloapp-sdk", []),
    ("viloxterm", ["viloapp-sdk"]),
    ("viloedit", ["viloapp-sdk"]),
    ("viloapp", ["viloapp-sdk"])
]

def run_command(cmd: List[str], cwd: Path = None) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr

def install_package(package_dir: Path, editable: bool = True) -> bool:
    """Install a single package."""
    print(f"Installing {package_dir.name}...")

    install_cmd = [sys.executable, "-m", "pip", "install"]
    if editable:
        install_cmd.append("-e")
    install_cmd.append(str(package_dir))

    returncode, stdout, stderr = run_command(install_cmd)

    if returncode != 0:
        print(f"Error installing {package_dir.name}:")
        print(stderr)
        return False

    print(f"✓ {package_dir.name} installed successfully")
    return True

def main():
    """Main setup function."""
    root = Path(__file__).parent.parent
    packages_dir = root / "packages"

    print("ViloxTerm Development Environment Setup")
    print("=" * 40)

    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: Python 3.8+ is required")
        sys.exit(1)

    # Install development dependencies
    print("\nInstalling development dependencies...")
    dev_deps = ["pytest", "pytest-qt", "pytest-cov", "black", "ruff", "mypy"]
    run_command([sys.executable, "-m", "pip", "install"] + dev_deps)

    # Install packages in order
    print("\nInstalling packages...")
    success = True
    for package_name, _ in PACKAGES:
        package_path = packages_dir / package_name
        if package_path.exists():
            if not install_package(package_path):
                success = False
                break

    if success:
        print("\n✅ Development environment setup complete!")
        print("\nYou can now run:")
        print("  make test     - Run all tests")
        print("  make format   - Format code")
        print("  make lint     - Lint code")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()