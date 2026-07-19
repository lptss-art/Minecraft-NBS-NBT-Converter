import streamlit as st
from core.config import get_export_dir, update_export_dir

st.header("Debug / Test Generation")

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



st.write("Generate complex note block structures (Lego bricks) to test layout limits and transformations directly in Minecraft.")

debug_export_dir_input = st.text_input("Export Directory Path (Debug)", value=get_export_dir(), help="Ex: C:/Users/Name/AppData/Roaming/.minecraft/saves/MyWorld/generated/minecraft/structures")





col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    test_pressed = st.button("Generate Test Blocks", type="primary", key="btn_generate")
with col_btn2:
    if st.button("Cancel", type="primary", key="btn_cancel"):
        st.rerun()

if test_pressed:

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
