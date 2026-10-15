# catalog

Portable file catalog validator and duplicate-group reporter. **No filesystem access** — all paths are treated as opaque portable POSIX relative strings.

## API

### `catalog(entries)`

Validates and sorts a list of file-entry dicts.

**Input:** `list[dict]` — each dict must have exactly three keys:
- `path` — non-empty POSIX relative path (no `\`, `:`, `/` prefix, empty components, `.` or `..`; Unicode allowed)
- `size` — integer >= 0 (bool forbidden)
- `sha256` — exactly 64 lowercase hex characters `[0-9a-f]`

**Returns:** A **new** list of validated dicts sorted lexicographically by `path`. The input list is never mutated.

**Raises:** `ValueError` on malformed entries, extra/missing keys, duplicate paths, or invalid field types.

**Examples:**
```python
>>> catalog([{'path': 'b.txt', 'size': 10, 'sha256': 'a'*64},
...          {'path': 'a.txt', 'size': 5, 'sha256': 'b'*64}])
[{'path': 'a.txt', 'size': 5, 'sha256': 'bb...'}, {'path': 'b.txt', 'size': 10, 'sha256': 'aa...'}]

>>> catalog([{'path': 'a.txt', 'size': 10, 'sha256': 'a'*64},
...          {'path': 'a.txt', 'size': 20, 'sha256': 'b'*64}])
ValueError: duplicate path: 'a.txt'
```

### `duplicate_groups(entries)`

Finds groups of entries sharing the same ``(size, sha256)`` fingerprint.

**Returns:** `list[list[str]]` — each inner list contains sorted paths; only groups with >= 2 members; groups sorted by first path.

**Example:**
```python
>>> duplicate_groups([
...     {'path': 'x.mp3', 'size': 100, 'sha256': 'aa'...},
...     {'path': 'y.mp3', 'size': 100, 'sha256': 'aa'...},
...     {'path': 'z.mp3', 'size': 200, 'sha256': 'bb'...},
... ])
[['x.mp3', 'y.mp3']]
```

## CLI

```bash
echo '[{"path":"a.txt","size":10,"sha256":"a"*64}]' | python module.py
```

**Output:** JSON object with ``catalog`` and ``duplicates`` keys (``ensure_ascii=False``).
Exit code 2 on invalid input (concise error to ``stderr``).

## Unicode

Paths may contain Unicode (``ñ``, ``中文``, ``é``, etc.). Validation checks for structural integrity only — no encoding conversion is performed.

## Constraints

- **No filesystem I/O** — all operations are in-memory.
- **Immutable** — input is never mutated; deep copies are used internally.
- **Portable** — paths follow POSIX conventions (no drive letters, backslashes, or absolute prefixes).
