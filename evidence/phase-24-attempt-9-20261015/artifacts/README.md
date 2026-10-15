# Invoice sandbox

Precise invoice arithmetic and cent-conserving allocation using Python's
``decimal`` module.

## Rounding

All monetary calculations use **ROUND_HALF_UP** (not the default
ROUND_HALF_EVEN / banker's rounding).  Every monetary value is rounded to two
decimal places via::

    Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

This ensures that values like `2.675` round to `2.68` (not `2.67`).

See the official documentation:
https://docs.python.org/3/library/decimal.html

## Functions

### `cents(value)`

Converts *value* to a ``Decimal`` (via ``str(value)``) and rounds to two
decimal places using ROUND_HALF_UP.

```python
>>> cents("2.675")
'2.68'
>>> cents("0")
'0.00'
```

Rejects non-finite values (NaN, Infinity), ``None``, and malformed strings
with ``ValueError``.

### `total(lines)`

Computes the total of an invoice.  *lines* is an iterable of
``(price, quantity)`` pairs.  Each line's ``price * quantity`` is computed
exactly with ``Decimal`` arithmetic.  The sum is rounded **once** at the end
with ROUND_HALF_UP — individual line products are **not** rounded
prematurely.

```python
>>> total([("2.675", 2), ("1.00", 3)])
'8.35'
>>> total([])
'0.00'
```

### `allocate(value, weights)`

Performs a **largest remainder** (Hare/Nq) allocation of a non-negative
monetary *value* across numeric *weights*, returning two-decimal strings that
sum **exactly** to the rounded input amount (cent conservation).

- *amount* must be >= 0 (nonnegative).
- Each *weight* must be >= 0 (nonnegative).  A zero weight is allowed and
  receives `"0.00"`.
- Negative, missing, non-numeric, or empty weights raise ``ValueError``.
- If all weights are zero (total weight == 0), raises ``ValueError``.
- Ties in the largest-remainder step are broken by earlier input index.

```python
>>> allocate("0.05", [1, 1, 1])
['0.02', '0.02', '0.01']
>>> allocate("1.00", [1, 2, 3])
['0.17', '0.33', '0.50']
>>> allocate("1.00", [0, 1])
['0.00', '1.00']
```

The method distributes the integer-cent remainder to the shares with the
largest fractional parts, guaranteeing that ``sum(Decimal(s) for s in
shares) == Decimal(value)``.

## References

- Decimal documentation: https://docs.python.org/3/library/decimal.html
- Largest remainder method (Hare/Nq): distributes residual seats/cent to
  parties with the largest fractional remainders, ties broken by index order.
