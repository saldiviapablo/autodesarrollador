# Synthetic Execution Report CLI

A noncritical synthetic run-report utility built with **Python stdlib only** (standard library). No external dependencies, no network access, no secrets required.

## API

### `round_seconds(value) -> str`

Rounds *value* to two decimal places using `decimal.Decimal` with `ROUND_HALF_UP`.

- Accepts `str`, `int`, or `float` (bool is explicitly rejected).
- Returns a formatted string such as `'1.01'` or `'0.00'`.
- Negative zero normalises to positive zero (`'-0.0'` → `'0.00'`).
- Rejects negative, out-of-range (`[0, 1e12]`), non-finite, and non-numeric inputs with `ValueError`.

**Example — rounding bug fix:**

```python
>>> from module import round_seconds
>>> round_seconds('1.005')   # string → Decimal preserves exactness
'1.01'
>>> round_seconds(1.005)     # float loses precision before Decimal sees it → floor
'1.00'
```

The canonical approach is to pass the **string** directly to `Decimal(str(value))` so `1.005` is rounded up to `1.01` as expected.

Official reference: https://docs.python.org/3/library/decimal.html

### `normalize(records) -> list[dict]`

Validates, normalises, and returns **new** record dicts sorted by `id`.

Each record must be a dict with **exactly** three keys:

| Key      | Constraint                                                          |
|----------|---------------------------------------------------------------------|
| `id`     | Non-empty stripped string, no CR/LF/NUL; IDs must be unique after stripping. Unicode preserved. |
| `status` | One of `PASS`, `FAIL`, `BLOCKED`, `TIMEOUT` (case-sensitive).      |
| `seconds`| String, int, or float (bool forbidden); finite Decimal in `[0, 1e12]`. Quantised to `.01` with `ROUND_HALF_UP`. |

- Input list and its elements are **never mutated**.
- Returns a list of **new** dicts sorted by `id`.
- Raises `ValueError` on any invalid input (never incidental exceptions).

**Example:**

```python
>>> from module import normalize
>>> recs = [{'id': ' ñ ', 'status': 'PASS', 'seconds': '2'},
...         {'id': 'a', 'status': 'FAIL', 'seconds': '.125'}]
>>> normalize(recs)
[{'id': 'a', 'status': 'FAIL', 'seconds': '0.13'},
 {'id': 'ñ', 'status': 'PASS', 'seconds': '2.00'}]
```

### `summarize(records) -> dict`

Produces a full report summary from raw *records*.

Returns a dict with keys:

```
{
    "records":        [...],   # normalised records sorted by id
    "counts":         {       # one entry per status, always present
        "PASS": int,
        "FAIL": int,
        "BLOCKED": int,
        "TIMEOUT": int
    },
    "total_seconds":  str,    # exact Decimal sum, formatted to .01
    "max_seconds":    str     # exact Decimal max, formatted to .01
}
```

- Uses **exact `Decimal` arithmetic** for totals and max — no float drift.
- Empty input → all counts `0`, `total_seconds`/`max_seconds` → `'0.00'`.
- Raises `ValueError` on invalid input.

**Example:**

```python
>>> from module import summarize
>>> recs = [
...     {'id': 'a', 'status': 'PASS', 'seconds': '0.105'},
...     {'id': 'b', 'status': 'FAIL', 'seconds': '2.675'},
...     {'id': 'c', 'status': 'BLOCKED', 'seconds': 0},
...     {'id': 'd', 'status': 'TIMEOUT', 'seconds': '1.005'}
... ]
>>> s = summarize(recs)
>>> s['counts']
{'PASS': 1, 'FAIL': 1, 'BLOCKED': 1, 'TIMEOUT': 1}
>>> s['total_seconds']   # 0.105 + 2.675 + 0 + 1.005 = 3.785 → 3.79
'3.80'
>>> s['max_seconds']     # 2.675 → 2.68
'2.68'
```

### `markdown(summary) -> str`

Renders a summary dict as a Markdown report.

Layout:

1. `# Execution report`
2. `Total seconds: <total_seconds>`
3. `Max seconds: <max_seconds>`
4. Two-column status table: `| Status | Count |` — rows in PASS, FAIL, BLOCKED, TIMEOUT order.
5. Three-column records table: `| ID | Status | Seconds |` — sorted by id.
6. Pipes (`|`) in IDs are escaped as `\|` to keep table cells well-formed.

**Example:**

```python
>>> from module import markdown, summarize
>>> print(markdown(summarize([
...     {'id': 'a', 'status': 'PASS', 'seconds': '1.005'},
...     {'id': 'z', 'status': 'FAIL', 'seconds': '2.675'}
... ])))
# Execution report
Total seconds: 3.69
Max seconds: 2.68

| Status | Count |
|--------|-------|
| PASS   | 1     |
| FAIL   | 1     |
| BLOCKED| 0     |
| TIMEOUT| 0     |

| ID | Status | Seconds |
|----|--------|---------|
| a  | PASS   | 1.01    |
| z  | FAIL   | 2.68    |
```

## CLI

```bash
# Default: JSON summary on stdout
echo '[{"id":"a","status":"PASS","seconds":"1.005"}]' | python module.py

# Markdown report
echo '[{"id":"a","status":"PASS","seconds":"1.005"}]' | python module.py --markdown
```

- Reads a JSON list from **stdin**.
- Default output: JSON summary (`ensure_ascii=False` so Unicode passes through).
- `--markdown` flag: outputs a formatted Markdown report.
- Invalid input or unknown options → exit code **2**, concise message on **stderr** (no traceback), **stdout** is empty.
- No network, filesystem reads, or external dependencies required.

## Validation rules

| Field   | Rules                                                                 |
|---------|-----------------------------------------------------------------------|
| `id`    | `str`, non-empty after strip, no `\r\n\x00`, unique after stripping.  |
| `status`| One of: `PASS`, `FAIL`, `BLOCKED`, `TIMEOUT` (exact match).          |
| `seconds`| `str`/`int`/`float` (bool forbidden), finite, in `[0, 1e12]`. Quantised with `ROUND_HALF_UP` to `.01`. Negative zero → `0.00`. |

Invalid inputs raise `ValueError` — never incidental `TypeError`, `OverflowError`, or `DecimalException`.

## Unicode / UTF-8

All I/O uses UTF-8 encoding. IDs preserve Unicode characters (e.g. `ñ`, `é`, `中文`). CLI JSON output uses `ensure_ascii=False` to keep Unicode readable.

## Decimal rounding

The `decimal` module (stdlib) provides exact fixed-point arithmetic. Key reference: https://docs.python.org/3/library/decimal.html

```python
>>> from decimal import Decimal, ROUND_HALF_UP
>>> Decimal('1.005').quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
Decimal('1.01')
```

Always pass **strings** to `Decimal()` to avoid float precision loss:

```python
>>> Decimal(str(1.005))   # float loses precision first → '1.00499...'
Decimal('1.00499999999999989341858963598497211933135986328125')
>>> Decimal('1.005')      # string preserves exact value
Decimal('1.005')
```

## Installation / Requirements

**None.** This project uses **stdlib or standard library only**. No `requirements.txt`, no `pip install`, no downloads.

```bash
python module.py          # CLI
python test_module.py     # Run tests
python build.py           # Generate reports from sample-records.json
```

## Examples

See `sample-records.json` for sample input data. The `build.py` script reads it and generates:

- `artifact-report.json` — JSON summary
- `REPORT.md` — Markdown report

Both are produced via:

```bash
python build.py
```

Output files are written with UTF-8 encoding, no BOM.

## Testing

```bash
python test_module.py
```

17 acceptance tests covering:

- `ROUND_HALF_UP` rounding (the `1.005` → `1.01` bug fix)
- Negative zero normalisation
- Unicode ID handling and sorting
- Input validation (bad types, out-of-range, duplicates, forbidden chars)
- Exact Decimal totals and max computation
- Markdown layout, pipe escaping, empty reports
- CLI: JSON output, Markdown output, fail-closed on bad input (exit 2)
- Documentation completeness

All tests must pass (exit code 0) before considering a change complete.
