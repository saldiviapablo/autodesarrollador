# csv-ledger

Normalize CSV ledger rows and aggregate exact decimal amounts.

## API

### `parse_ledger(text) -> list[dict]`

Parse a CSV string with the exact header `date,category,amount` and return a list of dicts.

**Validation rules** (all raise `ValueError` on bad input):

| Field     | Rules                                                                 |
|-----------|-----------------------------------------------------------------------|
| `date`    | Must match `YYYY-MM-DD` exactly (zero-padded). Must be a valid ISO calendar date (e.g., `2023-02-29` is rejected). |
| `category`| Stripped of leading/trailing whitespace. Empty after strip is rejected. |
| `amount`  | Converted via `Decimal(str(x))`, quantized to 2 decimal places using `ROUND_HALF_UP`. Nonfinite (`NaN`, `Infinity`) and malformed values raise `ValueError`. |

- Blank input (empty string or only whitespace) raises `ValueError`.
- Header-only input (no data rows) returns an empty list `[]`.
- Row order and Unicode content are preserved.

### `totals(rows) -> dict[str, str]`

Aggregate rows (output of `parse_ledger`) by category.

- Returns a `dict` with keys sorted lexicographically.
- Values are strings with exactly two decimal digits.
- Negative amounts are supported.

## CLI

```bash
echo 'date,category,amount
2024-01-01,Alimentación,10.50
2024-01-02,Café,5.125' | python module.py
```

**Output** (JSON):

```json
{
  "rows": [
    {"date": "2024-01-01", "category": "Alimentación", "amount": "10.50"},
    {"date": "2024-01-02", "category": "Café", "amount": "5.13"}
  ],
  "totals": {
    "Alimentación": "10.50",
    "Café": "5.13"
  }
}
```

- Reads CSV from **stdin**.
- Prints JSON to **stdout** with `ensure_ascii=False` (preserves Unicode).
- Invalid input: prints a concise error message to **stderr** (no traceback) and exits with code **2**.

## Decimal rounding

All amounts use Python's `decimal.Decimal` with `ROUND_HALF_UP`:

```python
Decimal("1.005").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)  # "1.01"
Decimal("2.675").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)  # "2.68"
```

This matches traditional "round half up" behaviour (not banker's rounding).

## Unicode

Input and output fully support Unicode (e.g., `Ñ`, `é`, `ñ`, `café`). CSV quoting is handled via Python's `csv` module, so fields containing commas or quotes are parsed correctly.

## Reference

- [Python `decimal` module](https://docs.python.org/3/library/decimal.html)
- [ISO 8601 date format](https://en.wikipedia.org/wiki/ISO_8601)
- [CSV RFC 4180](https://www.rfc-editor.org/rfc/rfc4180)
