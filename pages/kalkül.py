import os
import tempfile
import zipfile

import pandas as pd
import streamlit as st

from models.receipt import ReceiptSource
from repository.receipt_repository import ReceiptDB, ReceiptRepository

st.title("Import Rechnungsapp ZIP")

receipt_repo = ReceiptRepository()
# add info text for this page
st.info("""
Go to Kalkül -> Export -> Set the time range and check "Rechnungen" option -> Herunterladen
""")
uploaded_zip = st.file_uploader("Upload ZIP file from Kalkül", type=["zip"])

if uploaded_zip:
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "upload.zip")
        with open(zip_path, "wb") as f:
            f.write(uploaded_zip.read())
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(tmpdir)

        csv_path = os.path.join(tmpdir, "Rechnungen.csv")
        pdf_dir = os.path.join(tmpdir, "Rechnungen")
        if not os.path.exists(csv_path) or not os.path.exists(pdf_dir):
            st.error("CSV or Rechnungen folder not found in ZIP.")
        else:
            df = pd.read_csv(
                csv_path, sep="\t" if "\t" in open(csv_path).read(1024) else ","
            )
            df["Datum"] = pd.to_datetime(df["Datum"])
            st.write(f"Found {len(df)} invoices in CSV.")
            imported = 0
            for idx, row in df.iterrows():
                num = str(row["#"]).strip()
                pdf_file = None
                for fname in os.listdir(pdf_dir):
                    if fname.startswith(num + " ") and fname.lower().endswith(".pdf"):
                        pdf_file = fname
                        break
                if not pdf_file:
                    continue
                # Copy PDF to saved_images
                dest_pdf = os.path.join("saved_images", pdf_file)
                src_pdf = os.path.join(pdf_dir, pdf_file)
                if not os.path.exists(dest_pdf):
                    with open(src_pdf, "rb") as fsrc, open(dest_pdf, "wb") as fdst:
                        fdst.write(fsrc.read())
                storno = row["Stornorechnung?"]
                if storno:
                    # flip signs
                    row["Gesamter Bruttobetrag"] *= -1
                    row["Gesamter Nettobetrag"] *= -1
                    row["Gesamter Steuerbetrag"] *= -1
                # Map fields
                db_receipt = ReceiptDB(
                    receipt_number=row["Nummer"],
                    date=row["Datum"].strftime("%Y-%m-%d"),
                    total_gross_amount=float(row["Gesamter Bruttobetrag"]),
                    total_net_amount=float(row["Gesamter Nettobetrag"]),
                    vat_amount=float(row["Gesamter Steuerbetrag"]),
                    company_name=row["Kundenname"]
                    if not pd.isna(row["Kundenname"])
                    else "",
                    description="Verkauf Käse und Spezialitäten",
                    comment=None if not storno else "Stornorechnung",
                    is_credit=not storno,
                    is_bio=False,
                    file_paths=[dest_pdf],
                    source=ReceiptSource.RECHNUNGSAPP.value,
                )
                receipt_repo.create_receipt(db_receipt)
                imported += 1
            st.success(f"Imported {imported} receipts from ZIP.")
