import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

# A basic map of block indices/names to colors for the visualizer
COLOR_MAP = {
    "minecraft:redstone_wire": (1.0, 0.0, 0.0, 0.5), # Translucent red
    "minecraft:redstone_block": (0.8, 0.0, 0.0, 0.9),
    "minecraft:stone": (0.5, 0.5, 0.5, 0.8),
    "minecraft:oak_planks": (0.6, 0.4, 0.2, 0.8),
    "minecraft:repeater": (0.9, 0.9, 0.9, 0.6),
    "minecraft:sticky_piston": (0.2, 0.8, 0.2, 0.8),
    "minecraft:note_block": (0.8, 0.6, 0.2, 0.9),
    "minecraft:air": (0, 0, 0, 0),
    # Default fallbacks
    "instrument": (0.4, 0.3, 0.1, 0.8),
    "default": (0.8, 0.8, 0.8, 0.3)
}

def get_block_name_from_index(nbt_palette, index):
    """Attempt to find the block name from the palette"""
    try:
        entry = nbt_palette[index]
        return entry["Name"].value
    except:
        return "unknown"

def render_data_to_image(data_blocks, nbt_palette=None, title="NBT Structure", output_path="output.png"):
    """
    Renders a 3D scatter/voxel plot of the blocks and saves it to output_path.
    """
    if not data_blocks:
        print(f"No blocks to render for {title}")
        return

    # Extract coordinates
    xs = [b['pos'][0] for b in data_blocks]
    ys = [b['pos'][1] for b in data_blocks]
    zs = [b['pos'][2] for b in data_blocks]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)

    size_x = max_x - min_x + 1
    size_y = max_y - min_y + 1
    size_z = max_z - min_z + 1

    # Create voxel grid
    voxels = np.zeros((size_x, size_y, size_z), dtype=bool)
    colors = np.empty(voxels.shape, dtype=object)

    for block in data_blocks:
        x = block['pos'][0] - min_x
        y = block['pos'][1] - min_y
        z = block['pos'][2] - min_z

        block_idx = block['index']
        name = get_block_name_from_index(nbt_palette, block_idx) if nbt_palette else "unknown"

        # Heuristics for instruments/notes if unknown
        color = COLOR_MAP.get(name, COLOR_MAP["default"])
        if block_idx >= 0 and nbt_palette:
            # Check if it's in the note block or instrument range
            if "note_block" in name:
                color = COLOR_MAP["minecraft:note_block"]
            elif "stone" in name or "planks" in name or "glass" in name or "wool" in name or "clay" in name or "sand" in name or "block" in name or "ice" in name or "pumpkin" in name or "glowstone" in name:
                 if not ("redstone" in name or "piston" in name):
                    color = COLOR_MAP["instrument"]

        if name == "minecraft:air":
            continue

        voxels[x, y, z] = True
        colors[x, y, z] = color

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    ax.voxels(voxels, facecolors=colors, edgecolor='k', linewidth=0.5)

    # Set labels and title
    ax.set_xlabel('X')
    ax.set_ylabel('Y (Vertical)')
    ax.set_zlabel('Z')
    ax.set_title(title)

    # Ensure proportional scaling
    max_range = np.array([size_x, size_y, size_z]).max()
    Xb = 0.5*max_range*np.mgrid[-1:2:2,-1:2:2,-1:2:2][0].flatten() + 0.5*(size_x)
    Yb = 0.5*max_range*np.mgrid[-1:2:2,-1:2:2,-1:2:2][1].flatten() + 0.5*(size_y)
    Zb = 0.5*max_range*np.mgrid[-1:2:2,-1:2:2,-1:2:2][2].flatten() + 0.5*(size_z)
    for xb, yb, zb in zip(Xb, Yb, Zb):
        ax.plot([xb], [yb], [zb], 'w')

    # Rotate for better isometric view
    ax.view_init(elev=30, azim=45)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved visualization to {output_path}")
