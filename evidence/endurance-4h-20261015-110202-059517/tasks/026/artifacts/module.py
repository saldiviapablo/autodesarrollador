"""Merge integer time intervals, compute gaps and peak concurrency.

All public helpers accept **lists of (start, end) pairs** where every
element is a plain ``int`` (``bool`` is explicitly rejected because
``bool`` is a subclass of ``int`` in Python).  All intervals are
**half-open** ``[start, end)`` — two intervals that merely touch at a
boundary (e.g. ``[0,2)`` and ``[2,4)``) do **not** overlap.

CLI usage
---------
::

    echo '{"intervals":[[1,3],[3,5]],"start":0,"end":6}' | python module.py

Output JSON
-----------
::

    {"merged":[[1,5]],"gaps":[[0,1],[5,6]],"peak":1}

Invalid input causes exit code 2 with a concise one-line message on
stderr (no Python traceback).
"""

import json
import sys
from typing import List, Tuple


# ── helpers ──────────────────────────────────────────────────────────

def _is_int(v: object) -> bool:
    """Return ``True`` only when *v* is a plain ``int`` (not ``bool``)."""
    return isinstance(v, int) and not isinstance(v, bool)


def _validate_pair(pair: object) -> Tuple[int, int]:
    """Validate and coerce a single (start, end) pair."""
    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
        raise ValueError(f"expected a 2-element list/tuple, got {pair!r}")
    start, end = pair[0], pair[1]
    if not _is_int(start) or not _is_int(end):
        raise ValueError(
            f"interval endpoints must be plain int, got {start!r}, {end!r}"
        )
    if start >= end:
        raise ValueError(
            f"start must be strictly less than end, got ({start},{end})"
        )
    if start < 0:
        raise ValueError(f"start must be >= 0, got {start}")
    return start, end


def _validate_intervals(intervals: object) -> List[Tuple[int, int]]:
    """Validate the full *intervals* list and return normalised tuples."""
    if not isinstance(intervals, list):
        raise ValueError(f"intervals must be a list, got {intervals!r}")
    result: List[Tuple[int, int]] = []
    for pair in intervals:
        result.append(_validate_pair(pair))
    return result


# ── public API ───────────────────────────────────────────────────────

def merge_intervals(intervals: object):
    """Return sorted merged *intervals* as a list of ``(start, end)`` tuples.

    Overlapping and **touching** intervals are merged (half-open semantics:
    ``[0,2)`` and ``[2,4)`` touch and merge into ``[0,4)``).

    The input list is **not mutated**.  Invalid input raises ``ValueError``.
    """
    raw = _validate_intervals(intervals)
    if not raw:
        return []

    # Sort by start, then by end
    sorted_iv = sorted(raw, key=lambda p: (p[0], p[1]))
    merged: List[Tuple[int, int]] = [sorted_iv[0]]

    for start, end in sorted_iv[1:]:
        prev_start, prev_end = merged[-1]
        # Touching (start <= prev_end) or overlapping → merge
        if start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))

    return merged


def gaps(intervals: object, start: object, end: object):
    """Return uncovered intervals in ``[start, end)``.

    * *intervals* – list of valid ``[s, e)`` pairs (must all lie inside
      ``[start, end)``).
    * *start*, *end* – plain ``int``, ``0 <= start < end``.
    * Returns a sorted list of uncovered ``(s, e)`` tuples within the
      window.  Touching intervals are merged before computing gaps.

    Raises ``ValueError`` on invalid input.
    """
    # Validate start/end
    if not _is_int(start) or not _is_int(end):
        raise ValueError("start and end must be plain int")
    if start < 0 or start >= end:
        raise ValueError(f"0 <= start < end required, got ({start},{end})")

    raw = _validate_intervals(intervals)

    # Every interval must be fully inside [start, end)
    for s, e in raw:
        if s < start or e > end:
            raise ValueError(
                f"interval ({s},{e}) lies outside window ({start},{end})"
            )

    # Merge and find uncovered portions in [start, end)
    merged = merge_intervals(raw)
    result: List[Tuple[int, int]] = []
    cursor = start

    for s, e in merged:
        if s > cursor:
            result.append((cursor, s))
        cursor = max(cursor, e)
        if cursor >= end:
            break

    if cursor < end:
        result.append((cursor, end))

    return result


def peak_load(intervals: object) -> int:
    """Return the maximum number of simultaneously active half-open intervals.

    Touching endpoints **do not** overlap: ``[0,2)`` and ``[2,4)`` contribute
    at most 1 concurrent interval.  An empty list returns ``0``.
    """
    raw = _validate_intervals(intervals)
    if not raw:
        return 0

    # Sweep-line: +1 at start, -1 at end.
    events: List[Tuple[int, int]] = []
    for s, e in raw:
        events.append((s, 1))   # interval begins
        events.append((e, -1))  # interval ends

    # Sort: by position; at the same position, ends (-1) before starts (+1)
    # so touching intervals never overlap.
    events.sort(key=lambda ev: (ev[0], ev[1]))

    peak = current = 0
    for _, delta in events:
        current += delta
        if current > peak:
            peak = current

    return peak


# ── CLI ──────────────────────────────────────────────────────────────

def _cli():
    """Read JSON from stdin, print JSON result, exit 2 on error."""
    try:
        import sys
        raw = sys.stdin.read()
        data = json.loads(raw)

        intervals = data["intervals"]
        start = data["start"]
        end = data["end"]

        merged = merge_intervals(intervals)
        gap_list = gaps(intervals, start, end)
        pk = peak_load(intervals)

        out = {
            "merged": [list(t) for t in merged],
            "gaps": [list(t) for t in gap_list],
            "peak": pk,
        }
        print(json.dumps(out))
    except Exception as exc:
        # Concise error, no traceback
        sys.stderr.write(f"invalid input: {exc}\n")
        sys.exit(2)


if __name__ == "__main__":
    _cli()
