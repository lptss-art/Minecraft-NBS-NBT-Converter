import pandas as pd
from struct import unpack,pack
import numpy as np



def read_int(fi):
    the_int, = unpack('i', fi.read(4))
    return the_int

def read_short(fi):
    sh, = unpack('h', fi.read(2))
    return sh
def read_byte(fi):
    return int.from_bytes(fi.read(1), "big")    

def readString(fi):
    lengh = read_int(fi)
    #print(lengh)
    s = ""
    for i in range(lengh):
        s += fi.read(1).decode('ascii')
    return s


def readString2(fi):
    lengh = read_int(fi)
    a = pack('i',lengh)
    for i in range(lengh):
        a += fi.read(1)
    return a


def write_int(f,a):
    f.write(pack('i',a))
    #print('write int', a)
def write_short(f,a):
    f.write(pack('h',a))
    #print('write short', a)
def write_byte(f,a):
    f.write(pack('b',a))
    #print('write byte', a)
def writeString0(f):
    lengh = write_int(f,0)

def read_file(file_name):
    
    print("Loading file: ", file_name)
    f = open(file_name, "rb")
    
    byte1 = read_byte(f)
    byte2 = read_byte(f)
    nbs_version = read_byte(f)
    #print('version', nbs_version)
    song_first_custom_index = read_byte(f)
    #print('custom index', song_first_custom_index )
    
    #Short: Song length
    #The length of the song, measured in ticks. Divide this by the tempo to get the length of the song in seconds. The Note Block Studio doesn't really care about this value, the song size is calculated in the second part.


    s_len = read_short(f)
    #print(s_len)

    #Short: Song height
    #The last layer with at least one note block in it, or the last layer that have had its name or volume changed.
    s_h = read_short(f)
    #print(s_h)


    #String: Song name
    #The name of the song.
    s_name = readString(f)
    #print(s_name)


    #String: Song author
    #The author of the song.
    author = readString(f)
    #print(author)

    #String: Original song author
    #The original song author of the song.
    author_o = readString(f)
    #print(author_o)

    #String: Song description
    #The description of the song.
    description = readString(f)
    #print(description)

    #Short: Tempo
    #The tempo of the song multiplied by 100 (1225 instead of 12.25 for example). This is measured in ticks per second.
    tempo = f.read(2)


    #Byte: Auto-saving
    #Whether auto-saving has been enabled (0 or 1).
    auto_save = f.read(1)

    #Byte: Auto-saving duration
    #The amount of minutes between each auto-save (if it has been enabled) (1-60).
    auto_save_dur = f.read(1)

    #Byte: Time signature
    #The time signature of the song. If this is 3, then the signature is 3/4. Default is 4. This value ranges from 2-8.

    time_signature = f.read(1)

    #Integer: Minutes spent
    #The amount of minutes spent on the project.
    time_spent = f.read(4)

    #Integer: Left clicks
    #The amount of times the user have left clicked.
    left_clicks = f.read(4)


    #Integer: Right clicks
    #The amount of times the user have right clicked.

    right_c = f.read(4)


    #Integer: Blocks added
    #The amount of times the user have added a block.

    block_added = f.read(4)

    #Integer: Blocks removed
    #The amount of times the user have removed a block.

    block_removed = f.read(4)

    #String: MIDI/Schematic file name
    #If the song has been imported from a .mid or .schematic file, that file name is stored here (Only the name of the file, not the path).

    mid_file = readString(f)
    #print(mid_file)

    
    # Fin lecture header
    
    # lecrure de qq bytes pour corriger
    read_byte(f)
    read_byte(f)
    read_short(f)
    

    
    #lecture du morceau
    
    # https://github.com/OpenNBS/OpenNoteBlockStudio/blob/master/scripts/load_song/load_song.gml

    layers = []
    ticks = []
    keys = []
    insts = []

    tick = -1;
    jumps = -1;
    while (True):
        jumps = read_short(f)
        #print("tick jumps: ", jumps)

        if(jumps == 0):
            break

        tick += jumps
        layer = -1

        while (True):

            jumps = read_short(f)
            #print("layer jumps: ", jumps)

            if(jumps == 0):
                break

            layer += jumps;

            inst = read_byte(f)
            key = read_byte(f)-33

            read_byte(f) # vel
            read_byte(f) # pan
            read_short(f) #pit


            layers.append(layer)
            ticks.append(tick)
            keys.append(key)
            insts.append(inst)


            # noteblocks.Add(new NoteBlock(tick, layer, inst, key)) #Found note block, add to the list

            #instrumentcount[inst]++
            #if (layer < layers):
            #    layercount[layer]++



    
    return pd.DataFrame(data = {"tick":ticks, "layer": layers, "key": keys, "insts": insts})
    

def read_file_complet(file_name):
    
    print("Loading file: ", file_name)
    f = open(file_name, "rb")
    
    a = f.read(8)
    
    #String: Song name
    a+=readString2(f)



    #String: Song author
    a+=readString2(f)


    #String: Original song author
    a+=readString2(f)


    #String: Song description
    a+=readString2(f)


    a+= f.read(25)

    #String: MIDI/Schematic file name
    #If the song has been imported from a .mid or .schematic file, that file name is stored here (Only the name of the file, not the path).

    a += readString2(f)
    #print(mid_file)

    
    # Fin lecture header
    
    a+= f.read(4) 
    
    
    header = a 
    
    
    #lecture du morceau
    
    # https://github.com/OpenNBS/OpenNoteBlockStudio/blob/master/scripts/load_song/load_song.gml

    layers = []
    ticks = []
    keys = []
    insts = []
    vels = []
    pans = []
    pits = []

    tick = -1;
    jumps = -1;
    while (True):
        jumps = read_short(f)
        #print("tick jumps: ", jumps)

        if(jumps == 0):
            break

        tick += jumps
        layer = -1

        while (True):

            jumps = read_short(f)
            #print("layer jumps: ", jumps)

            if(jumps == 0):
                break

            layer += jumps;
            
            #print("read values")
            
            inst = read_byte(f)
            key = read_byte(f)-33

            vel = read_byte(f) # vel
            pan = read_byte(f) # pan
            pit = read_short(f) #pit


            layers.append(layer)
            ticks.append(tick)
            keys.append(key)
            insts.append(inst)
            
            vels.append(vel)
            pans.append(pan)
            pits.append(pit)


            # noteblocks.Add(new NoteBlock(tick, layer, inst, key)) #Found note block, add to the list

            #instrumentcount[inst]++
            #if (layer < layers):
            #    layercount[layer]++



    fin = f.read()
    f.close()
    return header, pd.DataFrame(data = {"tick":ticks, "layer": layers, "key": keys, "insts": insts, "vels": vels,"pans": pans,"pits": pits}), fin
        
def read_file_complet2(file_name):
    
    print("Loading file: ", file_name)
    f = open(file_name, "rb")
    
    song_data = {}
    
    
    # Read initial fixed bytes
    song_data['initial_bytes'] = f.read(8)
    song_data['song_name'] = readString2(f)
    song_data['song_author'] = readString2(f)
    song_data['original_song_author'] = readString2(f)
    song_data['song_description'] = readString2(f)
    
    song_data['tempo'] = read_short(f)
    
    song_data['additional_bytes'] = f.read(23)
    
    song_data['midi_schematic_file_name'] = readString2(f)
    
    # Fin lecture header
    
    song_data['final_bytes'] = f.read(4)
    
    
    
    #lecture du morceau
    
    # https://github.com/OpenNBS/OpenNoteBlockStudio/blob/master/scripts/load_song/load_song.gml

    layers = []
    ticks = []
    keys = []
    insts = []
    vels = []
    pans = []
    pits = []

    tick = -1;
    jumps = -1;
    while (True):
        jumps = read_short(f)
        #print("tick jumps: ", jumps)

        if(jumps == 0):
            break

        tick += jumps
        layer = -1

        while (True):

            jumps = read_short(f)
            #print("layer jumps: ", jumps)

            if(jumps == 0):
                break

            layer += jumps;
            
            #print("read values")
            
            inst = read_byte(f)
            key = read_byte(f)-33

            vel = read_byte(f) # vel
            pan = read_byte(f) # pan
            pit = read_short(f) #pit


            layers.append(layer)
            ticks.append(tick)
            keys.append(key)
            insts.append(inst)
            
            vels.append(vel)
            pans.append(pan)
            pits.append(pit)


            # noteblocks.Add(new NoteBlock(tick, layer, inst, key)) #Found note block, add to the list

            #instrumentcount[inst]++
            #if (layer < layers):
            #    layercount[layer]++



    fin = f.read()
    f.close()
    return song_data, pd.DataFrame(data = {"tick":ticks, "layer": layers, "key": keys, "insts": insts, "vels": vels,"pans": pans,"pits": pits}), fin
    
    
def WriteNBS(data,file_out, header, fin):
    f = open(file_out, "wb")
    f.write(header)

    write_short(f, 1)

    tick = 0;
    jumps = -1;

    for i in range(len(data.index)):

        ctick = data.iloc[i]['real tick']
        layer = data.iloc[i]['layer']

        key = data.iloc[i]['key']
        inst = data.iloc[i]['insts']
        vel = data.iloc[i]['vels']
        pan = data.iloc[i]['pans']
        pit = data.iloc[i]['pits']


        diff = ctick - tick
        if(diff != 0):
            #print(diff)
            write_short(f, 0)
            write_short(f, diff)
            tick = ctick
            jumps = -1

        write_short(f, layer - jumps)
        jumps = layer

        #print("values")
        write_byte(f, inst)
        write_byte(f,key+33)

        write_byte(f,vel) # vel
        write_byte(f,pan) # pan
        write_short(f,pit) #pit

        #print("fin values")

    write_short(f, 0)
    write_short(f, 0)

    f.write(fin)
    f.close()

def WriteNBS2(data,file_out, song_data, fin):
    f = open(file_out, "wb")
    
    f.write(song_data['initial_bytes'])
    f.write(song_data['song_name'])
    f.write(song_data['song_author'])
    f.write(song_data['original_song_author'])
    f.write(song_data['song_description'])
    
    write_short(f,song_data['tempo'])
    
    f.write(song_data['additional_bytes'])
    f.write(song_data['midi_schematic_file_name'])
    f.write(song_data['final_bytes'])
    

    write_short(f, 1)

    tick = 0;
    jumps = -1;

    for i in range(len(data.index)):

        ctick = data.iloc[i]['real tick']
        layer = data.iloc[i]['layer']

        key = data.iloc[i]['key']
        inst = data.iloc[i]['insts']
        vel = data.iloc[i]['vels']
        pan = data.iloc[i]['pans']
        pit = data.iloc[i]['pits']


        diff = ctick - tick
        if(diff != 0):
            #print(diff)
            write_short(f, 0)
            write_short(f, diff)
            tick = ctick
            jumps = -1

        write_short(f, layer - jumps)
        jumps = layer

        #print("values")
        write_byte(f, inst)
        write_byte(f,key+33)

        write_byte(f,vel) # vel
        write_byte(f,pan) # pan
        write_short(f,pit) #pit

        #print("fin values")

    write_short(f, 0)
    write_short(f, 0)

    f.write(fin)
    f.close()

        
    
class Note:
    def __init__(self, x=0, y=0):
        self.note = x
        self.instr = y
        
    def write(self, nbt_file, x,y,z):
        block = makeBlock(self.note, x, y, z)
        nbtfile['blocks'].append(block)
        
        block = makeBlock(self.instr+25, x, y-1, z)
        nbtfile['blocks'].append(block)
        
        
def PrepData(df, tick_s, tick_offset = 0, decoupeTick = True, ajusterVitesse = True):
    
    tick_multiplier = 10/tick_s#(11.428571428571427)
    df['real tick'] = df['tick']*tick_multiplier#[math.ceil(a)/2 for a in df['tick']*tick_multiplier*2]#df['tick']*tick_multiplier
    
    
    # on met les données sous un autre format

    # on comtpe combien il y a de notes par tick  (en regardan les indices et quand on changhe de tick)
    data = df[['real tick']].drop_duplicates()
    data["i"]=data.index
    data["nb"] = -data.i.diff(periods=-1)
    data = data.set_index("real tick")



    # on remplis le tableau avec les notes
    ticks = []
    for t in data.index:
        tick = []
        for index in df[df['real tick'] == t].index:
            tick.append(Note(df.iloc[index]['key'],df.iloc[index]['insts']))
        ticks.append(tick)
    data['note'] = ticks

    data.nb.values[-1] = len(data.note.values[-1])


    # On soustrait 1 à tous les demis ticks ( le piston prends 1.5 'tick' pour lancer la note, on doit alors la lancer en avance)
    new_tick = []
    for tick in data.index:
        if(tick == int(tick)):
            new_tick.append(tick)
        else:
            new_tick.append(tick-1)

    data.index = new_tick
    data = data.sort_index()

    
    
    # On ajoute 5 secondes pour que tout se goupille bien avant de lancer
    data.index  = data.index + tick_offset


    newData = pd.DataFrame(columns = ['note entier', 'note demi','block number'])

    lastTick = -1
    block_number = 0

    for i in range(len(data.index)):

        row = {'note entier': None, 'note demi': None, 'block number': 0}

        tick = data.index[i]
        tickEntier = int(tick)

        if(lastTick == tickEntier):
            # Si on a deja "traité" le tick on saute au suivant
            continue   

        if(i == len(data.index)-1):
            nextTick = tick +1 #Si pas de prochain tick on s'assure que on le traite pas comme un demi en plus
        else:
            nextTick = data.index[i+1]


        if(tick != tickEntier):
            row['note demi'] = data.iloc[i]["note"]
            # on est sur un demi tick
            #layout.Add(tickEntier, )
        elif(nextTick == tick + 0.5):
            row['note entier'] = data.iloc[i]["note"]
            row['note demi'] = data.iloc[i+1]["note"]
            # Sinon, si on a un demi tick juste apres
            #layout.Add(tickEntier, )
        else:
            row['note entier'] = data.iloc[i]["note"]
            # sinon on est sur un entier et il n'y a rien après

        if(decoupeTick):
            while(tickEntier-lastTick > 4):
                lastTick += 4

                row_inter = {'note entier': None, 'note demi': None, 'block number': block_number}
                block_number+=1
                newData.loc[lastTick] = row_inter

        row['block number'] = block_number
        lastTick = tickEntier
        newData.loc[lastTick] = row  
        block_number+=1


    newData['block number souhaité'] = np.floor(newData.index / 7.5 * 4)


    block_number_added = 0
    newDataa = pd.DataFrame(columns = ['note entier', 'note demi','block number','block number souhaité'])

    for i in range(len(newData.index)-1):
        delta = newData.iloc[i]['block number souhaité'] - newData.iloc[i]['block number'] - block_number_added
        if(delta > 0 and ajusterVitesse):
            if(newData.index[i] +1 != newData.index[i+1]):
                row_inter = {'note entier': None, 'note demi': None, 'block number': 0, 'block number souhaité':0}
                newDataa.loc[newData.index[i]+1] = row_inter
                block_number_added +=1


    for index in newDataa.index:
        newData.loc[index] = newDataa.loc[index]

    for i in data.index:
        if(i == int(i)):
            lenData = 0
            if(newData.loc[i]['note entier'] != None):
                lenData = len(newData.loc[i]['note entier'])
            if(len(data.loc[i]['note'])!= lenData):
                print(i, "error")
        if(i != int(i)):
            lenData = 0
            if(newData.loc[i-0.5]['note demi'] != None):
                lenData = len(newData.loc[i-0.5]['note demi'])
            if(len(data.loc[i]['note'])!= lenData):
                print(i, "error")

    data_old = data
    data = newData
    data = data.sort_index()

    
    return data
    
    
   