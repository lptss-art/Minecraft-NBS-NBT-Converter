import numpy as np
from core.layout_base import LayoutBase
from core.brick import Brick

class MinecartBrick(LayoutBase):
    """
    Manages the central minecart rail for Layout 1.
    Builds a 2-block long straight rail segment (progressing along X).
    """
    def __init__(self, start_x=0, start_y=0, start_z=0):
        super().__init__(x=start_x, y=start_y, z=start_z)

    def build(self):
        # We need a solid block under the rail
        self.add_block(0, 0, 0, "minecraft:oak_planks")
        self.add_block(1, 0, 0, "minecraft:oak_planks")

        # Detector rail on the first block, powered rail on the second
        self.add_block(0, 1, 0, "minecraft:detector_rail", {"shape": "east_west"})
        self.add_block(1, 1, 0, "minecraft:powered_rail", {"shape": "east_west"})

        self.tick += 1

class Layout1Brick(LayoutBase):
    """
    Manages a straight line layout (Repeater -> Block) for a single tick.
    Inherits from LayoutBase.
    """
    def __init__(self, start_x=0, start_y=0, start_z=0):
        super().__init__(x=start_x, y=start_y, z=start_z)

    def build(self, notes_integer=None, notes_half=None):
        """
        Builds a single tick's worth of blocks for the straight layout.
        Notes branch off sideways from the central block.
        """
        if notes_integer is None:
            notes_integer = []
        if notes_half is None:
            notes_half = []

        integer_note_count = len(notes_integer)
        half_note_count = len(notes_half)

        # The central block (wood)
        self.add_block(0, 0, 0, "minecraft:oak_planks")

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
                self.add_block(0, 0, -1, "minecraft:redstone_wire", needs_down=True)
                self.add_note(0, 0, -2, notes_integer[2])

            # 4th Note: z=2
            if integer_note_count >= 4:
                self.add_block(0, 0, 1, "minecraft:redstone_wire", needs_down=True)
                self.add_note(0, 0, 2, notes_integer[3])

        # Half ticks logic using piston
        if half_note_count > 0:
            # Place piston above the central block
            # Actually, standard redstone clock offset:
            # Piston at [0, 1, 0] facing East, pushing a redstone block
            self.add_block(0, 1, 0, "minecraft:sticky_piston", {"facing": "east"})
            self.add_block(1, 1, 0, "minecraft:redstone_block")

            # Note for half tick is activated by the redstone block
            # Let's place it at x=2, y=1, z=1
            if half_note_count >= 1:
                self.add_note(2, 1, 1, notes_half[0])

            if half_note_count >= 2:
                self.add_note(2, 1, -1, notes_half[1])

            if half_note_count >= 3:
                self.add_block(2, 1, 1, "minecraft:redstone_wire", needs_down=True)
                self.add_note(2, 1, 2, notes_half[2])

            if half_note_count >= 4:
                self.add_block(2, 1, -1, "minecraft:redstone_wire", needs_down=True)
                self.add_note(2, 1, -2, notes_half[3])

        self.tick += 1

class Layout1Track(Brick):
    """
    Manages a sequence of Layout1Bricks, assembling them into a continuous straight line.
    """
    def __init__(self):
        super().__init__()

    def build_sequence(self, df_notes):
        """Processes notes and maps them to a continuous straight line of bricks."""
        last_tick = -1
        pos = [1, 0, 0]

        for tick in df_notes.index:
            tick_diff = int(tick - last_tick)

            brick = Layout1Brick()
            brick.tick = int(last_tick)

            # Get notes for this tick
            notes_entier = df_notes.loc[tick]['note entier']
            notes_demi = df_notes.loc[tick]['note demi']

            # Build the brick (just the notes)
            brick.build(notes_entier, notes_demi)

            # Add the connecting repeater to the track itself
            actual_delay = max(1, min(4, tick_diff))

            # The track adds a repeater after the brick's main block.
            # Position it directly on the track logic
            self.add_block(pos[0] + 1, pos[1], pos[2], "minecraft:repeater", {"facing": "west", "delay": actual_delay}, tick, needs_down=True)

            # Build the parallel minecart track
            minecart = MinecartBrick()
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
