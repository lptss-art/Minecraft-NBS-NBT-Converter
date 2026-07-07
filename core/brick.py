import numpy as np
from core.customNBT import CustomNBT
from random import randint

class Brick:
    """
    Represents a 3D structure of blocks as a list of block dictionaries.
    Provides support for translation, rotation, flipping, and NBT export.
    """

    def __init__(self, x=0, y=0, z=0, nbt=None, facing='south', direction=-1):
        self.position = [0, 0, 0]
        self.blocks = []

    def get_shape(self):
        """Computes a pseudo-shape (size_x, size_y, size_z) for backwards compatibility where necessary."""
        if not self.blocks:
            return (0, 0, 0)
        xs = [b['pos'][0] for b in self.blocks]
        ys = [b['pos'][1] for b in self.blocks]
        zs = [b['pos'][2] for b in self.blocks]

        # Max dimensions from center (0,0,0) as in old implementation
        max_x = max(max(xs), abs(min(xs)))
        max_y = max(max(ys), abs(min(ys)))
        max_z = max(max(zs), abs(min(zs)))

        return (max_x * 2 + 1, max_y * 2 + 1, max_z * 2 + 1)

    @property
    def shape(self):
        return self.get_shape()

    def translate(self, dx, dy, dz):
        """Translates the entire brick by shifting block coordinates."""
        for block in self.blocks:
            block['pos'][0] += dx
            block['pos'][1] += dy
            block['pos'][2] += dz

    def add_data(self, data_b):
        """Merges another Brick object into this one, applying data_b's position offset."""
        for block in data_b.blocks:
            new_block = block.copy()
            new_block['pos'] = [
                block['pos'][0] + data_b.position[0],
                block['pos'][1] + data_b.position[1],
                block['pos'][2] + data_b.position[2]
            ]
            self.blocks.append(new_block)

    def add_block(self, x, y, z, index, tick=0, random_delay_range=-1, needs_down=False, needs_up=False):
        """Adds a block at the specified coordinates."""
        actual_random_delay = random_delay_range if random_delay_range != -1 else 255
        self.blocks.append({
            'pos': [x, y, z],
            'index': index,
            'metadata': {
                'tick': tick,
                'random_delay_range': actual_random_delay,
                'layer': 0,
                'needs_down': needs_down,
                'needs_up': needs_up
            }
        })

    def clean(self, index_floor=-1):
        """Removes duplicate blocks at the same coordinate, keeping the most recent one.
           If a block has 'needs_down' and there is nothing below it, it inserts a floor block.
        """
        seen = {}
        # Iterate forwards; latter blocks with same coordinate will overwrite previous ones
        for block in self.blocks:
            coord = tuple(block['pos'])
            seen[coord] = block

        self.blocks = list(seen.values())

        if index_floor == -1:
            return

        # Second pass: inject floor blocks for elements requiring support
        coord_map = {tuple(b['pos']): b for b in self.blocks}
        to_add = []
        for block in self.blocks:
            if block['metadata'].get('needs_down', False):
                below_coord = (block['pos'][0], block['pos'][1] - 1, block['pos'][2])
                if below_coord not in coord_map:
                    to_add.append({
                        'pos': list(below_coord),
                        'index': index_floor,
                        'metadata': {
                            'tick': block['metadata']['tick'],
                            'random_delay_range': block['metadata']['random_delay_range'],
                            'layer': block['metadata']['layer'],
                            'needs_down': False,
                            'needs_up': False
                        }
                    })
                    coord_map[below_coord] = to_add[-1]

        self.blocks.extend(to_add)

    def rotate(self, rotations, nbt=None):
        """Rotates the grid blocks by 90 degree steps."""
        rotations = rotations % 4
        if rotations == 0:
            return

        for block in self.blocks:
            x, y, z = block['pos']
            if rotations == 1:
                block['pos'] = [-z, y, x]
            elif rotations == 2:
                block['pos'] = [-x, y, -z]
            elif rotations == 3:
                block['pos'] = [z, y, -x]

        if nbt is None:
            return

        correspondence = nbt.get_rotation_index(rotations)

        for block in self.blocks:
            if block['index'] in correspondence:
                block['index'] = correspondence[block['index']]

    def flip(self, nbt=None):
        """Flips the grid along the Z axis."""
        for block in self.blocks:
            block['pos'][2] = -block['pos'][2]

        if nbt is None:
            return

        correspondence = nbt.get_rotation_index(2, True)

        for block in self.blocks:
            if block['index'] in correspondence:
                block['index'] = correspondence[block['index']]

    def write_nbt(self, nbt):
        """Writes the blocks to the NBT object."""
        for block in self.blocks:
            pos = [
                block['pos'][0] + self.position[0],
                block['pos'][1] + self.position[1],
                block['pos'][2] + self.position[2]
            ]
            nbt.add_block(pos, block['index'], metadata=block['metadata'])

    def set_layers(self, default_random_amount=5):
        """Calculates the layer for each block based on tick and randomness."""
        # Create lookup dictionary by coordinate for dependency checking
        coord_map = {tuple(b['pos']): b for b in self.blocks}

        for block in self.blocks:
            meta = block['metadata']
            r_val = meta['random_delay_range']
            random_range = default_random_amount if r_val == 255 else r_val

            current_tick = meta['tick']
            tick_required = current_tick - randint(0, random_range) if random_range > 0 else current_tick

            meta['layer'] = max(0, int(tick_required))

        # Re-apply layers based on needs_down and needs_up dependencies
        # (This was originally multiple passes implicitly in the 3D grid loop, here we do a direct lookup)
        for block in self.blocks:
            meta = block['metadata']
            x, y, z = block['pos']

            if meta['needs_down']:
                below_coord = (x, y - 1, z)
                if below_coord in coord_map:
                    coord_map[below_coord]['metadata']['layer'] = meta['layer']

            # In the old code: if self.data[rel_x, rel_y - 1, rel_z][6]: current layer = below layer
            # That translates to: if the block below me has needs_up, I copy its layer.
            below_coord = (x, y - 1, z)
            if below_coord in coord_map and coord_map[below_coord]['metadata']['needs_up']:
                meta['layer'] = coord_map[below_coord]['metadata']['layer']
