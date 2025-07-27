import itertools
import random
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st
from matplotlib import cm

from pages.utils import highlight_url
from repository.receipt_repository import ProductDB, ReceiptDB, SessionLocal

KAESEINNAHMEN_COMPANIES = ["Hofladen", "Kemmts Eina", "Wochenmarkt"]

st.title("Käseinnahmen Produkte")

with SessionLocal() as session:
    query = (
        session.query(ProductDB, ReceiptDB)
        .join(ReceiptDB, ProductDB.receipt_id == ReceiptDB.id)
        .filter(
            ReceiptDB.is_credit == True,
            ReceiptDB.company_name.in_(KAESEINNAHMEN_COMPANIES),
        )
    )
    all_rows = query.all()
    data = []
    for prod, rec in all_rows:
        data.append(
            {
                "id": prod.id,
                "receipt_id": prod.receipt_id,
                "name": prod.name,
                "amount": prod.amount,
                "unit": prod.unit.value if hasattr(prod.unit, "value") else prod.unit,
                "price": prod.price,
                "company_name": rec.company_name,
                "is_credit": rec.is_credit,
                "date": rec.date,
                "receipt_number": rec.receipt_number,
                "receipt_url": f"/receipt_detail?id={quote_plus(str(rec.id))}",
            }
        )
    df = pd.DataFrame(data)

# Filter: is_credit=True, company in KAESEINNAHMEN_COMPANIES
# Sidebar filter
st.sidebar.header("Filter Käseinnahmen")
companies = [None] + sorted(df["company_name"].dropna().unique().tolist())
company = st.sidebar.selectbox("Company", options=companies, key="kaese_company")
filtered = df.copy()
if company:
    filtered = filtered[filtered["company_name"] == company]
# dfregate by name, unit, price, and Details, sum amount

# Assign a color to each unique receipt_url
unique_urls = df["receipt_url"].unique()




styled_df = df.style.apply(highlight_url, axis=1)

st.dataframe(
    styled_df,
    use_container_width=True,
    column_config={
        "name": "Product Name",
        "amount": st.column_config.NumberColumn("Total Amount", step=0.01),
        "price": st.column_config.ProgressColumn(
            "Price (€)",
            format="euro",
            help="Visualize the price as a progress bar if available",
        ),
        "unit": "Unit",
        "receipt_number": "Receipt Number",
        "receipt_url": st.column_config.LinkColumn("🔍 Rechnung", display_text="Edit"),
    },
    column_order=[
        col for col in df.columns if col not in ["id", "receipt_id", "is_credit"]
    ],
)
