import dotenv
import streamlit as st

dotenv.load_dotenv()

pg = st.navigation(
    [
        st.Page("pages/upload.py", title="Upload", icon="📃"),
        st.Page("pages/view_receipts.py", title="View Receipts", icon="📚"),
        st.Page("pages/kalkül.py", title="Import Kalkül ZIP", icon="📦"),
        st.Page("pages/statistik.py", title="Statistics", icon="📊"),
        st.Page("pages/biokontrolle.py", title="Biokontrolle", icon="🌱"),
        st.Page("pages/kaeseinnahmen.py", title="Käseinnahmen", icon="🧀"),
        st.Page("pages/receipt_detail.py", title=" -", icon="⚪"),
    ]
)
st.set_page_config(layout="wide")
pg.run()
