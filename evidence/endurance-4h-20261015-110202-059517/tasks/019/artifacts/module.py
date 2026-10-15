"""CSV-ledger: normalize ledger rows and aggregate exact decimal amounts."""
import csv
import io
import json
import sys
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


EXPECTED_HEADER = ["date", "category", "amount"]


def parse_ledger(text: str) -> list[dict]:
    """Parse CSV ledger text into a list of row dicts.

    Validation rules
    ----------------
    * *text* must not be blank / whitespace-only.
    * The first line must match the header ``date,category,amount`` exactly.
    * Every data row must have exactly 3 comma-separated fields.
    * ``date`` is validated as a strict ISO ``YYYY-MM-DD`` (rejects
      non-canonical forms such as ``2024-1-01`` and invalid calendar
      dates like ``2023-02-29``).
    * ``category`` must be a non-empty string after stripping whitespace.
    * ``amount`` is converted via ``Decimal(str(x))`` and quantised to
      2 decimal places with ``ROUND_HALF_UP``.  Non-finite values
      (``NaN``, ``Infinity``) and malformed strings raise ``ValueError``.

    Parameters
    ----------
    text : str
        CSV content (UTF-8).  Header-only input returns ``[]``.

    Returns
    -------
    list[dict]
        Rows in original order, each dict keyed by ``date``,
        ``category``, ``amount`` (amount is a 2-decimal string).

    Raises
    ------
    ValueError
        On any validation failure.
    """
    if not text or not text.strip():
        raise ValueError("blank input")

    lines = text.splitlines()
    reader = csv.reader(io.StringIO(text))
    rows_raw = list(reader)

    if not rows_raw:
        raise ValueError("blank input")

    header = [h.strip().lower() for h in rows_raw[0]]
    if header != EXPECTED_HEADER:
        raise ValueError(
            f"invalid header: expected {','.join(EXPECTED_HEADER)}, "
            f"got {','.join(rows_raw[0])}"
        )

    if len(rows_raw) == 1:
        # Header-only -> no data rows
        return []

    results: list[dict] = []
    for line_idx, fields in enumerate(rows_raw[1:], start=2):
        if len(fields) != 3:
            raise ValueError(
                f"row {line_idx}: expected 3 fields, got {len(fields)}"
            )

        date_str, category_str, amount_str = fields

        # --- date validation (strict ISO YYYY-MM-DD) ---
        date_str = date_str.strip()
        # Reject non-canonical formats: must be exactly YYYY-MM-DD with
        # zero-padded month and day (e.g. reject 2024-1-01, 2024/01/01).
        parts = date_str.split("-")
        if len(parts) != 3:
            raise ValueError(f"row {line_idx}: invalid date format '{date_str}'")
        y_str, m_str, d_str = parts
        if len(y_str) != 4 or len(m_str) != 2 or len(d_str) != 2:
            raise ValueError(
                f"row {line_idx}: date must be YYYY-MM-DD (got '{date_str}')"
            )
        try:
            year = int(y_str)
            month = int(m_str)
            day = int(d_str)
        except ValueError:
            raise ValueError(
                f"row {line_idx}: non-numeric date in '{date_str}'"
            )
        # Use datetime to validate the actual calendar date
        try:
            datetime(year, month, day)
        except ValueError:
            raise ValueError(
                f"row {line_idx}: invalid calendar date '{date_str}'"
            )
        # Re-format to canonical ISO form (ensures zero-padding preserved)
        canonical_date = f"{year:04d}-{month:02d}-{day:02d}"

        # --- category validation ---
        category = category_str.strip()
        if not category:
            raise ValueError(f"row {line_idx}: empty category")

        # --- amount validation ---
        amount_raw = amount_str.strip()
        if not amount_raw:
            raise ValueError(f"row {line_idx}: empty amount")
        try:
            amount_dec = Decimal(str(amount_raw))
        except (InvalidOperation, ValueError):
            raise ValueError(
                f"row {line_idx}: malformed amount '{amount_raw}'"
            )
        if not amount_dec.is_finite():
            raise ValueError(
                f"row {line_idx}: non-finite amount '{amount_raw}'"
            )
        amount_quantized = amount_dec.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        results.append({
            "date": canonical_date,
            "category": category,
            "amount": str(amount_quantized),
        })

    return results


def totals(rows: list[dict]) -> dict[str, str]:
    """Aggregate ``parse_ledger`` output by category.

    Parameters
    ----------
    rows : list[dict]
        Output of :func:`parse_ledger`.

    Returns
    -------
    dict[str, str]
        Lexicographically ordered dict mapping category -> 2-decimal
        string sum.
    """
    sums: dict[str, Decimal] = {}
    for row in rows:
        cat = row["category"]
        amt = Decimal(row["amount"])
        sums[cat] = sums.get(cat, Decimal("0")) + amt

    return {
        cat: str(sums[cat].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        for cat in sorted(sums)
    }


def main() -> None:
    """CLI entry-point: read CSV from stdin, print JSON to stdout."""
    try:
        text = sys.stdin.read()
        rows = parse_ledger(text)
        total = totals(rows)
        output = json.dumps(
            {"rows": rows, "totals": total}, ensure_ascii=False, indent=2
        )
        print(output)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
