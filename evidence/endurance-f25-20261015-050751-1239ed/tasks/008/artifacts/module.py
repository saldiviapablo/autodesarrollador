"""Merge integer time intervals, compute gaps and peak concurrency.

Semantics
---------
All interval APIs use **half-open** [start, end) semantics:
  - The start point is inclusive, the end point is exclusive.
  - Two intervals that "touch" (one ends where the other begins) are
    considered overlapping and **will be merged** by ``merge_intervals``.
  - For ``peak_load``, touching endpoints do **not** overlap (a point where
    one interval ends and another begins counts as concurrency 1, not 2).

Examples
--------
>>> merge_intervals([(1, 4), (4, 6), (7, 8)])
[(1, 6), (7, 8)]   # (1,4) and (4,6) touch → merged

>>> gaps([(2, 4), (4, 6)], 0, 8)
[(0, 2), (6, 8)]   # [2, 6) covered → gaps at [0, 2) and [6, 8)

>>> peak_load([(0, 2), (1, 3), (2, 4)])
2   # (0,2)&(1,3) overlap at t=1; (2,4) touches but does not overlap
"""

import json
import sys
from typing import List, Tuple


def _validate_interval_pair(value) -> bool:
    """Return True if *value* is a valid interval tuple/list [start, end).

    Rules
    -----
    - Must be a 2-element sequence.
    - Both elements must be ``int`` but **not** ``bool`` (bool is a subclass
      of int in Python, so we reject it explicitly).
    - ``0 <= start < end``.
    """
    try:
        if isinstance(value, bool):
            return False
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            return False
        start, end = value
        if isinstance(start, bool) or isinstance(end, bool):
            return False
        if not isinstance(start, int) or not isinstance(end, int):
            return False
        if start < 0 or start >= end:
            return False
        return True
    except (TypeError, ValueError):
        return False


def _validate_intervals(intervals):
    """Validate that *intervals* is a list of valid interval pairs."""
    if not isinstance(intervals, list):
        raise ValueError("intervals must be a list")
    for iv in intervals:
        if not _validate_interval_pair(iv):
            raise ValueError(f"invalid interval: {iv!r}")


def merge_intervals(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Merge overlapping and touching intervals.

    Parameters
    ----------
    intervals : list of [start, end) pairs (integers, 0 <= start < end)

    Returns
    -------
    list of merged [start, end) tuples sorted by start time.

    Raises
    ------
    ValueError : on invalid input.

    Notes
    -----
    - Does **not** mutate the input list.
    - Touching intervals are merged (e.g. (1,4) and (4,6) → (1,6)).
    """
    _validate_intervals(intervals)

    if not intervals:
        return []

    # Work on a deep copy of sorted intervals to avoid mutating input
    sorted_ivs = sorted((iv[0], iv[1]) for iv in intervals)

    merged: List[Tuple[int, int]] = [sorted_ivs[0]]
    for start, end in sorted_ivs[1:]:
        last_start, last_end = merged[-1]
        # Touching or overlapping: start <= last_end (half-open)
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


def gaps(intervals: List[Tuple[int, int]], start: int, end: int) -> List[Tuple[int, int]]:
    """Compute uncovered intervals within [start, end).

    Parameters
    ----------
    intervals : list of [start, end) pairs (integers).
    start, end : window boundaries (integers, 0 <= start < end).

    Returns
    -------
    list of [start, end) tuples representing uncovered time within the window.

    Raises
    ------
    ValueError : on invalid input or if intervals fall outside the window.

    Notes
    -----
    - All *intervals* must be completely inside [start, end).
    - Touching intervals are merged before computing gaps.
    """
    # Validate start/end
    if isinstance(start, bool) or isinstance(end, bool):
        raise ValueError("start and end must be integers, not bool")
    if not isinstance(start, int) or not isinstance(end, int):
        raise ValueError("start and end must be integers")
    if start < 0 or start >= end:
        raise ValueError(f"invalid window: {start}..{end} (require 0 <= start < end)")

    _validate_intervals(intervals)

    # Verify all intervals are within the window [start, end)
    for iv in intervals:
        iv_start, iv_end = iv
        if iv_start < start or iv_end > end:
            raise ValueError(
                f"interval {iv!r} outside window [{start}, {end})"
            )

    # Shift intervals to window-relative coordinates
    shifted = sorted((iv[0] - start, iv[1] - start) for iv in intervals)
    window_size = end - start

    if not shifted:
        return [(start, end)]

    # Merge touching/overlapping intervals
    merged = [shifted[0]]
    for s, e in shifted[1:]:
        last_s, last_e = merged[-1]
        if s <= last_e:
            merged[-1] = (last_s, max(last_e, e))
        else:
            merged.append((s, e))

    # Compute gaps relative to window, then shift back
    result: List[Tuple[int, int]] = []
    current = 0  # current position relative to window start

    for s, e in merged:
        if current < s:
            result.append((start + current, start + s))
        current = max(current, e)

    if current < window_size:
        result.append((start + current, end))

    return result


def peak_load(intervals: List[Tuple[int, int]]) -> int:
    """Compute maximum concurrent half-open intervals.

    Parameters
    ----------
    intervals : list of [start, end) pairs (integers).

    Returns
    -------
    int : maximum number of overlapping intervals at any point.
          Returns 0 for empty input.

    Raises
    ------
    ValueError : on invalid input.

    Notes
    -----
    - Touching endpoints do **not** overlap (half-open semantics).
      E.g. (0,2) and (2,4) → peak = 1.
    """
    _validate_intervals(intervals)

    if not intervals:
        return 0

    # Sweep line: events at interval boundaries.
    # For half-open [s, e):
    #   - start event: +1 concurrency
    #   - end event: -1 concurrency
    #   - On ties, process end events before start events
    #     (so touching intervals don't overlap).
    events: List[Tuple[int, int]] = []
    for iv in intervals:
        events.append((iv[0], 1))    # interval starts
        events.append((iv[1], -1))   # interval ends

    # Sort: by coordinate, then end events (-1) before start events (1)
    events.sort(key=lambda x: (x[0], x[1]))

    max_concurrent = 0
    current = 0
    for _, delta in events:
        current += delta
        max_concurrent = max(max_concurrent, current)

    return max_concurrent


def _cli_main():
    """CLI entry point: read JSON from stdin, output merged/gaps/peak."""
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        print("ERROR: invalid JSON input", file=sys.stderr)
        sys.exit(2)

    # Validate required keys
    if not isinstance(data, dict):
        print("ERROR: input must be a JSON object", file=sys.stderr)
        sys.exit(2)

    for key in ("intervals", "start", "end"):
        if key not in data:
            print(f"ERROR: missing required key '{key}'", file=sys.stderr)
            sys.exit(2)

    try:
        intervals = data["intervals"]
        start = data["start"]
        end = data["end"]

        # Compute results
        merged = merge_intervals(intervals)
        gap_result = gaps(intervals, start, end)
        peak = peak_load(intervals)

        # Output JSON
        output = {
            "merged": [list(iv) for iv in merged],
            "gaps": [list(iv) for iv in gap_result],
            "peak": peak,
        }
        print(json.dumps(output))

    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    _cli_main()
