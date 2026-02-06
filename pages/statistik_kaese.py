import altair as alt
import pandas as pd
import streamlit as st
from sqlalchemy import or_

from models.product import ProductUnit
from models.receipt import ReceiptSource
from repository.receipt_repository import ProductDB, ReceiptDB, SessionLocal, SortimentDB

KAESEINNAHMEN_COMPANIES = ["Hofladen", "Kemmts Eina", "Wochenmarkt", "Marktwagen"]


def show_kaese_statistics():
    """Display cheese statistics with aggregation by type and unit."""
    st.header("Käse Statistik")

    # Load käse data
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
            st.info("No cheese products found.")
            return
        
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
                    "product_class_id": prod.product_class_reference,
                }
            )
        kaese_df = pd.DataFrame(data)

    # Get product class names
    product_class_ids = kaese_df[kaese_df["product_class_id"].notna()]["product_class_id"].unique()
    sortiment_map = {}
    if len(product_class_ids) > 0:
        with SessionLocal() as session:
            sortiments = session.query(SortimentDB).filter(
                SortimentDB.id.in_(product_class_ids)
            ).all()
            sortiment_map = {s.id: s.name for s in sortiments}

    kaese_df["cheese_type"] = kaese_df["product_class_id"].map(sortiment_map)

    # Sidebar filter
    st.sidebar.header("Filter Käse")
    companies = [None] + sorted(kaese_df["company_name"].dropna().unique().tolist())
    company = st.sidebar.selectbox(
        "Company", options=companies, key="kaese_stat_company"
    )
    filtered_kaese = kaese_df.copy()
    if company:
        filtered_kaese = filtered_kaese[filtered_kaese["company_name"] == company]

    # ==========================================
    # PRODUCT CLASS AGGREGATION BY UNIT
    # ==========================================
    st.subheader("📊 By Cheese Type")
    classified_kaese = filtered_kaese[filtered_kaese["cheese_type"].notna()].copy()

    if not classified_kaese.empty:
        # Aggregate by cheese type and unit
        class_agg = (
            classified_kaese.groupby(["cheese_type", "unit"], as_index=False)
            .agg({
                "amount": "sum",
                "price": "sum",
                "id": "count",
            })
            .sort_values(by="price", ascending=False)
        )
        class_agg.columns = ["Cheese Type", "Unit", "Total Amount", "Total Price", "Count"]

        # Horizontal bar charts - Income by cheese type
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Income by Cheese Type**")
            # Aggregate price by cheese type (summing across all units)
            income_by_type = class_agg.groupby("Cheese Type", as_index=False)["Total Price"].sum()
            income_by_type = income_by_type.sort_values(by="Total Price", ascending=False)
            # Pre-format the values for display
            income_by_type["Price_Label"] = income_by_type["Total Price"].apply(lambda x: f"€{x:,.2f}")
            
            bars = (
                alt.Chart(income_by_type)
                .mark_bar()
                .encode(
                    y=alt.Y("Cheese Type", sort="-x"),
                    x=alt.X("Total Price", title="Income (€)"),
                    color=alt.value("green"),
                )
            )
            
            text = bars.mark_text(align="left", dx=3).encode(
                text=alt.Text("Price_Label:N")
            )
            
            income_chart = (alt.layer(bars, text)
                .properties(height=max(300, len(income_by_type) * 40))
                .configure_axis(labelLimit=0)
            )
            st.altair_chart(income_chart, use_container_width=True)

        with col2:
            st.write("**Amount by Cheese Type**")
            # Aggregate amount by cheese type (summing across all units)
            amount_by_type = class_agg.groupby("Cheese Type", as_index=False)["Total Amount"].sum()
            amount_by_type = amount_by_type.sort_values(by="Total Amount", ascending=False)
            # Pre-format the values for display
            amount_by_type["Amount_Label"] = amount_by_type["Total Amount"].apply(lambda x: f"{x:,.2f}")
            
            bars = (
                alt.Chart(amount_by_type)
                .mark_bar()
                .encode(
                    y=alt.Y("Cheese Type", sort="-x"),
                    x=alt.X("Total Amount", title="Total Amount"),
                    color=alt.value("gold"),
                )
            )
            
            text = bars.mark_text(align="left", dx=3).encode(
                text=alt.Text("Amount_Label:N")
            )
            
            amount_chart = (alt.layer(bars, text)
                .properties(height=max(300, len(amount_by_type) * 40))
                .configure_axis(labelLimit=0)
            )
            st.altair_chart(amount_chart, use_container_width=True)

        st.divider()

        # Display detailed tables for each unit type
        st.subheader("📋 Details by Unit")

        # Map unit values to display names
        unit_display_names = {
            ProductUnit.PIECE.value: "Pieces (Stück)",
            ProductUnit.KILO.value: "Kilograms (kg)",
            ProductUnit.LITER.value: "Liters (L)",
        }

        for unit_enum in [ProductUnit.PIECE, ProductUnit.KILO, ProductUnit.LITER]:
            unit_value = unit_enum.value
            unit_data = class_agg[class_agg["Unit"] == unit_value].copy()
            
            if not unit_data.empty:
                st.write(f"**{unit_display_names.get(unit_value, unit_value)}**")
                st.dataframe(
                    unit_data[["Cheese Type", "Total Amount", "Total Price", "Count"]],
                    use_container_width=True,
                    hide_index=True,
                )
    else:
        st.info("No classified cheese products yet. Use the Product Reference Tool to classify products.")
