from sqlalchemy import func

from repository.receipt_repository import ProductDB, SessionLocal


def get_products_for_receipt(receipt_id):
    with SessionLocal() as session:
        return session.query(ProductDB).filter(ProductDB.receipt_id == receipt_id).all()


def get_products_counts():
    """For each product id, get the count of products with that receipt_id"""
    with SessionLocal() as session:
        return (
            session.query(ProductDB.receipt_id, func.count(ProductDB.id))
            .group_by(ProductDB.receipt_id)
            .all()
        )
