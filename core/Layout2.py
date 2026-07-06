import numpy as np
from core.customNBT import CustomNBT
from core.layout_base import LayoutBase
from core.brick import Brick

class Layout2Brick(LayoutBase):
    """
    Manages the layout of note blocks and redstone structures for a single tick.
    Inherits from LayoutBase.
    """
    def __init__(self, x=0, y=0, z=0, nbt=None, facing='south', direction=-1):
        super().__init__(x=x, y=y, z=z, nbt=nbt, facing=facing, direction=direction)
        
    def build(self, tick_delay, notes_integer=None, notes_half=None, is_symmetric=False):
        """
        Adds a segment of the song (one or more ticks) to the layout.

        Args:
            tick_delay (int): Tick delay from previous segment.
            notes_integer (list): List of notes on integer ticks.
            notes_half (list): List of notes on half ticks (requiring pistons).
            is_symmetric (bool): Symmetry flag for layout variation.
        """
        integer_note_count = 0
        half_note_count = 0

        if notes_integer is not None:
            integer_note_count = len(notes_integer)
        if notes_half is not None:
            half_note_count = len(notes_half)
  
        # For the complex extensions, we create a sub-brick
        sub_brick = Brick(nbt=self.custom_nbt)

        # Piston side logic (half ticks) - rotated parts
        if notes_half is not None:
            if half_note_count >= 1:
                self.add_note_to_brick(sub_brick, 1, 0, 0, notes_half[0])
            if half_note_count >= 2:
                self.add_note_to_brick(sub_brick, 0, 0, -1, notes_half[1])
            if half_note_count >= 3:
                self.add_note_to_brick(sub_brick, 0, 0, 1, notes_half[2])
            if half_note_count >= 4:
                sub_brick.translate(1, 0, 0)
                sub_brick.add_block(0, 0, 0, self.index_redstone, self.tick, needs_down=True)
                sub_brick.add_block(0, -1, 0, self.index_floor, self.tick)
                self.add_note_to_brick(sub_brick, 1, 0, 0, notes_half[3])
            if half_note_count >= 5:
                self.add_note_to_brick(sub_brick, 0, -1, 1, notes_half[4])
            if half_note_count >= 6:
                self.add_note_to_brick(sub_brick, 0, -1, -1, notes_half[5])
            if half_note_count >= 7:
                sub_brick.translate(1, 0, 0)
                sub_brick.add_block(0, 0, 0, self.index_redstone, self.tick, needs_down=True)
                sub_brick.add_block(0, -1, 0, self.index_floor, self.tick)
                self.add_note_to_brick(sub_brick, 0, -1, 1, notes_half[6])
            if half_note_count >= 8:
                self.add_note_to_brick(sub_brick, 0, -1, -1, notes_half[7]) # Up to 8 half notes supported
                
            if half_note_count >= 4:
                sub_brick.translate(1, 0, 0)

            sub_brick.translate(2, 0, 0)
            sub_brick.add_block(0, 0, 0, self.index_piston, self.tick)
            sub_brick.add_block(1, 0, 0, self.index_redstone_block, self.tick)
            
            sub_brick.translate(1, 0, 0)
            
        # Integer tick notes (rotated part)
        # Triggered if > 5 notes (no piston) or > 4 notes (with piston)
        if integer_note_count > 5 or (integer_note_count > 4 and half_note_count != 0):

            # Symmetry adjustment allows one extra block (block #4)
            offset_notes_integer = 1 if is_symmetric else 0

            sub_brick.add_block(0, 0, 0, self.index_redstone, self.tick, needs_down=True)
            sub_brick.add_block(0, -1, 0, self.index_floor, self.tick)

            if integer_note_count >= 4 + offset_notes_integer:
                self.add_note_to_brick(sub_brick, 0, -1, -1, notes_integer[3 + offset_notes_integer])
                    
            if integer_note_count >= 5 + offset_notes_integer:
                self.add_note_to_brick(sub_brick, 0, -1, 1, notes_integer[4 + offset_notes_integer])

            if integer_note_count >= 6 + offset_notes_integer:
                sub_brick.translate(1, 0, 0)
                sub_brick.add_block(0, 0, 0, self.index_redstone, self.tick, needs_down=True)
                sub_brick.add_block(0, -1, 0, self.index_floor, self.tick)
                self.add_note_to_brick(sub_brick, 0, -1, -1, notes_integer[5 + offset_notes_integer])
            if integer_note_count >= 7 + offset_notes_integer:
                self.add_note_to_brick(sub_brick, 0, -1, 1, notes_integer[6 + offset_notes_integer])
             
            if integer_note_count >= 8 + offset_notes_integer:
                sub_brick.translate(1, 0, 0)
                sub_brick.add_block(0, 0, 0, self.index_redstone, self.tick, needs_down=True)
                sub_brick.add_block(0, -1, 0, self.index_floor, self.tick)
                self.add_note_to_brick(sub_brick, 0, -1, -1, notes_integer[7 + offset_notes_integer])
            if integer_note_count >= 9 + offset_notes_integer:
                self.add_note_to_brick(sub_brick, 0, -1, 1, notes_integer[8 + offset_notes_integer])
            
            sub_brick.translate(1, 0, 0)

        # Rotate piston/extended parts
        if is_symmetric:
            sub_brick.rotate(1, self.custom_nbt)
        sub_brick.translate(1, 0, 0)

        # Merge the sub brick into this one
        self.add_data(sub_brick)

        # Central block
        if integer_note_count == 0:
            self.add_block(1, 0, 0, self.index_wood)
        if integer_note_count >= 1:
            self.add_note(1, 0, 0, notes_integer[0])
            
        # Redstone side notes
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
            if integer_note_count >= 2 and not is_symmetric:
                self.add_note(1, 0, 1, notes_integer[1])
            if integer_note_count >= 2 and is_symmetric:
                self.add_note(2, 0, 0, notes_integer[1])
            if integer_note_count >= 3:
                self.add_note(0, -1, -1, notes_integer[2])
            if integer_note_count >= 4:
                self.add_note(2, -1, -1, notes_integer[3])
        
        else:
            if integer_note_count >= 2 and not is_symmetric:
                self.add_note(1, 0, 1, notes_integer[1])
            if integer_note_count >= 2 and is_symmetric:
                self.add_note(2, 0, 0, notes_integer[1])
            if integer_note_count >= 3:
                self.add_note(0, -1, -1, notes_integer[2])
            if integer_note_count >= 4 and is_symmetric:
                self.add_note(2, -1, -1, notes_integer[3])

        # Redstone line & floor
        self.add_block(0, 0, 0, self.index_repeater + tick_delay - 1, needs_down=True)
        self.add_block(0, -1, 0, self.index_floor)
        
        self.add_block(1, 0, -1, self.index_redstone, needs_down=True)
        self.add_block(1, -1, -1, self.index_floor)

class Layout2Track(Brick):
    """
    Manages a sequence of Layout2Bricks, assembling them into a continuous serpentine layout.
    """
    def __init__(self, nbt_template=None):
        super().__init__()
        self.nbt_template = nbt_template

    def build_sequence(self, df_notes):
        """Processes notes and maps them to a serpentine sequence of bricks."""
        last_tick = -1
        direction = 0
        pos = [1, 0, 0]

        for tick in df_notes.index:
            tick_diff = int(tick - last_tick)

            brick = Layout2Brick(nbt=self.nbt_template)
            brick.tick = int(last_tick)

            # Get notes for this tick
            notes_entier = df_notes.loc[tick]['note entier']
            notes_demi = df_notes.loc[tick]['note demi']

            # Position of this brick in the track
            brick.position = [pos[0], pos[1], pos[2]]

            # Serpentine logic
            if direction % 4 == 0:
                brick.build(tick_diff, notes_entier, notes_demi, is_symmetric=True)
                pos[0] += 1
                pos[2] += -2
            elif direction % 4 == 1:
                brick.build(tick_diff, notes_entier, notes_demi)
                brick.flip()
                brick.rotate(3, self.nbt_template) # -1 is 3 in mod 4
                pos[0] += 2
                pos[2] += -1
            elif direction % 4 == 2:
                brick.build(tick_diff, notes_entier, notes_demi, is_symmetric=True)
                brick.flip()
                pos[0] += 1
                pos[2] += 2
            else:
                brick.build(tick_diff, notes_entier, notes_demi)
                brick.rotate(1, self.nbt_template)
                pos[0] += 2
                pos[2] += 1

            direction += 1

            # Merge the brick into this track
            self.add_data(brick)
            last_tick = tick
        
