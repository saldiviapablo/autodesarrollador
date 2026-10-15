from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


def cents(value):
    """Round a monetary value to two decimal places using ROUND_HALF_UP.

    Accepts anything that can be turned into a *Decimal* via ``str()``:
    strings like ``"2.675"``, ints, floats (converted through str first),
    or existing Decimal instances.

    Rejects malformed or non-finite amounts with ``ValueError``.
    """
    text = str(value)

    if text in ("NaN", "Infinity", "-Infinity", "+Infinity", "inf", "-inf",
                "sNaN", "-sNaN"):
        raise ValueError(f"non-finite amount: {value!r}")

    try:
        d = Decimal(text)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"invalid monetary amount: {value!r}")

    if not d.is_finite():
        raise ValueError(f"non-finite amount: {value!r}")

    return str(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def total(lines):
    """Return the cents-string of the sum of ``price * quantity`` items.

    Parameters
    ----------
    lines : iterable of (price, quantity)
        *price* is a monetary value (string / number); *quantity* is an int.
        Raw price * quantity products are summed, then rounded once at the end.

    Returns
    -------
    str
        Two-decimal digits, e.g. ``"8.35"``.
    """
    subtotal = Decimal("0")
    for price, quantity in lines:
        subtotal += Decimal(str(price)) * quantity
    return str(subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def allocate(value, weights):
    """Distribute a monetary *value* across slots using largest remainder.

    Parameters
    ----------
    value : str | Decimal
        The total amount to allocate (non-negative, i.e. ``>= 0``).
    weights : list[int | float | str]
        Positive numeric weights for each slot.  Individual zero weights are
        allowed (they simply receive ``"0.00"``).  Empty lists, all-zero
        lists, negative values, or non-numeric entries are rejected.

    Returns
    -------
    list[str]
        One two-decimal string per weight.  The sum is guaranteed to equal
        ``cents(value)`` exactly.  Ties are broken by earlier input index.
    """
    # --- validate amount (must be non-negative) ---
    try:
        total_cents = Decimal(cents(value))
    except (ValueError, TypeError):
        raise ValueError(f"invalid allocation amount: {value!r}")

    if total_cents < 0:
        raise ValueError(f"negative allocation amount: {value!r}")

    # --- validate weights ---
    numeric_weights = []
    for w in weights:
        try:
            nw = Decimal(str(w))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(f"non-numeric weight: {w!r}")
        if nw < 0:
            raise ValueError(f"negative weight: {w!r}")
        numeric_weights.append(nw)

    total_weight = sum(numeric_weights)
    if total_weight <= 0:
        raise ValueError(
            "weights must be non-negative with at least one positive value"
        )

    # --- integer-cent allocation ---
    total_int = int(total_cents * 100)

    floored = [(total_int * int(w)) // int(total_weight) for w in numeric_weights]
    remainder = total_int - sum(floored)

    # Largest remainder: compute fractional parts, sort by (-fraction, index)
    fractional = []
    total_w_int = int(total_weight)
    for i, w in enumerate(numeric_weights):
        w_int = int(w)
        if total_w_int <= 0 or w_int == 0:
            fractional.append((Decimal("0"), i))
            continue
        exact = (total_int * w_int) % total_w_int
        fractional.append((Decimal(exact) / total_w_int, i))

    fractional.sort(key=lambda x: (x[0], -x[1]), reverse=True)

    for j in range(remainder):
        idx = fractional[j][1]
        floored[idx] += 1

    return [str((Decimal(c) / 100).quantize(Decimal("0.01"))) for c in floored]
