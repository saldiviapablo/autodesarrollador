from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

_CENT = Decimal("0.01")


def cents(value):
    """Round *value* to two decimal places using ROUND_HALF_UP.

    Accepts str, int, float or Decimal.  Rejects malformed, NaN or
    non-finite inputs by raising *ValueError*.  Returns a two-digit
    string (e.g. ``"3.10"``).
    """
    if isinstance(value, str):
        stripped = value.strip()
        try:
            d = Decimal(stripped)
        except InvalidOperation:
            raise ValueError(f"invalid monetary value: {value!r}")
        if not d.is_finite():
            raise ValueError(f"non-finite monetary value: {value!r}")
    else:
        d = Decimal(str(value))
    rounded = d.quantize(_CENT, rounding=ROUND_HALF_UP)
    return format(rounded, "f")


def total(lines):
    """Return the cent-conserving total of *lines*.

    *lines* is an iterable of ``(price, quantity)`` pairs.  Each product
    is accumulated in full Decimal precision and the sum is rounded once
    at the end (ROUND_HALF_UP to 0.01).  Individual prices are **not**
    rounded before accumulation.
    """
    s = Decimal("0")
    for price, quantity in lines:
        s += Decimal(str(price)) * Decimal(str(quantity))
    return format(s.quantize(_CENT, rounding=ROUND_HALF_UP), "f")


def allocate(value, weights):
    """Largest-remainder allocation in integer cents.

    *value* – non-negative monetary amount (str|int|float|Decimal).
    *weights* – positive numeric non-negative weights; a total-weight
    of zero or any negative weight raises *ValueError*.

    Allocation algorithm (integer-cents largest remainder / Hare method):
    1. Convert *value* to an integer number of cents.
    2. ``floor_cents[i] = total_cents * weights[i] // total_weight``.
    3. Compute the unspent remainder and distribute it one-by-one to
    the shares with the largest remainders (ties go to the earlier
    index).
    4. Returns a list of two-decimal strings that sum exactly to the
    rounded input value.
    """
    # --- validation ---
    try:
        d = Decimal(str(value)) if not isinstance(value, str) else Decimal(value.strip())
    except InvalidOperation:
        raise ValueError(f"invalid allocation amount: {value!r}")
    if not d.is_finite():
        raise ValueError(f"non-finite allocation amount: {value!r}")
    if d < 0:
        raise ValueError("amount must be non-negative")

    total_weight = Decimal("0")
    int_weights = []
    for i, w in enumerate(weights):
        try:
            iw = int(Decimal(str(w)))
        except Exception:
            raise ValueError(f"weight[{i}] is not a valid number: {w!r}")
        if iw < 0:
            raise ValueError(f"weight[{i}] must be non-negative, got {iw}")
        int_weights.append(iw)
        total_weight += iw

    if total_weight == 0:
        raise ValueError("total weight must be positive")

    # --- integer-cents allocation ---
    # Convert value to total integer cents (multiply by 100, round once)
    total_cents = int((d * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    floor_cents = []
    remainders = []  # (remainder_fraction, index)
    for i, w in enumerate(int_weights):
        fc = total_cents * w // total_weight
        floored = total_cents * w - fc * total_weight  # leftover numerator
        remainders.append((floored, i))
        floor_cents.append(fc)

    # Sort by descending remainder, break ties by smaller index (earlier input)
    remainders.sort(key=lambda r: (-r[0], r[1]))

    # Distribute the leftover cents one by one
    leftover = total_cents - sum(floor_cents)
    if isinstance(leftover, Decimal):
        leftover = int(leftover)
    for j in range(leftover):
        floor_cents[remainders[j][1]] += 1

    # Format as two-decimal strings (divide cents back to monetary format)
    return [format(Decimal(c) / 100, "0.2f") for c in floor_cents]
