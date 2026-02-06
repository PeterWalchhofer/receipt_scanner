import altair as alt
import pandas as pd
import streamlit as st

from pages.utils import get_location
from repository.receipt_repository import ReceiptRepository


def show_overview_statistics(df):
    """Display overview statistics: income/expense summary, monthly trends, VAT comparison, and top companies."""
    st.header("Überblick")

    # 1. Summarize all expanses and all incomes (is_credit False/True) and visualize via Bar Chart
    income = df[df["is_credit"]]["total_gross_amount"].sum()
    expanse = df[~df["is_credit"]]["total_gross_amount"].sum()
    gewinn = income - expanse

    # 1. Summarize all expanses and all incomes (is_credit False/True) and visualize via Bar Chart
    income = df[df["is_credit"]]["total_gross_amount"].sum()
    expanse = df[~df["is_credit"]]["total_gross_amount"].sum()
    gewinn = income - expanse

    bar_data = pd.DataFrame(
        {
            "Type": ["Income", "Expanse", "Gewinn"],
            "Amount": [income, expanse, gewinn],
            "Label": [f"€{income:,.2f}", f"€{expanse:,.2f}", f"€{gewinn:,.2f}"],
        }
    )

    bars = (
        alt.Chart(bar_data)
        .mark_bar()
        .encode(
            y=alt.Y("Type", sort=["Income", "Expanse", "Gewinn"]),
            x=alt.X("Amount", title="Sum (€)"),
            color=alt.Color(
                "Type",
                scale=alt.Scale(
                    domain=["Income", "Expanse", "Gewinn"],
                    range=["green", "red", "blue"] if gewinn >= 0 else ["green", "red", "orange"],
                ),
                legend=None,
            ),
        )
    )

    text = bars.mark_text(align="left", dx=3).encode(
        text=alt.Text("Label:N")
    )

    bar_chart = (
        alt.layer(bars, text)
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
    income_vat = df[df["is_credit"]].get("vat_amount", pd.Series([])).sum()
    expanse_vat = df[~df["is_credit"]].get("vat_amount", pd.Series([])).sum()
    vat_delta = expanse_vat - income_vat  # VAT to pay back (expenses) minus VAT to pay (income)
    vat_data = pd.DataFrame(
        {
            "Type": ["USt. Ausgaben", "USt. Einnahmen", "Delta"],
            "VAT": [expanse_vat, income_vat, vat_delta],
            "Label": [f"€{expanse_vat:,.2f}", f"€{income_vat:,.2f}", f"€{vat_delta:,.2f}"],
        }
    )

    bars = (
        alt.Chart(vat_data)
        .mark_bar()
        .encode(
            y=alt.Y("Type", sort=["USt. Ausgaben", "USt. Einnahmen", "Delta"]),
            x=alt.X("VAT", title="Sum VAT (€)"),
            color=alt.Color(
                "Type",
                scale=alt.Scale(
                    domain=["USt. Ausgaben", "USt. Einnahmen", "Delta"], 
                    range=["green", "red", "darkgray"]
                ),
                legend=None,
            ),
        )
    )

    text = bars.mark_text(align="left", dx=3).encode(
        text=alt.Text("Label:N")
    )

    vat_chart = (
        alt.layer(bars, text)
        .properties(title="USt. Vergleich", height=200)
        .configure_axis(labelLimit=0)
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
    expanse_df["Label"] = expanse_df["total_net_amount"].apply(lambda x: f"€{x:,.2f}")
    chart_height = max(300, len(expanse_df) * 40)  # Dynamic height: 40px per company

    bars = (
        alt.Chart(expanse_df)
        .mark_bar()
        .encode(
            y=alt.Y("company_name", title="Company", sort="-x"),
            x=alt.X("total_net_amount", title="Expenses (€)"),
            color=alt.value("red"),
        )
    )

    text = bars.mark_text(align="left", dx=3).encode(
        text=alt.Text("Label:N")
    )

    expanse_chart = (
        alt.layer(bars, text)
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
    location_income["Label"] = location_income["total_gross_amount"].apply(lambda x: f"€{x:,.2f}")

    # Create horizontal bar chart with dynamic height
    location_chart_height = max(300, len(location_income) * 50)  # Dynamic height: 50px per location

    bars = (
        alt.Chart(location_income)
        .mark_bar()
        .encode(
            y=alt.Y("location", title="Sales Location", sort="-x"),
            x=alt.X("total_gross_amount", title="Income (€)"),
            color=alt.value("green"),
        )
    )

    text = bars.mark_text(align="left", dx=3).encode(
        text=alt.Text("Label:N")
    )

    location_chart = (
        alt.layer(bars, text)
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
            other_df["Label"] = other_df["total_net_amount"].apply(lambda x: f"€{x:,.2f}")
            other_chart_height = max(300, len(other_df) * 40)  # Dynamic height: 40px per company

            bars = (
                alt.Chart(other_df)
                .mark_bar()
                .encode(
                    y=alt.Y("company_name", title="Company", sort="-x"),
                    x=alt.X("total_net_amount", title="Income (€)"),
                    color=alt.value("lightgreen"),
                )
            )

            text = bars.mark_text(align="left", dx=3).encode(
                text=alt.Text("Label:N")
            )

            other_chart = (
                alt.layer(bars, text)
                .properties(title="Other Income Companies (>200€)", height=other_chart_height)
                .configure_axis(labelLimit=0)
            )
            st.altair_chart(other_chart, use_container_width=True)
        else:
            st.info("No other income companies with sums over 200€")
