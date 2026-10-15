"""CSV-ledger: normalize ledger rows and aggregate exact decimal amounts.

API
---
parse_ledger(text: str) -> list[dict]
    Accept a CSV string whose first line is the exact header
    ``date,category,amount``.  Returns a list of dicts preserving row order
    and Unicode.  Raises ``ValueError`` on any malformed input.

totals(rows: list[dict]) -> dict[str, str]
    Aggregate ``amount`` (a two-decimal string) by ``category``.  Returns a
    dictionary keyed in **lexicographic** category order with values as
    two-decimal strings.  Negative amounts are allowed.

CLI
---
    python -m module < input.csv
    Reads CSV from stdin, prints ``{"rows":..., "totals":...}`` as JSON
    (``ensure_ascii=False``).  Invalid input exits with code 2 and prints
    a concise error to stderr (no traceback).

Validation
----------
* Header must be exactly ``date,category,amount``.
* Dates are validated as strict ISO ``YYYY-MM-DD``; non-canonical formats
  (e.g. ``2024-1-01``, ``2024-01-1``) are rejected.  Calendar validity is
  enforced (e.g. ``2023-02-29`` is rejected).
* Category must be non-empty after stripping whitespace.
* Amount is parsed via ``Decimal(str(value))`` and quantized to two decimal
  places using **ROUND_HALF_UP** (see `Python decimal docs
  <https://docs.python.org/3/library/decimal.html>`_).  Non-finite values
  (``NaN``, ``Infinity``) and non-numeric strings raise ``ValueError``.
* Row width must match the header (3 columns).

Rounding
--------
The module uses :class:`~decimal.Decimal` throughout to avoid floating-point
errors.  Quantization with ``ROUND_HALF_UP`` means ``0.125 -> '0.13'`` and
``-2.675 -> '-2.68'``.
"""
from __future__ import annotations

import csv
import io
import json
import sys
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


_HEADER = "date,category,amount"
_Q2 = Decimal("0.01")


def parse_ledger(text: str) -> list[dict]:
    """Parse a CSV ledger string and return a list of row dicts.

    Raises ``ValueError`` on malformed input.
    """
    if not text or not text.strip():
        raise ValueError("blank input")

    reader = csv.reader(io.StringIO(text))
    rows_iter = iter(reader)

    # --- header ---
    try:
        header = next(rows_iter)
    except StopIteration:
        raise ValueError("empty input")

    # Normalise for comparison (join to handle BOM / trailing newline quirks)
    if ",".join(h.strip() for h in header) != _HEADER:
        raise ValueError("invalid header")

    result: list[dict] = []

    for lineno, raw_row in enumerate(rows_iter, start=2):
        if len(raw_row) != 3:
            raise ValueError(
                f"row {lineno}: expected 3 columns, got {len(raw_row)}"
            )

        date_str, category_str, amount_str = raw_row

        # --- date ---
        date_str = date_str.strip()
        _validate_date(date_str)

        # --- category ---
        category = category_str.strip()
        if not category:
            raise ValueError(f"row {lineno}: empty category")

        # --- amount ---
        amount_raw = amount_str.strip()
        amount = _parse_amount(amount_raw, lineno)

        result.append({
            "date": date_str,
            "category": category,
            "amount": amount,
        })

    return result


def _validate_date(s: str) -> None:
    """Raise ``ValueError`` if *s* is not a valid ISO date."""
    # Reject non-canonical formats: must match YYYY-MM-DD with exactly 4-2-2
    # digits (no leading zeros omitted, no extra chars).
    if len(s) != 10 or s[4] != "-" or s[7] != "-":
        raise ValueError(f"invalid date format: {s!r}")
    try:
        d = date.fromisoformat(s)
    except ValueError:
        raise ValueError(f"invalid date: {s!r}") from None
    # Ensure round-trip preserves the string (rejects e.g. 2024-1-01 →
    # date.fromisoformat accepts it but fromisoformat returns '2024-01-01').
    if d.isoformat() != s:
        raise ValueError(f"non-canonical date: {s!r}")


def _parse_amount(s: str, lineno: int) -> str:
    """Parse a numeric string into a quantized two-decimal string.

    Raises ``ValueError`` for non-finite or non-numeric values.
    """
    if not s:
        raise ValueError(f"row {lineno}: empty amount")
    try:
        d = Decimal(s)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(
            f"row {lineno}: invalid amount: {s!r}"
        ) from exc
    if not d.is_finite():
        raise ValueError(f"row {lineno}: non-finite amount: {s!r}")
    quantized = d.quantize(_Q2, rounding=ROUND_HALF_UP)
    return str(quantized)


def totals(rows: list[dict]) -> dict[str, str]:
    """Aggregate *rows* (parse_ledger output or equivalent dicts) by category.

    Returns a dict in **lexicographic** category order with two-decimal values.
    """
    aggregated: dict[str, Decimal] = {}
    for row in rows:
        cat = row["category"]
        amt = Decimal(row["amount"])
        aggregated[cat] = aggregated.get(cat, Decimal("0")) + amt

    return {
        cat: str(aggregated[cat].quantize(_Q2, rounding=ROUND_HALF_UP))
        for cat in sorted(aggregated)
    }


# --- CLI ---

def _main() -> None:
    raw = sys.stdin.read()
    try:
        rows = parse_ledger(raw)
        t = totals(rows)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
    print(json.dumps({"rows": rows, "totals": t}, ensure_ascii=False))


if __name__ == "__main__":
    _main()
