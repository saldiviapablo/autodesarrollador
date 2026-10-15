# catalog

Portable file catalog validator and duplicate grouper.  Operates purely
on in-memory data — **never accesses the filesystem**.

## API

### `catalog(entries) -> list[dict]`

Validates a list of file-entry dicts and returns a **new** list sorted by
`path`.  Input is never mutated.

**Entry contract**

Each entry must be a dict with **exactly** three keys:

| Key      | Type               | Constraint                                                                                   |
|----------|--------------------|----------------------------------------------------------------------------------------------|
| `path`   | `str`              | Non-empty POSIX relative path. No backslash, colon, leading `/`, `//`, `.` or `..` component, NUL or newline. Unicode allowed. |
| `size`   | `int` (not `bool`) | `size >= 0`                                                                                  |
| `sha256` | `str`              | Exactly 64 lowercase hex characters `[0-9a-f]{64}`                                           |

Invalid or duplicate-path entries raise ``ValueError``.

**Example**

```python
>>> from module import catalog
>>> entries = [
...     {'path': 'docs/readme.md', 'size': 1024, 'sha256': 'a' * 64},
...     {'path': 'src/main.py',    'size': 512,  'sha256': 'b' * 64},
... ]
>>> catalog(entries)
[{'path': 'docs/readme.md', 'size': 1024, 'sha256': 'a' * 64},
 {'path': 'src/main.py', 'size': 512, 'sha256': 'b' * 64}]
```

**Unicode paths**

```python
>>> catalog([{'path': 'ñ/datos.txt', 'size': 0, 'sha256': 'c' * 64}])
[{'path': 'ñ/datos.txt', 'size': 0, 'sha256': 'c' * 64}]
```

### `duplicate_groups(entries) -> list[list[str]]`

Returns groups of paths that share the same ``(size, sha256)`` tuple.

* Each group is a sorted list of path strings (≥ 2 members).
* Groups are sorted lexicographically by their first path.
* Returns ``[]`` when no duplicates exist.

**Example**

```python
>>> from module import duplicate_groups
>>> entries = [
...     {'path': 'a', 'size': 100, 'sha256': 'x' * 64},
...     {'path': 'b', 'size': 100, 'sha256': 'x' * 64},
...     {'path': 'c', 'size': 200, 'sha256': 'y' * 64},
... ]
>>> duplicate_groups(entries)
[['a', 'b']]
```

## CLI

Reads a JSON array from **stdin**, outputs JSON to **stdout**:

```bash
echo '[{"path":"a","size":1,"sha256":"a..."}]' | python module.py
# → {"catalog": [...], "duplicates": [...]}
```

- Exit 0 on success, exit 2 on invalid JSON or malformed entries.
- ``ensure_ascii=False`` so Unicode paths are emitted directly.

## No filesystem I/O

Neither function opens, reads, writes, or stat-s any file on disk.
All validation and grouping is done purely on the Python objects passed
as arguments.
