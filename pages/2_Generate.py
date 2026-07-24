import streamlit as st
import os
import shutil
from core.MusicData import MusicData, prep_data
from core.StructureGenerator import StructureGenerator
from core.config import get_export_dir, update_export_dir

st.header("Generate NBT Structure")

st.markdown('''
<style>
/* Make all cancel buttons red */
div[class*="st-key-btn_cancel"] button {
    background-color: #ff4b4b !important;
    color: white !important;
}

/* Make all generation buttons green */
div[class*="st-key-btn_generate"] button {
    background-color: #00cc66 !important;
    color: white !important;
}
</style>
''', unsafe_allow_html=True)


col_up, col_stats = st.columns(2)
with col_up:
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

with col_stats:
    if processor and processor.data is not None and not processor.data.empty:
        total_notes = len(processor.data)
        max_tick = processor.data['tick'].max()
        duration_secs = max_tick / processor.get_tempo() if processor.get_tempo() > 0 else 0
        s_col1, s_col2 = st.columns(2)
        s_col1.metric("Total Notes", f"{total_notes} 🎵")
        s_col1.metric("Duration (Ticks)", f"{max_tick} ⏱️")
        s_col2.metric("Duration (Seconds)", f"{duration_secs:.2f} s 🕒")
    else:
        st.write("Upload a file to see statistics.")





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
    force_positive = st.toggle("Force Positive Coordinates (Z)", value=False, disabled=(processor is None))


st.subheader("Layout Personalization")
layout_params = {}
if layout_type == "Layout 1":
    col_l1, col_l2, col_l3 = st.columns(3)
    layout_params["l1_glass"] = col_l1.text_input("Support Block (Redstone, etc.)", value="minecraft:glass")
    layout_params["l1_base"] = col_l2.text_input("Central Base Material", value="minecraft:polished_blackstone_bricks")
    layout_params["l1_empty"] = col_l3.text_input("Empty Note Block", value="minecraft:redstone_lamp")
elif layout_type == "Layout 2":
    col_l1, col_l2 = st.columns(2)
    layout_params["l2_base"] = col_l1.text_input("Support Block (Redstone, etc.)", value="minecraft:oak_planks")
    layout_params["l2_empty"] = col_l2.text_input("Empty Note Block", value="minecraft:redstone_lamp")
elif layout_type == "Layout 3":
    col_l1, col_l2 = st.columns(2)
    layout_params["l3_base"] = col_l1.text_input("Support Block (Redstone, etc.)", value="minecraft:oak_planks")
    layout_params["l3_attempts"] = col_l2.number_input("Max Attempts", value=1000, step=100)

    col_l3, col_l4 = st.columns(2)
    layout_params["l3_speed"] = col_l3.number_input("X Speed (blocks/tick)", value=4, step=1)
    layout_params["l3_prob"] = col_l4.number_input("Redstone Wire Probability", value=0.3, step=0.05)

st.subheader("Export Configuration")
export_dir_input = st.text_input("Export Directory Path", value=get_export_dir(), help="Ex: C:/Users/Name/AppData/Roaming/.minecraft/saves/MyWorld/generated/minecraft/structures")
custom_out_name = st.text_input("Output File Name (without .nbt)", value=name.lower() if name else "structure_output", disabled=(processor is None))

st.subheader("Decoration Palette")
palettes = {}
if st.toggle("Apply Decorations", value=True, disabled=(processor is None)):
    st.markdown("### Floor Distance Bands")

    col_band1, col_band2 = st.columns(2)

    with col_band1:
        band1_dist = st.slider("Band 1 Max Distance", 1, 20, 3, disabled=(processor is None))
        band1_blocks = st.text_input("Band 1 Blocks (e.g., stone:80, andesite:20)", value="stone:100", disabled=(processor is None))

    with col_band2:
        band2_dist = st.slider("Band 2 Max Distance", 1, 50, 10, disabled=(processor is None))
        band2_blocks = st.text_input("Band 2 Blocks (e.g., grass_block:80, dirt:20)", value="grass_block:100", disabled=(processor is None))

    st.markdown("### Top Decoration (y=0)")

    col_top1, col_top2 = st.columns(2)
    with col_top1:
        top_prob = st.slider("Top Decoration Probability", 0.0, 1.0, 0.1, disabled=(processor is None))
    with col_top2:
        top_blocks = st.text_input("Top Blocks (e.g., poppy:50, dandelion:50)", value="poppy:50, dandelion:50", disabled=(processor is None))

    def parse_blocks(block_str):
        if not block_str.strip():
            return {}
        result = {}
        for item in block_str.split(','):
            parts = item.split(':')
            if len(parts) == 2:
                name = parts[0].strip()
                try:
                    weight = float(parts[1].strip())
                    if not name.startswith("minecraft:"):
                        name = f"minecraft:{name}"
                    result[name] = weight
                except ValueError:
                    pass
        return result

    palettes = {
        "distance_bands": [
            {"max_distance": band1_dist, "blocks": parse_blocks(band1_blocks)},
            {"max_distance": band2_dist, "blocks": parse_blocks(band2_blocks)}
        ],
        "top_decor": {
            "probability": top_prob,
            "blocks": parse_blocks(top_blocks)
        }
    }





col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    generate_pressed = st.button("Generate NBT", disabled=(processor is None or layout_type is None or export_mode is None), type="primary", key="btn_generate")
with col_btn2:
    if st.button("Cancel", type="primary", key="btn_cancel"):
        st.rerun()

if generate_pressed:

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

            generator = StructureGenerator(df_prep, layout_type=full_layout, palettes=palettes, force_positive_coords=force_positive, layout_params=layout_params)

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
