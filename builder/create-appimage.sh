#!/bin/bash
# Create AppImage from existing standalone build

set -e

echo "Creating AppImage from standalone build..."

# Check if standalone build exists
if [ ! -d "../docker-build-output/ViloxTerm.dist" ]; then
    echo "Error: Standalone build not found. Run './build.sh build' first."
    exit 1
fi

# Create AppDir structure
echo "Setting up AppDir structure..."
rm -rf ../docker-build-output/ViloxTerm.AppDir
mkdir -p ../docker-build-output/ViloxTerm.AppDir/usr/bin
mkdir -p ../docker-build-output/ViloxTerm.AppDir/usr/lib
mkdir -p ../docker-build-output/ViloxTerm.AppDir/usr/share/applications
mkdir -p ../docker-build-output/ViloxTerm.AppDir/usr/share/icons/hicolor/256x256/apps

# Copy distribution
echo "Copying distribution files..."
cp -r ../docker-build-output/ViloxTerm.dist/* ../docker-build-output/ViloxTerm.AppDir/usr/lib/

# Create wrapper script
echo "Creating wrapper script..."
cat > ../docker-build-output/ViloxTerm.AppDir/usr/bin/ViloxTerm << 'EOF'
#!/bin/bash
# Get the directory where this script is located
BIN_DIR="$(dirname "$(readlink -f "$0")")"
# Go up to usr then to lib
exec "$BIN_DIR/../lib/main.bin" "$@"
EOF
chmod +x ../docker-build-output/ViloxTerm.AppDir/usr/bin/ViloxTerm

# Create AppRun
cat > ../docker-build-output/ViloxTerm.AppDir/AppRun << 'EOF'
#!/bin/bash
APPDIR="$(dirname "$(readlink -f "$0")")"
exec "$APPDIR/usr/bin/ViloxTerm" "$@"
EOF
chmod +x ../docker-build-output/ViloxTerm.AppDir/AppRun

# Copy desktop file
echo "Adding desktop file..."
cp ViloxTerm.desktop ../docker-build-output/ViloxTerm.AppDir/
cp ViloxTerm.desktop ../docker-build-output/ViloxTerm.AppDir/usr/share/applications/

# Copy or create icon
echo "Adding icon..."
if [ -f "../deploy/icons/viloxterm.png" ]; then
    cp ../deploy/icons/viloxterm.png ../docker-build-output/ViloxTerm.AppDir/viloxterm.png
    cp ../deploy/icons/viloxterm.png ../docker-build-output/ViloxTerm.AppDir/usr/share/icons/hicolor/256x256/apps/
else
    # Create placeholder icon
    echo "Warning: Icon not found at ../deploy/icons/viloxterm.png"
    # Create a simple blue square as placeholder
    echo "Creating placeholder icon..."
fi

# Download appimagetool if not present
if [ ! -f "../docker-build-output/appimagetool-x86_64.AppImage" ]; then
    echo "Downloading appimagetool..."
    wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage \
        -O ../docker-build-output/appimagetool-x86_64.AppImage
    chmod +x ../docker-build-output/appimagetool-x86_64.AppImage
fi

# Build AppImage
echo "Building AppImage..."
cd ../docker-build-output
ARCH=x86_64 ./appimagetool-x86_64.AppImage ViloxTerm.AppDir ViloxTerm-x86_64.AppImage

if [ -f "ViloxTerm-x86_64.AppImage" ]; then
    chmod +x ViloxTerm-x86_64.AppImage
    echo ""
    echo "Success! AppImage created:"
    ls -lh ViloxTerm-x86_64.AppImage
    echo ""
    echo "You can now run: ./ViloxTerm-x86_64.AppImage"
else
    echo "Error: AppImage creation failed"
    exit 1
fi