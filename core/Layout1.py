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
        else:
            self.index_stone = -1
            self.index_redstone = -1
            self.index_piston = -1
            self.index_redstone_block = -1
            self.index_rail = -1
            self.index_detector = -1
            self.offset_notes = -1
            self.offset_instr = -1
            self.index_air = -1

    def add(self, tick_delay, notes_integer=None, notes_half=None, is_symmetric=False):
        """
        Adds a single tick's worth of blocks for the Minecart layout.
        Note: The actual logic in the notebook separates 'redstone line' and 'cart line'.
        For now, this mimics the basic note addition based on offsets to integrate with
        a generator.
        """
        sym = is_symmetric
        if notes_integer is None:
            notes_integer = []
        if notes_half is None:
            notes_half = []

        # This logic is adapted to fit the 'data' approach, although the original
        # heavily relied on direct NBT writes. Here we prepare the standard structure
        # (similar to Layout2) but with the spatial arrangement of Layout1.

        # This was an old placeholder for a stacking logic that doesn't match
        # the user's flat rail expectation. We will mirror the layout 2 geometric progression,
        # but optimized for a straight line with rails, keeping Y=0 the rail line and notes on the side.

        integer_note_count = len(notes_integer)
        half_note_count = len(notes_half)

        # Piston side logic (half ticks) - extending laterally along the straight rail
        if notes_half:
            if half_note_count >= 1:
                self.add_note(1, 0, 0, notes_half[0])
            if half_note_count >= 2:
                self.add_note(0, 0, -1, notes_half[1])
            if half_note_count >= 3:
                self.add_note(0, 0, 1, notes_half[2])
            if half_note_count >= 4:
                self._roll(1)
                self.add_block(0, 0, 0, self.index_redstone, needs_down=True)
                self.add_note(1, 0, 0, notes_half[3])
            if half_note_count >= 5:
                self.add_note(0, -1, 1, notes_half[4])
            if half_note_count >= 6:
                self.add_note(0, -1, -1, notes_half[5])
            if half_note_count >= 7:
                self._roll(1)
                self.add_block(0, 0, 0, self.index_redstone, needs_down=True)
                self.add_note(0, -1, 1, notes_half[6])
            if half_note_count >= 8:
                self.add_note(0, -1, -1, notes_half[7])

            if half_note_count >= 4:
                self._roll(1)

            self._roll(2)
            self.add_block(0, 0, 0, self.index_piston)
            self.add_block(1, 0, 0, self.index_redstone_block)

            self._roll(1)

        # Integer tick notes
        if integer_note_count > 5 or (integer_note_count > 4 and half_note_count != 0):
            offset_notes_integer = 1 if sym else 0

            self.add_block(0, 0, 0, self.index_redstone, needs_down=True)

            if integer_note_count >= 4 + offset_notes_integer:
                self.add_note(0, -1, -1, notes_integer[3 + offset_notes_integer])
            if integer_note_count >= 5 + offset_notes_integer:
                self.add_note(0, -1, 1, notes_integer[4 + offset_notes_integer])
            if integer_note_count >= 6 + offset_notes_integer:
                self._roll(1)
                self.add_block(0, 0, 0, self.index_redstone, needs_down=True)
                self.add_note(0, -1, -1, notes_integer[5 + offset_notes_integer])
            if integer_note_count >= 7 + offset_notes_integer:
                self.add_note(0, -1, 1, notes_integer[6 + offset_notes_integer])
            if integer_note_count >= 8 + offset_notes_integer:
                self._roll(1)
                self.add_block(0, 0, 0, self.index_redstone, needs_down=True)
                self.add_note(0, -1, -1, notes_integer[7 + offset_notes_integer])
            if integer_note_count >= 9 + offset_notes_integer:
                self.add_note(0, -1, 1, notes_integer[8 + offset_notes_integer])

            self._roll(1)

        if sym:
            self.rotate(1)
        self._roll(1)

        # Redstone side notes around the rail
        if half_note_count == 0 and integer_note_count <= 5:
            if integer_note_count >= 2:
                self.add_note(1, 0, 1, notes_integer[1])
            if integer_note_count >= 3:
                self.add_note(2, 0, 0, notes_integer[2])
            if integer_note_count >= 4:
                self.add_note(0, -1, -1, notes_integer[3])
            if integer_note_count >= 5:
                self.add_note(2, -1, -1, notes_integer[4])
        elif half_note_count == 1 and integer_note_count <= 4:
            if integer_note_count >= 2 and not sym:
                self.add_note(1, 0, 1, notes_integer[1])
            if integer_note_count >= 2 and sym:
                self.add_note(2, 0, 0, notes_integer[1])
            if integer_note_count >= 3:
                self.add_note(0, -1, -1, notes_integer[2])
            if integer_note_count >= 4:
                self.add_note(2, -1, -1, notes_integer[3])
        else:
            if integer_note_count >= 2 and not sym:
                self.add_note(1, 0, 1, notes_integer[1])
            if integer_note_count >= 2 and sym:
                self.add_note(2, 0, 0, notes_integer[1])
            if integer_note_count >= 3:
                self.add_note(0, -1, -1, notes_integer[2])
            if integer_note_count >= 4 and sym:
                self.add_note(2, -1, -1, notes_integer[3])

        # Central block / rail logic
        block_type = self.index_rail if self.tick % 10 != 0 else self.index_detector

        self.add_block(0, 0, 0, block_type, needs_down=True)

        if integer_note_count >= 1:
            self.add_note(0, -1, 1, notes_integer[0])

        self.tick += 1

    def _roll(self, shift):
        for block in self.data.blocks:
            block['pos'][0] += shift

    def add_note(self, x, y, z, note):
        if not hasattr(note, 'note'):
            return
        # Instrument block
        self.data.add_block(x, y - 1, z, note.instr + self.offset_instr, self.tick, needs_down=True)
        # Note block
        self.data.add_block(x, y, z, note.note + self.offset_notes, self.tick)
        # Air block
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
