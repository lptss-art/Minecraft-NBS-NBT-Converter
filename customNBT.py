from nbt.nbt import *

class customNBT:

    minecaft_instruments = {
    "Piano":"minecraft:copper_block",
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
    "Pling": "minecraft:glowstone"}

    indexInstr = -1
    indexNotes = -1
    indexRepeters = -1
    indexPistons = -1
    
    
    custom_index = {}
    named_index = {}
    
    
    def __init__(self):
        
        self.custom_index = {}
        self.named_index = {}
        self.InitNBT()
        self.AddPaletteNote()
        self.AddPaletteInstr()
        self.AddRepeters()
        self.AddPistons()

    def InitNBT(self):
        
        self.nbtfile = NBTFile()
        #file.name = "name"

        # size

        self.nbtfile["size"] = TAG_List(TAG_Int)
        self.nbtfile["size"].append(TAG_Int(3))
        self.nbtfile["size"].append(TAG_Int(3))
        self.nbtfile["size"].append(TAG_Int(3))

        # palette
        self.nbtfile['palette'] = TAG_List(TAG_Compound)
        # blocks
        self.nbtfile['blocks'] = TAG_List(TAG_Compound)
        
        
        #self.nbtfile = file
        
        
    def write_file(self, filename):
        self.nbtfile.write_file(filename)
        
    def AddPalette(self, name, prop = None):
        pal = TAG_Compound()
        pal['Name'] = TAG_String(name)

        if(prop != None):
            pal['Properties'] = TAG_Compound()

            for key in prop.keys():
                pal['Properties'][key] = TAG_String(str(prop[key]))

        self.nbtfile['palette'].append(pal)
        
    def Index(self, bloc_name = "air", prop = None, name = None):
        if(False):#name):
            if(name in self.named_index.keys()):
                return self.named_index[name]
            else:
                self.named_index[name] = self.GetIndex("minecraft:"+bloc_name, prop)
                return self.named_index[name]
        else:
            if(prop != None):
                return self.GetIndex("minecraft:"+bloc_name, prop)
            else:
                if(bloc_name in self.custom_index.keys()):
                    return self.custom_index[bloc_name]
                else:
                    self.custom_index[bloc_name] = self.GetIndex("minecraft:"+bloc_name, prop)
                    return self.custom_index[bloc_name]
                
        
    
    def GetIndex(self, name, prop = None):
        for i in range(len(self.nbtfile['palette'])):
            pal = self.nbtfile['palette'][i]
            if(pal["Name"].value == name):
                if(prop == None):
                    return i
                correctProp = True
                for key in prop:
                    if(pal['Properties'][key].value != prop[key]):
                        correctProp = False
                if(correctProp):
                    return i
        self.AddPalette(name, prop)
        return self.GetIndex(name, prop)
    
    def GetRotationIndex(self,i, sym=False):
        correspondance = {}
        
        directions = {'north':0, 'east':1, 'south':2, 'west':3}
        directions_i = {0:'north', 1:'east', 2:'south', 3:'west'}
        
        oldIndex=-1
        for pal in self.nbtfile['palette']:
            oldIndex += 1
            if('Properties'  in pal):
                if 'facing' in pal['Properties']:
                    props = {}
                    for key in pal['Properties'].keys():
                        props[key] = pal['Properties'][key].value
                        
                        
                    #oldIndex = self.GetIndex(pal["Name"].value, props)
                    
                    direction = props['facing']
                    if(sym and (direction =='east' or direction == 'west')):
                        pass
                    else:
                        props['facing'] = directions_i[(directions[direction]+i)%4]
                    

                        newIndex = self.GetIndex(pal["Name"].value, props)

                        correspondance[oldIndex] = newIndex
                    
        return correspondance
    
    
    def AddBloc(self, pos, typ):

        block = TAG_Compound()
        block['pos'] = TAG_List(TAG_Int)
        #print(pos[0])
        block['pos'].append(TAG_Int(value = int(pos[0])))
        block['pos'].append(TAG_Int(value = int(pos[1])))
        block['pos'].append(TAG_Int(value = int(pos[2])))

        block['state'] = TAG_Int(int(typ))

        self.nbtfile['blocks'].append(block)
        
        
        
    def AddStructureBloc(self, pos, name, deltaX=0,deltaY=0,deltaZ=0):

        typ = self.Index('structure_block', {'mode':'load'})
        
        block = TAG_Compound()
        block['pos'] = TAG_List(TAG_Int)
        #print(pos[0])
        block['pos'].append(TAG_Int(value = int(pos[0])))
        block['pos'].append(TAG_Int(value = int(pos[1])))
        block['pos'].append(TAG_Int(value = int(pos[2])))

        block['state'] = TAG_Int(int(typ))

        nbt = TAG_Compound()
        nbt['name'] = TAG_String(name)
        nbt['mode'] = TAG_String('LOAD')
        nbt['posX'] = TAG_Int(value = deltaX)
        nbt['posZ'] = TAG_Int(value = deltaY)
        nbt['posZ'] = TAG_Int(value = deltaZ)
        block['nbt'] = nbt
                         
        self.nbtfile['blocks'].append(block)
        
    def AddArray(self,array, offset):
        for i in range(array.shape[0]):
            for j in range(array.shape[1]):
                for k in range(array.shape[2]):
                    if(array[i,j,k] != -1):
                        self.AddBloc([i+offset[0],j+offset[1],k+offset[2]],array[i,j,k])
        
        
    def AddPaletteNote(self):
        self.indexNotes = len(self.nbtfile['palette'])
        for i in range(25):
            self.AddPalette("minecraft:note_block", {'note':i})

    def AddPaletteInstr(self):
        self.indexInstr = len(self.nbtfile['palette'])
        for key in self.minecaft_instruments.keys():
            self.AddPalette(self.minecaft_instruments[key])
                
    def AddRepeters(self):
        directions = ['east','west',"north","south"]
        self.indexRepeters = {}
        for direction in directions:
            self.indexRepeters[direction] = len(self.nbtfile['palette'])
            for i in range(4):
                self.AddPalette("minecraft:repeater", {"facing":direction,"delay":i+1})

    def AddPistons(self):
        directions = ['east','west',"north","south"]
        self.indexPistons = {}
        for direction in directions:
            self.indexPistons[direction] = len(self.nbtfile['palette'])
            self.AddPalette("minecraft:sticky_piston", {"facing":direction})   