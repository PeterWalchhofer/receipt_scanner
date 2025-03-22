import io
import os
import zipfile

import pandas as pd
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

from components.input import get_receipt_inputs
from repository.receipt_repository import ReceiptDB, ReceiptRepository

# Initialize the database connection

receipt_repo = ReceiptRepository()


def init_session_state():
    default_values = {
        "expanded": {},
    }
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


def get_cached_receipts():
    return receipt_repo.get_all_receipts()


# Fetch all receipts (cached)
receipts = get_cached_receipts()

# Streamlit UI
st.title(f"View and Edit Receipts ({len(receipts)})")


# CSS for column alignment and button styling
st.markdown(
    """
    <style>
        .receipt-header {
            display: flex;
            justify-content: space-between;
            font-weight: bold;
            border-bottom: 2px solid #ddd;
            padding: 5px 0;
        }
        .receipt-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }
        .column {
            flex: 1;
            text-align: left;
        }
        .expand-btn {
            background-color: #f5f5f5;
            border: none;
            cursor: pointer;
            padding: 5px 10px;
            font-weight: bold;
            border-radius: 5px;
            transition: background 0.2s;
        }
        .expand-btn:hover {
            background-color: #ddd;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Display table header
st.markdown(
    """
    <div class="receipt-header">
        <div class="column">📅 Receipt Date</div>
        <div class="column">💰 Gross (€)</div>
        <div class="column">💵 Net (€)</div>
        <div class="column">🏢 Company</div>
        <div class="column" style="text-align: right;">🔍 Actions</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Display list of receipts
if receipts:
    for receipt in receipts:
        receipt_id = receipt.id
        is_expanded = st.session_state.expanded.get(f"show_receipt_{receipt_id}", False)
        arrow = "⮛" if is_expanded else "⮚"

        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 0.5])

        with col1:
            st.markdown(f"**{receipt.date}**")
        with col2:
            st.markdown(
                f"{receipt.total_gross_amount:.2f}€"
                if receipt.total_gross_amount
                else "-"
            )
        with col3:
            st.markdown(
                f"{receipt.total_net_amount:.2f}€" if receipt.total_net_amount else "-"
            )
        with col4:
            st.markdown(f"{receipt.company_name}")
        with col5:
            if st.button(f"{arrow}", key=f"btn_{receipt_id}", type="tertiary"):
                st.session_state.expanded[
                    f"show_receipt_{receipt_id}"
                ] = not is_expanded
                st.rerun()

        if is_expanded:
            col_1, col_2 = st.columns(2)
            with col_1:
                # Load images when expanded
                if receipt.file_paths:
                    st.markdown("### Receipt Images")
                    columns = st.columns(len(receipt.file_paths))
                    for i, file_path in enumerate(receipt.file_paths):
                        with columns[i]:
                            if file_path.endswith(".pdf"):
                                pdf_viewer(file_path)
                            else:
                                st.image(
                                    file_path,
                                    caption="Receipt Image",
                                    use_container_width=True,
                                )
            with col_2:
                inputs = get_receipt_inputs(receipt, receipt_id)
                if st.button("Save Changes", key=f"save_{receipt_id}"):
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
                    )
                    receipt_repo.update_receipt(receipt_id, updated_receipt)
                    st.success("Changes saved successfully!")
                    # st.session_state.expanded = {}
                    st.rerun()

    # --- CSV EXPORT ---
    if st.button("Download Data as CSV"):
        df = pd.DataFrame([r.__dict__ for r in receipts]).drop(
            "_sa_instance_state", axis=1
        )
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="receipts_data.csv",
            mime="text/csv",
        )

    # --- ZIP EXPORT ---
    if st.button("Download Files as ZIP"):
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for receipt in receipts:
                for i, file_path in enumerate(receipt.file_paths):
                    if os.path.exists(file_path):
                        zip_file.write(file_path, os.path.basename(file_path))
                    else:
                        st.warning(f"File not found: {file_path}")

        zip_buffer.seek(0)

        st.download_button(
            label="📥 Download Image/PDF ZIP",
            data=zip_buffer,
            file_name="receipt_files.zip",
            mime="application/zip",
        )

else:
    st.write("No receipts found.")
