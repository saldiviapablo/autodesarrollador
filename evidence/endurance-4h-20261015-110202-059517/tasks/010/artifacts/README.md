# csv-ledger

Normalize CSV ledger rows and aggregate exact-decimal amounts.

## API

### `parse_ledger(text: str) -> list[dict]`

Parse a CSV string with the exact header `date,category,amount`.

- **date** — ISO calendar-valid `YYYY-MM-DD` (zero-padded month/day).
  Rejects non-canonical formats such as `2024-1-01` or invalid calendar
  dates like `2023-02-29`.
- **category** — stripped, non-empty Unicode string.
- **amount** — quantized to two decimal places using `Decimal(str(x))`
  with `ROUND_HALF_UP` rounding.

Returns a list of dicts in original row order.
Blank input raises `ValueError`; header-only input returns `[]`.

#### Validation (all raise `ValueError`)

| Condition | Example |
|---|---|
| Empty / whitespace-only input | `""` |
| Wrong header | `"wrong,header\n"` |
| Invalid calendar date | `"2023-02-29"` |
| Non-canonical date format | `"2024-1-01"` |
| Empty category | `"2024-01-01,,1"` |
| Non-finite amount (`NaN`, `Infinity`) | `"2024-01-01,X,NaN"` |
| Malformed amount | `"2024-01-01,X,bad"` |
| Row width mismatch | `"2024-01-01,X"` or `"2024-01-01,X,1,extra"` |

### `totals(rows: list[dict]) -> dict[str, str]`

Aggregate `amount` values from `parse_ledger` output by `category`.

- Returns a `dict` with categories in **lexicographic** order.
- Values are two-decimal-place strings.
- Negative amounts are supported.

### Unicode

All strings are handled natively — accents, CJK, emoji are preserved.

## CLI

```bash
python module.py < input.csv
```

Reads CSV from stdin and prints a JSON object:

```json
{
  "rows": [...],
  "totals": {...}
}
```

- Exit code **0** on success.
- Exit code **2** on invalid input (concise stderr, no traceback).

## Rounding reference

Uses Python's `decimal.ROUND_HALF_UP` — the midpoint digit `5` rounds
**away from zero**:

| Input | Result |
|---|---|
| `1.005` | `1.01` |
| `16.125` | `16.13` |
| `-2.675` | `-2.68` |

## Reference

- [Python `decimal` documentation](https://docs.python.org/3/library/decimal.html)
- [ISO 8601 date format](https://en.wikipedia.org/wiki/ISO_8601)
