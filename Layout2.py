import numpy as np
from customNBT import CustomNBT
from data import Data

class Layout2:
    """
    Manages the layout of note blocks and redstone structures.
    This class defines how notes are placed in 3D space relative to the redstone line.
    """
    
    def __init__(self, x=0, y=0, z=0, nbt=None, facing='south', direction=-1):
        self.start_x = x
        self.start_y = y
        self.start_z = z
        
        self.current_position = [0, 0, 0]
        
        if nbt is None:
            return
        
        self.custom_nbt = nbt
        self.direction = direction
        self.facing = facing
        
        self.data = Data()
        
        # Cache indices from customNBT
        self.index_repeater = self.custom_nbt.index_repeaters["west"]
        self.index_piston = self.custom_nbt.index_pistons["east"]

        self.index_redstone = self.custom_nbt.get_index("minecraft:redstone_wire", {'east': 'side', 'west': 'side'})
        self.index_redstone_block = self.custom_nbt.get_index("minecraft:redstone_block")
        self.index_lamp = self.custom_nbt.get_index("minecraft:redstone_lamp")
        self.index_air = self.custom_nbt.get_index("minecraft:air")
        self.index_floor = -1 # self.custom_nbt.get_index("minecraft:stone")

        self.offset_notes = self.custom_nbt.index_notes
        self.offset_instr = self.custom_nbt.index_instr

        self.tick = 0
        self.index = 0

    def add(self, tick_delay, notes_integer=None, notes_half=None, is_symmetric=False):
        """
        Adds a segment of the song (one or more ticks) to the layout.

        Args:
            tick_delay (int): Tick delay from previous segment.
            notes_integer (list): List of notes on integer ticks.
            notes_half (list): List of notes on half ticks (requiring pistons).
            is_symmetric (bool): Symmetry flag for layout variation.
        """
        self.data.reshape(10, 0, 4)

        integer_note_count = 0
        half_note_count = 0

        if notes_integer is not None:
            integer_note_count = len(notes_integer)
        if notes_half is not None:
            half_note_count = len(notes_half)
  
        # Piston side logic (half ticks) - rotated parts
        if notes_half is not None:
            if half_note_count >= 1:
                self.add_note(1, 0, 0, notes_half[0])
            if half_note_count >= 2:
                self.add_note(0, 0, -1, notes_half[1])
            if half_note_count >= 3:
                self.add_note(0, 0, 1, notes_half[2])
            if half_note_count >= 4:
                self.data.data = np.roll(self.data.data, 1, axis=0)
                self.add_block(0, 0, 0, self.index_redstone, needs_down=True)
                self.add_block(0, -1, 0, self.index_floor)
                self.add_note(1, 0, 0, notes_half[3])
            if half_note_count >= 5:
                self.add_note(0, -1, 1, notes_half[4])
            if half_note_count >= 6:
                self.add_note(0, -1, -1, notes_half[5])
            if half_note_count >= 7:
                self.data.data = np.roll(self.data.data, 1, axis=0)
                self.add_block(0, 0, 0, self.index_redstone, needs_down=True)
                self.add_block(0, -1, 0, self.index_floor)
                self.add_note(0, -1, 1, notes_half[6])
            if half_note_count >= 8:
                self.add_note(0, -1, -1, notes_half[7]) # Up to 8 half notes supported
                
            if half_note_count >= 4:
                self.data.data = np.roll(self.data.data, 1, axis=0)

            self.data.data = np.roll(self.data.data, 2, axis=0)
            self.add_block(0, 0, 0, self.index_piston)
            self.add_block(1, 0, 0, self.index_redstone_block)
            
            self.data.data = np.roll(self.data.data, 1, axis=0)
            
        # Integer tick notes (rotated part)
        # Triggered if > 5 notes (no piston) or > 4 notes (with piston)
        if integer_note_count > 5 or (integer_note_count > 4 and half_note_count != 0):

            # Symmetry adjustment allows one extra block (block #4)
            offset_notes_integer = 1 if is_symmetric else 0

            self.add_block(0, 0, 0, self.index_redstone, needs_down=True)
            self.add_block(0, -1, 0, self.index_floor)

            if integer_note_count >= 4 + offset_notes_integer:
                self.add_note(0, -1, -1, notes_integer[3 + offset_notes_integer])
                    
            if integer_note_count >= 5 + offset_notes_integer:
                self.add_note(0, -1, 1, notes_integer[4 + offset_notes_integer])

            if integer_note_count >= 6 + offset_notes_integer:
                self.data.data = np.roll(self.data.data, 1, axis=0)
                self.add_block(0, 0, 0, self.index_redstone, needs_down=True)
                self.add_block(0, -1, 0, self.index_floor)
                self.add_note(0, -1, -1, notes_integer[5 + offset_notes_integer])
            if integer_note_count >= 7 + offset_notes_integer:
                self.add_note(0, -1, 1, notes_integer[6 + offset_notes_integer])
             
            if integer_note_count >= 8 + offset_notes_integer:
                self.data.data = np.roll(self.data.data, 1, axis=0)
                self.add_block(0, 0, 0, self.index_redstone, needs_down=True)
                self.add_block(0, -1, 0, self.index_floor)
                self.add_note(0, -1, -1, notes_integer[7 + offset_notes_integer])
            if integer_note_count >= 9 + offset_notes_integer:
                self.add_note(0, -1, 1, notes_integer[8 + offset_notes_integer])
            
            self.data.data = np.roll(self.data.data, 1, axis=0)

        # Rotate piston/extended parts
        if is_symmetric:
            self.rotate(1)
        self.data.data = np.roll(self.data.data, 1, axis=0)

        # Central block
        if integer_note_count == 0:
            self.add_block(1, 0, 0, self.index_lamp)
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
     
    def add_note(self, x, y, z, note):
        """Adds a note block, instrument block below, and air above."""
        # Note block
        self.data.add_block(x, y, z, note.note + self.offset_notes, self.tick)

        # Instrument block
        self.data.add_block(x, y - 1, z, note.instr + self.offset_instr, self.tick)
        
        # Air block
        self.data.add_block(x, y + 1, z, self.index_air, self.tick)
        
    def add_block(self, x, y, z, index, random_delay_range=-1, needs_down=False, needs_up=False):
        """Adds a generic block to the layout data."""
        if index == -1:
            return
        self.data.add_block(x, y, z, index, self.tick, random_delay_range=random_delay_range, needs_down=needs_down, needs_up=needs_up)
    
    def rotate(self, i):
        """Rotates the entire layout data."""
        self.data.rotate(i, self.custom_nbt)
    
    def flip(self):
        """Flips the entire layout data."""
        self.data.flip(self.custom_nbt)
    
    def write_nbt(self):
        """Writes the layout data to the customNBT object."""
        size_x = self.data.shape[0]
        size_y = self.data.shape[1]
        size_z = self.data.shape[2]
        for i in range(size_x):
            for j in range(size_y):
                for k in range(size_z):
                    if self.data.data[i - size_x // 2, j - size_y // 2, k - size_z // 2]['f0']:
                        # Assuming index 1 holds the block type
                        block_type = self.data.data[i - size_x // 2, j - size_y // 2, k - size_z // 2]['f1']
                        self.custom_nbt.add_block([i - size_x // 2, j - size_y // 2, k - size_z // 2], block_type)
