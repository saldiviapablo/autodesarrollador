from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


def cents(value):
    """Convert *value* to a ``Decimal`` via ``str(value)`` and round to two
    decimal places using **ROUND_HALF_UP** (not banker's rounding).

    Raises ``ValueError`` on malformed input, non-finite values (NaN, Infinity)
    or ``None``.
    """
    # Reject None / floats that are NaN or inf before string conversion
    if value is None:
        raise ValueError(f"cents() does not accept None")
    # Catch Python floats that are NaN / Infinity *before* str() (which would
    # produce "nan" / "inf" strings — we want to be strict about floats).
    if isinstance(value, float):
        import math
        if math.isfinite(value):
            value = Decimal(str(value))
        else:
            raise ValueError(f"cents() rejects non-finite float: {value!r}")
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"cents() cannot parse {value!r}")
    if not d.is_finite():
        raise ValueError(f"cents() rejects non-finite value: {value!r}")
    return str(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def total(lines):
    """Return the two-decimal-string total of *lines*.

    *lines* is an iterable of ``(price_str, quantity)`` tuples.  Each line's
    ``price * quantity`` is computed exactly using ``Decimal`` arithmetic.
    The sum is rounded **once** at the end with ROUND_HALF_UP to two decimal
    places — individual line products are *not* rounded prematurely.
    """
    sum_ = Decimal("0")
    for price, qty in lines:
        sum_ += Decimal(str(price)) * Decimal(str(qty))
    return str(sum_.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def allocate(value, weights):
    """Largest-remainder (Hare/Nq) allocation of *value* across *weights*.

    Parameters
    ----------
    value : str | Decimal
        Non-negative monetary amount (e.g. ``"1.00"``).
    weights : list[int | float | str | Decimal]
        Positive numeric weights.  A single ``0`` weight is allowed and yields
        ``"0.00"``.  Negative, missing, or non-numeric entries raise
        ``ValueError``.  Total weight of zero raises ``ValueError``.

    Returns
    -------
    list[str]
        Two-decimal strings whose Decimal sum equals the rounded input value
        exactly (cent conservation).  Ties in the largest-remainder step are
        broken by earlier input index.

    Raises
    ------
    ValueError
        If *value* is negative, malformed, or non-finite; or if any weight
        is negative, malformed, or non-numeric; or if total weight is zero.
    """
    # --- validate amount ---------------------------------------------------
    if value is None:
        raise ValueError("allocate() rejects None amount")
    try:
        amt = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"allocate() cannot parse amount {value!r}")
    if not amt.is_finite():
        raise ValueError(f"allocate() rejects non-finite amount: {value!r}")
    if amt < 0:
        raise ValueError(f"allocate() rejects negative amount: {amt}")

    rounded_amt = int(amt.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) * 100)

    # --- validate weights --------------------------------------------------
    parsed = []
    for w in weights:
        if w is None:
            raise ValueError(f"allocate() rejects None weight")
        try:
            parsed.append(Decimal(str(w)))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(f"allocate() cannot parse weight {w!r}")
        if parsed[-1] < 0:
            raise ValueError(f"allocate() rejects negative weight: {parsed[-1]}")

    total_weight = sum(parsed, Decimal("0"))
    if total_weight == 0:
        raise ValueError("allocate() requires total weight > 0")

    n = len(weights)
    if n == 0:
        raise ValueError("allocate() requires non-empty weights")

    # --- integer-cent base allocation (floor) -------------------------------
    # Each share gets floor(rounded_amt * weight / total_weight).
    # The fractional parts are distributed one cent at a time via largest
    # remainder.  Ties in fractional part are broken by earlier input index.
    base = []
    fractional = []
    for i in range(n):
        if parsed[i] == 0:
            # Zero-weight shares get zero cents and zero fractional part.
            base.append(0)
            fractional.append((Decimal("0"), i))
        else:
            exact = Decimal(rounded_amt) * parsed[i] / total_weight
            floored = int(exact)  # int(Decimal) truncates toward zero; for positive exact this IS floor
            frac_part = exact - Decimal(floored)
            base.append(floored)
            fractional.append((frac_part, i))

    remainder = rounded_amt - sum(base)

    # --- largest remainder distribution (ties by earlier index) ------------
    # Compute fractional parts for weights > 0
    fractional = []
    for i in range(n):
        if total_weight == 0 or parsed[i] == 0:
            fractional.append((Decimal("0"), i))
        else:
            exact = (Decimal(rounded_amt) * parsed[i] / total_weight)
            floored = int(exact)
            frac_part = exact - floored
            fractional.append((frac_part, i))

    # Sort by fractional part descending; ties broken by earlier index ascending
    fractional.sort(key=lambda x: (-x[0], x[1]))

    for j in range(remainder):
        idx = fractional[j][1]
        base[idx] += 1

    # --- format: convert integer cents back to two-decimal strings -----------
    # base[i] is an integer number of cents; divide by 100 to get dollars.
    return [str((Decimal(c) / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)) for c in base]
