import json

import streamlit as st
from PIL import Image, ImageOps
from streamlit_pdf_viewer import pdf_viewer

from components.input import get_receipt_inputs
from components.product_grid import product_grid_ui
from models.product import BioCategory, ProductUnit
from models.receipt import Receipt
from pages.upload import extract_data
from receipt_parser.llm import Prompt
from repository.receipt_repository import (
    ProductDB,
    ReceiptDB,
    ReceiptRepository,
    SessionLocal,
)

receipt_repo = ReceiptRepository()


@st.dialog("Delete?")
def delete_dialog():
    st.markdown("Are you sure you want to delete this receipt?")
    if st.button("Yes, delete"):
        if receipt_id is not None:
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
        if (
            receipt
            and receipt.file_paths is not None
        ):
            # SQLAlchemy may return a JSON column as a string, so parse if needed
            file_paths = receipt.file_paths
            if isinstance(file_paths, str):
                try:
                    file_paths = json.loads(file_paths)
                except Exception:
                    file_paths = []
            if not isinstance(file_paths, list):
                file_paths = []
            st.markdown("### Receipt Images")
            columns = st.columns(len(file_paths))
            for i, file_path in enumerate(file_paths):
                with columns[i]:
                    if file_path.endswith(".pdf"):
                        pdf_viewer(file_path)
                    else:
                        try:
                            img = Image.open(file_path)
                            img = ImageOps.exif_transpose(img)
                            if img is not None:
                                st.image(
                                    img,
                                    caption="Receipt Image",
                                    use_container_width=True,
                                )
                        except Exception:
                            st.warning(f"Could not load image: {file_path}")
    with col_2:
        inputs = get_receipt_inputs(
            receipt, receipt_id if receipt_id is not None else 0
        )
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
                    source=inputs["source"],
                )
                receipt_repo.update_receipt(receipt_id, updated_receipt)
                st.success("Changes saved successfully!")
                st.rerun()
        with col_2_2:
            if st.button("Delete Receipt", key=f"delete_{receipt_id}"):
                delete_dialog()


# --- Product Management Section ---
st.markdown("---")
st.subheader("Products")
# Only show product UI for relevant receipts
show_products = receipt.should_have_products()
if not show_products:
    st.warning(
        "Produkt nur für Bioausgaben und Kaseinnahmen. Drücke Rechnung speichern, falls du die Angabe aktualisiert hast."
    )

if show_products:
    with SessionLocal() as session:
        products = (
            session.query(ProductDB).filter(ProductDB.receipt_id == receipt_id).all()
        )
    if not products:
        if st.button("Extract Products"):
            extracted_data = extract_data(
                receipt.file_paths, Prompt.PRODUCTS_ONLY, None
            )
            receipt = Receipt(**extracted_data)
            products = receipt.products
            if products:
                for p in products:
                    p_db = ProductDB(
                        receipt_id=receipt_id,
                        name=p.name,
                        amount=p.amount,
                        price=p.price,
                        is_bio=inputs["is_bio"],
                        unit=p.unit,
                        bio_category=p.bio_category,
                    )
                    with SessionLocal() as session:
                        session.add(p_db)
                        session.commit()

                st.rerun()
    product_grid_ui(
        receipt_id=receipt_id,
        is_bio=inputs["is_bio"],
        products=products,
        prefix="detail_",
        show_price=True,
    )
