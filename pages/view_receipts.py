import streamlit as st
import pandas as pd
import zipfile
import os
import io
from db.database import get_db
from repository.receipt_repository import ReceiptRepository
from models.receipt import Receipt

# Initialize the database connection
db = next(get_db())
receipt_repo = ReceiptRepository(db)

# Streamlit UI
st.title("View and Edit Receipts")

# Fetch all receipts from the database
receipts = receipt_repo.get_all_receipts()

# CSS for column alignment
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
            padding: 5px 0;
        }
        .column {
            flex: 1;
            text-align: left;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Display a table header
st.markdown(
    """
    <div class="receipt-header">
        <div class="column">📅 Date</div>
        <div class="column">💰 Gross (€)</div>
        <div class="column">💵 Net (€)</div>
        <div class="column">🏢 Company</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Display the list of receipts
if receipts:
    for receipt in receipts:
        st.markdown(
            f"""
            <div class="receipt-row">
                <div class="column">{receipt.date}</div>
                <div class="column">{receipt.total_gross_amount:.2f}€</div>
                <div class="column">{receipt.total_net_amount:.2f}€</div>
                <div class="column">{receipt.company_name}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("View & Edit Receipt"):
            st.image(receipt.image_path, caption="Receipt Image", use_container_width=True)

            # Editable fields
            receipt_number = st.text_input("Receipt Number", value=receipt.receipt_number, key=f"receipt_number_{receipt.id}")
            receipt_date = st.text_input("Receipt Date", value=receipt.date, key=f"date_{receipt.id}")
            total_gross_amount = st.text_input("Total Gross Amount", value=str(receipt.total_gross_amount), key=f"gross_{receipt.id}")
            total_net_amount = st.text_input("Total Net Amount", value=str(receipt.total_net_amount), key=f"net_{receipt.id}")
            vat_amount = st.text_input("VAT Amount", value=str(receipt.vat_amount), key=f"vat_{receipt.id}")
            company_name = st.text_input("Company Name", value=receipt.company_name, key=f"company_{receipt.id}")
            description = st.text_area("Description", value=receipt.description, key=f"description_{receipt.id}")
            is_credit = st.checkbox("Is Credit", value=receipt.is_credit, key=f"is_credit_{receipt.id}")

            if st.button(f"Save Changes for {receipt.id}"):
                updated_receipt = Receipt(
                    id=receipt.id,
                    receipt_number=receipt_number,
                    date=receipt_date,
                    total_gross_amount=float(total_gross_amount),
                    total_net_amount=float(total_net_amount),
                    vat_amount=float(vat_amount),
                    company_name=company_name,
                    description=description,
                    is_credit=is_credit,
                    image_path=receipt.image_path,
                )
                receipt_repo.update_receipt(updated_receipt.dict())
                st.success("Changes saved successfully!")

    # --- CSV EXPORT ---
    if st.button("Download Data as CSV"):
        df = pd.DataFrame([r.__dict__ for r in receipts])
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="receipts_data.csv",
            mime="text/csv",
        )

    # --- ZIP EXPORT ---
    if st.button("Download Images as ZIP"):
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for receipt in receipts:
                if os.path.exists(receipt.image_path):
                    zip_file.write(receipt.image_path, os.path.basename(receipt.image_path))

        zip_buffer.seek(0)

        st.download_button(
            label="📥 Download Images ZIP",
            data=zip_buffer,
            file_name="receipts_images.zip",
            mime="application/zip",
        )

else:
    st.write("No receipts found.")
