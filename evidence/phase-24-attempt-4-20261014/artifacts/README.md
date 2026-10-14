# Invoice sandbox

## Overview

Precise invoice arithmetic and cent-conserving allocation built on Python's
`decimal` module.  All monetary values are represented as two-decimal-digit
strings produced with **ROUND_HALF_UP** rounding.

Reference: https://docs.python.org/3/library/decimal.html

## Functions

### `cents(value) -> str`

Rounds *value* to two decimal places using **ROUND_HALF_UP**.

* Accepts `str`, `int`, `float`, or `Decimal`.
* Rejects malformed input and non-finite values (`NaN`, `Infinity`) with
  `ValueError`.
* Returns a two-decimal-digit string (e.g. `"2.68"`).

**Example**

```python
>>> cents("2.675")
'2.68'
>>> cents("-2.675")
'-2.68'
>>> cents("0")
'0.00'
```

### `total(lines) -> str`

Returns the cents-string of the sum of `price × quantity` for every line.

* *lines* is an iterable of `(price, quantity)` tuples.
* Individual line products are **not** rounded; the final sum is rounded
  to two decimals with **ROUND_HALF_UP**.
* Returns a two-decimal-digit string.

**Example**

```python
>>> total([("2.675", 2), ("1.00", 3)])
'8.35'
>>> total([])
'0.00'
```

### `allocate(value, weights) -> list[str]`

Distributes a non-negative monetary *value* across *weights* using the
**largest remainder method** (also known as the Hare or Saint-Laguë method).

**Parameters**

| Param   | Constraint                                              |
| ------- | ------------------------------------------------------- |
| `value` | non-negative (amount ≥ 0, no negativo, >= 0)            |
| `weights` | non-negative per-share weights (each weight ≥ 0); at least one must be positive |

* Individual zero weights are allowed — they receive `"0.00"`.
* Bad input (negative value, negative weight, zero total weight, non-numeric
  weights) raises `ValueError`.

**Returns**

A list of two-decimal-digit strings whose `Decimal` sum equals the rounded
input value exactly — the **cent-conservation invariant** holds.

**Algorithm**

1. Round *value* to cents via `cents()` → integer-cents target.
2. Floor-allocate proportional cents: `floor(target_cents × weight_i / total_weights)`.
3. Distribute the remaining cents one-by-one to the shares with the largest
   fractional remainders; ties go to the earlier input index.

**Example**

```python
>>> allocate("0.05", [1, 1, 1])
['0.02', '0.02', '0.01']
>>> allocate("1.00", [1, 2, 3])
['0.17', '0.33', '0.50']
>>> allocate("1.00", [0, 1])
['0.00', '1.00']
```

## Rationale

Binary floating-point (`float`) cannot represent values like `1.1` or `2.675`
exactly, which leads to surprising results (`1.1 + 2.2 == 3.3000000000000003`).
The `decimal` module provides exact decimal arithmetic preferred in accounting
applications with strict equality invariants.
