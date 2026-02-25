import numpy as np
from customNBT import CustomNBT
from data import Data

class Layout2:
    """
    Manages the layout of note blocks and redstone structures.
    This class defines how notes are placed in 3D space relative to the redstone line.
    """
    
    def __init__(self, x=0, y=0, z=0, nbt=None, facing='south', direction=-1):
        self.x0 = x
        self.y0 = y
        self.z0 = z
        
        self.pos = [0, 0, 0]
        
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

    def add(self, tick, notes_entier=None, notes_demi=None, sym=False):
        """
        Adds a segment of the song (one or more ticks) to the layout.

        Args:
            tick (int): Tick delay from previous segment.
            notes_entier (list): List of notes on integer ticks.
            notes_demi (list): List of notes on half ticks (requiring pistons).
            sym (bool): Symmetry flag for layout variation.
        """
        self.data.reshape(10, 0, 4)

        nb_entier = 0
        nb_demi = 0

        if notes_entier is not None:
            nb_entier = len(notes_entier)
        if notes_demi is not None:
            nb_demi = len(notes_demi)
  
        # Piston side logic (half ticks) - rotated parts
        if notes_demi is not None:
            if nb_demi >= 1:
                self.add_note(1, 0, 0, notes_demi[0])
            if nb_demi >= 2:
                self.add_note(0, 0, -1, notes_demi[1])
            if nb_demi >= 3:
                self.add_note(0, 0, 1, notes_demi[2])
            if nb_demi >= 4:
                self.data.data = np.roll(self.data.data, 1, axis=0)
                self.add_block(0, 0, 0, self.index_redstone, needs_down=True)
                self.add_block(0, -1, 0, self.index_floor)
                self.add_note(1, 0, 0, notes_demi[3])
            if nb_demi >= 5:
                self.add_note(0, -1, 1, notes_demi[4])
            if nb_demi >= 6:
                self.add_note(0, -1, -1, notes_demi[5])
            if nb_demi >= 7:
                self.data.data = np.roll(self.data.data, 1, axis=0)
                self.add_block(0, 0, 0, self.index_redstone, needs_down=True)
                self.add_block(0, -1, 0, self.index_floor)
                self.add_note(0, -1, 1, notes_demi[6])
            if nb_demi >= 8:
                self.add_note(0, -1, -1, notes_demi[7]) # Up to 8 half notes supported
                
            if nb_demi >= 4:
                self.data.data = np.roll(self.data.data, 1, axis=0)

            self.data.data = np.roll(self.data.data, 2, axis=0)
            self.add_block(0, 0, 0, self.index_piston)
            self.add_block(1, 0, 0, self.index_redstone_block)
            
            self.data.data = np.roll(self.data.data, 1, axis=0)
            
        # Integer tick notes (rotated part)
        # Triggered if > 5 notes (no piston) or > 4 notes (with piston)
        if nb_entier > 5 or (nb_entier > 4 and nb_demi != 0):

            # Symmetry adjustment allows one extra block (block #4)
            offset_notes_entier = 1 if sym else 0

            self.add_block(0, 0, 0, self.index_redstone, needs_down=True)
            self.add_block(0, -1, 0, self.index_floor)

            if nb_entier >= 4 + offset_notes_entier:
                self.add_note(0, -1, -1, notes_entier[3 + offset_notes_entier])
                    
            if nb_entier >= 5 + offset_notes_entier:
                self.add_note(0, -1, 1, notes_entier[4 + offset_notes_entier])

            if nb_entier >= 6 + offset_notes_entier:
                self.data.data = np.roll(self.data.data, 1, axis=0)
                self.add_block(0, 0, 0, self.index_redstone, needs_down=True)
                self.add_block(0, -1, 0, self.index_floor)
                self.add_note(0, -1, -1, notes_entier[5 + offset_notes_entier])
            if nb_entier >= 7 + offset_notes_entier:
                self.add_note(0, -1, 1, notes_entier[6 + offset_notes_entier])
             
            if nb_entier >= 8 + offset_notes_entier:
                self.data.data = np.roll(self.data.data, 1, axis=0)
                self.add_block(0, 0, 0, self.index_redstone, needs_down=True)
                self.add_block(0, -1, 0, self.index_floor)
                self.add_note(0, -1, -1, notes_entier[7 + offset_notes_entier])
            if nb_entier >= 9 + offset_notes_entier:
                self.add_note(0, -1, 1, notes_entier[8 + offset_notes_entier])
            
            self.data.data = np.roll(self.data.data, 1, axis=0)

        # Rotate piston/extended parts
        if sym:
            self.rotate(1)
        self.data.data = np.roll(self.data.data, 1, axis=0)

        # Central block
        if nb_entier == 0:
            self.add_block(1, 0, 0, self.index_lamp)
        if nb_entier >= 1:
            self.add_note(1, 0, 0, notes_entier[0])
            
        # Redstone side notes
        if nb_demi == 0 and nb_entier <= 5:
            if nb_entier >= 2:
                self.add_note(1, 0, 1, notes_entier[1])
            if nb_entier >= 3:
                self.add_note(2, 0, 0, notes_entier[2])
            if nb_entier >= 4:
                self.add_note(0, -1, -1, notes_entier[3])
            if nb_entier >= 5:
                self.add_note(2, -1, -1, notes_entier[4])

        elif nb_demi == 1 and nb_entier <= 4:
            if nb_entier >= 2 and not sym:
                self.add_note(1, 0, 1, notes_entier[1])
            if nb_entier >= 2 and sym:
                self.add_note(2, 0, 0, notes_entier[1])
            if nb_entier >= 3:
                self.add_note(0, -1, -1, notes_entier[2])
            if nb_entier >= 4:
                self.add_note(2, -1, -1, notes_entier[3])
        
        else:
            if nb_entier >= 2 and not sym:
                self.add_note(1, 0, 1, notes_entier[1])
            if nb_entier >= 2 and sym:
                self.add_note(2, 0, 0, notes_entier[1])
            if nb_entier >= 3:
                self.add_note(0, -1, -1, notes_entier[2])
            if nb_entier >= 4 and sym:
                self.add_note(2, -1, -1, notes_entier[3])

        # Redstone line & floor
        self.add_block(0, 0, 0, self.index_repeater + tick - 1, needs_down=True)
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
        
    def add_block(self, x, y, z, index, random_amount=-1, needs_down=False, needs_up=False):
        """Adds a generic block to the layout data."""
        if index == -1:
            return
        self.data.add_block(x, y, z, index, self.tick, random_amount=random_amount, needs_down=needs_down, needs_up=needs_up)
    
    def rotate(self, i):
        """Rotates the entire layout data."""
        self.data.rotate(i, self.custom_nbt)
    
    def flip(self):
        """Flips the entire layout data."""
        self.data.flip(self.custom_nbt)
    
    def write_nbt(self):
        """Writes the layout data to the customNBT object."""
        sX = self.data.shape[0]
        sY = self.data.shape[1]
        sZ = self.data.shape[2]
        for i in range(sX):
            for j in range(sY):
                for k in range(sZ):
                    if self.data.data[i - sX // 2, j - sY // 2, k - sZ // 2, 0] != -1:
                        # Assuming index 1 holds the block type
                        block_type = self.data.data[i - sX // 2, j - sY // 2, k - sZ // 2, 1]
                        self.custom_nbt.add_block([i - sX // 2, j - sY // 2, k - sZ // 2], block_type)
