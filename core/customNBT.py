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

    def __init__(self):
        self.custom_index = {}
        self.named_index = {}
        self.init_nbt()

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

        if properties:
            palette_entry['Properties'] = TAG_Compound()
            for key in properties.keys():
                palette_entry['Properties'][key] = TAG_String(str(properties[key]))

        self.nbtfile['palette'].append(palette_entry)
        
    def get_index_safe(self, block_name="air", properties=None):
        """
        Gets the index of a block in the palette, adding it if necessary.
        """
        if not block_name.startswith("minecraft:"):
            block_name = "minecraft:" + block_name

        if properties is None:
            properties = {}

        # Serialize properties into a string key for caching
        prop_str = str(sorted(properties.items()))
        cache_key = f"{block_name}|{prop_str}"

        if cache_key in self.custom_index:
            return self.custom_index[cache_key]
        else:
            idx = self.get_index(block_name, properties)
            self.custom_index[cache_key] = idx
            return idx
                
    def get_index(self, name, properties=None):
        """Gets the index of a block state in the palette."""
        if properties is None:
            properties = {}

        for i in range(len(self.nbtfile['palette'])):
            palette_entry = self.nbtfile['palette'][i]
            if palette_entry["Name"].value == name:
                correct_properties = True

                palette_props = {}
                if 'Properties' in palette_entry:
                    for k, v in palette_entry['Properties'].items():
                        palette_props[k] = v.value

                if len(properties) != len(palette_props):
                    correct_properties = False
                else:
                    for k, v in properties.items():
                        if k not in palette_props or palette_props[k] != str(v):
                            correct_properties = False
                            break

                if correct_properties:
                    return i

        self.add_palette(name, properties)
        return self.get_index(name, properties)
    
    def add_block(self, position, block_state_id, metadata=None):
        """Adds a block to the structure."""
        block = TAG_Compound()
        block['pos'] = TAG_List(TAG_Int)
        block['pos'].append(TAG_Int(value=int(position[0])))
        block['pos'].append(TAG_Int(value=int(position[1])))
        block['pos'].append(TAG_Int(value=int(position[2])))

        block['state'] = TAG_Int(int(block_state_id))

        if metadata:
            block['nbt'] = TAG_Compound()
            for key, value in metadata.items():
                if isinstance(value, bool):
                    block['nbt'][key] = TAG_Byte(int(value))
                elif isinstance(value, int):
                    block['nbt'][key] = TAG_Int(value)
                elif isinstance(value, str):
                    block['nbt'][key] = TAG_String(value)

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
