import altair as alt
import pandas as pd
import streamlit as st

from pages.utils import get_location
from repository.receipt_repository import ReceiptRepository

st.title("📊 Statistik")

receipt_repo = ReceiptRepository()
receipts = receipt_repo.get_all_receipts()

if not receipts:
    st.info("No receipts found.")
    st.stop()

df = pd.DataFrame([r.__dict__ for r in receipts])
if "_sa_instance_state" in df.columns:
    df = df.drop("_sa_instance_state", axis=1)

# Convert date to datetime
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

# Section: Overview
st.header("Überblick")

# 1. Summarize all expanses and all incomes (is_credit False/True) and visualize via Bar Chart
income = df[df["is_credit"]]["total_gross_amount"].sum()
expanse = df[~df["is_credit"]]["total_gross_amount"].sum()
gewinn = income - expanse

bar_data = pd.DataFrame(
    {
        "Type": ["Income", "Expanse", "Gewinn"],
        "Amount": [income, expanse, gewinn],
        "Color": ["green", "red", "darkgreen"],
    }
)
bar_chart = (
    alt.Chart(bar_data)
    .mark_bar()
    .encode(
        x=alt.X("Type", sort=["Income", "Expanse", "Gewinn"]),
        y=alt.Y("Amount", title="Sum (€)"),
        color=alt.Color(
            "Type",
            scale=alt.Scale(
                domain=["Income", "Expanse", "Gewinn"],
                range=["green", "red", "darkgreen"],
            ),
            legend=None,
        ),
        tooltip=["Amount"],
    )
    .properties(title="Income, Expanse & Gewinn")
)
st.altair_chart(bar_chart, use_container_width=True)
st.markdown(f"**Gewinn:** {gewinn:.2f} €")

# 2. Line Chart of Income vs Expanses for each month
if "date" in df.columns:
    df["month"] = df["date"].dt.to_period("M").astype(str)
    monthly = (
        df.groupby(["month", "is_credit"])
        .agg({"total_gross_amount": "sum"})
        .reset_index()
    )
    monthly["Type"] = monthly["is_credit"].map({True: "Income", False: "Expanse"})
    line_chart = (
        alt.Chart(monthly)
        .mark_line(point=True)
        .encode(
            x=alt.X("month:T", title="Month"),
            y=alt.Y("total_gross_amount", title="Sum (€)"),
            color=alt.Color(
                "Type",
                scale=alt.Scale(domain=["Income", "Expanse"], range=["green", "red"]),
            ),
            tooltip=["month", "Type", "total_gross_amount"],
        )
        .properties(title="Monthly Income vs Expanse")
    )
    st.altair_chart(line_chart, use_container_width=True)

# 3. Bar Chart for the VAT. Compare the total USt. Einnahmen and the USt. Ausgaben.
income_vat = df[df["is_credit"]]["vat_amount"].sum()
expanse_vat = df[~df["is_credit"]]["vat_amount"].sum()
vat_data = pd.DataFrame(
    {
        "Type": ["USt. Einnahmen", "USt. Ausgaben"],
        "VAT": [income_vat, expanse_vat],
        "Color": ["green", "red"],
    }
)
vat_chart = (
    alt.Chart(vat_data)
    .mark_bar()
    .encode(
        x=alt.X("Type", sort=["USt. Einnahmen", "USt. Ausgaben"]),
        y=alt.Y("VAT", title="Sum VAT (€)"),
        color=alt.Color(
            "Type",
            scale=alt.Scale(
                domain=["USt. Einnahmen", "USt. Ausgaben"], range=["green", "red"]
            ),
            legend=None,
        ),
        tooltip=["VAT"],
    )
    .properties(title="USt. Vergleich")
)
st.altair_chart(vat_chart, use_container_width=True)

# Section: Ausgaben
st.header("Ausgaben")
K = st.number_input(
    "Number of top companies to show", min_value=1, max_value=20, value=5, step=1
)
expanse_companies = (
    df[~df["is_credit"]]
    .groupby("company_name")["total_net_amount"]
    .sum()
    .sort_values(ascending=False)
    .head(int(K))
)
st.write(f"Top {int(K)} companies where expanses were made (by total net amount):")
st.table(expanse_companies)

# Section: Einnahmen
st.header("Einnahmen")


income_df = df[df["is_credit"]].copy()
income_df["location"] = income_df.apply(get_location, axis=1)
location_income = (
    income_df.groupby("location")["total_gross_amount"].sum().reset_index()
)
location_chart = (
    alt.Chart(location_income)
    .mark_bar()
    .encode(
        x=alt.X("location", title="Sales Location"),
        y=alt.Y("total_gross_amount", title="Income (€)"),
        tooltip=["total_gross_amount"],
        color=alt.Color("location", legend=None),
    )
    .properties(title="Einkommen nach Verkaufsort")
)
st.altair_chart(location_chart, use_container_width=True)

K2 = st.number_input(
    "Number of top companies to show (income)",
    min_value=1,
    max_value=20,
    value=5,
    step=1,
)
income_companies = (
    income_df[income_df["location"] == "Other"]
    .groupby("company_name")["total_net_amount"]
    .sum()
    .sort_values(ascending=False)
    .head(int(K2))
)
st.write(f"Top {int(K2)} companies where income were made (by total net amount):")
st.table(income_companies)
