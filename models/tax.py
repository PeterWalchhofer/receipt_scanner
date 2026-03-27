from pydantic import BaseModel
from typing import Optional


class TaxEntry(BaseModel):
    net_sum: float
    tax_sum: float
    gross_sum: float


class TaxRateEntry(TaxEntry):
    """TaxEntry with its rate — used in LLM responses where keys can't be dynamic."""
    rate: int


class TaxSummaryModel(BaseModel):
    has_mixed_taxes: bool
    entries: list[TaxRateEntry]


class TaxValidationResult(BaseModel):
    ok: bool
    vat_total: float
    diff: float
    reason: Optional[str] = None
