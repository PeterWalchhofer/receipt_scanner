import streamlit as st

from models.receipt import ReceiptSource
from repository.receipt_repository import ReceiptDB


def get_receipt_inputs(receipt: ReceiptDB, receipt_id: int = 0):
    # Immutable fields
    st.markdown("### Receipt Details")
    # Set by server
    if hasattr(receipt, "created_on") and hasattr(receipt, "updated_on"):
        st.write(
            f"Created on: {receipt.created_on.strftime('%d.%m.%Y um %H:%M:%S') if receipt.created_on else '-'}"
        )
        st.write(
            f"Updated on: {receipt.updated_on.strftime('%d.%m.%Y um %H:%M:%S') if receipt.updated_on else '-'}"
        )

    # Editable fields
    receipt_number = st.text_input(
        "Receipt Number",
        value=receipt.receipt_number,
        key=f"receipt_number_{receipt_id}",
    )
    receipt_date = st.text_input(
        "Receipt Date", value=receipt.date, key=f"date_{receipt_id}"
    )
    total_gross_amount = st.text_input(
        "Total Gross Amount",
        value=str(receipt.total_gross_amount),
        key=f"gross_{receipt_id}",
    )
    total_net_amount = st.text_input(
        "Total Net Amount",
        value=str(receipt.total_net_amount),
        key=f"net_{receipt_id}",
    )
    vat_amount = st.text_input(
        "VAT Amount", value=str(receipt.vat_amount), key=f"vat_{receipt_id}"
    )
    company_name = st.text_input(
        "Company Name",
        value=receipt.company_name,
        key=f"company_{receipt_id}",
    )
    description = st.text_area(
        "Description",
        value=receipt.description,
        key=f"description_{receipt_id}",
    )
    comment = st.text_area(
        "Comment", key=f"comment_{receipt_id}", value=receipt.comment
    )
    is_bio = st.checkbox("Bio", key=f"bio_{receipt_id}", value=receipt.is_bio)
    is_credit = st.checkbox(
        "Gutschrift", value=receipt.is_credit, key=f"is_credit_{receipt_id}"
    )
    source_options = [e.value for e in ReceiptSource]
    source = st.selectbox(
        "Source",
        options=source_options,
        index=source_options.index(
            getattr(receipt, "source", ReceiptSource.RECEIPT_SCANNER.value)
        ),
        key=f"source_{receipt_id}",
    )

    return {
        "receipt_number": receipt_number,
        "receipt_date": receipt_date,
        "total_gross_amount": total_gross_amount,
        "total_net_amount": total_net_amount,
        "vat_amount": vat_amount,
        "company_name": company_name,
        "description": description,
        "comment": comment,
        "is_bio": is_bio,
        "is_credit": is_credit,
        "source": source,
    }
