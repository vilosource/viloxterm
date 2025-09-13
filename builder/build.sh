#!/bin/bash
# ViloxTerm Docker Build Script
# This script manages the Docker build environment for ViloxTerm

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="viloxterm-builder"
IMAGE_TAG="latest"
CONTAINER_NAME="viloxterm-build"
PROJECT_ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
OUTPUT_DIR="${PROJECT_ROOT}/docker-build-output"

# Print colored message
print_msg() {
    echo -e "${GREEN}[ViloxTerm Builder]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
}

# Build the Docker image
build_image() {
    print_msg "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"

    # Copy entrypoint script to builder directory for Docker context
    cp "${PROJECT_ROOT}/builder/entrypoint.sh" "${PROJECT_ROOT}/builder/entrypoint.sh.tmp" 2>/dev/null || true

    docker build \
        -t "${IMAGE_NAME}:${IMAGE_TAG}" \
        -f "${PROJECT_ROOT}/builder/Dockerfile" \
        "${PROJECT_ROOT}/builder"

    # Clean up temporary file
    rm -f "${PROJECT_ROOT}/builder/entrypoint.sh.tmp"

    print_msg "Docker image built successfully!"
}

# Run the build in Docker container
run_build() {
    local build_type="${1:-standalone}"

    if [ "$build_type" = "onefile" ]; then
        print_msg "Building single-file executable in Docker container..."
    else
        print_msg "Building standalone distribution in Docker container..."
    fi

    # Create output directory if it doesn't exist
    mkdir -p "${OUTPUT_DIR}"

    # Remove existing container if it exists
    docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true

    # Run the build
    docker run \
        --name "${CONTAINER_NAME}" \
        --rm \
        -v "${PROJECT_ROOT}:/workspace:ro" \
        -v "${OUTPUT_DIR}:/output" \
        -v "viloxterm-ccache:/ccache" \
        "${IMAGE_NAME}:${IMAGE_TAG}" \
        build "$build_type"

    print_msg "Build complete! Output in: ${OUTPUT_DIR}"

    # List output files
    if [ "$build_type" = "onefile" ] && [ -f "${OUTPUT_DIR}/ViloxTerm" ]; then
        print_msg "Single executable created:"
        ls -lh "${OUTPUT_DIR}/ViloxTerm" 2>/dev/null || true
    elif [ -d "${OUTPUT_DIR}/ViloxTerm.dist" ]; then
        print_msg "Standalone distribution created:"
        ls -lh "${OUTPUT_DIR}/ViloxTerm.dist/main.bin" 2>/dev/null || true
    fi
}

# Run tests in Docker container
run_tests() {
    print_msg "Running tests in Docker container..."

    docker run \
        --rm \
        -v "${PROJECT_ROOT}:/workspace:ro" \
        "${IMAGE_NAME}:${IMAGE_TAG}" \
        test
}

# Start interactive shell in container
run_shell() {
    print_msg "Starting interactive shell in Docker container..."

    docker run \
        --rm \
        -it \
        -v "${PROJECT_ROOT}:/workspace" \
        -v "${OUTPUT_DIR}:/output" \
        -v "viloxterm-ccache:/ccache" \
        "${IMAGE_NAME}:${IMAGE_TAG}" \
        shell
}

# Clean build artifacts
clean() {
    print_msg "Cleaning build artifacts..."

    # Remove output directory
    rm -rf "${OUTPUT_DIR}"

    # Run clean command in container
    docker run \
        --rm \
        -v "viloxterm-ccache:/ccache" \
        "${IMAGE_NAME}:${IMAGE_TAG}" \
        clean

    print_msg "Clean complete!"
}

# Remove Docker image
remove_image() {
    print_msg "Removing Docker image..."
    docker rmi "${IMAGE_NAME}:${IMAGE_TAG}" 2>/dev/null || true
    docker volume rm viloxterm-ccache 2>/dev/null || true
    print_msg "Docker image and cache volume removed!"
}

# Show usage
usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  build-image    - Build the Docker image"
    echo "  build          - Build standalone distribution (folder with exe + libs)"
    echo "  appimage       - Build AppImage (single portable file for Linux)"
    echo "  test           - Run tests"
    echo "  shell          - Start interactive shell in container"
    echo "  clean          - Clean build artifacts"
    echo "  remove         - Remove Docker image and cache"
    echo "  rebuild        - Clean, rebuild image, and build executable"
    echo ""
    echo "Examples:"
    echo "  $0 build          # Build standalone distribution"
    echo "  $0 appimage       # Build AppImage (recommended for Linux)"
    echo "  $0 rebuild        # Full rebuild from scratch"
    echo "  $0 shell          # Debug in container"
}

# Main script logic
main() {
    check_docker

    case "$1" in
        build-image)
            build_image
            ;;
        build)
            # Build image if it doesn't exist
            if ! docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" &> /dev/null; then
                print_warning "Docker image not found. Building..."
                build_image
            fi
            run_build "standalone"
            ;;
        appimage)
            # Build image if it doesn't exist
            if ! docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" &> /dev/null; then
                print_warning "Docker image not found. Building..."
                build_image
            fi
            # First build standalone, then convert to AppImage
            print_msg "Building AppImage..."
            docker run \
                --name "${CONTAINER_NAME}" \
                --rm \
                -v "${PROJECT_ROOT}:/workspace:ro" \
                -v "${OUTPUT_DIR}:/output" \
                -v "viloxterm-ccache:/ccache" \
                "${IMAGE_NAME}:${IMAGE_TAG}" \
                build appimage

            if [ -f "${OUTPUT_DIR}/ViloxTerm-x86_64.AppImage" ]; then
                print_msg "AppImage created successfully!"
                ls -lh "${OUTPUT_DIR}/ViloxTerm-x86_64.AppImage"
            else
                print_error "AppImage build failed!"
            fi
            ;;
        test)
            run_tests
            ;;
        shell)
            run_shell
            ;;
        clean)
            clean
            ;;
        remove)
            remove_image
            ;;
        rebuild)
            clean
            remove_image
            build_image
            run_build "standalone"
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"