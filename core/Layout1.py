import numpy as np
from core.customNBT import CustomNBT
from core.layout_base import LayoutBase
from core.brick import Brick

class MinecartBrick(LayoutBase):
    """
    Manages the central minecart rail for Layout 1.
    Builds a 2-block long straight rail segment (progressing along X).
    """
    def __init__(self, nbt=None, start_x=0, start_y=0, start_z=0):
        super().__init__(x=start_x, y=start_y, z=start_z, nbt=nbt)

    def build(self):
        # We need a solid block under the rail
        self.add_block(0, 0, 0, self.index_wood)
        self.add_block(1, 0, 0, self.index_wood)

        # Detector rail on the first block, powered rail on the second
        self.add_block(0, 1, 0, self.index_detector)
        self.add_block(1, 1, 0, self.index_rail)

        self.tick += 1

class Layout1Brick(LayoutBase):
    """
    Manages a straight line layout (Repeater -> Block) for a single tick.
    Inherits from LayoutBase.
    """
    def __init__(self, nbt=None, start_x=0, start_y=0, start_z=0):
        super().__init__(x=start_x, y=start_y, z=start_z, nbt=nbt)

    def build(self, tick_delay, notes_integer=None, notes_half=None, is_symmetric=False):
        """
        Builds a single tick's worth of blocks for the straight layout.
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

class Layout1Track(Brick):
    """
    Manages a sequence of Layout1Bricks, assembling them into a continuous straight line.
    """
    def __init__(self, nbt_template=None):
        super().__init__()
        self.nbt_template = nbt_template

    def build_sequence(self, df_notes):
        """Processes notes and maps them to a continuous straight line of bricks."""
        last_tick = -1
        pos = [1, 0, 0]

        for tick in df_notes.index:
            tick_diff = int(tick - last_tick)

            brick = Layout1Brick(nbt=self.nbt_template)
            brick.tick = int(last_tick)

            # Get notes for this tick
            notes_entier = df_notes.loc[tick]['note entier']
            notes_demi = df_notes.loc[tick]['note demi']

            # Build the brick
            brick.build(tick_diff, notes_entier, notes_demi)

            # Build the parallel minecart track
            minecart = MinecartBrick(nbt=self.nbt_template)
            minecart.build()

            # Translate both to current global track position
            brick.position = [pos[0], pos[1], pos[2]]

            # The minecart track runs parallel, separated by a couple blocks on the Z axis
            minecart.position = [pos[0], pos[1], pos[2] - 3]

            # Layout1 progresses 2 blocks per tick on the X axis
            pos[0] += 2

            # Merge the bricks into this track
            self.add_data(brick)
            self.add_data(minecart)
            last_tick = tick
