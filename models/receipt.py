from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from models.product import Product


class ReceiptSource(str, Enum):
    RECEIPT_SCANNER = "RECEIPT_SCANNER"
    RECHNUNGSAPP = "RECHNUNGSAPP"
    REGISTRIERKASSA = "REGISTRIERKASSA"


class Receipt(BaseModel):
    id: Optional[int] = Field(None, description="Receipt ID")
    receipt_number: Optional[str] = Field(
        None, description="Receipt number or identification number"
    )
    date: Optional[str] = Field(None, description="Date of the receipt")
    total_gross_amount: Optional[float] = Field(
        None, description="Total amount with tax"
    )
    total_net_amount: Optional[float] = Field(
        None, description="Total amount without tax"
    )
    is_bio: Optional[bool] = Field(
        None, description="Indicates if the receipt is relevant for organic monitoring"
    )
    vat_amount: Optional[float] = Field(None, description="VAT amount")
    company_name: Optional[str] = Field(None, description="Name of the issuing company")
    description: Optional[str] = Field(
        None, description="Description of purchased items or services"
    )
    is_credit: Optional[bool] = Field(
        None, description="Indicates if it's a credit note"
    )
    source: Optional[ReceiptSource] = Field(
        default=ReceiptSource.RECEIPT_SCANNER,
        description="Source of the receipt (RECEIPT_SCANNER, RECHNUNGSAPP, REGISTRIERKASSA)",
    )
    products: list[Product] = Field(
        default=[], description="List of products in the receipt"
    )
