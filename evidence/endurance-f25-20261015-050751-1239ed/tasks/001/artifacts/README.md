# csv-ledger

Normalize CSV ledger rows and aggregate exact-decimal amounts.

## API

Import ``parse_ledger`` and ``totals`` from **module.py**.

### `parse_ledger(text) -> list[dict]`

Parse a CSV string with the exact header `date,category,amount`.

**Validation rules**

| Field    | Rule                                                                 |
|----------|----------------------------------------------------------------------|
| Header   | Must be exactly `date,category,amount`                               |
| Date     | ISO 8601 `YYYY-MM-DD`, zero-padded month/day, real calendar date     |
| Category | Stripped, must be non-empty                                          |
| Amount   | Parseable as `Decimal`, quantized to 2 decimals via `ROUND_HALF_UP`  |

Invalid input raises **`ValueError`** (blank input, bad header, wrong row width, unparseable or non-finite amounts). Header-only input returns `[]`.

**Rounding** — amounts are converted through `Decimal(str(x))` then quantized to two decimal places with `ROUND_HALF_UP`:

```python
>>> from module import parse_ledger
>>> parse_ledger("date,category,amount\n2024-01-01,A,7.125\n")[0]["amount"]
'7.13'
>>> parse_ledger("date,category,amount\n2024-01-01,B,1.005\n")[0]["amount"]
'1.01'
```

Negative amounts are allowed. Unicode in categories is preserved.

### `totals(rows) -> dict`

Aggregate rows returned by `parse_ledger` by category. Returns a dict in lexicographic category order with values as two-decimal strings.

```python
>>> from module import parse_ledger, totals
>>> totals(parse_ledger("date,category,amount\n2024-01-01,Z,0.10\n2024-01-01,A,0.20\n"))
{'A': '0.20', 'Z': '0.30'}
```

## CLI

```bash
echo "date,category,amount
2024-01-01,Salario,1500.00" | python module.py
```

Outputs JSON:

```json
{"rows": [...], "totals": {"Salario": "1500.00"}}
```

- **Exit 0** on success.
- **Exit 2** with a concise error on **stderr** (no traceback) for invalid input.

## Installation

No external dependencies required. Python 3.6+ with the standard library is sufficient.

```bash
python module.py < input.csv
```

## Testing

```bash
python test_module.py
python build.py
```

Both must exit with code 0.
