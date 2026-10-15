# csv-ledger

Normalize CSV ledger rows and aggregate exact decimal amounts using Python's
:class:`~decimal.Decimal` — no floating-point arithmetic.

## Installation

```bash
pip install -r requirements.txt
```

(No external dependencies required; only the Python standard library.)

## API

### `parse_ledger(text: str) -> list[dict]`

Accepts a CSV string whose first line is the exact header
`date,category,amount`.  Returns a list of dicts with keys
`date`, `category`, `amount`, preserving row order and Unicode.

**Validation rules (raises `ValueError` on violation):**

| Field | Rule |
|---|---|
| Input | Blank / whitespace-only → rejected |
| Header | Must be exactly `date,category,amount` |
| Row width | Must have exactly 3 columns |
| `date` | Strict ISO `YYYY-MM-DD`; calendar-valid (e.g. no `2023-02-29`); non-canonical formats (e.g. `2024-1-01`) rejected |
| `category` | Non-empty after stripping whitespace |
| `amount` | Parsed via `Decimal(str(value))`, quantized to 2 decimal places with **ROUND_HALF_UP**; non-finite (`NaN`, `Infinity`) or non-numeric strings rejected |

**Header-only input** (`"date,category,amount\n"`) returns `[]`.

### `totals(rows: list[dict]) -> dict[str, str]`

Aggregates `amount` values (two-decimal strings) by `category`.  Returns a
dictionary keyed in **lexicographic** order with values as two-decimal
strings.  Negative amounts are allowed.

```python
from module import parse_ledger, totals

rows = parse_ledger(
    "date,category,amount\n"
    "2024-01-01,Z,0.10\n"
    "2024-01-01,A,0.20\n"
    "2024-01-02,Z,0.20\n"
)
print(totals(rows))  # {'A': '0.20', 'Z': '0.30'}
```

### Rounding

The module uses `Decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`.
This means:

- `10.125` → `"10.13"`
- `1.005` → `"1.01"`
- `-2.675` → `"-2.68"`

See the [official Python decimal documentation](https://docs.python.org/3/library/decimal.html) for details.

## CLI

```bash
python module.py < ledger.csv
```

Reads CSV from **stdin**, prints JSON to stdout:

```json
{"rows": [...], "totals": {...}}
```

Options:

- `ensure_ascii=False` — Unicode characters are preserved in output.
- On **valid** input → exit code `0`.
- On **invalid** input → exit code `2` with a concise error message to
  **stderr** (no traceback).

```bash
# Valid
echo -e "date,category,amount\n2024-01-01,Ñ,1.005" | python module.py
# → {"rows": [{"date":"2024-01-01","category":"Ñ","amount":"1.01"}], "totals":{"Ñ":"1.01"}}

# Invalid
echo "bad" | python module.py; echo $?
# → exit code 2
```

## Testing

```bash
python test_module.py
python build.py
```

Both must exit with code 0.

## Unicode

All strings are UTF-8.  Categories like `Café`, `Ñ`, or `日本語` are
preserved through parsing, aggregation, and CLI output.

## Dependencies

Python 3.7+ standard library only: `csv`, `io`, `json`, `sys`, `datetime`,
`decimal`, `pathlib`.
