import pandas as pd
from struct import unpack, pack
import numpy as np

def read_int(fi):
    """Reads a 4-byte integer from the file."""
    data = fi.read(4)
    if not data:
        return 0
    the_int, = unpack('i', data)
    return the_int

def read_short(fi):
    """Reads a 2-byte short from the file."""
    data = fi.read(2)
    if not data:
        return 0
    sh, = unpack('h', data)
    return sh

def read_byte(fi):
    """Reads a 1-byte integer from the file."""
    data = fi.read(1)
    if not data:
        return 0
    return int.from_bytes(data, "big")

def read_string(fi):
    """Reads a string from the file (length + chars). Returns bytes including length."""
    length = read_int(fi)
    a = pack('i', length)
    for i in range(length):
        a += fi.read(1)
    return a

def write_int(f, a):
    """Writes a 4-byte integer to the file."""
    f.write(pack('i', a))

def write_short(f, a):
    """Writes a 2-byte short to the file."""
    f.write(pack('h', a))

def write_byte(f, a):
    """Writes a 1-byte integer to the file."""
    f.write(pack('b', a))

def read_nbs(file_name):
    """
    Reads an NBS file and returns header data, note data, and footer bytes.
    
    Args:
        file_name (str): Path to the .nbs file.
        
    Returns:
        tuple: (song_data (dict), dataframe (pd.DataFrame), fin (bytes))
    """
    print("Loading file: ", file_name)
    f = open(file_name, "rb")
    
    song_data = {}
    
    # Read initial fixed bytes
    song_data['initial_bytes'] = f.read(8) # First 8 bytes
    
    # Read metadata strings
    song_data['song_name'] = read_string(f)
    song_data['song_author'] = read_string(f)
    song_data['original_song_author'] = read_string(f)
    song_data['song_description'] = read_string(f)
    
    song_data['tempo'] = read_short(f)
    
    song_data['additional_bytes'] = f.read(23) # Auto-save, time sig, stats
    
    song_data['midi_schematic_file_name'] = read_string(f)
    
    song_data['final_bytes'] = f.read(4) # Tick jumps start
    
    # Read Note Blocks
    layers = []
    ticks = []
    keys = []
    insts = []
    vels = []
    pans = []
    pits = []

    tick = -1
    jumps = -1

    while True:
        jumps = read_short(f)
        if jumps == 0:
            break

        tick += jumps
        layer = -1

        while True:
            jumps = read_short(f)
            if jumps == 0:
                break

            layer += jumps
            
            inst = read_byte(f)
            key = read_byte(f) - 33 # NBS key adjustment

            vel = read_byte(f) # velocity
            pan = read_byte(f) # panning
            pit = read_short(f) # pitch

            layers.append(layer)
            ticks.append(tick)
            keys.append(key)
            insts.append(inst)
            vels.append(vel)
            pans.append(pan)
            pits.append(pit)

    fin = f.read() # Read remaining footer data
    f.close()
    
    df = pd.DataFrame(data={
        "tick": ticks,
        "layer": layers,
        "key": keys,
        "insts": insts,
        "vels": vels,
        "pans": pans,
        "pits": pits
    })

    return song_data, df, fin

def write_nbs(data, file_out, song_data, fin):
    """
    Writes data to an NBS file.

    Args:
        data (pd.DataFrame): The note data.
        file_out (str): Output file path.
        song_data (dict): Header data.
        fin (bytes): Footer bytes.
    """
    f = open(file_out, "wb")
    
    f.write(song_data['initial_bytes'])
    f.write(song_data['song_name'])
    f.write(song_data['song_author'])
    f.write(song_data['original_song_author'])
    f.write(song_data['song_description'])
    
    write_short(f, song_data['tempo'])
    
    f.write(song_data['additional_bytes'])
    f.write(song_data['midi_schematic_file_name'])
    f.write(song_data['final_bytes'])
    
    # Start writing notes
    write_short(f, 1) # Start tick jumps

    tick = 0
    jumps = -1

    # Ensure data is sorted if necessary, though usually expected to be
    # data = data.sort_values(by=['real tick', 'layer'])

    for i in range(len(data.index)):
        ctick = int(data.iloc[i]['real tick']) if 'real tick' in data.columns else int(data.iloc[i]['tick'])
        layer = int(data.iloc[i]['layer'])

        key = int(data.iloc[i]['key'])
        inst = int(data.iloc[i]['insts'])
        vel = int(data.iloc[i]['vels'])
        pan = int(data.iloc[i]['pans'])
        pit = int(data.iloc[i]['pits'])

        diff = ctick - tick
        if diff != 0:
            write_short(f, 0) # End of layer jumps for previous tick
            write_short(f, diff) # Jumps to next tick
            tick = ctick
            jumps = -1

        write_short(f, layer - jumps)
        jumps = layer

        write_byte(f, inst)
        write_byte(f, key + 33)
        write_byte(f, vel)
        write_byte(f, pan)
        write_short(f, pit)

    write_short(f, 0) # End of tick jumps
    write_short(f, 0) # End of layers (redundant but safe)

    f.write(fin)
    f.close()
