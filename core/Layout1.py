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

    def build(self, notes_integer=None, notes_half=None, delay=1, is_symmetric=True):
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

        brick_int = Brick()
        brick_half = Brick()

        # The central block (wood) and the connecting repeater
        brick_int.add_block(0, 0, 0, "minecraft:oak_planks", tick=self.tick)
        brick_int.add_block(1, 0, 0, "minecraft:repeater", {"facing": "west", "delay": delay}, tick=self.tick, needs_down=True)

        # Place notes branching off to the sides (z-axis)
        if is_symmetric:
            for i in range(integer_note_count):
                side = 1 if i % 2 == 0 else -1
                depth = (i // 2) + 1
                brick_int.add_block(0, 0, depth * side, "minecraft:redstone_wire", tick=self.tick, needs_down=True)
                self.add_note_to_brick(brick_int, -1, 0, depth * side, notes_integer[i])
        else:
            for i in range(integer_note_count):
                z_pos = i + 1
                brick_int.add_block(0, 0, z_pos, "minecraft:redstone_wire", tick=self.tick, needs_down=True)
                self.add_note_to_brick(brick_int, -1, 0, z_pos, notes_integer[i])

        # Half ticks logic using piston
        if half_note_count > 0:
            # Place piston above the central block
            brick_half.add_block(0, 1, 0, "minecraft:sticky_piston", {"facing": "east"}, tick=self.tick)
            brick_half.add_block(1, 1, 0, "minecraft:redstone_block", tick=self.tick)

            if is_symmetric:
                for i in range(half_note_count):
                    side = 1 if i % 2 == 0 else -1
                    depth = (i // 2) + 1
                    brick_half.add_block(1, 1, depth * side, "minecraft:redstone_wire", tick=self.tick, needs_down=True)
                    self.add_note_to_brick(brick_half, 2, 1, depth * side, notes_half[i])
            else:
                for i in range(half_note_count):
                    z_pos = i + 1
                    brick_half.add_block(1, 1, z_pos, "minecraft:redstone_wire", tick=self.tick, needs_down=True)
                    self.add_note_to_brick(brick_half, 2, 1, z_pos, notes_half[i])

        self.add_data(brick_int)
        self.add_data(brick_half)

        self.tick += 1

class Layout1Track(Brick):
    """
    Manages a sequence of Layout1Bricks, assembling them into a continuous straight line.
    """
    def __init__(self, is_symmetric=True):
        super().__init__()
        self.is_symmetric = is_symmetric

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
            brick.build(notes_entier, notes_demi, delay=actual_delay, is_symmetric=self.is_symmetric)

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
