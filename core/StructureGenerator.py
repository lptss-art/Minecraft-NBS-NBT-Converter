import numpy as np
from core.customNBT import CustomNBT
from core.brick import Brick
from core.Layout1 import Layout1Track,Layout1CompleteTrack
from core.Layout2 import Layout2Track
from core.Layout3 import Layout3Track

class StructureGenerator:
    """
    Generates NBT files from processed MusicData.
    Supports different layouts and output modes (Monolithic vs. Mini-NBT parts).
    """
    def __init__(self, processed_data, layout_type="Layout2", palettes=None, force_positive_coords=False, layout_params=None):
        self.df_notes = processed_data
        self.layout_type = layout_type
        self.global_data = Brick()
        self.palettes = palettes or {}
        self.force_positive_coords = force_positive_coords
        self.layout_params = layout_params or {}

    def generate_blocks(self, progress_callback=None):
        """Processes notes and maps them to a global Brick structure using the selected layout track."""
        if "Layout1" in self.layout_type:
            track = Layout1CompleteTrack()
        elif "Layout3" in self.layout_type:
            track = Layout3Track()
        else:
            track = Layout2Track()

        if "Layout3" in self.layout_type:
            track.build_sequence(self.df_notes, progress_callback=progress_callback, force_positive_coords=self.force_positive_coords, **self.layout_params)
        else:
            track.build_sequence(self.df_notes, progress_callback=progress_callback, **self.layout_params)
        self.global_data = track

        # Before decoration, we must resolve all 'needs_down' constraints
        # using a default floor block, e.g. stone or wood if specified
        # Determine floor block from layout parameters if provided, else use palette floor
        floor_block_name = None
        if "Layout1" in self.layout_type:
            floor_block_name = self.layout_params.get("l1_glass")
        elif "Layout2" in self.layout_type:
            floor_block_name = self.layout_params.get("l2_base")
        elif "Layout3" in self.layout_type:
            floor_block_name = self.layout_params.get("l3_base")

        if not floor_block_name:
            if self.palettes and self.palettes.get('floor'):
                floor_block_name = f"minecraft:{self.palettes['floor'][0]}"
            else:
                floor_block_name = "minecraft:stone"

        self.global_data.clean(floor_block_name)

        self.apply_decoration()

    def apply_decoration(self):
        """Applies distance-based floor and random top decorations to the generated structure."""
        if not self.palettes or not any(self.palettes.values()):
            return

        import random
        from collections import deque

        if not self.global_data.blocks:
            return

        # Old layout 1 can skip distance based logic or use it, let's allow it but the focus is 2 & 3.
        # It's generally fine for all, but user requested for layout 2 and 3.
        if "Layout1" in self.layout_type:
            # We can still apply it if we want, or fall back to an empty return if not requested.
            # But the prompt says "on va faire la logique pour les layout 2 et 3".
            # We'll just apply it universally since the logic relies on coordinates.
            pass

        # Parse palettes
        # Expected structure in palettes (updated for the new UI):
        # palettes = {
        #    "distance_bands": [
        #        {"max_distance": 5, "blocks": {"minecraft:stone": 80, "minecraft:andesite": 20}},
        #        {"max_distance": 15, "blocks": {"minecraft:grass_block": 100}}
        #    ],
        #    "top_decor": {"blocks": {"minecraft:poppy": 50, "minecraft:dandelion": 50}, "probability": 0.2},
        #    "ceiling": ["lantern"] # kept for backwards compatibility if needed, though we might just drop it.
        # }

        distance_bands = self.palettes.get("distance_bands", [])
        top_decor = self.palettes.get("top_decor", {})

        # Fallback to old behavior if distance bands are not defined but old ones are
        if not distance_bands and self.palettes.get('floor'):
            # Convert old format to new format
            blocks = {f"minecraft:{b}": 100/len(self.palettes['floor']) for b in self.palettes['floor']}
            distance_bands = [{"max_distance": 3, "blocks": blocks}]

        if not distance_bands:
            return

        # Max distance to explore
        max_dist = max([band["max_distance"] for band in distance_bands])

        # Get all base blocks (x, z) and their tick
        occupied_positions = set()
        base_blocks = {} # (x, z) -> min_tick

        for block in self.global_data.blocks:
            x, y, z = block['pos']
            occupied_positions.add((x, y, z))
            coord = (x, z)
            tick = block['metadata'].get('tick', 0)
            if coord not in base_blocks or tick < base_blocks[coord]:
                base_blocks[coord] = tick

        # Multi-source BFS for distances
        # Queue: ((x, z), distance, tick)
        queue = deque()
        visited = {} # (x, z) -> (distance, tick)

        for coord, tick in base_blocks.items():
            queue.append((coord, 0, tick))
            visited[coord] = (0, tick)

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]

        while queue:
            (cx, cz), dist, tick = queue.popleft()

            if dist >= max_dist:
                continue

            for dx, dz in directions:
                nx, nz = cx + dx, cz + dz
                ndist = dist + 1

                if (nx, nz) not in visited or visited[(nx, nz)][0] > ndist:
                    visited[(nx, nz)] = (ndist, tick)
                    queue.append(((nx, nz), ndist, tick))

        # We need a function to pick a block from a weight dict
        def pick_block(block_weights):
            if not block_weights:
                return "minecraft:air"
            total_weight = sum(block_weights.values())
            if total_weight <= 0:
                return "minecraft:air"
            rand_val = random.uniform(0, total_weight)
            current = 0
            for b, w in block_weights.items():
                current += w
                if rand_val <= current:
                    return b
            return list(block_weights.keys())[-1]

        # Sort bands by distance ascending
        distance_bands.sort(key=lambda x: x["max_distance"])

        data_deco = Brick()

        for (x, z), (dist, tick) in visited.items():
            # Find which band this cell belongs to
            selected_band = None
            for band in distance_bands:
                if dist <= band["max_distance"]:
                    selected_band = band
                    break

            if not selected_band:
                continue

            floor_block = pick_block(selected_band.get("blocks", {}))
            if floor_block and floor_block != "minecraft:air":
                # Ensure we don't overwrite any existing block at y = -1
                if (x, -1, z) not in occupied_positions:
                    data_deco.add_block(x, -1, z, floor_block, tick=tick)

            # Top decor (y = 0)
            if top_decor and "blocks" in top_decor and top_decor.get("probability", 0) > 0:
                if random.random() < top_decor["probability"]:
                    top_block = pick_block(top_decor["blocks"])
                    if top_block and top_block != "minecraft:air":
                        if (x, 0, z) not in occupied_positions:
                            data_deco.add_block(x, 0, z, top_block, tick=tick, needs_down=True)

        # Merge the generated track into the decoration
        data_deco.add_data(self.global_data)
        self.global_data = data_deco

    def export_monolithic(self, output_path):
        """Exports the entire structure as a single NBT file."""
        nbt_out = CustomNBT()
        self.global_data.write_nbt(nbt_out)
        nbt_out.write_file(output_path)

    def export_multipart(self, output_dir, prefix="song_part", tick_delay=28):
        """Exports the structure as multiple mini-NBTs with Structure Blocks."""
        import os
        prefix = prefix.lower()
        self.global_data.set_layers(5)

        # Determine number of layers
        max_layer = 0
        for block in self.global_data.blocks:
            max_layer = max(max_layer, block['metadata'].get('layer', 0))

        nb_layers = max_layer + 1

        layouts = [Brick() for _ in range(nb_layers)]

        offsets = [None] * nb_layers

        for block in self.global_data.blocks:
            layer = block['metadata'].get('layer', 0)
            x, y, z = block['pos']

            if offsets[layer] is None:
                offsets[layer] = x
                layouts[layer].position = [0, 0, 0]

            layouts[layer].add_block(
                x - offsets[layer],
                y,
                z,
                block['block_name'],
                properties=block.get('properties', {}),
                tick=0
            )

        # Export individual layer parts
        for i, layout in enumerate(layouts):
            nbt_part = CustomNBT()
            layout.write_nbt(nbt_part)
            nbt_part.write_file(os.path.join(output_dir, f"{prefix}_{i}.nbt"))

        # Create Master Structure (Base) connecting Structure Blocks
        nbt_base = CustomNBT()
        for i in range(len(layouts) * tick_delay):
            if i % tick_delay == 0:
                n_layout = int(i / tick_delay)
                offset = offsets[n_layout] if offsets[n_layout] is not None else 0

                # Place a Structure Block to load the part
                name = f"{prefix}_{n_layout}"
                # Base is at x=0, z=0. The parts offset along x based on the serpentine logic.
                nbt_base.add_structure_block([offset, 0, 0], name, 0, 0, 0)

        nbt_base.write_file(os.path.join(output_dir, "base_start.nbt"))
