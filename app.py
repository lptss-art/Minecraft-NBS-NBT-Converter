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

tab1, tab2 = st.tabs(["1. Pre-process NBS (Instruments & Tempo)", "2. Generate NBT Structure"])

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

        if 'instrument_matrix' not in st.session_state:
            df = pd.DataFrame(False, index=octaves, columns=instruments)
            st.session_state.instrument_matrix = df

        edited_df = st.data_editor(st.session_state.instrument_matrix)

        if st.button("Save & Process"):
            processor.file_name = output_name
            modifier_matrix = edited_df.to_numpy()
            processor.modify_instrument_data(modifier_matrix)

            if adjust_tempo:
                processor.update_tempo(selected_tempo_idx)

            out_file = processor.write_nbs()
            if out_file:
                with open(out_file, "rb") as f:
                    st.download_button(
                        label="Download Processed NBS",
                        data=f,
                        file_name=f"{output_name}.nbs",
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
                    generator = StructureGenerator(df_prep, nbt_template, layout_type=layout_type)
                    generator.generate_blocks()
                    progress_bar.progress(80)

                    status_text.text("Exporting NBT...")
                    out_name = os.path.splitext(uploaded_file_2.name)[0]

                    if not os.path.exists("output"):
                        os.makedirs("output")

                    if export_mode == "Single Monolithic File":
                        out_path = f"output/{out_name}_complete.nbt"
                        generator.export_monolithic(out_path)
                        progress_bar.progress(100)
                        status_text.text("Finished!")

                        with open(out_path, "rb") as f:
                            st.download_button(
                                label="Download NBT Structure",
                                data=f,
                                file_name=f"{out_name}_complete.nbt",
                                mime="application/octet-stream"
                            )
                    else:
                        out_dir = f"output/{out_name}_parts"
                        if os.path.exists(out_dir):
                            shutil.rmtree(out_dir)
                        os.makedirs(out_dir, exist_ok=True)
                        generator.export_multipart(out_dir)

                        # Zip the directory
                        zip_path = f"output/{out_name}_parts.zip"
                        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', out_dir)

                        progress_bar.progress(100)
                        status_text.text("Finished!")

                        with open(zip_path, "rb") as f:
                            st.download_button(
                                label="Download NBT Parts (ZIP)",
                                data=f,
                                file_name=f"{out_name}_parts.zip",
                                mime="application/zip"
                            )

                    st.success("Generation completed successfully!")
            except Exception as e:
                import traceback
                st.error(f"An error occurred during generation: {e}")
                st.text(traceback.format_exc())
