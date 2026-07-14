import numpy as np
from core.customNBT import CustomNBT
from core.brick import Brick
from core.Layout1 import Layout1Track,Layout1CompleteTrack
from core.Layout2 import Layout2Track

class StructureGenerator:
    """
    Generates NBT files from processed MusicData.
    Supports different layouts and output modes (Monolithic vs. Mini-NBT parts).
    """
    def __init__(self, processed_data, layout_type="Layout2", palettes=None):
        self.df_notes = processed_data
        self.layout_type = layout_type
        self.global_data = Brick()
        self.palettes = palettes or {}

    def generate_blocks(self):
        """Processes notes and maps them to a global Brick structure using the selected layout track."""
        if "Layout1" in self.layout_type:
            track = Layout1CompleteTrack()
        else:
            track = Layout2Track()

        track.build_sequence(self.df_notes)
        self.global_data = track

        # Before decoration, we must resolve all 'needs_down' constraints
        # using a default floor block, e.g. stone or wood if specified
        if self.palettes and self.palettes.get('floor'):
            floor_block_name = f"minecraft:{self.palettes['floor'][0]}"
        else:
            floor_block_name = "minecraft:stone"

        self.global_data.clean(floor_block_name)

        # Temporary debugging request: disable decorations
        # self.apply_decoration()

    def apply_decoration(self):
        """Applies floor, ceiling, and random decorations to the generated structure based on palettes."""
        if not self.palettes or not any(self.palettes.values()):
            return

        import random

        if not self.global_data.blocks:
            return

        xs = [b['pos'][0] for b in self.global_data.blocks]
        zs = [b['pos'][2] for b in self.global_data.blocks]

        min_x = min(xs) - 3
        max_x = max(xs) + 3
        min_z = min(zs) - 3
        max_z = max(zs) + 3

        data_deco = Brick()

        floor_blocks = [f"minecraft:{b}" for b in self.palettes.get('floor', [])]
        ceiling_blocks = [f"minecraft:{b}" for b in self.palettes.get('ceiling', [])]
        flowers = [f"minecraft:{b}" for b in self.palettes.get('flowers', [])]

        def rand_block(blocks, prob_nothing=0.0):
            if not blocks or random.random() < prob_nothing:
                return "minecraft:air"
            return random.choice(blocks)

        for i in range(min_x, max_x + 1):
            for k in range(min_z, max_z + 1):
                # Floor
                if floor_blocks:
                    data_deco.add_block(i, -2, k, rand_block(floor_blocks), random_delay_range=5)
                    data_deco.add_block(i, -1, k, rand_block(floor_blocks), random_delay_range=5)

                # Flowers (sparse)
                if flowers and random.random() > 0.8:
                    data_deco.add_block(i, 0, k, rand_block(flowers), needs_down=True)

                # Ceiling / Lanterns (sparse grid)
                if ceiling_blocks and (i % 4 == 0 and k % 4 == 0):
                    data_deco.add_block(i, 4, k, rand_block(ceiling_blocks))

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
