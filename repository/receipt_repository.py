import os
import uuid
import datetime
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

# from models.receipt import Base  # Adjust the import according to where you define your models

DATABASE_URL = "sqlite:///./receipts.db"
# Database URL (SQLite in this case)

# Setup SQLAlchemy
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
# Create all tables
Base.metadata.create_all(bind=engine)

# Base = declarative_base()
# # Define the Receipt table with SQLAlchemy


class ReceiptDB(Base):
    __tablename__ = "receipts"
    created_on = Column(DateTime(timezone=True), server_default=func.now())
    updated_on = Column(DateTime(timezone=True), onupdate=func.now())
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    receipt_number = Column(String, index=True)
    date = Column(String)
    total_gross_amount = Column(Float)
    total_net_amount = Column(Float)
    vat_amount = Column(Float)
    company_name = Column(String)
    description = Column(String)
    comment = Column(String)
    is_credit = Column(Boolean, default=False)
    is_bio = Column(Boolean, default=False)
    file_paths = Column(JSON)  # Store multiple image paths


# Repository Class
class ReceiptRepository:
    def __init__(self):
        self.init_db()

    def init_db(self):
        with SessionLocal() as session:
            Base.metadata.create_all(bind=session.bind)

    def clean_up(self):
        """Get all paths and compre with local dir /saved_images. Delete images in saved_images that are not in the database"""
        with SessionLocal() as session:
            db_paths = session.query(ReceiptDB.file_paths).all()
            db_paths = set(path for path_group in db_paths for path in path_group[0])

        local_paths = os.listdir("saved_images")
        for local_path in local_paths:
            local_path = "saved_images/" + local_path
            if local_path not in db_paths:
                os.remove(local_path)
                print(f"Deleted {local_path}")

    def create_receipt(self, db_receipt: ReceiptDB) -> ReceiptDB:
        with SessionLocal() as session:
            session.add(db_receipt)
            session.commit()
            session.refresh(db_receipt)
            return db_receipt

    def update_receipt(self, receipt_id: int, receipt_data: ReceiptDB) -> None:
        with SessionLocal() as session:
            receipt = (
                session.query(ReceiptDB).filter(ReceiptDB.id == receipt_id).first()
            )
            if not receipt:
                return None
            for key, value in receipt_data.__dict__.items():
                if key == "_sa_instance_state":
                    continue
                setattr(receipt, key, value)
            session.commit()

    def delete_receipt(self, receipt_id: int) -> None:
        with SessionLocal() as session:
            receipt = (
                session.query(ReceiptDB).filter(ReceiptDB.id == receipt_id).first()
            )
            if not receipt:
                return None
            session.delete(receipt)
            session.commit()

    def get_all_receipts(self):
        if datetime.datetime.now().minute % 10 == 0:
            self.clean_up()
        with SessionLocal() as session:
            return session.query(ReceiptDB).order_by(ReceiptDB.created_on.desc()).all()

    def get_receipt_by_id(self, receipt_id: int):
        with SessionLocal() as session:
            return session.query(ReceiptDB).filter(ReceiptDB.id == receipt_id).first()
