"""Validated Windows batch invocation for E2E tests; no Runner changes.

cmd.exe does not implement the CRT quoting grammar used by list2cmdline.
Accept literal arguments only; reject shell metacharacters before process creation.
"""
import os
import pathlib
import subprocess

_UNSAFE = frozenset('"&|<>()^%!\r\n\x00')

def _literal(value):
    if not isinstance(value, str):
        raise TypeError('CMD_ARGUMENT_MUST_BE_STRING')
    if any(char in _UNSAFE for char in value):
        raise ValueError('CMD_UNSAFE_ARGUMENT_DENIED')
    return '"' + value + '"'

def launch_batch(launcher, arguments, *, cwd=None, env=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
    """Start a validated batch exactly once using CreateProcess (shell=False)."""
    if os.name != 'nt':
        raise OSError('WINDOWS_BATCH_ADAPTER_REQUIRES_WINDOWS')
    path = pathlib.Path(launcher).resolve(strict=True)
    if not path.is_file() or path.suffix.lower() not in ('.bat', '.cmd'):
        raise ValueError('BATCH_LAUNCHER_REQUIRED')
    if not isinstance(arguments, (list, tuple)):
        raise TypeError('CMD_ARGUMENT_LIST_REQUIRED')
    tokens = [_literal(str(path)), *[_literal(value) for value in arguments]]
    cmd = pathlib.Path(os.environ['SystemRoot']) / 'System32/cmd.exe'
    cmd = cmd.resolve(strict=True)
    # Each already-validated literal has one pair of quotes. Pass a raw Windows
    # command line to avoid Python applying list2cmdline to the /c expression.
    line = _literal(str(cmd)) + ' /d /v:off /s /c "' + ' '.join(tokens) + '"'
    return subprocess.Popen(line, executable=str(cmd), shell=False, cwd=cwd,
                            env=env, stdout=stdout, stderr=stderr,
                            text=True, encoding='utf-8', errors='strict')
