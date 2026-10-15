"""CSV-ledger: parse ledger CSV, aggregate totals, CLI entry-point."""

import csv
import io
import json
import sys
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date


def parse_ledger(text):
    """Parse a CSV string with header ``date,category,amount``.

    Returns a list of dicts keyed by *date*, *category*, *amount*.
    *date* is validated via :py:class:`~datetime.date` (ISO-calendar only).
    *category* must be non-empty after stripping.
    *amount* is quantised to two decimal places using
    :py:obj:`~decimal.ROUND_HALF_UP` on ``Decimal(str(x))``.

    Raises :py:class:`ValueError` on malformed headers, wrong row widths,
    invalid dates, blank categories, or non-finite / malformed amounts.
    Blank input is invalid.  Header-only input returns ``[]``.
    """

    if not text or not text.strip():
        raise ValueError("blank input")

    reader = csv.reader(io.StringIO(text))
    rows_raw = list(reader)

    if not rows_raw:
        raise ValueError("empty input")

    header = [h.strip().lower() for h in rows_raw[0]]
    if header != ["date", "category", "amount"]:
        raise ValueError("malformed header")

    result = []
    for line_idx, row in enumerate(rows_raw[1:], start=2):
        if len(row) != 3:
            raise ValueError(
                f"row {line_idx}: expected 3 fields, got {len(row)}"
            )

        date_str, category_str, amount_str = (
            row[0].strip(),
            row[1].strip(),
            row[2].strip(),
        )

        # --- date validation (ISO calendar, YYYY-MM-DD only) ---
        try:
            d = date.fromisoformat(date_str)
        except ValueError:
            raise ValueError(f"row {line_idx}: invalid date")

        # Reject non-canonical formats (e.g. 2024-1-01)
        if date_str != d.isoformat():
            raise ValueError(f"row {line_idx}: non-canonical date")

        # --- category validation ---
        if not category_str:
            raise ValueError(f"row {line_idx}: empty category")

        # --- amount validation & quantisation ---
        try:
            amount = Decimal(str(amount_str))
        except (InvalidOperation, ValueError):
            raise ValueError(f"row {line_idx}: malformed amount")

        if not amount.is_finite():
            raise ValueError(f"row {line_idx}: non-finite amount")

        amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        result.append(
            {"date": date_str, "category": category_str, "amount": str(amount)}
        )

    return result


def totals(rows):
    """Aggregate *rows* (output of :py:func:`parse_ledger`) by category.

    Returns a ``dict`` in **lexicographic** category order whose values are
    two-decimal-place strings produced by exact :py:class:`~decimal.Decimal`
    addition.
    """

    agg = {}
    for row in rows:
        cat = row["category"]
        agg[cat] = agg.get(cat, Decimal("0.00")) + Decimal(row["amount"])

    return {
        k: str(agg[k].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        for k in sorted(agg)
    }


# ------------------------------------------------------------------ CLI
def _cli():
    """Read CSV from stdin, print JSON {rows, totals}, exit 0 on success."""
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
