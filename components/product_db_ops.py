from sqlalchemy import func

from repository.receipt_repository import ProductDB, SessionLocal


def get_products_for_receipt(receipt_id):
    with SessionLocal() as session:
        return session.query(ProductDB).filter(ProductDB.receipt_id == receipt_id).all()


def add_product_to_receipt(receipt_id, product_inputs):
    with SessionLocal() as session:
        new_product = ProductDB(
            receipt_id=str(receipt_id),
            name=product_inputs["name"],
            is_bio=product_inputs["is_bio"],
            bio_category=product_inputs["bio_category"],
            amount=product_inputs["amount"],
            unit=product_inputs["unit"],
            price=product_inputs["price"],
        )
        session.add(new_product)
        session.commit()
        return new_product


def update_product(product_id, product_inputs):
    with SessionLocal() as session:
        prod = session.query(ProductDB).get(product_id)
        if prod:
            prod.name = product_inputs["name"]
            prod.is_bio = product_inputs["is_bio"]
            prod.bio_category = product_inputs["bio_category"]
            prod.amount = product_inputs["amount"]
            prod.unit = product_inputs["unit"]
            prod.price = product_inputs["price"]
            session.commit()
        return prod


def delete_product(product_id):
    with SessionLocal() as session:
        prod = session.query(ProductDB).get(product_id)
        if prod:
            session.delete(prod)
            session.commit()
        return prod


def get_products_counts():
    """For each product id, get the count of products with that receipt_id"""
    with SessionLocal() as session:
        return (
            session.query(ProductDB.receipt_id, func.count(ProductDB.id))
            .group_by(ProductDB.receipt_id)
            .all()
        )
