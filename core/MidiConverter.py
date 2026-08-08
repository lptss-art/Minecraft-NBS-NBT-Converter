import mido
import pandas as pd
import struct
import os

def convert_midi_to_nbs_df(midi_path):
    mid = mido.MidiFile(midi_path)
    notes = []

    target_tps = 10

    abs_time_s = 0.0
    for msg in mid:
        abs_time_s += msg.time
        if not msg.is_meta and msg.type == 'note_on' and msg.velocity > 0:
            key = msg.note - 21
            if key < 0: key = 0
            if key > 87: key = 87

            notes.append({
                'time_s': abs_time_s,
                'key': key,
                'insts': 0, # Default Harp
                'vels': 100,
                'pans': 100,
                'pits': 0
            })

    df = pd.DataFrame(notes)
    if not df.empty:
        df['tick'] = (df['time_s'] * target_tps).round().astype(int)
        df = df.sort_values(by='tick')
        df['layer'] = df.groupby('tick').cumcount()
    else:
        df = pd.DataFrame(columns=['tick', 'layer', 'key', 'insts', 'vels', 'pans', 'pits'])

    version = 5
    vanilla_insts = 16
    length = df['tick'].max() if not df.empty else 0
    layers = df['layer'].max() + 1 if not df.empty else 0

    initial_bytes = struct.pack('<hbbhh', 0, version, vanilla_insts, length, layers)

    name = os.path.splitext(os.path.basename(midi_path))[0]

    def write_string(s):
        b = s.encode('latin1', errors='replace')
        return struct.pack('<i', len(b)) + b

    song_data = {
        'initial_bytes': initial_bytes,
        'song_name': write_string(name),
        'song_author': write_string("MIDI Converter"),
        'original_song_author': write_string(""),
        'song_description': write_string("Converted from MIDI"),
        'tempo': int(target_tps * 100),
        'additional_bytes': struct.pack('<bbbiiiii', 0, 0, 4, 0, 0, 0, 0, 0),
        'midi_schematic_file_name': write_string(os.path.basename(midi_path)),
        'final_bytes': struct.pack('<bbh', 0, 0, 0)
    }

    return song_data, df, b""
