from PIL import Image, ImageDraw, ImageColor
import os
from pathlib import Path

def create_app_icon():
    # Base configuration
    SIZE = 1024
    SCALE = SIZE / 100.0
    
    # Colors
    COLOR_LEFT = "#27272A"
    COLOR_RIGHT = "#09090B"
    STOP_POS = 0.68  # Gradient stop
    
    # Create main image (RGBA)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 1. Create a mask for the shape
    # We want Outer Rect - Inner Rect
    # To do this cleanly with anti-aliasing, we draw into a mask image
    # Note: Pillow's rounded_rectangle supports variable radius, but let's stick to simple geometry
    
    mask = Image.new("L", (SIZE, SIZE), 0)
    mask_draw = ImageDraw.Draw(mask)
    
    # Outer Rounded Rect (White)
    outer_radius = 10 * SCALE
    mask_draw.rounded_rectangle(
        [(0, 0), (SIZE, SIZE)], 
        radius=outer_radius, 
        fill=255
    )
    
    # Inner Rounded Rect (Black - creates hole)
    inner_radius = 20 * SCALE
    inner_margin = 25 * SCALE
    inner_box = [
        (inner_margin, inner_margin),
        (SIZE - inner_margin, SIZE - inner_margin)
    ]
    mask_draw.rounded_rectangle(
        inner_box,
        radius=inner_radius,
        fill=0
    )
    
    # 2. Create the fill pattern (Gradient/Split)
    fill_img = Image.new("RGBA", (SIZE, SIZE), COLOR_RIGHT)
    fill_draw = ImageDraw.Draw(fill_img)
    
    # Draw left side color up to STOP_POS
    split_x = int(SIZE * STOP_POS)
    fill_draw.rectangle([(0, 0), (split_x, SIZE)], fill=COLOR_LEFT)
    
    # 3. Apply mask to fill pattern
    # The mask defines the alpha channel of the final image
    final_img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    final_img.paste(fill_img, mask=mask)
    
    # 4. Save ICO with multiple sizes
    resources_dir = Path("resources")
    resources_dir.mkdir(exist_ok=True)
    
    output_path = resources_dir / "VKMusicSaver.ico"
    
    # Windows standard icon sizes
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    
    print(f"Saving icon to {output_path}")
    final_img.save(
        output_path, 
        format="ICO", 
        sizes=sizes,
        append_images=[] # Pillow automatically generates lower sizes if not specified, but passing sizes explicitly via `sizes` param is correct for resizing or we can resize manually
    )
    
    # For better quality downscaling, let's manually resize to each target size
    # and pass them as appended images
    # Wait, Pillow's ICO save takes 'sizes' to declare WHICH sizes to save, 
    # but it resizes the main image automatically? 
    # Actually for best results, we should provide a list of images.
    
    icon_images = []
    # We keep the original 1024 as the largest or just use 256 as max for ICO standard
    # 256 is usually max for Windows ICO.
    
    # Resample
    for w, h in sizes:
        icon_images.append(final_img.resize((w, h), Image.Resampling.LANCZOS))

    # The first image is the one 'save' is called on, others are appended
    # However, saving as ICO usually takes the first image and additional images in 'append_images'
    # But wait, Pillow ICO plugin handles 'sizes' differently.
    # Let's use the robust way: save the largest one, and append others.
    
    base_icon = icon_images[0] # 256x256
    other_icons = icon_images[1:]
    
    base_icon.save(
        output_path,
        format="ICO",
        append_images=other_icons
    )
    print("Done.")

if __name__ == "__main__":
    create_app_icon()
