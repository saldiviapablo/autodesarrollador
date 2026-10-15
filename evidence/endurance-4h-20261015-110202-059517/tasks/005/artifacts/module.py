"""Merge integer time intervals, compute gaps and peak concurrency.

All public functions validate that inputs are plain ``int`` (not bool) and
raise ``ValueError`` with a concise one-line message on the first bad value
encountered.  ``merge_intervals`` and ``gaps`` return lists of ``(start, end)``
tuples; ``peak_load`` returns a single ``int``.

Semantics
---------
* Intervals are **half-open** ``[start, end)`` — the end is exclusive.
* Two intervals ``[a, b)`` and ``[b, c)`` do **not** overlap (touching at a
  single point is fine).  ``merge_intervals`` merges them because "touching
  intervals" are considered contiguous and are collapsed into ``[a, c)``.
* ``peak_load`` counts concurrency on half-open intervals, so touching
  endpoints contribute 1, not 2.
"""
import json
import sys
from pathlib import Path


# ── helpers ────────────────────────────────────────────────────────────────

def _check_int(value, label: str = "value") -> None:
    """Raise ``ValueError`` when *value* is not a plain ``int`` (bool excluded)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be int, not {type(value).__name__}")


def _check_non_empty_list(items, label: str = "intervals") -> list:
    """Return *items* after validating it is a list of ``[start, end]`` pairs."""
    if not isinstance(items, list):
        raise ValueError(f"{label} must be list")
    for i, iv in enumerate(items):
        if not isinstance(iv, (list, tuple)) or len(iv) != 2:
            raise ValueError(f"{label}[{i}] must be [start, end]")
        s, e = iv[0], iv[1]
        _check_int(s, f"{label}[{i}].start")
        _check_int(e, f"{label}[{i}].end")
        if s < 0:
            raise ValueError(f"{label}[{i}].start must be >= 0")
        if s >= e:
            raise ValueError(f"{label}[{i}]: start ({s}) >= end ({e})")
    return items


# ── public API ─────────────────────────────────────────────────────────────

def merge_intervals(intervals: list) -> list:
    """Merge overlapping and touching integer intervals.

    Returns a new list of ``(start, end)`` tuples sorted by start time.
    Does **not** mutate *intervals*.
    """
    items = _check_non_empty_list(intervals, "intervals")
    if not items:
        return []

    sorted_ivs = sorted(items, key=lambda iv: (iv[0], iv[1]))
    merged = [tuple(sorted_ivs[0])]

    for start, end in sorted_ivs[1:]:
        prev_start, prev_end = merged[-1]
        # Touching or overlapping → merge
        if start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))

    return merged


def gaps(intervals: list, start: int, end: int) -> list:
    """Return sorted uncovered tuples within the window ``[start, end)``.

    Validates that *start*, *end* are plain ``int`` with ``0 <= start < end``,
    and that every interval in *intervals* lies completely inside the window.
    """
    _check_int(start, "start")
    _check_int(end, "end")
    if start < 0:
        raise ValueError("start must be >= 0")
    if start >= end:
        raise ValueError("start must be < end")

    items = _check_non_empty_list(intervals, "intervals")

    for i, iv in enumerate(items):
        if iv[0] < start or iv[1] > end:
            raise ValueError(
                f"intervals[{i}] ({iv[0]},{iv[1]}) outside window ({start},{end})"
            )

    merged = merge_intervals(intervals)
    result = []
    cursor = start

    for m_start, m_end in merged:
        if m_start > cursor:
            result.append((cursor, m_start))
        cursor = max(cursor, m_end)

    if cursor < end:
        result.append((cursor, end))

    return result


def peak_load(intervals: list) -> int:
    """Maximum number of concurrent half-open intervals.

    Touching endpoints do **not** overlap.  Empty input → ``0``.
    """
    items = _check_non_empty_list(intervals, "intervals")
    if not items:
        return 0

    events = []
    for s, e in items:
        events.append((s, 1))   # interval starts
        events.append((e, -1))  # interval ends

    events.sort(key=lambda x: (x[0], x[1]))

    peak = current = 0
    for _, delta in events:
        current += delta
        if current > peak:
            peak = current

    return peak


# ── CLI ────────────────────────────────────────────────────────────────────

def _cli() -> int:
    """Read JSON from stdin, write JSON result to stdout. Exit 2 on error."""
    try:
        raw = Path("/dev/stdin" if sys.platform == "win32" else "/dev/stdin").read_text(encoding="utf-8")
    except Exception:
        raw = sys.stdin.read()

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Invalid JSON: {exc}", file=sys.stderr)
        return 2

    if not isinstance(data, dict):
        print("Input must be a JSON object", file=sys.stderr)
        return 2

    intervals = data.get("intervals")
    start = data.get("start")
    end = data.get("end")

    if intervals is None or start is None or end is None:
        print("Missing keys: intervals, start, end", file=sys.stderr)
        return 2

    try:
        merged = merge_intervals(intervals)
        gap_list = gaps(intervals, start, end)
        peak = peak_load(intervals)
    except ValueError as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        return 2

    output = {
        "merged": [list(t) for t in merged],
        "gaps": [list(t) for t in gap_list],
        "peak": peak,
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
