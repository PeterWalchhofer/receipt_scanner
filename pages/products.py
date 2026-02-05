"""
Products Page

Browse and search all products with comprehensive filtering options.
Link directly to receipts for editing.
"""

from urllib.parse import quote_plus

import pandas as pd
import streamlit as st

from repository.receipt_repository import ProductDB, ReceiptDB, SessionLocal

st.title("🛍️ All Products")
st.write("Browse and search all products with flexible filtering.")

# Fetch all products with their receipt info
with SessionLocal() as session:
    query = session.query(ProductDB, ReceiptDB).join(
        ReceiptDB, ProductDB.receipt_id == ReceiptDB.id
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
                "bio_category": (
                    prod.bio_category.value
                    if hasattr(prod.bio_category, "value")
                    else prod.bio_category
                ),
                "product_class": None,  # Will populate below
                "company_name": rec.company_name,
                "is_credit": rec.is_credit,
                "date": rec.date,
                "receipt_number": rec.receipt_number,
                "receipt_url": f"/receipt_detail?id={quote_plus(str(rec.id))}",
            }
        )

df = pd.DataFrame(data)

# Sidebar filters
st.sidebar.header("🔍 Filters")

# Text search for product name
name_search = st.sidebar.text_input(
    "Search Product Name",
    placeholder="e.g., käse, butter...",
)

# Price range
price_range = st.sidebar.slider(
    "Price Range (€)",
    min_value=0.0,
    max_value=float(df["price"].max()) if df["price"].max() else 100.0,
    value=(0.0, float(df["price"].max()) if df["price"].max() else 100.0),
    step=0.01,
)

# Amount range
amount_range = st.sidebar.slider(
    "Amount Range",
    min_value=0.0,
    max_value=float(df["amount"].max()) if df["amount"].max() else 1000.0,
    value=(0.0, float(df["amount"].max()) if df["amount"].max() else 1000.0),
    step=0.1,
)

# Unit filter
units = [None] + sorted(df["unit"].dropna().unique().tolist())
selected_unit = st.sidebar.selectbox("Unit", options=units)

# is_bio filter
bio_options = ["All", "Bio Only", "Non-Bio Only"]
bio_filter = st.sidebar.selectbox("Bio Status", options=bio_options)

# is_credit filter
credit_options = ["All", "Credit Only", "Non-Credit Only"]
credit_filter = st.sidebar.selectbox("Receipt Type", options=credit_options)

# Company filter
companies = [None] + sorted(df["company_name"].dropna().unique().tolist())
selected_company = st.sidebar.selectbox("Company", options=companies)

# Apply filters
filtered = df.copy()

if name_search:
    filtered = filtered[
        filtered["name"].str.contains(name_search, case=False, na=False)
    ]

filtered = filtered[
    (filtered["price"] >= price_range[0]) & (filtered["price"] <= price_range[1])
]

filtered = filtered[
    (filtered["amount"] >= amount_range[0]) & (filtered["amount"] <= amount_range[1])
]

if selected_unit:
    filtered = filtered[filtered["unit"] == selected_unit]

if bio_filter == "Bio Only":
    filtered = filtered[filtered["is_bio"] == True]
elif bio_filter == "Non-Bio Only":
    filtered = filtered[filtered["is_bio"] == False]

if credit_filter == "Credit Only":
    filtered = filtered[filtered["is_credit"] == True]
elif credit_filter == "Non-Credit Only":
    filtered = filtered[filtered["is_credit"] == False]

if selected_company:
    filtered = filtered[filtered["company_name"] == selected_company]

# Display results info
st.sidebar.divider()
st.sidebar.metric("Total Products", len(df))
st.sidebar.metric("Filtered Results", len(filtered))

# Display the filtered table
if filtered.empty:
    st.info("No products match your filters. Try adjusting them!")
else:
    column_config = {
        "name": st.column_config.TextColumn("Product Name", width="medium"),
        "amount": st.column_config.NumberColumn("Amount", format="%.2f"),
        "unit": st.column_config.TextColumn("Unit", width="small"),
        "price": st.column_config.NumberColumn("Price (€)", format="€%.2f"),
        "is_bio": st.column_config.CheckboxColumn("Bio", width="small"),
        "bio_category": st.column_config.TextColumn("Bio Category", width="small"),
        "company_name": st.column_config.TextColumn("Company", width="small"),
        "is_credit": st.column_config.CheckboxColumn("Credit", width="small"),
        "date": st.column_config.TextColumn("Date", width="small"),
        "receipt_number": st.column_config.TextColumn("Receipt #", width="small"),
        "receipt_url": st.column_config.LinkColumn("🔍 Edit", display_text="Edit"),
    }

    st.dataframe(
        filtered,
        use_container_width=True,
        column_config=column_config,
        column_order=[
            "name",
            "amount",
            "unit",
            "price",
            "is_bio",
            "bio_category",
            "company_name",
            "is_credit",
            "date",
            "receipt_number",
            "receipt_url",
        ],
        hide_index=True,
    )

    # Download as CSV option
    st.divider()
    csv = filtered.to_csv(index=False)
    st.download_button(
        label="📥 Download Filtered Products as CSV",
        data=csv,
        file_name="products_filtered.csv",
        mime="text/csv",
    )
