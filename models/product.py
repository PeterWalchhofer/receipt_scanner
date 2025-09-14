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
    PFLANZENBAU = "Pflanzenbau"  # z.B. Jungpflanzen, Weizensaat, Grünlandmischung usw.
    TIERHALTUNG = "Tierhaltung"  # z.B.- Dünger/Einstreu/Futter Sägespäne, Euterwolle, Euterpflege, Mineralfutter, Alpenkorn, Gerste, Stroh usw.


class Product(BaseModel):
    name: str = Field(..., description="Name of the product")
    is_bio: bool | None = Field(True, description="Is the product organic?")
    bio_category: Optional[BioCategory] = Field(
        None, description="Bio category (required if is_bio is True)"
    )
    amount: float = Field(..., description="Amount of the product")
    unit: ProductUnit = Field(
        ..., description="Unit of the product (KILO, LITER, PIECE)"
    )
    price: float | None = Field(
        None, description="Price of the product per unit (optional)"
    )
