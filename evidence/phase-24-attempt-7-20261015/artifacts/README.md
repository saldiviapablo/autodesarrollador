# Invoice sandbox

## Precise invoice arithmetic

All monetary values are handled through Python's **decimal** module
([official reference](https://docs.python.org/3/library/decimal.html)),
which guarantees exact decimal representation and schoolbook rounding —
exactly the invariants required for accounting applications.

### `cents(value) → str`

Rounds *value* (str, int, float, or Decimal) to two decimal places using
**ROUND_HALF_UP** and returns a two-digit string (e.g. `"3.10"`).

* Rejects malformed or non-finite inputs (`NaN`, `Infinity`, garbage strings)
  by raising `ValueError`.

### `total(lines) → str`

Computes the invoice total of *lines* — an iterable of `(price, quantity)`
pairs.  Each `price × quantity` product is accumulated in full Decimal
precision; the sum is rounded **once** at the end with ROUND_HALF_UP to
0.01.  Individual prices are **not** rounded before accumulation.

### `allocate(value, weights) → list[str]`

Distributes a non-negative *amount* across shares proportional to
*weights* using the **largest remainder method** (integer-cents / Hare
method):

1. Convert *value* to an integer number of cents (ROUND_HALF_UP).
2. `floor_cents[i] = total_cents * weights[i] // total_weight`.
3. Distribute the leftover cents one-by-one to the shares with the
   largest remainders; ties go to the **earlier input index**.
4. Returns a list of two-decimal strings whose sum equals exactly the
   rounded input *value*.

**Validation:**

| Constraint | Behaviour |
|---|---|
| *amount* < 0 | raises `ValueError` |
| any weight < 0 | raises `ValueError` |
| total weight == 0 | raises `ValueError` |
| individual weight == 0 | allowed (share receives 0) |

**Examples:**

```python
>>> allocate("0.05", [1, 1, 1])
["0.02", "0.02", "0.01"]

>>> allocate("1.00", [1, 2, 3])
["0.17", "0.33", "0.50"]

>>> allocate("1.00", [0, 1])
["0.00", "1.00"]
```
