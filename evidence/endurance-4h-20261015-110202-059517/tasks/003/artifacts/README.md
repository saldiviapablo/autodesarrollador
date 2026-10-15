# catalog

Portable file catalog validator and duplicate grouper. **No filesystem access** — all operations are in-memory.

## API

### `catalog(entries)`

Validates a list of file entries and returns a new list sorted by `path`.

**Contract**

* *entries* — list of dicts, each with exactly `{path: str, size: int, sha256: str}`.
  * `path` — nonempty POSIX relative path (no backslash, colon, leading `/`, empty component, `.` or `..`). Unicode allowed. No NUL or newline.
  * `size` — integer >= 0. `bool` is forbidden.
  * `sha256` — exactly 64 lowercase hex characters (`[0-9a-f]`).
* Returns: **new** list of dicts sorted by `path`. Never mutates input.
* Raises: `ValueError` on malformed entry, duplicate path, or unexpected keys.

### `duplicate_groups(entries)`

Groups entries by `(size, sha256)`.

* Input: list of validated entries (same schema as `catalog`).
* Returns: list of lists of path strings. Each inner list contains paths with the same `(size, sha256)` and has length >= 2.
* Groups are sorted lexicographically; paths within each group are also sorted.
* Raises: `ValueError` on invalid input (same rules as `catalog`).

## CLI usage

```bash
# Valid catalog
echo '[{"path":"a.txt","size":10,"sha256":"'"$(python -c 'print("a"*64)"')"'},{"path":"b.txt","size":10,"sha256":"'"$(python -c 'print("a"*64)"')"'},{"path":"c.txt","size":5,"sha256":"'"$(python -c 'print("b"*64)"')"' }]' | python module.py

# Output (pretty-printed JSON):
# {"catalog": [{"path": "a.txt", "size": 10, "sha256": "aa..."}, ...], "duplicates": [["a.txt", "b.txt"]]}

# Invalid input → exit code 2 with concise error on stderr (no traceback)
echo 'bad' | python module.py  # exit 2
```

## Unicode

Unicode characters are supported in paths (e.g. `ñ`, `中文`, `ελληνικά`). The only constraints are the portable POSIX rules listed above.

```python
>>> from module import catalog, duplicate_groups
>>> catalog([{'path': 'ñ/fichero.txt', 'size': 100, 'sha256': 'a'*64}])
[{'path': 'ñ/fichero.txt', 'size': 100, 'sha256': 'a'*64}]
>>> duplicate_groups([
...     {'path': 'a.txt', 'size': 10, 'sha256': 'a'*64},
...     {'path': 'ñ/b.txt', 'size': 10, 'sha256': 'a'*64},
... ])
[['a.txt', 'ñ/b.txt']]
```

## No filesystem I/O

This module never reads or writes files, directories, or environment paths. It depends only on `sys`, `json`, `copy`, `re`, and `collections`.

## Examples

### Duplicate detection

```python
>>> entries = [
...     {'path': 'z.txt', 'size': 50, 'sha256': 'a'*64},
...     {'path': 'a.txt', 'size': 50, 'sha256': 'a'*64},
...     {'path': 'b.txt', 'size': 30, 'sha256': 'b'*64},
...     {'path': 'unique.txt', 'size': 99, 'sha256': 'c'*64},
... ]
>>> duplicate_groups(entries)
[['a.txt', 'z.txt']]
```

### Validation errors

```python
>>> catalog([{'path': '', 'size': 0, 'sha256': 'a'*64}])
ValueError: path must be nonempty

>>> catalog([{'path': 'x', 'size': True, 'sha256': 'a'*64}])
ValueError: size must not be bool

>>> catalog([{'path': 'x', 'size': 1, 'sha256': 'A'*64}])
ValueError: sha256 must be exactly 64 lowercase hex characters

>>> catalog([{'path': 'x', 'size': 1}, {'path': 'x', 'size': 2}])
ValueError: duplicate path: 'x'
```

## Acceptance criteria

1. ✅ Validate a portable file catalog and report duplicates without filesystem access
2. ✅ Immutable acceptance — never mutates input, no filesystem calls
3. ✅ Documented CLI with exit code 2 on invalid input (concise stderr, no traceback)
