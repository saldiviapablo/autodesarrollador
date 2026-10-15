# Invoice sandbox

## Overview

Precise invoice arithmetic with cent-conserving allocation.  All monetary
values are handled through Python's ``decimal.Decimal`` to avoid the
inexactness of binary floating-point (IEEE 754).

## Functions

### `cents(value) -> str`

Convert *value* to a two-decimal string using **ROUND_HALF_UP** rounding.

```python
>>> cents("2.675")
'2.68'
>>> cents("0")
'0.00'
>>> cents("-2.675")
'-2.68'
```

Malformed or non-finite values (``NaN``, ``Infinity``, ``None``, …) raise
``ValueError``.

### `total(lines) -> str`

Sum ``price × quantity`` pairs, then round **once** at the end.

```python
>>> total([("2.675", 2), ("1.00", 3)])
'8.35'
>>> total([])
'0.00'
```

Individual prices are rounded by ``cents()`` before multiplication; the
aggregate is rounded again at the top level.

### `allocate(value, weights) -> list[str]`

Distribute a non-negative *amount* across positive numeric *weights* using
the **largest remainder method** (also known as the Hare–Niemeyer or
largest-average method).

* The amount must be **non-negative** (``>= 0``).
* Each weight must be numeric and **non-negative**; at least one weight must
  be **positive**.  Individual zero weights are allowed and receive
  ``"0.00"``.
* Negative values, empty weight lists, or all-zero lists raise ``ValueError``.
* Ties are broken by earlier input index.
* The returned two-decimal strings **sum exactly** to ``cents(value)``.

```python
>>> allocate("0.05", [1, 1, 1])
['0.02', '0.02', '0.01']
>>> allocate("1.00", [1, 2, 3])
['0.17', '0.33', '0.50']
>>> allocate("1.00", [0, 1])
['0.00', '1.00']
```

## Rounding

| Standard | Behaviour |
|---|---|
| **ROUND_HALF_UP** | .005 → .01 (the "schoolbook" round-half-up taught in primary school) |

This is the default expectation for monetary applications.  The Python
`decimal` module implements this precisely:

> <https://docs.python.org/3/library/decimal.html>

## Largest remainder method

The largest remainder algorithm:

1. Compute each slot's exact share as `floor(total × weight / total_weight)`.
2. Distribute the remaining integer units one-by-one to slots with the
   largest fractional remainders, breaking ties by earlier input index.

This guarantees that the integer-cent values sum to the total and that each
slot is off by at most one cent from its exact proportional share.

## References

* Python decimal module —
  <https://docs.python.org/3/library/decimal.html>
* Largest remainder method — Wikipedia:
  <https://en.wikipedia.org/wiki/Largest_remainder_method>
