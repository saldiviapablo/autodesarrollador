"""Normalize CSV ledger rows and aggregate exact decimal amounts.

API
---
parse_ledger(text: str) -> list[dict]
    Accepts a CSV string with the exact header ``date,category,amount``.
    Returns a list of dicts with keys ``date``, ``category``, ``amount``.

    Validation rules
    ----------------
    * Blank input raises ``ValueError``.
    * Header must be exactly ``date,category,amount``.
    * Each data row must have exactly 3 fields.
    * ``date`` must be a valid ISO calendar date in canonical ``YYYY-MM-DD``
      format (rejects ``YYYY-M-D``, non-existent dates like 2023-02-29).
    * ``category`` must be a non-empty stripped string.
    * ``amount`` is parsed via ``Decimal(str(x))`` and quantized to two
      decimal places using ``ROUND_HALF_UP``.  Non-finite values (NaN,
      Infinity), empty strings, and malformed amounts raise ``ValueError``.
    * Row order is preserved.  Unicode is preserved verbatim.

totals(rows: list[dict]) -> dict[str, str]
    Aggregates ``amount`` values from ``parse_ledger`` output by category.
    Returns a ``dict`` with categories as keys in lexicographic order and
    values as two-decimal-place strings.  Negative amounts are allowed.

CLI
---
    ``python module.py`` reads CSV from stdin and prints JSON to stdout
    with keys ``rows`` and ``totals``.  ``ensure_ascii=False`` is used.
    Invalid input causes exit code 2 with a concise error message on
    stderr (no traceback).
"""
import csv
import io
import json
import sys
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date

# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _parse_date(raw: str) -> str:
    """Validate and return a canonical ISO date string (YYYY-MM-DD)."""
    s = raw.strip()
    # Must be exactly 10 characters: YYYY-MM-DD
    if len(s) != 10 or s[4] != '-' or s[7] != '-':
        raise ValueError(f"invalid date format: {raw!r}")
    year_s, month_s, day_s = s.split('-')
    # All parts must be purely numeric (no leading signs etc.)
    for part_name, part in [("year", year_s), ("month", month_s), ("day", day_s)]:
        if not part.isdigit():
            raise ValueError(f"non-numeric {part_name} in date: {raw!r}")
    try:
        d = date(int(year_s), int(month_s), int(day_s))
    except ValueError:
        raise ValueError(f"non-existent date: {raw!r}")
    # Enforce canonical representation — reject 2024-1-01 style
    canonical = d.isoformat()  # always YYYY-MM-DD
    if s != canonical:
        raise ValueError(f"non-canonical date: {raw!r} (use {canonical!r})")
    return canonical


def _parse_amount(raw: str) -> str:
    """Parse amount string to a 2-decimal-place string via Decimal."""
    s = raw.strip()
    if not s:
        raise ValueError("empty amount")
    try:
        val = Decimal(s)
    except (InvalidOperation, ValueError):
        raise ValueError(f"malformed amount: {raw!r}")
    if not val.is_finite():
        raise ValueError(f"non-finite amount: {raw!r}")
    return str(val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def parse_ledger(text: str) -> list[dict]:
    """Parse CSV ledger text and return a list of validated row dicts."""
    if not text or not text.strip():
        raise ValueError("blank input is invalid")

    reader = csv.reader(io.StringIO(text))
    rows_iter = iter(reader)

    # --- header -------------------------------------------------------
    try:
        header = next(rows_iter)
    except StopIteration:
        raise ValueError("blank input is invalid")

    if len(header) != 3 or [h.strip() for h in header] != ['date', 'category', 'amount']:
        raise ValueError(f"invalid header: expected 'date,category,amount'")

    result: list[dict] = []

    for line_idx, row in enumerate(rows_iter, start=2):
        if len(row) != 3:
            raise ValueError(
                f"row {line_idx}: expected 3 fields, got {len(row)}"
            )
        raw_date, raw_category, raw_amount = row
        parsed_date = _parse_date(raw_date)
        category = raw_category.strip()
        if not category:
            raise ValueError(f"row {line_idx}: category must be non-empty")
        parsed_amount = _parse_amount(raw_amount)
        result.append({
            'date': parsed_date,
            'category': category,
            'amount': parsed_amount,
        })

    return result


def totals(rows: list[dict]) -> dict:
    """Aggregate parsed ledger rows by category, return dict[str, str]."""
    agg: dict[str, Decimal] = {}
    for row in rows:
        cat = row['category']
        amt = Decimal(row['amount'])
        agg[cat] = agg.get(cat, Decimal('0')) + amt

    return {
        cat: str(agg[cat].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        for cat in sorted(agg)
    }


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

def main() -> None:
    """Read CSV from stdin, print JSON {rows, totals} to stdout."""
    try:
        text = sys.stdin.read()
        rows = parse_ledger(text)
        tot = totals(rows)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

    print(json.dumps({'rows': rows, 'totals': tot}, ensure_ascii=False))


if __name__ == '__main__':
    main()
