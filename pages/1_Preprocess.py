import streamlit as st
import os
import pandas as pd
import json
from core.MusicData import MusicData

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

    st.session_state.current_processor = processor
    st.session_state.current_name = name

# Always show the rest of the page UI, disabled or default if no file
processor = st.session_state.get('current_processor', None)
name = st.session_state.get('current_name', "")

st.subheader("File Parameters")
output_name = st.text_input("Output File Name", value=f"{name}_updated" if name else "updated_song", disabled=(processor is None))

if processor:
    tempo = processor.get_tempo()
    st.write(f"**Input Tempo:** {tempo:.2f} tps")

    adjust_tempo = st.checkbox("Adjust Tempo", value=False)
    tempos = processor.get_tempos()
    selected_tempo_idx = st.selectbox("Choose tempo:", range(len(tempos)), format_func=lambda i: tempos[i], index=1 if len(tempos) > 1 else 0)
else:
    st.write("**Input Tempo:** N/A")
    adjust_tempo = st.checkbox("Adjust Tempo", value=False, disabled=True)
    st.selectbox("Choose tempo:", ["N/A"], disabled=True)

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

st.subheader("Instruments by Octave")

instruments = ['didgeridoo', 'bass', 'guitar', 'banjo', 'pling', 'iron_xylophone',
               'bit', 'harp', 'cow_bell', 'flute', 'chime', 'xylophone', 'bell']
octaves = [-3, -2, -1, 0, 1, 2, 3, 4]

instrument_values = {'didgeridoo': -2, 'bass': -2, 'guitar': -1, 'banjo': 0, 'pling': 0, 'iron_xylophone': 0,
                    'bit': 0, 'harp': 0, 'cow_bell': 1, 'flute': 1, 'chime': 2, 'xylophone': 2, 'bell': 2}

PRESET_FILE = "instrument_presets.json"

def load_presets():
    p = {}
    if os.path.exists(PRESET_FILE):
        try:
            with open(PRESET_FILE, "r") as f:
                p = json.load(f)
        except Exception:
            pass

    # Ensure default presets exist
    dirty = False
    if "vierge" not in p:
        p["vierge"] = { f"{o}_{i}": False for o in octaves for i in instruments }
        dirty = True

    if "default" not in p:
        p["default"] = { f"{o}_{i}": False for o in octaves for i in instruments }
        # Default asks for bass, harp, bell in their two native notes
        # Bass (-2, -1), Harp (0, 1), Bell (2, 3)
        for o in [-2, -1]:
            p["default"][f"{o}_bass"] = True
        for o in [0, 1]:
            p["default"][f"{o}_harp"] = True
        for o in [2, 3]:
            p["default"][f"{o}_bell"] = True
        dirty = True

    if dirty:
        with open(PRESET_FILE, "w") as f:
            json.dump(p, f, indent=4)

    return p

def save_presets(presets):
    with open(PRESET_FILE, "w") as f:
        json.dump(presets, f, indent=4)

presets = load_presets()

# Initialize session state for matrix if needed, load from default
if 'instrument_matrix' not in st.session_state:
    st.session_state.instrument_matrix = presets["default"].copy()

col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
preset_names = list(presets.keys())
# Set 'default' as the default index if it exists
default_idx = preset_names.index("default") if "default" in preset_names else 0
selected_preset_name = col_p1.selectbox("Load Preset", preset_names, index=default_idx)

if col_p2.button("Load", use_container_width=True):
    loaded_matrix = presets[selected_preset_name]
    for key in st.session_state.instrument_matrix:
        if key in loaded_matrix:
            st.session_state.instrument_matrix[key] = loaded_matrix[key]
    st.success(f"Loaded preset {selected_preset_name}")

new_preset_name = col_p3.text_input("Save as Preset Name", placeholder="MyPreset")
if col_p3.button("Save", use_container_width=True):
    if new_preset_name.strip():
        presets[new_preset_name.strip()] = st.session_state.instrument_matrix
        save_presets(presets)
        st.success(f"Saved preset {new_preset_name.strip()}")
    else:
        st.error("Please enter a name.")

# Custom CSS for the instrument grid toggles to hide text and show pure color
st.markdown("""
<style>
/* Hide text on all grid buttons */
div[class*="st-key-btn_grid_"] button p {
    color: transparent !important;
}
div[class*="st-key-btn_grid_"] button {
    border: none;
    height: 2.5rem;
}

/* Gray - Below Range */
div[class*="st-key-btn_grid_gray_inactive_"] button { background-color: rgba(160, 160, 160, 0.3) !important; }
div[class*="st-key-btn_grid_gray_active_"] button   { background-color: rgba(100, 100, 100, 1) !important; }

/* Blue - Native Range */
div[class*="st-key-btn_grid_blue_inactive_"] button { background-color: rgba(135, 206, 235, 0.3) !important; } /* Sky Blue faded */
div[class*="st-key-btn_grid_blue_active_"] button   { background-color: rgba(30, 144, 255, 1) !important; } /* Dodger Blue bright */

/* Yellow - Above Range */
div[class*="st-key-btn_grid_yellow_inactive_"] button { background-color: rgba(255, 255, 153, 0.3) !important; }
div[class*="st-key-btn_grid_yellow_active_"] button   { background-color: rgba(255, 215, 0, 1) !important; } /* Gold */
</style>
""", unsafe_allow_html=True)


st.write("*Color Legend: 🟦 Blue = Native Minecraft Octave Range (2 octaves), ⬜ Gray = Below Range, 🟨 Yellow = Above Range. Active cells are vivid, inactive are faded. Click to toggle.*")

def toggle_instrument(o, i):
    key = f"{o}_{i}"
    st.session_state.instrument_matrix[key] = not st.session_state.instrument_matrix[key]

# Render instrument grid
# Header row
header_cols = st.columns([1.5] + [1]*len(instruments))
with header_cols[0]:
    st.write("**Octave**")
for idx, i in enumerate(instruments):
    with header_cols[idx+1]:
        st.write(f"**{i[:4]}**")

# Grid rows
for o in octaves:
    row_cols = st.columns([1.5] + [1]*len(instruments))
    with row_cols[0]:
        # Rename -3 to 4 as F#0 to F#7
        octave_label = f"F♯{o + 3}"
        st.write(f"**{octave_label}**")

    for idx, i in enumerate(instruments):
        val = instrument_values[i]
        key = f"{o}_{i}"
        is_active = st.session_state.instrument_matrix.get(key, False)

        if o < val:
            base_color = "gray"
        elif o == val or o == val + 1:
            base_color = "blue"
        else:
            base_color = "yellow"

        active_state = "active" if is_active else "inactive"
        css_key = f"btn_grid_{base_color}_{active_state}_{key}"

        with row_cols[idx+1]:
            st.button("X", key=css_key, on_click=toggle_instrument, args=(o, i), use_container_width=True)


col_act1, col_act2 = st.columns([1, 1])
if col_act2.button("Annuler / Cancel", key="cancel_page1_bottom"):
    st.warning("Action annulée.")
    st.stop()

if col_act1.button("Save & Process", disabled=(processor is None), type="primary"):
    import numpy as np

    # Convert session state dict back to numpy matrix (octaves x instruments)
    modifier_matrix = np.zeros((len(octaves), len(instruments)), dtype=bool)
    for row_idx, o in enumerate(octaves):
        for col_idx, i in enumerate(instruments):
             modifier_matrix[row_idx, col_idx] = st.session_state.instrument_matrix.get(f"{o}_{i}", False)

    processor.file_name = output_name
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
