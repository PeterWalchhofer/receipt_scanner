import streamlit as st

pg = st.navigation(
    [
        st.Page("pages/upload.py", title="Upload", icon="📃"),
        st.Page("pages/view_receipts.py", title="View Receipts", icon="📚"),
    ]
)
st.set_page_config(layout="wide")
pg.run()
