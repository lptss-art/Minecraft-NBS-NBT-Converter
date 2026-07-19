import streamlit as st

st.set_page_config(page_title="NoteBlock Studio to NBT Generator", layout="wide", page_icon="🎵")

pg = st.navigation([
    st.Page("pages/1_Preprocess.py", title="1. Pre-process NBS", icon="🎵"),
    st.Page("pages/2_Generate.py", title="2. Generate NBT Structure", icon="🧱"),
    st.Page("pages/3_Debug.py", title="3. Debug & Test Generation", icon="🐛")
])
pg.run()
