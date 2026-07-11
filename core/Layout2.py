import numpy as np
from core.layout_base import LayoutBase
from core.brick import Brick

class Layout2Brick(LayoutBase):
    """
    Manages the layout of note blocks and redstone structures for a single tick.
    Inherits from LayoutBase.
    """
    def __init__(self, x=0, y=0, z=0, facing='south', direction=-1):
        super().__init__(x=x, y=y, z=z, facing=facing, direction=direction)
        
    def build(self, notes_integer=None, notes_half=None, delay=1, en_L=False):
        """
        Adds a segment of the song (one or more ticks) to the layout using the flat unified logic.
        """
        notes_integer = notes_integer or []
        notes_half = notes_half or []
        nb_integer, nb_half = len(notes_integer), len(notes_half)

        # We apply blocks directly to self, using built-in translation to shift coordinates natively.

        # =========================================================================
        # CONFIGURATIONS DES COORDONNÉES
        # =========================================================================

        # Format : (x, y, z, amount_of_translation)
        CONFIG_HALF = [
            (1,  0,  0, 0),
            (0,  0, -1, 0),
            (0,  0,  1, 0),
            (1,  0,  0, 2), # User requested translate by 2
            (0, -1,  1, 0),
            (0, -1, -1, 0),
            (0, -1,  1, 1), # Translate 1
            (0, -1, -1, 0),
            (0, -1,  1, 1), # Translate 1
            (0, -1, -1, 0)
        ]

        CONFIG_INTEGER = [
            (0, (0, 0, 0), 0),
            (2, (1, -1,  1), 0),
            (3, (-1, -1,  1), 0),
            (4, (1, 0,  0), 0)
        ]

        CONFIG_INTEGER_PISTON = [
            (4, (0, -1, -1), 1),
            (5, (0, -1,  1), 0),
            (6, (0, -1, -1), 1),
            (7, (0, -1,  1), 0),
            (8, (0, -1, -1), 1),
            (9, (0, -1,  1), 0)
        ]

        # =========================================================================
        # LOGIQUE D'EXÉCUTION
        # =========================================================================

        # 1. Partie Demi-Notes (Côté Piston)
        if nb_half > 0:
            for i, (x, y, z, translation_amount) in enumerate(CONFIG_HALF[:nb_half]):
                if translation_amount > 0:
                    for _ in range(translation_amount):
                        self.translate(1, 0, 0)
                        self.add_block(0,  0, 0, "minecraft:redstone_wire", tick=self.tick, needs_down=True)

                self.add_note_to_brick(self, x, y, z, notes_half[i])

            self.translate(2, 0, 0) # User requested to change it from 3 to 2
            self.add_block(0, 0, 0, "minecraft:sticky_piston", {"facing": "east"}, tick=self.tick)
            self.add_block(1, 0, 0, "minecraft:redstone_block", tick=self.tick)
            self.translate(1, 0, 0)

        # 2. Partie Notes Entières (Côté Piston)
        if nb_integer > 5 or (nb_integer > 4 and nb_half != 0):
            self.add_block(0,  0, 0, "minecraft:redstone_wire", tick=self.tick, needs_down=True)

            for idx, (x, y, z), trigger_translation in CONFIG_INTEGER_PISTON:
                if nb_integer > idx:
                    if trigger_translation:
                        self.translate(1, 0, 0)
                        self.add_block(0,  0, 0, "minecraft:redstone_wire", tick=self.tick, needs_down=True)

                    self.add_note_to_brick(self, x, y, z, notes_integer[idx])

            self.translate(1, 0, 0)

        # 3. Rotation si L (affecte tout ce qui a été construit jusqu'à présent)
        if en_L:
            self.rotate(1)

        # 4. Placement Notes Entières Base (CONFIG_INTEGER)
        # We process the remaining notes around the origin (0,0,0)
        # Note 0 is at (0,0,0)
        if nb_integer == 0:
            self.add_block(0, 0, 0, "minecraft:oak_planks", tick=self.tick)
        else:
            self.add_note_to_brick(self, 0, 0, 0, notes_integer[0])

        for idx, (x, y, z), _ in CONFIG_INTEGER:
            if idx == 0: continue

            # Conditionally place note 4 if no half notes and <= 4 integer notes
            if idx == 4:
                if nb_half == 0 and nb_integer <= 5:
                    if nb_integer > 4:
                        self.add_note_to_brick(self, x, y, z, notes_integer[4])
                continue

            if nb_integer > idx:
                self.add_note_to_brick(self, x, y, z, notes_integer[idx])

        # 5. Note 1 en fonction de L ou I (CONFIG_INTEGER_1)
        if nb_integer > 1:
            if en_L:
                self.add_note_to_brick(self, 1, 0, 0, notes_integer[1])
            else:
                self.add_note_to_brick(self, 0, 0, 1, notes_integer[1])

        # 6. Finitions Alimentation Redstone
        self.add_block(-1, 0, 0, "minecraft:repeater", {"facing": "west", "delay": delay}, tick=self.tick, needs_down=True)
        self.add_block(0, 0, -1, "minecraft:redstone_wire", tick=self.tick, needs_down=True)

class Layout2Track(Brick):
    """
    Manages a sequence of Layout2Bricks, assembling them into a continuous serpentine layout.
    """
    def __init__(self, branch_shape='I'):
        super().__init__()
        self.branch_shape = branch_shape

    def build_sequence(self, df_notes):
        """Processes notes and maps them to a serpentine sequence of bricks."""
        last_tick = -1
        direction = 0
        pos = [1, 0, 0]

        for tick in df_notes.index:
            tick_diff = int(tick - last_tick)
            actual_delay = max(1, min(4, tick_diff))

            brick = Layout2Brick()
            brick.tick = int(last_tick)

            # Get notes for this tick
            notes_entier = df_notes.loc[tick]['note entier']
            notes_demi = df_notes.loc[tick]['note demi']

            # Position of this brick in the track
            brick.position = [pos[0], pos[1], pos[2]]

            # Alternating en_L logic based on serpentine placement (%4=0: L, %4=1: I, %4=2: L, %4=3: I)
            en_L = (direction % 2 == 0)

            # Build natively
            brick.build(notes_entier, notes_demi, delay=actual_delay, en_L=en_L)

            # Align serpentine according to user instructions
            if direction % 4 == 0:
                pass # L
            elif direction % 4 == 1:
                brick.flip(axis='z')
                brick.rotate(3) # I, flip, rot 3
            elif direction % 4 == 2:
                brick.flip(axis='z') # L, flip
            else:
                brick.rotate(1) # I, rot 1

            # Update coordinates for NEXT brick
            # User request: "les espacementn des serpentins , ce pour les 4 cas. de 3 et pas de 2"
            if direction % 4 == 0:
                pos[2] += -3
            elif direction % 4 == 1:
                pos[0] += 3
            elif direction % 4 == 2:
                pos[2] += 3
            else:
                pos[0] += 3

            direction += 1

            # Merge the brick into this track
            self.add_data(brick)
            last_tick = tick
        
