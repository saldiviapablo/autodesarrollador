# Invoice sandbox

## Precise monetary rounding — `cents(value)`

`cents(value)` converts any numeric value to a **two-decimal string** using Python's
`decimal.Decimal` with the **`ROUND_HALF_UP`** rounding mode.

```python
>>> cents("2.675")
'2.68'
>>> cents("0")
'0.00'
```

Invalid, non-finite or non-numeric inputs (NaN, Infinity, arbitrary strings) raise
`ValueError`.

> **Reference:** https://docs.python.org/3/library/decimal.html

## Invoice totals — `total(lines)`

`total(lines)` computes the sum of `price × quantity` pairs without rounding
individual line items, then rounds the final sum to two decimals with
`ROUND_HALF_UP`.

```python
>>> total([("2.675", 2), ("1.00", 3)])
'8.35'
>>> total([])
'0.00'
```

## Cent-conserving allocation — `allocate(value, weights)`

`allocate(value, weights)` distributes a non-negative *amount* across
positive or zero *weights* using the **largest remainder method**
(Hare / Sainte-Laguë) in integer cents.

* **`value`** — a non-negative amount (e.g. `"1.00"`). Must be >= 0.
* **`weights`** — a non-empty list of non-negative numbers. Individual zero
  weights are allowed (they receive `"0.00"`). Total weight must be positive.

The function returns a list of two-decimal strings whose sum is **exactly**
the rounded input value (cent conservation). Ties in the remainder bucket
are broken by **earlier input index**.

```python
>>> allocate("0.05", [1, 1, 1])
['0.02', '0.02', '0.01']
>>> allocate("1.00", [1, 2, 3])
['0.17', '0.33', '0.50']
>>> allocate("1.00", [0, 1])
['0.00', '1.00']
```

Invalid inputs (negative amount, negative weight, zero total weight,
non-numeric values) raise `ValueError`.

> **Reference:** Largest remainder method — fair apportionment algorithm that
> guarantees integer totals sum exactly to the rounded value.
