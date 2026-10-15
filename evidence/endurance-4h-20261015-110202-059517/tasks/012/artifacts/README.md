# catalog

A Python module that validates a portable file catalog and reports duplicates
without any filesystem access.  All data flows through in-memory data
structures only — no ``open()``, ``Path.*``, ``os.*``, or ``shutil.*`` calls.

## API

### ``catalog(entries)``

**Parameters**

``entries`` — ``list[dict]``, each dict must have **exactly** three keys:

| Key       | Type     | Constraint                                                                 |
|-----------|----------|----------------------------------------------------------------------------|
| ``path``  | ``str``  | Non-empty POSIX relative path. No backslash, colon, leading ``/``, ``.`` or ``..`` component, NUL or newline. Empty components (``//``) rejected. Unicode allowed. |
| ``size``  | ``int``  | Integer >= 0. Python ``bool`` is explicitly rejected.                      |
| ``sha256``| ``str``  | Exactly 64 lowercase hexadecimal characters (``[a-f0-9]``).               |

**Returns**

A **new** ``list[dict]`` sorted by ``path`` (standard ``str`` comparison).
The input list and its dicts are never mutated.

**Raises**

``ValueError`` on any violation (malformed entry, duplicate path, wrong type,
extra/missing keys, invalid path syntax, non-integer size, bad sha256 format).

### ``duplicate_groups(entries)``

**Parameters**

``entries`` — output of ``catalog()`` or any list of validated entry dicts.

**Returns**

``list[list[str]]` — each inner list contains the ``path`` strings of entries
sharing the same ``(size, sha256)`` tuple.  Each group is sorted
lexicographically.  Only groups with ``>= 2`` members are included. Groups
themselves are sorted by their first path element.

**Raises**

None (relies on ``catalog()`` pre-validation; passes through invalid input).

## Examples

### Basic usage

```python
>>> from module import catalog, duplicate_groups
>>> entries = [
...     {"path": "a.txt", "size": 100, "sha256": "a" * 64},
...     {"path": "b.txt", "size": 100, "sha256": "a" * 64},  # duplicate of a.txt
...     {"path": "c.txt", "size": 200, "sha256": "b" * 64},
... ]
>>> validated = catalog(entries)
>>> duplicate_groups(validated)
[['a.txt', 'b.txt']]
```

### Unicode paths

Unicode is fully supported in paths:

```python
>>> catalog([
...     {"path": "ñ/dato.csv", "size": 42, "sha256": "b" * 64},
...     {"path": "a.txt", "size": 0, "sha256": "a" * 64},
... ])
[{'path': 'a.txt', 'size': 0, 'sha256': 'aaa...'},
 {'path': 'ñ/dato.csv', 'size': 42, 'sha256': 'bbb...'}]
```

### Invalid input

```python
>>> catalog([{"path": "", "size": 0, "sha256": "a" * 64}])  # empty path
ValueError: path must be non-empty
>>> catalog([{"path": "f", "size": True, "sha256": "a" * 64}])  # bool size
ValueError: size must not be a bool
>>> catalog([{"path": "f", "size": 1, "sha256": "a" * 63}])  # short hash
ValueError: sha256 must be exactly 64 lowercase hex chars
```

## CLI usage

```bash
$ echo '[{"path":"f","size":10,"sha256":"a"*64}]' | python module.py
{"catalog":[{"path":"f","size":10,"sha256":"aaa..."}],"duplicates":[]}
```

- Input: JSON array of entry dicts via ``stdin``.
- Output: JSON object ``{"catalog": ..., "duplicates": ...}`` to ``stdout``
  with ``ensure_ascii=False``.
- On invalid input (bad JSON or validation failure): exit code **2**, concise
  error message to ``stderr`` (no Traceback).

## No filesystem I/O

This module is **pure in-memory**. It does not read, write, list, stat, or
interact with the filesystem in any way.  The "catalog" represents file
metadata supplied by the caller; the module only validates structure and
detects duplicates.

## Testing

```bash
python test_module.py
python build.py
```

Both must exit with code 0.
