from urllib.parse import quote_plus

import pandas as pd
import streamlit as st

from models.product import BioCategory
from pages.utils import highlight_url
from repository.receipt_repository import ProductDB, ReceiptDB, SessionLocal

st.title("Biokontrolle Produkte")

with SessionLocal() as session:
    query = (
        session.query(ProductDB, ReceiptDB)
        .join(ReceiptDB, ProductDB.receipt_id == ReceiptDB.id)
        .filter(
            ReceiptDB.is_credit == False,  # Only include non-credit receipts
            ProductDB.is_bio == True,  # Only include bio products
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
                "is_bio": prod.is_bio,
                "bio_category": prod.bio_category.value if prod.bio_category else None,
                "company_name": rec.company_name,
                "is_credit": rec.is_credit,
                "date": rec.date,
                "receipt_number": rec.receipt_number,
                "receipt_url": f"/receipt_detail?id={quote_plus(str(rec.id))}",
            }
        )
    df = pd.DataFrame(data)

# Sidebar filters
st.sidebar.header("Filter Biokontrolle")
bio_categories = [None] + [e.value for e in BioCategory]
bio_category = st.sidebar.selectbox("BioCategory", options=bio_categories)
companies = [None] + sorted(df["company_name"].dropna().unique().tolist())
company = st.sidebar.selectbox("Company", options=companies)
filtered = df.copy()
if bio_category:
    filtered = filtered[filtered["bio_category"] == bio_category]
if company:
    filtered = filtered[filtered["company_name"] == company]
styled_filtered = filtered.style.apply(highlight_url, axis=1)
st.dataframe(
    styled_filtered,
    use_container_width=True,
    column_config={
        "name": "Product Name",
        "amount": st.column_config.NumberColumn("Amount", step=0.01),
        "unit": "Unit",
        "bio_category": "BioCategory",
        "company_name": "Company",
        "date": "Date",
        "receipt_number": "Receipt Number",
        "receipt_url": st.column_config.LinkColumn("🔍 Rechnung", display_text="Edit"),
    },
    column_order=[
        col
        for col in filtered.columns
        if col not in ["id", "receipt_id", "is_credit", "is_bio", "price"]
    ],
)
