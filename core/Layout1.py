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
        self.add_block(-1, 0, 0, "minecraft:oak_planks")
        self.add_block(0, 0, 0, "minecraft:oak_planks")

        # Detector rail on the first block, powered rail on the second
        self.add_block(-1, 1, 0, "minecraft:detector_rail", {"shape": "east_west"})
        self.add_block(0, 1, 0, "minecraft:powered_rail", {"shape": "east_west"})

        self.tick += 1

class Layout1Brick(LayoutBase):
    """
    Manages a straight line layout (Repeater -> Block) for a single tick.
    Inherits from LayoutBase.
    """
    def __init__(self, start_x=0, start_y=0, start_z=0):
        super().__init__(x=start_x, y=start_y, z=start_z)

    def build(self, notes_integer=None, notes_half=None, delay=1):
        """
        Builds a single tick's worth of blocks for the straight layout.
        Notes branch off sideways from the central block.
        """
        if notes_integer is None:
            notes_integer = []
        if notes_half is None:
            notes_half = []

        brick_int = Brick()
        brick_half = Brick()

        # (-1, 0, 0) repeater facing east
        brick_int.add_block(-1, 0, 0, "minecraft:repeater", {"facing": "east", "delay": delay}, tick=self.tick, needs_down=True)

        if len(notes_integer) > 0:
            brick_int.add_block(0, 0, 0, "minecraft:redstone_wire", tick=self.tick, needs_down=True)
            self.add_note_to_brick(brick_int, 0, 0, 0, notes_integer[0])
        else:
            brick_int.add_block(0, 0, 0, "minecraft:oak_planks", tick=self.tick)

        if len(notes_integer) > 1:
            brick_int.add_block(0, 0, 1, "minecraft:redstone_wire", tick=self.tick, needs_down=True)
            self.add_note_to_brick(brick_int, 0, 0, 1, notes_integer[1])

        if len(notes_half) > 0:
            brick_half.add_block(0, 0, -1, "minecraft:sticky_piston", {"facing": "north"}, tick=self.tick)
            brick_half.add_block(0, 0, -2, "minecraft:redstone_block", tick=self.tick)

            if len(notes_half) > 0:
                brick_half.add_block(0, 0, -4, "minecraft:redstone_wire", tick=self.tick, needs_down=True)
                self.add_note_to_brick(brick_half, 0, 0, -4, notes_half[0])

            if len(notes_half) > 1:
                brick_half.add_block(1, 0, -3, "minecraft:redstone_wire", tick=self.tick, needs_down=True)
                self.add_note_to_brick(brick_half, 1, 0, -3, notes_half[1])

            if len(notes_half) > 2:
                brick_half.add_block(-1, 0, -3, "minecraft:redstone_wire", tick=self.tick, needs_down=True)
                self.add_note_to_brick(brick_half, -1, 0, -3, notes_half[2])

        self.add_data(brick_int)
        self.add_data(brick_half)

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
            actual_delay = max(1, min(4, tick_diff))

            brick = Layout1Brick()
            brick.tick = int(last_tick)

            # Get notes for this tick
            notes_entier = df_notes.loc[tick]['note entier']
            notes_demi = df_notes.loc[tick]['note demi']

            # Build the brick (includes the repeater now)
            brick.build(notes_entier, notes_demi, delay=actual_delay)

            # Build the parallel minecart track
            minecart = MinecartBrick()
            minecart.build()

            # Translate both to current global track position
            brick.position = [pos[0], pos[1], pos[2]]

            # The minecart track runs parallel, separated by a couple blocks on the Z axis
            minecart.position = [pos[0], pos[1], pos[2] + 3]

            # Layout1 progresses 2 blocks per tick on the X axis
            pos[0] += 2

            # Merge the bricks into this track
            self.add_data(brick)
            self.add_data(minecart)
            last_tick = tick
