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
        
    def add_palette(self, name, properties=None):
        """Adds a block to the palette."""
        palette_entry = TAG_Compound()
        palette_entry['Name'] = TAG_String(name)

        if properties is not None:
            palette_entry['Properties'] = TAG_Compound()
            for key in properties.keys():
                palette_entry['Properties'][key] = TAG_String(str(properties[key]))

        self.nbtfile['palette'].append(palette_entry)
        
    def get_index_safe(self, block_name="air", properties=None):
        """
        Gets the index of a block in the palette, adding it if necessary.
        """
        if properties is not None:
            return self.get_index("minecraft:" + block_name, properties)
        else:
            if block_name in self.custom_index.keys():
                return self.custom_index[block_name]
            else:
                self.custom_index[block_name] = self.get_index("minecraft:" + block_name, properties)
                return self.custom_index[block_name]
                
    def get_index(self, name, properties=None):
        """Gets the index of a block state in the palette."""
        for i in range(len(self.nbtfile['palette'])):
            palette_entry = self.nbtfile['palette'][i]
            if palette_entry["Name"].value == name:
                if properties is None:
                    return i
                correct_properties = True
                if 'Properties' in palette_entry:
                    for key in properties:
                        if key not in palette_entry['Properties'] or palette_entry['Properties'][key].value != properties[key]:
                            correct_properties = False
                            break
                else:
                    correct_properties = False # Properties provided but palette has none

                if correct_properties:
                    return i

        self.add_palette(name, properties)
        return self.get_index(name, properties)
    
    def get_rotation_index(self, rotations, is_symmetric=False):
        """Calculates rotation mapping for block states."""
        correspondence = {}
        
        directions = {'north': 0, 'east': 1, 'south': 2, 'west': 3}
        directions_i = {0: 'north', 1: 'east', 2: 'south', 3: 'west'}
        
        old_index = -1
        for palette_entry in self.nbtfile['palette']:
            old_index += 1
            if 'Properties' in palette_entry:
                if 'facing' in palette_entry['Properties']:
                    props = {}
                    for key in palette_entry['Properties'].keys():
                        props[key] = palette_entry['Properties'][key].value
                        
                    direction = props['facing']
                    if is_symmetric and (direction == 'east' or direction == 'west'):
                        pass
                    else:
                        if direction in directions:
                            props['facing'] = directions_i[(directions[direction] + rotations) % 4]
                            new_index = self.get_index(palette_entry["Name"].value, props)
                            correspondence[old_index] = new_index
                    
        return correspondence
    
    def add_block(self, position, block_state_id):
        """Adds a block to the structure."""
        block = TAG_Compound()
        block['pos'] = TAG_List(TAG_Int)
        block['pos'].append(TAG_Int(value=int(position[0])))
        block['pos'].append(TAG_Int(value=int(position[1])))
        block['pos'].append(TAG_Int(value=int(position[2])))

        block['state'] = TAG_Int(int(block_state_id))

        self.nbtfile['blocks'].append(block)
        
    def add_structure_block(self, position, name, delta_x=0, delta_y=0, delta_z=0):
        """Adds a structure block (Load mode)."""
        block_state_id = self.get_index_safe('structure_block', {'mode': 'load'})
        
        block = TAG_Compound()
        block['pos'] = TAG_List(TAG_Int)
        block['pos'].append(TAG_Int(value=int(position[0])))
        block['pos'].append(TAG_Int(value=int(position[1])))
        block['pos'].append(TAG_Int(value=int(position[2])))

        block['state'] = TAG_Int(int(block_state_id))

        nbt_data = TAG_Compound()
        nbt_data['name'] = TAG_String(name)
        nbt_data['mode'] = TAG_String('LOAD')
        nbt_data['posX'] = TAG_Int(value=delta_x)
        nbt_data['posY'] = TAG_Int(value=delta_y)
        nbt_data['posZ'] = TAG_Int(value=delta_z)
        block['nbt'] = nbt_data
                         
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
