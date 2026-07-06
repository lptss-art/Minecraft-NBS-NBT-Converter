import os
import math
import random
from PIL import Image, ImageDraw

TILE_WIDTH = 64
TILE_HEIGHT = 32
BLOCK_Z_HEIGHT = 32

def draw_polygon(draw, points, fill, outline):
    draw.polygon(points, fill=fill, outline=outline)

def get_block_name_from_index(nbt_palette, index):
    try:
        entry = nbt_palette[index]
        return entry["Name"].value
    except:
        return "unknown"

def generate_cube_sprite(color_top, color_left, color_right, outline, name="stone", is_flat=False, alpha=255, height_ratio=1.0):
    img = Image.new('RGBA', (TILE_WIDTH, TILE_HEIGHT + int(BLOCK_Z_HEIGHT * height_ratio)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    w = TILE_WIDTH
    h = TILE_HEIGHT
    z = int(BLOCK_Z_HEIGHT * height_ratio)

    # Bottom center is (w/2, h + z)
    top_points = [
        (w/2, z),
        (w, h/2 + z),
        (w/2, h + z),
        (0, h/2 + z)
    ]

    if is_flat:
        # Flat like redstone wire, render at bottom of block space
        flat_points = [
            (w/2, z + h),
            (w*0.8, h/2 + z + h*0.2),
            (w/2, h + z + h*0.4),
            (w*0.2, h/2 + z + h*0.2)
        ]
        color_top = list(color_top)
        color_top[3] = alpha
        draw_polygon(draw, flat_points, fill=tuple(color_top), outline=outline)
        return img

    left_points = [
        (0, h/2 + z),
        (w/2, h + z),
        (w/2, h),
        (0, h/2)
    ]

    right_points = [
        (w/2, h + z),
        (w, h/2 + z),
        (w, h/2),
        (w/2, h)
    ]

    top_points = [(p[0], p[1] - z) for p in top_points]

    color_top_a = list(color_top)
    color_top_a[3] = alpha
    color_left_a = list(color_left)
    color_left_a[3] = alpha
    color_right_a = list(color_right)
    color_right_a[3] = alpha

    draw_polygon(draw, left_points, fill=tuple(color_left_a), outline=outline)
    draw_polygon(draw, right_points, fill=tuple(color_right_a), outline=outline)
    draw_polygon(draw, top_points, fill=tuple(color_top_a), outline=outline)

    # Texture details based on name
    if "oak_planks" in name or "instrument" in name:
        # Draw horizontal plank lines
        for i in range(1, 4):
            ly = h/2 + z - (i * z/4)
            ry = h/2 + z - (i * z/4)
            draw.line([(0, h/2 + ly - z), (w/2, h + ly - z)], fill=(80, 50, 20, 100), width=1)
            draw.line([(w/2, h + ry - z), (w, h/2 + ry - z)], fill=(80, 50, 20, 100), width=1)

    if "stone" in name and "redstone" not in name:
        # Draw noise
        for _ in range(20):
            rx = random.randint(0, w)
            ry = random.randint(0, int(h + z))
            draw.point((rx, ry), fill=(80, 80, 80, 50))

    if "note_block" in name:
        # Wooden border outline
        draw.line(left_points + [left_points[0]], fill=(80, 50, 20, 255), width=2)
        draw.line(right_points + [right_points[0]], fill=(80, 50, 20, 255), width=2)
        draw.line(top_points + [top_points[0]], fill=(80, 50, 20, 255), width=2)
        # Note dot
        draw.polygon([(w*0.25, h*0.75 + z*0.5), (w*0.35, h*0.8 + z*0.5), (w*0.35, h*0.8 + z*0.2), (w*0.25, h*0.75 + z*0.2)], fill=(40,40,40,255))
        draw.polygon([(w*0.75, h*0.75 + z*0.5), (w*0.65, h*0.8 + z*0.5), (w*0.65, h*0.8 + z*0.2), (w*0.75, h*0.75 + z*0.2)], fill=(40,40,40,255))

    if "repeater" in name:
        # Draw redstone torches on top
        draw.rectangle([w*0.3, z-h*0.5, w*0.35, z-h*0.2], fill=(200,0,0,255))
        draw.rectangle([w*0.6, z-h*0.2, w*0.65, z+h*0.1], fill=(200,0,0,255))

    return img

def get_sprite_for_block(name):
    # Default Stone
    c_top, c_left, c_right, outline = (120, 120, 120, 255), (100, 100, 100, 255), (80, 80, 80, 255), (60, 60, 60, 255)
    flat = False
    alpha = 255
    hr = 1.0

    if "redstone_wire" in name:
        c_top = (255, 0, 0, 255)
        flat = True
        alpha = 150
    elif "redstone_block" in name:
        c_top, c_left, c_right = (220, 0, 0, 255), (180, 0, 0, 255), (140, 0, 0, 255)
        outline = (100, 0, 0, 255)
    elif "oak_planks" in name or "instrument" in name:
        c_top, c_left, c_right = (160, 110, 50, 255), (140, 90, 40, 255), (120, 70, 30, 255)
        outline = (80, 50, 20, 255)
    elif "note_block" in name:
        c_top, c_left, c_right = (180, 130, 60, 255), (160, 110, 50, 255), (140, 90, 40, 255)
        outline = (80, 50, 20, 255)
    elif "sticky_piston" in name:
        # Green top, stone sides
        c_top = (100, 200, 100, 255)
        c_left, c_right = (100, 100, 100, 255), (80, 80, 80, 255)
        outline = (60, 60, 60, 255)
    elif "repeater" in name:
        c_top, c_left, c_right = (200, 200, 200, 255), (160, 160, 160, 255), (140, 140, 140, 255)
        hr = 0.2

    return generate_cube_sprite(c_top, c_left, c_right, outline, name=name, is_flat=flat, alpha=alpha, height_ratio=hr)

def render_data_to_image(data_blocks, nbt_palette=None, title="NBT Structure", output_path="output.png"):
    if not data_blocks:
        print(f"No blocks to render for {title}")
        return

    # To draw properly: sort by Y ascending, then X descending, then Z descending
    # X axis points "down-right" and Z axis points "down-left"
    sorted_blocks = sorted(data_blocks, key=lambda b: (b['pos'][1], -b['pos'][0], -b['pos'][2]))

    xs = [b['pos'][0] for b in sorted_blocks]
    ys = [b['pos'][1] for b in sorted_blocks]
    zs = [b['pos'][2] for b in sorted_blocks]

    def to_iso(x, y, z):
        iso_x = (x - z) * (TILE_WIDTH / 2)
        iso_y = (x + z) * (TILE_HEIGHT / 2) - (y * BLOCK_Z_HEIGHT)
        return iso_x, iso_y

    iso_coords = [to_iso(x, y, z) for x, y, z in zip(xs, ys, zs)]
    min_iso_x = min(c[0] for c in iso_coords)
    max_iso_x = max(c[0] for c in iso_coords)
    min_iso_y = min(c[1] for c in iso_coords)
    max_iso_y = max(c[1] for c in iso_coords)

    img_w = int(max_iso_x - min_iso_x + TILE_WIDTH * 2)
    img_h = int(max_iso_y - min_iso_y + TILE_HEIGHT * 2 + BLOCK_Z_HEIGHT * 2)

    img = Image.new('RGBA', (img_w, img_h), (255, 255, 255, 255))

    sprites = {}

    for block in sorted_blocks:
        x, y, z = block['pos']
        idx = block['index']
        name = get_block_name_from_index(nbt_palette, idx) if nbt_palette else "unknown"

        if "air" in name:
            continue

        if idx >= 0 and nbt_palette:
            if "stone" in name or "planks" in name or "glass" in name or "wool" in name or "clay" in name or "sand" in name or "block" in name or "ice" in name or "pumpkin" in name or "glowstone" in name:
                 if not ("redstone" in name or "piston" in name or "note" in name):
                    name = "instrument"

        if name not in sprites:
            sprites[name] = get_sprite_for_block(name)

        sprite = sprites[name]

        iso_x, iso_y = to_iso(x, y, z)

        draw_x = int(iso_x - min_iso_x + TILE_WIDTH / 2)
        draw_y = int(iso_y - min_iso_y + TILE_HEIGHT + BLOCK_Z_HEIGHT)

        # Transparent blocks (redstone) should paste with alpha
        img.paste(sprite, (draw_x, draw_y), sprite)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)
    print(f"Saved visualization to {output_path}")

def export_topdown_grid(data_blocks, nbt_palette=None, title="NBT Grid", csv_path="output.csv", img_path="output_grid.png"):
    """
    Exports a top-down view of the layout.
    Generates both a CSV matrix of [X, Z] pointing to stacked Y layers, and a rendered Image table.
    """
    import csv
    from collections import defaultdict
    from PIL import ImageFont

    if not data_blocks:
        return

    # Group blocks by X, Z
    grid = defaultdict(list)
    for block in data_blocks:
        x, y, z = block['pos']
        idx = block['index']
        name = get_block_name_from_index(nbt_palette, idx) if nbt_palette else "unknown"
        if "air" in name:
            continue

        # Clean up name for display
        display_name = name.replace("minecraft:", "")
        if "note_block" in display_name:
            display_name = "Note"
        elif "repeater" in display_name:
            display_name = "Rep"
        elif "redstone_wire" in display_name:
            display_name = "RedWire"
        elif "redstone_block" in display_name:
            display_name = "RedBlk"
        elif "sticky_piston" in display_name:
            display_name = "Piston"
        elif "oak_planks" in display_name:
            display_name = "Wood"
        elif "stone" in display_name:
            display_name = "Stone"

        grid[(x, z)].append((y, display_name))

    if not grid:
        return

    xs = [coord[0] for coord in grid.keys()]
    zs = [coord[1] for coord in grid.keys()]
    min_x, max_x = min(xs), max(xs)
    min_z, max_z = min(zs), max(zs)

    width = max_x - min_x + 1
    depth = max_z - min_z + 1

    # Format the cell texts
    matrix = [["" for _ in range(width)] for _ in range(depth)]
    for z in range(min_z, max_z + 1):
        for x in range(min_x, max_x + 1):
            cell_blocks = grid.get((x, z), [])
            if not cell_blocks:
                continue
            # Sort by Y ascending so floor is first, top is last
            cell_blocks.sort(key=lambda b: b[0])

            # Format: "Y:-1 Stone | Y:0 Rep"
            cell_text = "\n".join([f"Y:{y} {name}" for y, name in cell_blocks])
            matrix[z - min_z][x - min_x] = cell_text

    # 1. Export CSV
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, mode='w', newline='') as f:
        writer = csv.writer(f)
        # Header Row (X coordinates)
        header = ["Z \\ X"] + [str(x) for x in range(min_x, max_x + 1)]
        writer.writerow(header)
        for z_idx, row in enumerate(matrix):
            writer.writerow([str(min_z + z_idx)] + row)

    print(f"Saved CSV grid to {csv_path}")

    # 2. Export Image Table
    # Estimate sizes
    cell_w = 120
    cell_h = 80
    margin = 40

    img_w = width * cell_w + margin * 2
    img_h = depth * cell_h + margin * 2

    img = Image.new('RGB', (img_w, img_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Try loading a basic font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except IOError:
        font = ImageFont.load_default()

    # Draw Grid Lines
    for i in range(width + 1):
        x = margin + i * cell_w
        draw.line([(x, margin), (x, img_h - margin)], fill=(0,0,0), width=1)
    for i in range(depth + 1):
        y = margin + i * cell_h
        draw.line([(margin, y), (img_w - margin, y)], fill=(0,0,0), width=1)

    # Draw X Headers
    for i in range(width):
        x = margin + i * cell_w + cell_w/2 - 10
        draw.text((x, margin - 20), f"X:{min_x + i}", fill=(0,0,0), font=font)

    # Draw Z Headers
    for i in range(depth):
        y = margin + i * cell_h + cell_h/2 - 10
        draw.text((margin - 35, y), f"Z:{min_z + i}", fill=(0,0,0), font=font)

    # Fill cells
    for z_idx in range(depth):
        for x_idx in range(width):
            text = matrix[z_idx][x_idx]
            if text:
                px = margin + x_idx * cell_w + 5
                py = margin + z_idx * cell_h + 5
                draw.text((px, py), text, fill=(0,0,0), font=font)

    # Title
    draw.text((margin, margin - 35), title, fill=(0,0,200), font=font)

    os.makedirs(os.path.dirname(img_path), exist_ok=True)
    img.save(img_path)
    print(f"Saved Grid Image to {img_path}")
