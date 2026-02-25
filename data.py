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
        self.position = [0, 0, 0]
        self.max_dimensions = [0, 0, 0]

        # 0: Present (bool)
        # 1: Block Index (uint8) - Palette index
        # 2: Tick (int16)
        # 3: Random Tick Delay (uint8)
        # 4: Layer (int16) - Calculated layer for NBT generation
        # 5: Needs Down (bool) - Needs block below
        # 6: Needs Up (bool) - Needs block above

        self.shape = [4, 1, 4]
        self.dtype = np.dtype("bool, uint8, int16, uint8, int16, bool, bool")
        self.data = np.zeros(shape=self.shape, dtype=self.dtype)

    def reshape(self, x, y, z):
        """
        Expands the internal data array if coordinates (x, y, z) are out of bounds
        relative to the current center.
        """
        new_shape = [0, 0, 0]
        self.max_dimensions = [0, 0, 0]
        
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

        size_x = self.shape[0]
        size_y = self.shape[1]
        size_z = self.shape[2]
            
        # Roll data to center it in the array (un-wrap negative indices)
        self.data = np.roll(self.data, [size_x//2, size_y//2, size_z//2], [0, 1, 2])
        
        new_data = np.zeros(shape=new_shape, dtype=self.dtype)
        # Copy old data to the beginning
        new_data[:size_x, :size_y, :size_z] = self.data
        
        # Roll back to restore wrapped coordinate system relative to 0
        self.data = np.roll(new_data, [-size_x//2, -size_y//2, -size_z//2], [0, 1, 2])

        self.shape = new_shape
        
    def calculate_max_dimensions(self):
        """Calculates the maximum extent of the blocks in the grid."""
        size_x = self.shape[0]
        size_y = self.shape[1]
        size_z = self.shape[2]

        present_mask = self.data['f0'] # 'f0' is the first field (bool)
        if not np.any(present_mask):
            return

        for i in range(size_x):
            for j in range(size_y):
                for k in range(size_z):
                    if self.data[i, j, k][0]:
                        dist_x = abs(i - size_x//2)
                        dist_y = abs(j - size_y//2)
                        dist_z = abs(k - size_z//2)

                        if dist_x > self.max_dimensions[0]:
                            self.max_dimensions[0] = dist_x
                        if dist_y > self.max_dimensions[1]:
                            self.max_dimensions[1] = dist_y
                        if dist_z > self.max_dimensions[2]:
                            self.max_dimensions[2] = dist_z

    def add_data(self, data_b):
        """Merges another Data object into this one."""
        data_b.calculate_max_dimensions()
        max_x = data_b.max_dimensions[0] + abs(data_b.position[0])
        max_y = data_b.max_dimensions[1] + abs(data_b.position[1])
        max_z = data_b.max_dimensions[2] + abs(data_b.position[2])

        self.reshape(max_x, max_y, max_z)

        # Roll B to center to make iteration easier/contiguous?
        new_data_b = np.roll(data_b.data, [data_b.shape[0]//2, data_b.shape[1]//2, data_b.shape[2]//2], axis=[0, 1, 2])

        for i in range(data_b.shape[0]):
            for j in range(data_b.shape[1]):
                for k in range(data_b.shape[2]):
                    if new_data_b[i, j, k][0]:
                        # Map coordinates
                        target_x = data_b.position[0] + i - data_b.shape[0]//2
                        target_y = data_b.position[1] + j - data_b.shape[1]//2
                        target_z = data_b.position[2] + k - data_b.shape[2]//2

                        self.data[target_x, target_y, target_z] = new_data_b[i, j, k]

    def add_block(self, x, y, z, index, tick=0, random_delay_range=-1, needs_down=False, needs_up=False):
        """Adds a block at the specified coordinates."""
        self.reshape(x, y, z)
        # Using field access by index for assigning multiple fields
        # fields: bool (0), uint8 (1), int16 (2), uint8 (3), int16 (4), bool (5), bool (6)
        # Default random_delay_range to 0 if -1 is passed (fixing bug)
        actual_random_delay = random_delay_range if random_delay_range != -1 else 255 # Using 255 as sentinel for default?
        # In set_layers I check for 255.

        self.data[x, y, z] = (True, index, tick, actual_random_delay, 0, needs_down, needs_up)

    def rotate(self, rotations, nbt=None):
        """Rotates the grid by 90 degrees steps."""
        rotations = rotations % 4

        if rotations == 1:
            axis = 0
            mvt = 1
            self.shape = [self.shape[2], self.shape[1], self.shape[0]]
        elif rotations == 2:
            axis = [0, 2]
            mvt = [1, 1]
        elif rotations == 3:
            axis = 2
            mvt = 1
            self.shape = [self.shape[2], self.shape[1], self.shape[0]]
        else:
            axis = 0
            mvt = 0

        self.data = np.roll(np.rot90(self.data, k=rotations, axes=(0, 2)), mvt, axis=axis)
        
        if nbt is None:
            return

        correspondence = nbt.get_rotation_index(rotations)

        # Apply rotation mapping to block indices
        present_mask = self.data['f0']
        indices = self.data['f1'] # Index field

        for old_idx, new_idx in correspondence.items():
            # Update indices where block is present and index matches
            mask = present_mask & (indices == old_idx)
            self.data['f1'][mask] = new_idx

    def flip(self, nbt):
        """Flips the grid along the Z axis."""
        self.data = np.roll(np.flip(self.data, axis=2), 1, axis=2)

        if nbt is None:
            return
        
        correspondence = nbt.get_rotation_index(2, True) # Symmetric flip?
        
        present_mask = self.data['f0']
        indices = self.data['f1']
        
        for old_idx, new_idx in correspondence.items():
            mask = present_mask & (indices == old_idx)
            self.data['f1'][mask] = new_idx

    def write_nbt(self, nbt):
        """Writes the data to the NBT object."""
        size_x = self.shape[0]
        size_y = self.shape[1]
        size_z = self.shape[2]

        for i in range(size_x):
            for j in range(size_y):
                for k in range(size_z):
                    # Using centered iteration logic
                    if self.data[i - size_x//2, j - size_y//2, k - size_z//2][0]:
                        block_idx = self.data[i - size_x//2, j - size_y//2, k - size_z//2][1]
                        pos = [
                            i - size_x//2 + self.position[0],
                            j - size_y//2 + self.position[1],
                            k - size_z//2 + self.position[2]
                        ]
                        nbt.add_block(pos, block_idx)
        
    def set_layers(self, default_random_amount=5):
        """Calculates the layer for each block based on tick and randomness."""
        size_x = self.shape[0]
        size_y = self.shape[1]
        size_z = self.shape[2]

        for i in range(size_x):
            for j in range(size_y):
                for k in range(size_z):
                    rel_x = i - size_x//2
                    rel_y = j - size_y//2
                    rel_z = k - size_z//2

                    if self.data[rel_x, rel_y, rel_z][0]:
                        # Field 3 is random delay
                        r_val = self.data[rel_x, rel_y, rel_z][3]
                        if r_val == 255:
                            random_range = default_random_amount
                        else:
                            random_range = r_val

                        # Field 2 is tick
                        current_tick = self.data[rel_x, rel_y, rel_z][2]
                        tick_required = current_tick - randint(0, random_range) if random_range > 0 else current_tick

                        # Field 4 is Layer
                        self.data[rel_x, rel_y, rel_z][4] = max(0, int(tick_required))
                                                
                        # Field 5 is needsDown
                        if self.data[rel_x, rel_y, rel_z][5]:
                            self.data[rel_x, rel_y - 1, rel_z][4] = self.data[rel_x, rel_y, rel_z][4]

                        # Field 6 is needsUp
                        if self.data[rel_x, rel_y - 1, rel_z][6]:
                            self.data[rel_x, rel_y, rel_z][4] = self.data[rel_x, rel_y - 1, rel_z][4]
