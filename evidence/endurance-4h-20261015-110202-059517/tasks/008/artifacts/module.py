"""Integer time-interval utilities with strict validation.

All intervals are half-open [start, end): the start point is included
and the end point is excluded.  Touching intervals such as [1,3) and
[3,5) do **not** overlap and are merged together during ``merge_intervals``
because their union covers a contiguous integer span.
"""

import json
import sys
from typing import List, Tuple


# ── helpers ──────────────────────────────────────────────────────────

def _validate_interval(interval: object) -> None:
    """Raise ValueError unless *interval* is exactly ``[int, int]`` with
    ``0 <= start < end`` and ``bool`` is explicitly rejected."""
    if not isinstance(interval, (list, tuple)) or len(interval) != 2:
        raise ValueError(f"expected [start, end], got {interval!r}")
    start, end = interval
    if isinstance(start, bool) or isinstance(end, bool):
        raise ValueError("bool values are not accepted")
    if not isinstance(start, int) or not isinstance(end, int):
        raise ValueError("start and end must be plain ints")
    if start < 0 or start >= end:
        raise ValueError(f"invalid interval {interval}: require 0 <= start < end")


def _validate_intervals(intervals: object) -> List[Tuple[int, int]]:
    """Validate and normalise *intervals* into a list of tuples."""
    if not isinstance(intervals, list):
        raise ValueError(f"expected a list, got {intervals!r}")
    return [_validate_interval(iv) or tuple(iv) for iv in intervals]


# ── public API ───────────────────────────────────────────────────────

def merge_intervals(intervals: object) -> List[Tuple[int, int]]:
    """Merge overlapping / touching integer intervals.

    Returns a **new** list of sorted ``[(start, end), …]`` tuples.
    Input is never mutated.

    Semantics: half-open ``[start, end)``.  Touching intervals
    (e.g. ``[1, 3)`` and ``[3, 5)``) are merged because their union
    covers a contiguous range of integers.
    """
    validated = _validate_intervals(intervals)
    if not validated:
        return []

    # Work on a fresh sorted copy — never mutates input.
    sorted_ivs = sorted(validated, key=lambda iv: (iv[0], iv[1]))
    merged: List[Tuple[int, int]] = [sorted_ivs[0]]

    for start, end in sorted_ivs[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:          # overlap or touch
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


def gaps(intervals: object, start: object, end: object) -> List[Tuple[int, int]]:
    """Return the uncovered integer segments inside ``[start, end)``.

    Parameters
    ----------
    intervals : list of [start, end]
        All intervals must lie *strictly* within the window
        ``0 <= iv[0] < iv[1] <= end`` and ``start <= iv[0]``.
    start, end : int
        Window boundaries (half-open).  ``0 <= start < end``.
    """
    # Validate window.
    if isinstance(start, bool) or isinstance(end, bool):
        raise ValueError("bool values are not accepted")
    if not isinstance(start, int) or not isinstance(end, int):
        raise ValueError("start and end must be plain ints")
    if start < 0 or start >= end:
        raise ValueError(f"invalid window [{start}, {end}): require 0 <= start < end")

    validated = _validate_intervals(intervals)

    # Every interval must be fully inside [start, end).
    for s, e in validated:
        if s < start or e > end:
            raise ValueError(
                f"interval [{s}, {e}) lies outside window [{start}, {end})"
            )

    merged = merge_intervals(intervals)
    result: List[Tuple[int, int]] = []
    cursor = start

    for s, e in merged:
        if s > cursor:
            result.append((cursor, s))
        if e > cursor:
            cursor = e

    if cursor < end:
        result.append((cursor, end))

    return result


def peak_load(intervals: object) -> int:
    """Maximum number of concurrently-active half-open intervals.

    Touching endpoints do **not** overlap  e.g. ``[0,2)`` and ``[2,4)``
    contribute at most ``1`` to the peak.

    Returns ``0`` for empty input.
    """
    validated = _validate_intervals(intervals)
    if not validated:
        return 0

    events: List[Tuple[int, int]] = []
    for s, e in validated:
        events.append((s, 1))       # interval opens
        events.append((e, -1))      # interval closes

    # Sort by time; closes before opens at the same point so that
    # touching intervals never overlap.
    events.sort(key=lambda ev: (ev[0], ev[1]))

    peak = current = 0
    for _, delta in events:
        current += delta
        if current > peak:
            peak = current

    return peak


# ── CLI entry point ──────────────────────────────────────────────────

def _cli() -> None:
    """Read JSON from stdin, print merged / gaps / peak as JSON to stdout.

    On any validation or parsing error writes a concise message to stderr
    and exits with code 2.
    """
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
        intervals = data["intervals"]
        start = data["start"]
        end = data["end"]
    except Exception as exc:
        sys.stderr.write(f"invalid input: {exc}\n")
        sys.exit(2)

    try:
        merged = merge_intervals(intervals)
        gl = gaps(intervals, start, end)
        pk = peak_load(intervals)
    except ValueError as exc:
        sys.stderr.write(f"validation error: {exc}\n")
        sys.exit(2)

    result = {
        "merged": [list(iv) for iv in merged],
        "gaps": [list(iv) for iv in gl],
        "peak": pk,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    _cli()
