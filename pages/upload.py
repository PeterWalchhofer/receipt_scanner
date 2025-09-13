import json
import os
import random
from datetime import datetime
from enum import Enum
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps
from streamlit_pdf_viewer import pdf_viewer

from components.input import get_receipt_inputs
from components.product_db_ops import get_products_for_receipt
from components.product_grid import product_grid_ui
from models.receipt import Receipt
from receipt_parser.llm import Prompt, get_prompt, query_openai
from repository.receipt_repository import (
    ProductDB,
    ReceiptDB,
    ReceiptRepository,
    SessionLocal,
)


# Initialize session state for extracted data
def init_session_state():
    default_values = {
        "extracted_data": None,
        "products": None,
        "created_receipt": None,
        "receipt_date": "",
        "receipt_number": "",
        "sum_gross": "",
        "sum_net": "",
        "file_paths": [],
        "uploader_key": 0,
        "expanded": {},
        "prompt": Prompt.DEFAULT,
    }
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# Dummy Machine Learning Function (as before)
def extract_data_mock(file_paths, prompt_type, custom_prompt=None):
    print("extracted")
    return {
        "receipt_number": "ABC123",
        "date": "2023-03-10",
        "total_gross_amount": 150.00,
        "total_net_amount": 120.00,
        "vat_amount": 30.00,
        "company_name": "XYZ Corp",
        "description": f"Number of items: {len(file_paths)}\n Prompt Type: {prompt_type}\n Custom Prompt: {custom_prompt}",
        "is_credit": False,
    }


def extract_data(file_paths, prompt_type, custom_prompt=None):
    response = query_openai(get_prompt(file_paths, prompt_type, custom_prompt))
    try:
        json_dict = json.loads(response)
    except json.JSONDecodeError:
        print("Failed to decode JSON response", response)
        return {}
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
    type=["jpg", "jpeg", "png", ".HEIC", "pdf", ".PDF"],
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
                        img = Image.open(img_path)
                        img = ImageOps.exif_transpose(img)
                        st.image(img_path, caption=f"Receipt Image {i}")

custom_prompt = None
if st.session_state.file_paths:
    receipt_type = st.pills(
        "Receipt Type",
        options=[prompt.value for prompt in Prompt],
        key="prompt",
        default=Prompt.DEFAULT.value,
    )
    if receipt_type == Prompt.CUSTOM.value:
        custom_prompt = st.text_area(
            "Custom Prompt",
            value="You are an expert receipt extraction algorithm. Only extract relevant information from the text. If you do not know the value of an attribute asked to extract, return null for the attribute's value.",
            key="custom_prompt",
        )

if st.session_state.file_paths and st.button("Extract Receipt Data"):
    extracted_data = extract_data(
        st.session_state.file_paths, Prompt(receipt_type), custom_prompt
    )
    receipt = Receipt(**extracted_data)  # Save the image path with the extracted data
    st.session_state.extracted_data = receipt
    st.session_state.products = receipt.products
    print(">>>>>>>>>")
    print("products", st.session_state.products)

with col_2:
    # Editable fields for the extracted data
    if st.session_state.extracted_data:
        st.subheader("Edit Extracted Data")

        inputs = get_receipt_inputs(
            ReceiptDB(
                receipt_number=st.session_state.extracted_data.receipt_number,
                date=st.session_state.extracted_data.date,
                total_gross_amount=st.session_state.extracted_data.total_gross_amount,
                total_net_amount=st.session_state.extracted_data.total_net_amount,
                vat_amount=st.session_state.extracted_data.vat_amount,
                company_name=st.session_state.extracted_data.company_name,
                description=st.session_state.extracted_data.description,
                is_credit=st.session_state.extracted_data.is_credit,
                file_paths=st.session_state.file_paths,
            )
        )
        allow_products_unsaved = (
            not st.session_state.created_receipt
            and (inputs["is_bio"] and not inputs["is_credit"])
            or (
                inputs["is_credit"]
                and inputs["company_name"] in ["Kemmts Eina", "Marktwagen", "Hofladen"]
            )
        )
        if allow_products_unsaved:
            st.badge("To add products save first", icon="ℹ️")

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
            created_receipt = receipt_repo.create_receipt(updated_receipt)
            st.session_state.created_receipt = created_receipt
            # Save extracted products to DB if any
            if st.session_state.products:
                for p in st.session_state.products:
                    p_db = ProductDB(
                        receipt_id=created_receipt.id,
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
            st.session_state.products = None  # Clear extracted products after saving
            st.success("Receipt data saved successfully!")

created_receipt = st.session_state.created_receipt
allow_products = created_receipt and created_receipt.should_have_products()

if allow_products and created_receipt:
    st.markdown("---")
    st.subheader("Products")
    # Only show products from DB after save
    products_db = get_products_for_receipt(created_receipt.id)
    product_grid_ui(
        receipt_id=created_receipt.id,
        is_bio=created_receipt.is_bio,
        products=products_db,
        prefix="upload_",
        show_price=True,
    )

if (created_receipt and not allow_products) or (
    created_receipt and st.button("Upload new receipt")
):
    # Clear session state after saving
    st.session_state.extracted_data = None
    st.session_state.products = None
    st.session_state.file_paths = []
    st.session_state.created_receipt = None
    st.session_state.uploader_key += 1
    # reload
    st.rerun()
