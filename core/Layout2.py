import numpy as np
from core.layout_base import LayoutBase
from core.brick import Brick

class Layout2Brick(LayoutBase):
    """
    Manages the layout of note blocks and redstone structures for a single tick.
    Inherits from LayoutBase.
    """
    def __init__(self, x=0, y=0, z=0, facing='south', direction=-1):
        super().__init__(x=x, y=y, z=z, facing=facing, direction=direction)
        
    def build(self, notes_integer=None, notes_half=None, delay=1, is_symmetric=True):
        """
        Adds a segment of the song (one or more ticks) to the layout.

        Args:
            notes_integer (list): List of notes on integer ticks.
            notes_half (list): List of notes on half ticks (requiring pistons).
        """
        integer_note_count = 0
        half_note_count = 0

        if notes_integer is not None:
            integer_note_count = len(notes_integer)
        if notes_half is not None:
            half_note_count = len(notes_half)

        brick_int = Brick()
        brick_half = Brick()

        # Central logic
        # Repeater connecting to the previous block (now positioned within the brick_int itself)
        brick_int.add_block(0, 0, 0, "minecraft:repeater", {"facing": "west", "delay": delay}, tick=self.tick, needs_down=True)

        if integer_note_count == 0:
            brick_int.add_block(1, 0, 0, "minecraft:oak_planks")
        else:
            self.add_note_to_brick(brick_int, 1, 0, 0, notes_integer[0])

        if integer_note_count > 1 or half_note_count > 0:
            # We add redstone to propagate signal sideways
            if is_symmetric:
                brick_int.add_block(1, 0, -1, "minecraft:redstone_wire", tick=self.tick, needs_down=True)
            else:
                brick_int.add_block(1, 0, 1, "minecraft:redstone_wire", tick=self.tick, needs_down=True)

        # Redstone side notes
        if is_symmetric:
            if half_note_count == 0 and integer_note_count <= 5:
                if integer_note_count >= 2:
                    self.add_note_to_brick(brick_int, 1, 0, 1, notes_integer[1])
                if integer_note_count >= 3:
                    self.add_note_to_brick(brick_int, 2, 0, 0, notes_integer[2])
                if integer_note_count >= 4:
                    self.add_note_to_brick(brick_int, 0, -1, -1, notes_integer[3])
                if integer_note_count >= 5:
                    self.add_note_to_brick(brick_int, 2, -1, -1, notes_integer[4])

            elif half_note_count == 1 and integer_note_count <= 4:
                if integer_note_count >= 2:
                    self.add_note_to_brick(brick_int, 1, 0, 1, notes_integer[1])
                if integer_note_count >= 3:
                    self.add_note_to_brick(brick_int, 0, -1, -1, notes_integer[2])
                if integer_note_count >= 4:
                    self.add_note_to_brick(brick_int, 2, -1, -1, notes_integer[3])
            else:
                if integer_note_count >= 2:
                    self.add_note_to_brick(brick_int, 1, 0, 1, notes_integer[1])
                if integer_note_count >= 3:
                    self.add_note_to_brick(brick_int, 0, -1, -1, notes_integer[2])
        else:
            if integer_note_count >= 2:
                self.add_note_to_brick(brick_int, 2, 0, 0, notes_integer[1])
            if integer_note_count >= 3:
                self.add_note_to_brick(brick_int, 0, -1, 1, notes_integer[2])
            if integer_note_count >= 4:
                self.add_note_to_brick(brick_int, 2, -1, 1, notes_integer[3])

        # Piston side logic (half ticks) - rotated parts
        # If is_symmetric is False, we flip the internal logic of half_notes so it builds on the +z side
        sub_brick_half = Brick()

        if notes_half is not None:
            if half_note_count >= 1:
                self.add_note_to_brick(sub_brick_half, 1, 0, 0, notes_half[0])
            if half_note_count >= 2:
                self.add_note_to_brick(sub_brick_half, 0, 0, -1, notes_half[1])
            if half_note_count >= 3:
                self.add_note_to_brick(sub_brick_half, 0, 0, 1, notes_half[2])
            if half_note_count >= 4:
                sub_brick_half.translate(1, 0, 0)
                sub_brick_half.add_block(0, 0, 0, "minecraft:redstone_wire", tick=self.tick, needs_down=True)
                self.add_note_to_brick(sub_brick_half, 1, 0, 0, notes_half[3])
            if half_note_count >= 5:
                self.add_note_to_brick(sub_brick_half, 0, -1, 1, notes_half[4])
            if half_note_count >= 6:
                self.add_note_to_brick(sub_brick_half, 0, -1, -1, notes_half[5])
            if half_note_count >= 7:
                sub_brick_half.translate(1, 0, 0)
                sub_brick_half.add_block(0, 0, 0, "minecraft:redstone_wire", tick=self.tick, needs_down=True)
                self.add_note_to_brick(sub_brick_half, 0, -1, 1, notes_half[6])
            if half_note_count >= 8:
                self.add_note_to_brick(sub_brick_half, 0, -1, -1, notes_half[7])
                
            if half_note_count >= 4:
                sub_brick_half.translate(1, 0, 0)

            sub_brick_half.translate(2, 0, 0)
            sub_brick_half.add_block(0, 0, 0, "minecraft:sticky_piston", {"facing": "east"}, tick=self.tick)
            sub_brick_half.add_block(1, 0, 0, "minecraft:redstone_block", tick=self.tick)
            
            sub_brick_half.translate(1, 0, 0)

        # Integer tick overflow notes
        if integer_note_count > 5 or (integer_note_count > 4 and half_note_count != 0):

            sub_brick_half.add_block(0, 0, 0, "minecraft:redstone_wire", tick=self.tick, needs_down=True)

            if integer_note_count >= 4:
                self.add_note_to_brick(sub_brick_half, 0, -1, -1, notes_integer[3])
            if integer_note_count >= 5:
                self.add_note_to_brick(sub_brick_half, 0, -1, 1, notes_integer[4])

            if integer_note_count >= 6:
                sub_brick_half.translate(1, 0, 0)
                sub_brick_half.add_block(0, 0, 0, "minecraft:redstone_wire", tick=self.tick, needs_down=True)
                self.add_note_to_brick(sub_brick_half, 0, -1, -1, notes_integer[5])
            if integer_note_count >= 7:
                self.add_note_to_brick(sub_brick_half, 0, -1, 1, notes_integer[6])
             
            if integer_note_count >= 8:
                sub_brick_half.translate(1, 0, 0)
                sub_brick_half.add_block(0, 0, 0, "minecraft:redstone_wire", tick=self.tick, needs_down=True)
                self.add_note_to_brick(sub_brick_half, 0, -1, -1, notes_integer[7])
            if integer_note_count >= 9:
                self.add_note_to_brick(sub_brick_half, 0, -1, 1, notes_integer[8])
            
            sub_brick_half.translate(1, 0, 0)

        sub_brick_half.translate(1, 0, 0)

        if not is_symmetric:
            sub_brick_half.flip(axis='z')

        brick_half.add_data(sub_brick_half)

        self.add_data(brick_int)
        self.add_data(brick_half)

class Layout2Track(Brick):
    """
    Manages a sequence of Layout2Bricks, assembling them into a continuous serpentine layout.
    """
    def __init__(self, is_symmetric=True):
        super().__init__()
        self.is_symmetric = is_symmetric

    def build_sequence(self, df_notes):
        """Processes notes and maps them to a serpentine sequence of bricks."""
        last_tick = -1
        direction = 0
        pos = [1, 0, 0]

        for tick in df_notes.index:
            tick_diff = int(tick - last_tick)
            actual_delay = max(1, min(4, tick_diff))

            brick = Layout2Brick()
            brick.tick = int(last_tick)

            # Get notes for this tick
            notes_entier = df_notes.loc[tick]['note entier']
            notes_demi = df_notes.loc[tick]['note demi']

            # Position of this brick in the track
            brick.position = [pos[0], pos[1], pos[2]]

            # Serpentine logic
            # Repeater is now built-in inside brick_int based on the delay provided
            brick.build(notes_entier, notes_demi, delay=actual_delay, is_symmetric=self.is_symmetric)

            if direction % 4 == 0:
                pos[0] += 1
                pos[2] += -2
            elif direction % 4 == 1:
                brick.flip(axis='z')
                brick.rotate(3) # -1 is 3 in mod 4
                pos[0] += 2
                pos[2] += -1
            elif direction % 4 == 2:
                brick.flip(axis='x')
                brick.flip(axis='z')
                pos[0] += 1
                pos[2] += 2
            else:
                brick.flip(axis='x')
                brick.rotate(1)
                pos[0] += 2
                pos[2] += 1

            direction += 1

            # Merge the brick into this track
            self.add_data(brick)
            last_tick = tick
        
