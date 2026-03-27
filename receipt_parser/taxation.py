from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

from models.tax import TaxValidationResult


DEFAULT_RATES = [10, 13, 20]


def _round(value: float) -> float:
    """Round to 2 decimal places using round-half-up (standard for currency)."""
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def infer_single_rate_from_totals(
    gross: float,
    net: Optional[float],
    vat: Optional[float],
    candidate_rates: List[int] = DEFAULT_RATES,
    tolerance: float = 0.05,
) -> Optional[int]:
    """Try to infer a single tax rate given gross/net/vat values.

    Returns the rate as integer percent if found within tolerance, else None.
    """
    if gross is None:
        return None

    for r in candidate_rates:
        rate = r / 100.0
        if net is not None:
            # With net known, verify via vat if available, otherwise via gross
            if vat is not None:
                if abs(_round(net * rate) - vat) <= tolerance:
                    return r
            else:
                if abs(_round(net * (1 + rate)) - gross) <= tolerance:
                    return r
        elif vat is not None:
            # No net: derive it from gross and check against known vat
            derived_net = _round(gross / (1 + rate))
            if abs(_round(gross - derived_net) - vat) <= tolerance:
                return r

    return None


def _build_entry(gross: float, net: Optional[float], vat: Optional[float], rate: int) -> Dict[str, float]:
    """Build a single tax entry, preferring known values over derived ones."""
    net_sum = _round(net) if net is not None else _round(gross / (1 + rate / 100.0))
    tax_sum = _round(vat) if vat is not None else _round(gross - net_sum)
    return {"net_sum": net_sum, "tax_sum": tax_sum, "gross_sum": _round(gross)}


def build_receipt_tax_summary(
    receipt: Dict[str, Any],
    candidate_rates: List[int] = DEFAULT_RATES,
    tolerance: float = 0.05,
) -> Dict[str, Any]:
    """Build a tax_summary for a receipt dict.

    Expected receipt keys: total_gross_amount, total_net_amount, vat_amount
    Returns dict with 'has_mixed_taxes' and 'tax_summary' mapping str(rate) -> {net_sum, tax_sum, gross_sum}.
    """
    gross = receipt.get("total_gross_amount")
    net = receipt.get("total_net_amount")
    vat = receipt.get("vat_amount")

    inferred_rate = infer_single_rate_from_totals(gross, net, vat, candidate_rates, tolerance)
    if inferred_rate is not None:
        return {
            "has_mixed_taxes": False,
            "tax_summary": {str(inferred_rate): _build_entry(gross, net, vat, inferred_rate)},
        }

    return {"has_mixed_taxes": False, "tax_summary": {}}


def has_mixed_taxes_from_summary(tax_summary: Dict[str, Dict[str, float]]) -> bool:
    """Return True if more than one rate has a non-zero tax_sum."""
    nonzero = sum(1 for v in tax_summary.values() if v.get("tax_sum", 0.0) != 0.0)
    return nonzero > 1


def validate_tax_summary(
    vat_amount: Optional[float],
    tax_summary: Dict[str, Dict[str, float]],
    tolerance: float = 0.05,
) -> TaxValidationResult:
    """Validate that vat_amount matches the sum of tax_summary tax_sums."""
    if vat_amount is None:
        return TaxValidationResult(ok=False, vat_total=0.0, diff=0.0, reason="receipt has no vat_amount")
    if not tax_summary:
        return TaxValidationResult(ok=False, vat_total=0.0, diff=float(vat_amount), reason="empty tax_summary")

    total = _round(sum(float(v.get("tax_sum", 0.0)) for v in tax_summary.values()))
    diff = _round(float(vat_amount) - total)
    return TaxValidationResult(ok=abs(diff) <= tolerance, vat_total=total, diff=diff)
