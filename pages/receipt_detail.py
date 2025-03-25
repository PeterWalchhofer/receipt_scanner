import streamlit as st
from PIL import Image, ImageOps
from streamlit_pdf_viewer import pdf_viewer
from components.input import get_receipt_inputs
from repository.receipt_repository import ReceiptDB, ReceiptRepository

receipt_repo = ReceiptRepository()

@st.dialog("Delete?")
def delete_dialog():
    st.markdown("Are you sure you want to delete this receipt?")
    if st.button("Yes, delete"):
        receipt_repo.delete_receipt(receipt_id)
        st.success("Receipt deleted successfully!")
        # go to /view_receipts
        st.switch_page("pages/view_receipts.py")

# Read query parameters
query_params = st.query_params
receipt_id = query_params.get("id", None)

if receipt_id:
    receipt = receipt_repo.get_receipt_by_id(receipt_id)
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
                        img = Image.open(file_path)
                        img = ImageOps.exif_transpose(img)
                        st.image(
                            img,
                            caption="Receipt Image",
                            use_container_width=True,
                        )
    with col_2:
        inputs = get_receipt_inputs(receipt, receipt_id)
        col_2_1, col_2_2 = st.columns(2)
        with col_2_1:
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
        with col_2_2:
            if st.button("Delete Receipt", key=f"delete_{receipt_id}"):
                delete_dialog()
