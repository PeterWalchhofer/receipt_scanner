"""
Sortiment Management Page

Manage product classes (sortiment) that are used for product classification.
View, add, and edit sortiment records with regex pattern counts.
"""

import streamlit as st

from components.product_classification import get_sortiment_with_regex_count
from repository.receipt_repository import SortimentDB, SessionLocal


def sortiment_page():
    """Main sortiment management page."""
    st.title("📦 Sortiment Management")
    st.write("Manage product classes and their associated regex patterns.")
    
    # Initialize session state for editing
    if "editing_sortiment_id" not in st.session_state:
        st.session_state.editing_sortiment_id = None
    if "editing_sortiment_name" not in st.session_state:
        st.session_state.editing_sortiment_name = None
    
    # Add new sortiment form
    with st.form("add_sortiment_form"):
        st.subheader("Add New Product Class")
        new_name = st.text_input("Product Class Name", placeholder="e.g., Bergk(ä|a)s")
        
        if st.form_submit_button("Add Product Class", icon="➕"):
            if not new_name.strip():
                st.error("Product class name cannot be empty")
            else:
                with SessionLocal() as session:
                    # Check if name already exists
                    existing = (
                        session.query(SortimentDB)
                        .filter(SortimentDB.name == new_name.strip())
                        .first()
                    )
                    if existing:
                        st.error(f"Product class '{new_name}' already exists")
                    else:
                        new_sortiment = SortimentDB(name=new_name.strip())
                        session.add(new_sortiment)
                        session.commit()
                        st.success(f"Product class '{new_name}' added!")
                        st.rerun()
    
    st.divider()
    
    # Display existing sortiments
    st.subheader("Existing Product Classes")
    sortiments = get_sortiment_with_regex_count()
    
    if not sortiments:
        st.info("No product classes created yet. Add one above to get started.")
    else:
        # Create a grid layout for sortiments
        cols = st.columns([3, 1, 1, 1, 1])
        with cols[0]:
            st.write("**Name**")
        with cols[1]:
            st.write("**Regexes**")
        with cols[2]:
            st.write("**Created**")
        with cols[3]:
            st.write("**Actions**")
        with cols[4]:
            st.write("")
        
        st.divider()
        
        for sortiment in sortiments:
            cols = st.columns([3, 1, 1, 1, 1])
            
            with cols[0]:
                st.write(sortiment["name"])
            
            with cols[1]:
                st.write(str(sortiment["regex_count"]))
            
            with cols[2]:
                created = sortiment["created_on"]
                date_str = created.strftime("%Y-%m-%d") if created else "N/A"
                st.write(date_str)
            
            with cols[3]:
                if st.button("Edit", key=f"edit_{sortiment['id']}", use_container_width=True):
                    st.session_state.editing_sortiment_id = sortiment['id']
                    st.session_state.editing_sortiment_name = sortiment['name']
            
            with cols[4]:
                if st.button("Delete", key=f"delete_{sortiment['id']}", use_container_width=True):
                    with SessionLocal() as session:
                        sortiment_obj = (
                            session.query(SortimentDB)
                            .filter(SortimentDB.id == sortiment["id"])
                            .first()
                        )
                        if sortiment_obj:
                            session.delete(sortiment_obj)
                            session.commit()
                            st.success("Product class deleted!")
                            st.rerun()
        
        # Show edit form if editing
        if st.session_state.editing_sortiment_id:
            st.divider()
            st.subheader("✏️ Edit Product Class")
            with st.form("edit_sortiment_form"):
                new_name = st.text_input(
                    "Product Class Name",
                    value=st.session_state.editing_sortiment_name,
                    placeholder="e.g., Bergk(ä|a)s",
                )
                col1, col2 = st.columns(2)
                with col1:
                    save_btn = st.form_submit_button("Save Changes", icon="💾")
                with col2:
                    cancel_btn = st.form_submit_button("Cancel", icon="❌")
                
                if save_btn:
                    if not new_name.strip():
                        st.error("Product class name cannot be empty")
                    else:
                        with SessionLocal() as session:
                            # Check if name already exists (but not the current one)
                            existing = (
                                session.query(SortimentDB)
                                .filter(
                                    SortimentDB.name == new_name.strip(),
                                    SortimentDB.id != st.session_state.editing_sortiment_id,
                                )
                                .first()
                            )
                            if existing:
                                st.error(f"Product class '{new_name}' already exists")
                            else:
                                sortiment_obj = (
                                    session.query(SortimentDB)
                                    .filter(SortimentDB.id == st.session_state.editing_sortiment_id)
                                    .first()
                                )
                                if sortiment_obj:
                                    sortiment_obj.name = new_name.strip()
                                    session.commit()
                                    st.success("Product class updated!")
                                    st.session_state.editing_sortiment_id = None
                                    st.session_state.editing_sortiment_name = None
                                    st.rerun()
                
                if cancel_btn:
                    st.session_state.editing_sortiment_id = None
                    st.session_state.editing_sortiment_name = None
                    st.rerun()


if __name__ == "__main__":
    sortiment_page()
