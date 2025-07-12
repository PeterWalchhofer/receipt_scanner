import altair as alt
import pandas as pd
import streamlit as st

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
st.header("Overview")

# 1. Summarize all expanses and all incomes (is_credit False/True) and visualize via Bar Chart
income = df[df["is_credit"]]["total_gross_amount"].sum()
expanse = df[~df["is_credit"]]["total_gross_amount"].sum()
gewinn = income - expanse

bar_data = pd.DataFrame(
    {
        "Type": ["Income", "Expanse"],
        "Amount": [income, expanse],
        "Color": ["green", "red"],
    }
)
bar_chart = (
    alt.Chart(bar_data)
    .mark_bar()
    .encode(
        x=alt.X("Type", sort=["Income", "Expanse"]),
        y=alt.Y("Amount", title="Sum (€)"),
        color=alt.Color(
            "Type",
            scale=alt.Scale(domain=["Income", "Expanse"], range=["green", "red"]),
            legend=None,
        ),
        tooltip=["Amount"],
    )
    .properties(title="Income vs Expanse")
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

# 3. Bar Chart for the VAT. Compare the total income VAT and the Expanse VAT.
income_vat = df[df["is_credit"]]["vat_amount"].sum()
expanse_vat = df[~df["is_credit"]]["vat_amount"].sum()
vat_data = pd.DataFrame(
    {
        "Type": ["Income VAT", "Expanse VAT"],
        "VAT": [income_vat, expanse_vat],
        "Color": ["green", "red"],
    }
)
vat_chart = (
    alt.Chart(vat_data)
    .mark_bar()
    .encode(
        x=alt.X("Type", sort=["Income VAT", "Expanse VAT"]),
        y=alt.Y("VAT", title="Sum VAT (€)"),
        color=alt.Color(
            "Type",
            scale=alt.Scale(
                domain=["Income VAT", "Expanse VAT"], range=["green", "red"]
            ),
            legend=None,
        ),
        tooltip=["VAT"],
    )
    .properties(title="VAT Comparison")
)
st.altair_chart(vat_chart, use_container_width=True)

# Section: Ausgaben
st.header("Ausgaben (Expanses)")
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
st.header("Einnahmen (Income)")
income_companies = (
    df[df["is_credit"]]
    .groupby("company_name")["total_net_amount"]
    .sum()
    .sort_values(ascending=False)
    .head(int(K))
)
st.write(f"Top {int(K)} companies where income was generated (by total net amount):")
st.table(income_companies)

# 2. Bar Chart for the summarised income for each source (ReceiptSource)
income_by_source = (
    df[df["is_credit"]].groupby("source")["total_gross_amount"].sum().reset_index()
)
source_chart = (
    alt.Chart(income_by_source)
    .mark_bar()
    .encode(
        x=alt.X("source", title="Source"),
        y=alt.Y("total_gross_amount", title="Income (€)"),
        tooltip=["total_gross_amount"],
    )
    .properties(title="Income by Source")
)
st.altair_chart(source_chart, use_container_width=True)
