import io
import os
import zipfile
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

from components.input import get_receipt_inputs
from repository.receipt_repository import ReceiptDB, ReceiptRepository

# Initialize the database connection
receipt_repo = ReceiptRepository()


def init_session_state():
    if "selected_receipts" not in st.session_state:
        st.session_state["selected_receipts"] = None


init_session_state()


def get_cached_receipts():
    return receipt_repo.get_all_receipts()


# Fetch all receipts (cached)
receipts = get_cached_receipts()

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
        df,
        column_order=(
            [*main_cols, *[col for col in df.columns if col not in main_cols]]
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
            "is_credit": "Einnahme",
            "is_bio": "Biokontrolle",
            "description": "Beschreibung",
            "comment": "Kommentar",
            "company_name": "🏢 Company",
            "Details": st.column_config.LinkColumn("🔍 Details", display_text="Edit"),
            "progress": st.column_config.ProgressColumn(
                "💰 Gross (€)",
                min_value=0,
                max_value=df["progress"].max(),
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

else:
    st.write("No receipts found.")
