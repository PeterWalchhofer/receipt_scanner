from urllib.parse import quote_plus

import pandas as pd
import streamlit as st
from sqlalchemy import or_

from models.receipt import ReceiptSource
from pages.utils import highlight_url
from repository.receipt_repository import ProductDB, ReceiptDB, SessionLocal, SortimentDB

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
                "product_class_id": prod.product_class_reference,
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

# ==========================================
# PRODUCT CLASS AGGREGATION TABLE (NEW)
# ==========================================
st.subheader("📊 By Product Class")
classified_products = filtered[filtered["product_class_id"].notna()].copy()

if not classified_products.empty:
    # Get sortiment names
    product_class_ids = classified_products["product_class_id"].unique()
    with SessionLocal() as session:
        sortiments = session.query(SortimentDB).filter(
            SortimentDB.id.in_(product_class_ids)
        ).all()
        sortiment_map = {s.id: s.name for s in sortiments}
    
    classified_products["product_class"] = classified_products["product_class_id"].map(sortiment_map)
    
    # Aggregate by product class
    class_agg = (
        classified_products.groupby("product_class", as_index=False)
        .agg({
            "amount": "sum",
            "price": "sum",
            "id": "count",
        })
        .sort_values(by="amount", ascending=False)
    )
    class_agg.columns = ["Product Class", "Total Amount", "Total Price", "Count"]
    
    # Calculate max price, handling NaN case
    max_price = class_agg["Total Price"].max()
    max_price = max_price if pd.notna(max_price) and max_price > 0 else 1
    
    class_column_config = {
        "Product Class": st.column_config.TextColumn("Product Class"),
        "Total Amount": st.column_config.NumberColumn("Total Amount", step=0.01),
        "Total Price": st.column_config.ProgressColumn(
            "Total Price (€)",
            format="euro",
            min_value=0,
            max_value=max_price,
        ),
        "Count": st.column_config.NumberColumn("Count"),
    }
    st.dataframe(class_agg, use_container_width=True, column_config=class_column_config)
else:
    st.info("No classified products yet. Use the Product Reference Tool to classify products.")

st.divider()

# ==========================================
# ORIGINAL PRODUCT NAME AGGREGATION TABLE
# ==========================================
st.subheader("📋 By Product Name")

if aggregated:
    filtered = (
        filtered.groupby(["name", "unit"], as_index=False)
        .agg({"amount": "sum", "price": "sum"})
        .sort_values(by="name")
    )

# Assign a color to each unique receipt_url
# Calculate max price for the progress bar BEFORE styling (handle NaN case)
max_filtered_price = filtered["price"].max() if not filtered.empty else None
max_filtered_price = max_filtered_price if pd.notna(max_filtered_price) and max_filtered_price > 0 else 1

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
        max_value=max_filtered_price,
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
        col for col in df.columns if col not in ["id", "receipt_id", "is_credit", "product_class_id"]
    ],
)

