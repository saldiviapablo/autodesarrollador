from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from math import isfinite


def cents(value):
    """Round a monetary value to two decimal places using ROUND_HALF_UP.

    Accepts strings, ints, floats, or Decimal.  Rejects malformed input
    and non-finite values (NaN / Infinity) with ValueError.

    Returns a two-decimal-digit string (e.g. "2.68").
    """
    # Coerce to string first to preserve significance
    raw = str(value).strip()
    if not raw:
        raise ValueError(f"invalid monetary value: {value!r}")

    try:
        d = Decimal(raw)
    except InvalidOperation:
        raise ValueError(f"invalid monetary value: {value!r}")

    # Reject NaN / Infinity (Decimal accepts these; we reject them)
    if not (d.is_finite()):
        raise ValueError(f"non-finite monetary value: {value!r}")

    return str(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def total(lines):
    """Return the cents-string of the sum of (price × quantity) for every line.

    * price — anything ``cents()`` accepts (converted via Decimal(str))
    * quantity — int or float, converted to int via Decimal

    Individual line products are **not** rounded; the final sum is rounded
    to two decimals with ROUND_HALF_UP.
    """
    acc = Decimal("0")
    for price_raw, qty_raw in lines:
        price = Decimal(str(price_raw))
        qty = int(Decimal(str(qty_raw)))
        acc += price * qty
    return str(acc.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def allocate(value, weights):
    """Largest-remainder allocation of *value* across *weights*.

    Parameters
    ----------
    value : str | Decimal
        Non-negative monetary amount to distribute.
    weights : list[int | float | str]
        Non-negative weights; at least one must be positive.
        Individual zero weights are allowed (they receive 0.00).

    Returns
    -------
    list[str]
        Two-decimal-digit strings whose Decimal sum equals the rounded
        input value exactly (cent-conservation invariant).

    Algorithm
    ---------
    1. Round *value* to cents via ``cents()`` → integer-cents target.
    2. Floor-allocate proportional cents using integer arithmetic.
    3. Distribute the remaining cents one-by-one to the shares with the
       largest fractional remainders; ties go to the earlier input index.
    """
    # --- validation ---
    rounded = cents(value)  # raises ValueError on bad input
    d_value = Decimal(rounded)
    if d_value < 0:
        raise ValueError(f"negative amount: {value!r}")
    target_cents = int(d_value * 100)

    # Convert weights, validate types and sign
    parsed_weights = []
    for w in weights:
        try:
            pw = Decimal(str(w))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(f"invalid weight: {w!r}")
        if not pw.is_finite():
            raise ValueError(f"non-finite weight: {w!r}")
        if pw < 0:
            raise ValueError(f"negative weight: {w!r}")
        parsed_weights.append(pw)

    total_weight = sum(parsed_weights)
    if total_weight == 0:
        raise ValueError("weights sum to zero")

    # --- largest-remainder allocation (Hare / Saint-Lague style) ---
    # Work in integer cents to avoid floating-point drift
    total_weight_d = total_weight  # Decimal, > 0

    allocations_cents = []  # integer cents per share
    remainders = []         # (remainder, index) for tie-breaking

    for i, w in enumerate(parsed_weights):
        # proportional share in integer-cents (floor)
        share_cents = (target_cents * w / total_weight_d).to_integral_value(
            rounding=ROUND_HALF_UP
        )
        # We need exact floor; Decimal division may not be exact.
        # Use integer arithmetic: floor(target_cents * w / total_weight_d)
        # target_cents is int, w and total_weight_d are Decimal.
        # Compute floor via quantize to integer with ROUND_FLOOR
        exact = Decimal(target_cents) * w / total_weight_d
        floor_cents = int(exact.to_integral_value(rounding="ROUND_FLOOR"))
        allocations_cents.append(floor_cents)

        # remainder = exact - floor (as Decimal)
        remainders.append((exact - Decimal(floor_cents), i))

    current_sum = sum(allocations_cents)
    remaining = target_cents - current_sum

    # Sort by remainder descending, then by index ascending for ties
    remainders.sort(key=lambda r: (-r[0], r[1]))

    for j in range(remaining):
        allocations_cents[remainders[j][1]] += 1

    # Format each share as two-decimal string (e.g. "0.00", "1.00", "10.50")
    two = Decimal("0.01")
    return [str((Decimal(c) / 100).quantize(two)) for c in allocations_cents]
