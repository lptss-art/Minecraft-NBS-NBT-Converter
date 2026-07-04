import numpy as np
from core.customNBT import CustomNBT
from core.data import Data
from core.Layout1 import Layout1
from core.Layout2 import Layout2

class StructureGenerator:
    """
    Generates NBT files from processed MusicData.
    Supports different layouts and output modes (Monolithic vs. Mini-NBT parts).
    """
    def __init__(self, processed_data, nbt_template, layout_type="Layout2", palettes=None):
        self.df_notes = processed_data
        self.nbt_template = nbt_template
        self.layout_type = layout_type
        self.global_data = Data()
        self.palettes = palettes or {}

    def generate_blocks(self):
        """Processes notes and maps them to a global Data array using the selected layout."""
        self.global_data = Data()
        last_tick = -1
        direction = 0
        pos = [1, 0, 0]

        for tick in self.df_notes.index:
            tick_diff = int(tick - last_tick)

            # Instantiate the chosen layout
            if "Layout1" in self.layout_type:
                layout = Layout1(nbt=self.nbt_template)
            else:
                layout = Layout2(nbt=self.nbt_template)

            layout.tick = int(last_tick)

            # Get notes for this tick
            notes_entier = self.df_notes.loc[tick]['note entier']
            notes_demi = self.df_notes.loc[tick]['note demi']

            # Basic serpentine logic (can be expanded for straight Minecart logic)
            if "Layout2" in self.layout_type:
                if direction % 4 == 0:
                    layout.add(tick_diff, notes_entier, notes_demi, is_symmetric=True)
                    pos[0] += 1
                    pos[2] += -2
                elif direction % 4 == 1:
                    layout.add(tick_diff, notes_entier, notes_demi)
                    layout.flip()
                    layout.rotate(-1)
                    pos[0] += 2
                    pos[2] += -1
                elif direction % 4 == 2:
                    layout.add(tick_diff, notes_entier, notes_demi, is_symmetric=True)
                    layout.flip()
                    pos[0] += 1
                    pos[2] += 2
                else:
                    layout.add(tick_diff, notes_entier, notes_demi)
                    layout.rotate(1)
                    pos[0] += 2
                    pos[2] += 1
                direction += 1
            else:
                # Layout1 (Minecart) just goes straight
                layout.add(tick_diff, notes_entier, notes_demi)
                pos[0] += 1

            # Shift layout data into global position and merge
            layout.data.position = [pos[0], pos[1], pos[2]]
            self.global_data.add_data(layout.data)
            last_tick = tick

        self.apply_decoration()

    def apply_decoration(self):
        """Applies floor, ceiling, and random decorations to the generated structure based on palettes."""
        if not self.palettes or not any(self.palettes.values()):
            return

        import random

        # Determine the bounding box of the generated structure
        sX, sY, sZ = self.global_data.shape
        if sX == 0 or sZ == 0:
            return

        min_x, max_x = 0, 0
        min_z, max_z = 0, 0

        # We need to find the actual min/max indices where blocks exist
        for i in range(sX):
            for k in range(sZ):
                if np.any(self.global_data.data[i - sX//2, :, k - sZ//2]['f0']):
                    min_x = min(min_x, i - sX//2)
                    max_x = max(max_x, i - sX//2)
                    min_z = min(min_z, k - sZ//2)
                    max_z = max(max_z, k - sZ//2)

        # Add some padding
        min_x -= 3
        max_x += 3
        min_z -= 3
        max_z += 3

        data_deco = Data()

        floor_blocks = self.palettes.get('floor', [])
        ceiling_blocks = self.palettes.get('ceiling', [])
        flowers = self.palettes.get('flowers', [])

        # Pre-calculate NBT indices
        floor_indices = [self.nbt_template.get_index_safe(b) for b in floor_blocks] if floor_blocks else []
        ceiling_indices = [self.nbt_template.get_index_safe(b) for b in ceiling_blocks] if ceiling_blocks else []
        flower_indices = [self.nbt_template.get_index_safe(b) for b in flowers] if flowers else []

        def rand_index(indices, prob_nothing=0.0):
            if not indices or random.random() < prob_nothing:
                return self.nbt_template.get_index_safe("minecraft:air")
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
        max_layer = int(np.max(self.global_data.data['f4'])) if self.global_data.data.size > 0 else 0
        nb_layers = max_layer + 1

        layouts = [Data() for _ in range(nb_layers)]
        for i in range(nb_layers):
            layouts[i].reshape(0, 0, self.global_data.shape[2] - 1)

        offsets = [None] * nb_layers
        offset_y = -10
        offset_z = 0

        sX, sY, sZ = self.global_data.shape
        for i in range(sX):
            for j in range(sY):
                for k in range(sZ):
                    i2 = i - sX // 2
                    j2 = j - sY // 2
                    k2 = k - sZ // 2

                    cell = self.global_data.data[i2, j2, k2]
                    if cell['f0']:  # If block is present
                        layer = int(cell['f4'])
                        if offsets[layer] is None:
                            offsets[layer] = i2
                            layouts[layer].position = [0, 0, 0]

                        layouts[layer].add_block(
                            i2 - offsets[layer],
                            j2 - offset_y,
                            k2 - offset_z,
                            cell['f1'],
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
