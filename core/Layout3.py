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

    def try_place_template(self, anchor, target_tick, is_half):
        """
        Tries to generate a redstone template from the anchor to satisfy target_tick.
        Returns (blocks_to_place, new_anchors) if successful, else None.
        """
        tick_diff = target_tick - anchor.tick

        # We can't connect to a future anchor
        if tick_diff < 0:
            return None

        blocks_to_place = []
        new_anchors = []

        cx, cy, cz = anchor.x, anchor.y, anchor.z
        dx, dz = anchor.direction

        # Advance 1 block from the anchor
        cx += dx
        cz += dz

        # Simple straight line template with repeaters to burn delay
        # In a full pathfinding A*, this would route around obstacles.
        # Here we do a straight projection in the anchor's direction.

        delay_left = tick_diff

        # 1. Route the delay
        while delay_left > 0:
            burn = min(4, delay_left)
            # Facing is opposite to direction of travel in Minecraft
            facing = 'north' if dz > 0 else 'south' if dz < 0 else 'west' if dx > 0 else 'east'

            blocks_to_place.append((cx, cy, cz, "minecraft:repeater", {"facing": facing, "delay": burn}, True))
            delay_left -= burn

            cx += dx
            cz += dz

        # 2. Place Note Infrastructure
        # Needs 3 blocks of height clearance
        note_coords = [(cx, cy-1, cz, 'instrument'), (cx, cy, cz, 'note_block'), (cx, cy+1, cz, 'air')]

        if is_half:
            # Need room for piston and redstone block (demi logic)
            blocks_to_place.append((cx, cy, cz, "minecraft:redstone_block", {}, False))
            cx += dx
            cz += dz
            facing_piston = 'north' if dz < 0 else 'south' if dz > 0 else 'west' if dx < 0 else 'east'
            blocks_to_place.append((cx, cy, cz, "minecraft:sticky_piston", {"facing": facing_piston}, False))
            cx += dx
            cz += dz
            note_coords = [(cx, cy-1, cz, 'instrument'), (cx, cy, cz, 'note_block'), (cx, cy+1, cz, 'air')]

        # Check collision and clearance
        all_proposed_blocks = [(x,y,z,btype) for x,y,z,btype,_,_ in blocks_to_place] + note_coords

        if not self.check_template_clearance(all_proposed_blocks, anchor):
            return None

        # If free, the note goes here
        note_placement = (cx, cy, cz)

        # Create a new anchor for future branches (branching sideways from the redstone wire before the note)
        # For simplicity, we just output straight ahead from the note block position
        new_anchors.append(RedstoneAnchor(cx, cy, cz, (dx, dz), target_tick))

        return blocks_to_place, note_placement, new_anchors

    def add_note_organic(self, note, target_x, target_z, target_tick, is_half):
        """
        Dynamically finds the best anchor and routes to place the note block.
        """
        # Sort anchors by score (cost/benefit)
        self.free_anchors.sort(key=lambda a: a.get_score(target_x, target_z, target_tick))

        best_anchor_index = -1
        placement_data = None

        for i, anchor in enumerate(self.free_anchors):
            res = self.try_place_template(anchor, target_tick, is_half)
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
        else:
            # Fallback si absolument tout est bloqué (Spiral basique d'urgence sans fil, juste pour poser la note)
            r = 0
            found = False
            while not found and r < 50:
                for dx in range(-r, r + 1):
                    for dz in range(-r, r + 1):
                        if abs(dx) == r or abs(dz) == r:
                            cx = target_x + dx
                            cz = target_z + dz

                            proposed = [
                                (cx, -1, cz, 'instrument'),
                                (cx, 0, cz, 'note_block'),
                                (cx, 1, cz, 'air')
                            ]
                            if self.check_template_clearance(proposed, None):
                                self.tick = target_tick
                                self.add_note(cx, 0, cz, note)
                                self.occupy(cx, -1, cz, 'instrument')
                                self.occupy(cx, 0, cz, 'note_block')
                                self.occupy(cx, 1, cz, 'air')
                                # New isolated anchor
                                self.free_anchors.append(RedstoneAnchor(cx, 0, cz, (0, 1), target_tick))
                                found = True
                                break
                    if found: break
                r += 1


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
