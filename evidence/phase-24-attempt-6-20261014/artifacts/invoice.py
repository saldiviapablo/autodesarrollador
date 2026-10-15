from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


def cents(value):
    """Round *value* to two decimal places using ROUND_HALF_UP.

    Accepts anything that can be turned into a string-safe Decimal,
    rejects NaN / Infinity / non-numeric strings with ValueError.
    """
    if not isinstance(value, (str, Decimal, int, float)):
        raise ValueError(f"bad monetary value: {value!r}")

    s = str(value).strip()
    try:
        d = Decimal(s)
    except InvalidOperation:
        raise ValueError(f"bad monetary value: {value!r}")

    if not d.is_finite():
        raise ValueError(f"bad monetary value: {value!r}")

    return str(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def total(lines):
    """Sum *price × quantity* pairs and return the total as a cents string.

    *lines* — iterable of ``(price, quantity)`` where each element accepts
    conversion via :func:`cents`.  No intermediate rounding is applied;
    the sum is rounded only once at the end.
    """
    acc = Decimal("0")
    for price, quantity in lines:
        acc += Decimal(str(price)) * Decimal(str(quantity))
    return str(acc.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def allocate(value, weights):
    """Split *value* across *weights* using the largest-remainder method.

    Parameters
    ----------
    value : str | Decimal | int | float
        The total amount to distribute.  Must be non-negative.
    weights : sequence of numbers
        Positive or zero weights.  Zero-weight shares receive nothing.

    Returns
    -------
    list[str]
        One two-decimal string per weight; the list sums exactly to the
        rounded *value*.

    Raises
    ------
    ValueError
        If *value* is negative or malformed, or if *weights* is empty,
        contains negatives, contains non-numeric entries, or sums to
        zero when at least one element is provided.
    """
    # --- validate value ---
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"bad allocation amount: {value!r}")
    if not amount.is_finite():
        raise ValueError(f"bad allocation amount: {value!r}")
    if amount < 0:
        raise ValueError("amount must be nonnegative")

    # --- validate weights ---
    if not weights:
        raise ValueError("weights must not be empty")

    parsed = []
    for w in weights:
        try:
            pw = Decimal(str(w))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(f"bad weight: {w!r}")
        if pw < 0:
            raise ValueError(f"weight must be nonnegative, got {w!r}")
        parsed.append(pw)

    total_weight = sum(parsed)
    if total_weight == 0:
        raise ValueError("total weight must be > 0")

    # --- largest-cent allocation ---
    cent = Decimal("0.01")
    total_cents = int((amount * 100).to_integral_value(rounding=ROUND_HALF_UP))

    # floor cents per share
    floor_cents = [int((w * total_cents) / total_weight) for w in parsed]
    remainder = total_cents - sum(floor_cents)  # >= 0 by construction

    # fractional parts for tie-breaking (largest first, earliest index first)
    frac = []
    for i, (w, fc) in enumerate(zip(parsed, floor_cents)):
        if w == 0:
            frac.append((Decimal("-1"), i))  # zero-weight gets no bump
        else:
            exact = (w * total_cents) / total_weight
            frac.append((exact - Decimal(fc), i))

    # sort by fractional part descending, break ties by index ascending
    indices = sorted(range(len(parsed)), key=lambda i: (frac[i][0], -frac[i][1]), reverse=True)

    result = list(floor_cents)
    for i in indices[:remainder]:
        result[i] += 1  # give one extra cent

    return [str(Decimal(c) * cent) for c in result]
