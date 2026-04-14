from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError as exc:
    raise SystemExit(
        "Pillow is required for icon generation. Install it with: python -m pip install Pillow"
    ) from exc


def _vertical_gradient(width, height, top_rgb, bottom_rgb):
    gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)
    for y in range(height):
        t = y / max(height - 1, 1)
        r = int(top_rgb[0] + (bottom_rgb[0] - top_rgb[0]) * t)
        g = int(top_rgb[1] + (bottom_rgb[1] - top_rgb[1]) * t)
        b = int(top_rgb[2] + (bottom_rgb[2] - top_rgb[2]) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
    return gradient


def create_app_icon():
    size = 1024
    pad = 68
    corner = 240

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # Main glossy rounded tile.
    tile_mask = Image.new("L", (size, size), 0)
    tile_draw = ImageDraw.Draw(tile_mask)
    tile_draw.rounded_rectangle(
        [(pad, pad), (size - pad, size - pad)],
        radius=corner,
        fill=255,
    )

    tile = _vertical_gradient(size, size, (13, 27, 44), (10, 122, 47))

    # Top highlight for depth.
    highlight = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hdraw = ImageDraw.Draw(highlight)
    hdraw.ellipse(
        [(140, 100), (920, 600)],
        fill=(255, 255, 255, 56),
    )
    highlight = highlight.filter(ImageFilter.GaussianBlur(18))
    tile = Image.alpha_composite(tile, highlight)

    # Apply rounded shape.
    canvas.paste(tile, mask=tile_mask)

    draw = ImageDraw.Draw(canvas)

    # White inner ring for visual separation on dark taskbars.
    draw.rounded_rectangle(
        [(pad + 18, pad + 18), (size - pad - 18, size - pad - 18)],
        radius=corner - 24,
        outline=(255, 255, 255, 165),
        width=18,
    )

    # Music note glyph.
    note_white = (250, 252, 255, 255)
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.polygon(
        [(530, 290), (700, 250), (700, 620), (530, 665)],
        fill=(0, 0, 0, 120),
    )
    sdraw.ellipse([(445, 610), (605, 765)], fill=(0, 0, 0, 120))
    sdraw.ellipse([(620, 565), (770, 710)], fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    canvas = Image.alpha_composite(canvas, shadow)
    draw = ImageDraw.Draw(canvas)

    draw.polygon(
        [(510, 270), (680, 230), (680, 600), (510, 645)],
        fill=note_white,
    )
    draw.ellipse([(425, 590), (585, 745)], fill=note_white)
    draw.ellipse([(600, 545), (750, 690)], fill=note_white)

    # Neon wave on the left to hint "signal/download".
    wave = [(250, 560), (310, 500), (370, 560), (430, 500), (490, 560)]
    draw.line(wave, fill=(130, 245, 176, 255), width=34, joint="curve")
    draw.line(wave, fill=(40, 105, 74, 210), width=10, joint="curve")

    resources_dir = Path("resources")
    resources_dir.mkdir(exist_ok=True)

    ico_path = resources_dir / "MusicSaver.ico"
    png_preview_path = resources_dir / "MusicSaver.icon.preview.png"

    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    resized = [canvas.resize((w, h), Image.Resampling.LANCZOS) for w, h in sizes]
    base, rest = resized[0], resized[1:]
    base.save(ico_path, format="ICO", append_images=rest)

    canvas.resize((512, 512), Image.Resampling.LANCZOS).save(png_preview_path, format="PNG")
    print(f"Icon generated: {ico_path}")
    print(f"Preview generated: {png_preview_path}")

if __name__ == "__main__":
    create_app_icon()
