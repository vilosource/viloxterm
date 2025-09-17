#!/usr/bin/env python3
"""
Generate a simple application icon using PIL/Pillow.
Fallback when system tools are not available.
"""

import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow not installed. Installing...")
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'Pillow'])
    from PIL import Image, ImageDraw, ImageFont

def create_icon():
    """Create a simple ViloxTerm icon."""
    # Create base image
    size = 256
    img = Image.new('RGBA', (size, size), (30, 30, 30, 255))  # Dark background
    draw = ImageDraw.Draw(img)

    # Draw rounded rectangle background
    padding = 20
    draw.rounded_rectangle(
        [padding, padding, size - padding, size - padding],
        radius=20,
        fill=(30, 30, 30, 255),
        outline=(0, 255, 0, 255),  # Green border
        width=3
    )

    # Draw terminal prompt symbol (>)
    prompt_x = 50
    prompt_y = size // 2 - 30
    draw.polygon([
        (prompt_x, prompt_y),
        (prompt_x + 40, prompt_y + 20),
        (prompt_x, prompt_y + 40),
        (prompt_x + 10, prompt_y + 20)
    ], fill=(0, 255, 0, 255))

    # Draw text lines (simulating terminal output)
    line_y = prompt_y + 10
    for i, width in enumerate([80, 100, 70, 90]):
        draw.rectangle(
            [prompt_x + 60, line_y + i * 20, prompt_x + 60 + width, line_y + i * 20 + 8],
            fill=(255, 255, 255, 150) if i > 0 else (0, 255, 0, 200)
        )

    # Draw VT text
    try:
        # Try to use a monospace font
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf", 48)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    text = "VT"
    # Get text bounding box for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    bbox[3] - bbox[1]
    text_x = (size - text_width) // 2
    text_y = size - 80

    draw.text((text_x, text_y), text, fill=(0, 255, 0, 255), font=font)

    return img

def save_multiple_sizes(img, base_path):
    """Save icon in multiple sizes."""
    sizes = [16, 24, 32, 48, 64, 128, 256]
    paths = []

    for size in sizes:
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        path = base_path.parent / f"viloxterm_{size}x{size}.png"
        resized.save(path, 'PNG')
        print(f"Saved: {path}")
        paths.append(path)

    return paths

def create_ico(img, ico_path):
    """Create Windows ICO file."""
    # ICO can contain multiple sizes
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (256, 256)]
    imgs = []

    for size in sizes:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        imgs.append(resized)

    # Save as ICO
    imgs[0].save(
        ico_path,
        format='ICO',
        sizes=sizes,
        append_images=imgs[1:]
    )
    print(f"Saved Windows ICO: {ico_path}")

def main():
    """Main icon generation."""
    icons_dir = Path('deploy/icons')
    if not icons_dir.exists():
        print("Error: Run from project root directory")
        return 1

    print("Generating ViloxTerm icons...")
    print("=" * 50)

    # Create base icon
    img = create_icon()

    # Save main PNG
    main_png = icons_dir / 'viloxterm.png'
    img.save(main_png, 'PNG')
    print(f"Saved main PNG: {main_png}")

    # Save multiple sizes
    save_multiple_sizes(img, main_png)

    # Create Windows ICO
    try:
        ico_path = icons_dir / 'viloxterm.ico'
        create_ico(img, ico_path)
    except Exception as e:
        print(f"Warning: Could not create ICO: {e}")

    print("\n" + "=" * 50)
    print("Icon generation complete!")
    print("\nNote: For production, consider using professional tools to generate")
    print("platform-specific icons (ICO for Windows, ICNS for macOS).")

    return 0

if __name__ == '__main__':
    sys.exit(main())
