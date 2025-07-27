import pandas as pd
import streamlit as st

from models.product import BioCategory
from repository.receipt_repository import ProductDB, ReceiptDB, SessionLocal

KAESEINNAHMEN_COMPANIES = ["Hofladen", "Kemmts Eina", "Wochenmarkt"]

st.title("Products Overview")

mode = st.radio("Mode", ["Biokontrolle", "Käseinnahmen"], horizontal=True)

with SessionLocal() as session:
    # Join products with receipts for filtering
    query = session.query(ProductDB, ReceiptDB).join(
        ReceiptDB, ProductDB.receipt_id == ReceiptDB.id
    )
    all_rows = query.all()
    # Build DataFrame
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
            }
        )
    df = pd.DataFrame(data)

if mode == "Biokontrolle":
    st.header("Biokontrolle Produkte")
    # Filter: is_credit=False, is_bio=True
    df_bio = df[(df["is_bio"] == True) & (df["is_credit"] == False)]
    # Sidebar filters
    st.sidebar.header("Filter Biokontrolle")
    bio_categories = [None] + [e.value for e in BioCategory]
    bio_category = st.sidebar.selectbox("BioCategory", options=bio_categories)
    companies = [None] + sorted(df_bio["company_name"].dropna().unique().tolist())
    company = st.sidebar.selectbox("Company", options=companies)
    filtered = df_bio.copy()
    if bio_category:
        filtered = filtered[filtered["bio_category"] == bio_category]
    if company:
        filtered = filtered[filtered["company_name"] == company]
    st.dataframe(
        filtered,
        use_container_width=True,
        column_config={
            "name": "Product Name",
            "amount": st.column_config.NumberColumn("Amount", step=0.01),
            "unit": "Unit",
            "bio_category": "BioCategory",
            "company_name": "Company",
            "date": "Date",
        },
    )

elif mode == "Käseinnahmen":
    st.header("Käseinnahmen Produkte")
    # Filter: is_credit=True, company in KAESEINNAHMEN_COMPANIES
    df_kaese = df[
        (df["is_credit"] == True) & (df["company_name"].isin(KAESEINNAHMEN_COMPANIES))
    ]
    # Sidebar filter
    st.sidebar.header("Filter Käseinnahmen")
    companies = [None] + sorted(df_kaese["company_name"].dropna().unique().tolist())
    company = st.sidebar.selectbox("Company", options=companies, key="kaese_company")
    filtered = df_kaese.copy()
    if company:
        filtered = filtered[filtered["company_name"] == company]
    # Aggregate by name and unit, sum amount
    agg = filtered.groupby(["name", "unit"]).agg({"amount": "sum"}).reset_index()
    st.dataframe(
        agg,
        use_container_width=True,
        column_config={
            "name": "Product Name",
            "amount": st.column_config.NumberColumn("Total Amount", step=0.01),
            "unit": "Unit",
        },
    )
