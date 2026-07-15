import numpy as np
import math
from core.layout_base import LayoutBase
from core.brick import Brick

class RedstoneAnchor:
    def __init__(self, x, y, z, direction, tick):
        self.x = x
        self.y = y
        self.z = z
        self.direction = direction # (dx, dz)
        self.tick = tick

    def get_score(self, target_x, target_z, target_tick, alpha=5.0):
        """
        Score = Distance Physique + alpha * abs(Différence de tick)
        On privilégie une borne proche physiquement et temporellement.
        """
        dist = abs(self.x - target_x) + abs(self.z - target_z)
        time_penalty = alpha * abs(target_tick - self.tick)
        return dist + time_penalty

class Layout3Brick(LayoutBase):
    """
    Manages the organic layout (Layout 3).
    Dynamic opportunistic generator using a score system and backtracking.
    """
    def __init__(self):
        super().__init__()
        # Grid to keep track of occupied coordinates: (x, y, z) -> type
        self.occupied_space = {}
        # Available connection points
        self.free_anchors = []

        # Initialize the start of the circuit (e.g., a button at 0,0,0)
        # Assuming the signal starts at tick 0 heading positive Z
        self.free_anchors.append(RedstoneAnchor(0, 0, 0, (0, 1), 0))
        self.occupy(0, 0, 0, 'start')

    def check_template_clearance(self, all_proposed_blocks, anchor_obj):
        """
        Checks that a 3x3x3 volume around each proposed block is free,
        ignoring blocks that are part of the template itself, the anchor block,
        and the block directly feeding the anchor.
        Adds extra clearance for moving parts like pistons, but only in their direction of movement.
        """
        proposed_coords = { (x, y, z) for x, y, z, _ in all_proposed_blocks }

        anchor_coord = None
        anchor_feeder_coord = None

        if anchor_obj:
            anchor_coord = (anchor_obj.x, anchor_obj.y, anchor_obj.z)
            # The block feeding the anchor is directly behind it
            anchor_feeder_coord = (anchor_obj.x - anchor_obj.direction[0], anchor_obj.y, anchor_obj.z - anchor_obj.direction[1])

        for i, (x, y, z, block_name) in enumerate(all_proposed_blocks):

            # We want to be a bit softer on the first block connecting to the anchor to prevent auto-sabotage
            is_first_block = (i == 0)

            # Base clearance is 1 block in all directions (3x3x3)
            clearance_x, clearance_y, clearance_z = 1, 1, 1

            # Special clearance for moving parts (piston/redstone block)
            if "piston" in block_name or "redstone_block" in block_name:
                # We only need extra clearance in the direction of the movement.
                # In our simple template projection, the movement is always along anchor.direction
                # However, since we don't pass the direction directly here, we can infer it
                # from the fact that the piston extends forward.
                # To be safe and precise as requested: 1 block on inactive sides, 2 blocks on active axis.
                if anchor_obj:
                    if anchor_obj.direction[0] != 0: # Moving along X
                        clearance_x = 2
                    if anchor_obj.direction[1] != 0: # Moving along Z
                        clearance_z = 2
                else:
                    # Fallback if no anchor (should not happen for pistons in normal flow)
                    clearance_x, clearance_y, clearance_z = 2, 2, 2

            for dx in range(-clearance_x, clearance_x + 1):
                for dy in range(-clearance_y, clearance_y + 1):
                    for dz in range(-clearance_z, clearance_z + 1):
                        check_coord = (x + dx, y + dy, z + dz)

                        # Ignore self-collisions within the template being placed
                        if check_coord in proposed_coords:
                            continue

                        # Ignore the anchor block we are connecting to
                        if check_coord == anchor_coord:
                            continue

                        # Ignore the feeder block behind the anchor to prevent auto-sabotage
                        if check_coord == anchor_feeder_coord:
                            continue

                        # Soften clearance for the first block: if it brushes against something far back, allow it
                        if is_first_block and anchor_obj:
                            # If the checked coordinate is "behind" the first block relative to direction of travel
                            # We tolerate it to avoid snagging on the circuit that fed the anchor.
                            if anchor_obj.direction[0] > 0 and dx < 0: continue
                            if anchor_obj.direction[0] < 0 and dx > 0: continue
                            if anchor_obj.direction[1] > 0 and dz < 0: continue
                            if anchor_obj.direction[1] < 0 and dz > 0: continue

                        # If we hit an occupied space belonging to something else, fail
                        if check_coord in self.occupied_space:
                            return False
        return True

    def is_free(self, coords):
        """Checks if a list of (x, y, z) coordinates are free."""
        for x, y, z in coords:
            if (x, y, z) in self.occupied_space: return False
        return True

    def occupy(self, x, y, z, block_type):
        """Marks a coordinate as occupied."""
        self.occupied_space[(x, y, z)] = block_type

    def get_facing(self, dx, dz):
        if dz > 0: return 'north'
        if dz < 0: return 'south'
        if dx > 0: return 'west'
        if dx < 0: return 'east'
        return 'north'

    def try_place_template(self, anchor, target_tick, is_half, target_x, target_z):
        """
        Uses BFS to find a path from the anchor to a free space closest to (target_x, target_z)
        while burning the necessary delay using repeaters, and using redstone wire for 0-delay distance.
        """
        tick_diff = target_tick - anchor.tick
        if tick_diff < 0:
            return None

        from collections import deque

        # State: (x, z, delay_left, current_direction, path_taken)
        # path_taken: list of tuples (x, y, z, block_name, properties, needs_down, new_direction)
        start_x, start_z = anchor.x + anchor.direction[0], anchor.z + anchor.direction[1]

        queue = deque([(start_x, start_z, tick_diff, anchor.direction, [])])
        visited = set()
        visited.add((start_x, start_z, tick_diff, anchor.direction))

        best_end_state = None
        best_end_dist = float('inf')

        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        # BFS search radius limit to prevent infinite loops
        max_search_depth = 50

        while queue:
            cx, cz, delay_left, current_dir, path = queue.popleft()

            if len(path) > max_search_depth:
                continue

            # If we burned all delay, we can potentially place the note block here
            if delay_left == 0:
                # Check if we can place the note infrastructure here
                cy = anchor.y

                blocks_to_place = []
                for px, pz, p_delay, p_dir, p_block, p_props, p_needs_down in path:
                    blocks_to_place.append((px, cy, pz, p_block, p_props, p_needs_down))

                note_cx, note_cz = cx, cz
                note_coords = [(note_cx, cy-1, note_cz, 'instrument'), (note_cx, cy, note_cz, 'note_block'), (note_cx, cy+1, note_cz, 'air')]

                if is_half:
                    blocks_to_place.append((note_cx, cy, note_cz, "minecraft:redstone_block", {}, False))
                    note_cx += current_dir[0]
                    note_cz += current_dir[1]
                    facing_piston = self.get_facing(current_dir[0], current_dir[1])
                    blocks_to_place.append((note_cx, cy, note_cz, "minecraft:sticky_piston", {"facing": facing_piston}, False))
                    note_cx += current_dir[0]
                    note_cz += current_dir[1]
                    note_coords = [(note_cx, cy-1, note_cz, 'instrument'), (note_cx, cy, note_cz, 'note_block'), (note_cx, cy+1, note_cz, 'air')]

                all_proposed_blocks = [(x,y,z,btype) for x,y,z,btype,_,_ in blocks_to_place] + note_coords

                if self.check_template_clearance(all_proposed_blocks, anchor):
                    dist = abs(note_cx - target_x) + abs(note_cz - target_z)
                    if dist < best_end_dist:
                        best_end_dist = dist

                        # Generate new anchors (branching sideways from the wire before the note, or after the note)
                        new_anchors = []

                        # The wire right before the note (or the note itself) can be a source.
                        # For chords, we want to branch off the redstone dust that led here.
                        # Find the last redstone wire in the path
                        last_wire_pos = None
                        for px, py, pz, pblock, _, _ in reversed(blocks_to_place):
                            if pblock == "minecraft:redstone_wire":
                                last_wire_pos = (px, pz)
                                break

                        if last_wire_pos:
                            wx, wz = last_wire_pos
                            # Add anchors branching off this wire
                            for branch_dir in directions:
                                if branch_dir != current_dir and branch_dir != (-current_dir[0], -current_dir[1]):
                                    new_anchors.append(RedstoneAnchor(wx, cy, wz, branch_dir, target_tick))

                        # Also add an anchor continuing straight after the note
                        new_anchors.append(RedstoneAnchor(note_cx, cy, note_cz, current_dir, target_tick))

                        best_end_state = (blocks_to_place, (note_cx, cy, note_cz), new_anchors)

                        # Found a valid placement. We could break early, but BFS finds shortest path anyway.
                        # Because we want closest to target, we might just accept the first valid one if we trust the heuristic,
                        # but our BFS expands outward from the anchor, not necessarily towards the target.
                        # Breaking here gives us the shortest wire length from anchor, which is usually compact.
                        break

                # Even if delay is 0, we could theoretically keep putting redstone wire to get closer to the target.
                # Let's allow expanding with redstone wire.

            # Expand neighbors
            for ndx, ndz in directions:
                # Don't go backwards
                if ndx == -current_dir[0] and ndz == -current_dir[1]:
                    continue

                nx, nz = cx + ndx, cz + ndz

                # If we still need to burn delay, we MUST place a repeater (or we can place wire to move around, but let's say repeater)
                if delay_left > 0:
                    burn = min(4, delay_left)
                    facing = self.get_facing(ndx, ndz)
                    new_path = list(path)
                    new_path.append((cx, nz if ndx==0 else cz, burn, (ndx, ndz), "minecraft:repeater", {"facing": facing, "delay": burn}, True))
                    # Actually, we place the block at cx, cz.
                    new_path[-1] = (cx, cz, burn, (ndx, ndz), "minecraft:repeater", {"facing": facing, "delay": burn}, True)

                    state = (nx, nz, delay_left - burn, (ndx, ndz))
                    if state not in visited:
                        visited.add(state)
                        queue.append((nx, nz, delay_left - burn, (ndx, ndz), new_path))

                    # Alternatively, we could just lay redstone wire to maneuver BEFORE placing the repeater
                    new_path_wire = list(path)
                    new_path_wire.append((cx, cz, 0, (ndx, ndz), "minecraft:redstone_wire", {}, True))
                    state_wire = (nx, nz, delay_left, (ndx, ndz))
                    if state_wire not in visited:
                        visited.add(state_wire)
                        queue.append((nx, nz, delay_left, (ndx, ndz), new_path_wire))
                else:
                    # Delay is 0, we can only place redstone wire to maneuver
                    new_path = list(path)
                    new_path.append((cx, cz, 0, (ndx, ndz), "minecraft:redstone_wire", {}, True))
                    state = (nx, nz, 0, (ndx, ndz))
                    if state not in visited:
                        visited.add(state)
                        queue.append((nx, nz, 0, (ndx, ndz), new_path))

        return best_end_state

    def add_note_organic(self, note, target_x, target_z, target_tick, is_half):
        """
        Dynamically finds the best anchor and routes to place the note block.
        """
        # Sort anchors by score (cost/benefit)
        self.free_anchors.sort(key=lambda a: a.get_score(target_x, target_z, target_tick))

        best_anchor_index = -1
        placement_data = None

        for i, anchor in enumerate(self.free_anchors):
            res = self.try_place_template(anchor, target_tick, is_half, target_x, target_z)
            if res is not None:
                placement_data = res
                best_anchor_index = i
                break

        if placement_data is not None:
            blocks_to_place, note_pos, new_anchors = placement_data

            # Commit the template to the grid and the NBT array
            self.tick = target_tick

            for bx, by, bz, btype, props, needs_down in blocks_to_place:
                self.occupy(bx, by, bz, btype)
                self.add_block(bx, by, bz, btype, properties=props, tick=self.tick, needs_down=needs_down)

            # Place the Note
            nx, ny, nz = note_pos
            self.add_note(nx, ny, nz, note)
            self.occupy(nx, ny-1, nz, 'instrument')
            self.occupy(nx, ny, nz, 'note_block')
            self.occupy(nx, ny+1, nz, 'air')

            # Update Anchors
            # Remove the used anchor to prevent saturation and ghost calculations
            self.free_anchors.pop(best_anchor_index)
            self.free_anchors.extend(new_anchors)


class Layout3Track(Brick):
    """
    Manages the overall sequence for the organic Layout 3.
    """
    def __init__(self):
        super().__init__()

    def build_sequence(self, df_notes):
        brick = Layout3Brick()

        # Target coordinates: (0, 0)
        target_x, target_z = 0, 0

        for tick in df_notes.index:
            notes_entier = df_notes.loc[tick]['note entier']
            notes_demi = df_notes.loc[tick]['note demi']

            if notes_entier is not None:
                # Handle cases where pandas might have inserted a NaN instead of None
                if not isinstance(notes_entier, float):
                    for note in notes_entier:
                        brick.add_note_organic(note, target_x, target_z, int(tick), is_half=False)

            if notes_demi is not None:
                if not isinstance(notes_demi, float):
                    for note in notes_demi:
                        brick.add_note_organic(note, target_x, target_z, int(tick), is_half=True)

            # target_x, target_z updates could go here

        self.add_data(brick)
