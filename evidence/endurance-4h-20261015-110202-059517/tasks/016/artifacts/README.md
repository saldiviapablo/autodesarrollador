# csv-ledger

Normalize CSV ledger rows and aggregate exact decimal amounts using Python's
`Decimal` for precise arithmetic.

## API

### `parse_ledger(text: str) -> list[dict]`

Accepts a CSV string with the **exact** header `date,category,amount` and
returns a list of dicts with keys `date`, `category`, `amount`.

**Validation rules**

| Rule | Behaviour |
|---|---|
| Header | Must be exactly `date,category,amount` (case-sensitive). |
| Row width | Every data row must have exactly 3 fields. |
| Date | Parsed strictly via `datetime.date.fromisoformat`; only canonical `YYYY-MM-DD` is accepted. Rejects non-canonical formats (e.g. `2024-1-1`) and invalid calendar dates (e.g. `2023-02-29`). |
| Category | Stripped of leading/trailing whitespace; must be non-empty. |
| Amount | Parsed as `Decimal(str(value))` and quantized to **2 decimal places** using `ROUND_HALF_UP`. Non-finite values (`NaN`, `Infinity`) and malformed strings raise `ValueError`. |
| Blank input | Empty or whitespace-only string raises `ValueError`. |
| Header-only | Returns an empty list `[]`. |

Row order and Unicode characters are preserved throughout.

### `totals(rows: list[dict]) -> dict[str, str]`

Aggregates the `amount` field of `parse_ledger` output by `category` using
exact `Decimal` arithmetic.

Returns a `dict` whose keys are in **lexicographic** order and whose values
are two-decimal-place string representations of the sums. Negative amounts
are supported.

```python
from module import parse_ledger, totals

rows = parse_ledger("""\
date,category,amount
2024-01-01,Z,0.10
2024-01-01,A,0.20
2024-01-02,Z,0.20
""")

print(totals(rows))
# → {'A': '0.20', 'Z': '0.30'}
```

## CLI

```bash
# Valid input — prints JSON to stdout (exit 0)
$ printf 'date,category,amount\n2024-01-01,Ñ,1.005\n' | python module.py
{"rows": [...], "totals": {"Ñ": "1.01"}}

# Invalid input — prints concise error to stderr, no traceback (exit 2)
$ echo 'bad' | python module.py
error: invalid header: expected ['date', 'category', 'amount'], got ['bad']
# exit code: 2
```

The JSON output always has two keys:

| Key | Value |
|---|---|
| `rows` | List of parsed row dicts (identical to `parse_ledger` output). |
| `totals` | Aggregated totals dict (identical to `totals(rows)` output). |

Output uses `ensure_ascii=False` so Unicode characters are written directly.

## Decimal rounding reference

The module uses Python's `decimal` module with `ROUND_HALF_UP` (the "commercial
rounding" rule taught in most schools):

| Input | Quantized |
|---|---|
| `1.005` | `1.01` |
| `2.675` | `2.68` |
| `0.105` | `0.11` |
| `-2.675` | `-2.68` |

This avoids floating-point drift that would occur with `float` or `round()`.

## Testing

```bash
python test_module.py
python build.py
```

Both must exit with code 0.
