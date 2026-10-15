# csv-ledger

Normalize CSV ledger rows and aggregate exact decimal amounts using Python's `decimal` module.

## API

### `parse_ledger(text: str) -> list[dict]`

Parse a CSV string with the exact header `date,category,amount`. Returns a list of dicts
preserving row order and Unicode. Each dict has keys `date` (ISO `YYYY-MM-DD`),
`category` (stripped, non-empty), and `amount` (a two-decimal string quantised with
`ROUND_HALF_UP`).

**Validation rules — raises `ValueError` on:**

- Blank or whitespace-only input
- Header that is not exactly `date,category,amount`
- Rows with field count ≠ 3
- Non-canonical or calendar-invalid dates (e.g. `2024-1-01`, `2023-02-29`)
- Empty category after stripping
- Malformed, NaN, or Infinity amounts

### `totals(rows: list[dict]) -> dict[str, str]`

Aggregate amounts by category. Returns a dict with lexicographically sorted keys and
two-decimal string values. Negative amounts are allowed.

## CLI

```bash
python module.py < input.csv
```

Prints JSON `{"rows": ..., "totals": ...}` with `ensure_ascii=False`. On invalid input
exits with code **2** and a concise error message on stderr (no traceback).

## Rounding

All amounts are quantised to 2 decimal places using `decimal.ROUND_HALF_UP`, which rounds
halfway cases away from zero (e.g. `1.005 → 1.01`, `-2.675 → -2.68`).

## References

- [decimal.ROUND_HALF_UP](https://docs.python.org/3/library/decimal.html#decimal.ROUND_HALF_UP)
- [json module](https://docs.python.org/3/library/json.html)
