import streamlit as st
import sqlite3
from PIL import Image

# --- Dummy Machine Learning Function ---
def extract_data(image):
    """
    Dummy function to simulate ML-based extraction.
    """
    return {
        "receipt_date": "2023-03-10",
        "receipt_number": "ABC123",
        "sum_gross": "150.00",
        "sum_net": "120.00"
    }

# --- SQLite Database Functions ---
def save_to_db(data):
    conn = sqlite3.connect("receipts.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_date TEXT,
            receipt_number TEXT,
            sum_gross TEXT,
            sum_net TEXT
        )
    """)
    cursor.execute(
        "INSERT INTO receipts (receipt_date, receipt_number, sum_gross, sum_net) VALUES (?, ?, ?, ?)",
        (data["receipt_date"], data["receipt_number"], data["sum_gross"], data["sum_net"])
    )
    conn.commit()
    conn.close()

# --- Initialize Session State Variables ---
def init_session_state():
    default_values = {"extracted_data": None, "image": None, "receipt_date": "", "receipt_number": "", "sum_gross": "", "sum_net": ""}
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- Streamlit Application UI ---
st.title("Receipt Information Extraction App")

st.write("Upload a receipt image or capture one with your smartphone.")

col1, col2 = st.columns(2)

with col1:
    st.header("Upload Image")
    uploaded_file = st.file_uploader("Choose a receipt image", type=["jpg", "jpeg", "png"])

with col2:
    st.header("Capture Image")
    camera_image = st.camera_input("Take a photo of the receipt")

if uploaded_file is not None:
    st.session_state.image = Image.open(uploaded_file)
elif camera_image is not None:
    st.session_state.image = Image.open(camera_image)

if st.session_state.image is not None:
    st.image(st.session_state.image, caption="Receipt Image", use_container_width=True)
    if st.button("Extract Receipt Data"):
        extracted_data = extract_data(st.session_state.image)
        st.session_state.extracted_data = extracted_data

if st.session_state.extracted_data is not None:
    st.subheader("Extracted Data")
    receipt_date = st.text_input("Receipt Date", value=st.session_state.extracted_data["receipt_date"], key="receipt_date_input")
    receipt_number = st.text_input("Receipt Number", value=st.session_state.extracted_data["receipt_number"], key="receipt_number_input")
    sum_gross = st.text_input("Sum Gross", value=st.session_state.extracted_data["sum_gross"], key="sum_gross_input")
    sum_net = st.text_input("Sum Net", value=st.session_state.extracted_data["sum_net"], key="sum_net_input")
    
    if st.button("Save to Database"):
        final_data = {
            "receipt_date": receipt_date,
            "receipt_number": receipt_number,
            "sum_gross": sum_gross,
            "sum_net": sum_net
        }
        save_to_db(final_data)
        st.success("Data saved successfully to the database!")
        for key in ["extracted_data", "image"]:
            st.session_state[key] = None
