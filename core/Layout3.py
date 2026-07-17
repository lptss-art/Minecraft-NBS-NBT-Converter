"""
Layout 3 - Architecture "Shadowing" & Depth-First Search (DFS)

Ce module génère des circuits redstone de manière organique.
Au lieu de modifier directement le monde (ce qui oblige à des copies complètes coûteuses en mémoire),
il utilise un système de "Calques" (Shadowing) via la pile d'exécution récursive.

1. La gestion des points de départ (Les Ancres) :
   - Anchor : Représente un bout de câble redstone libre (point de départ potentiel).
   - AnchorManagerLayer : Gère les ancres de façon virtuelle sur des calques superposés.

2. La gestion des collisions et court-circuits :
   - ExclusionMapLayer : "Radar" à collisions qui empêche les câbles de fusionner (crosstalk).
     Il y a un calque pour les émetteurs (redstone) et un pour les récepteurs (noteblocks).

3. Le Moteur de Construction :
   - Layout3Brick : Le chef d'orchestre qui lit la musique et lance le moteur de recherche (dfs_find_path).
   - dfs_find_path : Explore les chemins possibles en empilant des calques virtuels. Si un chemin est valide,
     il le "commit" (le valide) dans le vrai monde.
"""
import numpy as np
import math
from core.layout_base import LayoutBase
from core.brick import Brick


class Anchor:
    """
    Une ancre représente un bout de câble redstone laissé libre.
    C'est un point de départ potentiel depuis lequel on peut prolonger le circuit.
    """
    def __init__(self, x, z, tick):
        self.x = x
        self.z = z
        self.tick = tick # Le moment (tick) où le signal arrive ici
        # Les 4 directions cardinales (Nord, Sud, Est, Ouest)
        self.free_directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def get_score(self, target_x, target_z, target_tick, alpha=0.2):
        """Calcule le coût de cette ancre (Distance + Pénalité de temps)."""
        dist = abs(self.x - target_x) + abs(self.z - target_z)
        time_penalty = alpha * abs(target_tick - self.tick)
        return dist + time_penalty


class AnchorManagerLayer:
    """
    Gère toutes les ancres disponibles de façon "virtuelle" via des calques superposés (Shadowing).
    Lors de l'exploration d'un chemin, on crée un nouveau calque pointant vers son parent.
    """
    def __init__(self, parent=None):
        self.parent = parent
        self.active_anchors = []
        self.consumed_directions = {} # anchor -> list of directions
        self.removed_anchors = set()

    def add_anchor(self, x, z, tick):
        new_anchor = Anchor(x, z, tick)
        self.active_anchors.append(new_anchor)
        return new_anchor

    def get_all_active_anchors(self):
        """Remonte tout l'historique des calques parents pour lister toutes les ancres encore utilisables."""
        anchors = list(self.active_anchors)
        if self.parent:
            parent_anchors = self.parent.get_all_active_anchors()
            for pa in parent_anchors:
                if pa not in self.removed_anchors and pa not in anchors:
                    anchors.append(pa)
        return anchors

    def get_best_anchor(self, target_x, target_z, target_tick):
        """Utilise le score des ancres pour trouver la meilleure parmi celles qui ont encore des directions libres."""
        all_anchors = self.get_all_active_anchors()
        # Filter anchors that still have free directions (considering layers)
        valid_anchors = []
        for anchor in all_anchors:
            free_dirs = self.get_free_directions(anchor)
            if free_dirs:
                valid_anchors.append(anchor)

        if not valid_anchors:
            return None
            
        valid_anchors.sort(key=lambda a: a.get_score(target_x, target_z, target_tick))
        return valid_anchors[0]

    def get_free_directions(self, anchor):
        """Regarde, pour une ancre donnée, quelles directions (N, S, E, O) n'ont pas encore été essayées."""
        base_free = list(anchor.free_directions)
        
        # Traverse up from self to gather consumed directions
        current = self
        while current:
            if anchor in current.consumed_directions:
                for d in current.consumed_directions[anchor]:
                    if d in base_free:
                        base_free.remove(d)
            current = current.parent

        return base_free

    def consume_direction(self, anchor, direction):
        """Note sur ce calque qu'une direction a été essayée (prise ou échouée). Si l'ancre n'a plus de directions, elle est supprimée."""
        if anchor not in self.consumed_directions:
            self.consumed_directions[anchor] = []
        self.consumed_directions[anchor].append(direction)

        if len(self.get_free_directions(anchor)) == 0:
            self.remove_anchor(anchor)

    def remove_anchor(self, anchor):
        if anchor in self.active_anchors:
            self.active_anchors.remove(anchor)
        else:
            self.removed_anchors.add(anchor)


class ExclusionMapLayer:
    """
    Radar à collisions et à court-circuits fonctionnant par calques (Shadowing).
    Sépare la logique des émetteurs (redstone/répéteurs) des récepteurs (noteblocks/pistons).
    """
    def __init__(self, parent=None, layer_type="redstone"):
        self.parent = parent
        self.layer_type = layer_type
        if self.parent:
            self.layer_type = self.parent.layer_type
        self.blocked_positions = {}
        self.occupied_blocks = {} # (x, y, z) -> block_type

    def mark_impossible(self, target_x, target_z, source_x, source_z, source_tick):
        if (target_x, target_z) not in self.blocked_positions:
            self.blocked_positions[(target_x, target_z)] = []
        self.blocked_positions[(target_x, target_z)].append({
            'source_coord': (source_x, source_z),
            'tick': source_tick
        })

    def occupy(self, x, y, z, block_type, tick=None, dx=0, dz=0):
        """
        Actionne la pose d'un bloc physique.
        Magie des exclusions : applique automatiquement des interdictions autour du bloc posé
        (ex: 4 cases autour pour la redstone) pour éviter que les câbles ne fusionnent (crosstalk).
        """
        self.occupied_blocks[(x, y, z)] = block_type

        if tick is None:
            return

        if self.layer_type == "redstone":
            if block_type == 'redstone_wire':
                for nx, nz in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    self.mark_impossible(x + nx, z + nz, x, z, tick)
            elif block_type == 'repeater':
                self.mark_impossible(x + dx, z + dz, x, z, tick)
                self.mark_impossible(x - dx, z - dz, x, z, tick)
                self.mark_impossible(x, z, x, z, tick)
        elif self.layer_type == "receiver":
            if block_type in ['note_block', 'piston']:
                for nx, nz in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    self.mark_impossible(x + nx, z + nz, x, z, tick)

    def is_blocked(self, target_x, target_z, current_tick):
        """Vérifie si on a le droit de poser un câble ici en s'assurant qu'il n'y a pas de conflit de tick (court-circuit)."""
        if (target_x, target_z) in self.blocked_positions:
            for conflict in self.blocked_positions[(target_x, target_z)]:
                if conflict['tick'] != current_tick:
                    return True
        if self.parent:
            return self.parent.is_blocked(target_x, target_z, current_tick)
        return False

    def is_physically_occupied(self, x, y, z):
        """Vérifie si un bloc dur (câble, instrument, air) est déjà présent physiquement à cet endroit précis."""
        if (x, y, z) in self.occupied_blocks:
            return self.occupied_blocks[(x, y, z)]
        if self.parent:
            return self.parent.is_physically_occupied(x, y, z)
        return None



class Layout3Brick(LayoutBase):
    """
    Chef d'orchestre de la génération organique.
    Contient le point de départ du circuit et les calques "racines" (le monde réel).
    """
    """
    Manages the organic layout (Layout 3).
    Dynamic opportunistic generator using a score system and 2D backtracking.
    """
    def __init__(self):
        super().__init__()
        # On définit une hauteur de base pour tout le circuit
        self.y_level = 0 
        
        # On instancie tes nouveaux gestionnaires
        self.anchor_manager = AnchorManagerLayer()
        self.impossible_redstone = ExclusionMapLayer(layer_type='redstone')
        self.impossible_notes = ExclusionMapLayer(layer_type='receiver')
        
        
        # On place le point de départ : (x, z, tick)
        self.anchor_manager.add_anchor(-1, -1, 0) 
        self.impossible_redstone.occupy(-1, self.y_level, -1, 'start_block')


    def add_note_organic(self, note, target_x, target_z, target_tick, is_half):
        """
        Tente de poser une note au bon tick.
        Lance la recherche récursive (DFS). Si elle réussit, récupère la liste des commandes validées
        et les exécute "pour de vrai" dans le monde réel (les calques racines).
        """
        commands_list = []
        success = self.dfs_find_path(
            target_x, target_z, target_tick, note, is_half,
            self.impossible_redstone, self.impossible_notes, self.anchor_manager,
            commands_list
        )

        if not success:
            print(f"Échec critique : Impossible de placer la note au tick {target_tick}")
            return False
            
        # Commit commands
        for cmd in commands_list:
            if cmd[0] == 'note':
                _, x, y, z, n, tick, source_anchor, direction = cmd
                self.impossible_notes.occupy(x, y, z, 'instrument')
                self.impossible_redstone.occupy(x, y, z, 'instrument')
                self.impossible_notes.occupy(x, y+1, z, 'note_block', tick=tick)
                self.impossible_redstone.occupy(x, y+1, z, 'note_block', tick=tick)
                self.impossible_notes.occupy(x, y+2, z, 'air')
                self.impossible_redstone.occupy(x, y+2, z, 'air')
                self.add_note(x, y+1, z, n)
                self.anchor_manager.consume_direction(source_anchor, direction)
            elif cmd[0] == 'redstone':
                _, x, y, z, tick, source_anchor, direction = cmd
                self.impossible_redstone.occupy(x, y, z, 'redstone_wire', tick=tick)
                self.impossible_notes.occupy(x, y, z, 'redstone_wire', tick=tick)
                self.add_block(x, y, z, "minecraft:redstone_wire", tick=tick, needs_down=True)
                self.anchor_manager.add_anchor(x, z, tick)
                self.anchor_manager.consume_direction(source_anchor, direction)
            elif cmd[0] == 'repeater':
                _, x, y, z, out_x, out_z, tick, new_tick, facing, delay, dx, dz, source_anchor, direction = cmd
                self.impossible_redstone.occupy(x, y, z, 'repeater', tick=tick, dx=dx, dz=dz)
                self.impossible_notes.occupy(x, y, z, 'repeater', tick=tick, dx=dx, dz=dz)
                self.add_block(x, y, z, "minecraft:repeater", properties={"facing": facing, "delay": delay}, tick=tick, needs_down=True)
                
                self.impossible_redstone.occupy(out_x, y, out_z, 'redstone_wire', tick=new_tick)
                self.impossible_notes.occupy(out_x, y, out_z, 'redstone_wire', tick=new_tick)
                self.add_block(out_x, y, out_z, "minecraft:redstone_wire", tick=new_tick, needs_down=True)
                self.anchor_manager.add_anchor(out_x, out_z, new_tick)
                self.anchor_manager.consume_direction(source_anchor, direction)

        return True

    def dfs_find_path(self, target_x, target_z, target_tick, note, is_half, current_redstone, current_notes, current_anchors, commands_list):
        """
        Le Cerveau : Fonction récursive qui empile les calques et simule les chemins.
        - S'il manque du temps : simule un répéteur (try_place_repeater_sim)
        - Si on est en avance : simule de la redstone pour avancer (try_expand_redstone_sim)
        - Si timing parfait : simule la note finale (try_place_note_setup_sim)
        S'annule proprement (Backtracking) en cas d'échec d'une branche.
        """
        all_anchors = current_anchors.get_all_active_anchors()
        valid_anchors = []
        for a in all_anchors:
            if current_anchors.get_free_directions(a):
                valid_anchors.append(a)

        if not valid_anchors:
            return False

        valid_anchors.sort(key=lambda a: a.get_score(target_x, target_z, target_tick))

        for best_anchor in valid_anchors:
            free_dirs = current_anchors.get_free_directions(best_anchor)
            free_dirs.sort(
                key=lambda d: abs((best_anchor.x + d[0]) - target_x) + abs((best_anchor.z + d[1]) - target_z)
            )

            for direction in free_dirs:
                new_redstone = ExclusionMapLayer(parent=current_redstone)
                new_notes = ExclusionMapLayer(parent=current_notes)
                new_anchors = AnchorManagerLayer(parent=current_anchors)

                dx, dz = direction
                test_x = best_anchor.x + dx
                test_z = best_anchor.z + dz
                tick_diff = target_tick - best_anchor.tick

                success = False

                if tick_diff < 0:
                    new_anchors.consume_direction(best_anchor, direction)
                    if self.dfs_find_path(target_x, target_z, target_tick, note, is_half, new_redstone, new_notes, new_anchors, commands_list):
                        return True
                    continue

                elif tick_diff == 0:
                    if len(free_dirs) > 1:
                        if self.try_place_note_setup_sim(test_x, test_z, best_anchor.tick, note, is_half, direction, new_redstone, new_notes):
                            new_anchors.consume_direction(best_anchor, direction)
                            commands_list.append(('note', test_x, self.y_level - 1, test_z, note, best_anchor.tick, best_anchor, direction))
                            return True
                        else:
                            if self.try_expand_redstone_sim(test_x, test_z, best_anchor.tick, best_anchor, new_redstone, new_notes, new_anchors):
                                new_anchors.consume_direction(best_anchor, direction)
                                commands_list.append(('redstone', test_x, self.y_level, test_z, best_anchor.tick, best_anchor, direction))
                                if self.dfs_find_path(target_x, target_z, target_tick, note, is_half, new_redstone, new_notes, new_anchors, commands_list):
                                    return True
                                commands_list.pop()
                    else:
                        if self.try_expand_redstone_sim(test_x, test_z, best_anchor.tick, best_anchor, new_redstone, new_notes, new_anchors):
                            new_anchors.consume_direction(best_anchor, direction)
                            commands_list.append(('redstone', test_x, self.y_level, test_z, best_anchor.tick, best_anchor, direction))
                            if self.dfs_find_path(target_x, target_z, target_tick, note, is_half, new_redstone, new_notes, new_anchors, commands_list):
                                return True
                            commands_list.pop()

                elif tick_diff > 0:
                    delay_to_burn = min(4, tick_diff)
                    if self.try_place_repeater_sim(test_x, test_z, best_anchor.tick, direction, delay_to_burn, best_anchor, new_redstone, new_notes, new_anchors):
                        new_anchors.consume_direction(best_anchor, direction)
                        out_x, out_z = test_x + dx, test_z + dz
                        new_tick = best_anchor.tick + delay_to_burn
                        facing = self.get_facing(dx, dz)
                        commands_list.append(('repeater', test_x, self.y_level, test_z, out_x, out_z, best_anchor.tick, new_tick, facing, delay_to_burn, dx, dz, best_anchor, direction))
                        if self.dfs_find_path(target_x, target_z, target_tick, note, is_half, new_redstone, new_notes, new_anchors, commands_list):
                            return True
                        commands_list.pop()

        return False

    def try_expand_redstone_sim(self, x, z, tick, source_anchor, redstone_layer, notes_layer, anchor_layer):
        if redstone_layer.is_blocked(x, z, tick) or notes_layer.is_blocked(x, z, tick):
            return False
        if redstone_layer.is_physically_occupied(x, self.y_level, z) or notes_layer.is_physically_occupied(x, self.y_level, z):
            return False

        redstone_layer.occupy(x, self.y_level, z, 'redstone_wire', tick=tick)
        notes_layer.occupy(x, self.y_level, z, 'redstone_wire', tick=tick)
        anchor_layer.add_anchor(x, z, tick)
        return True

    def try_place_repeater_sim(self, x, z, current_tick, direction, delay, source_anchor, redstone_layer, notes_layer, anchor_layer):
        dx, dz = direction
        out_x, out_z = x + dx, z + dz
        new_tick = current_tick + delay
        
        if redstone_layer.is_blocked(x, z, current_tick) or notes_layer.is_blocked(x, z, current_tick):
            return False
        if redstone_layer.is_physically_occupied(x, self.y_level, z) or notes_layer.is_physically_occupied(x, self.y_level, z):
            return False
            
        if redstone_layer.is_blocked(out_x, out_z, new_tick) or notes_layer.is_blocked(out_x, out_z, new_tick):
            return False
        if redstone_layer.is_physically_occupied(out_x, self.y_level, out_z) or notes_layer.is_physically_occupied(out_x, self.y_level, out_z):
            return False

        redstone_layer.occupy(x, self.y_level, z, 'repeater', tick=current_tick, dx=dx, dz=dz)
        notes_layer.occupy(x, self.y_level, z, 'repeater', tick=current_tick, dx=dx, dz=dz)

        redstone_layer.occupy(out_x, self.y_level, out_z, 'redstone_wire', tick=new_tick)
        notes_layer.occupy(out_x, self.y_level, out_z, 'redstone_wire', tick=new_tick)
        
        anchor_layer.add_anchor(out_x, out_z, new_tick)
        return True

    def try_place_note_setup_sim(self, x, z, tick, note, is_half, direction, redstone_layer, notes_layer):
        if redstone_layer.is_blocked(x, z, tick) or notes_layer.is_blocked(x, z, tick):
            return False
            
        y = self.y_level
        if notes_layer.is_physically_occupied(x, y-1, z) or redstone_layer.is_physically_occupied(x, y-1, z) or \
           notes_layer.is_physically_occupied(x, y, z) or redstone_layer.is_physically_occupied(x, y, z) or \
           notes_layer.is_physically_occupied(x, y+1, z) or redstone_layer.is_physically_occupied(x, y+1, z):
            return False

        notes_layer.occupy(x, y-1, z, 'instrument')
        redstone_layer.occupy(x, y-1, z, 'instrument')
        notes_layer.occupy(x, y, z, 'note_block', tick=tick)
        redstone_layer.occupy(x, y, z, 'note_block', tick=tick)
        notes_layer.occupy(x, y+1, z, 'air')
        redstone_layer.occupy(x, y+1, z, 'air')
        return True

    def get_facing(self, dx, dz):
        if dz > 0: return 'north'
        if dz < 0: return 'south'
        if dx > 0: return 'west'
        if dx < 0: return 'east'
        return 'north'



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
            
            target_x = int(tick/20)
            
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
