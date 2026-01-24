"""
Product Reference Tool Page

Manage regex patterns for product classification.
Test regex patterns against products and batch assign them to product classes.
"""

import re

import pandas as pd
import streamlit as st

from components.product_classification import (
    assign_product_class,
    get_unclassified_products,
    match_regex_to_products,
)
from repository.receipt_repository import ProductDB, RegexDB, SessionLocal, SortimentDB


def product_reference_page():
    """Main product reference tool page."""
    st.title("🔗 Product Reference Tool")
    st.write(
        "Manage regex patterns for product classification. Match products to product classes."
    )
    
    # Initialize session state for regex testing
    if "test_regex_results" not in st.session_state:
        st.session_state.test_regex_results = None
    if "test_regex_pattern" not in st.session_state:
        st.session_state.test_regex_pattern = None
    
    # Sidebar: sortiment selector
    st.sidebar.subheader("Product Classes")
    with SessionLocal() as session:
        sortiments = session.query(SortimentDB).order_by(SortimentDB.name).all()
        sortiment_map = {s.id: s.name for s in sortiments}
    
    if not sortiments:
        st.warning("No product classes found. Create some in the Sortiment page first.")
        return
    
    selected_sortiment_id = st.sidebar.selectbox(
        "Select Product Class",
        options=[s.id for s in sortiments],
        format_func=lambda x: sortiment_map[x],
    )
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Regex List", "Add Regex", "Batch Assign", "Reset"])
    
    # TAB 1: Regex List
    with tab1:
        st.subheader("Regex Patterns")
        with SessionLocal() as session:
            regexes = (
                session.query(RegexDB)
                .filter(RegexDB.product_class_id == selected_sortiment_id)
                .all()
            )
        
        if not regexes:
            st.info(
                f"No regex patterns for '{sortiment_map[selected_sortiment_id]}'. "
                "Add one in the 'Add Regex' tab."
            )
        else:
            for regex_obj in regexes:
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.code(regex_obj.regex, language="regex")
                with col2:
                    if st.button(
                        "Test",
                        key=f"test_{regex_obj.id}",
                        help="Test this regex against unclassified products",
                    ):
                        # Test regex and show results
                        unclassified = get_unclassified_products()
                        matches = match_regex_to_products(regex_obj.regex, unclassified)
                        st.session_state.test_regex_results = matches
                        st.session_state.test_regex_pattern = regex_obj.regex
                with col3:
                    if st.button("Edit", key=f"edit_regex_{regex_obj.id}"):
                        st.session_state.editing_regex_id = regex_obj.id
                        st.session_state.editing_regex_pattern = regex_obj.regex
                with col4:
                    if st.button("Delete", key=f"delete_regex_{regex_obj.id}"):
                        with SessionLocal() as session:
                            regex_to_delete = (
                                session.query(RegexDB)
                                .filter(RegexDB.id == regex_obj.id)
                                .first()
                            )
                            if regex_to_delete:
                                session.delete(regex_to_delete)
                                session.commit()
                                st.success("Regex deleted!")
                                st.rerun()
            
            # Show edit form if editing
            if st.session_state.get("editing_regex_id"):
                st.divider()
                st.subheader("✏️ Edit Regex Pattern")
                with st.form("edit_regex_form"):
                    new_pattern = st.text_area(
                        "Updated Regex Pattern",
                        value=st.session_state.editing_regex_pattern,
                        height=100,
                    )
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        test_btn = st.form_submit_button("Test Updated Pattern", icon="🧪")
                    with col2:
                        save_btn = st.form_submit_button("Save Changes", icon="💾")
                    with col3:
                        cancel_btn = st.form_submit_button("Cancel", icon="❌")
                    
                    if test_btn:
                        if not new_pattern.strip():
                            st.error("Regex pattern cannot be empty")
                        else:
                            try:
                                unclassified = get_unclassified_products()
                                matches = match_regex_to_products(new_pattern, unclassified)
                                st.session_state.test_regex_results = matches
                                st.session_state.test_regex_pattern = new_pattern
                                st.info(f"Updated pattern matches {len(matches)} products")
                            except re.error as e:
                                st.error(f"Invalid regex: {e}")
                    
                    if save_btn:
                        if not new_pattern.strip():
                            st.error("Regex pattern cannot be empty")
                        else:
                            try:
                                # Validate regex
                                re.compile(new_pattern)
                                with SessionLocal() as session:
                                    regex_to_update = (
                                        session.query(RegexDB)
                                        .filter(RegexDB.id == st.session_state.editing_regex_id)
                                        .first()
                                    )
                                    if regex_to_update:
                                        regex_to_update.regex = new_pattern.strip()
                                        session.commit()
                                        st.success("Regex pattern updated!")
                                        st.session_state.editing_regex_id = None
                                        st.session_state.editing_regex_pattern = None
                                        st.rerun()
                            except re.error as e:
                                st.error(f"Invalid regex pattern: {e}")
                    
                    if cancel_btn:
                        st.session_state.editing_regex_id = None
                        st.session_state.editing_regex_pattern = None
                        st.rerun()
            
            # Show test results if available
            if st.session_state.test_regex_results is not None:
                st.divider()
                st.subheader("Test Results")
                results = st.session_state.test_regex_results
                st.info(f"Found {len(results)} matching products")
                
                if results:
                    df = pd.DataFrame([
                        {
                            "Product Name": p.name,
                            "Amount": p.amount,
                            "Unit": p.unit.value if p.unit else "N/A",
                            "Price": p.price or 0,
                        }
                        for p in results
                    ])
                    st.dataframe(df, use_container_width=True)
    
    # TAB 2: Add Regex
    with tab2:
        st.subheader(f"Add Regex for '{sortiment_map[selected_sortiment_id]}'")
        st.info(f"🎯 **Currently editing**: {sortiment_map[selected_sortiment_id]} — Change in sidebar if needed")
        with st.form("add_regex_form"):
            regex_pattern = st.text_area(
                "Regex Pattern",
                placeholder="e.g., ^bergkäse|käse.*butter",
                height=100,
            )
            col1, col2 = st.columns(2)
            with col1:
                test_btn = st.form_submit_button("Test Pattern", icon="🧪")
            with col2:
                add_btn = st.form_submit_button("Add Regex", icon="➕")
            
            if test_btn:
                if not regex_pattern.strip():
                    st.error("Regex pattern cannot be empty")
                else:
                    try:
                        unclassified = get_unclassified_products()
                        matches = match_regex_to_products(regex_pattern, unclassified)
                        st.session_state.test_regex_results = matches
                        st.session_state.test_regex_pattern = regex_pattern
                        st.info(f"Pattern matched {len(matches)} products")
                    except re.error as e:
                        st.error(f"Invalid regex: {e}")
            
            if add_btn:
                if not regex_pattern.strip():
                    st.error("Regex pattern cannot be empty")
                else:
                    try:
                        # Validate regex
                        re.compile(regex_pattern)
                        with SessionLocal() as session:
                            new_regex = RegexDB(
                                regex=regex_pattern.strip(),
                                product_class_id=selected_sortiment_id,
                            )
                            session.add(new_regex)
                            session.commit()
                            st.success("Regex pattern added!")
                            st.rerun()
                    except re.error as e:
                        st.error(f"Invalid regex pattern: {e}")
        
        # Show test results
        if st.session_state.test_regex_results is not None:
            st.divider()
            st.subheader("Test Results")
            results = st.session_state.test_regex_results
            st.info(f"Pattern '{st.session_state.test_regex_pattern}' matched {len(results)} products")
            
            if results:
                df = pd.DataFrame([
                    {
                        "Product Name": p.name,
                        "Amount": p.amount,
                        "Unit": p.unit.value if p.unit else "N/A",
                        "Price": p.price or 0,
                    }
                    for p in results
                ])
                st.dataframe(df, use_container_width=True)
    
    # TAB 3: Batch Assign
    with tab3:
        st.subheader("Batch Assign Products to Product Class")
        
        # Get all regexes for selected sortiment
        with SessionLocal() as session:
            regexes = (
                session.query(RegexDB)
                .filter(RegexDB.product_class_id == selected_sortiment_id)
                .all()
            )
        
        if not regexes:
            st.warning(
                f"No regex patterns for '{sortiment_map[selected_sortiment_id]}'. "
                "Add some in the 'Add Regex' tab first."
            )
        else:
            # Get all unclassified products
            unclassified = get_unclassified_products()
            st.info(f"Total unclassified products: {len(unclassified)}")
            
            # Show preview of matching products
            st.subheader("Products that match this product class's regexes:")
            
            all_matches = []
            for regex_obj in regexes:
                matches = match_regex_to_products(regex_obj.regex, unclassified)
                all_matches.extend(matches)
            
            # Remove duplicates (a product might match multiple regexes)
            unique_matches = list({p.id: p for p in all_matches}.values())
            
            if not unique_matches:
                st.info("No products match the regex patterns for this product class.")
            else:
                df = pd.DataFrame([
                    {
                        "Product Name": p.name,
                        "Amount": p.amount,
                        "Unit": p.unit.value if p.unit else "N/A",
                        "Price": p.price or 0,
                        "Receipt ID": p.receipt_id[:8] + "...",
                    }
                    for p in unique_matches
                ])
                st.dataframe(df, use_container_width=True)
                
                # Apply button
                if st.button(
                    f"✅ Assign {len(unique_matches)} Products",
                    use_container_width=True,
                    type="primary",
                ):
                    product_ids = [p.id for p in unique_matches]
                    updated_count = assign_product_class(
                        product_ids, selected_sortiment_id
                    )
                    st.success(
                        f"✅ Assigned {updated_count} products to "
                        f"'{sortiment_map[selected_sortiment_id]}'"
                    )
                    st.rerun()
    
    # TAB 4: Reset Classifications
    with tab4:
        st.subheader("🔄 Reset Classifications")
        st.warning("⚠️ Be careful! Resetting will unassign products from their product classes.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Reset Single Product Class")
            st.write(f"Unassign all products from: **{sortiment_map[selected_sortiment_id]}**")
            if st.button(
                f"Reset '{sortiment_map[selected_sortiment_id]}' Only",
                key="reset_single_class",
                type="secondary",
                use_container_width=True,
            ):
                with SessionLocal() as session:
                    updated = (
                        session.query(ProductDB)
                        .filter(ProductDB.product_class_reference == selected_sortiment_id)
                        .update({ProductDB.product_class_reference: None})
                    )
                    session.commit()
                    st.success(
                        f"✅ Unassigned {updated} products from "
                        f"'{sortiment_map[selected_sortiment_id]}'"
                    )
                    st.rerun()
        
        with col2:
            st.subheader("Reset All Classifications")
            st.write("Unassign ALL products from ALL product classes")
            if st.button(
                "Reset Everything",
                key="reset_all_classes",
                type="secondary",
                use_container_width=True,
            ):
                with SessionLocal() as session:
                    updated = (
                        session.query(ProductDB)
                        .update({ProductDB.product_class_reference: None})
                    )
                    session.commit()
                    st.success(f"✅ Unassigned {updated} products from all classes")
                    st.rerun()
        
        st.divider()
        st.subheader("Classification Status")
        with SessionLocal() as session:
            total_products = session.query(ProductDB).count()
            classified = (
                session.query(ProductDB)
                .filter(ProductDB.product_class_reference.isnot(None))
                .count()
            )
            unclassified = total_products - classified
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Products", total_products)
        with col2:
            st.metric("Classified", classified)
        with col3:
            st.metric("Unclassified", unclassified)


if __name__ == "__main__":
    product_reference_page()
