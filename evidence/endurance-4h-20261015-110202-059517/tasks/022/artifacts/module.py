"""CSV ledger: parse rows and aggregate totals with exact Decimal arithmetic."""

import csv
import io
import json
import sys
from collections import OrderedDict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

_EXPECTED_HEADER = ["date", "category", "amount"]


def parse_ledger(text):
    """Parse a CSV string with header *date,category,amount* and return a list of dicts.

    Validation rules:
    - **Blank input** → ``ValueError``.
    - **Header mismatch** → ``ValueError``.
    - **Row width mismatch** → ``ValueError``.
    - **Date** must be canonical ``YYYY-MM-DD`` (digits/dashes only, no leading/trailing
      padding anomalies) and represent a real calendar date on the ISO proleptic
      Gregorian calendar.
    - **Category** must be nonempty after stripping whitespace.
    - **Amount** must parse as a finite number; the result is quantized to two
      decimal places using ``Decimal(str(x))`` with ``ROUND_HALF_UP``.

    Preserves original row order and Unicode content.

    A header-only document (no data rows) returns ``[]``.

    Raises ``ValueError`` on any violation.
    """
    if not text or not text.strip():
        raise ValueError("blank input")

    reader = csv.reader(io.StringIO(text))
    rows_raw = list(reader)

    if not rows_raw:
        raise ValueError("blank input")

    header = [h.strip() for h in rows_raw[0]]
    if header != _EXPECTED_HEADER:
        raise ValueError(
            f"expected header {_EXPECTED_HEADER}, got {header}"
        )

    if len(rows_raw) == 1:
        return []

    result = []
    for row in rows_raw[1:]:
        # Skip completely blank lines produced by trailing newline
        if len(row) == 0 or (len(row) == 1 and row[0].strip() == ""):
            continue

        if len(row) != 3:
            raise ValueError(f"row width {len(row)}, expected 3")

        raw_date, raw_category, raw_amount = row

        # --- date ---
        d_str = raw_date.strip()
        # Must be exactly YYYY-MM-DD with 4-digit year, 2-digit month, 2-digit day
        if len(d_str) != 10 or d_str[4] != "-" or d_str[7] != "-":
            raise ValueError(f"invalid date format: {raw_date!r}")
        try:
            parsed = date.fromisoformat(d_str)
        except ValueError:
            raise ValueError(f"invalid date: {raw_date!r}")
        # Canonical round-trip: ensure the repr matches (rejects e.g. 2024-1-01)
        if parsed.isoformat() != d_str:
            raise ValueError(f"noncanonical date: {d_str!r}")

        # --- category ---
        category = raw_category.strip()
        if not category:
            raise ValueError("empty category")

        # --- amount ---
        amount_raw = raw_amount.strip()
        if not amount_raw:
            raise ValueError("empty amount")
        try:
            d_amount = Decimal(str(amount_raw))
        except (InvalidOperation, ValueError):
            raise ValueError(f"malformed amount: {amount_raw!r}")
        if not d_amount.is_finite():
            raise ValueError(f"nonfinite amount: {amount_raw!r}")
        amount_q = d_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        result.append({
            "date": d_str,
            "category": category,
            "amount": str(amount_q),
        })

    return result


def totals(rows):
    """Aggregate *rows* (output of :func:`parse_ledger`) by category.

    Returns a ``dict`` keyed in lexicographic category order, values are
    two-decimal-place strings quantized with ``ROUND_HALF_UP``.
    """
    acc = {}
    for row in rows:
        cat = row["category"]
        acc[cat] = acc.get(cat, Decimal("0.00")) + Decimal(row["amount"])
    quantized = {
        k: str(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        for k, v in sorted(acc.items())
    }
    return quantized


def _cli():
    """CLI entry-point: read CSV from stdin, print JSON to stdout."""
    try:
        import sys
        text = sys.stdin.read()
        rows = parse_ledger(text)
        total = totals(rows)
        print(json.dumps({"rows": rows, "totals": total}, ensure_ascii=False, indent=2))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    _cli()
