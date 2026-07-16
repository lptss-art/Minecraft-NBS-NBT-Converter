import numpy as np
import math
from core.layout_base import LayoutBase
from core.brick import Brick

class Anchor:
    def __init__(self, x, z, tick):
        self.x = x
        self.z = z
        self.tick = tick
        # Les 4 directions cardinales (Nord, Sud, Est, Ouest)
        self.free_directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def get_score(self, target_x, target_z, target_tick, alpha=0.2):
        """Calcule le coût de cette ancre (Distance + Pénalité de temps)."""
        dist = abs(self.x - target_x) + abs(self.z - target_z)
        time_penalty = alpha * abs(target_tick - self.tick)
        return dist + time_penalty


class AnchorManager:
    def __init__(self):
        self.active_anchors = []

    def add_anchor(self, x, z, tick):
        """Crée une nouvelle ancre à chaque fois qu'on pose de la redstone."""
        new_anchor = Anchor(x, z, tick)
        self.active_anchors.append(new_anchor)
        return new_anchor

    def get_best_anchor(self, target_x, target_z, target_tick):
        """Trie les ancres et renvoie la plus pertinente."""
        if not self.active_anchors:
            return None
            
        # On trie la liste en direct selon le score
        self.active_anchors.sort(key=lambda a: a.get_score(target_x, target_z, target_tick))
        
        # On renvoie la meilleure (la première de la liste)
        return self.active_anchors[0]

    def consume_direction(self, anchor, direction):
        """
        Retire une direction d'une ancre (car on l'a utilisée ou elle a échoué).
        Si l'ancre n'a plus de directions, on la supprime de la liste active.
        """
        if direction in anchor.free_directions:
            anchor.free_directions.remove(direction)
            
        # L'ancre est "morte" (encerclée ou totalement exploitée)
        if len(anchor.free_directions) == 0:
            self.remove_anchor(anchor)

    def remove_anchor(self, anchor):
        """Supprime complètement une ancre de la liste."""
        if anchor in self.active_anchors:
            self.active_anchors.remove(anchor)


class ExclusionMap:
    def __init__(self):
        # Dictionnaire : (x, z) -> { 'source_coord': (sx, sz), 'tick': tick }
        # On pourrait aussi stocker une liste de conflits si plusieurs sources bloquent la même case.
        self.blocked_positions = {}

    def mark_impossible(self, target_x, target_z, source_x, source_z, source_tick):
        """Mémorise qu'une case est bloquée, et par qui."""
        self.blocked_positions[(target_x, target_z)] = {
            'source_coord': (source_x, source_z),
            'tick': source_tick
        }

    def is_blocked(self, target_x, target_z, current_tick):
        """
        Vérifie si on a le droit de poser un bloc ici.
        Retourne True si c'est interdit, False si c'est autorisé.
        """
        if (target_x, target_z) not in self.blocked_positions:
            return False # La case est vierge d'interdiction
        
        # On récupère le responsable du blocage
        conflict = self.blocked_positions[(target_x, target_z)]
        
        # Ton exception intelligente : si le conflit a lieu exactement au même tick, on tolère !
        if conflict['tick'] == current_tick:
            return False 
            
        return True # Vraiment impossible (ticks différents = court-circuit temporel)



class Layout3Brick(LayoutBase):
    """
    Manages the organic layout (Layout 3).
    Dynamic opportunistic generator using a score system and 2D backtracking.
    """
    def __init__(self):
        super().__init__()
        # On définit une hauteur de base pour tout le circuit
        self.y_level = 0 
        
        # On instancie tes nouveaux gestionnaires
        self.anchor_manager = AnchorManager()
        self.impossible_redstone = ExclusionMap()
        self.impossible_notes = ExclusionMap()
        
        # Grid pour les collisions pures (ce qui est physiquement posé)
        self.occupied_space = {}
        
        # On place le point de départ : (x, z, tick)
        self.anchor_manager.add_anchor(-1, -1, 0) 
        self.occupy(-1, self.y_level, -1, 'start_block')


    def add_note_organic(self, note, target_x, target_z, target_tick, is_half):
        """
        Cherche le meilleur chemin pour poser une note au bon tick.
        """
        # Tant qu'on a des ancres actives, on cherche
        while True:
            best_anchor = self.anchor_manager.get_best_anchor(target_x, target_z, target_tick)
            
            if not best_anchor:
                print(f"Échec critique : Impossible de placer la note au tick {target_tick}")
                return False
                
            # --- LA MODIFICATION MAGIQUE ---
            # On trie les directions restantes selon la distance de Manhattan jusqu'à la cible
            best_anchor.free_directions.sort(
                key=lambda d: abs((best_anchor.x + d[0]) - target_x) + abs((best_anchor.z + d[1]) - target_z)
            )
            
            # On prend la direction qui nous rapproche le plus
            direction = best_anchor.free_directions[0]
            dx, dz = direction
            
            test_x = best_anchor.x + dx
            test_z = best_anchor.z + dz
            
            tick_diff = target_tick - best_anchor.tick
            
            # CAS 1 : L'ancre est trop "récente" (le tick cible est déjà passé pour elle)
            if tick_diff < 0:
                self.anchor_manager.consume_direction(best_anchor, direction)
                continue
                
            # CAS 2 : Le timing est parfait, on est au bon tick !
            if tick_diff == 0:
                
                # NOUVELLE RÈGLE : On vérifie s'il nous reste plus d'une direction
                if len(best_anchor.free_directions) > 1:
                    
                    # On a de la marge, on peut tenter de sacrifier cette direction pour une note
                    if self.try_place_note_setup(test_x, test_z, best_anchor.tick, note, is_half, direction):
                        # Succès ! La note est posée.
                        self.anchor_manager.consume_direction(best_anchor, direction)
                        return True 
                    else:
                        # Échec : pas de place pour la note. 
                        # On se rabat sur l'extension du circuit pour esquiver l'obstacle.
                        self.try_expand_redstone(test_x, test_z, best_anchor.tick, best_anchor)
                        self.anchor_manager.consume_direction(best_anchor, direction)
                        
                else:
                    # DANGER : Il ne reste qu'une seule direction !
                    # C'est notre bouée de sauvetage pour continuer le circuit. Interdit de poser une note.
                    # On force l'extension avec de la redstone.
                    self.try_expand_redstone(test_x, test_z, best_anchor.tick, best_anchor)
                    self.anchor_manager.consume_direction(best_anchor, direction)
                    
            # CAS 3 : Il faut brûler du délai, on pose un répéteur
            elif tick_diff > 0:
                delay_to_burn = min(4, tick_diff)
                self.try_place_repeater(test_x, test_z, best_anchor.tick, direction, delay_to_burn, best_anchor)
                self.anchor_manager.consume_direction(best_anchor, direction)

    def occupy(self, x, y, z, block_type):
        """Marque une coordonnée 3D comme étant occupée."""
        self.occupied_space[(x, y, z)] = block_type
    
    def try_expand_redstone(self, x, z, tick, source_anchor):
        """Tente de poser de la poudre et crée une nouvelle ancre si succès."""
        # 1. Est-ce blacklisté par l'historique ?
        if self.impossible_redstone.is_blocked(x, z, tick):
            return False
            
        # 2. Est-ce physiquement occupé ?
        if (x, self.y_level, z) in self.occupied_space:
            self.impossible_redstone.mark_impossible(x, z, source_anchor.x, source_anchor.z, tick)
            return False
            
        # 3. Règle Minecraft : Vérifier le "crosstalk" (fusion de câbles)
        # On regarde les 4 cases adjacentes. Si on trouve de la redstone avec un tick différent, on annule.
        for dx, dz in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            neighbor_pos = (x + dx, self.y_level, z + dz)
            if neighbor_pos in self.occupied_space and self.occupied_space[neighbor_pos] == 'redstone_wire':
                # Il faudrait idéalement stocker le tick de chaque bloc posé pour vérifier s'il est différent.
                # Simplification : si on frôle un autre câble, c'est dangereux.
                self.impossible_redstone.mark_impossible(x, z, source_anchor.x, source_anchor.z, tick)
                return False

        # SUCCÈS : On pose la redstone et on crée l'ancre
        self.occupy(x, self.y_level, z, 'redstone_wire')
        self.add_block(x, self.y_level, z, "minecraft:redstone_wire", tick=tick, needs_down=True)
        
        self.anchor_manager.add_anchor(x, z, tick)
        return True

        
    def try_place_repeater(self, x, z, current_tick, direction, delay, source_anchor):
        """Place un répéteur, puis une poudre de redstone juste devant, qui deviendra la nouvelle ancre."""
        dx, dz = direction
        out_x, out_z = x + dx, z + dz
        new_tick = current_tick + delay
        
        # 1. Vérifier si la place du répéteur est libre
        if self.impossible_redstone.is_blocked(x, z, current_tick):
            return False
        if (x, self.y_level, z) in self.occupied_space:
            return False
            
        # 2. Vérifier si la place pour la poudre (l'ancre de sortie) est libre
        if self.impossible_redstone.is_blocked(out_x, out_z, new_tick):
            return False
        if (out_x, self.y_level, out_z) in self.occupied_space:
            return False

        # 3. Règle Minecraft : Vérifier le "crosstalk" pour la NOUVELLE poudre de redstone
        for ndx, ndz in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            neighbor_pos = (out_x + ndx, self.y_level, out_z + ndz)
            # On ignore le répéteur qu'on est en train de poser juste derrière
            if neighbor_pos == (x, self.y_level, z):
                continue
                
            if neighbor_pos in self.occupied_space and self.occupied_space[neighbor_pos] == 'redstone_wire':
                self.impossible_redstone.mark_impossible(out_x, out_z, source_anchor.x, source_anchor.z, new_tick)
                return False
        
        facing = self.get_facing(dx, dz)
        
        # SUCCÈS - ÉTAPE A : On pose le répéteur
        self.occupy(x, self.y_level, z, 'repeater')
        self.add_block(x, self.y_level, z, "minecraft:repeater", properties={"facing": facing, "delay": delay}, tick=current_tick, needs_down=True)
        
        # SUCCÈS - ÉTAPE B : On pose la redstone dust juste devant
        self.occupy(out_x, self.y_level, out_z, 'redstone_wire')
        # needs_down=True car la poudre a aussi besoin d'un bloc en dessous
        self.add_block(out_x, self.y_level, out_z, "minecraft:redstone_wire", tick=new_tick, needs_down=True) 
        
        # On crée la nouvelle ancre physiquement sur cette poudre
        self.anchor_manager.add_anchor(out_x, out_z, new_tick)
        return True
        
    def try_place_note_setup(self, x, z, tick, note, is_half, direction):
        """Vérifie la place 3D pour la note (et le piston si demi-temps)."""
        if self.impossible_notes.is_blocked(x, z, tick):
            return False
            
        # Un noteblock a besoin de 3 blocs de haut libres (Instrument, Note, Air)
        y = self.y_level
        if (x, y-1, z) in self.occupied_space or (x, y, z) in self.occupied_space or (x, y+1, z) in self.occupied_space:
            # On note que cet endroit est pourri (on met 0,0 en source arbitraire pour la note)
            self.impossible_notes.mark_impossible(x, z, 0, 0, tick) 
            return False

        # TODO : Rajouter la vérification d'espace supplémentaire si is_half == True (pour le piston)

        # SUCCÈS : On pose l'infrastructure
        self.occupy(x, y-1, z, 'instrument')
        self.occupy(x, y, z, 'note_block')
        self.occupy(x, y+1, z, 'air') # L'air au dessus pour que ça sonne
        
        # On ajoute la note dans ton système NBT
        self.add_note(x, y-1, z, note)
        
        # Remarque : on ne crée PAS d'ancre ici, car c'est une impasse (fin de ligne pour cette note)
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
