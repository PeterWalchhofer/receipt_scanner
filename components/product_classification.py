"""
Product classification and aggregation utilities.
Provides functions for regex matching, product filtering, and batch assignment logic.
"""

import re
from typing import Optional

import pandas as pd

from repository.receipt_repository import ProductDB, RegexDB, SortimentDB, SessionLocal, ReceiptDB



def match_regex_to_products(regex_pattern: str, products: list[ProductDB]) -> list[ProductDB]:
    """
    Find all products matching a given regex pattern.
    
    Args:
        regex_pattern: Regex pattern to match against product names
        products: List of ProductDB objects to filter
        
    Returns:
        List of products whose names match the regex pattern
    """
    try:
        compiled_pattern = re.compile(regex_pattern, re.IGNORECASE)
        return [p for p in products if p.name and compiled_pattern.search(p.name)]
    except re.error as e:
        print(f"Invalid regex pattern: {e}")
        return []


def get_unclassified_products(
    regex_id: Optional[str] = None,
) -> list[ProductDB]:
    """
    Get all unclassified products (product_class_reference IS NULL) 
    that belong to käseinnahmen receipts (is_credit=TRUE).
    Optionally filter by regex pattern if regex_id is provided.
    
    Args:
        regex_id: Optional RegexDB ID to apply regex matching
        
    Returns:
        List of unclassified ProductDB objects from käseinnahmen receipts
    """
    with SessionLocal() as session:
        unclassified = (
            session.query(ProductDB)
            .join(ReceiptDB, ProductDB.receipt_id == ReceiptDB.id)
            .filter(
                ProductDB.product_class_reference.is_(None),
                ReceiptDB.is_credit == True,
            )
            .all()
        )
        
        if regex_id:
            regex_obj = session.query(RegexDB).filter(RegexDB.id == regex_id).first()
            if regex_obj:
                unclassified = match_regex_to_products(regex_obj.regex, unclassified)
        
        return unclassified


def assign_product_class(
    product_ids: list[str], product_class_id: str
) -> int:
    """
    Assign a product class to multiple products.
    
    Args:
        product_ids: List of ProductDB IDs to update
        product_class_id: SortimentDB ID to assign
        
    Returns:
        Number of products updated
    """
    with SessionLocal() as session:
        updated = (
            session.query(ProductDB)
            .filter(ProductDB.id.in_(product_ids))
            .update({ProductDB.product_class_reference: product_class_id})
        )
        session.commit()
        return updated


def get_sortiment_with_regex_count() -> list[dict]:
    """
    Get all sortiment records with their regex pattern counts.
    
    Returns:
        List of dicts with sortiment info and regex count
    """
    with SessionLocal() as session:
        sortiments = session.query(SortimentDB).all()
        result = []
        for sortiment in sortiments:
            regex_count = (
                session.query(RegexDB)
                .filter(RegexDB.product_class_id == sortiment.id)
                .count()
            )
            result.append({
                "id": sortiment.id,
                "name": sortiment.name,
                "regex_count": regex_count,
                "created_on": sortiment.created_on,
                "updated_on": sortiment.updated_on,
            })
        return result


def get_product_class_aggregation(
    products: list[ProductDB],
    receipts_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Aggregate product data by product_class_reference.
    
    Args:
        products: List of ProductDB objects with product_class_reference
        receipts_df: DataFrame with receipt metadata (indexed by receipt_id)
        
    Returns:
        DataFrame with aggregated data by product class
    """
    if not products:
        return pd.DataFrame()
    
    # Convert to DataFrame
    data = []
    for product in products:
        if product.product_class_reference:
            data.append({
                "product_class_id": product.product_class_reference,
                "amount": product.amount or 0,
                "price": product.price or 0,
                "receipt_id": product.receipt_id,
                "product_name": product.name,
            })
    
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # Get sortiment names
    with SessionLocal() as session:
        sortiments = session.query(SortimentDB).all()
        sortiment_map = {s.id: s.name for s in sortiments}
    
    df["product_class"] = df["product_class_id"].map(sortiment_map)
    
    # Aggregate by product class
    agg_df = df.groupby("product_class").agg({
        "amount": "sum",
        "price": "sum",
        "receipt_id": "count",
    }).reset_index()
    agg_df.columns = ["Product Class", "Total Amount", "Total Price", "Count"]
    
    return agg_df


def get_product_aggregation_by_name(
    products: list[ProductDB],
) -> pd.DataFrame:
    """
    Aggregate product data by product name (for backwards compatibility).
    
    Args:
        products: List of ProductDB objects
        
    Returns:
        DataFrame with aggregated data by product name
    """
    if not products:
        return pd.DataFrame()
    
    data = []
    for product in products:
        data.append({
            "name": product.name,
            "amount": product.amount or 0,
            "unit": product.unit.value if product.unit else "Unknown",
            "price": product.price or 0,
            "receipt_id": product.receipt_id,
        })
    
    df = pd.DataFrame(data)
    
    # Aggregate by name and unit
    agg_df = (
        df.groupby(["name", "unit"])
        .agg({
            "amount": "sum",
            "price": "sum",
            "receipt_id": "count",
        })
        .reset_index()
    )
    agg_df.columns = ["Product Name", "Unit", "Total Amount", "Total Price", "Count"]
    agg_df = agg_df.sort_values("Total Amount", ascending=False)
    
    return agg_df
