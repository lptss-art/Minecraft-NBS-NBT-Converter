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

        # We apply blocks directly to self. Using cursor_x to emulate translations safely
        cursor_x, cursor_y, cursor_z = 0, 0, 0

        def add_at(x, y, z, block_name, properties=None, needs_down=False):
            self.add_block(cursor_x + x, cursor_y + y, cursor_z + z, block_name, properties, tick=self.tick, needs_down=needs_down)

        def add_note_at(x, y, z, note):
            self.add_note_to_brick(self, cursor_x + x, cursor_y + y, cursor_z + z, note)

        # =========================================================================
        # CONFIGURATIONS DES COORDONNÉES
        # =========================================================================

        CONFIG_HALF = [
            (1,  0,  0, False),
            (0,  0, -1, False),
            (0,  0,  1, False),
            (1,  0,  0, True),
            (0, -1,  1, False),
            (0, -1, -1, False),
            (0, -1,  1, True),
            (0, -1, -1, False),
            (0, -1,  1, True),
            (0, -1, -1, False)
        ]

        CONFIG_INTEGER = [
            (0, (0, 0, 0), False), # le 1 sera posé en fonction de L ou pas L, mais sera fait en dernier
            (2, (1, -1,  1), False),
            (3, (-1, -1,  1), False),
            (4, (1, 0,  0), False) #le 4 sera posé si pas posé si demi notes ou si plus de 4 notes entières
        ]

        CONFIG_INTEGER_1 = [
            ("L", (0, 0,  -1)),
            ("I", (0, 0,  1))
        ]

        # Format : (index_relatif_note, (x, y, z), declenche_translation)
        CONFIG_INTEGER_PISTON = [
            (4, (0, -1, -1), True),
            (5, (0, -1,  1), False),
            (6, (0, -1, -1), True),  # Index 6 : Déclenche translate + redstone dust
            (7, (0, -1,  1), False),
            (8, (0, -1, -1), True),  # Index 8 : Déclenche translate + redstone dust
            (9, (0, -1,  1), False)
        ]

        # =========================================================================
        # LOGIQUE D'EXÉCUTION
        # =========================================================================

        # 1. Partie Demi-Notes (Côté Piston)
        if nb_half > 0:
            for i, (x, y, z, trigger_translation) in enumerate(CONFIG_HALF[:nb_half]):
                if trigger_translation:
                    cursor_x += 1
                    add_at(0,  0, 0, "minecraft:redstone_wire", needs_down=True)

                add_note_at(x, y, z, notes_half[i])

            cursor_x += 2
            add_at(0, 0, 0, "minecraft:sticky_piston", {"facing": "east"})
            add_at(1, 0, 0, "minecraft:redstone_block")
            cursor_x += 1

        # 2. Partie Notes Entières (Côté Piston)
        if nb_integer > 5 or (nb_integer > 4 and nb_half != 0):
            add_at(0,  0, 0, "minecraft:redstone_wire", needs_down=True)

            for idx, (x, y, z), trigger_translation in CONFIG_INTEGER_PISTON:
                if nb_integer > idx:
                    if trigger_translation:
                        cursor_x += 1
                        add_at(0,  0, 0, "minecraft:redstone_wire", needs_down=True)

                    add_note_at(x, y, z, notes_integer[idx])

            cursor_x += 1

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
            # The base center is now (0,0,0) with repeater at (-1,0,0) and previous block expected at (-2,0,0).
            # The new connection logic relies purely on these built-in positions.
            if direction % 4 == 0:
                pos[0] += 1
                pos[2] += -2
            elif direction % 4 == 1:
                pos[0] += 2
                pos[2] += -1
            elif direction % 4 == 2:
                pos[0] += 1
                pos[2] += 2
            else:
                pos[0] += 2
                pos[2] += 1

            direction += 1

            # Merge the brick into this track
            self.add_data(brick)
            last_tick = tick
        
