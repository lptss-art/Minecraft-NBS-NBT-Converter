import streamlit as st
import os
import shutil
import re
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

st.subheader("Decoration Palette")

with st.expander("ℹ️ Comment formater les blocs de décoration ?"):
    st.markdown("""
Le format attendu pour les blocs de décoration permet de configurer 3 choses en même temps : **le nom du bloc**, **ses propriétés** (états de bloc comme l'orientation, s'il est allumé, l'âge, etc.), et **son poids** pour les probabilités d'apparition.

### Format général :
`minecraft:nom_du_bloc[propriete=valeur,autre=valeur]:poids`

### Exemples d'utilisation :

**1. Un bloc simple avec un poids de 80 :**
> `stone:80`
*(Le "minecraft:" est ajouté automatiquement s'il manque, et s'il n'y a pas de crochets, aucune propriété n'est définie)*

**2. Un bloc avec des propriétés (ex: un escalier orienté vers l'Est) :**
> `oak_stairs[facing=east]:50`

**3. Un bloc avec plusieurs propriétés (ex: un feu de camp éteint et face au Nord) :**
> `campfire[lit=false,facing=north]:100`

**4. Un mélange de plusieurs blocs avec et sans propriétés :**
> `stone:50, oak_leaves[distance=7,persistent=true]:30, dirt:20`

**Remarque :** Assure-toi de ne pas mettre d'espaces à l'intérieur des crochets `[...]` autour du `=` pour éviter des soucis avec la génération Minecraft.
    """)

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

    new_defaults = {
        "Default_Village": {
            "num_bands": 3,
            "bands": [
                {"dist": 3, "blocks": "cobblestone:70, mossy_cobblestone:30"},
                {"dist": 6, "blocks": "dirt_path:80, coarse_dirt:20", "top_prob": 0.05, "top_blocks": "lantern[hanging=false]:100"},
                {"dist": 12, "blocks": "grass_block:100", "top_prob": 0.15, "top_blocks": "poppy:30, dandelion:30, cornflower:40"}
            ]
        },
        "Deep_Forest": {
            "redstone_band": {"enabled": True, "blocks": "spruce_log[axis=y]:100", "top_prob": 0.0, "top_blocks": ""},
            "num_bands": 3,
            "bands": [
                {"dist": 3, "blocks": "moss_block:80, rooted_dirt:20", "top_prob": 0.2, "top_blocks": "fern:70, large_fern[half=lower]:30"},
                {"dist": 7, "blocks": "podzol:60, coarse_dirt:40", "top_prob": 0.05, "top_blocks": "campfire[lit=true,facing=north]:50, brown_mushroom:50"},
                {"dist": 14, "blocks": "grass_block:100", "top_prob": 0.1, "top_blocks": "spruce_sapling:30, sweet_berry_bush[age=3]:70"}
            ]
        },
        "Desert_Oasis": {
            "num_bands": 3,
            "bands": [
                {"dist": 3, "blocks": "cut_sandstone:70, chiseled_sandstone:30"},
                {"dist": 8, "blocks": "sand:70, smooth_sandstone:30", "top_prob": 0.05, "top_blocks": "dead_bush:100"},
                {"dist": 15, "blocks": "sand:90, red_sand:10", "top_prob": 0.1, "top_blocks": "cactus[age=5]:30, red_tulip:70"}
            ]
        },
        "Crimson_Fortress": {
            "redstone_band": {"enabled": True, "blocks": "magma_block:100", "top_prob": 0.0, "top_blocks": ""},
            "num_bands": 3,
            "bands": [
                {"dist": 3, "blocks": "polished_blackstone_bricks:70, cracked_polished_blackstone_bricks:30", "top_prob": 0.1, "top_blocks": "soul_lantern[hanging=false]:100"},
                {"dist": 7, "blocks": "crimson_nylium:80, netherrack:20", "top_prob": 0.2, "top_blocks": "crimson_roots:60, crimson_fungus:40"},
                {"dist": 15, "blocks": "netherrack:90, soul_soil:10", "top_prob": 0.05, "top_blocks": "fire[age=0]:100"}
            ]
        },
        "Ancient_City": {
            "redstone_band": {"enabled": True, "blocks": "sculk_catalyst:100", "top_prob": 0.0, "top_blocks": ""},
            "num_bands": 3,
            "bands": [
                {"dist": 4, "blocks": "polished_deepslate:80, deepslate_tiles:20", "top_prob": 0.0, "top_blocks": ""},
                {"dist": 9, "blocks": "sculk:100", "top_prob": 0.3, "top_blocks": "sculk_sensor[sculk_sensor_phase=active]:30, sculk_shrieker[can_summon=false]:10, sculk_vein[up=true]:60"},
                {"dist": 15, "blocks": "deepslate:70, cobbled_deepslate:30", "top_prob": 0.0, "top_blocks": ""}
            ]
        },
        "Amethyst_Geode": {
            "num_bands": 4,
            "bands": [
                {"dist": 2, "blocks": "smooth_basalt:100"},
                {"dist": 5, "blocks": "calcite:100"},
                {"dist": 10, "blocks": "amethyst_block:80, budding_amethyst:20", "top_prob": 0.3, "top_blocks": "amethyst_cluster[facing=up]:40, large_amethyst_bud[facing=up]:30, medium_amethyst_bud[facing=up]:30"},
                {"dist": 14, "blocks": "tuff:100"}
            ]
        },
        "Warped_Magic": {
            "redstone_band": {"enabled": True, "blocks": "pearlescent_froglight[axis=y]:100", "top_prob": 0.0, "top_blocks": ""},
            "num_bands": 3,
            "bands": [
                {"dist": 4, "blocks": "warped_planks:80, stripped_warped_stem[axis=y]:20"},
                {"dist": 9, "blocks": "warped_nylium:100", "top_prob": 0.25, "top_blocks": "warped_roots:50, nether_sprouts:30, warped_fungus:20"},
                {"dist": 15, "blocks": "blackstone:60, obsidian:40"}
            ]
        },
        "Cherry_Grove": {
            "num_bands": 4,
            "bands": [
                {"dist": 3, "blocks": "cherry_planks:70, stripped_cherry_log[axis=y]:30", "top_prob": 0.1, "top_blocks": "pink_candle[candles=3,lit=true]:100"},
                {"dist": 6, "blocks": "dirt_path:100", "top_prob": 0.0, "top_blocks": ""},
                {"dist": 11, "blocks": "moss_block:60, grass_block:40", "top_prob": 0.5, "top_blocks": "pink_petals[flower_amount=4,facing=north]:40, pink_petals[flower_amount=2,facing=south]:40, cherry_sapling:20"},
                {"dist": 18, "blocks": "grass_block:100", "top_prob": 0.1, "top_blocks": "peony[half=lower]:50, lilac[half=lower]:50"}
            ]
        },
        "Lush_Glow": {
            "redstone_band": {"enabled": True, "blocks": "shroomlight:100", "top_prob": 0.0, "top_blocks": ""},
            "num_bands": 4,
            "bands": [
                {"dist": 3, "blocks": "ochre_froglight[axis=y]:20, moss_block:80", "top_prob": 0.0, "top_blocks": ""},
                {"dist": 8, "blocks": "moss_block:100", "top_prob": 0.4, "top_blocks": "flowering_azalea:40, azalea:40, spore_blossom:20"},
                {"dist": 13, "blocks": "rooted_dirt:60, moss_block:40", "top_prob": 0.15, "top_blocks": "big_dripleaf[facing=north,tilt=none]:100"},
                {"dist": 18, "blocks": "tuff:60, stone:40", "top_prob": 0.0, "top_blocks": ""}
            ]
        }
    }

    for key, data in new_defaults.items():
        if key not in p:
            p[key] = data
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
    default_idx = preset_names.index("Default_Village") if "Default_Village" in preset_names else 0
    selected_preset_name = col_p1.selectbox("Load Decoration Preset", preset_names, index=default_idx, label_visibility="collapsed", disabled=(processor is None))

    if col_p2.button("Load", key="load_deco", use_container_width=True, disabled=(processor is None)):
        preset = deco_presets[selected_preset_name]
        st.session_state.current_deco_config = preset

        # Explicitly inject preset values into session_state to force widgets to update
        st.session_state["deco_y_offset"] = preset.get("y_offset", 0)
        st.session_state["num_bands"] = preset.get("num_bands", 2)

        rs_conf = preset.get("redstone_band", {})
        st.session_state["rs_enabled"] = rs_conf.get("enabled", False)
        st.session_state["rs_blocks"] = rs_conf.get("blocks", "glowstone:100")
        st.session_state["rs_top_prob"] = float(rs_conf.get("top_prob", 0.0))
        st.session_state["rs_top_blocks"] = rs_conf.get("top_blocks", "")

        min_dist_track = 1
        for i in range(preset.get("num_bands", 2)):
            band = preset["bands"][i] if i < len(preset.get("bands", [])) else {}
            dist_val = band.get("dist", min_dist_track + 5)
            if dist_val < min_dist_track:
                dist_val = min_dist_track
            st.session_state[f"band_dist_{i}"] = dist_val
            st.session_state[f"band_blocks_{i}"] = band.get("blocks", "stone:100")
            st.session_state[f"top_prob_{i}"] = float(band.get("top_prob", 0.0))
            st.session_state[f"top_blocks_{i}"] = band.get("top_blocks", "")
            min_dist_track = dist_val + 1

        st.rerun()

    if 'current_deco_config' not in st.session_state:
        st.session_state.current_deco_config = deco_presets["Default_Village"]

    new_preset_name = col_p3.text_input("Save as Preset Name", placeholder="MyPreset", label_visibility="collapsed", key="save_deco_name", disabled=(processor is None))
    if col_p4.button("Save", key="save_deco", use_container_width=True, disabled=(processor is None)):
        if new_preset_name.strip():
            # We will populate the config object right before saving below
            st.session_state.pending_deco_save = new_preset_name.strip()
        else:
            st.error("Please enter a name.")

    current_config = st.session_state.current_deco_config

    st.markdown("### General Settings")
    deco_y_offset = st.radio("Y-Offset (Relative to Noteblocks)", options=[0, 1], index=current_config.get("y_offset", 0), horizontal=True, key="deco_y_offset", disabled=(processor is None))

    st.markdown("### Redstone Adjacency Band")
    rs_config = current_config.get("redstone_band", {"enabled": False, "blocks": "glowstone:100", "top_prob": 0.0, "top_blocks": ""})

    rs_enabled = st.toggle("Enable Redstone Adjacency Decor (Strictly 1 block Orthogonal)", value=rs_config.get("enabled", False), key="rs_enabled", disabled=(processor is None))
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
        "y_offset": deco_y_offset,
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

        # Split on commas, EXCEPT if they are inside brackets [...]
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
        "y_offset": deco_y_offset,
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
