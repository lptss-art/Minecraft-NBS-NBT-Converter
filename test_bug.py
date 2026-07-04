import pandas as pd
from core.MusicData import prep_data, MusicData
from core.customNBT import CustomNBT
from core.StructureGenerator import StructureGenerator
import core.ReadNBS as ReadNBS

test_file = "test_song.nbs"
header = {
    'initial_bytes': b'\x00'*8,
    'song_name': b'\x04\x00\x00\x00Test',
    'song_author': b'\x00\x00\x00\x00',
    'original_song_author': b'\x00\x00\x00\x00',
    'song_description': b'\x00\x00\x00\x00',
    'tempo': 2000,
    'additional_bytes': b'\x00'*23,
    'midi_schematic_file_name': b'\x00\x00\x00\x00',
    'final_bytes': b'\x00'*4
}
data = pd.DataFrame({
    'tick': [0, 10, 20, 30],
    'layer': [0, 0, 0, 0],
    'key': [33, 40, 50, 60],
    'insts': [0, 0, 0, 0],
    'vels': [100, 100, 100, 100],
    'pans': [100, 100, 100, 100],
    'pits': [0, 0, 0, 0],
    'real tick': [0, 10, 20, 30],
    'octave': [3, 4, 5, 5],
    'note': [1, 2, 3, 4]
})

ReadNBS.write_nbs(data, test_file, header, b'')

music = MusicData()
music.read_file(test_file)
df_prep = prep_data(music.data, ticks_per_second=20, tick_offset=5)

nbt_template = CustomNBT()
generator = StructureGenerator(df_prep, nbt_template, layout_type="Layout2")
generator.generate_blocks()
print(f"Generated Layout2: {generator.global_data.shape}")
