import os
import random
import pandas as pd
from core.MusicData import Note
from core.Layout2 import Layout2Brick
from core.Layout1 import Layout1Brick
from core.customNBT import CustomNBT
from core.StructureGenerator import StructureGenerator

try:
    from tools.visualize_nbt import render_data_to_image, export_topdown_grid
    CAN_VISUALIZE = True
except ImportError:
    CAN_VISUALIZE = False

def make_notes(count):
    return [Note(random.randint(0, 24), random.randint(0, 5)) for _ in range(count)]

def generate_test_blocks():
    if not os.path.exists("output/debug"):
        os.makedirs("output/debug")
    if not os.path.exists("output/debug_images"):
        os.makedirs("output/debug_images")

    spawner_nbt = CustomNBT()
    test_index = 0

    # Test 1: Layout 1 (Shape I)
    nbt1 = CustomNBT()
    l1 = Layout1Brick()
    l1.build(notes_integer=make_notes(10), notes_half=make_notes(10), branch_shape='I')
    l1.clean("minecraft:stone")
    l1.normalize()
    l1.write_nbt(nbt1)
    nbt1.write_file("output/debug/debug_layout1_shape_i.nbt")
    if CAN_VISUALIZE:
        render_data_to_image(l1.blocks, nbt1.nbtfile['palette'], "Layout 1 (Shape I)", "output/debug_images/debug_layout1_shape_i.png")
        export_topdown_grid(l1.blocks, nbt1.nbtfile['palette'], "Layout 1 (Shape I) Grid", "output/debug_images/debug_layout1_shape_i_grid.csv", "output/debug_images/debug_layout1_shape_i_grid.png")
    spawner_nbt.add_structure_block([test_index * 15, 0, 0], "debug_layout1_shape_i")
    test_index += 1

    # Test 2: Layout 1 (Shape L)
    nbt2 = CustomNBT()
    l2 = Layout1Brick()
    l2.build(notes_integer=make_notes(10), notes_half=make_notes(10), branch_shape='L')
    l2.clean("minecraft:stone")
    l2.normalize()
    l2.write_nbt(nbt2)
    nbt2.write_file("output/debug/debug_layout1_shape_l.nbt")
    if CAN_VISUALIZE:
        render_data_to_image(l2.blocks, nbt2.nbtfile['palette'], "Layout 1 (Shape L)", "output/debug_images/debug_layout1_shape_l.png")
        export_topdown_grid(l2.blocks, nbt2.nbtfile['palette'], "Layout 1 (Shape L) Grid", "output/debug_images/debug_layout1_shape_l_grid.csv", "output/debug_images/debug_layout1_shape_l_grid.png")
    spawner_nbt.add_structure_block([test_index * 15, 0, 0], "debug_layout1_shape_l")
    test_index += 1

    # Test 3: Layout 2 (Shape I)
    nbt3 = CustomNBT()
    l3 = Layout2Brick()
    l3.build(notes_integer=make_notes(10), notes_half=make_notes(10), en_L=False)
    l3.clean("minecraft:stone")
    l3.normalize()
    l3.write_nbt(nbt3)
    nbt3.write_file("output/debug/debug_layout2_shape_i.nbt")
    if CAN_VISUALIZE:
        render_data_to_image(l3.blocks, nbt3.nbtfile['palette'], "Layout 2 (Shape I)", "output/debug_images/debug_layout2_shape_i.png")
        export_topdown_grid(l3.blocks, nbt3.nbtfile['palette'], "Layout 2 (Shape I) Grid", "output/debug_images/debug_layout2_shape_i_grid.csv", "output/debug_images/debug_layout2_shape_i_grid.png")
    spawner_nbt.add_structure_block([test_index * 15, 0, 0], "debug_layout2_shape_i")
    test_index += 1

    # Test 4: Layout 2 (Shape L)
    nbt4 = CustomNBT()
    l4 = Layout2Brick()
    l4.build(notes_integer=make_notes(10), notes_half=make_notes(10), en_L=True)
    l4.clean("minecraft:stone")
    l4.normalize()
    l4.write_nbt(nbt4)
    nbt4.write_file("output/debug/debug_layout2_shape_l.nbt")
    if CAN_VISUALIZE:
        render_data_to_image(l4.blocks, nbt4.nbtfile['palette'], "Layout 2 (Shape L)", "output/debug_images/debug_layout2_shape_l.png")
        export_topdown_grid(l4.blocks, nbt4.nbtfile['palette'], "Layout 2 (Shape L) Grid", "output/debug_images/debug_layout2_shape_l_grid.csv", "output/debug_images/debug_layout2_shape_l_grid.png")
    spawner_nbt.add_structure_block([test_index * 15, 0, 0], "debug_layout2_shape_l")
    test_index += 1

    # Test 5: Complete Serpentine Assembly
    data_seq = {
        'tick': list(range(0, 20, 2)),
        'note entier': [make_notes(random.randint(1, 6)) for _ in range(10)],
        'note demi': [make_notes(random.randint(0, 4)) for _ in range(10)]
    }
    df_seq = pd.DataFrame(data_seq).set_index('tick')

    nbt_seq = CustomNBT()
    gen_seq = StructureGenerator(df_seq, layout_type="Layout2", palettes={"branch_shape": "L"})
    gen_seq.generate_blocks()

    gen_seq.global_data.clean("minecraft:stone")

    gen_seq.global_data.write_nbt(nbt_seq)
    nbt_seq.write_file("output/debug/debug_assembly_serpentine.nbt")
    spawner_nbt.add_structure_block([test_index * 15, 0, 0], "debug_assembly_serpentine")
    test_index += 1

    # Output the master spawner
    index_stone = spawner_nbt.get_index_safe("minecraft:stone")
    index_button = spawner_nbt.get_index_safe("minecraft:stone_button", {"face": "floor", "facing": "east"})
    spawner_nbt.add_block([-1, 0, 0], index_stone)
    spawner_nbt.add_block([-1, 1, 0], index_button)
    spawner_nbt.write_file("output/debug/debug_spawner.nbt")

    return 4, 1
