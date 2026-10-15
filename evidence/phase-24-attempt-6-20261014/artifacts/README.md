# Invoice sandbox

Precise invoice arithmetic using Python's ``decimal`` module with
``ROUND_HALF_UP`` rounding to two decimal places.

## Functions

### ``cents(value)``

Converts *value* to a two-decimal string using
``ROUND_HALF_UP``.  Rejects ``NaN``, ``Infinity``, and any
non-numeric input with ``ValueError``.

```python
>>> from invoice import cents
>>> cents("2.675")
'2.68'
>>> cents("-2.675")
'-2.68'
>>> cents("NaN")
ValueError: bad monetary value: 'NaN'
```

### ``total(lines)``

Sums ``price × quantity`` pairs and returns the grand total as a
cent-level string.  No intermediate rounding is applied; the sum is
rounded exactly once.

```python
>>> from invoice import total
>>> total([("2.675", 2), ("1.00", 3)])
'8.35'
>>> total([])
'0.00'
```

### ``allocate(value, weights)``

Splits a non-negative *amount* across a sequence of non-negative
*weights* using the **largest remainder method** (Hare–Niemeyer /
Jefferson) in integer cents.  Ties (identical fractional parts) are
broken by earlier input index.

- **amount** must be non-negative (>= 0).
- **weights** must contain at least one entry; zero-weight shares are
  allowed and receive ``"0.00"``.
- The returned list of two-decimal strings sums exactly to the
  rounded amount.

```python
>>> from invoice import allocate
>>> allocate("0.05", [1, 1, 1])
['0.02', '0.02', '0.01']
>>> allocate("1.00", [1, 2, 3])
['0.17', '0.33', '0.50']
>>> allocate("1.00", [0, 1])
['0.00', '1.00']
```

Raises ``ValueError`` for negative amounts, negative weights, empty
weight lists, or when all weights are zero.

## Why ``Decimal`` with ``ROUND_HALF_UP``

Binary ``float`` cannot represent values like 1.1 or 2.675 exactly;
rounding 2.675 with ``round()`` gives ``2.67`` (banker's rounding).
The ``decimal`` module provides exact decimal representation and a
configurable ``ROUND_HALF_UP`` rounding mode — the standard for
accounting and monetary calculations — where 2.675 rounds to 2.68.

Reference: https://docs.python.org/3/library/decimal.html
