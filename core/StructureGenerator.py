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

    def get_active_palettes(self, x_coord, palettes_config):
        mode = palettes_config.get("mode", "simple")

        if mode == "simple":
            return [(palettes_config.get("palette", palettes_config), 1.0)]

        adv_palettes = palettes_config.get("palettes", [])
        if not adv_palettes:
            return []

        loop = palettes_config.get("loop", False)

        # Construct timeline
        timeline = [] # list of (start_x, end_x, type, pal1, pal2)
        current_x = 0

        for i, p in enumerate(adv_palettes):
            trans_w = p.get("transition_width", 0)
            length = p.get("length", 50)

            # Transition phase
            if trans_w > 0:
                if i == 0:
                    if loop:
                        prev_pal = adv_palettes[-1]["palette"]
                    else:
                        prev_pal = p["palette"] # Should be 0 trans width anyway if not looping
                else:
                    prev_pal = adv_palettes[i-1]["palette"]

                timeline.append((current_x, current_x + trans_w, "transition", prev_pal, p["palette"]))
                current_x += trans_w

            # Solid phase
            timeline.append((current_x, current_x + length, "solid", p["palette"], None))
            current_x += length

        cycle_length = current_x

        if cycle_length == 0:
            return [(adv_palettes[-1]["palette"], 1.0)]

        if loop:
            x_coord = x_coord % cycle_length
        else:
            if x_coord >= cycle_length:
                return [(adv_palettes[-1]["palette"], 1.0)]

        # Find which region we are in
        for region in timeline:
            start_x, end_x, r_type, p1, p2 = region
            if start_x <= x_coord < end_x:
                if r_type == "solid":
                    return [(p1, 1.0)]
                else:
                    trans_w = end_x - start_x
                    progress = (x_coord - start_x) / trans_w
                    return [(p1, 1.0 - progress), (p2, progress)]

        return [(adv_palettes[-1]["palette"], 1.0)]

    def apply_decoration(self):
        """Applies distance-based floor and random top decorations to the generated structure."""
        if not self.palettes or not any(self.palettes.values()):
            return

        import random
        from collections import deque

        if not self.global_data.blocks:
            return

        if "Layout1" in self.layout_type:
            pass

        mode = self.palettes.get("mode", "simple")

        # Get max dist across all palettes to know how far to BFS
        max_dist = 0
        if mode == "advanced":
            for p in self.palettes.get("palettes", []):
                pal = p.get("palette", {})
                bands = pal.get("distance_bands", [])
                if bands:
                    m = max([b.get("max_distance", 0) for b in bands])
                    if m > max_dist: max_dist = m
        else:
            pal = self.palettes.get("palette", self.palettes)
            bands = pal.get("distance_bands", [])
            if bands:
                max_dist = max([b.get("max_distance", 0) for b in bands])

        if max_dist == 0:
            return

        # Get all base blocks (x, z) and their tick
        occupied_positions = set()
        base_blocks = {} # (x, z) -> min_tick
        redstone_positions = set()

        for block in self.global_data.blocks:
            x, y, z = block['pos']
            occupied_positions.add((x, y, z))
            coord = (x, z)
            tick = block['metadata'].get('tick', 0)
            if coord not in base_blocks or tick < base_blocks[coord]:
                base_blocks[coord] = tick

            if block['block_name'] == "minecraft:redstone_wire":
                redstone_positions.add(coord)

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

        def parse_block_and_props(block_str):
            if "[" in block_str and block_str.endswith("]"):
                parts = block_str.split("[", 1)
                b_name = parts[0]
                props_str = parts[1][:-1]
                props = {}
                if props_str:
                    for kv in props_str.split(","):
                        if "=" in kv:
                            k, v = kv.split("=", 1)
                            props[k.strip()] = v.strip()
                return b_name, props
            return block_str, {}

        data_deco = Brick()

        for (x, z), (dist, tick) in visited.items():
            active_pals = self.get_active_palettes(x, self.palettes)
            if not active_pals:
                continue

            # Randomly pick a palette if in transition
            r = random.random()
            current_weight = 0
            chosen_pal = active_pals[-1][0] # Default to last
            for pal, prob in active_pals:
                current_weight += prob
                if r <= current_weight:
                    chosen_pal = pal
                    break

            distance_bands = chosen_pal.get("distance_bands", [])
            redstone_band = chosen_pal.get("redstone_band", None)
            y_offset = chosen_pal.get("y_offset", 0)

            # Sort just in case
            distance_bands.sort(key=lambda b: b["max_distance"])

            selected_band = None

            # Check for redstone adjacency first
            is_redstone_adjacent = False
            if redstone_band and redstone_band.get("enabled", False):
                for dx, dz in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    if (x + dx, z + dz) in redstone_positions:
                        is_redstone_adjacent = True
                        break

                if is_redstone_adjacent:
                    selected_band = redstone_band

            if not selected_band:
                for band in distance_bands:
                    if dist <= band["max_distance"]:
                        selected_band = band
                        break

            if not selected_band:
                continue

            floor_block_str = pick_block(selected_band.get("blocks", {}))
            if floor_block_str and floor_block_str != "minecraft:air":
                if (x, -1 - y_offset, z) not in occupied_positions:
                    floor_name, floor_props = parse_block_and_props(floor_block_str)
                    data_deco.add_block(x, -1 - y_offset, z, floor_name, properties=floor_props, tick=tick)

            # Top decor (y = 0)
            top_decor = selected_band.get("top_decor", {})
            if top_decor and "blocks" in top_decor and top_decor.get("probability", 0) > 0:
                if random.random() < top_decor["probability"]:
                    top_block_str = pick_block(top_decor["blocks"])
                    if top_block_str and top_block_str != "minecraft:air":
                        if (x, 0 - y_offset, z) not in occupied_positions:
                            top_name, top_props = parse_block_and_props(top_block_str)
                            data_deco.add_block(x, 0 - y_offset, z, top_name, properties=top_props, tick=tick, needs_down=True)

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
