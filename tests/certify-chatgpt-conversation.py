"""Certify DOM turn layout extraction and existing bridge suites without sending."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
E = Path(os.environ['F24_PREFLIGHT_E']).resolve()
assert E.is_relative_to(ROOT / 'evidence')
D = E / 'chatgpt'
D.mkdir(exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
bridge_sha = sha(ROOT / 'tools/chatgpt-bridge.js')
(D / 'integrity-before.json').write_text(json.dumps({
    'protected': {'tools/chatgpt-bridge.js': bridge_sha},
    'source': 'authorized DOM extractor fix before regression; state machine unchanged'
}), encoding='utf-8')
env = dict(os.environ, F24_PREFLIGHT_E=str(E), CHATGPT_TEST_EVIDENCE_DIR=str(D),
           PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
results = {}
for name in ['conversation', 'transaction', 'fresh-chat', 'delivery', 'send-actuator',
             'single-physical-click', 'domain-lock', 'idempotency', 'human-reconciliation', 'controlled-send-utf8']:
    source = ROOT / 'tests' / ('test-chatgpt-' + name + '.js' if name != 'controlled-send-utf8' else 'test-controlled-send-utf8.js')
    result = subprocess.run(['node', str(source)], cwd=ROOT, env=env, capture_output=True, encoding='utf-8', timeout=45)
    (E / (name + '.stdout.txt')).write_text(result.stdout, encoding='utf-8')
    (E / (name + '.stderr.txt')).write_text(result.stderr, encoding='utf-8')
    results[name] = {'status': 'PASS' if result.returncode == 0 else 'FAIL', 'exit_code': result.returncode}
    print(json.dumps({name: results[name]}), flush=True)
    assert result.returncode == 0, name + ': ' + result.stderr[-2000:]
assert sha(ROOT / 'tools/chatgpt-bridge.js') == bridge_sha
for source in ['runner/contract.py', 'tests/seal-f24-preflight.py']:
    text = (ROOT / source).read_text(encoding='utf-8-sig')
    ast.parse(text, filename=source)
    assert "ROOT/'tools/chatgpt-conversation.js'" in text
(E / 'REGRESSION.json').write_text(json.dumps({
    'status': 'PASS', 'suites': results, 'pre_send_coverage': 'transaction (owned/legacy recovery, abort, interruption, denial paths)',
    'extractor_pinned_for_future_approvals': True, 'real_sends': 0, 'live_browser_access': False,
    'bridge_unchanged_during_tests': True
}, indent=2) + '\n', encoding='utf-8')
