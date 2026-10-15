# csv-ledger

Normalizes CSV ledger rows and aggregates exact decimal amounts using Python's `decimal` module for financial-grade precision.

## API

### `parse_ledger(text) → list[dict]`

Parses a CSV string whose first line must be the exact header `date,category,amount`.  Each subsequent row becomes a dict with keys `date`, `category`, and `amount`.

- **date** — validated ISO 8601 calendar date (`YYYY-MM-DD`, zero-padded month/day).  Noncanonical formats such as `2024-1-01` are rejected.
- **category** — stripped, non-empty Unicode string.
- **amount** — parsed and quantised to two decimal places via `Decimal` with `ROUND_HALF_UP` rounding.

**Rounding:** The `Decimal` module represents numbers exactly (no IEEE-754 float).  For example:

```python
>>> from decimal import ROUND_HALF_UP
>>> Decimal("13.125").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
Decimal('13.13')
>>> Decimal("2.675").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
Decimal('2.68')
```

Values are returned as two-decimal **string** representations (e.g. `"13.13"`).

**Header-only input** (e.g. `"date,category,amount\n"`) returns `[]`.

### `totals(rows) → dict`

Aggregates a list returned by `parse_ledger` by `category`.  Returns a `dict` with:

- Keys sorted in **lexicographic** order.
- Values as two-decimal **string** amounts (e.g. `"42.50"`).

```python
>>> rows = parse_ledger("date,category,amount\n2024-01-01,Z,0.10\n2024-01-01,A,0.20\n")
>>> totals(rows)
{'A': '0.20', 'Z': '0.10'}
```

Negative amounts are supported.

## CLI

```bash
python module.py < input.csv
```

Reads CSV from **stdin** and prints a JSON object to **stdout**:

```json
{"rows": [...], "totals": {...}}
```

- Output uses `ensure_ascii=False` so Unicode characters (e.g. `Ñ`, `É`) are preserved.
- On invalid input the process exits with **code 2** and prints a concise error message to **stderr** (no Python traceback).

### Examples

```bash
# Valid input
$ echo 'date,category,amount
2024-01-01,Salario,1500.50
2024-01-02,Comida,-35.75' | python module.py

# Invalid input → exit 2
$ echo 'bad' | python module.py
malformed header
```

## Validation rules

| Field      | Rule                                                                 |
|------------|----------------------------------------------------------------------|
| Header     | Must be exactly `date,category,amount` (comma-separated, lowercase). |
| Date       | ISO 8601 `YYYY-MM-DD`, zero-padded, calendar-valid (e.g. rejects Feb 29 on non-leap years). |
| Category   | Stripped, non-empty Unicode string.                                  |
| Amount     | Finite numeric value; quantised to 2 dp via `ROUND_HALF_UP`.         |
| Row width  | Exactly 3 columns per row.                                           |
| Blank input| Raises `ValueError`.                                                 |

## Unicode

The module preserves Unicode in both category names and output.  CSV parsing is handled by Python's standard `csv` module, which supports quoted fields (e.g. `"Comida, casa"`).

## Decimal reference

- **Python docs:** <https://docs.python.org/3/library/decimal.html>
- **RFC 4180 (CSV):** <https://www.rfc-editor.org/rfc/rfc4180>
- **ISO 8601:** <https://en.wikipedia.org/wiki/ISO_8601>

## Error handling

Any validation failure raises `ValueError` with a concise message.  The CLI catches exceptions, prints the message to stderr, and exits with code 2 — no tracebacks exposed to the user.
