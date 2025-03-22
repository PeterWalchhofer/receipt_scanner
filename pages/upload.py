import json
import os
import random
from datetime import datetime
from pathlib import Path

import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

from components.input import get_receipt_inputs
from models.receipt import Receipt
from receipt_parser.llm import get_prompt, query_openai
from repository.receipt_repository import ReceiptDB, ReceiptRepository


# Initialize session state for extracted data
def init_session_state():
    default_values = {
        "extracted_data": None,
        "receipt_date": "",
        "receipt_number": "",
        "sum_gross": "",
        "sum_net": "",
        "file_paths": [],
        "uploader_key": 0,
        "expanded": {},
    }
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# Dummy Machine Learning Function (as before)
def extract_data_mock(file_paths):
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


def extract_data(file_paths):
    response = query_openai(get_prompt(file_paths))
    json_dict = json.loads(response)
    return json_dict


receipt_repo = ReceiptRepository()

# Directory for saving images
UPLOAD_FOLDER = "saved_images"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Streamlit UI
st.title("Receipt Information Extraction App")
st.write("Upload a receipt image or capture one with your smartphone.")

uploaded_files = st.file_uploader(
    "Choose a receipt image",
    type=["jpg", "jpeg", "png", ".HEIC", "pdf"],
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_key}",
)

if uploaded_files:
    if st.button(
        "Confirm" if not st.session_state.file_paths else "Update", key="confirm"
    ):
        st.session_state.file_paths = []
        for uploaded_file in uploaded_files:
            print("uf", uploaded_file)
            img_name = datetime.now().strftime("%Y%m%d-%H%M%S")
            suffix = Path(uploaded_file.name).suffix
            image_path = os.path.join(
                UPLOAD_FOLDER, f"{img_name}_{random.random() * 20}{suffix}"
            )
            with open(image_path, "wb") as f:
                f.write(uploaded_file.read())

            st.session_state.file_paths.append(image_path)


col_1, col_2 = st.columns(2)
with col_1:
    if st.session_state.file_paths:
        st.subheader("Uploaded Receipt Images")
        columns = st.columns(len(st.session_state.file_paths))
        for i, img_path in enumerate(st.session_state.file_paths):
            if os.path.exists(img_path):
                with columns[i]:
                    if img_path.endswith(".pdf"):
                        pdf_viewer(img_path)
                    else:
                        st.image(img_path, caption=f"Receipt Image {i}")

if st.session_state.file_paths and st.button("Extract Receipt Data"):
    extracted_data = extract_data_mock(st.session_state.file_paths)
    receipt = Receipt(
        **extracted_data, file_paths=st.session_state.file_paths
    )  # Save the image path with the extracted data
    st.session_state.extracted_data = receipt

with col_2:
    # Editable fields for the extracted data
    if st.session_state.extracted_data:
        st.subheader("Edit Extracted Data")
        inputs = get_receipt_inputs(
            ReceiptDB(**st.session_state.extracted_data.__dict__)
        )

        if st.button("Save to Database"):
            # Update the extracted data with user inputs
            updated_receipt = ReceiptDB(
                receipt_number=inputs["receipt_number"],
                date=inputs["receipt_date"],
                total_gross_amount=(inputs["total_gross_amount"]),
                total_net_amount=(inputs["total_net_amount"]),
                vat_amount=(inputs["vat_amount"]),
                company_name=inputs["company_name"],
                description=inputs["description"],
                is_credit=inputs["is_credit"],
                file_paths=st.session_state.file_paths,
                comment=inputs["comment"],
                is_bio=inputs["is_bio"],
            )
            # Save updated receipt to the database
            receipt_repo.create_receipt(updated_receipt)
            st.success("Receipt data saved successfully!")
            # Clear session state after saving
            st.session_state.extracted_data = None
            st.session_state.file_paths = []
            st.session_state.uploader_key += 1
            # reload
            st.rerun()
