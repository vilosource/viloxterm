#!/usr/bin/env python3
"""Development setup script for ViloxTerm plugin architecture."""

import os
import sys
import subprocess
from pathlib import Path

def setup_development_environment():
    """Setup development environment for ViloxTerm with plugins."""

    # Get project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print("=== ViloxTerm Development Setup ===")
    print(f"Project root: {project_root}")

    # Install SDK first (others depend on it)
    print("\n1. Installing SDK package...")
    sdk_path = project_root / "packages" / "viloapp-sdk"
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", str(sdk_path)], check=True)

    # Install terminal plugin
    print("\n2. Installing Terminal plugin...")
    terminal_path = project_root / "packages" / "viloxterm"
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", str(terminal_path)], check=True)

    # Install editor plugin
    print("\n3. Installing Editor plugin...")
    editor_path = project_root / "packages" / "viloedit"
    if editor_path.exists():
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", str(editor_path)], check=True)

    # Install main app dependencies
    print("\n4. Installing main application dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)

    print("\n=== Setup Complete ===")
    print("All packages installed in editable mode.")
    print("\nYou can now run ViloxTerm with plugin support!")
    print("To verify installation:")
    print("  python -c \"import viloapp_sdk; print(viloapp_sdk.__version__)\"")
    print("  python -c \"import viloxterm; print('Terminal plugin available')\"")

if __name__ == "__main__":
    setup_development_environment()