"""CSV-ledger: parse ledger rows and aggregate exact-decimal totals."""

import csv
import io
import json
import sys
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date

_HEADER = ("date", "category", "amount")
_TWO_PLACES = Decimal("0.01")


def parse_ledger(text):
    """Parse a CSV string into a list of row dicts.

    Contract
    --------
    * Header must be exactly ``date,category,amount`` (no extra columns).
    * Dates must be ISO 8601 ``YYYY-MM-DD`` with zero-padded month/day
      and represent a real calendar date (e.g. 2023-02-29 raises).
    * Categories are stripped; empty categories raise.
    * Amounts are quantized to two decimals via ``Decimal(str(x))`` with
      ``ROUND_HALF_UP`` (e.g. ``1.005 → '1.01'``, ``7.125 → '7.13'``).
    * Blank input raises ``ValueError``; header-only input returns ``[]``.
    * Malformed headers, wrong row widths, or non-finite amounts raise
      ``ValueError``.

    Returns
    -------
    list[dict]  – rows in original order with keys ``date``, ``category``,
                  ``amount`` (string, two-decimal).
    """

    if not text or not text.strip():
        raise ValueError("blank input is invalid")

    reader = csv.reader(io.StringIO(text))
    rows_iter = iter(reader)

    # --- header ---
    try:
        header = next(rows_iter)
    except StopIteration:
        raise ValueError("blank input is invalid")

    if len(header) != 3 or tuple(header) != _HEADER:
        raise ValueError(
            f"invalid header: expected {','.join(_HEADER)}, got {','.join(header)}"
        )

    results = []
    for row in rows_iter:
        if len(row) != 3:
            raise ValueError(
                f"row width mismatch: expected 3 columns, got {len(row)}"
            )

        date_str, cat_str, amt_str = row

        # Date validation
        if not _is_valid_date(date_str):
            raise ValueError(f"invalid date: {date_str}")

        # Category — stripped, must be non-empty
        cat = cat_str.strip()
        if not cat:
            raise ValueError("empty category")

        # Amount
        try:
            amt = Decimal(amt_str)
        except (InvalidOperation, ValueError):
            raise ValueError(f"invalid amount: {amt_str}")
        if not amt.is_finite():
            raise ValueError(f"non-finite amount: {amt_str}")

        amt = amt.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)

        results.append({"date": date_str, "category": cat, "amount": str(amt)})

    return results


def _is_valid_date(s):
    """Return True if *s* is a canonical ``YYYY-MM-DD`` calendar date."""
    if not isinstance(s, str):
        return False
    parts = s.split("-")
    if len(parts) != 3:
        return False
    yyyy_s, mm_s, dd_s = parts
    # Must be exactly 4 / 2 / 2 digits
    if len(yyyy_s) != 4 or len(mm_s) != 2 or len(dd_s) != 2:
        return False
    if not (yyyy_s.isdigit() and mm_s.isdigit() and dd_s.isdigit()):
        return False
    try:
        date(int(yyyy_s), int(mm_s), int(dd_s))
    except ValueError:
        return False
    return True


def totals(rows):
    """Aggregate *rows* (``parse_ledger`` output) by category.

    Returns a ``dict`` sorted in lexicographic category order with values as
    two-decimal strings (e.g. ``{"A": "0.20", "Z": "0.30"}`).
    """

    buckets = {}
    for row in rows:
        cat = row["category"]
        amt = Decimal(row["amount"])
        buckets[cat] = buckets.get(cat, Decimal("0")) + amt

    return {cat: str(amt.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP))
            for cat, amt in sorted(buckets.items())}


# ------------------------------------------------------------------ CLI
def _cli_main():
    """Entry point when run as ``python module.py``."""
    raw = sys.stdin.read()
    try:
        rows = parse_ledger(raw)
        total = totals(rows)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

    output = {"rows": rows, "totals": total}
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    _cli_main()
