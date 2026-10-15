# csv-ledger

CSV ledger normalizer and exact-decimal aggregator.

## API

### `parse_ledger(text: str) -> list[dict]`

Accepts a CSV string with the exact header `date,category,amount`.  Returns a list of dicts with keys `date`, `category`, `amount`:

* **date** — ISO calendar-valid `YYYY-MM-DD` (rejects noncanonical formats such as `2024-1-01` or impossible dates like `2023-02-29`).
* **category** — stripped, nonempty string.
* **amount** — string quantized to two decimal places using `Decimal(str(x))` with `ROUND_HALF_UP` rounding.

Negative amounts are allowed. Row order and Unicode characters are preserved.

#### Validation & Errors

* Blank input (empty / whitespace-only) → `ValueError`.
* Malformed or unexpected header → `ValueError`.
* Wrong row width (not exactly 3 fields) → `ValueError`.
* Invalid / non-canonical dates → `ValueError`.
* Non-finite (`NaN`, `Infinity`) or non-numeric amounts → `ValueError`.

### `totals(rows: list[dict]) -> dict[str, str]`

Aggregates `amount` values by `category` using exact `Decimal` arithmetic.  Returns a dict with:

* **Keys** — category names in **lexicographic** order.
* **Values** — two-decimal-place strings.

Negative amounts are supported.

## CLI

```bash
echo "date,category,amount
2024-01-01,Food,10.505" | python module.py
```

Outputs JSON to stdout:

```json
{"rows": [{"date": "2024-01-01", "category": "Food", "amount": "10.51"}], "totals": {"Food": "10.51"}}
```

Invalid input exits with code **2** and prints a concise error to stderr (no traceback).

## Rounding

All amounts use Python's `decimal.Decimal` with `ROUND_HALF_UP` to exactly two decimal places, matching common financial rounding conventions.  See the [Python docs](https://docs.python.org/3/library/decimal.html) for details.

## Unicode

All input/output is UTF-8.  Unicode characters in category names (e.g. `Café`, `Ñ`) are preserved as-is.  The CLI uses `ensure_ascii=False` in JSON output.

## References

* [RFC 4180 — Common Format and MIME Type for CSV Files](https://www.ietf.org/rfc/rfc4180.txt)
* [Python `decimal` module](https://docs.python.org/3/library/decimal.html)
* [ISO 8601 — Date and Time Representations](https://www.iso.org/iso-8601-date-and-time-format.html)
