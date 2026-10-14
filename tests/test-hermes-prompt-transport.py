"""Exercise the production stdin path and installed Hermes parser, without inference.

Only the inference boundary is instrumented in a temporary wrapper copy. Native
CLI parsing and _read_query_file run unchanged; no installed files are modified.
"""
import base64
import hashlib
import json
import os
import pathlib
import subprocess
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
E = pathlib.Path(os.environ.get('F24_PREFLIGHT_E',str(ROOT/'evidence/hermes-prompt-transport-20261014')))/'reviewer-transport'
E.mkdir(parents=True,exist_ok=True)
case = ROOT / 'runtime' / ('transport-' + uuid.uuid4().hex)
case.mkdir()
source = ROOT / 'scripts/invoke-hermes.ps1'
prompt = '''Normal text\n"missing rounding feature" and "0.01"
{"nested":{"items":[{"single":"'quoted'", "double":"\\\"quoted\\\""}]}}
diff --git a/calculator.py b/calculator.py
-raise ValueError("missing rounding feature")
+return Decimal("0.01")
--texto-que-parece-opcion
C:\\Project with spaces\\folder\\
& | > < $(Write-Error unsafe) `literal` "dobles" 'simples'
áéíóú ñ ¿? € °
'''+ '\r\nCRLF preserved\r\n'
(case / 'prompt.txt').write_bytes(prompt.encode('utf-8'))
expected = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
probe = case / 'probe.py'
probe.write_text('''import sys, json, hashlib, os, time
def capture(frame, event, arg):
    if event == 'return' and frame.f_code.co_name == '_read_query_file':
        query = frame.f_locals['args'].query
        print(json.dumps({'native_prompt_sha256': hashlib.sha256(query.encode('utf-8')).hexdigest(),
                          'query': query, 'argv': sys.argv, 'ARGPARSE_ERROR': False}, ensure_ascii=False))
        sys.setprofile(None)
        if os.environ.get('DA_TRANSPORT_PROBE_SLEEP'):
            time.sleep(60)
        raise SystemExit(0)
sys.setprofile(capture)
''', encoding='utf-8')
q = lambda value: "'" + str(value).replace("'", "''") + "'"
text = source.read_text(encoding='utf-8-sig')
# A copy keeps all integrity, inference-lock, owned-job and byte transport logic.
text = text.replace('$infraRoot = (Resolve-Path "$scriptDir\\..").Path', '$infraRoot = ' + q(ROOT), 1)
needle = '$runtimeCommand[3]=$hermesPrelude+"`n"+$runtimeCommand[3]'
assert text.count(needle) == 1
text = text.replace(needle, "$hermesPrelude += \"`nimport runpy; runpy.run_path(os.environ['DA_TRANSPORT_PROBE'])\"\n    " + needle)
wrapper = case / 'wrapper.ps1'
wrapper.write_text(text, encoding='utf-8-sig')
env = dict(os.environ, DA_TRANSPORT_PROBE=str(probe), PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
results = []
try:
    for role, mode in (('reviewer', 'chat-stream-json'), ('supervisor', 'chat')):
        body = "$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules';[Console]::OutputEncoding=[Text.Encoding]::UTF8;"
        body += '$p=[IO.File]::ReadAllText(' + q(case / 'prompt.txt') + ',(New-Object Text.UTF8Encoding($false,$true)));'
        body += '$r=& '+q(wrapper)+' -Mode '+mode+' -Profile desarrollador-autonomo-'+role+' -Prompt $p -TimeoutSeconds 30;'
        body += '$r|ConvertTo-Json -Depth 12 -Compress'
        r = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand', base64.b64encode(body.encode('utf-16le')).decode()], capture_output=True, encoding='utf-8', env=env, timeout=60)
        assert r.returncode == 0, r.stderr
        wrapper_result = json.loads(r.stdout.lstrip('\ufeff'))
        native = json.loads(wrapper_result['Stdout'].strip())
        item = {'role': role, 'mode': mode, 'wrapper': wrapper_result, 'native': native,
                'expected_sha256': expected, 'PROMPT_INTEGRITY': native['native_prompt_sha256'] == expected and native['query'] == prompt,
                'UTF8': native['query'] == prompt, 'content_absent_from_argv': prompt not in native['argv'] and '--query-file' in native['argv']}
        results.append(item)
        assert wrapper_result['ExitCode'] == 0 and not wrapper_result['TimedOut'], wrapper_result
        assert item['PROMPT_INTEGRITY'] and item['UTF8'] and item['content_absent_from_argv'], item
    # Failure path: a slow native process must time out and close its owned job.
    timeout_env = dict(env, DA_TRANSPORT_PROBE_SLEEP='1')
    body = "$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules';[Console]::OutputEncoding=[Text.Encoding]::UTF8;"
    body += '$p=[IO.File]::ReadAllText('+q(case/'prompt.txt')+');$r=& '+q(wrapper)+' -Mode chat -Profile desarrollador-autonomo-reviewer -Prompt $p -TimeoutSeconds 5;$r|ConvertTo-Json -Depth 12 -Compress'
    r = subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(body.encode('utf-16le')).decode()],capture_output=True,encoding='utf-8',env=timeout_env,timeout=40)
    timeout_result = json.loads(r.stdout.lstrip('\ufeff'))
    assert r.returncode == 0 and timeout_result['TimedOut'] and not timeout_result['Success'], timeout_result
    result = {'status': 'PASS', 'ARGPARSE_ERROR': False, 'PROMPT_INTEGRITY': 'PASS', 'UTF8': 'PASS', 'results': results,
              'timeout_test': 'PASS', 'timeout_result': timeout_result,
              'wrapper_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'probe': 'native parser and stdin reader; inference intercepted after read', 'local_inferences': 0}
finally:
    # Only task-created files in the verified task-specific runtime directory.
    assert case.parent == ROOT / 'runtime' and case.name.startswith('transport-')
    for path in case.iterdir():
        if path.is_file(): path.unlink()
    case.rmdir()
(E / 'complex-transport.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='results'}, ensure_ascii=False))
