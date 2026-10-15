"""CSV ledger normaliser: parse rows, aggregate totals, CLI entry-point."""
import csv
import io
import json
import sys
from calendar import isleap
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def _is_valid_iso_date(s: str) -> bool:
    """Return True only for canonical YYYY-MM-DD with a real calendar date."""
    if len(s) != 10 or s[4] != '-' or s[7] != '-':
        return False
    try:
        y, m, d = int(s[:4]), int(s[5:7]), int(s[8:10])
    except ValueError:
        return False
    if m < 1 or m > 12 or d < 1:
        return False
    # day-in-month cap per Gregorian month
    days_in_month = (0, 31, 29 if isleap(y) else 28, 31, 30, 31, 30,
                     31, 31, 30, 31, 30, 31)
    if d > days_in_month[m]:
        return False
    return True


def _quantize_amount(raw: str) -> str:
    """Convert *raw* to a two-decimal quantised string via Decimal."""
    try:
        val = Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"nonfinite/malformed amount: {raw!r}")
    if not val.is_finite():
        raise ValueError(f"nonfinite amount: {raw!r}")
    return str(val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def parse_ledger(text: str) -> list[dict]:
    """Parse a CSV string with exact header ``date,category,amount``.

    Returns a list of dicts (inserted in row order) with keys
    ``date``, ``category``, ``amount``.

    Raises ``ValueError`` on blank input, bad header, wrong row width,
    invalid/non-canonical dates, empty categories, or malformed/nonfinite
    amounts.  Header-only input returns ``[]``.
    """
    if not text or not text.strip():
        raise ValueError("blank input")

    reader = csv.reader(io.StringIO(text))
    rows_raw = list(reader)

    if not rows_raw:
        raise ValueError("no rows")

    header = [h.strip().lower() for h in rows_raw[0]]
    if header != ["date", "category", "amount"]:
        raise ValueError(f"invalid header: {rows_raw[0]}")

    results: list[dict] = []
    for row in rows_raw[1:]:
        if len(row) != 3:
            raise ValueError(f"row width mismatch: {row}")

        date_raw, cat_raw, amt_raw = row
        date = date_raw.strip()
        category = cat_raw.strip()
        amount_raw = amt_raw.strip()

        if not _is_valid_iso_date(date):
            raise ValueError(f"invalid date: {date!r}")
        if not category:
            raise ValueError("empty category")
        amount = _quantize_amount(amount_raw)

        results.append({"date": date, "category": category, "amount": amount})

    return results


def totals(rows: list[dict] | str) -> dict:
    """Aggregate *rows* (parse_ledger output or raw CSV string) by category.

    Returns a ``dict`` keyed by lexicographic category name; values are
    two-decimal strings produced by exact ``Decimal`` addition +
    ``ROUND_HALF_UP`` quantisation.
    """
    if isinstance(rows, str):
        rows = parse_ledger(rows)

    buckets: dict[str, Decimal] = {}
    for r in rows:
        cat = r["category"]
        amt = Decimal(r["amount"])
        buckets[cat] = buckets.get(cat, Decimal("0")) + amt

    return {
        cat: str(buckets[cat].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        for cat in sorted(buckets)
    }


# --- CLI --------------------------------------------------------------------
if __name__ == "__main__":
    try:
        raw = sys.stdin.read()
        parsed = parse_ledger(raw)
        total = totals(parsed)
        print(json.dumps({"rows": parsed, "totals": total}, ensure_ascii=False))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
