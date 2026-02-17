import pandas as pd
import math
from ReadNBS import read_file_complet2,WriteNBS2
import numpy as np
import os

class MusicData:
    def __init__(self):
        #self.read_file(file_in)

        self.file_loaded = False
        

    def read_file(self, file_in):
        self.header, self.data, self.fin = read_file_complet2(file_in)
        self.file_loaded = True
        
        self.directory = os.path.dirname(file_in)
        self.file_name = os.path.splitext(os.path.basename(file_in))[0]
        
        self.process_initial_data()
        self.adjust_layers()
        #self.modify_instrument_data()
        
        return self.file_name
        
        
        
    def get_tempo(self):
        return self.header['tempo']/100
    
    def set_tempo(self, tempo):
        self.header['tempo'] = int(tempo*100)
        
    def get_tempos(self):
        closest_delay = int(np.floor(1/(self.get_tempo()/4)*100//5)*5)
        delays = [closest_delay - 5, closest_delay, closest_delay + 5]
        self.tempos = [100/(d)*4 for d in delays]
        text = []
        for i in range(3):
            if(delays[i]%10 == 0):
                text.append(f"{self.tempos[i]:.2f} : Exact bpm")
            else:
                text.append(f"{self.tempos[i]:.2f} : Swing bpm")
        return text
        
    def upadte_tempo(self, index):
        self.speed_up(self.tempos[index])
        self.set_tempo(20)
    
    def speed_up(self,tick_second):
        self.new_data['real tick'] = [math.ceil(a*20/tick_second) for a in self.new_data['tick']]

    def process_initial_data(self):
        self.data['octave'] = self.data['key'] // 12
        self.data['note'] = self.data['key'] % 12
        self.data['real tick'] = self.data['tick']

    def adjust_layers(self):
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
        nbs_instruments = {'didgeridoo': 12, 'bass': 1, 'guitar': 5, 'banjo': 14, 'pling': 15, 'iron_xylophone': 10,
                       'bit': 13, 'harp': 0, 'cow_bell': 11, 'flute': 6, 'chime': 8, 'xylophone': 9, 'bell': 7}

        octave_instruments = {'didgeridoo': -2, 'bass': -2, 'guitar': -1, 'banjo': 0, 'pling': 0, 'iron_xylophone': 0,
                       'bit': 0, 'harp': 0, 'cow_bell': 1, 'flute': 1, 'chime': 2, 'xylophone': 2, 'bell': 2}

        new_rows = []
        tick = 0
        layer = 0
        for i in range(self.data.shape[0]):
            if self.data.iloc[i]['tick'] > tick:
                tick = self.data.iloc[i]['tick']
                layer = 0

            for instr_i in range(13):
                note = self.data.iloc[i].copy()
                octave = max(-3, min(note['octave'], 4))

                if modifier[octave+3, instr_i]:
                    note['insts'] = nbs_instruments[list(octave_instruments.keys())[instr_i]]
                    instr_octave = octave_instruments[list(octave_instruments.keys())[instr_i]]
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
        tick = 0
        layer = 0
        for i in range(self.new_data.shape[0]):
            if self.new_data.iloc[i]['tick'] > tick:
                tick = self.new_data.iloc[i]['tick']
                layer = 0
            if self.new_data.iloc[i]['layer'] > layer:
                self.new_data.at[i, 'layer'] = layer
            layer += 1

    def write_nbs(self):
        if(self.file_loaded):
            full_file_name  = self.directory+'/'+self.file_name+".nbs"
            print("Saving " + full_file_name)
            WriteNBS2(self.new_data,full_file_name, self.header, self.fin)
            print("file saved")
            return full_file_name

