import dotenv
import streamlit as st

dotenv.load_dotenv()

pages = {
    "Main": [
        st.Page("pages/upload.py", title="Upload", icon="📃"),
        st.Page("pages/view_receipts.py", title="View Receipts", icon="📚"),
        st.Page("pages/kalkül.py", title="Import Kalkül ZIP", icon="📦"),
        st.Page("pages/statistik.py", title="Statistics", icon="📊"),
        st.Page("pages/biokontrolle.py", title="Biokontrolle", icon="🌱"),
        st.Page("pages/kaeseinnahmen.py", title="Käseinnahmen", icon="🧀"),
        st.Page("pages/receipt_detail.py", title=" -", icon="⚪"),

    ],
    "🗜 Unify Product Names": [
        st.Page("pages/sortiment.py", title="Sortiment Management", icon="📟"),
        st.Page("pages/product_reference.py", title="Product Reference Tool", icon="🔗"),
    ],
}

pg = st.navigation(pages)
st.set_page_config(layout="wide")
pg.run()
