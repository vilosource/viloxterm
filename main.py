#!/usr/bin/env python3
"""
ViloxTerm Entry Point

This is a minimal launcher that delegates to the main viloapp package.
After reorganization, all application code lives in packages/viloapp/src/viloapp/.
"""

import sys
import os

# Add the viloapp package to the path
project_root = os.path.dirname(os.path.abspath(__file__))
viloapp_src = os.path.join(project_root, "packages", "viloapp", "src")
sys.path.insert(0, viloapp_src)

# Import and run the main application
try:
    from viloapp.main import main

    if __name__ == "__main__":
        main()
except ImportError as e:
    print(f"Failed to import viloapp: {e}")
    print("Ensure the packages/viloapp/src directory exists and contains the application code.")
    sys.exit(1)
