# csv-ledger

Normalize CSV ledger rows and aggregate exact decimal amounts.

## Installation

```
pip install -r requirements.txt
```

## Usage

### API — `parse_ledger(text)`

```python
from module import parse_ledger, totals

rows = parse_ledger("date,category,amount\n2024-01-01,Café,1.005\n")
# → [{"date": "2024-01-01", "category": "Café", "amount": "1.01"}]
```

Reads a CSV string whose first row is the header `date,category,amount`.  
Returns a list of dicts preserving row order and Unicode content.

**Validation rules** (all raise ``ValueError`` on violation):

| Field    | Rules                                                                 |
|----------|-----------------------------------------------------------------------|
| **date** | Canonical ``YYYY-MM-DD``; real ISO proleptic Gregorian calendar date. |
| **category** | Nonempty after stripping whitespace.                              |
| **amount** | Parseable finite number; quantized to 2 decimal places.             |

**Decimal rounding:** each amount is converted via ``Decimal(str(x))`` and quantized with ``ROUND_HALF_UP`` to two decimal digits. This is the standard "round half up" taught in schools (0.125 → 0.13, 2.675 → 2.68).

**Edge cases:**

- Blank input → ``ValueError``.
- Header-only (no data rows) → ``[]``.
- Invalid dates (e.g. ``2023-02-29``, ``2024-1-01``) → ``ValueError``.
- Nonfinite amounts (``NaN``, ``Infinity``) → ``ValueError``.
- Row width mismatch → ``ValueError``.

### API — `totals(rows)`

```python
from module import parse_ledger, totals

rows = parse_ledger("date,category,amount\n2024-01-01,Z,0.10\n2024-01-01,A,0.20\n")
agg = totals(rows)
# → {"A": "0.20", "Z": "0.10"}
```

Aggregates the output of ``parse_ledger`` by category using ``Decimal`` arithmetic.  
Returns a ``dict`` keyed in lexicographic category order with values as two-decimal strings.

### CLI

```bash
# Valid input
echo -e "date,category,amount\n2024-01-01,Test,10.50" | python module.py
# → {"rows": [...], "totals": {"Test": "10.50"}}

# Invalid input → exit code 2, concise error on stderr (no traceback)
echo "bad data" | python module.py
# → error message on stderr, exit code 2
```

The CLI reads CSV from **stdin**, prints JSON (``ensure_ascii=False``) to **stdout**.

## Requirements

- Python 3.8+ (standard library only — ``csv``, ``decimal``, ``json``, ``datetime``).
