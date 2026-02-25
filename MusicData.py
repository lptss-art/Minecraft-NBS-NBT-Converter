import pandas as pd
import math
import numpy as np
import os
from ReadNBS import read_nbs, write_nbs

class Note:
    """Represents a single note in the music."""
    def __init__(self, x=0, y=0):
        self.note = x
        self.instr = y

    # def write(self, nbt_file, x, y, z):
    #     # Legacy/Unused code requiring external functions
    #     pass

def prep_data(df, tick_s, tick_offset=0, decoupe_tick=True, ajuster_vitesse=True):
    """
    Prepares the dataframe for NBT generation by calculating real ticks and handling timing.

    Args:
        df (pd.DataFrame): Input dataframe.
        tick_s (float): Ticks per second (tempo).
        tick_offset (int): Offset in ticks.
        decoupe_tick (bool): Whether to split ticks.
        ajuster_vitesse (bool): Whether to adjust speed.

    Returns:
        pd.DataFrame: Processed dataframe ready for layout.
    """
    # tick_multiplier calculation (10 ticks/sec default for NBS?)
    # Adjusting to Minecraft Redstone ticks (10 redstone ticks = 1 second? No, 10 rs ticks = 1 sec. 20 game ticks = 1 sec)
    # NBS usually stores ticks.
    tick_multiplier = 10 / tick_s
    df['real tick'] = df['tick'] * tick_multiplier

    # Process data format
    # Count notes per tick
    data = df[['real tick']].drop_duplicates()
    data["i"] = data.index
    data["nb"] = -data.i.diff(periods=-1)
    data = data.set_index("real tick")

    # Fill table with notes
    ticks = []
    for t in data.index:
        tick = []
        # Filter original df for this real tick
        for index in df[df['real tick'] == t].index:
            tick.append(Note(df.iloc[index]['key'], df.iloc[index]['insts']))
        ticks.append(tick)
    data['note'] = ticks

    if len(data.nb.values) > 0:
        data.nb.values[-1] = len(data.note.values[-1])

    # Subtract 1 from all half ticks (piston takes 1.5 ticks to launch, so launch early)
    new_tick = []
    for tick in data.index:
        if tick == int(tick):
            new_tick.append(tick)
        else:
            new_tick.append(tick - 1)

    data.index = new_tick
    data = data.sort_index()

    # Add offset
    data.index = data.index + tick_offset

    new_data = pd.DataFrame(columns=['note entier', 'note demi', 'block number'])

    last_tick = -1
    block_number = 0

    for i in range(len(data.index)):
        row = {'note entier': None, 'note demi': None, 'block number': 0}

        tick = data.index[i]
        tick_entier = int(tick)

        if last_tick == tick_entier:
            # Already processed this tick
            continue

        if i == len(data.index) - 1:
            next_tick = tick + 1
        else:
            next_tick = data.index[i+1]

        if tick != tick_entier:
            row['note demi'] = data.iloc[i]["note"]
        elif next_tick == tick + 0.5:
            row['note entier'] = data.iloc[i]["note"]
            row['note demi'] = data.iloc[i+1]["note"]
        else:
            row['note entier'] = data.iloc[i]["note"]

        if decoupe_tick:
            while tick_entier - last_tick > 4:
                last_tick += 4
                row_inter = {'note entier': None, 'note demi': None, 'block number': block_number}
                block_number += 1
                new_data.loc[last_tick] = row_inter

        row['block number'] = block_number
        last_tick = tick_entier
        new_data.loc[last_tick] = row
        block_number += 1

    new_data['block number souhaité'] = np.floor(new_data.index / 7.5 * 4)

    block_number_added = 0
    new_data_adjusted = pd.DataFrame(columns=['note entier', 'note demi', 'block number', 'block number souhaité'])

    for i in range(len(new_data.index) - 1):
        delta = new_data.iloc[i]['block number souhaité'] - new_data.iloc[i]['block number'] - block_number_added
        if delta > 0 and ajuster_vitesse:
            if new_data.index[i] + 1 != new_data.index[i+1]:
                row_inter = {'note entier': None, 'note demi': None, 'block number': 0, 'block number souhaité': 0}
                new_data_adjusted.loc[new_data.index[i] + 1] = row_inter
                block_number_added += 1

    for index in new_data_adjusted.index:
        new_data.loc[index] = new_data_adjusted.loc[index]

    # Verification (optional, prints errors)
    for i in data.index:
        if i == int(i):
            len_data = 0
            if new_data.loc[i]['note entier'] is not None:
                len_data = len(new_data.loc[i]['note entier'])
            if len(data.loc[i]['note']) != len_data:
                print(i, "error verification entier")
        if i != int(i):
            len_data = 0
            if new_data.loc[i-0.5]['note demi'] is not None:
                len_data = len(new_data.loc[i-0.5]['note demi'])
            if len(data.loc[i]['note']) != len_data:
                print(i, "error verification demi")

    data = new_data.sort_index()
    return data

class MusicData:
    """
    Handles loading, processing, and saving of NBS music data.
    """
    def __init__(self):
        self.file_loaded = False
        self.header = None
        self.data = None
        self.fin = None
        self.directory = None
        self.file_name = None
        self.new_data = None
        self.tempos = []

    def read_file(self, file_in):
        """Reads an NBS file."""
        self.header, self.data, self.fin = read_nbs(file_in)
        self.file_loaded = True
        
        self.directory = os.path.dirname(file_in)
        self.file_name = os.path.splitext(os.path.basename(file_in))[0]
        
        self.process_initial_data()
        self.adjust_layers()
        
        return self.file_name
        
    def get_tempo(self):
        """Returns the tempo in ticks per second."""
        if self.header:
            return self.header['tempo'] / 100
        return 0
    
    def set_tempo(self, tempo):
        """Sets the tempo."""
        if self.header:
            self.header['tempo'] = int(tempo * 100)
        
    def get_tempos(self):
        """Calculates possible tempos for optimization."""
        current_tempo = self.get_tempo()
        if current_tempo == 0:
            return []

        # Calculation logic from original code
        closest_delay = int(np.floor(1 / (current_tempo / 4) * 100 // 5) * 5)
        delays = [closest_delay - 5, closest_delay, closest_delay + 5]
        # Avoid division by zero
        delays = [d for d in delays if d != 0]

        self.tempos = [100 / d * 4 for d in delays]
        text = []
        for i in range(len(delays)):
            if delays[i] % 10 == 0:
                text.append(f"{self.tempos[i]:.2f} : Exact bpm")
            else:
                text.append(f"{self.tempos[i]:.2f} : Swing bpm")
        return text
        
    def update_tempo(self, index):
        """Updates the tempo to the selected index from calculated tempos."""
        if 0 <= index < len(self.tempos):
            self.speed_up(self.tempos[index])
            self.set_tempo(20) # Set to standard Minecraft tick rate?
    
    def speed_up(self, tick_second):
        """Resamples the song ticks to match a target ticks/second rate."""
        # This creates 'new_data' which seems to be the one to be saved
        if self.data is not None:
            # We copy data to new_data if not exists or start fresh
            self.new_data = self.data.copy()
            # Calculate new tick positions
            self.new_data['real tick'] = [math.ceil(a * 20 / tick_second) for a in self.new_data['tick']]
            self.final_layer_adjustment()

    def process_initial_data(self):
        """Adds octave and note columns."""
        if self.data is not None:
            self.data['octave'] = self.data['key'] // 12
            self.data['note'] = self.data['key'] % 12
            self.data['real tick'] = self.data['tick']
            self.new_data = self.data.copy() # Initialize new_data

    def adjust_layers(self):
        """Ensures layers are sequential per tick."""
        if self.data is not None:
            tick = 0
            layer = 0
            for i in range(self.data.shape[0]):
                if self.data.iloc[i]['tick'] > tick:
                    tick = self.data.iloc[i]['tick']
                    layer = 0
                if self.data.iloc[i]['layer'] > layer:
                    self.data.at[i, 'layer'] = layer
                layer += 1

    def modify_instrument_data(self, modifier):
        """
        Modifies instruments and keys based on a modifier matrix (octave x instrument).
        """
        if self.data is None:
            return

        nbs_instruments = {'didgeridoo': 12, 'bass': 1, 'guitar': 5, 'banjo': 14, 'pling': 15, 'iron_xylophone': 10,
                       'bit': 13, 'harp': 0, 'cow_bell': 11, 'flute': 6, 'chime': 8, 'xylophone': 9, 'bell': 7}

        octave_instruments = {'didgeridoo': -2, 'bass': -2, 'guitar': -1, 'banjo': 0, 'pling': 0, 'iron_xylophone': 0,
                       'bit': 0, 'harp': 0, 'cow_bell': 1, 'flute': 1, 'chime': 2, 'xylophone': 2, 'bell': 2}

        new_rows = []
        tick = 0
        layer = 0

        # Iterate over original data
        for i in range(self.data.shape[0]):
            if self.data.iloc[i]['tick'] > tick:
                tick = self.data.iloc[i]['tick']
                layer = 0

            # modifier seems to be 8x13 matrix (octaves -3 to 4 mapped to indices)
            for instr_i in range(13):
                note = self.data.iloc[i].copy()
                octave = max(-3, min(note['octave'], 4))

                # Check if this instrument/octave combination is selected in the modifier
                if modifier[octave+3, instr_i]:
                    instrument_name = list(octave_instruments.keys())[instr_i]
                    note['insts'] = nbs_instruments[instrument_name]
                    instr_octave = octave_instruments[instrument_name]

                    # Adjust key based on target instrument octave
                    if instr_octave < octave:
                        note['key'] = note['note'] + 12
                    elif instr_octave + 1 == octave:
                        note['key'] = note['note'] + 12
                    else:
                        note['key'] = note['note']

                    note['layer'] = layer
                    layer += 1
                    new_rows.append(note)

        self.new_data = pd.DataFrame(new_rows)
        self.final_layer_adjustment()
    
    def final_layer_adjustment(self):
        """Adjusts layers for new_data."""
        if self.new_data is not None and not self.new_data.empty:
            tick = 0
            layer = 0
            # Ensure sorting by real tick first
            self.new_data = self.new_data.sort_values(by=['real tick'])

            for i in range(self.new_data.shape[0]):
                if self.new_data.iloc[i]['real tick'] > tick:
                    tick = self.new_data.iloc[i]['real tick']
                    layer = 0
                if self.new_data.iloc[i]['layer'] > layer:
                    self.new_data.at[i, 'layer'] = layer
                layer += 1

    def write_nbs(self):
        """Writes the modified data to a new NBS file."""
        if self.file_loaded and self.new_data is not None:
            full_file_name = self.directory + '/' + self.file_name + ".nbs"
            print("Saving " + full_file_name)
            write_nbs(self.new_data, full_file_name, self.header, self.fin)
            print("file saved")
            return full_file_name
        return None
