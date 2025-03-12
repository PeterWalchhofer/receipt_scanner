from sqlalchemy.orm import Session
from models.receipt import Receipt
from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
# Define the Receipt table with SQLAlchemy
class ReceiptDB(Base):
    __tablename__ = "receipts"
    
    id = Column(Integer, primary_key=True, index=True)
    receipt_number = Column(String, index=True)
    date = Column(String)
    total_gross_amount = Column(Float)
    total_net_amount = Column(Float)
    vat_amount = Column(Float)
    company_name = Column(String)
    description = Column(String)
    is_credit = Column(Boolean, default=False)
    image_path = Column(String)


# Repository Class
class ReceiptRepository:
    def __init__(self, db: Session):
        self.db = db

    def init_db(self):
        Base.metadata.create_all(bind=self.db.bind)

    def create_receipt(self, receipt_data: dict):
        self.init_db()
        db_receipt = ReceiptDB(**receipt_data)
        self.db.add(db_receipt)
        self.db.commit()
        self.db.refresh(db_receipt)
        return db_receipt

    def update_receipt(self, receipt_data: dict):
        print(receipt_data)
        receipt_id = receipt_data["id"]
        self.db.query(ReceiptDB).filter(ReceiptDB.id == receipt_id).update(receipt_data)
        self.db.commit()

    def get_all_receipts(self):
        return self.db.query(ReceiptDB).all()

    def get_receipt_by_id(self, receipt_id: int):
        return self.db.query(ReceiptDB).filter(ReceiptDB.id == receipt_id).first()
