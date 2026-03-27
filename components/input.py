import json
import streamlit as st
from receipt_parser.taxation import DEFAULT_RATES, _round, build_receipt_tax_summary
from receipt_parser.llm import extract_tax_summary

from models.product import BioCategory, ProductUnit
from models.receipt import ReceiptSource
from repository.receipt_repository import ReceiptDB


def get_receipt_inputs(receipt: ReceiptDB, receipt_id: int = 0, expand_tax: bool = False):
    # Immutable fields
    st.markdown("### Receipt Details")
    # Set by server
    if receipt.created_on or receipt.updated_on:
        st.write(
            f"Created on: {receipt.created_on.strftime('%d.%m.%Y um %H:%M:%S') if receipt.created_on else '-'}"
        )
        st.write(
            f"Updated on: {receipt.updated_on.strftime('%d.%m.%Y um %H:%M:%S') if receipt.updated_on else '-'}"
        )

    # Editable fields
    receipt_number = st.text_input(
        "Receipt Number",
        value=receipt.receipt_number,
        key=f"receipt_number_{receipt_id}",
    )
    receipt_date = st.text_input(
        "Receipt Date", value=receipt.date, key=f"date_{receipt_id}"
    )
    total_gross_amount = st.text_input(
        "Total Gross Amount",
        value=str(receipt.total_gross_amount),
        key=f"gross_{receipt_id}",
    )
    total_net_amount = st.text_input(
        "Total Net Amount",
        value=str(receipt.total_net_amount),
        key=f"net_{receipt_id}",
    )
    vat_amount = st.text_input(
        "VAT Amount", value=str(receipt.vat_amount), key=f"vat_{receipt_id}"
    )
    company_name = st.text_input(
        "Company Name",
        value=receipt.company_name,
        key=f"company_{receipt_id}",
    )
    description = st.text_area(
        "Description",
        value=receipt.description,
        key=f"description_{receipt_id}",
    )
    comment = st.text_area(
        "Comment", key=f"comment_{receipt_id}", value=receipt.comment
    )
    is_bio = st.checkbox("Bio", key=f"bio_{receipt_id}", value=receipt.is_bio)
    is_credit = st.checkbox(
        "Gutschrift", value=receipt.is_credit, key=f"is_credit_{receipt_id}"
    )
    # Taxation inputs for credit notes
    has_mixed_taxes = None
    tax_summary_data = None
    if is_credit:
        tax_missing = bool(receipt.vat_amount and not receipt.tax_summary)
        with st.expander("⚠️ Tax Breakdown — Action Required" if tax_missing else "Tax Breakdown", expanded=expand_tax):
            if tax_missing:
                st.error("Tax breakdown is missing. Use one of the buttons below to fill it in before saving.")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Extract from totals", key=f"extract_tax_{receipt_id}"):
                    rs = build_receipt_tax_summary({
                        "total_gross_amount": receipt.total_gross_amount,
                        "total_net_amount": receipt.total_net_amount,
                        "vat_amount": receipt.vat_amount,
                    })
                    for rate in DEFAULT_RATES:
                        entry = rs["tax_summary"].get(str(rate), {})
                        st.session_state[f"tax_{rate}_{receipt_id}"] = float(entry.get("tax_sum", 0.0))
                    st.rerun()
            with col_b:
                if st.button("Extract via LLM", key=f"extract_tax_llm_{receipt_id}"):
                    with st.spinner("Querying LLM..."):
                        file_paths = receipt.file_paths
                        if isinstance(file_paths, str):
                            try:
                                file_paths = json.loads(file_paths)
                            except Exception:
                                file_paths = []
                        rs = extract_tax_summary(
                            file_paths if isinstance(file_paths, list) else [],
                            {
                                "total_gross_amount": receipt.total_gross_amount,
                                "total_net_amount": receipt.total_net_amount,
                                "vat_amount": receipt.vat_amount,
                            },
                        )
                    for rate in DEFAULT_RATES:
                        entry = (rs.get("tax_summary") or {}).get(str(rate), {})
                        st.session_state[f"tax_{rate}_{receipt_id}"] = float(entry.get("tax_sum", 0.0))
                    st.rerun()

            existing_summary = receipt.tax_summary if isinstance(receipt.tax_summary, dict) else {}
            tax_summary_data = {}
            for rate in DEFAULT_RATES:
                entry = existing_summary.get(str(rate)) or {}
                existing_tax = entry.get("tax_sum") if isinstance(entry, dict) else None
                key = f"tax_{rate}_{receipt_id}"
                if key not in st.session_state:
                    st.session_state[key] = float(existing_tax) if existing_tax is not None else 0.0
                tax_val = st.number_input(
                    f"VAT amount {rate}%",
                    step=0.01,
                    key=key,
                )
                if tax_val:
                    net = _round(tax_val * 100.0 / rate)
                    gross = _round(net + tax_val)
                else:
                    net = 0.0
                    gross = 0.0
                tax_summary_data[str(rate)] = {"net_sum": net, "tax_sum": _round(tax_val), "gross_sum": gross}

            nonzero_rates = [r for r in DEFAULT_RATES if tax_summary_data[str(r)]["tax_sum"] != 0.0]
            has_mixed_taxes = len(nonzero_rates) > 1
            if has_mixed_taxes:
                st.info(f"Mixed taxes detected: {', '.join(f'{r}%' for r in nonzero_rates)}")
    source_options = [e.value for e in ReceiptSource]
    source = st.selectbox(
        "Source",
        options=source_options,
        index=source_options.index(receipt.source) if receipt.source in source_options else 0,
        key=f"source_{receipt_id}",
    )

    return {
        "receipt_number": receipt_number,
        "receipt_date": receipt_date,
        "total_gross_amount": total_gross_amount,
        "total_net_amount": total_net_amount,
        "vat_amount": vat_amount,
        "company_name": company_name,
        "description": description,
        "comment": comment,
        "is_bio": is_bio,
        "is_credit": is_credit,
        "has_mixed_taxes": has_mixed_taxes,
        "tax_summary_data": tax_summary_data,
        "source": source,
    }


def get_product_inputs(product=None, default_is_bio=False, prefix="", show_price=True):
    """
    Render Streamlit input widgets for a product (add or edit).
    Args:
        product: ProductDB or similar object, or None for add mode
        default_is_bio: bool, default value for is_bio if product is None
        prefix: str, unique prefix for Streamlit keys
        show_price: bool, whether to show the price input
    Returns:
        dict with product input values
    """
    name = st.text_input(
        "Product Name",
        value=product.name or "" if product else "",
        key=f"{prefix}name",
    )
    is_bio = st.checkbox(
        "Biokontrolle",
        value=bool(product.is_bio if product else default_is_bio),
        key=f"{prefix}is_bio",
    )
    bio_category = None
    options = [None] + [e.value for e in BioCategory]
    if is_bio:
        current_bio = product.bio_category if product else None
        bio_category = st.selectbox(
            "Bio Category",
            options,
            index=options.index(current_bio) if current_bio in options else 0,
            key=f"{prefix}bio_category",
        )
    amount = st.number_input(
        "Amount",
        value=float(product.amount) if product and product.amount is not None else 0.0,
        step=0.01,
        key=f"{prefix}amount",
    )
    unit_options = [e.value for e in ProductUnit]
    unit = st.selectbox(
        "Unit",
        unit_options,
        index=unit_options.index(product.unit) if product and product.unit else 0,
        key=f"{prefix}unit",
    )
    price = None
    if show_price:
        price = st.number_input(
            "Price",
            value=float(product.price) if product and product.price is not None else 0.0,
            step=0.01,
            key=f"{prefix}price",
        )
    return {
        "name": name,
        "is_bio": is_bio,
        "bio_category": bio_category if is_bio else None,
        "amount": amount,
        "unit": unit,
        "price": price,
    }
