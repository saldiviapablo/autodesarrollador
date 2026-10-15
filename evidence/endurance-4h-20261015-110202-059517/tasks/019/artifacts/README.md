# csv-ledger

Normalize CSV ledger rows and aggregate exact decimal amounts using Python's
`decimal` module for **exact** arithmetic (no floating-point drift).

## Installation

No external dependencies required.  The project uses the Python standard
library only (`csv`, `decimal`, `json`, `datetime`, `io`, `sys`).

```bash
python -m py_compile module.py   # quick syntax check
```

## API

### `parse_ledger(text: str) -> list[dict]`

Parse a CSV string with the **exact** header `date,category,amount`.

**Validation rules**

| Field    | Rule                                                                                   |
|----------|----------------------------------------------------------------------------------------|
| `text`   | Must not be blank or whitespace-only.                                                  |
| header   | First line must match `date,category,amount` exactly (after stripping & lower-casing). |
| rows     | Every data row must contain exactly **3** comma-separated fields.                      |
| `date`   | Strict ISO `YYYY-MM-DD`. Rejects non-canonical forms (e.g. `2024-1-01`, `2024/01/01`) and invalid calendar dates (e.g. `2023-02-29`). |
| `category` | Non-empty after stripping whitespace.                                                |
| `amount` | Valid finite number. Converted via `Decimal(str(x))` and quantised to **2 decimal places** with `ROUND_HALF_UP`. `NaN`, `Infinity`, and malformed strings raise `ValueError`. |

**Return value**

- A list of dicts `{"date": str, "category": str, "amount": str}` preserving
  original row order and Unicode characters.
- Header-only input (no data rows) returns `[]`.
- `amount` is always a string with exactly 2 decimal digits.

**Example**

```python
>>> from module import parse_ledger
>>> rows = parse_ledger("date,category,amount\n2024-01-15,Comida,25.125\n2024-01-16,Transporte,-3.50\n")
>>> rows
[{'date': '2024-01-15', 'category': 'Comida', 'amount': '25.13'},
 {'date': '2024-01-16', 'category': 'Transporte', 'amount': '-3.50'}]
```

### `totals(rows: list[dict]) -> dict[str, str]`

Aggregate amounts by category using exact `Decimal` arithmetic.

**Parameters**

- `rows`: Output of `parse_ledger()`.

**Return value**

- A `dict` with **lexicographically sorted** categories as keys and values
  as 2-decimal strings (the sum per category).
- Negative amounts are supported.

**Example**

```python
>>> from module import parse_ledger, totals
>>> rows = parse_ledger("date,category,amount\n2024-01-01,Z,0.10\n2024-01-01,A,0.20\n2024-01-02,Z,0.20\n")
>>> totals(rows)
{'A': '0.20', 'Z': '0.30'}
```

### `ValueError`

The following inputs raise `ValueError` (no traceback, just the message):

| Input                                        | Reason                     |
|----------------------------------------------|----------------------------|
| `""` or `"   "`                              | Blank input                |
| `"wrong,header\n"`                           | Invalid header             |
| `"date,category,amount\n2023-02-29,X,1\n"`   | Invalid calendar date      |
| `"date,category,amount\n2024-1-01,X,1\n"`    | Non-canonical date format  |
| `"date,category,amount\n2024-01-01,,1\n"`    | Empty category             |
| `"date,category,amount\n2024-01-01,X,NaN\n"` | Non-finite amount          |
| `"date,category,amount\n2024-01-01,X,1\n"`   | Row with wrong field count |

## CLI

Read a CSV from **stdin** and print JSON to **stdout**:

```bash
python module.py < input.csv
```

**Output format**

```json
{
  "rows": [
    {"date": "2024-01-15", "category": "Comida", "amount": "25.13"}
  ],
  "totals": {
    "Comida": "25.13"
  }
}
```

- `ensure_ascii=False` — Unicode characters are preserved (not escaped).
- On invalid input: prints a **concise** error message to **stderr** (no
  Python traceback) and exits with code **2**.
- On success: exits with code **0**.

**Example**

```bash
$ printf 'date,category,amount\n2024-01-01,Ñ,1.005\n' | python module.py
{
  "rows": [
    {
      "date": "2024-01-01",
      "category": "Ñ",
      "amount": "1.01"
    }
  ],
  "totals": {
    "Ñ": "1.01"
  }
}
```

**Error case**

```bash
$ printf 'bad' | python module.py
invalid header: expected date,category,amount, got bad
# exits with code 2
```

## Exact Decimal rounding

All monetary arithmetic uses Python's `decimal.Decimal` with `ROUND_HALF_UP`:

- `25.125` → `25.13` (rounds up at the midpoint)
- `-2.675` → `-2.68`
- `1.005` → `1.01`

This avoids floating-point drift issues inherent in `float` arithmetic.

## Unicode

The module preserves Unicode characters in category names and handles
multi-byte characters (e.g. `Ñ`, `é`, `café`) correctly throughout parsing,
aggregation, and JSON output.

## Running tests

```bash
python test_module.py
python build.py
```

Both must exit with code **0**.
