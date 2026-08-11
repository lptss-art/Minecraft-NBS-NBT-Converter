import streamlit as st
import os
import re
from core.deco_presets import load_deco_presets, save_deco_presets

st.header("Edit Decoration Palettes")

st.markdown("""
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
""", unsafe_allow_html=True)

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

deco_presets = load_deco_presets()

col_p1, col_p2, col_p3, col_p4 = st.columns([2, 1, 2, 1])
preset_names = list(deco_presets.keys())
default_idx = preset_names.index("Default_Village") if "Default_Village" in preset_names else 0
selected_preset_name = col_p1.selectbox("Load Decoration Preset", preset_names, index=default_idx, label_visibility="collapsed")

if col_p2.button("Load", key="load_deco", use_container_width=True):
    preset = deco_presets[selected_preset_name]
    st.session_state.current_deco_config_edit = preset

    # Explicitly inject preset values into session_state to force widgets to update
    st.session_state["deco_y_offset_edit"] = preset.get("y_offset", 0)
    st.session_state["num_bands_edit"] = preset.get("num_bands", 2)

    rs_conf = preset.get("redstone_band", {})
    st.session_state["rs_enabled_edit"] = rs_conf.get("enabled", False)
    st.session_state["rs_blocks_edit"] = rs_conf.get("blocks", "glowstone:100")
    st.session_state["rs_top_prob_edit"] = float(rs_conf.get("top_prob", 0.0))
    st.session_state["rs_top_blocks_edit"] = rs_conf.get("top_blocks", "")

    # For width, we need to convert cumulative dist back to width
    prev_dist = 0
    for i in range(preset.get("num_bands", 2)):
        band = preset["bands"][i] if i < len(preset.get("bands", [])) else {}
        dist_val = band.get("dist", prev_dist + 5)
        width = dist_val - prev_dist
        if width < 1:
            width = 1
        st.session_state[f"band_width_edit_{i}"] = width
        st.session_state[f"band_blocks_edit_{i}"] = band.get("blocks", "stone:100")
        st.session_state[f"top_prob_edit_{i}"] = float(band.get("top_prob", 0.0))
        st.session_state[f"top_blocks_edit_{i}"] = band.get("top_blocks", "")
        prev_dist = prev_dist + width

    st.rerun()

if 'current_deco_config_edit' not in st.session_state:
    st.session_state.current_deco_config_edit = deco_presets["Default_Village"]

new_preset_name = col_p3.text_input("Save as Preset Name", placeholder="MyPreset", label_visibility="collapsed", key="save_deco_name")

current_config = st.session_state.current_deco_config_edit

st.markdown("### General Settings")
deco_y_offset = st.radio("Y-Offset (Relative to Noteblocks)", options=[0, 1], index=current_config.get("y_offset", 0), horizontal=True, key="deco_y_offset_edit")

st.markdown("### Redstone Adjacency Band")
rs_config = current_config.get("redstone_band", {"enabled": False, "blocks": "glowstone:100", "top_prob": 0.0, "top_blocks": ""})

rs_enabled = st.toggle("Enable Redstone Adjacency Decor (Strictly 1 block Orthogonal)", value=rs_config.get("enabled", False), key="rs_enabled_edit")
if rs_enabled:
    col_rs1, col_rs2 = st.columns(2)
    with col_rs1:
        rs_blocks = st.text_input("Floor Blocks (y=-1)", value=rs_config.get("blocks", "glowstone:100"), key="rs_blocks_edit")
    with col_rs2:
        st.write("") # spacing

    col_rs3, col_rs4 = st.columns(2)
    with col_rs3:
        rs_top_prob = st.slider("Top Decor Probability", 0.0, 1.0, float(rs_config.get("top_prob", 0.0)), key="rs_top_prob_edit")
    with col_rs4:
        rs_top_blocks = st.text_input("Top Blocks (y=0)", value=rs_config.get("top_blocks", ""), key="rs_top_blocks_edit")
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

num_bands = st.slider("Number of Distance Bands", 1, 20, current_config.get("num_bands", 2), key="num_bands_edit")

bands_data = []

# Pre-calculate widths from current_config for defaults
default_widths = []
prev_dist = 0
for b in current_config.get("bands", []):
    w = b.get("dist", prev_dist + 5) - prev_dist
    if w < 1: w = 1
    default_widths.append(w)
    prev_dist = prev_dist + w

current_dist = 0
for i in range(num_bands):
    st.markdown(f"**Band {i+1}**")
    col_dist, col_blocks = st.columns(2)

    default_width = default_widths[i] if i < len(default_widths) else 5
    default_blocks = current_config["bands"][i]["blocks"] if i < len(current_config.get("bands", [])) else "stone:100"
    default_top_prob = current_config["bands"][i].get("top_prob", 0.0) if i < len(current_config.get("bands", [])) else 0.0
    default_top_blocks = current_config["bands"][i].get("top_blocks", "") if i < len(current_config.get("bands", [])) else ""

    with col_dist:
        band_width = st.slider(f"Band Width", 1, 20, default_width, key=f"band_width_edit_{i}")
    with col_blocks:
        band_blocks = st.text_input(f"Floor Blocks (y=-1)", value=default_blocks, key=f"band_blocks_edit_{i}")

    col_top1, col_top2 = st.columns(2)
    with col_top1:
        top_prob = st.slider(f"Top Decor Probability", 0.0, 1.0, float(default_top_prob), key=f"top_prob_edit_{i}")
    with col_top2:
        top_blocks = st.text_input(f"Top Blocks (y=0)", value=default_top_blocks, key=f"top_blocks_edit_{i}")

    current_dist += band_width
    bands_data.append({
        "dist": current_dist,
        "blocks": band_blocks,
        "top_prob": top_prob,
        "top_blocks": top_blocks
    })

updated_config = {
    "y_offset": deco_y_offset,
    "redstone_band": redstone_band_data,
    "num_bands": num_bands,
    "bands": bands_data
}
st.session_state.current_deco_config_edit = updated_config

if col_p4.button("Save", key="save_deco", use_container_width=True):
    if new_preset_name.strip():
        preset_name = new_preset_name.strip()
        deco_presets[preset_name] = updated_config
        save_deco_presets(deco_presets)
        st.success(f"Saved preset {preset_name}")
    else:
        st.error("Please enter a name.")
