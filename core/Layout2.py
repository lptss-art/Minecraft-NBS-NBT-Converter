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

        # We apply blocks directly to a sub-brick first so we can manipulate it before the final merge
        brick_int = Brick()

        # We define a cursor that acts like self.translate
        cursor_x, cursor_y, cursor_z = 0, 0, 0

        def add_at(x, y, z, block_name, properties=None, needs_down=False):
            brick_int.add_block(cursor_x + x, cursor_y + y, cursor_z + z, block_name, properties, tick=self.tick, needs_down=needs_down)

        def add_note_at(x, y, z, note):
            self.add_note_to_brick(brick_int, cursor_x + x, cursor_y + y, cursor_z + z, note)

        # =========================================================================
        # CONFIGURATIONS DES COORDONNÉES
        # =========================================================================

        # Format : (x, y, z, declenche_translation_et_blocs)
        CONFIG_HALF = [
            (1,  0,  0, False),
            (0,  0, -1, False),
            (0,  0,  1, False),
            (1,  0,  0, True),   # Index 3 : Déclenche translate + blocs de support
            (0, -1,  1, False),
            (0, -1, -1, False),
            (0, -1,  1, True),   # Index 6 : Déclenche translate + blocs de support
            (0, -1, -1, False)
        ]

        # Format : (index_relatif_note, (x, y, z), declenche_translation)
        CONFIG_INTEGER_PISTON = [
            (3, (0, -1, -1), False),
            (4, (0, -1,  1), False),
            (5, (0, -1, -1), True),  # Index 5 : Déclenche translate + blocs
            (6, (0, -1,  1), False),
            (7, (0, -1, -1), True),  # Index 7 : Déclenche translate + blocs
            (8, (0, -1,  1), False)
        ]

        # Évaluation des cas pour les notes côté redstone
        case_1 = (nb_half == 0 and nb_integer <= 5)
        case_2 = (nb_half == 1 and nb_integer <= 4)

        # Renvoie les coordonnées (x, y, z) dynamiquement selon l'état du circuit
        CONFIG_REDSTONE = {
            1: lambda: (1, 0, 1) if (case_1 or not en_L) else (2, 0, 0),
            2: lambda: (0, -1, -1),
            3: lambda: (0, -1, -1) if case_1 else ((2, -1, -1) if (case_2 or en_L) else None),
            4: lambda: (2, -1, -1) if case_1 else None
        }

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

            if nb_half >= 4:
                cursor_x += 1

            cursor_x += 2
            add_at(0, 0, 0, "minecraft:sticky_piston", {"facing": "east"})
            add_at(1, 0, 0, "minecraft:redstone_block")
            cursor_x += 1

        # 2. Partie Notes Entières (Côté Piston)
        if nb_integer > 5 or (nb_integer > 4 and nb_half != 0):
            offset = 1 if en_L else 0
            add_at(0,  0, 0, "minecraft:redstone_wire", needs_down=True)

            for idx, (x, y, z), trigger_translation in CONFIG_INTEGER_PISTON:
                if nb_integer >= (idx + 1 + offset):
                    if trigger_translation:
                        cursor_x += 1
                        add_at(0,  0, 0, "minecraft:redstone_wire", needs_down=True)

                    add_note_at(x, y, z, notes_integer[idx + offset])

            cursor_x += 1

        # 3. Rotation & Centre (L'intention de "en_L" prend tout son sens ici)
        if en_L:
            brick_int.rotate(1)

        brick_int.translate(1, 0, 0)

        if nb_integer == 0:
            # We use oak planks for the center block as standard
            brick_int.add_block(1, 0, 0, "minecraft:oak_planks", tick=self.tick)
        else:
            self.add_note_to_brick(brick_int, 1, 0, 0, notes_integer[0])

        # 4. Notes Côté Redstone
        for idx in range(1, 5):
            if nb_integer >= idx + 1 and idx in CONFIG_REDSTONE:
                coords = CONFIG_REDSTONE[idx]()
                if coords:
                    self.add_note_to_brick(brick_int, *coords, notes_integer[idx])

        # 5. Finitions Alimentation Redstone
        brick_int.add_block(0,  0,  0, "minecraft:repeater", {"facing": "west", "delay": delay}, tick=self.tick, needs_down=True)

        brick_int.add_block(1,  0, -1, "minecraft:redstone_wire", tick=self.tick, needs_down=True)

        self.add_data(brick_int)

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

            # Alternating en_L logic based on serpentine placement
            en_L = (direction % 2 == 1)

            # Build natively
            brick.build(notes_entier, notes_demi, delay=actual_delay, en_L=en_L)

            # Align serpentine
            if direction % 4 == 0:
                pass # Straight +X
            elif direction % 4 == 1:
                brick.flip(axis='z')
                brick.rotate(3)
            elif direction % 4 == 2:
                brick.flip(axis='z')
            else:
                brick.rotate(1)

            # Update coordinates for NEXT brick
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
        
