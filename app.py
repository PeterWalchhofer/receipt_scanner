import streamlit as st
import dotenv

dotenv.load_dotenv()

pg = st.navigation(
    [
        st.Page("pages/upload.py", title="Upload", icon="📃"),
        st.Page("pages/view_receipts.py", title="View Receipts", icon="📚"),
        st.Page("pages/receipt_detail.py", title=" -", icon=""),
    ]
)
st.set_page_config(layout="wide")
pg.run()
