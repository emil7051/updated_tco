import streamlit as st

st.markdown("<h1>Test HTML</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: red;'>This text should be red</p>", unsafe_allow_html=True)

# Test simple div
st.markdown("""
<div style="background-color: lightblue; padding: 10px;">
    This should have a light blue background
</div>
""", unsafe_allow_html=True)
