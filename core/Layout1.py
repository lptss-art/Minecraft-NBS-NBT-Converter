import numpy as np
from core.customNBT import CustomNBT
from core.data import Data

class Layout1:
    """
    Manages the older "Minecart" layout with stacked lanes and a central decoration.
    Extracted from the Nouveau Layout.ipynb notebook logic.
    """
    def __init__(self, nbt=None, start_x=0, start_y=0, start_z=0):
        self.start_x = start_x
        self.start_y = start_y
        self.start_z = start_z
        self.pos = [0, 0, 0]

        self.custom_nbt = nbt
        self.data = Data()
        self.tick = 0

        if nbt:
            self.index_stone = self.custom_nbt.get_index_safe("minecraft:stone")
            self.index_redstone = self.custom_nbt.get_index_safe("minecraft:redstone_wire")
            self.index_piston = self.custom_nbt.get_index_safe("minecraft:sticky_piston", {"facing": "up"})
            self.index_redstone_block = self.custom_nbt.get_index_safe("minecraft:redstone_block")
            self.index_rail = self.custom_nbt.get_index_safe("minecraft:powered_rail", {"shape": "east_west"})
            self.index_detector = self.custom_nbt.get_index_safe("minecraft:detector_rail", {"shape": "east_west"})
            self.offset_notes = self.custom_nbt.index_notes
            self.offset_instr = self.custom_nbt.index_instr
            self.index_air = self.custom_nbt.get_index_safe("minecraft:air")

    def add(self, tick_delay, notes_integer=None, notes_half=None, sym=False):
        """
        Adds a single tick's worth of blocks for the Minecart layout.
        Note: The actual logic in the notebook separates 'redstone line' and 'cart line'.
        For now, this mimics the basic note addition based on offsets to integrate with
        a generator.
        """
        if notes_integer is None:
            notes_integer = []
        if notes_half is None:
            notes_half = []

        # This logic is adapted to fit the 'data' approach, although the original
        # heavily relied on direct NBT writes. Here we prepare the standard structure
        # (similar to Layout2) but with the spatial arrangement of Layout1.

        # Example logic: stack notes vertically
        layer_offset = 0
        for i, note in enumerate(notes_integer):
            # Put note blocks on sides
            z_offset = 2 if i % 2 == 0 else -2
            y_offset = (i // 2) * 2
            self.add_note(0, y_offset, z_offset, note)

        for i, note in enumerate(notes_half):
            # Half notes can be added via pistons
            z_offset = 3 if i % 2 == 0 else -3
            y_offset = (i // 2) * 2

            # Piston pushing redstone block into note
            self.add_block(0, y_offset - 2, z_offset, self.index_piston)
            self.add_block(0, y_offset - 1, z_offset, self.index_redstone_block)
            self.add_note(0, y_offset, z_offset, note)

        # The center rail
        self.add_block(0, 0, 0, self.index_rail, needs_down=True)
        self.add_block(0, -1, 0, self.index_stone)

        self.tick += 1

    def add_note(self, x, y, z, note):
        if not hasattr(note, 'note'):
            return
        self.data.add_block(x, y, z, note.note + self.offset_notes, self.tick)
        self.data.add_block(x, y - 1, z, note.instr + self.offset_instr, self.tick)
        self.data.add_block(x, y + 1, z, self.index_air, self.tick)

    def add_block(self, x, y, z, index, random_delay_range=-1, needs_down=False, needs_up=False):
        if index == -1: return
        self.data.add_block(x, y, z, index, self.tick, random_delay_range=random_delay_range, needs_down=needs_down, needs_up=needs_up)

    def flip(self):
        self.data.flip(self.custom_nbt)

    def rotate(self, r):
        self.data.rotate(r, self.custom_nbt)

    def write_nbt(self):
        """Writes the layout data to the customNBT object."""
        self.data.write_nbt(self.custom_nbt)
