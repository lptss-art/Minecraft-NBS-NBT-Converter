import streamlit as st
import os
import shutil
import re
from core.MusicData import MusicData, prep_data
from core.StructureGenerator import StructureGenerator
from core.config import get_export_dir, update_export_dir
from core.deco_presets import load_deco_presets, save_deco_presets

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
    col_l5 = st.columns(1)[0]
    layout_params["l3_time_penalty"] = col_l5.number_input("Time Penalty Coef", value=10.0, step=1.0)

    col_l3, col_l4 = st.columns(2)
    layout_params["l3_speed"] = col_l3.number_input("X Speed (blocks/tick)", value=4, step=1)
    layout_params["l3_prob"] = col_l4.number_input("Redstone Wire Probability", value=0.3, step=0.05)

st.subheader("Export Configuration")
save_log = st.toggle("Save complete generation log to file", value=False, disabled=(processor is None))

export_dir_input = st.text_input("Export Directory Path", value=get_export_dir(), help="Ex: C:/Users/Name/AppData/Roaming/.minecraft/saves/MyWorld/generated/minecraft/structures")

def clean_filename(filename):
    if not filename:
        return ""
    # Lowercase, replace spaces with underscores, and remove any character that isn't a-z, 0-9, -, or _
    cleaned = filename.lower().replace(" ", "_")
    cleaned = re.sub(r'[^a-z0-9\-_]', '', cleaned)
    return cleaned

default_out_name = clean_filename(name) if name else "structure_output"
if not default_out_name:
    default_out_name = "structure_output"

custom_out_name = st.text_input("Output File Name (without .nbt)", value=default_out_name, disabled=(processor is None))

st.subheader("Decoration Settings")

def parse_blocks(block_str):
    if not block_str.strip():
        return {}
    result = {}
    items = re.split(r',\s*(?![^\[]*\])', block_str)
    for item in items:
        parts = item.rsplit(':', 1)
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

def config_to_palette(preset):
    if not preset:
        return {}
    parsed_bands = []
    for bd in preset.get("bands", []):
        parsed_bands.append({
            "max_distance": bd.get("dist", 1),
            "blocks": parse_blocks(bd.get("blocks", "")),
            "top_decor": {
                "probability": bd.get("top_prob", 0.0),
                "blocks": parse_blocks(bd.get("top_blocks", ""))
            }
        })
    rs_data = preset.get("redstone_band", {})
    return {
        "y_offset": preset.get("y_offset", 0),
        "redstone_band": {
            "enabled": rs_data.get("enabled", False),
            "blocks": parse_blocks(rs_data.get("blocks", "")),
            "top_decor": {
                "probability": rs_data.get("top_prob", 0.0),
                "blocks": parse_blocks(rs_data.get("top_blocks", ""))
            }
        },
        "distance_bands": parsed_bands
    }

palettes = {}

if st.toggle("Apply Decorations", value=True, disabled=(processor is None)):
    deco_presets = load_deco_presets()
    preset_names = list(deco_presets.keys())

    deco_mode = st.radio("Decoration Mode", ["Simple", "Advanced"], horizontal=True, disabled=(processor is None))

    if deco_mode == "Simple":
        st.info("In Simple mode, you select one palette. To create or edit palettes, please use the **4. Edit Decoration Palettes** tab.")
        default_idx = preset_names.index("Default_Village") if "Default_Village" in preset_names else 0
        selected_preset = st.selectbox("Select Decoration Palette", preset_names, index=default_idx, disabled=(processor is None))
        palettes = {
            "mode": "simple",
            "palette": config_to_palette(deco_presets[selected_preset])
        }
    else:
        st.info("In Advanced mode, you can select multiple palettes and transition between them along the X axis. The first palette starts at X=0.")

        num_palettes = st.number_input("Number of Palettes", min_value=1, max_value=10, value=2, disabled=(processor is None))

        advanced_palettes = []
        for i in range(int(num_palettes)):
            st.markdown(f"**Palette {i+1}**")
            col_p, col_x, col_w = st.columns(3)
            with col_p:
                p_name = st.selectbox(f"Palette {i+1}", preset_names, key=f"adv_p_{i}", disabled=(processor is None))
            with col_x:
                if i == 0:
                    start_x = 0
                    st.text_input("Start Position (X)", value="0", disabled=True, key=f"adv_x_{i}")
                else:
                    start_x = st.number_input("Start Position (X Coordinate)", value=i*50, key=f"adv_x_{i}", disabled=(processor is None))
            with col_w:
                if i == 0:
                    trans_w = 0
                    st.text_input("Transition Width", value="0", disabled=True, key=f"adv_w_{i}")
                else:
                    trans_w = st.number_input("Transition Width (X Blocks)", min_value=1, value=10, key=f"adv_w_{i}", disabled=(processor is None))

            advanced_palettes.append({
                "start_x": start_x,
                "transition_width": trans_w,
                "palette": config_to_palette(deco_presets[p_name])
            })

        loop_palettes = st.toggle("Loop Palettes", value=False, disabled=(processor is None))
        loop_dist = 0
        loop_trans = 0
        if loop_palettes:
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                loop_dist = st.number_input("Distance before looping (X Blocks)", min_value=1, value=50, disabled=(processor is None))
            with col_l2:
                loop_trans = st.number_input("Loop Transition Width (X Blocks)", min_value=1, value=10, disabled=(processor is None))

        palettes = {
            "mode": "advanced",
            "palettes": advanced_palettes,
            "loop": loop_palettes,
            "loop_distance": loop_dist,
            "loop_transition": loop_trans
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
            full_log = []
            stats = {"failed_notes": 0, "first_failed": None}

            if "Layout3" in full_layout:
                st.write("Layout 3 Generation Progress:")
                stats_container = st.empty()
                log_container = st.empty()
                if 'log_lines' not in st.session_state:
                    st.session_state.log_lines = []
                else:
                    st.session_state.log_lines.clear()

                # We can also track total notes if we parse it from the messages
                ui_stats = {"total": 0, "processed": 0, "success": 0, "fail": 0}

                def pc(msg, end="\n"):
                    # Try to parse total notes from the debug messages
                    if "Note " in msg and "/" in msg:
                        try:
                            parts = msg.split("Note ")[1].split(" ")[0].split("/")
                            if len(parts) == 2:
                                ui_stats["processed"] = int(parts[0])
                                ui_stats["total"] = int(parts[1])
                        except:
                            pass

                    if "Succès pour la note" in msg:
                        ui_stats["success"] += 1
                    elif "Échec critique" in msg:
                        ui_stats["fail"] += 1

                    stats_container.markdown(f"**Notes processed:** {ui_stats['processed']}/{ui_stats['total']} | **Success:** {ui_stats['success']} | **Failed:** {ui_stats['fail']}")

                    # UI Log Handling
                    if end == "\r" and len(st.session_state.log_lines) > 0:
                        st.session_state.log_lines[-1] = msg
                    else:
                        st.session_state.log_lines.append(msg)

                    if len(st.session_state.log_lines) > 15:
                        st.session_state.log_lines = st.session_state.log_lines[-15:]
                    log_container.code("\n".join(st.session_state.log_lines), language="bash")

                    # Full Log Handling & Stats
                    if save_log:
                        if end == "\r" and len(full_log) > 0:
                            full_log[-1] = msg
                        else:
                            full_log.append(msg)

                        if "Échec critique" in msg:
                            stats["failed_notes"] += 1
                            if stats["first_failed"] is None:
                                stats["first_failed"] = msg

                progress_callback = pc

            generator.generate_blocks(progress_callback=progress_callback)
            progress_bar.progress(80)

            status_text.text("Exporting NBT...")
            out_name = custom_out_name.lower().strip()

            if export_mode == "Single Monolithic File":
                out_path = os.path.join(export_dir, f"{out_name}.nbt")
                generator.export_monolithic(out_path)
                st.session_state.generated_nbt_path = out_path
                st.session_state.generated_nbt_name = f"{out_name}.nbt"
                st.session_state.generated_nbt_mime = "application/octet-stream"
            else:
                out_dir = os.path.join(export_dir, f"{out_name}_parts")
                if os.path.exists(out_dir):
                    shutil.rmtree(out_dir)
                os.makedirs(out_dir, exist_ok=True)
                generator.export_multipart(out_dir, prefix=out_name)

                zip_path = os.path.join(export_dir, f"{out_name}_parts.zip")
                shutil.make_archive(zip_path.replace('.zip', ''), 'zip', out_dir)

                st.session_state.generated_nbt_path = zip_path
                st.session_state.generated_nbt_name = f"{out_name}_parts.zip"
                st.session_state.generated_nbt_mime = "application/zip"

            if save_log and "Layout3" in full_layout:
                log_path = os.path.join(export_dir, f"{out_name}_log.txt")
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write("\n".join(full_log))
                    f.write("\n\n--- STATISTICS ---\n")
                    f.write(f"Total Notes Failed: {stats['failed_notes']}\n")
                    if stats['first_failed']:
                        f.write(f"First Failure: {stats['first_failed']}\n")
                    else:
                        f.write("First Failure: None\n")
                st.session_state.generated_log_path = log_path
                st.session_state.generated_log_name = f"{out_name}_log.txt"
            else:
                st.session_state.generated_log_path = None

            progress_bar.progress(100)
            status_text.text("Finished!")

    except Exception as e:
        import traceback
        st.error(f"An error occurred during generation: {e}")
        st.text(traceback.format_exc())

if 'generated_nbt_path' in st.session_state and os.path.exists(st.session_state.generated_nbt_path):
    st.success("Generation completed successfully!")

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        with open(st.session_state.generated_nbt_path, "rb") as f:
            st.download_button(
                label=f"Download {st.session_state.generated_nbt_name}",
                data=f,
                file_name=st.session_state.generated_nbt_name,
                mime=st.session_state.generated_nbt_mime
            )

    if st.session_state.get('generated_log_path') and os.path.exists(st.session_state.generated_log_path):
        with col_dl2:
            with open(st.session_state.generated_log_path, "r", encoding="utf-8") as f:
                st.download_button(
                    label=f"Download Generation Log",
                    data=f.read(),
                    file_name=st.session_state.generated_log_name,
                    mime="text/plain"
                )
