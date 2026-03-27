"""Backfill existing receipts with a best-effort `tax_summary`.

Run after running `scripts/update_schema.py` to ensure columns exist.

Usage:
    python scripts/backfill_tax_summary.py
"""
import argparse
import logging
import os
import shutil
from repository.receipt_repository import SessionLocal, ReceiptDB
from receipt_parser.taxation import build_receipt_tax_summary


logger = logging.getLogger("backfill")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def backfill(db_path: str = None, apply: bool = False, backup_path: str | None = None):
    """Backfill receipts with a best-effort `tax_summary`.

    If `apply` is False the script runs in dry-run mode and will not write changes.
    If `backup_path` is provided and `db_path` is a file, a copy will be made before applying.
    """
    updated = 0
    flagged = 0
    flagged_ids: list[str] = []

    if apply and backup_path and db_path and os.path.exists(db_path):
        try:
            shutil.copy2(db_path, backup_path)
            logger.info(f"Created DB backup: {backup_path}")
        except Exception as e:
            logger.warning(f"Could not create backup '{backup_path}': {e}")

    with SessionLocal() as session:
        receipts = session.query(ReceiptDB).all()
        for r in receipts:
            try:
                existing = r.tax_summary if isinstance(r.tax_summary, dict) else {}

                if existing:
                    # Preserve manually-entered summaries; just fix has_mixed_taxes
                    tax_summary = existing
                else:
                    # No summary yet — try to compute one from totals
                    rs = build_receipt_tax_summary({
                        "total_gross_amount": r.total_gross_amount,
                        "total_net_amount": r.total_net_amount,
                        "vat_amount": r.vat_amount,
                    })
                    tax_summary = rs["tax_summary"]

                if apply:
                    r.tax_summary = tax_summary
                    session.add(r)
                    session.commit()

                updated += 1
                if not tax_summary:
                    flagged += 1
                    flagged_ids.append(r.id)
            except Exception as exc:
                logger.error(f"Error processing receipt id={getattr(r, 'id', 'unknown')}: {exc}")
                session.rollback()
                continue

    logger.info(f"Backfilled {updated} receipts; {flagged} flagged with empty tax_summary.")
    if flagged_ids:
        logger.info(f"Sample flagged receipt ids: {flagged_ids[:20]}")


def _parse_args():
    p = argparse.ArgumentParser(description="Backfill receipts.tax_summary")
    p.add_argument("--db-path", help="Path to sqlite DB file (optional)")
    p.add_argument("--apply", action="store_true", help="Apply changes to the DB (default: dry-run)")
    p.add_argument("--backup", help="If provided and --apply, copy DB to this path before modifying")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    backfill(db_path=args.db_path, apply=bool(args.apply), backup_path=args.backup)
