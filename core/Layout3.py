import numpy as np
import math
from core.layout_base import LayoutBase
from core.brick import Brick

class Layout3Brick(LayoutBase):
    """
    Manages the organic layout (Layout 3).
    Tries to place note blocks and redstone infrastructure as close as possible to a target coordinate.
    """
    def __init__(self):
        super().__init__()
        # Grid to keep track of occupied coordinates
        # format: (x, y, z) -> {'type': str, 'tick': int, 'signal_in': list, 'signal_out': list}
        self.occupied_space = {}

    def is_free(self, x, y, z):
        """Checks if a column of 3 blocks (y-1, y, y+1) is free for a note block."""
        if (x, y-1, z) in self.occupied_space: return False
        if (x, y, z) in self.occupied_space: return False
        if (x, y+1, z) in self.occupied_space: return False
        return True

    def occupy(self, x, y, z, block_type, tick):
        """Marks a coordinate as occupied with metadata."""
        self.occupied_space[(x, y, z)] = {
            'type': block_type,
            'tick': tick,
            'signal_in': [],
            'signal_out': []
        }

    def add_note_organic(self, note, target_x, target_z, tick, is_half):
        """
        Finds the closest available spot around (target_x, target_z) to place a note block.
        """
        y = 0
        r = 0
        found = False
        place_x, place_z = target_x, target_z

        # Basic spiral search for the closest free spot
        while not found and r < 100:
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    # Check only the perimeter of the current radius
                    if abs(dx) == r or abs(dz) == r:
                        cx = target_x + dx
                        cz = target_z + dz

                        if self.is_free(cx, y, cz):
                            place_x, place_z = cx, cz
                            found = True
                            break
                if found:
                    break
            r += 1

        if found:
            self.tick = tick
            # Place the note block visually
            self.add_note(place_x, y, place_z, note)

            # Register in the grid
            self.occupy(place_x, y, place_z, 'note_block', tick)
            self.occupy(place_x, y - 1, place_z, 'instrument', tick)
            self.occupy(place_x, y + 1, place_z, 'air', tick)

            # TODO: Poser l'infrastructure redstone (repéteurs, poudre, pistons pour demi-notes)
            # et gérer la connexion (direction du signal).


class Layout3Track(Brick):
    """
    Manages the overall sequence for the organic Layout 3.
    """
    def __init__(self):
        super().__init__()

    def build_sequence(self, df_notes):
        brick = Layout3Brick()

        # Target coordinates, staying at (0, 0) for now as requested.
        target_x, target_z = 0, 0

        for tick in df_notes.index:
            notes_entier = df_notes.loc[tick]['note entier']
            notes_demi = df_notes.loc[tick]['note demi']

            for note in notes_entier:
                brick.add_note_organic(note, target_x, target_z, int(tick), is_half=False)

            for note in notes_demi:
                brick.add_note_organic(note, target_x, target_z, int(tick), is_half=True)

            # À l'avenir: target_x, target_z pourront être mis à jour ici
            # pour suivre la position d'un minecart, etc.

        self.add_data(brick)
