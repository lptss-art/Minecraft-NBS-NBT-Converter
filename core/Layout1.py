import numpy as np
from core.layout_base import LayoutBase
from core.brick import Brick

import numpy as np
from core.layout_base import LayoutBase

class BaseLaneBrick(LayoutBase):
    """
    Gère la construction de la ligne de base (Base Lane).
    Normalisée : Le point le plus haut de la structure (le toit/rail) est à Y = 0.
    """
    def __init__(self, start_x=0, start_y=0, start_z=0):
        # Plus de bidouille à base de "- 10" ici. L'origine Y de la brick est le TOIT.
        super().__init__(x=start_x, y=start_y+2, z=start_z)

    # ==========================================
    #      FONCTIONS INTERMÉDIAIRES DE FORME
    # ==========================================

    def fill_region(self, x_range, y_range, z_range, block_name, properties=None):
        """Remplit une zone 3D définie par des plages de coordonnées inclusives."""
        x_start, x_end = x_range
        y_start, y_end = y_range
        z_start, z_end = z_range
        
        for x in range(x_start, x_end + 1):
            for y in range(y_start, y_end + 1):
                for z in range(z_start, z_end + 1):
                    self.add_block(x, y, z, block_name, properties, tick=self.tick)

    def draw_floor(self, longueur_x, y, width_range=(-2, 2), block_name="minecraft:polished_blackstone_bricks"):
        """Dessine un sol horizontal de 'longueur_x' blocs le long de l'axe X."""
        self.fill_region((0, longueur_x - 1), (y, y), width_range, block_name)

    def draw_wall(self, longueur_x, y_range, z, block_name="minecraft:polished_blackstone_bricks"):
        """Dessine un mur vertical le long de l'axe X à la position Z."""
        self.fill_region((0, longueur_x - 1), y_range, (z, z), block_name)

    # ==========================================
    #            CONSTRUCTION DE LA BRICK
    # ==========================================

    def build(self, start=False):
        # On définit clairement la longueur sur l'axe X
        longueur_x = 12 if start else 6

        # --- RE-RECONSTRUCTION DES HAUTEURS (Toit à Y = 0) ---
        # Ancien Y=13 (Rail START) -> Devient Y = 0
        # Ancien Y=12 (Dalle sous le rail) -> Devient Y = -1
        # Ancien Y=11 (Plafond standard / lampes) -> Devient Y = -2
        # Ancien Y=9  (Sol haut) -> Devient Y = -4
        # Ancien Y=5  (Sol milieu) -> Devient Y = -8
        # Ancien Y=1  (Sol bas) -> Devient Y = -12
        # Les couches de redstone (anciens Y=10, 6, 2) deviennent Y = -3, -7, -11

        # Murs latéraux de tout en bas (Y=-13) jusqu'au plafond standard (Y=-2)
        # Largeur : Z = -2 et Z = 2
        self.draw_wall(longueur_x, (-13, -2), z=-2, block_name="minecraft:polished_blackstone_bricks")
        self.draw_wall(longueur_x, (-13, -2), z=2,  block_name="minecraft:polished_blackstone_bricks")

        # Sols des étages (sur toute la largeur de Z=-2 à Z=2)
        for y_sol in [-12, -8, -4, -2]:
            self.draw_floor(longueur_x, y=y_sol, width_range=(-2, 2))


        # --- ÉTAGES DE REDSTONE (Y = -11, -7, -3) ---
        for y_redstone in [-11, -7, -3]:
            if not start:
                # Répétition standard sur longueur_x = 6
                self.fill_region((0, 2), (y_redstone, y_redstone), (0, 0), "minecraft:repeater", {"facing": "west", "delay": 4})
                self.add_block(3, y_redstone, 0, "minecraft:repeater", {"facing": "west", "delay": 3})
                self.add_block(4, y_redstone, 0, "minecraft:redstone_wire")
                # Ligne finale en T (X=5, de Z=-1 à Z=1)
                self.fill_region((5, 5), (y_redstone, y_redstone), (-1, 1), "minecraft:redstone_wire")
            else:
                # Mode START : Une simple ligne droite continue de redstone au centre (Z=0)
                self.fill_region((0, longueur_x - 1), (y_redstone, y_redstone), (0, 0), "minecraft:redstone_wire")


        # --- LAMPES DE REDSTONE ---
        # Placées tout au bout, sous le plafond (Y=-2), sur les murs latéraux (Z=-2 et Z=2)
        x_lamp = 11 if start else 5
        self.add_block(x_lamp, -2, -2, "minecraft:redstone_lamp")
        self.add_block(x_lamp, -2, 2,  "minecraft:redstone_lamp")
        
        self.draw_floor(longueur_x, y=-1, width_range=(0, 0), block_name="minecraft:polished_blackstone_bricks") # Support
        self.fill_region((0, longueur_x - 1), (0, 0), (0, 0), "minecraft:rail", {"shape": "east_west"})

        # --- CAS SPÉCIFIQUE : START ---
        if start:
            from nbt.nbt import TAG_List, TAG_Compound, TAG_String, TAG_Byte
            # Le point culminant (le rail) est posé exactement à Y = 0

            
            self.add_block(0, 0, 0, "minecraft:polished_blackstone_bricks") # Bloc d'arrêt sur le rail

            # Chest with items
            items = TAG_List(TAG_Compound)

            item1 = TAG_Compound()
            item1['Slot'] = TAG_Byte(0)
            item1['id'] = TAG_String("minecraft:coal")
            item1['Count'] = TAG_Byte(1)
            items.append(item1)

            item2 = TAG_Compound()
            item2['Slot'] = TAG_Byte(1)
            item2['id'] = TAG_String("minecraft:minecart")
            item2['Count'] = TAG_Byte(1)
            items.append(item2)

            item3 = TAG_Compound()
            item3['Slot'] = TAG_Byte(2)
            item3['id'] = TAG_String("minecraft:furnace_minecart")
            item3['Count'] = TAG_Byte(1)
            items.append(item3)

            self.add_block(0, 1, 0, "minecraft:chest", properties={"facing": "east"}, nbt_data={"Items": items})

            # Descente du signal (les coordonnées Y ont toutes été décalées de -13)
            self.add_block(6, 0, 0, "minecraft:detector_rail", {"shape": "east_west"})
            self.add_block(6, -1, 1, "minecraft:redstone_wire")
            self.add_block(6, -2, 1, "minecraft:polished_blackstone_bricks")
            
            self.add_block(7, -2, 1, "minecraft:redstone_wire")
            self.add_block(7, -3, 1, "minecraft:polished_blackstone_bricks")
            self.add_block(7, -2, 0, "minecraft:air")
            
            self.add_block(7, -4, -1, "minecraft:redstone_wire")
            self.add_block(7, -5, -1, "minecraft:polished_blackstone_bricks")
            
            self.add_block(8, -5, -1, "minecraft:redstone_wire")
            self.add_block(8, -6, -1, "minecraft:polished_blackstone_bricks")
            self.add_block(8, -4, -1, "minecraft:air")
            
            self.add_block(9, -6, -1, "minecraft:redstone_wire")
            self.add_block(9, -7, -1, "minecraft:polished_blackstone_bricks")
            
            self.add_block(9, -8, 1, "minecraft:redstone_wire")
            self.add_block(9, -9, 1, "minecraft:polished_blackstone_bricks")
            
            self.add_block(10, -9, 1, "minecraft:redstone_wire")
            self.add_block(10, -10, 1, "minecraft:polished_blackstone_bricks")
            self.add_block(10, -8, 1, "minecraft:air")
            
            self.add_block(11, -10, 1, "minecraft:redstone_wire")
            self.add_block(11, -11, 1, "minecraft:polished_blackstone_bricks")

        self.tick += 1

class MinecartBrick(LayoutBase):
    """
    Manages the central minecart rail for Layout 1.
    Builds a 2-block long straight rail segment (progressing along X).
    """
    def __init__(self, start_x=0, start_y=0, start_z=0):
        super().__init__(x=start_x, y=start_y, z=start_z)

    def build(self):
        # We need a solid block under the rail
        self.add_block(-1, 0, 0, "minecraft:oak_planks")
        self.add_block(0, 0, 0, "minecraft:oak_planks")

        # Detector rail on the first block, powered rail on the second
        self.add_block(-1, 1, 0, "minecraft:detector_rail", {"shape": "east_west"})
        self.add_block(0, 1, 0, "minecraft:powered_rail", {"shape": "east_west"})

        self.tick += 1

class Layout1Brick(LayoutBase):
    """
    Manages a straight line layout (Repeater -> Block) for a single tick.
    Inherits from LayoutBase.
    """
    def __init__(self, start_x=0, start_y=0, start_z=0):
        super().__init__(x=start_x, y=start_y, z=start_z)

    def build(self, notes_integer=None, notes_half=None, delay=1):
        """
        Builds a single tick's worth of blocks for the straight layout.
        Notes branch off sideways from the central block.
        """
        notes_integer = notes_integer or []
        notes_half = notes_half or []
        nb_integer, nb_half = len(notes_integer), len(notes_half)

        CONFIG_HALF = [
            (0,  (1,  0, -4)),
            (1,  (2, 0, -3)),
        ]
        
        CONFIG_INT = [
            (0,  (1, 0, 0)),
            (1,  (1, 0, 1)),
        ]
        
        for idx, (x, y, z) in CONFIG_INT:
            if nb_integer > idx:
                self.add_note_to_brick(self, x, y, z, notes_integer[idx])
                
        for idx, (x, y, z) in CONFIG_HALF:
            if nb_half > idx:
                self.add_note_to_brick(self, x, y, z, notes_half[idx])
        
        if nb_integer == 0:
            self.add_block(1, 0, 0, "minecraft:redstone_lamp", tick=self.tick)
        
        if(nb_half!=0):
            self.add_block(1, 0, -2, "minecraft:redstone_block", tick=self.tick)
            self.add_block(1, 0, -1, "minecraft:sticky_piston", {"facing": "north"}, tick=self.tick)
        self.add_block(0, 0, 0, "minecraft:repeater", {"facing": "west", "delay": delay}, tick=self.tick, needs_down=True)
 
class Layout1Track(Brick):
    """
    Manages a sequence of Layout1Bricks, assembling them into a continuous straight line.
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

            brick = Layout1Brick()
            brick.tick = int(last_tick)

            # Get notes for this tick
            notes_entier = df_notes.loc[tick]['note entier']
            notes_demi = df_notes.loc[tick]['note demi']

            # Position of this brick in the track
            brick.position = [pos[0], pos[1], pos[2]]



            # Build natively
            brick.build(notes_entier, notes_demi, delay=actual_delay)

            pos[0] += 2

            # Merge the brick into this track
            self.add_data(brick)
            last_tick = tick
        
        
        #fini





class Layout1CompleteTrack(Brick):
    """
    Génère le Layout 1 Complet par morceaux (chunks) de 15 ticks.
    Avance pas à pas dans le temps, applique les transformations géométriques
    sur des pistes locales de 15 ticks, puis les assemble sur l'axe global X.
    """
    def __init__(self):
        super().__init__()

    def extraire_chunk_notes(self, df_notes, tick_debut, tick_fin):
        """
        Filtre le DataFrame pour le chunk [tick_debut, tick_fin[ et distribue 
        les notes de chaque tick de manière séquentielle (0 à 11) à travers les 6 pistes.
        """
        # 1. Sélection et réalignement du chunk temporel
        mask = (df_notes.index >= tick_debut) & (df_notes.index < tick_fin)
        df_chunk = df_notes.loc[mask].copy()
        
        if not df_chunk.empty:
            df_chunk.index = df_chunk.index - tick_debut

        # 2. Initialisation des 6 pistes avec des listes vides
        pistes = {
            "G_HAUT": df_chunk.copy(), "G_MID": df_chunk.copy(), "G_BAS": df_chunk.copy(),
            "D_HAUT": df_chunk.copy(), "D_MID": df_chunk.copy(), "D_BAS": df_chunk.copy()
        }
        
        for clef in pistes:
            pistes[clef]['note entier'] = [[] for _ in range(len(df_chunk))]
            pistes[clef]['note demi'] = [[] for _ in range(len(df_chunk))]

        # Ordre de distribution exact dicté par ta séquence (12 étapes)
        ordre_distribution = [
            "D_HAUT", "G_HAUT", "D_HAUT", "G_HAUT",  # 0, 1, 2, 3
            "D_MID",  "G_MID",  "D_MID",  "G_MID",   # 4, 5, 6, 7
            "D_BAS",  "G_BAS",  "D_BAS",  "G_BAS"    # 8, 9, 10, 11
        ]

        # 3. Répartition cyclique des notes
        for tick in df_chunk.index:
            notes_entier_brutes = df_chunk.loc[tick]['note entier'] or []
            notes_demi_brutes = df_chunk.loc[tick]['note demi'] or []

            # Distribution pour les notes entières
            for idx, note in enumerate(notes_entier_brutes):
                # Le modulo % 12 permet de boucler si un tick a plus de 12 notes
                piste_cible = ordre_distribution[idx % 12]
                pistes[piste_cible].loc[tick]['note entier'].append(note)

            # Même logique et même ordre pour les notes demi
            for idx, note in enumerate(notes_demi_brutes):
                piste_cible = ordre_distribution[idx % 12]
                pistes[piste_cible].loc[tick]['note demi'].append(note)

        return pistes

    def build_sequence(self, df_notes):
        """Parcourt la chanson par fenêtres de 15 ticks et assemble le tout."""
        if df_notes.empty:
            return

        tick_max = df_notes.index.max()
        taille_chunk_ticks = 15
        longueur_chunk_x = 6 
        
        lane_intro = BaseLaneBrick()
        lane_intro.build(start=True)
        self.add_data(lane_intro)
        pos_x = longueur_chunk_x*2
        
        
        lane = BaseLaneBrick()
        lane.position = [pos_x,0,0]
        lane.build(start=False)
        self.add_data(lane)
        
        pos_x += longueur_chunk_x   
        
        

        # Boucle principale par intervalles de 15 ticks
        for tick_debut in range(0, int(tick_max) + 1, taille_chunk_ticks):
            
            
            # 5. Remplissage de la colonne vertébrale centrale (BaseLane) pour ces 30 blocs
            # On pose des briques centrales jusqu'à couvrir la distance de ce chunk

            lane = BaseLaneBrick()
            lane.position = [pos_x,0,0]
            lane.build(start=False)
            self.add_data(lane)
            
            pos_x += longueur_chunk_x   

            

            
            tick_fin = tick_debut + taille_chunk_ticks
            
            # 1. Extraction et séparation des notes pour ce bloc de 15 ticks
            pistes_chunk = self.extraire_chunk_notes(df_notes, tick_debut, tick_fin)
            
            # 2. Instanciation et build des 6 pistes locales pour ce chunk
            tracks_locaux = {clef: Layout1Track() for clef in pistes_chunk.keys()}
            for clef, track_obj in tracks_locaux.items():
                track_obj.build_sequence(pistes_chunk[clef])


            # 4. Placement et imbrication des 6 pistes de notes dans la structure globale
            # On combine la position fixe (Y, Z) et la progression sur l'axe X (pos_x)
            configuration_pistes = {
                "G_HAUT": (-1, -3, -2), "G_MID": (-1, -7, -2), "G_BAS": (-1, -11, -2),
                "D_HAUT": (-1, -3,  2), "D_MID": (-1, -7,  2), "D_BAS": (-1, -11,  2),
            }

            for clef, (offset_x, offset_y, offset_z) in configuration_pistes.items():
                # La position globale prend en compte l'avancée pos_x de la session en cours
                tracks_locaux[clef].position = [pos_x + offset_x, offset_y, offset_z]
                tracks_locaux[clef].rotate(1)


                # Pistes de Gauche : Rotation de -1, puis Flip sur l'axe Z
                if clef in ["G_HAUT", "G_MID", "G_BAS"]:
                    tracks_locaux[clef].flip(axis='z')
                
                self.add_data(tracks_locaux[clef])


