"""CSV ledger normaliser: parse rows and aggregate totals."""

import csv
import io
import json
import sys
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

TWO_PLACES = Decimal("0.01")


def parse_ledger(text):
    """Parse a CSV string with header ``date,category,amount``.

    Returns a list of dicts preserving row order.

    Raises ValueError on blank input, wrong header, malformed rows,
    invalid calendar dates, non-numeric or nonfinite amounts, or
    wrong column counts.  Header-only input returns ``[]``.
    """
    if not text or not text.strip():
        raise ValueError("blank input")

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)

    if not rows or rows[0] != ["date", "category", "amount"]:
        raise ValueError("malformed header")

    data = rows[1:]
    # If the only "row" after header is an empty trailing line, return []
    if len(data) == 1 and data[0] == [""]:
        return []
    if not data:
        return []

    result = []
    for row in data:
        if len(row) != 3:
            raise ValueError("wrong row width")

        date_str, cat, amt = row[0].strip(), row[1].strip(), row[2].strip()

        if not _valid_date(date_str):
            raise ValueError(f"invalid date: {date_str}")

        if not cat:
            raise ValueError("empty category")

        result.append({
            "date": date_str,
            "category": cat,
            "amount": str(_parse_amount(amt)),
        })

    return result


def totals(rows):
    """Aggregate *rows* (parse_ledger output) by category.

    Returns a dict in lexicographic category order with two-decimal
    string values.
    """
    buckets = {}
    for r in rows:
        buckets[r["category"]] = buckets.get(r["category"], Decimal("0")) + Decimal(r["amount"])
    return {
        cat: str(buckets[cat].quantize(TWO_PLACES, rounding=ROUND_HALF_UP))
        for cat in sorted(buckets)
    }


# ── helpers ───────────────────────────────────────────────────────────

def _valid_date(s):
    """Return True when *s* is a canonical ``YYYY-MM-DD`` calendar date."""
    if len(s) != 10 or s[4] != "-" or s[7] != "-":
        return False
    try:
        parts = s.split("-")
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
    except (ValueError, IndexError):
        return False
    # Enforce canonical format: zero-padded
    if f"{y:04d}-{m:02d}-{d:02d}" != s:
        return False
    # Calendar validation via datetime (catches Feb 29 etc.)
    import datetime
    try:
        datetime.date(y, m, d)
    except ValueError:
        return False
    return True


def _parse_amount(s):
    """Parse a numeric string into a quantised Decimal (2 dp, ROUND_HALF_UP)."""
    if not s:
        raise ValueError("empty amount")
    # Reject non-finite / sentinel values early
    low = s.lower().replace("+", "")
    if low in ("nan", "infinity", "inf", "-inf", "+inf", "-infinity", "+infinity"):
        raise ValueError(f"nonfinite amount: {s}")
    try:
        d = Decimal(s)
    except InvalidOperation:
        raise ValueError(f"malformed amount: {s}")
    if not d.is_finite():
        raise ValueError(f"nonfinite amount: {s}")
    return d.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


# ── CLI ───────────────────────────────────────────────────────────────

def main():
    data = sys.stdin.read()
    try:
        rows = parse_ledger(data)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
    result = {
        "rows": rows,
        "totals": totals(rows),
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
