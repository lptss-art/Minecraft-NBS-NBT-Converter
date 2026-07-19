import streamlit as st
import time

st.write("Start")

if st.button("Run Long Task"):
    with st.spinner("Running..."):
        for i in range(10):
            time.sleep(1)
            st.write(f"Step {i}")
    st.success("Done!")

if st.button("Cancel"):
    st.warning("Cancelled")
    # No st.stop() here

st.write("End of script. This should always render.")
