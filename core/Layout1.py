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
            self.index_wood = self.custom_nbt.get_index_safe("minecraft:oak_planks")
            self.index_redstone = self.custom_nbt.get_index("minecraft:redstone_wire", {'east': 'side', 'west': 'side'})
            self.index_piston = self.custom_nbt.index_pistons["east"]
            self.index_redstone_block = self.custom_nbt.get_index_safe("minecraft:redstone_block")
            self.index_repeater = self.custom_nbt.index_repeaters["west"]

            self.offset_notes = self.custom_nbt.index_notes
            self.offset_instr = self.custom_nbt.index_instr
            self.index_air = self.custom_nbt.get_index_safe("minecraft:air")
        else:
            self.index_stone = -1
            self.index_wood = -1
            self.index_redstone = -1
            self.index_piston = -1
            self.index_redstone_block = -1
            self.index_repeater = -1
            self.offset_notes = -1
            self.offset_instr = -1
            self.index_air = -1

    def add(self, tick_delay, notes_integer=None, notes_half=None, is_symmetric=False):
        """
        Adds a single tick's worth of blocks for the straight layout.
        Uses a straight redstone line: Repeater -> Block -> Repeater.
        Notes branch off sideways.
        """
        sym = is_symmetric
        if notes_integer is None:
            notes_integer = []
        if notes_half is None:
            notes_half = []

        integer_note_count = len(notes_integer)
        half_note_count = len(notes_half)

        # Base structure is 2 blocks long:
        # [0, 0, 0] = Block that notes attach to
        # [1, 0, 0] = Repeater (delay from previous tick)

        # Add the redstone block (default is wood if no notes to attach, else instrument)
        # Note: If there is an integer note, the central block will be the instrument block for that note.
        # But we handle instruments inside add_note (it places at y-1).
        # So at y=0, we place wood to propagate the signal.
        self.add_block(0, 0, 0, self.index_wood)

        # Add repeater at pos x=1
        # Repeater points west (towards x=0).
        # We clamp tick_delay between 1 and 4 for the repeater
        actual_delay = max(1, min(4, tick_delay))
        self.add_block(1, 0, 0, self.index_repeater + actual_delay - 1, needs_down=True)

        # Place notes branching off to the sides (z-axis)
        if integer_note_count > 0:
            # Place note directly on top of the block? No, note goes on top of its instrument.
            # Let's put notes next to the central block.

            # 1st Note: z=-1
            if integer_note_count >= 1:
                self.add_note(0, 0, -1, notes_integer[0])

            # 2nd Note: z=1
            if integer_note_count >= 2:
                self.add_note(0, 0, 1, notes_integer[1])

            # 3rd Note: z=-2 (attached via redstone)
            if integer_note_count >= 3:
                self.add_block(0, 0, -1, self.index_redstone, needs_down=True)
                self.add_note(0, 0, -2, notes_integer[2])

            # 4th Note: z=2
            if integer_note_count >= 4:
                self.add_block(0, 0, 1, self.index_redstone, needs_down=True)
                self.add_note(0, 0, 2, notes_integer[3])

        # Half ticks logic using piston
        if half_note_count > 0:
            # Place piston above the central block
            # Actually, standard redstone clock offset:
            # Piston at [0, 1, 0] facing East, pushing a redstone block
            self.add_block(0, 1, 0, self.index_piston)
            self.add_block(1, 1, 0, self.index_redstone_block)

            # Note for half tick is activated by the redstone block
            # Let's place it at x=2, y=1, z=1
            if half_note_count >= 1:
                self.add_note(2, 1, 1, notes_half[0])

            if half_note_count >= 2:
                self.add_note(2, 1, -1, notes_half[1])

            if half_note_count >= 3:
                self.add_block(2, 1, 1, self.index_redstone, needs_down=True)
                self.add_note(2, 1, 2, notes_half[2])

            if half_note_count >= 4:
                self.add_block(2, 1, -1, self.index_redstone, needs_down=True)
                self.add_note(2, 1, -2, notes_half[3])

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
