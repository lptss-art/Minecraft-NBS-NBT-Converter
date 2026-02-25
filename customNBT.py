from nbt.nbt import *

class CustomNBT:
    """
    A wrapper class to manage Minecraft NBT data for structures.
    """

    minecraft_instruments = {
        "Piano": "minecraft:copper_block",
        "Double Bass": "minecraft:oak_planks",
        "Bass Drum": "minecraft:stone",
        "Snare Drum": "minecraft:sand",
        "Click": "minecraft:glass",
        "Guitar": "minecraft:white_wool",
        "BFlute": "minecraft:clay",
        "Bell": "minecraft:gold_block",
        "Chime": "minecraft:packed_ice",
        "Xylophone": "minecraft:bone_block",
        "Iron Xylophone": "minecraft:iron_block",
        "Cow Bel": "minecraft:soul_sand",
        "Didgeridoo": "minecraft:pumpkin",
        "Bit": "minecraft:emerald_block",
        "Banjo": "minecraft:hay_block",
        "Pling": "minecraft:glowstone"
    }

    index_instr = -1
    index_notes = -1
    index_repeaters = -1
    index_pistons = -1
    
    custom_index = {}
    named_index = {}
    
    def __init__(self):
        self.custom_index = {}
        self.named_index = {}
        self.init_nbt()
        self.add_palette_note()
        self.add_palette_instr()
        self.add_repeaters()
        self.add_pistons()

    def init_nbt(self):
        """Initializes the NBT file structure."""
        self.nbtfile = NBTFile()

        # size (dummy values initially)
        self.nbtfile["size"] = TAG_List(TAG_Int)
        self.nbtfile["size"].append(TAG_Int(3))
        self.nbtfile["size"].append(TAG_Int(3))
        self.nbtfile["size"].append(TAG_Int(3))

        # palette
        self.nbtfile['palette'] = TAG_List(TAG_Compound)
        # blocks
        self.nbtfile['blocks'] = TAG_List(TAG_Compound)
        
    def write_file(self, filename):
        """Writes the NBT file to disk."""
        self.nbtfile.write_file(filename)
        
    def add_palette(self, name, prop=None):
        """Adds a block to the palette."""
        pal = TAG_Compound()
        pal['Name'] = TAG_String(name)

        if prop is not None:
            pal['Properties'] = TAG_Compound()
            for key in prop.keys():
                pal['Properties'][key] = TAG_String(str(prop[key]))

        self.nbtfile['palette'].append(pal)
        
    def get_index_safe(self, bloc_name="air", prop=None):
        """
        Gets the index of a block in the palette, adding it if necessary.
        Renamed from Index to get_index_safe to avoid confusion with GetIndex.
        """
        if prop is not None:
            return self.get_index("minecraft:" + bloc_name, prop)
        else:
            if bloc_name in self.custom_index.keys():
                return self.custom_index[bloc_name]
            else:
                self.custom_index[bloc_name] = self.get_index("minecraft:" + bloc_name, prop)
                return self.custom_index[bloc_name]
                
    def get_index(self, name, prop=None):
        """Gets the index of a block state in the palette."""
        for i in range(len(self.nbtfile['palette'])):
            pal = self.nbtfile['palette'][i]
            if pal["Name"].value == name:
                if prop is None:
                    return i
                correct_prop = True
                if 'Properties' in pal:
                    for key in prop:
                        if key not in pal['Properties'] or pal['Properties'][key].value != prop[key]:
                            correct_prop = False
                            break
                else:
                    correct_prop = False # Prop provided but palette has none

                if correct_prop:
                    return i

        self.add_palette(name, prop)
        return self.get_index(name, prop)
    
    def get_rotation_index(self, i, sym=False):
        """Calculates rotation mapping for block states."""
        correspondance = {}
        
        directions = {'north': 0, 'east': 1, 'south': 2, 'west': 3}
        directions_i = {0: 'north', 1: 'east', 2: 'south', 3: 'west'}
        
        old_index = -1
        for pal in self.nbtfile['palette']:
            old_index += 1
            if 'Properties' in pal:
                if 'facing' in pal['Properties']:
                    props = {}
                    for key in pal['Properties'].keys():
                        props[key] = pal['Properties'][key].value
                        
                    direction = props['facing']
                    if sym and (direction == 'east' or direction == 'west'):
                        pass
                    else:
                        if direction in directions:
                            props['facing'] = directions_i[(directions[direction] + i) % 4]
                            new_index = self.get_index(pal["Name"].value, props)
                            correspondance[old_index] = new_index
                    
        return correspondance
    
    def add_block(self, pos, typ):
        """Adds a block to the structure."""
        block = TAG_Compound()
        block['pos'] = TAG_List(TAG_Int)
        block['pos'].append(TAG_Int(value=int(pos[0])))
        block['pos'].append(TAG_Int(value=int(pos[1])))
        block['pos'].append(TAG_Int(value=int(pos[2])))

        block['state'] = TAG_Int(int(typ))

        self.nbtfile['blocks'].append(block)
        
    def add_structure_block(self, pos, name, deltaX=0, deltaY=0, deltaZ=0):
        """Adds a structure block (Load mode)."""
        typ = self.get_index_safe('structure_block', {'mode': 'load'})
        
        block = TAG_Compound()
        block['pos'] = TAG_List(TAG_Int)
        block['pos'].append(TAG_Int(value=int(pos[0])))
        block['pos'].append(TAG_Int(value=int(pos[1])))
        block['pos'].append(TAG_Int(value=int(pos[2])))

        block['state'] = TAG_Int(int(typ))

        nbt = TAG_Compound()
        nbt['name'] = TAG_String(name)
        nbt['mode'] = TAG_String('LOAD')
        nbt['posX'] = TAG_Int(value=deltaX)
        nbt['posY'] = TAG_Int(value=deltaY) # Fixed typo posZ -> posY
        nbt['posZ'] = TAG_Int(value=deltaZ)
        block['nbt'] = nbt
                         
        self.nbtfile['blocks'].append(block)
        
    def add_array(self, array, offset):
        """Adds blocks from a 3D array."""
        for i in range(array.shape[0]):
            for j in range(array.shape[1]):
                for k in range(array.shape[2]):
                    if array[i, j, k] != -1:
                        self.add_block([i + offset[0], j + offset[1], k + offset[2]], array[i, j, k])
        
    def add_palette_note(self):
        """Adds note blocks to the palette."""
        self.index_notes = len(self.nbtfile['palette'])
        for i in range(25):
            self.add_palette("minecraft:note_block", {'note': i})

    def add_palette_instr(self):
        """Adds instrument blocks to the palette."""
        self.index_instr = len(self.nbtfile['palette'])
        for key in self.minecraft_instruments.keys():
            self.add_palette(self.minecraft_instruments[key])
                
    def add_repeaters(self):
        """Adds repeaters to the palette."""
        directions = ['east', 'west', "north", "south"]
        self.index_repeaters = {}
        for direction in directions:
            self.index_repeaters[direction] = len(self.nbtfile['palette'])
            for i in range(4):
                self.add_palette("minecraft:repeater", {"facing": direction, "delay": i + 1})

    def add_pistons(self):
        """Adds pistons to the palette."""
        directions = ['east', 'west', "north", "south"]
        self.index_pistons = {}
        for direction in directions:
            self.index_pistons[direction] = len(self.nbtfile['palette'])
            self.add_palette("minecraft:sticky_piston", {"facing": direction})
