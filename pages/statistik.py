import pandas as pd
import streamlit as st

from pages.statistik_overview import show_overview_statistics
from pages.statistik_kaese import show_kaese_statistics
from repository.receipt_repository import ReceiptRepository

st.title("📊 Statistik")

# Create tabs for different statistics views
tab_overview, tab_kaese = st.tabs(["📈 Overview", "🧀 Käse"])

receipt_repo = ReceiptRepository()
receipts = receipt_repo.get_all_receipts()

if not receipts:
    st.info("No receipts found.")
    st.stop()

df = pd.DataFrame([r.__dict__ for r in receipts])
if "_sa_instance_state" in df.columns:
    df = df.drop("_sa_instance_state", axis=1)

# Convert date to datetime
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

# ============================================
# TAB 1: OVERVIEW
# ============================================
with tab_overview:
    show_overview_statistics(df)

# ============================================
# TAB 2: KÄSE STATISTICS
# ============================================
with tab_kaese:
    show_kaese_statistics()
