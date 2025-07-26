import streamlit as st
from PIL import Image, ImageOps
from streamlit_pdf_viewer import pdf_viewer

from components.input import get_product_inputs, get_receipt_inputs
from models.product import BioCategory, ProductUnit
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
            and hasattr(receipt, "file_paths")
            and receipt.file_paths is not None
        ):
            # SQLAlchemy may return a JSON column as a string, so parse if needed
            import json

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
                    file_paths=getattr(receipt, "file_paths", []),
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
show_products = (
    receipt
    and (receipt.is_bio and not receipt.is_credit)
    or (
        receipt.is_credit
        and receipt.company_name in ["Hofladen", "Kemmts Eina", "Wochenmarkt"]
    )
)
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
        st.write("No products found for this receipt.")
    # Display add new product form in the first cell of the grid, then existing products
    max_cols = 4
    total_products = len(products) + 1  # +1 for the add form
    rows = (total_products + max_cols - 1) // max_cols
    product_idx = 0
    for row in range(rows):
        row_items = []
        for col in range(max_cols):
            grid_idx = row * max_cols + col
            if grid_idx == 0:
                # Add New Product form in the first cell
                row_items.append("add_form")
            elif grid_idx - 1 < len(products):
                row_items.append(products[grid_idx - 1])
            else:
                row_items.append(None)
        cols = st.columns(max_cols)
        for col, item in zip(cols, row_items):
            with col:
                if item == "add_form":
                    with st.form("add_product_form"):
                        st.subheader("Add New Product")
                        product_inputs = get_product_inputs(
                            product=None,
                            default_is_bio=inputs["is_bio"],
                            prefix="add_",
                            show_price=True,
                        )
                        if st.form_submit_button("Add Product", icon="➕"):
                            with SessionLocal() as session:
                                new_product = ProductDB(
                                    receipt_id=str(receipt_id),
                                    name=product_inputs["name"],
                                    is_bio=product_inputs["is_bio"],
                                    bio_category=product_inputs["bio_category"],
                                    amount=product_inputs["amount"],
                                    unit=product_inputs["unit"],
                                    price=product_inputs["price"],
                                )
                                session.add(new_product)
                                session.commit()
                            st.success("Product added!")
                            st.rerun()
                elif item is not None:
                    with st.form(f"edit_product_{item.id}"):
                        st.subheader(f"Edit Product: {row + 1}")
                        product_inputs = get_product_inputs(
                            product=item,
                            prefix=f"edit_{item.id}_",
                            show_price=True,
                        )
                        col_save, col_delete = st.columns(2)
                        with col_save:
                            if st.form_submit_button("Save Product"):
                                with SessionLocal() as session:
                                    prod = session.query(ProductDB).get(item.id)
                                    if prod:
                                        prod.name = product_inputs["name"]
                                        prod.is_bio = product_inputs["is_bio"]
                                        prod.bio_category = product_inputs[
                                            "bio_category"
                                        ]
                                        prod.amount = product_inputs["amount"]
                                        prod.unit = product_inputs["unit"]
                                        prod.price = product_inputs["price"]
                                        session.commit()
                                st.success("Product updated!")
                                st.rerun()
                        with col_delete:
                            if st.form_submit_button("Delete Product"):
                                with SessionLocal() as session:
                                    prod = session.query(ProductDB).get(item.id)
                                    if prod:
                                        session.delete(prod)
                                        session.commit()
                                st.success("Product deleted!")
                                st.rerun()
