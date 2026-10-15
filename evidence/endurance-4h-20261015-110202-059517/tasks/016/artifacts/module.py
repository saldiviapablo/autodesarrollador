"""Normalize CSV ledger rows and aggregate exact decimal amounts.

API
---
parse_ledger(text: str) -> list[dict]
    Accepts a CSV string with the exact header ``date,category,amount``.
    Returns a list of dicts with keys ``date``, ``category``, ``amount``.

    Validation rules
    ----------------
    * Header must be exactly ``date,category,amount`` (case-sensitive).
    * Each data row must have exactly 3 fields.
    * ``date`` is parsed strictly with ``datetime.date.fromisoformat``; only
      canonical ``YYYY-MM-DD`` is accepted (rejects ``2024-1-1``,
      ``2023-02-29``, etc.).
    * ``category`` is stripped of whitespace and must be non-empty.
    * ``amount`` is parsed as ``Decimal(str(value))`` and quantized to
      two decimal places using ``ROUND_HALF_UP``.  Non-finite values
      (``NaN``, ``Infinity``) and malformed strings raise ``ValueError``.
    * Blank input (empty string) raises ``ValueError``.
    * Header-only input returns an empty list ``[]``.

    Row order and Unicode characters are preserved.

totals(rows: list[dict]) -> dict[str, str]
    Aggregates the ``amount`` field of ``parse_ledger`` output by
    ``category`` using exact ``Decimal`` arithmetic.
    Returns a ``dict`` whose keys are in **lexicographic** order and whose
    values are two-decimal-place string representations of the sums.
    Negative amounts are supported.

CLI
---
    ``python module.py`` reads a CSV from **stdin** and prints a JSON object
    with keys ``rows`` and ``totals``.  Output uses ``ensure_ascii=False``.
    On invalid input the CLI exits with code **2** and writes a concise
    error message to **stderr** (no Python traceback).
"""
import sys
import csv
import json
import io
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date


def parse_ledger(text: str) -> list[dict]:
    """Parse a CSV ledger string and return a list of validated row dicts."""
    if not text or not text.strip():
        raise ValueError("blank input is invalid")

    reader = csv.reader(io.StringIO(text))
    rows_iter = iter(reader)

    # --- header validation -------------------------------------------------
    try:
        header = next(rows_iter)
    except StopIteration:
        raise ValueError("empty input")

    if header != ["date", "category", "amount"]:
        raise ValueError(
            f"invalid header: expected ['date', 'category', 'amount'], "
            f"got {header}"
        )

    results: list[dict] = []

    # --- data rows ---------------------------------------------------------
    for lineno, raw_row in enumerate(rows_iter, start=2):
        if len(raw_row) != 3:
            raise ValueError(
                f"row {lineno}: expected 3 fields, got {len(raw_row)}"
            )

        raw_date, raw_category, raw_amount = raw_row

        # date — strict ISO round-trip
        try:
            d = date.fromisoformat(raw_date.strip())
            canonical = d.isoformat()  # always YYYY-MM-DD
        except (ValueError, TypeError):
            raise ValueError(f"row {lineno}: invalid date {raw_date!r}")

        # category — strip and reject empty
        category = raw_category.strip()
        if not category:
            raise ValueError(f"row {lineno}: empty category")

        # amount — Decimal with ROUND_HALF_UP to 2 dp
        amount_str = raw_amount.strip()
        try:
            amount_dec = Decimal(amount_str)
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(f"row {lineno}: malformed amount {amount_str!r}")

        if not amount_dec.is_finite():
            raise ValueError(
                f"row {lineno}: non-finite amount {amount_str!r}"
            )

        amount_quantized = amount_dec.quantize(
            Decimal("0.00"), rounding=ROUND_HALF_UP
        )

        results.append(
            {
                "date": canonical,
                "category": category,
                "amount": str(amount_quantized),
            }
        )

    return results


def totals(rows: list[dict]) -> dict[str, str]:
    """Aggregate *rows* (parse_ledger output) by category.

    Returns a dict in **lexicographic** key order with two-decimal string
    values.
    """
    agg: dict[str, Decimal] = {}
    for row in rows:
        cat = row["category"]
        amt = Decimal(row["amount"])
        agg[cat] = agg.get(cat, Decimal("0")) + amt

    return {cat: str(agg[cat].quantize(Decimal("0.00"), rounding=ROUND_HALF_UP))
            for cat in sorted(agg)}


# --- CLI entrypoint --------------------------------------------------------
def _cli() -> None:
    """Read CSV from stdin, print JSON {rows, totals}, or exit 2 on error."""
    try:
        text = sys.stdin.read()
        rows = parse_ledger(text)
        total = totals(rows)
        print(json.dumps({"rows": rows, "totals": total}, ensure_ascii=False))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    _cli()
