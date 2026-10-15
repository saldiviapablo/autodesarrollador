# csv-ledger

Normalize CSV ledger rows and aggregate exact decimal amounts using Python's
``decimal.Decimal`` for exact arithmetic.

## API

### `parse_ledger(text: str) -> list[dict]`

Accepts a CSV string with the **exact** header `date,category,amount`.

**Return** — a list of dicts in row order, each with keys:

| Key        | Type     | Description                                              |
|------------|----------|----------------------------------------------------------|
| `date`     | `str`    | ISO calendar-valid `YYYY-MM-DD` (canonical zero-padded). |
| `category` | `str`    | Non-empty, stripped of leading/trailing whitespace.      |
| `amount`   | `str`    | Quantised to **2 decimal digits** (`ROUND_HALF_UP`).     |

**Raises** `ValueError` on:

- Blank / empty input
- Non-matching header (wrong columns, wrong order, extra spaces)
- Row width ≠ 3 columns
- Invalid or non-canonical dates (e.g. `2023-02-29`, `2024-1-01`, `2024/01/01`)
- Empty or whitespace-only category
- Malformed, nonfinite, or non-numeric amounts (`NaN`, `Infinity`, `"bad"`)

**Note:** Blank input is **invalid** and raises `ValueError`.
Header-only input (no data rows) returns `[]`.

### `totals(rows: list[dict] | str) -> dict`

Aggregates amounts by category.  Accepts either the output of
``parse_ledger`` or a raw CSV string (parsed internally).

**Return** — a `dict` keyed by **lexicographic** category name; values are
two-decimal strings produced by exact ``Decimal`` addition +
``ROUND_HALF_UP`` quantisation.

**Example:**

```python
>>> rows = parse_ledger(
...     'date,category,amount\n'
...     '2024-01-01,Z,0.10\n'
...     '2024-01-01,A,0.20\n'
...     '2024-01-02,Z,0.20\n'
... )
>>> totals(rows)
{'A': '0.20', 'Z': '0.30'}
```

## CLI

```bash
echo "date,category,amount
2024-01-01,Food,10.555" | python module.py
```

**Output** (stdout, JSON, `ensure_ascii=False`):

```json
{"rows": [{"date":"2024-01-01","category":"Food","amount":"10.56"}], "totals": {"Food": "10.56"}}
```

- **Success** → exit code `0`.
- **Invalid input** → exit code `2` with a concise error message on stderr
  (no Python traceback).

## Rounding

All monetary amounts use ``decimal.Decimal(str(x)).quantize(Decimal("0.01"),
rounding=ROUND_HALF_UP)`` — the standard "round half up" behaviour familiar
from accounting.  This avoids float imprecision entirely.

## Unicode

Categories, dates, and amounts are processed as Unicode strings.  The CSV
reader respects RFC 4180 quoting (e.g. `"Comida, casa"` preserves the comma
inside quotes).  JSON output uses `ensure_ascii=False` so non-ASCII
characters are written directly.
