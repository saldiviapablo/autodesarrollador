from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


def cents(value):
    """Convert *value* to a two-decimal-digit string using ROUND_HALF_UP.

    Accepts int, float, str, or Decimal.  Malformed, non-finite, NaN,
    Infinity or ``None`` values raise ``ValueError``.
    """
    if value is None:
        raise ValueError(f"invalid cents value: {value!r}")

    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError(f"invalid cents value: {value!r}")
        dec = Decimal(str(value))
    elif isinstance(value, Decimal):
        if value.is_nan() or value.is_infinite():
            raise ValueError(f"invalid cents value: {value!r}")
        dec = value
    else:
        # Coerce via str so Decimal("2.675") works naturally.
        try:
            dec = Decimal(str(value))
        except Exception as exc:
            raise ValueError(f"invalid cents value: {value!r}") from exc

    if dec.is_nan() or dec.is_infinite():
        raise ValueError(f"invalid cents value: {value!r}")

    try:
        rounded = dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise ValueError(f"invalid cents value: {value!r}")

    return str(rounded)


def total(lines):
    """Return the cent-accurate total of *lines* as a two-decimal string.

    Each line is ``(price, quantity)``.  Prices are converted via
    :func:`cents` *after* multiplying by quantity (individual prices are
    **not** rounded first).  The raw sum is then rounded ROUND_HALF_UP to
    the nearest cent.
    """
    raw_sum = Decimal("0")
    for price, quantity in lines:
        raw_sum += Decimal(str(price)) * Decimal(str(quantity))
    return str(raw_sum.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def allocate(value, weights):
    """Allocate *value* across *weights* using the largest-remainder method.

    Parameters
    ----------
    value : str | int | float | Decimal
        Non-negative amount to allocate.
    weights : list[int | float | str]
        Positive numeric weights.  Individual zeros are allowed (the share
        for that slot is ``0.00``).  Empty, all-zero, negative, or
        non-numeric weight values raise ``ValueError``.

    Returns
    -------
    list[str]
        Two-decimal-digit strings that sum exactly to *value* (rounded).

    Algorithm
    ---------
    1. Convert *value* to integer cents.
    2. Distribute ``floor(weight_i / sum(weights) * total_cents)`` cents
       to each slot.
    3. Distribute the remaining cents one-by-one to slots with the largest
       fractional remainders, breaking ties by earlier input index.

    Examples
    --------
    >>> allocate("0.05", [1, 1, 1])
    ['0.02', '0.02', '0.01']
    >>> allocate("1.00", [1, 2, 3])
    ['0.17', '0.33', '0.50']
    """
    # --- Validate amount ---
    if value is None:
        raise ValueError(f"invalid amount: {value!r}")

    try:
        dec_value = Decimal(str(value))
    except Exception as exc:
        raise ValueError(f"invalid amount: {value!r}") from exc

    if dec_value < 0:
        raise ValueError(f"amount must be non-negative, got {dec_value}")
    if dec_value.is_nan() or dec_value.is_infinite():
        raise ValueError(f"amount must be non-negative, got {dec_value}")

    total_cents = int((dec_value * 100).to_integral_value(rounding=ROUND_HALF_UP))

    # --- Validate weights ---
    if not weights or not isinstance(weights, (list, tuple)):
        raise ValueError(f"weights must be a non-empty list, got {weights!r}")

    numeric_weights = []
    for w in weights:
        try:
            numeric_weights.append(Decimal(str(w)))
        except Exception as exc:
            raise ValueError(f"invalid weight {w!r}: {exc}") from exc

    if any(w < 0 for w in numeric_weights):
        raise ValueError(f"weights must be non-negative, got {weights!r}")

    weight_sum = sum(numeric_weights)
    if weight_sum == 0:
        raise ValueError(f"total weight must be > 0, got {weights!r}")

    # --- Largest-remainder allocation ---
    n = len(weights)
    base_cents = []
    remainders = []

    for i, w in enumerate(numeric_weights):
        if w == 0:
            # Zero-weight slots get zero cents; still track remainder for tie-breaking.
            base_cents.append(0)
            remainders.append((Decimal("0"), i))
            continue

        share = Decimal(total_cents) * w / weight_sum
        floor_c = int(share)  # floor toward negative infinity works because share >= 0
        remainder = share - Decimal(floor_c)
        base_cents.append(floor_c)
        remainders.append((remainder, i))

    distributed = sum(base_cents)
    leftover = total_cents - distributed

    # Sort by remainder desc, then by index asc for tie-breaking.
    remainders.sort(key=lambda x: (-x[0], x[1]))

    for j in range(leftover):
        base_cents[remainders[j][1]] += 1

    # Format as two-decimal strings (cents → currency).
    return [str((Decimal(c) / Decimal("100")).quantize(Decimal("0.01"))) for c in base_cents]
