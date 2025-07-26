from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ProductUnit(str, Enum):
    KILO = "KILO"
    LITER = "LITER"
    PIECE = "PIECE"  # PIECE is a better name than QUANTITY for clarity


class BioCategory(str, Enum):
    VERMARKTUNG_VERARBEITUNG = "Vermarktung/Verarbeitung"  # z.B. Olivenöl, Lab, Kulturen, Salz, Kräuter, Honig, Essig, usw.
    PFLANZENBAU = (
        "Pflanzenbau"  # z.B. Jungpflanzen, Weizensaat, Grünlandmischung usw.
    )
    TIERHALTUNG = "Tierhaltung"  # z.B.- Dünger/Einstreu/Futter Sägespäne, Euterwolle, Euterpflege, Mineralfutter, Alpenkorn, Gerste, Stroh usw.


class Product(BaseModel):
    id: Optional[str] = Field(None, description="Product ID")
    receipt_id: str = Field(
        ..., description="Related receipt ID (join to ReceiptDB.id)"
    )
    name: str = Field(..., description="Name of the product")
    is_bio: bool = Field(..., description="Is the product organic?")
    bio_category: Optional[BioCategory] = Field(
        None, description="Bio category (required if is_bio is True)"
    )
    amount: float = Field(..., description="Amount of the product")
    unit: ProductUnit = Field(
        ..., description="Unit of the product (KILO, LITER, PIECE)"
    )
    created_on: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_on: Optional[datetime] = Field(default_factory=datetime.utcnow)
