# csv-ledger

Normalize CSV ledger rows and aggregate exact decimal amounts.

## API

### `parse_ledger(text: str) -> list[dict]`

Parse a CSV string with the exact header `date,category,amount`.

- **Header validation**: The first row must be exactly `date,category,amount`. Any deviation raises `ValueError`.
- **Date validation**: Strict ISO YYYY-MM-DD format. Dates are validated against the Gregorian calendar (e.g., `2023-02-29` is invalid because 2023 is not a leap year; `2024-1-01` raises `ValueError` for noncanonical format).
- **Category**: Stripped of whitespace; blank categories raise `ValueError`.
- **Amount**: Parsed as `Decimal(str(x))` and quantized to two decimal places using `ROUND_HALF_UP`. Nonfinite values (`NaN`, `Infinity`) and malformed strings raise `ValueError`.
- **Row width**: Each row must have exactly 3 fields. Extra or missing fields raise `ValueError`.
- **Blank input**: Raises `ValueError`.
- **Header-only input**: Returns an empty list `[]`.
- **Unicode**: Preserved through CSV parsing and output.

Example:

```python
from module import parse_ledger

rows = parse_ledger(
    "date,category,amount\n"
    "2024-02-29, Café ,1.005\n"
    '2024-03-01,"Comida, casa",-2.675\n'
)
# Returns:
# [
#   {"date": "2024-02-29", "category": "Café", "amount": "1.01"},
#   {"date": "2024-03-01", "category": "Comida, casa", "amount": "-2.68"}
# ]
```

### `totals(rows: list[dict]) -> dict[str, str]`

Aggregate parsed rows by category using `Decimal` arithmetic.

- Returns a dictionary with keys sorted **lexicographically**.
- Values are two-decimal strings (quantized with `ROUND_HALF_UP`).
- Negative amounts are allowed and aggregated correctly.

Example:

```python
from module import totals

result = totals([
    {"date": "2024-01-01", "category": "Z", "amount": "0.10"},
    {"date": "2024-01-01", "category": "A", "amount": "0.20"},
    {"date": "2024-01-02", "category": "Z", "amount": "0.20"},
])
# Returns: {"A": "0.20", "Z": "0.30"}
```

## CLI

```bash
echo "date,category,amount
2024-01-01,Ñ,1.005" | python module.py
```

Output (JSON):

```json
{"rows": [{"date": "2024-01-01", "category": "Ñ", "amount": "1.01"}], "totals": {"Ñ": "1.01"}}
```

- **Success**: Exit code `0`, JSON to `stdout` with `ensure_ascii=False`.
- **Error**: Exit code `2`, concise error message to `stderr` (no traceback).

## Decimal Rounding

All amounts use Python's `decimal.Decimal` with `ROUND_HALF_UP` to two decimal places:

| Input  | Output |
|--------|--------|
| 1.005  | 1.01   |
| 2.675  | 2.68   |
| -2.675 | -2.68  |

This follows the IEEE 754 standard for commercial rounding, avoiding binary floating-point artifacts.

## Validation Errors

The following inputs raise `ValueError`:

- Blank or whitespace-only input
- Wrong header (e.g., `wrong,header`)
- Invalid dates (e.g., `2023-02-29`, `2024-1-01`)
- Empty categories
- Nonfinite amounts (`NaN`, `Infinity`)
- Malformed amounts (e.g., `bad`, non-numeric strings)
- Row width mismatch (too few or too many fields)

## Unicode

All Unicode characters are preserved throughout parsing and output. Category names, dates, and amounts support full Unicode (e.g., `Ñ`, ` café `, emojis if present in CSV fields).
