import streamlit as st
from repository.receipt_repository import ProductDB, SessionLocal
from components.input import get_product_inputs

def product_grid_ui(receipt_id, is_bio, products=None, prefix="", show_price=True):
    """
    Render a grid UI for adding and editing products for a given receipt.
    Args:
        receipt_id: ID of the related receipt
        is_bio: bool, default value for is_bio
        products: list of ProductDB objects
        prefix: str, prefix for Streamlit keys
        show_price: bool, whether to show the price input
    Returns:
        None (handles add/edit/delete via Streamlit forms)
    """
    if products is None:
        products = []
    max_cols = 4
    total_products = len(products) + 1  # +1 for the add form
    rows = (total_products + max_cols - 1) // max_cols
    for row in range(rows):
        row_items = []
        for col in range(max_cols):
            grid_idx = row * max_cols + col
            if grid_idx == 0:
                row_items.append("add_form")
            elif grid_idx - 1 < len(products):
                row_items.append(products[grid_idx - 1])
            else:
                row_items.append(None)
        cols = st.columns(max_cols)
        for col, item in zip(cols, row_items):
            with col:
                if item == "add_form":
                    with st.form(f"{prefix}add_product_form"):
                        st.subheader("Add New Product")
                        product_inputs = get_product_inputs(
                            product=None,
                            default_is_bio=is_bio,
                            prefix=f"{prefix}add_",
                            show_price=show_price,
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
                    with st.form(f"{prefix}edit_product_{item.id}"):
                        st.subheader("Edit Product")
                        product_inputs = get_product_inputs(
                            product=item,
                            prefix=f"{prefix}edit_{item.id}_",
                            show_price=show_price,
                        )
                        col_save, col_delete = st.columns(2)
                        with col_save:
                            if st.form_submit_button("Save Product"):
                                with SessionLocal() as session:
                                    prod = session.query(ProductDB).get(item.id)
                                    if prod:
                                        prod.name = product_inputs["name"]
                                        prod.is_bio = product_inputs["is_bio"]
                                        prod.bio_category = product_inputs["bio_category"]
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
