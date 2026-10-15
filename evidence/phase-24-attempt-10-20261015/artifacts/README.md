# Invoice sandbox

## Precise monetary rounding — `cents(value)`

Uses Python's ``decimal.Decimal`` with ``ROUND_HALF_UP`` to round any
monetary amount to exactly two decimal digits.

```python
>>> from invoice import cents
>>> cents("2.675")
'2.68'          # half-up, not banker's rounding
>>> cents("0")
'0.00'
```

Rejects ``NaN``, ``Infinity``, negative infinity, ``None``, and any
non-finite or malformed input with ``ValueError``.

Official reference: <https://docs.python.org/3/library/decimal.html>

## Invoice totals — `total(lines)`

``total(lines)`` computes the sum of ``price × quantity`` for each line,
**without** rounding individual line items first.  Only the final sum is
rounded to two decimal places using ``ROUND_HALF_UP``.

```python
>>> from invoice import total
>>> total([("2.675", 2), ("1.00", 3)])
'8.35'
```

## Fair allocation — `allocate(value, weights)`

Distributes a non-negative *amount* across integer *weights* using the
**largest remainder method** (also known as Hamilton's method or
Saint-Laguë):

1. Convert the amount to integer cents.
2. Compute ``base = cents // total_weight`` — every recipient gets ``base``
   cents.
3. Distribute the ``remainder`` one cent at a time to the recipients with
   the largest fractional shares
   ``weight_i × remainder / total_weight``.  Ties are broken by **earlier
   input index**.
4. Return each share as a two-decimal string.  The shares **sum exactly** to
   the rounded input amount (cent conservation).

### Parameters

| Param    | Constraint                                       |
|----------|---------------------------------------------------|
| `amount` | non-negative, finite (``>= 0``)                  |
| `weights`| non-negative integers whose sum is **strictly** positive; individual zero weights are allowed |

### Examples

```python
>>> from invoice import allocate
>>> allocate("0.05", [1, 1, 1])
['0.02', '0.02', '0.01']       # ties broken by index
>>> allocate("1.00", [1, 2, 3])
['0.17', '0.33', '0.50']       # sums to exactly 1.00
>>> allocate("1.00", [0, 1])
['0.00', '1.00']               # zero weight → zero share
>>> allocate("0.00", [1, 2])
['0.00', '0.00']
```

### Rejection

``allocate`` raises ``ValueError`` when:

* `amount` is negative, ``NaN``, or ``Infinity``.
* any weight is negative or non-convertible to ``int``.
* the total weight is zero (e.g. ``[0, 0]`` or ``[]``).

## References

* Decimal arithmetic: <https://docs.python.org/3/library/decimal.html>
* Largest remainder method: Wikipedia — "Highest averages method / Hamilton method"
