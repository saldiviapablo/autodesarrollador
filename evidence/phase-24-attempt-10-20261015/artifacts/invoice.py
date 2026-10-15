from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

_ONE_HUNDRED = Decimal("1.00")


def cents(value):
    """Round *value* to two decimal digits using ROUND_HALF_UP.

    Accepts str, int, float, or Decimal.  Rejects malformed, non-finite,
    missing (None), NaN, and Infinity inputs with ``ValueError``.
    """
    if value is None:
        raise ValueError("cents rejects None")

    # Convert floats/ints through str to avoid binary-representation noise
    if isinstance(value, float):
        if not value == value:          # NaN check
            raise ValueError("cents rejects NaN")
        if value == float("inf") or value == float("-inf"):
            raise ValueError("cents rejects Infinity")
        text = str(value)
    elif isinstance(value, Decimal):
        if value.is_nan() or value.is_infinite():
            raise ValueError("cents rejects NaN/Infinity")
        text = str(value)
    elif isinstance(value, int):
        text = str(value)
    elif isinstance(value, str):
        stripped = value.strip()
        try:
            d = Decimal(stripped)
        except InvalidOperation:
            raise ValueError(f"cents rejects {stripped!r}")
        if d.is_nan() or d.is_infinite():
            raise ValueError(f"cents rejects {stripped!r}")
        text = stripped
    else:
        raise ValueError(f"cents rejects {type(value).__name__}")

    return str(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def total(lines):
    """Return the cents-string of the sum of ``price * quantity`` for every line.

    Individual prices are *not* rounded before multiplication; only the final
    sum is rounded to two decimal digits via ``ROUND_HALF_UP``.
    """
    s = Decimal("0")
    for price, qty in lines:
        s += Decimal(str(price)) * Decimal(str(qty))
    return str(s.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def allocate(value, weights):
    """Largest-remainder allocation of *value* across *weights*.

    Parameters
    ----------
    value : str|int|float|Decimal
        Non-negative monetary amount (e.g. ``"1.00"``).
    weights : list[int|float|Decimal]
        Non-negative weights whose total must be strictly positive.

    Returns
    -------
    list[str]
        Two-decimal-string shares that sum exactly to the rounded *value*.
        Ties are broken by earlier input index.
    """
    # --- validate value ---
    try:
        amt = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"invalid value {value!r}") from exc
    if amt < 0 or amt.is_nan() or amt.is_infinite():
        raise ValueError("value must be non-negative and finite")

    # --- validate weights ---
    int_weights = []
    for w in weights:
        try:
            iw = int(w)
        except (TypeError, ValueError):
            raise ValueError(f"weight must be integer-like, got {w!r}")
        if iw < 0:
            raise ValueError(f"negative weight {iw}")
        int_weights.append(iw)

    total_w = sum(int_weights)
    if total_w == 0:
        raise ValueError("total weight must be positive")

    cents_amt = int(amt * 100)
    n = len(int_weights)

    # Largest-remainder method: each unit of weight gets base cents,
    # remainder cents distributed proportionally by weight.
    base = cents_amt // total_w
    remainder = cents_amt - base * total_w

    # Fractional remainders for positive-weight slots only, sorted descending
    # by fraction, ties broken by earlier input index ascending.
    positive_indices = [i for i in range(n) if int_weights[i] > 0]
    fractions = [(i, Decimal(int_weights[i]) * remainder / total_w)
                 for i in positive_indices]
    fractions.sort(key=lambda t: (-t[1], t[0]))
    frac_count = len(fractions)

    # Each positive-weight slot starts with base * weight_i cents
    result = [Decimal("0.00")] * n
    for i in positive_indices:
        result[i] = Decimal(base * int_weights[i]) / 100

    # Distribute remainder extra cents one at a time, cycling through
    # the sorted fraction list (same slot may receive multiple extras).
    for k in range(remainder):
        result[fractions[k % frac_count][0]] += Decimal("0.01")

    # Return plain two-decimal strings
    return [str(s.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            for s in result]

    # Return plain two-decimal strings
    return [str(s.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            for s in result]
