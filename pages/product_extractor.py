import pandas as pd
import streamlit as st

from models.product import BioCategory, ProductUnit
from repository.receipt_repository import ProductDB, ReceiptRepository, SessionLocal

st.title("🧀 Product Extraction & Categorization")

# Filter options
type_options = [
    ("Marktwagen", "company_name", "Marktwagen"),
    ("Kemmts Eina", "company_name", "Kemmts Eina"),
    ("Hofladen", "company_name", "Hofladen"),
    ("Lieferungen (RECHNUNGSAPP)", "source", "RECHNUNGSAPP"),
]

selected_type = st.selectbox(
    "Select receipt type to filter:", [t[0] for t in type_options]
)

# Get filter
filter_col, filter_val = [t[1:] for t in type_options if t[0] == selected_type][0]

receipt_repo = ReceiptRepository()
receipts = receipt_repo.get_all_receipts()
df = pd.DataFrame([r.__dict__ for r in receipts])
if "_sa_instance_state" in df.columns:
    df = df.drop("_sa_instance_state", axis=1)

# Filter
df_filtered = df[df[filter_col] == filter_val]

st.write(f"Filtered receipts for: {selected_type}")
st.dataframe(df_filtered)

# Row selection and popup (Streamlit workaround: use expander for now)
if len(df_filtered) > 0:
    for idx, row in df_filtered.iterrows():
        with st.expander(
            f"Extract products for receipt {row['receipt_number']} (ID: {row['id']})"
        ):
            st.write("### Receipt File(s)")
            if isinstance(row["file_paths"], list):
                for f in row["file_paths"]:
                    if f.lower().endswith(".pdf"):
                        st.write(f"PDF: {f}")
                    else:
                        st.image(f, caption=f)
            else:
                st.write(row["file_paths"])
            st.write("---")
            st.write("#### Extraction Prompt (edit as needed):")
            st.code(
                """Here you have a receipt of the cheese i sold. Please extract each type of cheese, the weight (kilos), in case it is sold per kilo, or simply the quantity. The format of the data on the sheet  is:
| product name| quantity | price.
Please emit a list of json files of the following DTO:
product = {
    receipt_id: int
    product_name: string,
    quanity: float
    unit: KILO | PIECE
    price: float
}
""",
                language="markdown",
            )
            # Editable product table
            with SessionLocal() as session:
                products = (
                    session.query(ProductDB)
                    .filter(ProductDB.receipt_id == row["id"])
                    .all()
                )
            if products:
                st.write("#### Existing Products (edit and save):")
                for p in products:
                    with st.form(f"edit_product_{p.id}"):
                        name = st.text_input("Product Name", value=p.name)
                        is_bio = st.checkbox("Bio", value=p.is_bio)
                        bio_category = None
                        if is_bio:
                            bio_category = st.selectbox(
                                "Bio Category",
                                [None] + [e.value for e in BioCategory],
                                index=([None] + [e.value for e in BioCategory]).index(
                                    p.bio_category
                                )
                                if p.bio_category
                                else 0,
                            )
                        amount = st.number_input("Amount", value=p.amount, step=0.01)
                        unit = st.selectbox(
                            "Unit",
                            [e.value for e in ProductUnit],
                            index=[e.value for e in ProductUnit].index(p.unit),
                        )
                        if st.form_submit_button("Save Product"):
                            with SessionLocal() as session:
                                prod = session.query(ProductDB).get(p.id)
                                prod.name = name
                                prod.is_bio = is_bio
                                prod.bio_category = bio_category if is_bio else None
                                prod.amount = amount
                                prod.unit = unit
                                session.commit()
                            st.success("Product updated!")
                            st.experimental_rerun()
            else:
                st.info("No products extracted yet for this receipt.")
            st.button("Start Extraction (not implemented)")


# Skeleton for mapping function
def map_product_name(raw_name: str, source: str) -> str:
    """Map raw product names to normalized names depending on the source."""
    # TODO: Implement mapping logic per source
    return raw_name
