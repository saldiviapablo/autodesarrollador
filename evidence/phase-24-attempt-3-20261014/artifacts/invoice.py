from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


def cents(value):
    """Convert *value* to a two-decimal string using ROUND_HALF_UP.

    ``value`` may be a string, int, float or Decimal.  NaN, Infinity and
    non-numeric strings raise ``ValueError``.
    """
    if isinstance(value, float):
        if not (value == value and value != float("inf") and value != float("-inf")):
            raise ValueError(f"non-finite float: {value!r}")

    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValueError(f"invalid monetary value: {value!r}")

    if not d.is_finite():
        raise ValueError(f"non-finite Decimal: {d}")

    return str(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def total(lines):
    """Return the cent-precise total of *(price, quantity)* pairs.

    *price* is interpreted via :func:`cents`; *quantity* is multiplied as a
    raw Decimal (no rounding on individual line items).  The final sum is
    rounded to two decimals with ROUND_HALF_UP.
    """
    acc = Decimal("0")
    for price, qty in lines:
        acc += Decimal(str(price)) * Decimal(str(qty))
    return str(acc.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def allocate(value, weights):
    """Split *value* (a two-decimal string) across *weights* via largest
    remainder (Hare / Sainte-Laguë style integer-cent allocation).

    Returns a list of two-decimal strings that sum *exactly* to the
    rounded input value.

    Validation
    ----------
    * *value* must be non-negative.
    * Every weight must be a non-negative number; total weight must be
      positive.  Zero weights are allowed (they receive ``"0.00"``).
    * Non-numeric or non-finite inputs raise ``ValueError``.
    """
    # ---- validate & normalise amount ----
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValueError(f"invalid amount: {value!r}")
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"amount must be non-negative: {value!r}")

    amount_cents = int(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) * 100)

    # ---- validate & normalise weights ----
    try:
        weights = [int(w) for w in weights]
    except (TypeError, ValueError):
        raise ValueError(f"all weights must be numeric: {weights!r}")

    if len(weights) == 0:
        raise ValueError("weights list must not be empty")
    if any(w < 0 for w in weights):
        raise ValueError(f"all weights must be non-negative: {weights!r}")
    total_weight = sum(weights)
    if total_weight == 0:
        raise ValueError("total weight must be positive")

    # ---- largest remainder (integer cents) ----
    # Each share gets (amount_cents * w) // total_weight cents.
    # Then distribute the remaining cents one-by-one to weights with the
    # largest fractional parts (ties broken by earlier index).
    shares_cents = []
    for w in weights:
        shares_cents.append((amount_cents * w) // total_weight)

    remainder = amount_cents - sum(shares_cents)

    # We need to distribute *remainder* extra cents.  The fractional part
    # of share *i* is ((amount_cents * w) % total_weight).  Sort by
    # descending fractional remainder, break ties by ascending index.
    indices = sorted(range(len(weights)),
                     key=lambda i: (
                         -((amount_cents * weights[i]) % total_weight), i))

    # Debug
    import sys
    print(f"DEBUG: amount_cents={amount_cents}, total_weight={total_weight}", file=sys.stderr)
    print(f"DEBUG: weights={weights}", file=sys.stderr)
    print(f"DEBUG: shares_cents before allocation={shares_cents}", file=sys.stderr)
    print(f"DEBUG: remainder={remainder}", file=sys.stderr)
    print(f"DEBUG: indices={indices}", file=sys.stderr)
    for i in range(len(weights)):
        frac = (amount_cents * weights[i]) % total_weight
        print(f"DEBUG: share[{i}] frac={frac}", file=sys.stderr)

    for j in range(remainder):
        shares_cents[indices[j]] += 1

    print(f"DEBUG: shares_cents after allocation={shares_cents}", file=sys.stderr)

    return [cents(Decimal(c) / 100) for c in shares_cents]
