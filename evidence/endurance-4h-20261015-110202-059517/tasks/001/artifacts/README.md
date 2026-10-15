# csv-ledger

Normalize CSV ledger rows and aggregate exact decimal amounts using Python's
`decimal` module for precise, reproducible arithmetic.

## Quick start

```bash
# Run unit acceptance tests
python test_module.py

# Syntax / AST build check
python build.py

# CLI: pipe CSV via stdin
echo 'date,category,amount
2024-01-01,Salary,3000.00
2024-01-02,Food,15.75' | python module.py
```

## API

### `parse_ledger(text: str) -> list[dict]`

Accepts a CSV string with the exact header `date,category,amount`.

Returns a list of dicts with keys `date`, `category`, `amount`.

**Validation rules:**

| Rule | Behaviour |
|---|---|
| Blank / whitespace-only input | Raises `ValueError` |
| Wrong header | Raises `ValueError` |
| Row field count ≠ 3 | Raises `ValueError` |
| `date` not canonical `YYYY-MM-DD` | Raises `ValueError` (rejects `2024-1-01`, non-existent dates like `2023-02-29`) |
| `category` empty after strip | Raises `ValueError` |
| `amount` empty / NaN / Infinity / non-numeric | Raises `ValueError` |

Date validation uses the `datetime.date` constructor, guaranteeing ISO
calendar correctness.  The canonical check ensures zero-padded month and
day fields.

Amounts are parsed via `Decimal(str(x))` and quantized to **two decimal
places** using `ROUND_HALF_UP` (standard commercial rounding).

Unicode is preserved verbatim in both `category` and `amount` strings.

### `totals(rows: list[dict]) -> dict[str, str]`

Aggregates `amount` values from `parse_ledger` output by category.

- Keys: category names in **lexicographic order**.
- Values: two-decimal-place strings (e.g. `'0.30'`).
- Negative amounts are supported.

```python
from module import parse_ledger, totals

rows = parse_ledger("""\
date,category,amount
2024-01-01,Z,0.10
2024-01-01,A,0.20
2024-01-02,Z,0.20
""")
print(totals(rows))
# {'A': '0.20', 'Z': '0.30'}
```

## CLI

```bash
python module.py < input.csv
```

- **Success** (exit 0): prints JSON to stdout with keys `rows` and `totals`.
  Uses `ensure_ascii=False` so Unicode characters appear unescaped.
- **Invalid input** (exit 2): prints a concise error message to stderr
  without a traceback.

## Rounding reference

All monetary arithmetic uses `decimal.Decimal`:

```python
from decimal import Decimal, ROUND_HALF_UP
Decimal('7.125').quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)  # '7.13'
Decimal('-2.675').quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) # '-2.68'
```

This is the standard "round half up" (commercial) rounding preferred
in accounting applications where exact equality invariants are required.
Unlike binary `float`, `Decimal` represents monetary values exactly and
avoids accumulated floating-point errors.

## Dependencies

- Python 3.6+ (standard library only — `csv`, `decimal`, `json`, `sys`,
  `io`, `datetime`, `pathlib`).

## Project files

| File | Purpose |
|---|---|
| `module.py` | Core API (`parse_ledger`, `totals`) + CLI entry point |
| `test_module.py` | Acceptance test suite (must pass with exit code 0) |
| `build.py` | AST parse check (ensures module.py is syntactically valid) |
| `README.md` | This file — API, CLI, validation, and rounding docs |
