"""CSV ledger normalizer and aggregator with exact Decimal arithmetic."""

import csv
import io
import json
import sys
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date


def parse_ledger(text: str) -> list[dict]:
    """Parse a CSV string into a list of ledger dicts.

    Header must be exactly ``date,category,amount``.
    Dates are validated as ISO YYYY-MM-DD using :class:`datetime.date`.
    Amounts are quantized to two decimals with ``Decimal(str(x)) ROUND_HALF_UP``.
    Categories are stripped (must be nonempty).
    Blank input raises ``ValueError``.
    """
    if not text or not text.strip():
        raise ValueError("blank input")

    reader = csv.reader(io.StringIO(text))
    rows_raw = list(reader)

    if not rows_raw:
        raise ValueError("empty csv")

    header = [h.strip() for h in rows_raw[0]]
    if header != ["date", "category", "amount"]:
        raise ValueError("invalid header")

    if len(rows_raw) == 1:
        return []

    result: list[dict] = []
    for row in rows_raw[1:]:
        if len(row) != 3:
            raise ValueError(f"row width mismatch: expected 3, got {len(row)}")

        date_str, category_str, amount_str = row

        # Validate date — must be YYYY-MM-DD and parse to a valid ISO calendar date
        date_stripped = date_str.strip()
        if len(date_stripped) != 10 or date_stripped[4] != '-' or date_stripped[7] != '-':
            raise ValueError(f"invalid date format: {date_str!r}")
        try:
            parsed_date = date(
                int(date_stripped[0:4]),
                int(date_stripped[5:7]),
                int(date_stripped[8:10])
            )
            # Verify roundtrip to catch formats like 2024-1-01
            if parsed_date.isoformat() != date_stripped:
                raise ValueError(f"noncanonical date: {date_str!r}")
        except (ValueError, OverflowError) as exc:
            raise ValueError(f"invalid date: {date_str!r}") from exc

        # Category: strip, reject empty
        category = category_str.strip()
        if not category:
            raise ValueError("empty category")

        # Amount: quantize to 2 decimals with ROUND_HALF_UP
        amount_raw = amount_str.strip()
        try:
            amount_dec = Decimal(amount_raw)
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"malformed amount: {amount_raw!r}") from exc

        if not amount_dec.is_finite():
            raise ValueError(f"nonfinite amount: {amount_raw!r}")

        amount_quantized = amount_dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        result.append({
            "date": parsed_date.isoformat(),
            "category": category,
            "amount": str(amount_quantized),
        })

    return result


def totals(rows: list[dict]) -> dict[str, str]:
    """Aggregate *rows* (output of :func:`parse_ledger`) by category.

    Returns a ``dict`` with keys sorted lexicographically and values as
    two-decimal strings.  Negative amounts are allowed.
    """
    agg: dict[str, Decimal] = {}
    for row in rows:
        cat = row["category"]
        amt = Decimal(row["amount"])
        agg[cat] = agg.get(cat, Decimal("0")) + amt

    return {k: str(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)) for k, v in sorted(agg.items())}


if __name__ == "__main__":
    import sys
    try:
        data = sys.stdin.read()
        rows = parse_ledger(data)
        out = {"rows": rows, "totals": totals(rows)}
        print(json.dumps(out, ensure_ascii=False))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
