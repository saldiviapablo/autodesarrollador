"""CSV ledger normalizer and exact-decimal aggregator.

API
---
parse_ledger(text: str) -> list[dict]
    Parse a CSV string with exact header ``date,category,amount``.
    Returns a list of dicts with keys ``date`` (``YYYY-MM-DD``),
    ``category`` (stripped, non-empty Unicode string), and ``amount``
    (quantized to two decimal places via ``Decimal(str(x))`` ROUND_HALF_UP).

totals(rows: list[dict]) -> dict[str, str]
    Aggregate ``amount`` values from :func:`parse_ledger` output by
    ``category``.  Returns a ``dict`` in lexicographic category order
    with two-decimal-string values.

CLI
---
    python module.py < input.csv
    Reads CSV from stdin, prints ``{"rows":..., "totals":...}`` to stdout.
    Invalid input causes exit code 2 with a concise stderr message.
"""

import csv
import io
import json
import sys
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date

TWO_PLACES = Decimal("0.01")


def _parse_amount(raw: str) -> str:
    """Quantise a single amount string to two decimal digits."""
    value = Decimal(str(raw))
    if not value.is_finite():
        raise ValueError(f"non-finite amount: {raw!r}")
    return str(value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP))


def parse_ledger(text: str) -> list[dict]:
    """Parse CSV ledger text and return normalised rows."""
    if not text or not text.strip():
        raise ValueError("blank input")

    reader = csv.reader(io.StringIO(text))
    rows_iter = iter(reader)

    # --- header -----------------------------------------------------------
    try:
        header = next(rows_iter)
    except StopIteration:
        raise ValueError("empty input")

    if [h.strip() for h in header] != ["date", "category", "amount"]:
        raise ValueError(f"invalid header: {header!r}")

    result: list[dict] = []

    for row in rows_iter:
        if len(row) != 3:
            raise ValueError(f"row width mismatch: {row!r}")

        raw_date, raw_category, raw_amount = row

        # date ----------------------------------------------------------------
        d = raw_date.strip()
        try:
            parts = d.split("-")
            if len(parts) != 3 or len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
                raise ValueError(f"non-YYYY-MM-DD date: {raw_date!r}")
            y, m, dd = int(parts[0]), int(parts[1]), int(parts[2])
            date(y, m, dd)  # raises ValueError on invalid calendar date
        except (ValueError, IndexError) as exc:
            raise ValueError(f"invalid date: {raw_date!r}") from exc

        # category ------------------------------------------------------------
        category = raw_category.strip()
        if not category:
            raise ValueError("empty category")

        # amount --------------------------------------------------------------
        amount_str = raw_amount.strip()
        try:
            amount_val = Decimal(amount_str)
        except (InvalidOperation, ValueError):
            raise ValueError(f"malformed amount: {raw_amount!r}")

        if not amount_val.is_finite():
            raise ValueError(f"non-finite amount: {raw_amount!r}")

        amount = str(amount_val.quantize(TWO_PLACES, rounding=ROUND_HALF_UP))

        result.append({"date": d, "category": category, "amount": amount})

    return result


def totals(rows: list[dict]) -> dict[str, str]:
    """Aggregate parsed rows by category, return sorted dict of two-decimal strings."""
    agg: dict[str, Decimal] = {}
    for row in rows:
        cat = row["category"]
        val = Decimal(row["amount"])
        agg[cat] = agg.get(cat, Decimal("0")) + val

    return {
        k: str(v.quantize(TWO_PLACES, rounding=ROUND_HALF_UP))
        for k, v in sorted(agg.items())
    }


# --- CLI -------------------------------------------------------------------
def _cli() -> int:
    """Read CSV from stdin, print JSON result."""
    try:
        text = sys.stdin.read()
        rows = parse_ledger(text)
        result = {
            "rows": rows,
            "totals": totals(rows),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except ValueError as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(_cli())
