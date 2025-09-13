#!/bin/bash
# ViloxTerm Docker Build Entrypoint

set -e  # Exit on error

echo "========================================="
echo "ViloxTerm Docker Build Environment"
echo "Python: $(python3 --version)"
echo "Nuitka: $(python3 -m nuitka --version | head -1)"
echo "========================================="

# Ensure we're in the workspace
cd /workspace

# Handle different commands
case "$1" in
    build)
        echo "Starting ViloxTerm build..."

        # Copy source code to build directory (to avoid modifying mounted volume)
        echo "Preparing build environment..."
        cp -r /workspace/* /build/ 2>/dev/null || true
        cd /build

        # Compile Qt resources
        echo "Compiling Qt resources..."
        if [ -f "resources/resources.qrc" ]; then
            pyside6-rcc resources/resources.qrc -o resources/resources_rc.py
            echo "Resources compiled successfully!"
        fi

        # Build standalone distribution with pyside6-deploy
        echo "Building standalone distribution with pyside6-deploy..."
        pyside6-deploy -v main.py || {
            echo "Build failed! Trying alternative method..."
            # Fallback to direct Nuitka if pyside6-deploy fails
            python3 -m nuitka \
                --standalone \
                --enable-plugin=pyside6 \
                --include-module=flask \
                --include-module=flask_socketio \
                --include-module=socketio \
                --include-module=engineio \
                --include-module=simple_websocket \
                --include-data-dir=resources/icons=resources/icons \
                --include-data-dir=ui/terminal/static=ui/terminal/static \
                --include-data-dir=deploy/icons=deploy/icons \
                --output-dir=/output \
                --assume-yes-for-downloads \
                main.py
        }

        # Copy build artifacts to output
        echo "Copying build artifacts to output..."
        if [ -d "ViloxTerm.dist" ]; then
            cp -r ViloxTerm.dist /output/
        elif [ -d "main.dist" ]; then
            cp -r main.dist /output/ViloxTerm.dist
        elif [ -d "/output/main.dist" ]; then
            mv /output/main.dist /output/ViloxTerm.dist
        fi

        # Set proper permissions
        if [ -f "/output/ViloxTerm.dist/main.bin" ]; then
            chmod +x /output/ViloxTerm.dist/main.bin
            echo "Build complete! Executable: /output/ViloxTerm.dist/main.bin"
        else
            echo "Warning: Executable not found in expected location"
            ls -la /output/
        fi

        # If AppImage mode is requested, create AppImage
        if [ "$2" = "appimage" ]; then
            echo "Creating AppImage from standalone build..."

            # Create AppDir structure
            mkdir -p /output/ViloxTerm.AppDir/usr/bin
            mkdir -p /output/ViloxTerm.AppDir/usr/lib
            mkdir -p /output/ViloxTerm.AppDir/usr/share/applications
            mkdir -p /output/ViloxTerm.AppDir/usr/share/icons/hicolor/256x256/apps

            # Copy entire distribution to AppDir
            cp -r /output/ViloxTerm.dist/* /output/ViloxTerm.AppDir/usr/lib/

            # Create wrapper script
            cat > /output/ViloxTerm.AppDir/usr/bin/ViloxTerm << 'EOF'
#!/bin/bash
APPDIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
exec "$APPDIR/usr/lib/main.bin" "$@"
EOF
            chmod +x /output/ViloxTerm.AppDir/usr/bin/ViloxTerm

            # Create symlink for AppRun
            ln -sf usr/bin/ViloxTerm /output/ViloxTerm.AppDir/AppRun

            # Copy desktop file
            if [ -f "/workspace/builder/ViloxTerm.desktop" ]; then
                cp /workspace/builder/ViloxTerm.desktop /output/ViloxTerm.AppDir/
                cp /workspace/builder/ViloxTerm.desktop /output/ViloxTerm.AppDir/usr/share/applications/
            else
                # Create basic desktop file
                cat > /output/ViloxTerm.AppDir/ViloxTerm.desktop << 'EOF'
[Desktop Entry]
Name=ViloxTerm
Exec=ViloxTerm
Icon=viloxterm
Type=Application
Categories=Development;IDE;
Terminal=false
EOF
                cp /output/ViloxTerm.AppDir/ViloxTerm.desktop /output/ViloxTerm.AppDir/usr/share/applications/
            fi

            # Copy icon
            if [ -f "/workspace/deploy/icons/viloxterm.png" ]; then
                cp /workspace/deploy/icons/viloxterm.png /output/ViloxTerm.AppDir/viloxterm.png
                cp /workspace/deploy/icons/viloxterm.png /output/ViloxTerm.AppDir/usr/share/icons/hicolor/256x256/apps/viloxterm.png
            else
                # Create a simple icon if not found
                convert -size 256x256 xc:blue -fill white -gravity center -pointsize 72 -annotate +0+0 'VT' /output/ViloxTerm.AppDir/viloxterm.png
                cp /output/ViloxTerm.AppDir/viloxterm.png /output/ViloxTerm.AppDir/usr/share/icons/hicolor/256x256/apps/
            fi

            # Build AppImage using appimagetool
            cd /output
            ARCH=x86_64 appimagetool ViloxTerm.AppDir ViloxTerm-x86_64.AppImage

            if [ -f "/output/ViloxTerm-x86_64.AppImage" ]; then
                chmod +x /output/ViloxTerm-x86_64.AppImage
                echo "AppImage created successfully: /output/ViloxTerm-x86_64.AppImage"
                echo "File size: $(du -h /output/ViloxTerm-x86_64.AppImage | cut -f1)"

                # Clean up AppDir after successful build
                rm -rf /output/ViloxTerm.AppDir
            else
                echo "AppImage creation failed!"
            fi
        fi
        ;;

    test)
        echo "Running tests..."
        cd /workspace
        python3 -m pytest tests/ -v
        ;;

    shell)
        echo "Starting interactive shell..."
        exec /bin/bash
        ;;

    clean)
        echo "Cleaning build artifacts..."
        rm -rf /build/* /output/* /ccache/*
        echo "Clean complete!"
        ;;

    *)
        echo "Unknown command: $1"
        echo "Available commands: build, test, shell, clean"
        exit 1
        ;;
esac