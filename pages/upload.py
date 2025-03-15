import os
import random
from datetime import datetime

import streamlit as st
from PIL import Image

from db.database import get_db
from models.receipt import Receipt
from repository.receipt_repository import ReceiptRepository


# Initialize session state for extracted data
def init_session_state():
    default_values = {
        "extracted_data": None,
        "receipt_date": "",
        "receipt_number": "",
        "sum_gross": "",
        "sum_net": "",
        "image_paths": [],
        "uploader_key": 0
    }
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# Dummy Machine Learning Function (as before)
def extract_data(image):
    print("extracted")
    return {
        "receipt_number": "ABC123",
        "date": "2023-03-10",
        "total_gross_amount": 150.00,
        "total_net_amount": 120.00,
        "vat_amount": 30.00,
        "company_name": "XYZ Corp",
        "description": "Product A, Product B",
        "is_credit": False,
    }


# Initialize the database connection
db = next(get_db())
receipt_repo = ReceiptRepository(db)

# Directory for saving images
UPLOAD_FOLDER = "saved_images"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Streamlit UI
st.title("Receipt Information Extraction App")
st.write("Upload a receipt image or capture one with your smartphone.")

uploaded_files = st.file_uploader(
    "Choose a receipt image", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"uploader_{st.session_state.uploader_key}"
)

if uploaded_files:
    # next step button
    if st.button("Confirm" if not st.session_state.image_paths else "Update", key="confirm"):
        st.session_state.image_paths = []
        for uploaded_file in uploaded_files:
            img = Image.open(uploaded_file)
            img_name = datetime.now().strftime("%Y%m%d-%H%M%S")
            image_path = os.path.join(
                UPLOAD_FOLDER, f"{img_name}_{random.random() * 20}.png"
            )
            img.save(image_path)
            st.session_state.image_paths.append(image_path)

if st.session_state.image_paths:
    st.subheader("Uploaded Receipt Images")
    columns = st.columns(len(st.session_state.image_paths))
    for i, img_path in enumerate(st.session_state.image_paths):
        if os.path.exists(img_path):
            with columns[i]:
                img = Image.open(img_path)
                st.image(img, caption=f"Receipt Image {i}")

if st.session_state.image_paths and st.button("Extract Receipt Data"):
    extracted_data = extract_data(st.session_state.image_paths)
    receipt = Receipt(
        **extracted_data, image_paths=st.session_state.image_paths
    )  # Save the image path with the extracted data
    st.session_state.extracted_data = receipt

# Editable fields for the extracted data
if st.session_state.extracted_data:
    st.subheader("Edit Extracted Data")
    receipt = st.session_state.extracted_data

    # Make the data editable
    receipt_number = st.text_input("Receipt Number", value=receipt.receipt_number)
    receipt_date = st.text_input("Receipt Date", value=receipt.date)
    total_gross_amount = st.text_input(
        "Total Gross Amount", value=str(receipt.total_gross_amount)
    )
    total_net_amount = st.text_input(
        "Total Net Amount", value=str(receipt.total_net_amount)
    )
    vat_amount = st.text_input("VAT Amount", value=str(receipt.vat_amount))
    company_name = st.text_input("Company Name", value=receipt.company_name)
    description = st.text_area("Description", value=receipt.description)
    is_credit = st.checkbox("Is Credit", value=receipt.is_credit)

    if st.button("Save to Database"):
        # Update the extracted data with user inputs
        updated_receipt = Receipt(
            receipt_number=receipt_number,
            date=receipt_date,
            total_gross_amount=float(total_gross_amount),
            total_net_amount=float(total_net_amount),
            vat_amount=float(vat_amount),
            company_name=company_name,
            description=description,
            is_credit=is_credit,
            image_paths=receipt.image_paths,
        )
        # Save updated receipt to the database
        receipt_repo.create_receipt(updated_receipt.dict())
        st.success("Receipt data saved successfully!")
        # Clear session state after saving
        st.session_state.extracted_data = None
        st.session_state.image_paths = []
        st.session_state.uploader_key += 1
        # reload
        st.rerun()
