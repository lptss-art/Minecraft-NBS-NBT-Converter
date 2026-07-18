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
import math
import random


class Anchor:
    def __init__(self, x, z, tick, allowed_directions, is_half=False):
        self.x = x
        self.z = z
        self.tick = tick
        self.is_half = is_half
        self.free_directions = list(allowed_directions)

    def get_score(self, target_x, target_z, target_tick):
        """
        Calcule le coût de cette ancre (le plus petit score est le meilleur).
        Utilise une distance classique (Euclidienne) et favorise fortement le bon tick.
        """
        # Distance classique (ligne droite)
        dist = math.hypot(self.x - target_x, self.z - target_z)
        
        tick_diff = target_tick - self.tick
        
        # Pénalité temporelle
        if tick_diff == 0:
            # Timing parfait : on donne un bonus pour forcer l'algo à l'essayer en premier
            time_penalty = -10.0 
        elif tick_diff > 0:
            # En retard : on pénalise. 
            # faible valeur = plus susceptible de mettre des repeteurs pour recuperer le signal autre part
            time_penalty = 10 * tick_diff
        else:
            # Trop tard (tick dépassé) : ce chemin est temporellement impossible.
            time_penalty = float('inf')
            
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

    def add_anchor(self, x, z, tick, dx=0, dz=0, block_type="redstone", is_half=False):
        """
        Crée une ancre et détermine intelligemment les directions possibles en fonction
        du bloc qui vient d'être posé et de la direction (dx, dz) utilisée pour y arriver.
        """
        allowed_dirs = []
        
        # Si c'est le point de départ (aucun mouvement)
        if dx == 0 and dz == 0:
            allowed_dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            
        elif block_type == "repeater":
            # Le signal sort d'un répéteur : il ne peut aller que tout droit
            allowed_dirs = [(dx, dz)]
            
        elif block_type == "redstone":
            # Le signal sort d'un câble redstone : 3 directions possibles (on exclut l'arrière)
            back_x, back_z = -dx, -dz
            for nx, nz in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                if nx == back_x and nz == back_z:
                    continue
                allowed_dirs.append((nx, nz))
        else:
            # Sécurité (fallback) : 4 directions par défaut
            allowed_dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        new_anchor = Anchor(x, z, tick, allowed_directions=allowed_dirs, is_half=is_half)
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

    def get_anchor(self, x, z):
        """
        Cherche et retourne une ancre active située aux coordonnées exactes (x, z).
        Renvoie None si aucune ancre n'existe à cet emplacement ou si elle a été supprimée.
        """
        # On passe par get_all_active_anchors pour respecter la logique 
        # d'héritage des calques et des ancres supprimées.
        for anchor in self.get_all_active_anchors():
            if anchor.x == x and anchor.z == z:
                return anchor
                
        return None


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
        self.occupied_blocks = {} # (x, z) -> block_type

    def mark_impossible(self, target_x, target_z, source_x, source_z, source_tick, source_is_half):
        if (target_x, target_z) not in self.blocked_positions:
            self.blocked_positions[(target_x, target_z)] = []
        self.blocked_positions[(target_x, target_z)].append({
            'source_coord': (source_x, source_z),
            'tick': source_tick,
            'is_half': source_is_half
        })

    def occupy(self, x, z, block_type, tick=None, dx=0, dz=0, is_half=False):
        self.occupied_blocks[(x, z)] = block_type

        if tick is None:
            return

        if self.layer_type == "redstone":
            if block_type == 'redstone_wire':
                for nx, nz in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    self.mark_impossible(x + nx, z + nz, x, z, tick, is_half)
                    
            elif block_type == 'repeater':
                # Le répéteur ne bloque que la direction d'en face et derrière soi
                self.mark_impossible(x + dx, z + dz, x, z, tick, is_half)
                self.mark_impossible(x - dx, z - dz, x, z, tick, is_half)
                
        elif self.layer_type == "receiver":
            # bloque les 4 directions
            for nx, nz in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                self.mark_impossible(x + nx, z + nz, x, z, tick, is_half)

    def is_occupied(self, x, z):
        """Vérifie si un bloc dur (câble, instrument, air) est déjà présent physiquement à cet endroit précis."""
        if (x, z) in self.occupied_blocks:
            return self.occupied_blocks[(x, z)]
        if self.parent:
            return self.parent.is_occupied(x, z)
        return None

    def is_blocked(self, target_x, target_z, current_tick, current_is_half):
        """Vérifie si on a le droit de poser un câble ici en s'assurant qu'il n'y a pas de conflit de tick ou de demi-tick (court-circuit)."""
        if (target_x, target_z) in self.blocked_positions:
            for conflict in self.blocked_positions[(target_x, target_z)]:
                if conflict['tick'] != current_tick or conflict['is_half'] != current_is_half:
                    return True
        if self.parent:
            return self.parent.is_blocked(target_x, target_z, current_tick, current_is_half)
        return False

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
        self.impossible_redstone.occupy(-1, -1, 'start_block',-1)
        self.impossible_notes.occupy(-1, -1, 'start_block',-1)
        
        

    def add_note_organic(self, note, target_x, target_z, target_tick, is_half):
        """
        Tente de poser une note au bon tick.
        Lance la recherche récursive (DFS). Si elle réussit, récupère la liste des commandes validées
        et les exécute "pour de vrai" dans le monde réel (les calques racines).
        """
        commands_list = []
        
        target_data = {
            'x': target_x,
            'z': target_z,
            'tick': target_tick,
            'note': note,
            'is_half': is_half
        }
        
        success = self.start_pathfinding(
            target_data,
            self.impossible_redstone, self.impossible_notes, self.anchor_manager,
            commands_list
        )

        if not success:
            print(f"Échec critique : Impossible de placer la note '{note}' au tick {target_tick}")
            return False
            
        # ==========================================
        # COMMIT DES COMMANDES DANS LE MONDE RÉEL
        # ==========================================
        for cmd in commands_list:
            action = cmd[0]
            
            if action == 'note':
                _, x, z, n, tick, source_anchor, direction = cmd
                dx, dz = direction
                target_is_half = target_data['is_half']
                
                
                self.impossible_notes.occupy(x, z, 'note_block', tick=tick, dx=dx, dz=dz, is_half=target_is_half)
               
                self.add_note(x, self.y_level - 1, z, n)
                
                # 3. Consommation de l'ancre parente
                base_source = self.anchor_manager.get_anchor(source_anchor.x, source_anchor.z)
                if base_source:
                    self.anchor_manager.consume_direction(base_source, direction)
                    
            elif action == 'redstone':
                _, x, z, tick, source_anchor, direction = cmd
                dx, dz = direction
                source_is_half = source_anchor.is_half
                
                self.impossible_redstone.occupy(x, z, 'redstone_wire', tick=tick, dx=dx, dz=dz, is_half=source_is_half)
                
                self.add_block(x, self.y_level, z, "minecraft:redstone_wire", tick=tick, needs_down=True)
                
                self.anchor_manager.add_anchor(x, z, tick, dx=dx, dz=dz, block_type="redstone", is_half=source_is_half)
                
                base_source = self.anchor_manager.get_anchor(source_anchor.x, source_anchor.z)
                if base_source:
                    self.anchor_manager.consume_direction(base_source, direction)
                    
            elif action == 'repeater':
                # On retire out_x, out_z de cette ligne :
                _, x, z, tick, new_tick, facing, delay, dx, dz, source_anchor, direction = cmd
                source_is_half = source_anchor.is_half
                
                self.impossible_redstone.occupy(x, z, 'repeater', tick=tick, dx=dx, dz=dz, is_half=source_is_half)
                
                self.add_block(x, self.y_level, z, "minecraft:repeater", properties={"facing": facing, "delay": delay}, tick=tick, needs_down=True)
                
                # L'ancre est créée en x, z
                self.anchor_manager.add_anchor(x, z, new_tick, dx=dx, dz=dz, block_type="repeater", is_half=False)
                
                base_source = self.anchor_manager.get_anchor(source_anchor.x, source_anchor.z)
                if base_source:
                    self.anchor_manager.consume_direction(base_source, direction)
                    
            elif action == 'piston':
                _, x, z, tick, dx, dz, source_anchor, direction = cmd
                
                x1, z1 = x, z                     # Piston
                x2, z2 = x + dx, z + dz           # Bloc de redstone
                x3, z3 = x + 2*dx, z + 2*dz       # Câble redstone (+ ancre)
                facing = self.get_facing(dx, dz)
                
                # +1 Piston (comportement de répéteur pour l'exclusion)
                self.impossible_redstone.occupy(x1, z1, 'repeater', tick=tick, dx=dx, dz=dz, is_half=False)
                self.impossible_notes.occupy(x1, z1, 'repeater', tick=tick, dx=dx, dz=dz, is_half=False)
                self.add_block(x1, self.y_level, z1, "minecraft:sticky_piston", properties={"facing": facing}, needs_down=True)
                
                # +2 Bloc de redstone (agît comme un émetteur à tick=0)
                self.impossible_redstone.occupy(x2, z2, 'redstone_wire', tick=0, dx=dx, dz=dz, is_half=False)
                self.impossible_notes.occupy(x2, z2, 'redstone_wire', tick=0, dx=dx, dz=dz, is_half=False)
                self.add_block(x2, self.y_level, z2, "minecraft:redstone_block")
                
                # +3 Câble de redstone sortant en demi-tick
                self.impossible_redstone.occupy(x3, z3, 'redstone_wire', tick=tick, dx=dx, dz=dz, is_half=True)
                self.impossible_notes.occupy(x3, z3, 'redstone_wire', tick=tick, dx=dx, dz=dz, is_half=True)

                
                # Ancre associée au +3
                self.anchor_manager.add_anchor(x3, z3, tick, dx=dx, dz=dz, block_type="repeater", is_half=True)
                
                base_source = self.anchor_manager.get_anchor(source_anchor.x, source_anchor.z)
                if base_source:
                    self.anchor_manager.consume_direction(base_source, direction)

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
        for a in all_anchors:#je n'aime pas cette logique, pour moi c'est superrflu, normalement, les chaors qui n'ont plus de direction de dispoiblibles devreient etre supprimé du anchor manager
            if current_anchors.get_free_directions(a):
                valid_anchors.append(a)

        if not valid_anchors:
            return False

        valid_anchors.sort(key=lambda a: a.get_score(target_x, target_z, target_tick))

        for best_anchor in valid_anchors:
            free_dirs = current_anchors.get_free_directions(best_anchor)
            # On trie les directions en utilisant la distance classique (ligne droite)
            free_dirs.sort(
                key=lambda d: math.hypot(
                    (current_anchor.x + d[0]) - target_data['x'], 
                    (current_anchor.z + d[1]) - target_data['z']
                )
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

    def try_expand_redstone_sim(self, x, z, tick, dx, dz, is_half, redstone_layer, notes_layer, anchor_layer):
        """
        Tente de poser un câble de redstone aux coordonnées (x, z).
        """
        # 1. Vérifications (Obstacles physiques et temporels)
        if redstone_layer.is_blocked(x, z, tick, is_half) or notes_layer.is_blocked(x, z, tick, is_half):
            return False
        if notes_layer.is_occupied(x, z) or redstone_layer.is_occupied(x, z):
            return False

        # 2. Pose du bloc (avec dx, dz pour ne bloquer que 3 directions autour)
        redstone_layer.occupy(x, z, 'redstone_wire', tick=tick, dx=dx, dz=dz, is_half=is_half)
        
        # 3. Création de la nouvelle ancre (avec dx, dz, et l'état is_half)
        anchor_layer.add_anchor(x, z, tick, dx=dx, dz=dz, block_type="redstone", is_half=is_half)
        
        return True

    def try_place_repeater_sim(self, x, z, current_tick, delay, dx, dz, is_half, redstone_layer, notes_layer, anchor_layer):
        """
        Tente de poser un répéteur en (x, z) orienté vers (dx, dz), # et un câble de sortie devant. on va ne pas le faire la
        """
        out_x, out_z = x + dx, z + dz
        new_tick = current_tick + delay + (1 if is_half else 0)
        

        if redstone_layer.is_occupied(x, z) or notes_layer.is_occupied(x, z):
            return False
            
        # 2. Vérifications pour la case de sortie (où sort le signal), si le signal ne peut pas être utilisé, cela ne sert a rien
        if redstone_layer.is_occupied(out_x, out_z) or notes_layer.is_occupied(out_x, out_z):
            return False

        # 3. Pose du répéteur
        # Transmet dx, dz pour ne bloquer que la case d'en face (logique du répéteur)
        redstone_layer.occupy(x, z, 'repeater', tick=new_tick, dx=dx, dz=dz)


        # 5. Création de la nouvelle ancre
        # Le type "repeater" va forcer l'ancre à n'avoir qu'une seule direction (tout droit)
        anchor_layer.add_anchor(x, z, new_tick, dx=dx, dz=dz, block_type="repeater", is_half=False)# une fois qu'on met un reptetur, on perd le half.
        
        return True

    def try_place_note_setup_sim(self, x, z, tick, note, is_half, dx, dz, redstone_layer, notes_layer):
        if redstone_layer.is_blocked(x, z, tick, is_half) or notes_layer.is_blocked(x, z, tick, is_half):
            return False
            
        if notes_layer.is_occupied(x, z) or redstone_layer.is_occupied(x, z):
            return False
            
        notes_layer.occupy(x, z, 'note_block', tick=tick, dx=dx, dz=dz, is_half=is_half)

        return True

    def try_place_piston_setup_sim(self, x, z, current_tick, dx, dz, redstone_layer, notes_layer, anchor_layer):
        """
        Setup d'un piston pour décaler le signal d'un demi-tick.
        Nécessite 4 espaces libres consécutifs dans la direction (dx, dz).
        """
        # Calcul des coordonnées des 4 blocs
        x1, z1 = x, z                 # +1 : Piston
        x2, z2 = x + dx, z + dz       # +2 : Bloc de redstone
        x3, z3 = x + 2 * dx, z + 2 * dz # +3 : Câble redstone (qui devient demi-tick)
        x4, z4 = x + 3 * dx, z + 3 * dz # +4 : Espace libre garanti pour la suite

        # 1. Vérification de l'occupation physique
        for bx, bz in [(x1, z1), (x2, z2), (x3, z3), (x4, z4)]:
            if redstone_layer.is_occupied(bx, bz) or notes_layer.is_occupied(bx, bz):
                return False

        # 2. Vérification des exclusions (court-circuits)
        # +1 (Piston) : tick actuel, is_half=False
        if redstone_layer.is_blocked(x1, z1, current_tick, False):
            return False
            
        # +2 (Redstone Block) : tick=0, is_half=False
        if redstone_layer.is_blocked(x2, z2, 0, False) or notes_layer.is_blocked(x2, z2, 0, False):
            return False
            
        # +3 et +4 : tick actuel, mais avec le nouveau statut is_half=True
        if redstone_layer.is_blocked(x3, z3, current_tick, True) or notes_layer.is_blocked(x3, z3, current_tick, True):
            return False
        if redstone_layer.is_blocked(x4, z4, current_tick, True) or notes_layer.is_blocked(x4, z4, current_tick, True):
            return False

        # 3. Exécution (Pose des blocs avec les bonnes règles d'exclusion)
        
        # +1 : Piston (On l'occupe en tant que 'repeater' pour qu'il ne bloque que devant et derrière)
        redstone_layer.occupy(x1, z1, 'repeater', tick=current_tick, dx=dx, dz=dz, is_half=False)
        notes_layer.occupy(x1, z1, 'repeater', tick=current_tick, dx=dx, dz=dz, is_half=False)

        # +2 : Bloc de redstone (On l'occupe en tant que 'redstone_wire' continu au tick 0)
        redstone_layer.occupy(x2, z2, 'redstone_wire', tick=0, dx=dx, dz=dz, is_half=False)
        notes_layer.occupy(x2, z2, 'redstone_wire', tick=0, dx=dx, dz=dz, is_half=False)

        # +3 : Câble de redstone (Passe en demi-tick !)
        redstone_layer.occupy(x3, z3, 'redstone_wire', tick=current_tick, dx=dx, dz=dz, is_half=True)
        notes_layer.occupy(x3, z3, 'redstone_wire', tick=current_tick, dx=dx, dz=dz, is_half=True)

        # 4. Création de la nouvelle ancre en +3
        # L'ancre se comporte comme la sortie d'un répéteur (1 seule direction) et propage le is_half
        anchor_layer.add_anchor(x3, z3, current_tick, dx=dx, dz=dz, block_type="repeater", is_half=True)

        return True

    def get_facing(self, dx, dz):
        if dz > 0: return 'north'
        if dz < 0: return 'south'
        if dx > 0: return 'west'
        if dx < 0: return 'east'
        return 'north'

    def start_pathfinding(self, target_data, current_redstone, current_notes, current_anchors, commands_list):
        """
        Le Lanceur : Prépare les données, trouve les meilleures ancres globales de départ, 
        et lance le parcours en profondeur.
        """

        all_anchors = current_anchors.get_all_active_anchors()
        valid_anchors = []
        
        # On filtre les ancres qui ont encore des directions libres
        for a in all_anchors:
            if current_anchors.get_free_directions(a):
                valid_anchors.append(a)

        if not valid_anchors:
            return False

        # On trie les ancres globales UNE SEULE FOIS pour commencer par la meilleure
        valid_anchors.sort(key=lambda a: a.get_score(target_data['x'], target_data['z'], target_data['tick']))

        # On lance le DFS en partant de l'ancre la plus prometteuse
        for start_anchor in valid_anchors:
            if self._dfs_step(start_anchor, target_data, current_redstone, current_notes, current_anchors, commands_list):
                return True

        return False

        def _dfs_step(self, current_anchor, target_data, current_redstone, current_notes, current_anchors, commands_list):
            """
            Le Travailleur (Cerveau) : Fonction récursive qui n'explore qu'à partir de l'ancre courante fournie.
            """
            free_dirs = current_anchors.get_free_directions(current_anchor)
            
            # On trie uniquement les directions de l'ancre courante vers la cible
            free_dirs.sort(
                key=lambda d: abs((current_anchor.x + d[0]) - target_data['x']) + abs((current_anchor.z + d[1]) - target_data['z'])
            )

            for direction in free_dirs:
                new_redstone = ExclusionMapLayer(parent=current_redstone)
                new_notes = ExclusionMapLayer(parent=current_notes)
                new_anchors = AnchorManagerLayer(parent=current_anchors)

                dx, dz = direction
                test_x = current_anchor.x + dx
                test_z = current_anchor.z + dz
                tick_diff = target_data['tick'] - current_anchor.tick

                if tick_diff < 0:
                    new_anchors.consume_direction(current_anchor, direction)
                    continue

                elif tick_diff == 0:
                    if len(free_dirs) > 1:
                        if self.try_place_note_setup_sim(test_x, test_z, current_anchor.tick, target_data['note'], target_data['is_half'], direction, new_redstone, new_notes):
                            new_anchors.consume_direction(current_anchor, direction)
                            commands_list.append(('note', test_x, test_z, target_data['note'], current_anchor.tick, current_anchor, direction))
                            return True
                    else:
                        if self.try_expand_redstone_sim(test_x, test_z, current_anchor.tick, current_anchor, new_redstone, new_notes, new_anchors):
                            new_anchors.consume_direction(current_anchor, direction)
                            commands_list.append(('redstone', test_x, test_z, current_anchor.tick, current_anchor, direction))
                            
                            new_anchor = new_anchors.get_anchor(test_x, test_z)
                            
                            if new_anchor and self._dfs_step(new_anchor, target_data, new_redstone, new_notes, new_anchors, commands_list):
                                return True
                            commands_list.pop()

                elif tick_diff > 0:
                    delay_to_burn = min(4, tick_diff)
                    if self.try_place_repeater_sim(test_x, test_z, current_anchor.tick, direction, delay_to_burn, current_anchor, new_redstone, new_notes, new_anchors):
                        new_anchors.consume_direction(current_anchor, direction)
                        out_x, out_z = test_x + dx, test_z + dz
                        new_tick = current_anchor.tick + delay_to_burn
                        facing = self.get_facing(dx, dz)
                        commands_list.append(('repeater', test_x, test_z, out_x, out_z, current_anchor.tick, new_tick, facing, delay_to_burn, dx, dz, current_anchor, direction))
                        
                        # Le répéteur sort sur out_x, out_z. C'est là que se trouve la nouvelle ancre.
                        new_anchor = new_anchors.get_anchor(out_x, out_z)
                        
                        if new_anchor and self._dfs_step(new_anchor, target_data, new_redstone, new_notes, new_anchors, commands_list):
                            return True
                        commands_list.pop()

            return False

    def _dfs_step(self, current_anchor, target_data, current_redstone, current_notes, current_anchors, commands_list):
        """
        Le Travailleur (Cerveau) : Fonction récursive propre séparant la décision de l'exécution.
        """
        # On calcule le temps restant dès le début, car cela va influencer notre stratégie de tri
        tick_diff = target_data['tick'] - current_anchor.tick

        free_dirs = current_anchors.get_free_directions(current_anchor)
        
        # L'ASTUCE MAGIQUE : 
        # Si tick_diff > 0 : On est en chemin (répéteur/redstone). On veut aller vers la cible (reverse=False).
        # Si tick_diff == 0 : On pose la note. On veut s'écarter du chemin (reverse=True -> pire direction d'abord).
        sort_reversed = (tick_diff == 0)

        # On trie les directions en utilisant la distance classique
        free_dirs.sort(
            key=lambda d: math.hypot(
                (current_anchor.x + d[0]) - target_data['x'], 
                (current_anchor.z + d[1]) - target_data['z']
            ),
            reverse=sort_reversed
        )

        for direction in free_dirs:
            dx, dz = direction
            test_x = current_anchor.x + dx
            test_z = current_anchor.z + dz
            
            # ==========================================
            # ÉTAPE 1 : DÉCISION (Quelles actions tenter ?)
            # ==========================================
            actions_to_try = []

            if random.random() < 0.2: 
                actions_to_try.append('redstone')


            if tick_diff < 0:
                # Trop tard : ce chemin a dépassé le temps imparti. 
                current_anchors.consume_direction(current_anchor, direction)
                continue
                

            elif tick_diff == 0:
                # Timing parfait sur les ticks entiers. On regarde les demi-ticks.
                target_is_half = target_data['is_half']
                anchor_is_half = current_anchor.is_half

                if len(free_dirs) > 1:
                    if target_is_half == anchor_is_half:
                        # Les deux sont normaux, ou les deux sont des demi-ticks : Parfait !
                        actions_to_try.append('note')
                    elif target_is_half and not anchor_is_half:
                        # On veut un demi-tick, mais le signal est normal : Il faut un Piston !
                        actions_to_try.append('piston')
                    elif not target_is_half and anchor_is_half:
                        # Cas inverse : on a un demi-tick mais on veut un tick normal.
                        # (Généralement impossible sans rajouter du délai, on ne fait rien ici)
                        pass

                # Même si on tente une note ou un piston, on garde l'option de juste 
                # prolonger la redstone (pour esquiver un obstacle par exemple).
                actions_to_try.append('redstone')

            elif tick_diff > 0:
                
                # random.random() renvoie un nombre entre 0.0 et 1.0
                if random.random() < 0.15: 
                    # 10% de chance : On force un "virage" en proposant la redstone en premier
                    actions_to_try.append('redstone')
                    actions_to_try.append('repeater')
                else:
                    # 90% de chance : Le comportement normal (on crame du temps)
                    actions_to_try.append('repeater')
                    actions_to_try.append('redstone')


            # ==========================================
            # ÉTAPE 2 : EXÉCUTION (Tentatives et Backtracking)
            # ==========================================
            for action in actions_to_try:
                new_redstone = ExclusionMapLayer(parent=current_redstone)
                new_notes = ExclusionMapLayer(parent=current_notes)
                new_anchors = AnchorManagerLayer(parent=current_anchors)

                if action == 'note':
                    if self.try_place_note_setup_sim(test_x, test_z, current_anchor.tick, target_data['note'], target_data['is_half'], dx, dz, new_redstone, new_notes):
                        new_anchors.consume_direction(current_anchor, direction)
                        commands_list.append(('note', test_x, test_z, target_data['note'], current_anchor.tick, current_anchor, direction))
                        return True

                elif action == 'piston':
                    if self.try_place_piston_setup_sim(test_x, test_z, current_anchor.tick, dx, dz, new_redstone, new_notes, new_anchors):
                        new_anchors.consume_direction(current_anchor, direction)
                        
                        commands_list.append(('piston', test_x, test_z, current_anchor.tick, dx, dz, current_anchor, direction))
                        
                        # On récupère l'ancre posée en +3
                        out_x, out_z = test_x + 2*dx, test_z + 2*dz
                        new_anchor = new_anchors.get_anchor(out_x, out_z)
                        
                        # On relance le DFS depuis +3 pour qu'il pose naturellement la note au coup d'après !
                        if new_anchor and self._dfs_step(new_anchor, target_data, new_redstone, new_notes, new_anchors, commands_list):
                            return True
                        commands_list.pop()

                elif action == 'redstone':
                    if self.try_expand_redstone_sim(test_x, test_z, current_anchor.tick, dx, dz, current_anchor.is_half, new_redstone, new_notes, new_anchors):
                        new_anchors.consume_direction(current_anchor, direction)
                        commands_list.append(('redstone', test_x, test_z, current_anchor.tick, current_anchor, direction))
                        
                        new_anchor = new_anchors.get_anchor(test_x, test_z)
                        
                        if new_anchor and self._dfs_step(new_anchor, target_data, new_redstone, new_notes, new_anchors, commands_list):
                            return True
                        commands_list.pop()

                elif action == 'repeater':
                    delay_to_burn = min(4, tick_diff)
                    if self.try_place_repeater_sim(test_x, test_z, current_anchor.tick, delay_to_burn, dx, dz, current_anchor.is_half, new_redstone, new_notes, new_anchors):
                        new_anchors.consume_direction(current_anchor, direction)
                        
                        new_tick = current_anchor.tick + delay_to_burn
                        facing = self.get_facing(dx, dz)
                        
                        # Plus besoin de out_x, out_z dans la commande
                        commands_list.append(('repeater', test_x, test_z, current_anchor.tick, new_tick, facing, delay_to_burn, dx, dz, current_anchor, direction))
                        
                        # L'ancre se trouve maintenant sur test_x, test_z (le répéteur)
                        new_anchor = new_anchors.get_anchor(test_x, test_z)
                        
                        if new_anchor and self._dfs_step(new_anchor, target_data, new_redstone, new_notes, new_anchors, commands_list):
                            return True
                        commands_list.pop()

        return False







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
            
            vitesse = 4 # bloc par seconde
            target_x = int(tick/10*vitesse)
            
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
