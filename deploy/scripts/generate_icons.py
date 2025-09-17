#!/usr/bin/env python3
"""
Generate application icons from SVG source for all platforms.
Creates .ico (Windows), .icns (macOS), and .png (Linux) files.
"""

import subprocess
import sys
from pathlib import Path


def check_dependencies():
    """Check if required tools are installed."""
    tools = {
        "convert": "ImageMagick (install: apt-get install imagemagick)",
        "png2icns": "libicns (install: apt-get install icnsutils)",
        "rsvg-convert": "librsvg (install: apt-get install librsvg2-bin)",
    }

    missing = []
    for tool, install_info in tools.items():
        try:
            subprocess.run(["which", tool], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            missing.append(f"{tool} - {install_info}")

    if missing:
        print("Missing required tools:")
        for tool in missing:
            print(f"  - {tool}")
        print("\nInstall missing tools and try again.")
        return False
    return True


def generate_png_sizes(svg_path, output_dir):
    """Generate PNG files in various sizes."""
    sizes = [16, 24, 32, 48, 64, 128, 256, 512]
    png_files = []

    for size in sizes:
        output_path = output_dir / f"viloxterm_{size}x{size}.png"
        cmd = [
            "rsvg-convert",
            "-w",
            str(size),
            "-h",
            str(size),
            str(svg_path),
            "-o",
            str(output_path),
        ]

        try:
            subprocess.run(cmd, check=True)
            print(f"Generated: {output_path}")
            png_files.append(output_path)
        except subprocess.CalledProcessError as e:
            print(f"Failed to generate {size}x{size} PNG: {e}")
            return None

    return png_files


def generate_ico(png_files, output_path):
    """Generate Windows ICO file from PNG files."""
    # Use specific sizes for ICO
    ico_sizes = [16, 24, 32, 48, 256]
    ico_pngs = [
        p for p in png_files if any(f"_{s}x{s}.png" in str(p) for s in ico_sizes)
    ]

    cmd = ["convert"] + [str(p) for p in ico_pngs] + [str(output_path)]

    try:
        subprocess.run(cmd, check=True)
        print(f"Generated Windows icon: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to generate ICO: {e}")
        return False


def generate_icns(png_files, output_path):
    """Generate macOS ICNS file from PNG files."""
    # macOS expects specific sizes
    required_sizes = {
        16: "icon_16x16.png",
        32: "icon_32x32.png",
        128: "icon_128x128.png",
        256: "icon_256x256.png",
        512: "icon_512x512.png",
    }

    # Create temporary directory for ICNS generation
    temp_dir = Path(output_path).parent / "temp_icns"
    temp_dir.mkdir(exist_ok=True)

    # Copy and rename files
    for size, name in required_sizes.items():
        source = next((p for p in png_files if f"_{size}x{size}.png" in str(p)), None)
        if source:
            dest = temp_dir / name
            subprocess.run(["cp", str(source), str(dest)])

    # Generate ICNS
    cmd = ["png2icns", str(output_path)] + [
        str(temp_dir / name) for name in required_sizes.values()
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"Generated macOS icon: {output_path}")

        # Cleanup
        for file in temp_dir.glob("*.png"):
            file.unlink()
        temp_dir.rmdir()

        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to generate ICNS: {e}")
        return False


def main():
    """Main icon generation process."""
    # Check if we're in the right directory
    if not Path("deploy/icons/viloxterm.svg").exists():
        print("Error: Run this script from the project root directory")
        return 1

    # Check dependencies
    if not check_dependencies():
        print("\nNote: On Ubuntu/Debian, install all tools with:")
        print("  sudo apt-get install imagemagick librsvg2-bin icnsutils")
        return 1

    # Paths
    svg_path = Path("deploy/icons/viloxterm.svg")
    icons_dir = Path("deploy/icons")

    print("Generating application icons from SVG...")
    print("=" * 50)

    # Generate PNG files
    png_files = generate_png_sizes(svg_path, icons_dir)
    if not png_files:
        print("Failed to generate PNG files")
        return 1

    # Generate Windows ICO
    ico_path = icons_dir / "viloxterm.ico"
    if not generate_ico(png_files, ico_path):
        print("Warning: Failed to generate Windows ICO")

    # Generate macOS ICNS
    icns_path = icons_dir / "viloxterm.icns"
    if not generate_icns(png_files, icns_path):
        print("Warning: Failed to generate macOS ICNS")

    # Copy main PNG for Linux
    main_png = icons_dir / "viloxterm.png"
    subprocess.run(["cp", str(icons_dir / "viloxterm_256x256.png"), str(main_png)])
    print(f"Copied main PNG for Linux: {main_png}")

    print("\n" + "=" * 50)
    print("Icon generation complete!")
    print("\nGenerated files:")
    print(f"  - Windows: {ico_path}")
    print(f"  - macOS: {icns_path}")
    print(f"  - Linux: {main_png}")
    print(
        f"  - PNG sizes: {', '.join(f'{s}x{s}' for s in [16, 24, 32, 48, 64, 128, 256, 512])}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
