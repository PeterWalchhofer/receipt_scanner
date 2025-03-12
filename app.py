import streamlit as st


pg = st.navigation([
    st.Page("pages/upload.py", title="Upload"),
    st.Page("pages/view_receipts.py", title="View Receipts"),
]
)
pg.run()