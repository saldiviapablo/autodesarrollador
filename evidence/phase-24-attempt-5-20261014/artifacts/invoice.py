from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

_CENT = Decimal("0.01")


def cents(value):
    """Round *value* to two decimal places using ROUND_HALF_UP.

    Accepts str or numeric types.  Rejects non-finite values
    (NaN, Infinity) and anything that cannot be parsed into a Decimal
    by raising ``ValueError``.
    """
    if isinstance(value, str):
        value = value.strip()
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"cannot parse monetary amount: {value!r}")
    if not d.is_finite():
        raise ValueError(f"non-finite monetary amount: {value!r}")
    return str(d.quantize(_CENT, rounding=ROUND_HALF_UP))


def total(lines):
    """Return the invoice total as a two-decimal string.

    *lines* is an iterable of (price, quantity) pairs.  Prices are
    NOT rounded individually; the sum of *price*×*quantity* is rounded
    once at the end using ROUND_HALF_UP to 0.01.
    """
    acc = Decimal("0")
    for price, qty in lines:
        acc += Decimal(str(price)) * Decimal(str(qty))
    return str(acc.quantize(_CENT, rounding=ROUND_HALF_UP))


def allocate(value, weights):
    """Largest-remainder allocation in integer cents.

    *value* — non-negative monetary string (e.g. "1.00").
    *weights* — positive numeric weights; individual zero weights are
    allowed but the **total** weight must be strictly positive.

    Returns a list of two-decimal strings that sum exactly to the
    rounded value.  Ties are broken in favour of the earlier input
    index.
    """
    # --- validate amount ---------------------------------------------------
    d_value = Decimal(str(value).strip())
    if not d_value.is_finite() or d_value < 0:
        raise ValueError(f"invalid amount: {value!r}")
    target_cents = int(d_value.quantize(_CENT, rounding=ROUND_HALF_UP) * 100)

    # --- validate weights --------------------------------------------------
    weights = list(weights)
    if len(weights) == 0:
        raise ValueError(f"empty weights: {weights!r}")
    numeric_weights = []
    for w in weights:
        try:
            nw = Decimal(str(w))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(f"invalid weight: {w!r}")
        if nw < 0 or not nw.is_finite():
            raise ValueError(f"invalid weight: {w!r}")
        numeric_weights.append(nw)

    total_weight = sum(numeric_weights)
    if total_weight == 0:
        raise ValueError(f"zero total weight: {weights!r}")

    # --- integer-cent allocation via largest remainder ---------------------
    base_cents = [int((w / total_weight) * target_cents) for w in numeric_weights]
    remainder = target_cents - sum(base_cents)

    # fractional parts for tie-breaking (earlier index wins)
    frac = [(Decimal(str(w)) * Decimal(target_cents) / total_weight) % 1
            for w in numeric_weights]
    # Sort indices by descending fractional remainder, ties → earlier index
    for idx in sorted(range(len(frac)), key=lambda i: frac[i], reverse=True):
        if remainder <= 0:
            break
        base_cents[idx] += 1
        remainder -= 1

    return [str((Decimal(c) / 100).quantize(_CENT, rounding=ROUND_HALF_UP)) for c in base_cents]
