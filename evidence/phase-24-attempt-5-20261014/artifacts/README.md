# Invoice sandbox

## Precise monetary rounding

All monetary values are handled with Python's ``decimal.Decimal`` using the
``ROUND_HALF_UP`` rounding mode and exactly two decimal places — this is the
behaviour required for accounting and financial applications where schoolbook
arithmetic must be preserved (see
https://docs.python.org/3/library/decimal.html).

| Function | Contract |
|---|---|
| ``cents(value)`` | Rounds *value* to two decimal digits using ``ROUND_HALF_UP``.  Accepts str, int, or float.  Rejects ``NaN``, ``Infinity``, and any non-parseable input by raising ``ValueError``. |
| ``total(lines)`` | Computes ``sum(price × quantity)`` across *lines* and rounds **once** at the end to ``0.01`` with ``ROUND_HALF_UP``.  Individual prices are **not** rounded first. |
| ``allocate(value, weights)`` | Distributes a non-negative *amount* across buckets using the **largest remainder method** in integer cents.  *weights* must be numeric; individual zero weights are allowed, but the total weight must be ``>= 0`` and strictly positive to succeed.  Returns a list of two-decimal strings that sum **exactly** to the rounded amount.  Ties are broken in favour of the earlier input index. |

### Examples

```python
>>> cents("2.675")
'2.68'
>>> total([("2.675", 2), ("1.00", 3)])
'8.35'
>>> allocate("0.05", [1, 1, 1])
['0.02', '0.02', '0.01']
>>> allocate("1.00", [1, 2, 3])
['0.17', '0.33', '0.50']
```

### References

- Decimal arithmetic (official docs): https://docs.python.org/3/library/decimal.html
- Largest remainder method — fair allocation algorithm that distributes integer units and awards the remaining units one-by-one to the shares with the largest fractional remainders, with ties broken by earlier input index.
