# ViloxTerm Build Container
# Based on Ubuntu 22.04 LTS for stability and compatibility
FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Build essentials
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    # Compression libraries
    zlib1g-dev \
    # Python 3.12
    software-properties-common \
    curl \
    wget \
    # Qt/PySide6 dependencies
    libgl1-mesa-dev \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xinerama0 \
    libxcb-xfixes0 \
    # Additional Qt dependencies
    libfontconfig1 \
    libfreetype6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxi6 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    libxcb-glx0 \
    # Tools for icon generation
    imagemagick \
    librsvg2-bin \
    icnsutils \
    # Git for version control
    git \
    # Compression tools
    upx-ucl \
    # Required for Nuitka
    patchelf \
    ccache \
    # AppImage tools
    file \
    fuse \
    desktop-file-utils \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Download and install AppImage tools
RUN wget -q https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage -O /usr/local/bin/linuxdeploy && \
    chmod +x /usr/local/bin/linuxdeploy && \
    cd /usr/local/bin && \
    ./linuxdeploy --appimage-extract && \
    mv squashfs-root linuxdeploy-extracted && \
    ln -sf /usr/local/bin/linuxdeploy-extracted/AppRun /usr/local/bin/linuxdeploy && \
    wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage -O /usr/local/bin/appimagetool && \
    chmod +x /usr/local/bin/appimagetool && \
    cd /usr/local/bin && \
    ./appimagetool --appimage-extract && \
    mv squashfs-root appimagetool-extracted && \
    ln -sf /usr/local/bin/appimagetool-extracted/AppRun /usr/local/bin/appimagetool

# Install Python 3.12 from deadsnakes PPA
RUN add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y python3.12 python3.12-dev python3.12-venv && \
    rm -rf /var/lib/apt/lists/*

# Set Python 3.12 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 && \
    update-alternatives --set python3 /usr/bin/python3.12

# Install pip for Python 3.12
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

# Create build user (non-root)
RUN useradd -m -s /bin/bash builder && \
    mkdir -p /workspace /build /output && \
    chown -R builder:builder /workspace /build /output

# Set up ccache for faster rebuilds
RUN mkdir -p /ccache && \
    chown -R builder:builder /ccache
ENV CCACHE_DIR=/ccache
ENV PATH="/usr/lib/ccache:${PATH}"

# Switch to builder user
USER builder
WORKDIR /workspace

# Create Python virtual environment
RUN python3.12 -m venv /home/builder/venv
ENV PATH="/home/builder/venv/bin:${PATH}"
ENV VIRTUAL_ENV="/home/builder/venv"

# Upgrade pip and install wheel
RUN pip install --upgrade pip setuptools wheel

# Install Python build dependencies
# These are installed in the venv to ensure consistency
RUN pip install \
    # Core GUI Framework
    PySide6>=6.7.0 \
    # Build tools
    Nuitka==2.7.11 \
    patchelf \
    # Terminal Dependencies
    flask>=2.0.0 \
    flask-socketio>=5.0.0 \
    python-socketio>=5.0.0 \
    python-engineio>=4.0.0 \
    simple-websocket>=1.0.0 \
    # Development tools
    black>=24.0.0 \
    ruff>=0.3.0 \
    mypy>=1.8.0 \
    # Testing (optional, but useful for CI)
    pytest>=8.0.0 \
    pytest-qt>=4.4.0 \
    pytest-cov>=4.1.0

# Set up entrypoint script
COPY --chown=builder:builder entrypoint.sh /home/builder/entrypoint.sh
RUN chmod +x /home/builder/entrypoint.sh

# Default command
ENTRYPOINT ["/home/builder/entrypoint.sh"]
CMD ["build"]