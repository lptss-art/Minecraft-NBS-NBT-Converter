import streamlit as st
from core.config import get_export_dir, update_export_dir

st.header("Debug / Test Generation")

# CANCEL BUTTON LOGIC
col_title, col_cancel = st.columns([4, 1])
if col_cancel.button("Annuler / Cancel", key="cancel_page3"):
    st.warning("Action annulée.")
    st.stop()

st.write("Generate complex note block structures (Lego bricks) to test layout limits and transformations directly in Minecraft.")

debug_export_dir_input = st.text_input("Export Directory Path (Debug)", value=get_export_dir(), help="Ex: C:/Users/Name/AppData/Roaming/.minecraft/saves/MyWorld/generated/minecraft/structures")

if st.button("Generate Test Blocks", type="primary"):
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
