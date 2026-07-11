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

        st.subheader("Export Configuration")
        from core.config import get_export_dir, update_export_dir
        export_dir_input = st.text_input("Export Directory Path", value=get_export_dir(), help="Ex: C:/Users/Name/AppData/Roaming/.minecraft/saves/MyWorld/generated/minecraft/structures")
        custom_out_name = st.text_input("Output File Name (without .nbt)", value=os.path.splitext(uploaded_file_2.name)[0].lower())

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
            # Update config file
            update_export_dir(export_dir_input)
            export_dir = get_export_dir()

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
                    generator = StructureGenerator(df_prep, layout_type=layout_type, palettes=palettes)
                    generator.generate_blocks()
                    progress_bar.progress(80)

                    status_text.text("Exporting NBT...")
                    out_name = custom_out_name.lower().strip()

                    if export_mode == "Single Monolithic File":
                        out_path = os.path.join(export_dir, f"{out_name}.nbt")
                        # Generator handles CustomNBT logic in export_monolithic now
                        generator.export_monolithic(out_path)
                        st.session_state.generated_nbt_path = out_path
                        st.session_state.generated_nbt_name = f"{out_name}.nbt"
                        st.session_state.generated_nbt_mime = "application/octet-stream"
                        progress_bar.progress(100)
                        status_text.text("Finished!")
                    else:
                        out_dir = os.path.join(export_dir, f"{out_name}_parts")
                        if os.path.exists(out_dir):
                            shutil.rmtree(out_dir)
                        os.makedirs(out_dir, exist_ok=True)
                        generator.export_multipart(out_dir, prefix=out_name)

                        # Zip the directory
                        zip_path = os.path.join(export_dir, f"{out_name}_parts.zip")
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

    from core.config import get_export_dir, update_export_dir
    debug_export_dir_input = st.text_input("Export Directory Path (Debug)", value=get_export_dir(), help="Ex: C:/Users/Name/AppData/Roaming/.minecraft/saves/MyWorld/generated/minecraft/structures")

    if st.button("Generate Test Blocks"):
        from tools.debug_generator import generate_test_blocks

        # Update config file
        update_export_dir(debug_export_dir_input)
        export_dir = get_export_dir()

        st.write("Generating debug lego bricks...")
        try:
            nb_bricks, nb_assemblies = generate_test_blocks(export_dir)
            st.success(f"Successfully generated {nb_bricks} shape test bricks and {nb_assemblies} assembly sequence in `{export_dir}/`")
        except Exception as e:
            import traceback
            st.error(f"An error occurred during debug generation: {e}")
            st.text(traceback.format_exc())
