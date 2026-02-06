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
        "Color": ["green", "red", "blue"] if gewinn >= 0 else ["green", "red", "orange"],
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
                range=["green", "red", "blue"] if gewinn >= 0 else ["green", "red", "orange"],
            ),
            legend=None,
        ),
        tooltip=["Amount"],
    )
    .properties(title="Income, Expanse & Gewinn")
)
st.altair_chart(bar_chart, use_container_width=True)
gewinn_color = "green" if gewinn >= 0 else "red"
st.markdown(f"**Gewinn:** :{gewinn_color}[{gewinn:.2f} €]")

# 2. Line Chart of Income vs Expanses for each month
if "date" in df.columns:
    df["month"] = df["date"].dt.to_period("M")
    monthly = (
        df.groupby(["month", "is_credit"])
        .agg({"total_gross_amount": "sum"})
        .reset_index()
    )
    # Convert month back to timestamp for proper sorting in Altair
    monthly["month"] = monthly["month"].dt.to_timestamp()
    monthly["Type"] = monthly["is_credit"].map({True: "Income", False: "Expanse"})
    line_chart = (
        alt.Chart(monthly)
        .mark_line(point=True)
        .encode(
            x=alt.X("month:T", title="Month", axis=alt.Axis(format="%Y-%m")),
            y=alt.Y("total_gross_amount", title="Sum (€)"),
            color=alt.Color(
                "Type",
                scale=alt.Scale(domain=["Income", "Expanse"], range=["green", "red"]),
            ),
            tooltip=["month:T", "Type", "total_gross_amount"],
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
expanse_df = expanse_companies.reset_index()
expanse_df.columns = ["company_name", "total_net_amount"]
chart_height = max(300, len(expanse_df) * 40)  # Dynamic height: 40px per company
expanse_chart = (
    alt.Chart(expanse_df)
    .mark_bar()
    .encode(
        y=alt.Y("company_name", title="Company", sort="-x"),
        x=alt.X("total_net_amount", title="Expenses (€)"),
        tooltip=["company_name", "total_net_amount"],
        color=alt.value("red"),
    )
    .properties(title=f"Top {int(K)} companies - Expenses", height=chart_height)
    .configure_axis(labelLimit=0)
)
st.altair_chart(expanse_chart, use_container_width=True)

# Section: Einnahmen
st.header("Einnahmen")

income_df = df[df["is_credit"]].copy()
income_df["location"] = income_df.apply(get_location, axis=1)

# Update get_location to include additional companies
def get_location_extended(row):
    location = get_location(row)
    if location != "Other":
        return location
    company = row.get("company_name", "").lower() if isinstance(row.get("company_name"), str) else ""
    if "salzburgmilch" in company:
        return "SalzburgMilch GmbH"
    if "viehhandel laßhofer" in company or "viehhandel lasshof" in company:
        return "Viehhandel Laßhofer"
    return "Other"

income_df["location"] = income_df.apply(get_location_extended, axis=1)
location_income = (
    income_df.groupby("location")["total_gross_amount"].sum().reset_index()
)

# Create horizontal bar chart with dynamic height
location_chart_height = max(300, len(location_income) * 50)  # Dynamic height: 50px per location
location_chart = (
    alt.Chart(location_income)
    .mark_bar()
    .encode(
        y=alt.Y("location", title="Sales Location", sort="-x"),
        x=alt.X("total_gross_amount", title="Income (€)"),
        tooltip=["location", "total_gross_amount"],
        color=alt.value("green"),
    )
    .properties(title="Einkommen nach Verkaufswert", height=location_chart_height)
    .configure_axis(labelLimit=0)
)
st.altair_chart(location_chart, use_container_width=True)

# Show "Other" incomes toggle
show_other = st.checkbox("Show other income companies (>200€)")
if show_other:
    other_companies = (
        income_df[income_df["location"] == "Other"]
        .groupby("company_name")["total_net_amount"]
        .sum()
        .sort_values(ascending=False)
    )
    other_companies = other_companies[other_companies > 200]
    if len(other_companies) > 0:
        other_df = other_companies.reset_index()
        other_df.columns = ["company_name", "total_net_amount"]
        other_chart_height = max(300, len(other_df) * 40)  # Dynamic height: 40px per company
        other_chart = (
            alt.Chart(other_df)
            .mark_bar()
            .encode(
                y=alt.Y("company_name", title="Company", sort="-x"),
                x=alt.X("total_net_amount", title="Income (€)"),
                tooltip=["company_name", "total_net_amount"],
                color=alt.value("lightgreen"),
            )
            .properties(title="Other Income Companies (>200€)", height=other_chart_height)
            .configure_axis(labelLimit=0)
        )
        st.altair_chart(other_chart, use_container_width=True)
    else:
        st.info("No other income companies with sums over 200€")
