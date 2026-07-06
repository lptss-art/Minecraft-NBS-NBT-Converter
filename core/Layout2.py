import numpy as np
from core.customNBT import CustomNBT
from core.brick import Brick

class Layout2(Brick):
    """
    Manages the layout of note blocks and redstone structures.
    This class defines how notes are placed in 3D space relative to the redstone line.
    Now inherits directly from Brick.
    """
    
    def __init__(self, x=0, y=0, z=0, nbt=None, facing='south', direction=-1):
        super().__init__(x=x, y=y, z=z, nbt=nbt, facing=facing, direction=direction)
        self.start_x = x
        self.start_y = y
        self.start_z = z
        
        if nbt is None:
            return
        
        self.custom_nbt = nbt
        self.direction = direction
        self.facing = facing
        
        # Cache indices from customNBT
        self.index_repeater = self.custom_nbt.index_repeaters["west"]
        self.index_piston = self.custom_nbt.index_pistons["east"]

        self.index_redstone = self.custom_nbt.get_index("minecraft:redstone_wire", {'east': 'side', 'west': 'side'})
        self.index_redstone_block = self.custom_nbt.get_index("minecraft:redstone_block")
        self.index_wood = self.custom_nbt.get_index_safe("minecraft:oak_planks")
        self.index_air = self.custom_nbt.get_index("minecraft:air")
        self.index_floor = -1 # self.custom_nbt.get_index("minecraft:stone")

        self.offset_notes = self.custom_nbt.index_notes
        self.offset_instr = self.custom_nbt.index_instr

        self.tick = 0
        self.index = 0

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
                self._add_note_to_brick(sub_brick, 1, 0, 0, notes_half[0])
            if half_note_count >= 2:
                self._add_note_to_brick(sub_brick, 0, 0, -1, notes_half[1])
            if half_note_count >= 3:
                self._add_note_to_brick(sub_brick, 0, 0, 1, notes_half[2])
            if half_note_count >= 4:
                sub_brick.translate(1, 0, 0)
                sub_brick.add_block(0, 0, 0, self.index_redstone, tick=self.tick, needs_down=True)
                sub_brick.add_block(0, -1, 0, self.index_floor, tick=self.tick)
                self._add_note_to_brick(sub_brick, 1, 0, 0, notes_half[3])
            if half_note_count >= 5:
                self._add_note_to_brick(sub_brick, 0, -1, 1, notes_half[4])
            if half_note_count >= 6:
                self._add_note_to_brick(sub_brick, 0, -1, -1, notes_half[5])
            if half_note_count >= 7:
                sub_brick.translate(1, 0, 0)
                sub_brick.add_block(0, 0, 0, self.index_redstone, tick=self.tick, needs_down=True)
                sub_brick.add_block(0, -1, 0, self.index_floor, tick=self.tick)
                self._add_note_to_brick(sub_brick, 0, -1, 1, notes_half[6])
            if half_note_count >= 8:
                self._add_note_to_brick(sub_brick, 0, -1, -1, notes_half[7]) # Up to 8 half notes supported
                
            if half_note_count >= 4:
                sub_brick.translate(1, 0, 0)

            sub_brick.translate(2, 0, 0)
            sub_brick.add_block(0, 0, 0, self.index_piston, tick=self.tick)
            sub_brick.add_block(1, 0, 0, self.index_redstone_block, tick=self.tick)
            
            sub_brick.translate(1, 0, 0)
            
        # Integer tick notes (rotated part)
        # Triggered if > 5 notes (no piston) or > 4 notes (with piston)
        if integer_note_count > 5 or (integer_note_count > 4 and half_note_count != 0):

            # Symmetry adjustment allows one extra block (block #4)
            offset_notes_integer = 1 if is_symmetric else 0

            sub_brick.add_block(0, 0, 0, self.index_redstone, tick=self.tick, needs_down=True)
            sub_brick.add_block(0, -1, 0, self.index_floor, tick=self.tick)

            if integer_note_count >= 4 + offset_notes_integer:
                self._add_note_to_brick(sub_brick, 0, -1, -1, notes_integer[3 + offset_notes_integer])
                    
            if integer_note_count >= 5 + offset_notes_integer:
                self._add_note_to_brick(sub_brick, 0, -1, 1, notes_integer[4 + offset_notes_integer])

            if integer_note_count >= 6 + offset_notes_integer:
                sub_brick.translate(1, 0, 0)
                sub_brick.add_block(0, 0, 0, self.index_redstone, tick=self.tick, needs_down=True)
                sub_brick.add_block(0, -1, 0, self.index_floor, tick=self.tick)
                self._add_note_to_brick(sub_brick, 0, -1, -1, notes_integer[5 + offset_notes_integer])
            if integer_note_count >= 7 + offset_notes_integer:
                self._add_note_to_brick(sub_brick, 0, -1, 1, notes_integer[6 + offset_notes_integer])
             
            if integer_note_count >= 8 + offset_notes_integer:
                sub_brick.translate(1, 0, 0)
                sub_brick.add_block(0, 0, 0, self.index_redstone, tick=self.tick, needs_down=True)
                sub_brick.add_block(0, -1, 0, self.index_floor, tick=self.tick)
                self._add_note_to_brick(sub_brick, 0, -1, -1, notes_integer[7 + offset_notes_integer])
            if integer_note_count >= 9 + offset_notes_integer:
                self._add_note_to_brick(sub_brick, 0, -1, 1, notes_integer[8 + offset_notes_integer])
            
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
        
        self.index += 1
     
    def _add_note_to_brick(self, brick, x, y, z, note):
        if not hasattr(note, 'note'):
            return
        brick.add_block(x, y, z, note.note + self.offset_notes, tick=self.tick)
        brick.add_block(x, y - 1, z, note.instr + self.offset_instr, tick=self.tick, needs_down=True)
        brick.add_block(x, y + 1, z, self.index_air, tick=self.tick)

    def add_note(self, x, y, z, note):
        """Adds a note block, instrument block below, and air above."""
        # Note block
        self.add_block(x, y, z, note.note + self.offset_notes)

        # Instrument block
        self.add_block(x, y - 1, z, note.instr + self.offset_instr, needs_down=True)
        
        # Air block
        self.add_block(x, y + 1, z, self.index_air)
        
    def add_block(self, x, y, z, index, random_delay_range=-1, needs_down=False, needs_up=False):
        """Adds a generic block to the layout data."""
        if index == -1:
            return
        super().add_block(x, y, z, index, self.tick, random_delay_range=random_delay_range, needs_down=needs_down, needs_up=needs_up)
    
    def rotate(self, i):
        """Rotates the entire layout data."""
        super().rotate(i, self.custom_nbt)
    
    def flip(self):
        """Flips the entire layout data."""
        super().flip(self.custom_nbt)
    
    def write_nbt(self):
        """Writes the layout data to the customNBT object."""
        super().write_nbt(self.custom_nbt)
