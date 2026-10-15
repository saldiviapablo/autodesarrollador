"""CSV ledger: parse ledger rows, aggregate totals, and provide a CLI."""
import csv
import io
import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date


def parse_ledger(text):
    """Parse a CSV string with header *date,category,amount* and return a list of dicts.

    Validation rules (all raise ``ValueError`` on bad input):
    - Input must not be blank (empty string or only whitespace).
    - Header must be exactly ``date,category,amount`` (line-separated).
    - Each data row must have exactly 3 comma-separated fields.
    - **date**: must match ``YYYY-MM-DD`` exactly and be a valid ISO calendar date
      (rejects e.g. ``2024-1-01``, ``2023-02-29``, non-canonical formats).
    - **category**: stripped of leading/trailing whitespace; empty after strip is rejected.
    - **amount**: converted via ``Decimal(str(x))`` and quantized to two decimal places
      using ``ROUND_HALF_UP``.  Nonfinite values (``NaN``, ``Infinity``) and malformed
      strings raise ``ValueError``.

    Row order and Unicode content are preserved.
    A header-only input (no data rows) returns an empty list ``[]``.
    """
    if not text or not text.strip():
        raise ValueError("blank input")

    reader = csv.reader(io.StringIO(text))
    rows_raw = list(reader)

    if not rows_raw:
        raise ValueError("no header found")

    header = [h.strip() for h in rows_raw[0]]
    if header != ["date", "category", "amount"]:
        raise ValueError("invalid header: expected date,category,amount")

    if len(rows_raw) == 1:
        return []

    _date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    result = []
    for row in rows_raw[1:]:
        if len(row) != 3:
            raise ValueError(
                f"row width mismatch: expected 3 fields, got {len(row)}"
            )

        raw_date, raw_category, raw_amount = row

        # --- date validation ---
        raw_date = raw_date.strip()
        if not _date_re.match(raw_date):
            raise ValueError(f"invalid date format: {raw_date!r}")
        try:
            parsed = date.fromisoformat(raw_date)
        except ValueError:
            raise ValueError(f"invalid date: {raw_date!r}") from None
        # Ensure round-trip produces the canonical zero-padded form
        if parsed.isoformat() != raw_date:
            raise ValueError(f"non-canonical date: {raw_date!r}")

        # --- category validation ---
        category = raw_category.strip()
        if not category:
            raise ValueError("empty category")

        # --- amount validation ---
        raw_amount = raw_amount.strip()
        try:
            amount = Decimal(str(raw_amount))
        except (InvalidOperation, ValueError):
            raise ValueError(f"malformed amount: {raw_amount!r}")

        if not amount.is_finite():
            raise ValueError(f"nonfinite amount: {raw_amount!r}")

        amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        result.append(
            {
                "date": parsed.isoformat(),
                "category": category,
                "amount": str(amount),
            }
        )

    return result


def totals(rows):
    """Aggregate *rows* (output of :func:`parse_ledger`) by category.

    Returns a ``dict`` with keys sorted lexicographically and values as
    two-decimal-place strings.  Negative amounts are supported.
    """
    buckets = {}
    for row in rows:
        cat = row["category"]
        buckets[cat] = buckets.get(cat, Decimal("0")) + Decimal(row["amount"])

    quantized = {
        k: str(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        for k, v in sorted(buckets.items())
    }
    return quantized


def _cli_main():
    """Read CSV from stdin, print JSON ``{"rows":...,"totals":...}`` to stdout."""
    try:
        text = sys.stdin.read()
        rows = parse_ledger(text)
        totals_map = totals(rows)
        output = json.dumps(
            {"rows": rows, "totals": totals_map}, ensure_ascii=False, indent=2
        )
        sys.stdout.write(output)
        sys.stdout.write("\n")
    except ValueError as exc:
        sys.stderr.write(f"error: {exc}\n")
        sys.exit(2)


if __name__ == "__main__":
    _cli_main()
