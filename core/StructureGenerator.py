import numpy as np
from core.customNBT import CustomNBT
from core.brick import Brick
from core.Layout1 import Layout1Track
from core.Layout2 import Layout2Track

class StructureGenerator:
    """
    Generates NBT files from processed MusicData.
    Supports different layouts and output modes (Monolithic vs. Mini-NBT parts).
    """
    def __init__(self, processed_data, nbt_template, layout_type="Layout2", palettes=None):
        self.df_notes = processed_data
        self.nbt_template = nbt_template
        self.layout_type = layout_type
        self.global_data = Brick()
        self.palettes = palettes or {}

    def generate_blocks(self):
        """Processes notes and maps them to a global Brick structure using the selected layout track."""
        if "Layout1" in self.layout_type:
            track = Layout1Track(nbt_template=self.nbt_template)
        else:
            track = Layout2Track(nbt_template=self.nbt_template)

        track.build_sequence(self.df_notes)
        self.global_data = track

        # Before decoration, we must resolve all 'needs_down' constraints
        # using a default floor block, e.g. stone or wood if specified
        if self.palettes and self.palettes.get('floor'):
            floor_index = self.nbt_template.get_index(f"minecraft:{self.palettes['floor'][0]}")
        else:
            floor_index = self.nbt_template.get_index_safe("minecraft:stone")

        self.global_data.clean(floor_index)

        self.apply_decoration()

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

        floor_blocks = self.palettes.get('floor', [])
        ceiling_blocks = self.palettes.get('ceiling', [])
        flowers = self.palettes.get('flowers', [])

        # Pre-calculate NBT indices
        floor_indices = [self.nbt_template.get_index(f"minecraft:{b}") for b in floor_blocks] if floor_blocks else []
        ceiling_indices = [self.nbt_template.get_index(f"minecraft:{b}") for b in ceiling_blocks] if ceiling_blocks else []
        flower_indices = [self.nbt_template.get_index(f"minecraft:{b}") for b in flowers] if flowers else []

        def rand_index(indices, prob_nothing=0.0):
            if not indices or random.random() < prob_nothing:
                return self.nbt_template.get_index("minecraft:air")
            return random.choice(indices)

        for i in range(min_x, max_x + 1):
            for k in range(min_z, max_z + 1):
                # Floor
                if floor_indices:
                    data_deco.add_block(i, -2, k, rand_index(floor_indices), random_delay_range=5)
                    data_deco.add_block(i, -1, k, rand_index(floor_indices), random_delay_range=5)

                # Flowers (sparse)
                if flower_indices and random.random() > 0.8:
                    data_deco.add_block(i, 0, k, rand_index(flower_indices), needs_down=True)

                # Ceiling / Lanterns (sparse grid)
                if ceiling_indices and (i % 4 == 0 and k % 4 == 0):
                    data_deco.add_block(i, 4, k, rand_index(ceiling_indices))

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
        self.global_data.set_layers(5)

        # Determine number of layers
        max_layer = 0
        for block in self.global_data.blocks:
            max_layer = max(max_layer, block['metadata'].get('layer', 0))

        nb_layers = max_layer + 1

        layouts = [Brick() for _ in range(nb_layers)]

        offsets = [None] * nb_layers
        offset_y = -10
        offset_z = 0

        for block in self.global_data.blocks:
            layer = block['metadata'].get('layer', 0)
            x, y, z = block['pos']

            if offsets[layer] is None:
                offsets[layer] = x
                layouts[layer].position = [0, 0, 0]

            layouts[layer].add_block(
                x - offsets[layer],
                y - offset_y,
                z - offset_z,
                block['index'],
                0
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
                nbt_base.add_structure_block([offset, 0, 0], f"minecraft:{name}", 0, 0, 0)

        nbt_base.write_file(os.path.join(output_dir, "base_start.nbt"))
