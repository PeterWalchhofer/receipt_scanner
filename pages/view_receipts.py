import io
import os
import zipfile
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

from components.input import get_receipt_inputs
from components.product_db_ops import get_products_counts
from pages.utils import get_location
from repository.receipt_repository import ReceiptDB, ReceiptRepository

# Initialize the database connection
receipt_repo = ReceiptRepository()


def init_session_state():
    if "selected_receipts" not in st.session_state:
        st.session_state["selected_receipts"] = None


init_session_state()


def get_cached_receipts():
    return receipt_repo.get_all_receipts()


def receipt_has_missing_products(receipt: ReceiptDB, product_dict: dict):
    """Determine if a receipt should contain products based on its attributes."""
    # No "kemmts eina" because we do it at the end of the year
    should_contain_product = receipt.should_have_products()
    if receipt.company_name == "Kemmts Eina" and receipt.is_credit:
        should_contain_product = False
    does_contain = receipt.id in product_dict
    return not (should_contain_product and does_contain) or (not should_contain_product)


# Fetch all receipts (cached)
receipts = get_cached_receipts()
products_count = {receipt_id: count for receipt_id, count in get_products_counts()}

# Streamlit UI
st.title(f"View and Edit Receipts ({len(receipts)})")
if st.button("🔃"):
    st.rerun()

if receipts:
    # Convert receipts to DataFrame
    df = pd.DataFrame([r.__dict__ for r in receipts]).drop("_sa_instance_state", axis=1)
    df["Details"] = [
        f"/receipt_detail?id={quote_plus(str(r.id))}" for r in receipts
    ]  # Clickable links
    df["progress"] = df["total_gross_amount"]
    df["source"] = [getattr(r, "source", "RECEIPT_SCANNER") for r in receipts]
    df["products"] = [receipt_has_missing_products(r, products_count) for r in receipts]

    # --- Filter UI ---
    st.sidebar.header("Filter Receipts")
    is_credit_filter = st.sidebar.selectbox(
        "Einnahme (is_credit)", options=["All", True, False], index=0
    )
    is_bio_filter = st.sidebar.selectbox(
        "Biokontrolle (is_bio)", options=["All", True, False], index=0
    )
    comment_filter = st.sidebar.selectbox(
        "Kommentar", options=["All", "Has Comment", "No Comment"], index=0
    )
    company_options = ["All"] + sorted(df["company_name"].dropna().unique().tolist())
    company_filter = st.sidebar.selectbox("Company", options=company_options, index=0)
    products_filter = st.sidebar.selectbox(
        "Missing Products", options=["All", True, False], index=0
    )
    source_filter = st.sidebar.selectbox(
        "Quelle",
        options=["All"] + sorted(df["source"].dropna().unique().tolist()),
        index=0,
    )
    filtered_df = df.copy()
    if is_credit_filter != "All":
        filtered_df = filtered_df[filtered_df["is_credit"] == is_credit_filter]
    if is_bio_filter != "All":
        filtered_df = filtered_df[filtered_df["is_bio"] == is_bio_filter]
    if comment_filter == "Has Comment":
        filtered_df = filtered_df[
            filtered_df["comment"].notnull() & (filtered_df["comment"] != "")
        ]
    elif comment_filter == "No Comment":
        filtered_df = filtered_df[
            filtered_df["comment"].isnull() | (filtered_df["comment"] == "")
        ]
    if company_filter != "All":
        filtered_df = filtered_df[filtered_df["company_name"] == company_filter]

    if products_filter != "All":
        filtered_df = filtered_df[filtered_df["products"] == products_filter]
    if source_filter != "All":
        filtered_df = filtered_df[filtered_df["source"] == source_filter]
    main_cols = [
        "date",
        "company_name",
        "total_gross_amount",
        "total_net_amount",
        "vat_amount",
        "source",
        "Details",
        "progress",
    ]
    # Display DataFrame as a table
    st.dataframe(
        filtered_df,
        column_order=(
            [*main_cols, *[col for col in filtered_df.columns if col not in main_cols]]
        ),
        column_config={
            "id": None,
            "updated_on": None,
            "created_on": None,
            "receipt_number": None,
            "file_paths": None,
            "date": "📅 Date",
            "total_gross_amount": st.column_config.NumberColumn(
                "💰 Brutto (€)", format="euro"
            ),
            "total_net_amount": st.column_config.NumberColumn(
                "💵 Netto (€)", format="euro"
            ),
            "vat_amount": st.column_config.NumberColumn("💶 USt. (€)", format="euro"),
            "products": st.column_config.CheckboxColumn("Missing Products"),
            "is_credit": "Einnahme",
            "is_bio": "Biokontrolle",
            "description": "Beschreibung",
            "comment": "Kommentar",
            "company_name": "🏢 Company",
            "Details": st.column_config.LinkColumn("🔍 Details", display_text="Edit"),
            "progress": st.column_config.ProgressColumn(
                "💰 Gross (€)",
                min_value=0,
                max_value=filtered_df["progress"].max() if not filtered_df.empty else 0,
                format="euro",
            ),
            "source": st.column_config.TextColumn("Quelle"),
        },
        use_container_width=True,
    )

    # Sidebar for details
    receipt_id = st.session_state.get("selected_receipt")
    if receipt_id:
        receipt = next((r for r in receipts if r.id == receipt_id), None)
        if receipt:
            st.sidebar.header("Receipt Details")
            st.sidebar.markdown(f"**Date:** {receipt.date}")
            st.sidebar.markdown(f"**Company:** {receipt.company_name}")
            st.sidebar.markdown(f"**Gross:** {receipt.total_gross_amount}€")
            st.sidebar.markdown(f"**Net:** {receipt.total_net_amount}€")
            st.sidebar.markdown(
                f"**Source:** {getattr(receipt, 'source', 'RECEIPT_SCANNER')}"
            )

            if receipt.file_paths:
                st.sidebar.markdown("### Files")
                for file_path in receipt.file_paths:
                    if file_path.endswith(".pdf"):
                        pdf_viewer(file_path)
                    else:
                        st.sidebar.image(
                            file_path, caption="Receipt Image", use_container_width=True
                        )

            # Editable fields
            inputs = get_receipt_inputs(receipt, receipt_id)
            if st.sidebar.button("Save Changes"):
                updated_receipt = ReceiptDB(
                    id=receipt_id,
                    receipt_number=inputs["receipt_number"],
                    date=inputs["receipt_date"],
                    total_gross_amount=float(inputs["total_gross_amount"]),
                    total_net_amount=float(inputs["total_net_amount"]),
                    vat_amount=float(inputs["vat_amount"]),
                    company_name=inputs["company_name"],
                    description=inputs["description"],
                    comment=inputs["comment"],
                    is_credit=inputs["is_credit"],
                    is_bio=inputs["is_bio"],
                    file_paths=receipt.file_paths,
                    source=inputs["source"],
                )
                receipt_repo.update_receipt(receipt_id, updated_receipt)
                st.success("Changes saved successfully!")
                st.rerun()
    # CSV and ZIP export buttons
    if st.button("Download Data as CSV"):
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download CSV", csv_data, "receipts_data.csv", "text/csv")

    if st.button("Download Files as ZIP"):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for receipt in receipts:
                for file_path in receipt.file_paths:
                    if os.path.exists(file_path):
                        zip_file.write(file_path, os.path.basename(file_path))
        zip_buffer.seek(0)
        st.download_button(
            "📥 Download Image/PDF ZIP",
            zip_buffer,
            "receipt_files.zip",
            "application/zip",
        )

    st.subheader("Export Steuerberaterin")

    col1, col2, col_3 = st.columns(3)

    with col1:
        # Date picker for filtering by created_on
        min_created_date = st.date_input(
            "Receipts created since",
            value=None,
            help="Export receipts created on or after this date.",
        )

    with col2:
        # Date picker for filtering by receipt date
        min_receipt_date = st.date_input(
            "Receipt date from (inclusive)",
            value=None,
            help="Export receipts with a receipt date on or after this date.",
        )
    with col_3:
        max_receipt_date = st.date_input(
            "Receipt date to (inclusive)",
            value=None,
            help="Export receipts with a receipt date on or before this date.",
        )
    if st.button("Export Steuerberaterin CSV"):
        col_rename_mapping = {
            "date": "Datum",
            "company_name": "Unternehmen",
            "is_credit": "Einnahme",
            "total_gross_amount": "Brutto",
            "total_net_amount": "Netto",
            "vat_amount": "USt.",
            "description": "Beschreibung",
            "comment": "Kommentar",
            "location": "Verkaufsort",
        }

        # Filter by created_on date and/or receipt date
        df_to_export = df.copy()

        if min_created_date or min_receipt_date or max_receipt_date:
            df_to_export["created_on"] = pd.to_datetime(df_to_export["created_on"])
            df_to_export["date"] = pd.to_datetime(df_to_export["date"], format="mixed")

            # Create filter conditions
            conditions = []

            if min_created_date:
                conditions.append(
                    df_to_export["created_on"].dt.date >= min_created_date
                )

            if min_receipt_date:
                conditions.append(df_to_export["date"].dt.date >= min_receipt_date)

            # Combine conditions with OR logic
            if len(conditions) == 2:
                combined_filter = conditions[0] | conditions[1]
            else:
                combined_filter = conditions[0]

            df_to_export = df_to_export[combined_filter] if not max_receipt_date else df_to_export[
                (combined_filter) & (df_to_export["date"].dt.date <= max_receipt_date)
            ]
        else:
            st.info(f"Exporting all {len(df_to_export)} receipts")

        # Aggregat einnahmen
        df_to_export["location"] = df_to_export.apply(get_location, axis=1)
        df_export = (
            df_to_export[list(col_rename_mapping.keys())]
            .rename(columns=col_rename_mapping)
            .sort_values("Datum")
        )
        df_einnahmen = df_export[df_export["Einnahme"]]
        df_ausgaben = df_export[~df_export["Einnahme"]]

        # Drop Einnahme column for export
        df_einnahmen = df_einnahmen.drop(columns="Einnahme")
        df_einnahmen_agg = df_einnahmen.groupby("Verkaufsort")[
            ["USt.", "Netto", "Brutto"]
        ].sum()
        df_ausgaben = df_ausgaben.drop(columns="Einnahme")

        # Export to Excel in-memory
        excel_einnahmen = io.BytesIO()
        with pd.ExcelWriter(excel_einnahmen, engine="xlsxwriter") as writer:
            df_einnahmen.to_excel(writer, index=False, sheet_name="Einnahmen")
        excel_einnahmen.seek(0)

        excel_einnahmen_aggregiert = io.BytesIO()
        with pd.ExcelWriter(excel_einnahmen_aggregiert, engine="xlsxwriter") as writer:
            df_einnahmen_agg.to_excel(writer, index=True, sheet_name="Einnahmen")
        excel_einnahmen_aggregiert.seek(0)

        excel_ausgaben = io.BytesIO()
        with pd.ExcelWriter(excel_ausgaben, engine="xlsxwriter") as writer:
            df_ausgaben.to_excel(writer, index=False, sheet_name="Ausgaben")
        excel_ausgaben.seek(0)

        st.download_button(
            "📥 Download Ausgaben Excel",
            excel_ausgaben.getvalue(),
            "receipt_ausgaben.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.download_button(
            "📥 Download Einnahmen Excel",
            excel_einnahmen.getvalue(),
            "receipts_einnahmen.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.download_button(
            "📥 Download Einnahmen Aggregiert Excel",
            excel_einnahmen_aggregiert.getvalue(),
            "receipts_einnahmen_agg.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


else:
    st.write("No receipts found.")
