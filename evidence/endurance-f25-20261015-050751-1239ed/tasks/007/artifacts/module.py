"""CSV ledger normalizer and aggregator — exact Decimal arithmetic."""
import csv
import io
import json
import sys
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

_EXPECTED_HEADER = ["date", "category", "amount"]


def parse_ledger(text: str) -> list[dict]:
    """Normalize a CSV string with header ``date,category,amount`` into dicts.

    Validation rules
    ----------------
    * **Blank input** (empty / whitespace-only) → ``ValueError``.
    * **Header** must match ``date,category,amount`` exactly (case-sensitive,
      stripped).  Any mismatch raises ``ValueError``.
    * **Date** — must be ``YYYY-MM-DD`` where the parsed date is canonical
      (``isoformat()`` reproduces the input), i.e. the calendar date is valid
      (rejects ``2023-02-29``) and zero-padded (rejects ``2024-1-01``).
    * **Category** — stripped value must be non-empty.
    * **Amount** — must be a finite number; string is quantised to 2 decimals
      with ``ROUND_HALF_UP``.  Rejects ``NaN``, ``Infinity``, non-numeric
      strings.
    * **Row width** — every data row must have exactly 3 fields.

    Returns
    -------
    list[dict] — ``[{"date": "...", "category": "...", "amount": "..."}, ...]``
    with amounts as 2-decimal strings preserving row order and Unicode.

    Raises
    ------
    ValueError on any validation failure.
    """
    if not text or not text.strip():
        raise ValueError("blank input")

    reader = csv.reader(io.StringIO(text))
    rows_raw = list(reader)

    if not rows_raw:
        raise ValueError("empty CSV")

    # --- header ---
    header = [h.strip() for h in rows_raw[0]]
    if header != _EXPECTED_HEADER:
        raise ValueError(
            f"invalid header: expected {_EXPECTED_HEADER!r}, got {header!r}"
        )

    result: list[dict] = []
    for row in rows_raw[1:]:
        if len(row) != 3:
            raise ValueError(
                f"row width {len(row)} != 3: {row!r}"
            )

        raw_date, raw_category, raw_amount = row

        # date validation — strict YYYY-MM-DD + canonical
        raw_date = raw_date.strip()
        if len(raw_date) != 10 or raw_date[4] != '-' or raw_date[7] != '-':
            raise ValueError(f"invalid date format: {raw_date!r}")
        try:
            d = date(int(raw_date[:4]), int(raw_date[5:7]), int(raw_date[8:10]))
        except ValueError:
            raise ValueError(f"invalid date: {raw_date!r}")
        if d.isoformat() != raw_date:
            raise ValueError(f"non-canonical date: {raw_date!r}")

        # category
        category = raw_category.strip()
        if not category:
            raise ValueError("empty category")

        # amount
        amount_raw = raw_amount.strip()
        try:
            dec = Decimal(str(amount_raw))
        except (InvalidOperation, ValueError):
            raise ValueError(f"invalid amount: {amount_raw!r}")
        if not dec.is_finite():
            raise ValueError(f"non-finite amount: {amount_raw!r}")
        amount_str = str(dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        result.append({
            "date": d.isoformat(),
            "category": category,
            "amount": amount_str,
        })

    return result


def totals(rows: list[dict]) -> dict[str, str]:
    """Aggregate *rows* (output of :func:`parse_ledger`) by category.

    Returns
    -------
    dict[str, str] — lexicographically sorted keys, values are 2-decimal
    strings.  Negative amounts are allowed.
    """
    agg: dict[str, Decimal] = {}
    for row in rows:
        cat = row["category"]
        amt = Decimal(str(row["amount"]))
        agg[cat] = agg.get(cat, Decimal("0")) + amt

    return {
        k: str(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        for k, v in sorted(agg.items())
    }


def _cli() -> None:
    """CLI entry-point: read CSV from stdin, print JSON to stdout."""
    import os
    try:
        text = sys.stdin.read()
        rows = parse_ledger(text)
        t = totals(rows)
        print(json.dumps({"rows": rows, "totals": t}, ensure_ascii=False))
    except (ValueError, KeyError, TypeError) as exc:
        # Concise error without traceback; exit code 2.
        sys.stderr.write(f"error: {exc}\n")
        sys.exit(2)


if __name__ == "__main__":
    _cli()
