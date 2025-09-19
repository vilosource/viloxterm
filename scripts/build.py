#!/usr/bin/env python3
"""Build all packages in the monorepo."""

import subprocess
import sys
import shutil
from pathlib import Path

PACKAGES = [
    "viloapp-sdk",
    "viloxterm",
    "viloedit",
    "viloapp"
]

def clean_package(package_dir: Path):
    """Clean build artifacts from a package."""
    dirs_to_remove = ["build", "dist", "*.egg-info"]
    for pattern in dirs_to_remove:
        for path in package_dir.glob(pattern):
            if path.is_dir():
                print(f"  Removing {path}")
                shutil.rmtree(path)

def build_package(package_dir: Path) -> bool:
    """Build a single package."""
    print(f"Building {package_dir.name}...")

    # Clean first
    clean_package(package_dir)

    # Build
    result = subprocess.run(
        [sys.executable, "-m", "build"],
        cwd=package_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Failed to build {package_dir.name}")
        print(result.stderr)
        return False

    print(f"✓ {package_dir.name} built successfully")

    # List built files
    dist_dir = package_dir / "dist"
    if dist_dir.exists():
        for file in dist_dir.iterdir():
            print(f"    - {file.name}")

    return True

def main():
    """Build all packages."""
    root = Path(__file__).parent.parent
    packages_dir = root / "packages"

    print("Building ViloxTerm Packages")
    print("=" * 40)

    # Install build dependencies
    print("Installing build dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "build"])

    # Build each package
    all_success = True
    for package in PACKAGES:
        package_dir = packages_dir / package
        if package_dir.exists():
            if not build_package(package_dir):
                all_success = False
                break
        else:
            print(f"Warning: Package {package} does not exist yet")

    if all_success:
        print("\n✅ All packages built successfully!")
    else:
        print("\n❌ Build failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()