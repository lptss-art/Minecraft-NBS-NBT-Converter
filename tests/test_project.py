import unittest
import os
import shutil
import pandas as pd
import numpy as np
from core.brick import Brick
from core.customNBT import CustomNBT
from core.Layout2 import Layout2Brick
from core.Layout1 import Layout1Brick, Layout1Track
from core.Layout2 import Layout2Track
from core.MusicData import prep_data, Note
import core.ReadNBS as ReadNBS
import sys
import os

# Add tools to path to allow importing the visualizer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from tools.visualize_nbt import render_data_to_image, export_topdown_grid
    CAN_VISUALIZE = True
except ImportError:
    CAN_VISUALIZE = False

class TestBrickClass(unittest.TestCase):
    def test_initialization(self):
        data = Brick()
        self.assertEqual(data.position, [0, 0, 0])
        self.assertEqual(len(data.blocks), 0)

    def test_add_block_and_clean(self):
        data = Brick()

        # Add block
        data.add_block(0, 0, 0, 1)
        self.assertEqual(len(data.blocks), 1)
        self.assertEqual(data.blocks[0]['index'], 1)
        self.assertEqual(data.blocks[0]['pos'], [0, 0, 0])

        # Add another block at same position
        data.add_block(0, 0, 0, 2)
        self.assertEqual(len(data.blocks), 2)

        # Clean should keep the second one
        data.clean()
        self.assertEqual(len(data.blocks), 1)
        self.assertEqual(data.blocks[0]['index'], 2)

    def test_set_layers(self):
        data = Brick()
        data.add_block(0, 0, 0, 1, tick=10, random_delay_range=5)
        data.set_layers(default_random_amount=5)
        # Layer should be set based on tick and random
        # Layer = tick - rand(0, 5) => 10 - [0,5] => [5, 10]
        layer = data.blocks[0]['metadata']['layer']
        self.assertTrue(5 <= layer <= 10)

class TestCustomNBT(unittest.TestCase):
    def test_initialization(self):
        nbt = CustomNBT()
        self.assertIsNotNone(nbt.nbtfile)
        self.assertTrue(len(nbt.nbtfile['palette']) > 0)

    def test_get_index(self):
        nbt = CustomNBT()
        idx1 = nbt.get_index("minecraft:stone")
        idx2 = nbt.get_index("minecraft:stone")
        self.assertEqual(idx1, idx2)

        idx3 = nbt.get_index("minecraft:dirt")
        self.assertNotEqual(idx1, idx3)

    def test_add_block(self):
        nbt = CustomNBT()
        idx = nbt.get_index("minecraft:stone")
        nbt.add_block([0, 1, 0], idx)
        self.assertEqual(len(nbt.nbtfile['blocks']), 1)
        block = nbt.nbtfile['blocks'][0]
        self.assertEqual(block['state'].value, idx)
        self.assertEqual(block['pos'][1].value, 1)

class TestLayout1(unittest.TestCase):
    def test_add_notes(self):
        nbt = CustomNBT()
        layout = Layout1Brick(nbt=nbt)

        notes_int = [Note(1, 0), Note(5, 0)]
        notes_half = [Note(3, 0)]

        layout.build(tick_delay=2, notes_integer=notes_int, notes_half=notes_half)

        # Check if data was populated
        self.assertTrue(len(layout.blocks) > 0)

        if CAN_VISUALIZE:
            # We must apply clean() with a floor to resolve needs_down like in the real app
            floor_idx = nbt.get_index_safe("minecraft:stone")
            layout.clean(floor_idx)

            render_data_to_image(
                layout.blocks,
                nbt_palette=nbt.nbtfile['palette'],
                title="Test Layout 1",
                output_path="output/debug_images/test_layout1.png"
            )
            export_topdown_grid(
                layout.blocks,
                nbt_palette=nbt.nbtfile['palette'],
                title="Test Layout 1 Grid",
                csv_path="output/debug_images/test_layout1_grid.csv",
                img_path="output/debug_images/test_layout1_grid.png"
            )

    def test_write_nbt(self):
        nbt = CustomNBT()
        layout = Layout1Brick(nbt=nbt)
        layout.add_block(0, 0, 0, 1)

        initial_blocks = len(nbt.nbtfile['blocks'])
        layout.write_nbt()
        self.assertTrue(len(nbt.nbtfile['blocks']) > initial_blocks)

class TestTrackAssembly(unittest.TestCase):
    def test_layout1_track_assembly(self):
        nbt = CustomNBT()
        track = Layout1Track(nbt_template=nbt)

        # Simulate df_notes
        data = {
            'note entier': [[Note(1, 0)], [], [Note(5, 0), Note(7, 0)]],
            'note demi': [[], [Note(3, 0)], []]
        }
        df_notes = pd.DataFrame(data, index=[0, 2, 4])

        track.build_sequence(df_notes)
        self.assertTrue(len(track.blocks) > 0)

        if CAN_VISUALIZE:
            floor_idx = nbt.get_index_safe("minecraft:stone")
            track.clean(floor_idx)

            render_data_to_image(
                track.blocks,
                nbt_palette=nbt.nbtfile['palette'],
                title="Test Track Layout 1",
                output_path="output/debug_images/test_layout1_track.png"
            )
            export_topdown_grid(
                track.blocks,
                nbt_palette=nbt.nbtfile['palette'],
                title="Test Track Layout 1 Grid",
                csv_path="output/debug_images/test_layout1_track_grid.csv",
                img_path="output/debug_images/test_layout1_track_grid.png"
            )

    def test_layout2_track_assembly(self):
        nbt = CustomNBT()
        track = Layout2Track(nbt_template=nbt)

        # Simulate df_notes sequence long enough to see the snake turn
        data = {
            'note entier': [[Note(1, 0)], [], [Note(5, 0)], [Note(7, 0)], [], [Note(12, 0)]],
            'note demi': [[], [Note(3, 0)], [], [], [Note(9, 0)], []]
        }
        df_notes = pd.DataFrame(data, index=[0, 2, 4, 6, 8, 10])

        track.build_sequence(df_notes)
        self.assertTrue(len(track.blocks) > 0)

        if CAN_VISUALIZE:
            floor_idx = nbt.get_index_safe("minecraft:stone")
            track.clean(floor_idx)

            render_data_to_image(
                track.blocks,
                nbt_palette=nbt.nbtfile['palette'],
                title="Test Track Layout 2",
                output_path="output/debug_images/test_layout2_track.png"
            )
            export_topdown_grid(
                track.blocks,
                nbt_palette=nbt.nbtfile['palette'],
                title="Test Track Layout 2 Grid",
                csv_path="output/debug_images/test_layout2_track_grid.csv",
                img_path="output/debug_images/test_layout2_track_grid.png"
            )

class TestLayout2(unittest.TestCase):
    def test_add_notes(self):
        nbt = CustomNBT()
        layout = Layout2Brick(nbt=nbt)

        notes_int = [Note(1, 0), Note(5, 0)]
        notes_half = [Note(3, 0)]

        layout.build(tick_delay=2, notes_integer=notes_int, notes_half=notes_half)

        # Check if data was populated
        self.assertTrue(len(layout.blocks) > 0)

        if CAN_VISUALIZE:
            floor_idx = nbt.get_index_safe("minecraft:stone")
            layout.clean(floor_idx)

            render_data_to_image(
                layout.blocks,
                nbt_palette=nbt.nbtfile['palette'],
                title="Test Layout 2",
                output_path="output/debug_images/test_layout2.png"
            )
            export_topdown_grid(
                layout.blocks,
                nbt_palette=nbt.nbtfile['palette'],
                title="Test Layout 2 Grid",
                csv_path="output/debug_images/test_layout2_grid.csv",
                img_path="output/debug_images/test_layout2_grid.png"
            )

    def test_write_nbt(self):
        nbt = CustomNBT()
        layout = Layout2Brick(nbt=nbt)
        layout.add_block(0, 0, 0, 1)

        initial_blocks = len(nbt.nbtfile['blocks'])
        layout.write_nbt()
        self.assertTrue(len(nbt.nbtfile['blocks']) > initial_blocks)

class TestMusicData(unittest.TestCase):
    def test_prep_data(self):
        # Create a dummy dataframe
        df = pd.DataFrame({
            'tick': [0, 2, 4],
            'key': [10, 12, 14],
            'insts': [0, 0, 0]
        })

        # Test prep_data
        # 10 ticks/s => multiplier = 1.
        processed_df = prep_data(df, ticks_per_second=10)

        # Check that we have rows
        self.assertEqual(len(processed_df), 3)
        # Check columns
        self.assertIn('note entier', processed_df.columns)
        # Check index values (should be 0, 2, 4 or close if processed)
        self.assertTrue(0 in processed_df.index)

class TestReadNBS(unittest.TestCase):
    def test_read_write_integration(self):

        test_file = "test_song.nbs"

        # Create dummy data
        header = {
            'initial_bytes': b'\x00'*8,
            'song_name': b'\x04\x00\x00\x00Test',
            'song_author': b'\x00\x00\x00\x00',
            'original_song_author': b'\x00\x00\x00\x00',
            'song_description': b'\x00\x00\x00\x00',
            'tempo': 1000,
            'additional_bytes': b'\x00'*23,
            'midi_schematic_file_name': b'\x00\x00\x00\x00',
            'final_bytes': b'\x00'*4
        }

        data = pd.DataFrame({
            'tick': [0, 2],
            'layer': [0, 0],
            'key': [10, 12],
            'insts': [0, 0],
            'vels': [100, 100],
            'pans': [100, 100],
            'pits': [0, 0]
        })

        footer = b''

        # Write
        try:
            ReadNBS.write_nbs(data, test_file, header, footer)

            # Read back
            header_read, data_read, footer_read = ReadNBS.read_nbs(test_file)

            self.assertEqual(header_read['tempo'], 1000)
            self.assertEqual(len(data_read), 2)
            self.assertEqual(data_read.iloc[0]['key'], 10)

        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

if __name__ == '__main__':
    unittest.main()
