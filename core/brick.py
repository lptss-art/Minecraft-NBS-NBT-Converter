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
            new_block['properties'] = block.get('properties', {}).copy()
            new_block['pos'] = [
                block['pos'][0] + data_b.position[0],
                block['pos'][1] + data_b.position[1],
                block['pos'][2] + data_b.position[2]
            ]
            self.blocks.append(new_block)

    def add_block(self, x, y, z, block_name, properties=None, tick=0, random_delay_range=-1, needs_down=False, needs_up=False, nbt_data=None):
        """Adds a block at the specified coordinates."""
        if properties is None:
            properties = {}
        actual_random_delay = random_delay_range if random_delay_range != -1 else 255
        metadata = {
            'tick': tick,
            'random_delay_range': actual_random_delay,
            'layer': 0,
            'needs_down': needs_down,
            'needs_up': needs_up
        }
        if nbt_data:
            metadata.update(nbt_data)

        self.blocks.append({
            'pos': [x, y, z],
            'block_name': block_name,
            'properties': properties,
            'metadata': metadata
        })

    def clean(self, floor_block_name=None, floor_properties=None):
        """Removes duplicate blocks at the same coordinate, keeping the most recent one.
           If a block has 'needs_down' and there is nothing below it, it inserts a floor block.
        """
        seen = {}
        # Iterate forwards; latter blocks with same coordinate will overwrite previous ones
        for block in self.blocks:
            coord = tuple(block['pos'])
            seen[coord] = block

        self.blocks = list(seen.values())

        if floor_block_name is None:
            return

        if floor_properties is None:
            floor_properties = {}

        # Second pass: inject floor blocks for elements requiring support
        coord_map = {tuple(b['pos']): b for b in self.blocks}
        to_add = []
        for block in self.blocks:
            if block['metadata'].get('needs_down', False):
                below_coord = (block['pos'][0], block['pos'][1] - 1, block['pos'][2])
                if below_coord not in coord_map:
                    to_add.append({
                        'pos': list(below_coord),
                        'block_name': floor_block_name,
                        'properties': floor_properties,
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

    def rotate(self, rotations):
        """Rotates the grid blocks by 90 degree steps."""
        rotations = rotations % 4
        if rotations == 0:
            return

        directions = {'north': 0, 'east': 1, 'south': 2, 'west': 3}
        directions_i = {0: 'north', 1: 'east', 2: 'south', 3: 'west'}

        for block in self.blocks:
            x, y, z = block['pos']
            if rotations == 1:
                block['pos'] = [-z, y, x]
            elif rotations == 2:
                block['pos'] = [-x, y, -z]
            elif rotations == 3:
                block['pos'] = [z, y, -x]

            if 'properties' in block:
                props = block['properties']
                has_changed = False
                new_props = props.copy()

                if 'facing' in props:
                    direction = props['facing']
                    if direction in directions:
                        new_props['facing'] = directions_i[(directions[direction] + rotations) % 4]
                        has_changed = True

                elif any(d in props for d in directions.keys()):
                    for d in directions.keys():
                        if d in props:
                            new_d = directions_i[(directions[d] + rotations) % 4]
                            new_props[new_d] = props[d]
                            if new_d != d and d not in new_props: # clean up old direction if it wasn't overwritten
                                # We need to properly clear old direction if it's not being used, but typical behavior
                                # is to just remap. Better to build a fresh dict for directional keys.
                                pass
                            has_changed = True

                    if has_changed:
                        # Rebuild directional keys completely
                        rebuilt = {}
                        for k, v in props.items():
                            if k not in directions:
                                rebuilt[k] = v
                        for d in directions.keys():
                            if d in props:
                                new_d = directions_i[(directions[d] + rotations) % 4]
                                rebuilt[new_d] = props[d]
                        new_props = rebuilt

                if has_changed:
                    block['properties'] = new_props

    def flip(self, axis='z'):
        """Flips the grid along the specified axis ('x', 'y', or 'z')."""
        axis = axis.lower()
        if axis not in ('x', 'y', 'z'):
            raise ValueError("Axis must be 'x', 'y', or 'z'")

        axis_index = {'x': 0, 'y': 1, 'z': 2}[axis]

        for block in self.blocks:
            block['pos'][axis_index] = -block['pos'][axis_index]

            if 'properties' in block:
                props = block['properties']
                has_changed = False
                new_props = props.copy()

                # Determine which directional pair to swap based on the axis
                if axis == 'x':
                    swap_pairs = [('east', 'west')]
                elif axis == 'y':
                    swap_pairs = [('up', 'down'), ('top', 'bottom')]
                elif axis == 'z':
                    swap_pairs = [('north', 'south')]

                # In traditional Minecraft logic:
                # X axis runs West to East (- to +)
                # Y axis runs Down to Up (- to +)
                # Z axis runs North to South (- to +)

                if 'facing' in props:
                    direction = props['facing']
                    for dir1, dir2 in swap_pairs:
                        if direction == dir1:
                            new_props['facing'] = dir2
                            has_changed = True
                        elif direction == dir2:
                            new_props['facing'] = dir1
                            has_changed = True

                # Check for individual directional keys (like in redstone_wire)
                for dir1, dir2 in swap_pairs:
                    if dir1 in props or dir2 in props:
                        new_props[dir1] = props.get(dir2, 'none')
                        new_props[dir2] = props.get(dir1, 'none')

                        if new_props[dir1] == 'none':
                            del new_props[dir1]
                        if new_props[dir2] == 'none':
                            del new_props[dir2]
                        has_changed = True

                if has_changed:
                    block['properties'] = new_props

    def write_nbt(self, nbt):
        """Writes the blocks to the NBT object."""
        for block in self.blocks:
            pos = [
                block['pos'][0] + self.position[0],
                block['pos'][1] + self.position[1],
                block['pos'][2] + self.position[2]
            ]
            index = nbt.get_index_safe(block['block_name'], block['properties'])
            nbt.add_block(pos, index, metadata=block['metadata'])

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
