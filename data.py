import numpy as np
from customNBT import CustomNBT
from random import randint

class Data:
    """
    Manages a 3D grid of blocks with support for expansion (reshaping),
    rotation, flipping, and NBT export.
    Uses numpy structured arrays to store block properties.
    """

    def __init__(self, x=0, y=0, z=0, nbt=None, facing='south', direction=-1):
        self.pos = [0, 0, 0]
        self.max_shape = [0, 0, 0]

        # 0: Present (bool)
        # 1: Block Index (uint8) - Palette index
        # 2: Tick (int16)
        # 3: Random Tick Delay (uint8)
        # 4: Layer (int16) - Calculated layer for NBT generation
        # 5: Needs Down (bool) - Needs block below
        # 6: Needs Up (bool) - Needs block above

        self.shape = [4, 1, 4]
        self.dt = np.dtype("bool, uint8, int16, uint8, int16, bool, bool")
        self.data = np.zeros(shape=self.shape, dtype=self.dt)

    def reshape(self, x, y, z):
        """
        Expands the internal data array if coordinates (x, y, z) are out of bounds
        relative to the current center.
        """
        new_shape = [0, 0, 0]
        self.max_shape = [0, 0, 0]
        
        resize_needed = False
        
        # Check X
        if abs(x) + 2 > self.shape[0] / 2:
            new_shape[0] = abs(x * 2) + 10
            resize_needed = True
        else:
            new_shape[0] = self.shape[0]

        # Check Y
        if abs(y) + 2 > self.shape[1] / 2:
            new_shape[1] = abs(y * 2) + 4
            resize_needed = True
        else:
            new_shape[1] = self.shape[1]

        # Check Z
        if abs(z) + 2 > self.shape[2] / 2:
            new_shape[2] = abs(z * 2) + 8
            resize_needed = True
        else:
            new_shape[2] = self.shape[2]
             
        if not resize_needed:
            return

        sX = self.shape[0]
        sY = self.shape[1]
        sZ = self.shape[2]
            
        # Roll data to center it in the array (un-wrap negative indices)
        self.data = np.roll(self.data, [sX//2, sY//2, sZ//2], [0, 1, 2])
        
        new_data = np.zeros(shape=new_shape, dtype=self.dt)
        # Copy old data to the beginning (or center? No, usually 0 to sX)
        new_data[:sX, :sY, :sZ] = self.data
        
        # Roll back to restore wrapped coordinate system relative to 0
        self.data = np.roll(new_data, [-sX//2, -sY//2, -sZ//2], [0, 1, 2])

        self.shape = new_shape
        
    def calculate_max_shape(self):
        """Calculates the maximum extent of the blocks in the grid."""
        sX = self.shape[0]
        sY = self.shape[1]
        sZ = self.shape[2]

        # This looks inefficient (O(N^3)), but logic is kept from original.
        # Could be optimized using np.nonzero on the 'Present' field.

        # Optimization using vectorization
        present_mask = self.data['f0'] # 'f0' is the first field (bool)
        if not np.any(present_mask):
            return

        indices = np.nonzero(present_mask)
        # Convert wrapped indices to centered relative coordinates
        rel_x = indices[0] - sX // 2
        rel_y = indices[1] - sY // 2
        rel_z = indices[2] - sZ // 2

        # Handle wrapping correctly?
        # If indices are raw, standard numpy indices are 0..N-1.
        # The logic `i - sX//2` implies we treat index sX//2 as 0.
        # But if we access data[x,y,z] with negative x, it wraps to N+x.
        # So -1 becomes N-1. N-1 - N//2 = N//2 - 1 (positive).
        # This logic assumes the data was NOT rolled and we are iterating raw indices.

        # Let's keep original iteration logic for safety, but cleaner loop.
        # Actually the original code iterates and checks `abs(i - sX//2)`.
        # This implies it treats the array as centered at sX//2.

        for i in range(sX):
            for j in range(sY):
                for k in range(sZ):
                    if self.data[i, j, k][0]:
                        # Original logic: access using wrapped indices logic
                        # But `i - sX//2` is just linear distance from center index.

                        # Just checking bounds
                        dist_x = abs(i - sX//2)
                        dist_y = abs(j - sY//2)
                        dist_z = abs(k - sZ//2)

                        if dist_x > self.max_shape[0]:
                            self.max_shape[0] = dist_x
                        if dist_y > self.max_shape[1]:
                            self.max_shape[1] = dist_y
                        if dist_z > self.max_shape[2]:
                            self.max_shape[2] = dist_z

    def add_data(self, data_b):
        """Merges another Data object into this one."""
        data_b.calculate_max_shape()
        max_x = data_b.max_shape[0] + abs(data_b.pos[0])
        max_y = data_b.max_shape[1] + abs(data_b.pos[1])
        max_z = data_b.max_shape[2] + abs(data_b.pos[2])

        self.reshape(max_x, max_y, max_z)

        # Roll B to center to make iteration easier/contiguous?
        new_data_b = np.roll(data_b.data, [data_b.shape[0]//2, data_b.shape[1]//2, data_b.shape[2]//2], axis=[0, 1, 2])

        for i in range(data_b.shape[0]):
            for j in range(data_b.shape[1]):
                for k in range(data_b.shape[2]):
                    if new_data_b[i, j, k][0]:
                        # Map coordinates
                        target_x = data_b.pos[0] + i - data_b.shape[0]//2
                        target_y = data_b.pos[1] + j - data_b.shape[1]//2
                        target_z = data_b.pos[2] + k - data_b.shape[2]//2

                        self.data[target_x, target_y, target_z] = new_data_b[i, j, k]

    def add_block(self, x, y, z, index, tick=0, random_amount=-1, needs_down=False, needs_up=False):
        """Adds a block at the specified coordinates."""
        self.reshape(x, y, z)
        # Using field access by index for assigning multiple fields
        # fields: bool (0), uint8 (1), int16 (2), uint8 (3), int16 (4), bool (5), bool (6)
        self.data[x, y, z] = (True, index, tick, random_amount if random_amount != -1 else 0, 0, needs_down, needs_up)

    def rotate(self, i, nbt=None):
        """Rotates the grid by 90 degrees steps."""
        i = i % 4

        if i == 1:
            axis = 0
            mvt = 1
            self.shape = [self.shape[2], self.shape[1], self.shape[0]]
        elif i == 2:
            axis = [0, 2]
            mvt = [1, 1]
        elif i == 3:
            axis = 2
            mvt = 1
            self.shape = [self.shape[2], self.shape[1], self.shape[0]]
        else:
            axis = 0
            mvt = 0

        self.data = np.roll(np.rot90(self.data, k=i, axes=(0, 2)), mvt, axis=axis)
        
        if nbt is None:
            return

        correspondance = nbt.get_rotation_index(i)

        # Apply rotation mapping to block indices
        # Optimization: use numpy mask
        present_mask = self.data['f0']
        indices = self.data['f1'] # Index field

        for old_idx, new_idx in correspondance.items():
            # Update indices where block is present and index matches
            mask = present_mask & (indices == old_idx)
            self.data['f1'][mask] = new_idx

    def flip(self, nbt):
        """Flips the grid along the Z axis."""
        self.data = np.roll(np.flip(self.data, axis=2), 1, axis=2)

        if nbt is None:
            return
        
        correspondance = nbt.get_rotation_index(2, True) # Symmetric flip?
        
        present_mask = self.data['f0']
        indices = self.data['f1']
        
        for old_idx, new_idx in correspondance.items():
            mask = present_mask & (indices == old_idx)
            self.data['f1'][mask] = new_idx

    def write_nbt(self, nbt):
        """Writes the data to the NBT object."""
        sX = self.shape[0]
        sY = self.shape[1]
        sZ = self.shape[2]

        for i in range(sX):
            for j in range(sY):
                for k in range(sZ):
                    # Using centered iteration logic
                    if self.data[i - sX//2, j - sY//2, k - sZ//2][0]:
                        block_idx = self.data[i - sX//2, j - sY//2, k - sZ//2][1]
                        pos = [
                            i - sX//2 + self.pos[0],
                            j - sY//2 + self.pos[1],
                            k - sZ//2 + self.pos[2]
                        ]
                        nbt.add_block(pos, block_idx)
        
    def set_layers(self, random_amount=5):
        """Calculates the layer for each block based on tick and randomness."""
        sX = self.shape[0]
        sY = self.shape[1]
        sZ = self.shape[2]

        for i in range(sX):
            for j in range(sY):
                for k in range(sZ):
                    i2 = i - sX//2
                    j2 = j - sY//2
                    k2 = k - sZ//2

                    if self.data[i2, j2, k2][0]:
                        # Field 3 is random delay
                        r_val = self.data[i2, j2, k2][3]
                        if r_val == 255: # Was check for -1? uint8 wraps or 255? In init I put 0 if -1.
                            # Original code: if(self.data[...][3] == 255): r = randomAmount
                            # My add_block puts 0 if -1.
                            # Let's assume if 0 it uses default? No, randomAmount parameter default is 5.
                            # In original code, default randomAmount in AddBlock was -1.
                            # If passed as -1, it was stored? self.data is uint8. -1 becomes 255.
                            # So 255 check is correct for "default".
                            r = random_amount
                        else:
                            r = r_val

                        # Field 2 is tick
                        tick_necessaire = self.data[i2, j2, k2][2] - randint(0, r) if r > 0 else self.data[i2, j2, k2][2]

                        # Field 4 is Layer
                        self.data[i2, j2, k2][4] = max(0, int(tick_necessaire))
                                                
                        # Field 5 is needsDown
                        if self.data[i2, j2, k2][5]:
                            self.data[i2, j2 - 1, k2][4] = self.data[i2, j2, k2][4]

                        # Field 6 is needsUp
                        if self.data[i2, j2 - 1, k2][6]: # Checking block below's needsUp?
                            # Original: if(self.data[i2,j2-1,k2][6]): self.data[i2,j2,k2][4] = self.data[i2,j2-1,k2][4]
                            # This implies if the block below needs UP, this block gets same layer.
                            self.data[i2, j2, k2][4] = self.data[i2, j2 - 1, k2][4]
