# ViloxTerm Docker Build Environment

This directory contains the Docker-based build system for creating standalone ViloxTerm executables.

## Quick Start

Build the executable:
```bash
cd builder
./build.sh build
```

The executable will be created in `docker-build-output/ViloxTerm.dist/main.bin`

## Requirements

- Docker installed and running
- At least 4GB of free disk space
- Linux, macOS, or Windows with Docker Desktop

## Build Commands

### Build the executable
```bash
./build.sh build
```
Creates the standalone executable in `docker-build-output/`

### Build Docker image only
```bash
./build.sh build-image
```
Builds the Docker image without creating the executable

### Run tests
```bash
./build.sh test
```
Runs the test suite in the Docker container

### Interactive shell
```bash
./build.sh shell
```
Opens a bash shell inside the container for debugging

### Clean build artifacts
```bash
./build.sh clean
```
Removes all build outputs and cache

### Full rebuild
```bash
./build.sh rebuild
```
Cleans everything, rebuilds the image, and creates a new executable

## Using Docker Compose

Alternative way to build using docker-compose:

```bash
# Build the executable
docker-compose run builder

# Run tests
docker-compose run tester

# Interactive shell
docker-compose run dev
```

## Build Environment Details

The Docker container includes:
- Ubuntu 22.04 LTS base
- Python 3.12 from deadsnakes PPA
- PySide6 6.7+ with all Qt dependencies
- Nuitka 2.7.11 compiler
- All required system libraries (Qt, OpenGL, X11, etc.)
- Build tools (gcc, cmake, patchelf, ccache)

## Output Structure

After a successful build, the output directory contains:

```
docker-build-output/
└── ViloxTerm.dist/
    ├── main.bin          # The executable
    ├── *.so              # Required shared libraries
    ├── PySide6/          # Qt/PySide6 files
    ├── resources/        # Application resources
    ├── ui/               # UI assets
    └── deploy/           # Deployment icons
```

## Troubleshooting

### Docker not running
```
Error: Docker daemon is not running
```
Solution: Start Docker Desktop or the Docker service

### Permission denied
```
Error: Permission denied while trying to connect to Docker
```
Solution: Add your user to the docker group:
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Build fails with missing libraries
The Dockerfile includes all known dependencies. If you encounter missing libraries, please report them.

### Executable doesn't run
Ensure all files in `ViloxTerm.dist/` are present when distributing. The executable needs all accompanying files.

## Architecture

The build process:
1. Mounts the source code read-only into the container
2. Copies source to a build directory
3. Compiles Qt resources (`.qrc` files)
4. Runs `pyside6-deploy` to create the executable
5. Falls back to direct Nuitka compilation if needed
6. Copies the result to the output directory

## Customization

### Modifying the build
Edit `entrypoint.sh` to change build parameters or add steps.

### Adding dependencies
Edit `Dockerfile` to add system packages or Python packages.

### Changing Nuitka options
Edit the `extra_args` in `pysidedeploy.spec` or the fallback command in `entrypoint.sh`.

## CI/CD Integration

The Docker build can be integrated into CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Build executable
  run: |
    cd builder
    ./build.sh build

- name: Upload artifact
  uses: actions/upload-artifact@v3
  with:
    name: viloxterm-linux
    path: docker-build-output/ViloxTerm.dist/
```

## Notes

- The build uses ccache for faster rebuilds
- The source is mounted read-only to prevent accidental modifications
- Build artifacts are isolated in the container
- The image is about 2GB due to Qt and Python dependencies