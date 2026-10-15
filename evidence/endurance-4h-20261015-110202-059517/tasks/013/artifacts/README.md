# csv-ledger

Normalize CSV ledger rows and aggregate exact decimal amounts.

## API

### `parse_ledger(text) → list[dict]`

Parse a CSV string with the exact header `date,category,amount`.

- **date** — validated via `datetime.date.fromisoformat`; must be canonical
  `YYYY-MM-DD` (rejects `2024-1-01`, `2024/01/01`, etc.).
- **category** — non-empty after stripping whitespace; Unicode-aware.
- **amount** — parsed via `Decimal(str(x))` and quantised to two decimal
  places using `ROUND_HALF_UP` (Python standard library,
  [Decimal rounding docs](https://docs.python.org/3/library/decimal.html#rounding)).

Returns a list of dicts in input order:
```python
[{"date": "2024-01-01", "category": "Café", "amount": "1.01"}, ...]
```

Raises **`ValueError`** on:
- blank input
- malformed / missing header
- wrong row width (not exactly 3 fields)
- non-canonical or invalid ISO dates (e.g. `2023-02-29`)
- empty category
- malformed, `NaN`, `Infinity`, or otherwise non-finite amounts

Header-only input returns `[]`.

### `totals(rows) → dict`

Aggregate rows (output of `parse_ledger`) by category using exact `Decimal`
addition.  Returns a dictionary in **lexicographic** category order with
two-decimal-place string values.  Negative amounts are supported.

## CLI

```bash
echo 'date,category,amount
2024-01-01,Ñ,1.005' | python module.py
# → {"rows":[{"date":"2024-01-01","category":"Ñ","amount":"1.01"}],"totals":{"Ñ":"1.01"}}
```

- Reads CSV from **stdin**.
- Prints JSON with `ensure_ascii=False`.
- On invalid input prints a concise error to **stderr** (no traceback) and
  **exits with code 2**.

## Exact Decimal rounding

All amounts are converted to `Decimal(str(x))` to avoid binary floating-point
artifacts.  The final quantisation uses `ROUND_HALF_UP` to the nearest cent
(`0.01`).  Example: `1.005 → 1.01`, `2.675 → 2.68`.

## Unicode

Categories and dates preserve original Unicode characters (e.g. `Café`, `Ñ`,
`Ω`).  The CSV reader handles full Unicode strings natively.
