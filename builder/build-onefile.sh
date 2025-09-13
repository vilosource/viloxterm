#!/bin/bash
# Build single-file ViloxTerm executable

set -e

echo "Building single-file ViloxTerm executable..."

# Run Docker container with onefile mode
docker run \
    --rm \
    -v "$(dirname "$(pwd)"):/workspace:ro" \
    -v "$(dirname "$(pwd)")/docker-build-output:/output" \
    viloxterm-builder:latest \
    bash -c "
        cd /workspace
        cp -r /workspace/* /build/ 2>/dev/null || true
        cd /build

        # Compile resources
        if [ -f resources/resources.qrc ]; then
            pyside6-rcc resources/resources.qrc -o resources/resources_rc.py
        fi

        # Build single file with Nuitka directly
        echo 'Building with Nuitka --onefile mode...'
        python3 -m nuitka \
            --onefile \
            --enable-plugin=pyside6 \
            --include-module=flask \
            --include-module=flask_socketio \
            --include-module=socketio \
            --include-module=engineio \
            --include-module=simple_websocket \
            --include-module=resources.resources_rc \
            --include-data-dir=resources/icons=resources/icons \
            --include-data-dir=ui/terminal/static=ui/terminal/static \
            --include-data-dir=deploy/icons=deploy/icons \
            --linux-onefile-icon=deploy/icons/viloxterm.ico \
            --output-filename=ViloxTerm \
            --assume-yes-for-downloads \
            --show-progress \
            main.py

        # Copy result
        if [ -f ViloxTerm ]; then
            cp ViloxTerm /output/
            chmod +x /output/ViloxTerm
            echo 'Single executable created: /output/ViloxTerm'
            echo \"Size: \$(du -h /output/ViloxTerm | cut -f1)\"
        else
            echo 'Build failed - executable not found'
            ls -la
        fi
    "

if [ -f "../docker-build-output/ViloxTerm" ]; then
    echo "Success! Single executable created:"
    ls -lh ../docker-build-output/ViloxTerm
else
    echo "Build may have failed. Check docker-build-output directory."
fi