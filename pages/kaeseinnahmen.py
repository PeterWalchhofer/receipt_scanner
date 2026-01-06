from urllib.parse import quote_plus

import pandas as pd
import streamlit as st
from sqlalchemy import or_

from models.receipt import ReceiptSource
from pages.utils import highlight_url
from repository.receipt_repository import ProductDB, ReceiptDB, SessionLocal

KAESEINNAHMEN_COMPANIES = ["Hofladen", "Kemmts Eina", "Wochenmarkt", "Marktwagen"]

st.title("Käseinnahmen Produkte")

with SessionLocal() as session:
    query = (
        session.query(ProductDB, ReceiptDB)
        .join(ReceiptDB, ProductDB.receipt_id == ReceiptDB.id)
        .filter(
            ReceiptDB.is_credit == True,
            or_(
                ReceiptDB.company_name.in_(KAESEINNAHMEN_COMPANIES),
                ReceiptDB.source == ReceiptSource.RECHNUNGSAPP,
            ),
        )
    )
    all_rows = query.all()
    if not all_rows:
        st.info("No products found.")
        st.stop()
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
aggregated = st.sidebar.toggle("Aggregiert", value=False, key="kaese_aggregated")
companies = [None] + sorted(df["company_name"].dropna().unique().tolist())
company = st.sidebar.selectbox(
    "Company", options=companies, key="kaese_company", disabled=aggregated
)
filtered = df.copy()
unique_urls = filtered["receipt_url"].unique()
if company:
    filtered = filtered[filtered["company_name"] == company]
if aggregated:
    filtered = (
        filtered.groupby(["name", "unit"], as_index=False)
        .agg({"amount": "sum", "price": "sum"})
        .sort_values(by="name")
    )
# dfregate by name, unit, price, and Details, sum amount

# Assign a color to each unique receipt_url

if not aggregated:
    filtered = filtered.style.apply(highlight_url, axis=1)


column_config = {
    "name": "Product Name",
    "amount": st.column_config.NumberColumn("Total Amount", step=0.01),
    "price": st.column_config.ProgressColumn(
        "Price (€)",
        format="euro",
        help="Visualize the price as a progress bar if available",
        min_value=0,
        max_value=df["price"].max(),
    ),
    "unit": "Unit",
    "receipt_number": "Receipt Number",
    "receipt_url": st.column_config.LinkColumn("🔍 Rechnung", display_text="Edit"),
}
st.dataframe(
    filtered,
    use_container_width=True,
    column_config={
        key: val for key, val in column_config.items() if key in filtered.columns
    },
    column_order=[
        col for col in df.columns if col not in ["id", "receipt_id", "is_credit"]
    ],
)
