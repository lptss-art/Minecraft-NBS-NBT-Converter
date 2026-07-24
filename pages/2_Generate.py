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

DECO_PRESET_FILE = "decoration_presets.json"

def load_deco_presets():
    import json
    p = {}
    if os.path.exists(DECO_PRESET_FILE):
        try:
            with open(DECO_PRESET_FILE, "r") as f:
                p = json.load(f)
        except Exception:
            pass

    dirty = False
    if "Default" not in p:
        p["Default"] = {
            "redstone_band": {"enabled": False, "blocks": "glowstone:100", "top_prob": 0.0, "top_blocks": ""},
            "num_bands": 2,
            "bands": [
                {"dist": 3, "blocks": "stone:80, andesite:20", "top_prob": 0.0, "top_blocks": ""},
                {"dist": 10, "blocks": "grass_block:100", "top_prob": 0.1, "top_blocks": "poppy:50, dandelion:50"}
            ]
        }
        dirty = True
    if "Forest" not in p:
        p["Forest"] = {
            "redstone_band": {"enabled": True, "blocks": "podzol:100", "top_prob": 0.0, "top_blocks": ""},
            "num_bands": 3,
            "bands": [
                {"dist": 2, "blocks": "moss_block:100", "top_prob": 0.0, "top_blocks": ""},
                {"dist": 5, "blocks": "podzol:50, coarse_dirt:50", "top_prob": 0.05, "top_blocks": "brown_mushroom:50, red_mushroom:50"},
                {"dist": 12, "blocks": "grass_block:100", "top_prob": 0.2, "top_blocks": "oak_sapling:30, fern:70"}
            ]
        }
        dirty = True
    if "Desert" not in p:
        p["Desert"] = {
            "redstone_band": {"enabled": False, "blocks": "glowstone:100", "top_prob": 0.0, "top_blocks": ""},
            "num_bands": 2,
            "bands": [
                {"dist": 4, "blocks": "sandstone:100", "top_prob": 0.0, "top_blocks": ""},
                {"dist": 15, "blocks": "sand:90, red_sand:10", "top_prob": 0.05, "top_blocks": "dead_bush:80, cactus:20"}
            ]
        }
        dirty = True
    if "Nether" not in p:
        p["Nether"] = {
            "redstone_band": {"enabled": True, "blocks": "glowstone:50, shroomlight:50", "top_prob": 0.0, "top_blocks": ""},
            "num_bands": 3,
            "bands": [
                {"dist": 2, "blocks": "blackstone:100", "top_prob": 0.0, "top_blocks": ""},
                {"dist": 6, "blocks": "magma_block:30, netherrack:70", "top_prob": 0.05, "top_blocks": "fire:100"},
                {"dist": 15, "blocks": "netherrack:100", "top_prob": 0.15, "top_blocks": "crimson_fungus:50, warped_fungus:50"}
            ]
        }
        dirty = True
    if "Deep Dark" not in p:
        p["Deep Dark"] = {
            "redstone_band": {"enabled": True, "blocks": "sculk_catalyst:100", "top_prob": 0.0, "top_blocks": ""},
            "num_bands": 2,
            "bands": [
                {"dist": 3, "blocks": "deepslate:80, cobbled_deepslate:20", "top_prob": 0.0, "top_blocks": ""},
                {"dist": 12, "blocks": "sculk:100", "top_prob": 0.2, "top_blocks": "sculk_vein:80, sculk_sensor:20"}
            ]
        }
        dirty = True

    if dirty:
        with open(DECO_PRESET_FILE, "w") as f:
            json.dump(p, f, indent=4)
    return p

def save_deco_presets(p):
    import json
    with open(DECO_PRESET_FILE, "w") as f:
        json.dump(p, f, indent=4)

if st.toggle("Apply Decorations", value=True, disabled=(processor is None)):
    deco_presets = load_deco_presets()

    col_p1, col_p2, col_p3, col_p4 = st.columns([2, 1, 2, 1])
    preset_names = list(deco_presets.keys())
    default_idx = preset_names.index("Default") if "Default" in preset_names else 0
    selected_preset_name = col_p1.selectbox("Load Decoration Preset", preset_names, index=default_idx, label_visibility="collapsed", disabled=(processor is None))

    if col_p2.button("Load", key="load_deco", use_container_width=True, disabled=(processor is None)):
        st.session_state.current_deco_config = deco_presets[selected_preset_name]
        # Clear Streamlit state keys to force them to re-initialize with the preset values
        for key in list(st.session_state.keys()):
            if key.startswith("band_dist_") or key.startswith("band_blocks_") or key.startswith("top_prob_") or key.startswith("top_blocks_") or key.startswith("rs_") or key == "num_bands":
                del st.session_state[key]
        st.rerun()

    if 'current_deco_config' not in st.session_state:
        st.session_state.current_deco_config = deco_presets["Default"]

    new_preset_name = col_p3.text_input("Save as Preset Name", placeholder="MyPreset", label_visibility="collapsed", key="save_deco_name", disabled=(processor is None))
    if col_p4.button("Save", key="save_deco", use_container_width=True, disabled=(processor is None)):
        if new_preset_name.strip():
            # We will populate the config object right before saving below
            st.session_state.pending_deco_save = new_preset_name.strip()
        else:
            st.error("Please enter a name.")

    current_config = st.session_state.current_deco_config

    st.markdown("### Redstone Adjacency Band")
    rs_config = current_config.get("redstone_band", {"enabled": False, "blocks": "glowstone:100", "top_prob": 0.0, "top_blocks": ""})

    rs_enabled = st.toggle("Enable Redstone Adjacency Decor (1-block radius)", value=rs_config.get("enabled", False), key="rs_enabled", disabled=(processor is None))
    if rs_enabled:
        col_rs1, col_rs2 = st.columns(2)
        with col_rs1:
            rs_blocks = st.text_input("Floor Blocks (y=-1)", value=rs_config.get("blocks", "glowstone:100"), key="rs_blocks", disabled=(processor is None))
        with col_rs2:
            st.write("") # spacing

        col_rs3, col_rs4 = st.columns(2)
        with col_rs3:
            rs_top_prob = st.slider("Top Decor Probability", 0.0, 1.0, float(rs_config.get("top_prob", 0.0)), key="rs_top_prob", disabled=(processor is None))
        with col_rs4:
            rs_top_blocks = st.text_input("Top Blocks (y=0)", value=rs_config.get("top_blocks", ""), key="rs_top_blocks", disabled=(processor is None))
    else:
        rs_blocks = rs_config.get("blocks", "glowstone:100")
        rs_top_prob = rs_config.get("top_prob", 0.0)
        rs_top_blocks = rs_config.get("top_blocks", "")

    redstone_band_data = {
        "enabled": rs_enabled,
        "blocks": rs_blocks,
        "top_prob": rs_top_prob,
        "top_blocks": rs_top_blocks
    }

    st.markdown("### Floor Distance Bands")

    num_bands = st.slider("Number of Distance Bands", 1, 20, current_config.get("num_bands", 2), key="num_bands", disabled=(processor is None))

    bands_data = []
    min_dist = 1

    for i in range(num_bands):
        st.markdown(f"**Band {i+1}**")
        col_dist, col_blocks = st.columns(2)

        # Load defaults from config if available, else fallback
        default_dist = current_config["bands"][i]["dist"] if i < len(current_config.get("bands", [])) else min_dist + 5
        default_blocks = current_config["bands"][i]["blocks"] if i < len(current_config.get("bands", [])) else "stone:100"
        default_top_prob = current_config["bands"][i].get("top_prob", 0.0) if i < len(current_config.get("bands", [])) else 0.0
        default_top_blocks = current_config["bands"][i].get("top_blocks", "") if i < len(current_config.get("bands", [])) else ""

        # Ensure default_dist is strictly greater than min_dist to prevent errors
        if default_dist < min_dist:
            default_dist = min_dist

        with col_dist:
            # Fix Streamlit out-of-bounds error by ensuring max_value scales with min_dist
            max_val = max(100, min_dist + 20)
            band_dist = st.slider(f"Max Distance", min_dist, max_val, default_dist, key=f"band_dist_{i}", disabled=(processor is None))
        with col_blocks:
            band_blocks = st.text_input(f"Floor Blocks (y=-1)", value=default_blocks, key=f"band_blocks_{i}", disabled=(processor is None))

        col_top1, col_top2 = st.columns(2)
        with col_top1:
            top_prob = st.slider(f"Top Decor Probability", 0.0, 1.0, float(default_top_prob), key=f"top_prob_{i}", disabled=(processor is None))
        with col_top2:
            top_blocks = st.text_input(f"Top Blocks (y=0)", value=default_top_blocks, key=f"top_blocks_{i}", disabled=(processor is None))

        bands_data.append({
            "dist": band_dist,
            "blocks": band_blocks,
            "top_prob": top_prob,
            "top_blocks": top_blocks
        })

        # The next band must start at least 1 block further
        min_dist = band_dist + 1

    # Update current config based on UI values
    updated_config = {
        "redstone_band": redstone_band_data,
        "num_bands": num_bands,
        "bands": bands_data
    }
    st.session_state.current_deco_config = updated_config

    if st.session_state.get("pending_deco_save"):
        preset_name = st.session_state.pending_deco_save
        deco_presets[preset_name] = updated_config
        save_deco_presets(deco_presets)
        st.success(f"Saved preset {preset_name}")
        st.session_state.pending_deco_save = None

    def parse_blocks(block_str):
        if not block_str.strip():
            return {}
        result = {}
        for item in block_str.split(','):
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

    parsed_bands = []
    for bd in bands_data:
        parsed_bands.append({
            "max_distance": bd["dist"],
            "blocks": parse_blocks(bd["blocks"]),
            "top_decor": {
                "probability": bd["top_prob"],
                "blocks": parse_blocks(bd["top_blocks"])
            }
        })

    palettes = {
        "redstone_band": {
            "enabled": redstone_band_data["enabled"],
            "blocks": parse_blocks(redstone_band_data["blocks"]),
            "top_decor": {
                "probability": redstone_band_data["top_prob"],
                "blocks": parse_blocks(redstone_band_data["top_blocks"])
            }
        },
        "distance_bands": parsed_bands
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
