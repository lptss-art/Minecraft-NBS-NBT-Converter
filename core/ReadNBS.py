import pandas as pd
from struct import unpack, pack
import numpy as np

def read_int(file_stream):
    """Reads a 4-byte integer from the file."""
    data = file_stream.read(4)
    if not data:
        return 0
    integer_value, = unpack('i', data)
    return integer_value

def read_short(file_stream):
    """Reads a 2-byte short from the file."""
    data = file_stream.read(2)
    if not data:
        return 0
    short_value, = unpack('h', data)
    return short_value

def read_byte(file_stream):
    """Reads a 1-byte integer from the file."""
    data = file_stream.read(1)
    if not data:
        return 0
    return int.from_bytes(data, "big")

def read_string(file_stream):
    """Reads a string from the file (length + chars). Returns bytes including length."""
    length = read_int(file_stream)
    string_bytes = pack('i', length)
    for i in range(length):
        string_bytes += file_stream.read(1)
    return string_bytes

def write_int(file_stream, value):
    """Writes a 4-byte integer to the file."""
    file_stream.write(pack('i', value))

def write_short(file_stream, value):
    """Writes a 2-byte short to the file."""
    file_stream.write(pack('h', value))

def write_byte(file_stream, value):
    """Writes a 1-byte integer to the file."""
    file_stream.write(pack('b', value))

def read_nbs(file_name):
    """
    Reads an NBS file and returns header data, note data, and footer bytes.
    
    Args:
        file_name (str): Path to the .nbs file.
        
    Returns:
        tuple: (song_data (dict), dataframe (pd.DataFrame), footer_bytes (bytes))
    """
    print("Loading file: ", file_name)
    file_stream = open(file_name, "rb")
    
    song_data = {}
    
    # Read initial fixed bytes
    song_data['initial_bytes'] = file_stream.read(8) # First 8 bytes
    
    # Read metadata strings
    song_data['song_name'] = read_string(file_stream)
    song_data['song_author'] = read_string(file_stream)
    song_data['original_song_author'] = read_string(file_stream)
    song_data['song_description'] = read_string(file_stream)
    
    song_data['tempo'] = read_short(file_stream)
    
    song_data['additional_bytes'] = file_stream.read(23) # Auto-save, time sig, stats
    
    song_data['midi_schematic_file_name'] = read_string(file_stream)
    
    song_data['final_bytes'] = file_stream.read(4) # Tick jumps start
    
    # Read Note Blocks
    layers = []
    ticks = []
    keys = []
    instruments = []
    velocities = []
    pannings = []
    pitches = []

    tick = -1
    jumps = -1

    while True:
        jumps = read_short(file_stream)
        if jumps == 0:
            break

        tick += jumps
        layer = -1

        while True:
            jumps = read_short(file_stream)
            if jumps == 0:
                break

            layer += jumps
            
            instrument = read_byte(file_stream)
            key = read_byte(file_stream) - 33 # NBS key adjustment

            velocity = read_byte(file_stream)
            panning = read_byte(file_stream)
            pitch = read_short(file_stream)

            layers.append(layer)
            ticks.append(tick)
            keys.append(key)
            instruments.append(instrument)
            velocities.append(velocity)
            pannings.append(panning)
            pitches.append(pitch)

    footer_bytes = file_stream.read() # Read remaining footer data
    file_stream.close()
    
    df = pd.DataFrame(data={
        "tick": ticks,
        "layer": layers,
        "key": keys,
        "insts": instruments,
        "vels": velocities,
        "pans": pannings,
        "pits": pitches
    })

    return song_data, df, footer_bytes

def write_nbs(data, file_out, song_data, footer_bytes):
    """
    Writes data to an NBS file.

    Args:
        data (pd.DataFrame): The note data.
        file_out (str): Output file path.
        song_data (dict): Header data.
        footer_bytes (bytes): Footer bytes.
    """
    file_stream = open(file_out, "wb")
    
    file_stream.write(song_data['initial_bytes'])
    file_stream.write(song_data['song_name'])
    file_stream.write(song_data['song_author'])
    file_stream.write(song_data['original_song_author'])
    file_stream.write(song_data['song_description'])
    
    write_short(file_stream, song_data['tempo'])
    
    file_stream.write(song_data['additional_bytes'])
    file_stream.write(song_data['midi_schematic_file_name'])
    file_stream.write(song_data['final_bytes'])
    
    # Start writing notes
    write_short(file_stream, 1) # Start tick jumps

    tick = 0
    jumps = -1

    # Ensure data is sorted if necessary, though usually expected to be
    # data = data.sort_values(by=['real tick', 'layer'])

    for i in range(len(data.index)):
        current_tick = int(data.iloc[i]['real tick']) if 'real tick' in data.columns else int(data.iloc[i]['tick'])
        layer = int(data.iloc[i]['layer'])

        key = int(data.iloc[i]['key'])
        instrument = int(data.iloc[i]['insts'])
        velocity = int(data.iloc[i]['vels'])
        panning = int(data.iloc[i]['pans'])
        pitch = int(data.iloc[i]['pits'])

        diff = current_tick - tick
        if diff != 0:
            write_short(file_stream, 0) # End of layer jumps for previous tick
            write_short(file_stream, diff) # Jumps to next tick
            tick = current_tick
            jumps = -1

        write_short(file_stream, layer - jumps)
        jumps = layer

        write_byte(file_stream, instrument)
        write_byte(file_stream, key + 33)
        write_byte(file_stream, velocity)
        write_byte(file_stream, panning)
        write_short(file_stream, pitch)

    write_short(file_stream, 0) # End of tick jumps
    write_short(file_stream, 0) # End of layers (redundant but safe)

    file_stream.write(footer_bytes)
    file_stream.close()
