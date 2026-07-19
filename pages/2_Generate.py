import streamlit as st
import os
import shutil
from core.MusicData import MusicData, prep_data
from core.StructureGenerator import StructureGenerator
from core.config import get_export_dir, update_export_dir

st.header("Generate NBT Structure")

# CANCEL BUTTON LOGIC
col_title, col_cancel = st.columns([4, 1])
if col_cancel.button("Annuler / Cancel", key="cancel_page2"):
    st.warning("Action annulée.")
    st.stop()

uploaded_file_2 = st.file_uploader("Upload NBS file for Generation", type=["nbs"], key="nbs_upload_2")

processor = None
name = ""
temp_path_2 = ""

if uploaded_file_2 is not None:
    if not os.path.exists("temp"):
        os.makedirs("temp")
    temp_path_2 = os.path.join("temp", uploaded_file_2.name)
    with open(temp_path_2, "wb") as f:
        f.write(uploaded_file_2.getbuffer())

    processor = MusicData()
    name = processor.read_file(temp_path_2)
    st.session_state.gen_processor = processor
    st.session_state.gen_name = name
    st.session_state.gen_temp_path = temp_path_2

processor = st.session_state.get('gen_processor', None)
name = st.session_state.get('gen_name', "")
temp_path_2 = st.session_state.get('gen_temp_path', "")

st.subheader("Song Statistics")
if processor and processor.data is not None and not processor.data.empty:
    total_notes = len(processor.data)
    max_tick = processor.data['tick'].max()
    duration_secs = max_tick / processor.get_tempo() if processor.get_tempo() > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Notes", f"{total_notes} 🎵")
    col2.metric("Duration (Ticks)", f"{max_tick} ⏱️")
    col3.metric("Duration (Seconds)", f"{duration_secs:.2f} s 🕒")
else:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Notes", "-")
    col2.metric("Duration (Ticks)", "-")
    col3.metric("Duration (Seconds)", "-")


# Use segmented control for Layout as requested
layout_type = st.segmented_control(
    "Select Structure Layout:",
    ["Layout 1", "Layout 2", "Layout 3"],
    default="Layout 2",
    selection_mode="single",
    disabled=(processor is None)
)

export_mode = st.segmented_control(
    "Generation Mode:",
    ["Single Monolithic File", "Dynamic Multi-Part (Structure Blocks)"],
    default="Single Monolithic File",
    selection_mode="single",
    disabled=(processor is None)
)

# Render force_positive only if Layout 3 is selected
force_positive = False
if layout_type == "Layout 3":
    force_positive = st.checkbox("Force Positive Coordinates (Layout 3)", value=False, disabled=(processor is None))

st.subheader("Export Configuration")
export_dir_input = st.text_input("Export Directory Path", value=get_export_dir(), help="Ex: C:/Users/Name/AppData/Roaming/.minecraft/saves/MyWorld/generated/minecraft/structures")
custom_out_name = st.text_input("Output File Name (without .nbt)", value=name.lower() if name else "structure_output", disabled=(processor is None))

st.subheader("Decoration Palette")
palettes = {}
if st.toggle("Apply Decorations", value=True, disabled=(processor is None)):
    col1, col2, col3 = st.columns(3)

    with col1:
        floor_options = ["stone", "andesite", "cobblestone", "mossy_cobblestone", "oak_planks", "grass_block", "dirt"]
        selected_floor = st.multiselect("Floor Blocks", floor_options, default=["stone"], disabled=(processor is None))
    with col2:
        flower_options = ["poppy", "dandelion", "azure_bluet", "red_tulip", "pink_tulip", "oxeye_daisy", "cornflower", "lily_of_the_valley"]
        selected_flowers = st.multiselect("Flowers / Ground Decor", flower_options, default=["poppy", "dandelion"], disabled=(processor is None))
    with col3:
        ceiling_options = ["lantern", "soul_lantern", "torch", "redstone_lamp", "ochre_froglight"]
        selected_ceiling = st.multiselect("Lighting / Ceiling", ceiling_options, default=["lantern"], disabled=(processor is None))

    palettes = {
        "floor": selected_floor,
        "flowers": selected_flowers,
        "ceiling": selected_ceiling
    }

if st.button("Generate NBT", disabled=(processor is None or layout_type is None or export_mode is None), type="primary"):
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

            # Map simplified segment control names back to expected values
            if layout_type == "Layout 1":
                full_layout = "Layout1 (Complete 6-track Minecart)"
            elif layout_type == "Layout 3":
                full_layout = "Layout3 (Organic)"
            else:
                full_layout = "Layout2 (Compact Serpentine)"

            generator = StructureGenerator(df_prep, layout_type=full_layout, palettes=palettes, force_positive_coords=force_positive)

            progress_callback = None
            if "Layout3" in full_layout:
                st.write("Layout 3 Generation Progress:")
                log_container = st.empty()
                if 'log_lines' not in st.session_state:
                    st.session_state.log_lines = []
                else:
                    st.session_state.log_lines.clear()

                def pc(msg, end="\n"):
                    # Handle terminal carriage return simulation
                    if end == "\r" and len(st.session_state.log_lines) > 0:
                        st.session_state.log_lines[-1] = msg
                    else:
                        st.session_state.log_lines.append(msg)
                    # Keep only the last 15 lines to avoid UI lag
                    if len(st.session_state.log_lines) > 15:
                        st.session_state.log_lines = st.session_state.log_lines[-15:]
                    log_container.code("\n".join(st.session_state.log_lines), language="bash")

                progress_callback = pc

            generator.generate_blocks(progress_callback=progress_callback)
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
