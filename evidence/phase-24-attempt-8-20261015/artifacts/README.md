# Invoice sandbox

Precise invoice arithmetic and cent-conserving allocation built on Python's
`decimal` module.

## Quick start

```python
from invoice import cents, total, allocate

# Rounding with ROUND_HALF_UP to two decimal digits
cents("2.675")        # → "2.68"
cents("-2.675")       # → "-2.68"
cents("0")            # → "0.00"

# Invoice totals — no per-line rounding
total([("2.675", 2), ("1.00", 3)])   # → "8.35"
total([])                            # → "0.00"

# Fair allocation (largest remainder method)
allocate("0.05", [1, 1, 1])    # → ["0.02", "0.02", "0.01"]
allocate("1.00", [1, 2, 3])    # → ["0.17", "0.33", "0.50"]
allocate("1.00", [0, 1])       # → ["0.00", "1.00"]  (zero weight allowed)
```

## API

### `cents(value) -> str`

Converts *value* (str, int, float, or Decimal) to a two-decimal-digit string
using **ROUND_HALF_UP**.

| Input          | Output |
|---------------|--------|
| `"2.675"`     | `"2.68"` |
| `"-2.675"`    | `"-2.68"` |
| `"0"`         | `"0.00"` |

Raises `ValueError` for non-finite values (NaN, Infinity), `None`, or
malformed inputs.

### `total(lines) -> str`

Returns the cent-accurate total of *lines* as a two-decimal string.  Each
line is ``(price, quantity)``.  Prices are multiplied by quantity **before**
a single ROUND_HALF_UP rounding at the end — individual prices are **not**
rounded first.  The result is guaranteed to be exact to the nearest cent.

### `allocate(value, weights) -> list[str]`

Distributes a non-negative *amount* (>= 0) across slots proportional to
numeric *weights* (each >= 0, total > 0) using the largest remainder method
(also known as the Hamilton/Vinton method).

- Individual zero weights are allowed — the corresponding share is
  ``"0.00"``.
- Negative, empty, all-zero, or non-numeric weights raise ``ValueError``.
- Negative *value* raises ``ValueError``.

**Algorithm**

1. Convert *value* to integer cents.
2. Each slot receives ``floor(weight_i / sum(weights) * total_cents)``.
3. Remaining cents are assigned one-by-one to slots with the largest
   fractional remainders, ties broken by earlier input index.
4. Returns two-decimal strings that **sum exactly** to the rounded input.

## References

- [Python `decimal` module](https://docs.python.org/3/library/decimal.html) —
  official documentation for exact decimal arithmetic, rounding modes, and
  context configuration.
- **largest remainder method** — a proportional allocation algorithm that
  guarantees the sum of integer parts plus distributed remainders equals the
  original total, avoiding off-by-one-cent drift common in naïve rounding.
