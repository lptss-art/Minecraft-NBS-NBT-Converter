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
    def __init__(self, processed_data, nbt_template, layout_type="Layout2"):
        self.df_notes = processed_data
        self.nbt_template = nbt_template
        self.layout_type = layout_type
        self.global_data = Data()

    def generate_blocks(self):
        """Processes notes and maps them to a global Data array using the selected layout."""
        self.global_data = Data()
        last_tick = -1
        direction = 0
        pos = [1, 0, 0]

        for tick in self.df_notes.index:
            tick_diff = int(tick - last_tick)

            # Instantiate the chosen layout
            if self.layout_type == "Layout1 (Minecart)":
                layout = Layout1(nbt=self.nbt_template)
            else:
                layout = Layout2(nbt=self.nbt_template)

            layout.tick = int(last_tick)

            # Get notes for this tick
            notes_entier = self.df_notes.loc[tick]['note entier']
            notes_demi = self.df_notes.loc[tick]['note demi']

            # Basic serpentine logic (can be expanded for straight Minecart logic)
            if self.layout_type == "Layout2":
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
            # (In a full implementation, we offset layout.data based on `pos`)
            # For simplicity in this unified structure, we mock the global data merge
            self.global_data.add_data(layout.data)
            last_tick = tick

    def export_monolithic(self, output_path):
        """Exports the entire structure as a single NBT file."""
        nbt_out = CustomNBT()
        self.global_data.write_nbt(nbt_out)
        nbt_out.write_file(output_path)

    def export_multipart(self, output_dir, prefix="part", tick_delay=28):
        """Exports the structure as multiple mini-NBTs with Structure Blocks."""
        # Split self.global_data into layers based on 'layer' / tick_delay
        # Save each to output_dir/prefix_0.nbt, prefix_1.nbt, etc.
        # Save a master start.nbt
        # (Placeholder for the complex multi-part logic found in Notebooks)
        pass
