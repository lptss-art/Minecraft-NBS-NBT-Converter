import streamlit as st
import os
import shutil
import numpy as np
import pandas as pd
from core.MusicData import MusicData, prep_data
from core.customNBT import CustomNBT
from core.StructureGenerator import StructureGenerator

st.set_page_config(page_title="NoteBlock Studio to NBT Generator", layout="wide")

st.title("NoteBlock Studio to NBT Generator")

tab1, tab2, tab3 = st.tabs(["1. Pre-process NBS (Instruments & Tempo)", "2. Generate NBT Structure", "3. Debug & Test Generation"])

with tab1:
    st.header("Pre-process NBS")

    uploaded_file = st.file_uploader("Upload NBS file", type=["nbs"], key="nbs_upload_1")

    if uploaded_file is not None:
        if not os.path.exists("temp"):
            os.makedirs("temp")
        temp_path = os.path.join("temp", uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"File {uploaded_file.name} loaded successfully!")

        processor = MusicData()
        name = processor.read_file(temp_path)

        st.subheader("File Parameters")
        output_name = st.text_input("Output File Name", value=f"{name}_updated")

        tempo = processor.get_tempo()
        st.write(f"**Input Tempo:** {tempo:.2f}")

        adjust_tempo = st.checkbox("Adjust Tempo")

        tempos = processor.get_tempos()
        selected_tempo_idx = st.selectbox("Choose tempo:", range(len(tempos)), format_func=lambda i: tempos[i], index=1 if len(tempos) > 1 else 0)

        st.subheader("Instruments by Octave")

        instruments = ['didgeridoo', 'bass', 'guitar', 'banjo', 'pling', 'iron_xylophone',
                       'bit', 'harp', 'cow_bell', 'flute', 'chime', 'xylophone', 'bell']
        octaves = [-3, -2, -1, 0, 1, 2, 3, 4]

        instrument_values = {'didgeridoo': -2, 'bass': -2, 'guitar': -1, 'banjo': 0, 'pling': 0, 'iron_xylophone': 0,
                            'bit': 0, 'harp': 0, 'cow_bell': 1, 'flute': 1, 'chime': 2, 'xylophone': 2, 'bell': 2}

        if 'instrument_matrix' not in st.session_state:
            df = pd.DataFrame(False, index=octaves, columns=instruments)
            st.session_state.instrument_matrix = df

        def style_df(data):
            df_styles = pd.DataFrame('', index=data.index, columns=data.columns)
            for row in data.index:
                for col in data.columns:
                    val = instrument_values[col]
                    if row < val:
                        # Gray for below native range
                        df_styles.loc[row, col] = 'background-color: #d3d3d3; color: black;'
                    elif row == val or row == val + 1:
                        # Blue for native range (2 octaves)
                        df_styles.loc[row, col] = 'background-color: #add8e6; color: black;'
                    else:
                        # Yellow for above native range
                        df_styles.loc[row, col] = 'background-color: #ffffe0; color: black;'
            return df_styles

        st.markdown("""
        <style>
        /* Increase the height of the cells in the data editor to make them easier to click */
        [data-testid="stDataFrameResizable"] {
            width: 100% !important;
        }
        [data-testid="data-grid"] {
            font-size: 1.1rem;
        }
        </style>
        """, unsafe_allow_html=True)

        st.write("*Color Legend: 🟦 Blue = Native Minecraft Octave Range (2 octaves), ⬜ Gray = Below Range, 🟨 Yellow = Above Range. Click the cells to toggle.*")

        edited_df = st.data_editor(
            st.session_state.instrument_matrix.style.apply(style_df, axis=None),
            use_container_width=True,
            height=350
        )

        if st.button("Save & Process"):
            processor.file_name = output_name
            modifier_matrix = edited_df.to_numpy()
            processor.modify_instrument_data(modifier_matrix)

            if adjust_tempo:
                processor.update_tempo(selected_tempo_idx)

            out_file = processor.write_nbs()
            if out_file:
                st.session_state.processed_nbs_path = out_file
                st.session_state.processed_nbs_name = f"{output_name}.nbs"

        if 'processed_nbs_path' in st.session_state and os.path.exists(st.session_state.processed_nbs_path):
            with open(st.session_state.processed_nbs_path, "rb") as f:
                st.download_button(
                    label="Download Processed NBS",
                    data=f,
                    file_name=st.session_state.processed_nbs_name,
                    mime="application/octet-stream"
                )
            st.success("File processed and ready for download!")

with tab2:
    st.header("Generate NBT Structure")

    uploaded_file_2 = st.file_uploader("Upload NBS file for Generation", type=["nbs"], key="nbs_upload_2")

    if uploaded_file_2 is not None:
        if not os.path.exists("temp"):
            os.makedirs("temp")
        temp_path_2 = os.path.join("temp", uploaded_file_2.name)
        with open(temp_path_2, "wb") as f:
            f.write(uploaded_file_2.getbuffer())

        layout_type = st.selectbox("Select Structure Layout:", ["Layout2 (Compact Serpentine)", "Layout1 (Minecart)"])
        export_mode = st.selectbox("Generation Mode:", ["Single Monolithic File", "Dynamic Multi-Part (Structure Blocks)"])

        st.subheader("Decoration Palette")

        col1, col2, col3 = st.columns(3)

        with col1:
            floor_options = ["stone", "andesite", "cobblestone", "mossy_cobblestone", "oak_planks", "grass_block", "dirt"]
            selected_floor = st.multiselect("Floor Blocks", floor_options, default=["stone"])
        with col2:
            flower_options = ["poppy", "dandelion", "azure_bluet", "red_tulip", "pink_tulip", "oxeye_daisy", "cornflower", "lily_of_the_valley"]
            selected_flowers = st.multiselect("Flowers / Ground Decor", flower_options, default=["poppy", "dandelion"])
        with col3:
            ceiling_options = ["lantern", "soul_lantern", "torch", "redstone_lamp", "ochre_froglight"]
            selected_ceiling = st.multiselect("Lighting / Ceiling", ceiling_options, default=["lantern"])

        palettes = {
            "floor": selected_floor,
            "flowers": selected_flowers,
            "ceiling": selected_ceiling
        }

        if st.button("Generate NBT"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                status_text.text("Loading Music Data...")
                progress_bar.progress(10)

                music = MusicData()
                music.read_file(temp_path_2)
                progress_bar.progress(30)

                if music.data is None or music.data.empty:
                    st.error("NBS file contains no note data.")
                else:
                    status_text.text("Preparing Data...")
                    df_prep = prep_data(music.data, ticks_per_second=20, tick_offset=5)
                    progress_bar.progress(50)

                    status_text.text("Generating Structure Blocks...")
                    nbt_template = CustomNBT()
                    generator = StructureGenerator(df_prep, nbt_template, layout_type=layout_type, palettes=palettes)
                    generator.generate_blocks()
                    progress_bar.progress(80)

                    status_text.text("Exporting NBT...")
                    out_name = os.path.splitext(uploaded_file_2.name)[0]

                    if not os.path.exists("output"):
                        os.makedirs("output")

                    if export_mode == "Single Monolithic File":
                        out_path = f"output/{out_name}_complete.nbt"
                        generator.export_monolithic(out_path)
                        st.session_state.generated_nbt_path = out_path
                        st.session_state.generated_nbt_name = f"{out_name}_complete.nbt"
                        st.session_state.generated_nbt_mime = "application/octet-stream"
                        progress_bar.progress(100)
                        status_text.text("Finished!")
                    else:
                        out_dir = f"output/{out_name}_parts"
                        if os.path.exists(out_dir):
                            shutil.rmtree(out_dir)
                        os.makedirs(out_dir, exist_ok=True)
                        generator.export_multipart(out_dir)

                        # Zip the directory
                        zip_path = f"output/{out_name}_parts.zip"
                        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', out_dir)

                        st.session_state.generated_nbt_path = zip_path
                        st.session_state.generated_nbt_name = f"{out_name}_parts.zip"
                        st.session_state.generated_nbt_mime = "application/zip"

                        progress_bar.progress(100)
                        status_text.text("Finished!")

            except Exception as e:
                import traceback
                st.error(f"An error occurred during generation: {e}")
                st.text(traceback.format_exc())

        if 'generated_nbt_path' in st.session_state and os.path.exists(st.session_state.generated_nbt_path):
            st.success("Generation completed successfully!")
            with open(st.session_state.generated_nbt_path, "rb") as f:
                st.download_button(
                    label=f"Download {st.session_state.generated_nbt_name}",
                    data=f,
                    file_name=st.session_state.generated_nbt_name,
                    mime=st.session_state.generated_nbt_mime
                )

with tab3:
    st.header("Debug / Test Generation")

    st.write("Generate complex note block structures (Lego bricks) to test layout limits and transformations directly in Minecraft.")

    if st.button("Generate Test Blocks"):
        import random
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

        st.write("Generating debug lego bricks...")

        if not os.path.exists("output/debug"):
            os.makedirs("output/debug")

        spawner_nbt = CustomNBT()
        test_index = 0

        # Helper for generating notes
        def make_notes(count):
            return [Note(random.randint(0, 24), random.randint(0, 5)) for _ in range(count)]

        # Test 1: Dense Layout1
        nbt1 = CustomNBT()
        l1 = Layout1Brick(nbt=nbt1)
        l1.build(tick_delay=2, notes_integer=make_notes(10), notes_half=make_notes(10))
        l1.clean(nbt1.get_index_safe("minecraft:stone"))
        l1.write_nbt()
        nbt1.write_file("output/debug/debug_layout1_dense.nbt")
        if CAN_VISUALIZE:
            render_data_to_image(l1.blocks, nbt1.nbtfile['palette'], "Layout 1 Dense", "output/debug_images/debug_layout1_dense.png")
            export_topdown_grid(l1.blocks, nbt1.nbtfile['palette'], "Layout 1 Dense Grid", "output/debug_images/debug_layout1_dense_grid.csv", "output/debug_images/debug_layout1_dense_grid.png")
        spawner_nbt.add_structure_block([test_index * 15, 0, 0], "debug_layout1_dense")
        test_index += 1

        # Test 2: Dense Layout2 (Base)
        nbt2 = CustomNBT()
        l2 = Layout2Brick(nbt=nbt2)
        l2.build(tick_delay=2, notes_integer=make_notes(10), notes_half=make_notes(10))
        l2.clean(nbt2.get_index_safe("minecraft:stone"))
        l2.write_nbt()
        nbt2.write_file("output/debug/debug_layout2_dense.nbt")
        if CAN_VISUALIZE:
            render_data_to_image(l2.blocks, nbt2.nbtfile['palette'], "Layout 2 Dense", "output/debug_images/debug_layout2_dense.png")
            export_topdown_grid(l2.blocks, nbt2.nbtfile['palette'], "Layout 2 Dense Grid", "output/debug_images/debug_layout2_dense_grid.csv", "output/debug_images/debug_layout2_dense_grid.png")
        spawner_nbt.add_structure_block([test_index * 15, 0, 0], "debug_layout2_dense")
        test_index += 1

        # Test 3: Dense Layout2 (Symmetric)
        nbt3 = CustomNBT()
        l3 = Layout2Brick(nbt=nbt3)
        l3.build(tick_delay=2, notes_integer=make_notes(10), notes_half=make_notes(10), is_symmetric=True)
        l3.clean(nbt3.get_index_safe("minecraft:stone"))
        l3.write_nbt()
        nbt3.write_file("output/debug/debug_layout2_dense_sym.nbt")
        if CAN_VISUALIZE:
            render_data_to_image(l3.blocks, nbt3.nbtfile['palette'], "Layout 2 Dense (Symmetric)", "output/debug_images/debug_layout2_dense_sym.png")
            export_topdown_grid(l3.blocks, nbt3.nbtfile['palette'], "Layout 2 Dense Sym Grid", "output/debug_images/debug_layout2_dense_sym_grid.csv", "output/debug_images/debug_layout2_dense_sym_grid.png")
        spawner_nbt.add_structure_block([test_index * 15, 0, 0], "debug_layout2_dense_sym")
        test_index += 1

        # Test 4: Layout2 Flipped
        nbt4 = CustomNBT()
        l4 = Layout2Brick(nbt=nbt4)
        l4.build(tick_delay=2, notes_integer=make_notes(10), notes_half=make_notes(10))
        l4.flip()
        l4.clean(nbt4.get_index_safe("minecraft:stone"))
        l4.write_nbt()
        nbt4.write_file("output/debug/debug_layout2_flipped.nbt")
        if CAN_VISUALIZE:
            render_data_to_image(l4.blocks, nbt4.nbtfile['palette'], "Layout 2 Flipped", "output/debug_images/debug_layout2_flipped.png")
            export_topdown_grid(l4.blocks, nbt4.nbtfile['palette'], "Layout 2 Flipped Grid", "output/debug_images/debug_layout2_flipped_grid.csv", "output/debug_images/debug_layout2_flipped_grid.png")
        spawner_nbt.add_structure_block([test_index * 15, 0, 0], "debug_layout2_flipped")
        test_index += 1

        # Test 5-8: Layout2 Rotations
        for rot in range(1, 4):
            nbt_rot = CustomNBT()
            l_rot = Layout2Brick(nbt=nbt_rot)
            l_rot.build(tick_delay=2, notes_integer=make_notes(10), notes_half=make_notes(10))
            l_rot.rotate(rot, nbt_rot)
            l_rot.clean(nbt_rot.get_index_safe("minecraft:stone"))
            l_rot.write_nbt()
            nbt_rot.write_file(f"output/debug/debug_layout2_rot{rot}.nbt")
            if CAN_VISUALIZE:
                render_data_to_image(l_rot.blocks, nbt_rot.nbtfile['palette'], f"Layout 2 Rotation {rot}", f"output/debug_images/debug_layout2_rot{rot}.png")
                export_topdown_grid(l_rot.blocks, nbt_rot.nbtfile['palette'], f"Layout 2 Rot {rot} Grid", f"output/debug_images/debug_layout2_rot{rot}_grid.csv", f"output/debug_images/debug_layout2_rot{rot}_grid.png")
            spawner_nbt.add_structure_block([test_index * 15, 0, 0], f"debug_layout2_rot{rot}")
            test_index += 1

        # Test 9: Complete Serpentine Assembly
        # Creates a 10-tick sequence to test StructureGenerator's automatic snake routing
        data_seq = {
            'tick': list(range(0, 20, 2)),
            'note entier': [make_notes(random.randint(1, 6)) for _ in range(10)],
            'note demi': [make_notes(random.randint(0, 4)) for _ in range(10)]
        }
        df_seq = pd.DataFrame(data_seq).set_index('tick')

        nbt_seq = CustomNBT()
        gen_seq = StructureGenerator(df_seq, nbt_seq, layout_type="Layout2")
        gen_seq.generate_blocks()

        # We manually clean here with a stone block fallback to ensure tests are stable
        gen_seq.global_data.clean(nbt_seq.get_index_safe("minecraft:stone"))

        gen_seq.global_data.write_nbt(nbt_seq)
        nbt_seq.write_file("output/debug/debug_assembly_serpentine.nbt")
        spawner_nbt.add_structure_block([test_index * 15, 0, 0], "debug_assembly_serpentine")
        test_index += 1

        # Output the master spawner, adding a button and redstone to trigger it
        index_stone = spawner_nbt.get_index_safe("minecraft:stone")
        index_button = spawner_nbt.get_index_safe("minecraft:stone_button", {"face": "floor", "facing": "east"})
        spawner_nbt.add_block([-1, 0, 0], index_stone)
        spawner_nbt.add_block([-1, 1, 0], index_button)
        spawner_nbt.write_file("output/debug/debug_spawner.nbt")

        st.success(f"Successfully generated 9 complex test bricks and 1 assembly sequence in `output/debug/`")
