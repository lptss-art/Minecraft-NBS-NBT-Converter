import streamlit as st
import time

st.write("Start")

col1, col2 = st.columns(2)

if col1.button("Run Long Task", type="primary"):
    st.session_state.is_running = True

if "is_running" in st.session_state and st.session_state.is_running:
    if col2.button("Cancel", type="primary"):
        st.session_state.is_running = False
        st.rerun()

    placeholder = st.empty()
    for i in range(10):
        if "is_running" not in st.session_state or not st.session_state.is_running:
            break
        time.sleep(1)
        placeholder.write(f"Step {i}")
    st.session_state.is_running = False
    st.success("Done!")
