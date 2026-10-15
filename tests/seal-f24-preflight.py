"""Seal tested sources and historical preservation before creating a live run."""
import ast,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];env=__import__('os').environ;E=pathlib.Path(env.get('F24_PREFLIGHT_E',ROOT/'evidence/f24-harness-preflight-20261014'))
proof=json.loads((E/'PREFLIGHT.json').read_text(encoding='utf-8-sig'));assert proof['status']=='PASS' and proof['tests']['budget-cache']['status']=='PASS'
native=json.loads((E/'native-qwen-model-input.json').read_text(encoding='utf-8'));assert native['status']=='PASS' and native['installed_native_cli_used'] and native['actual_model_input_research_binding']
assert json.loads((E/'runtime-dependencies.json').read_text(encoding='utf-8'))['status']=='PASS'
proof['tests']['runtime-dependencies']={'status':'PASS','evidence':'runtime-dependencies.json','live_run_started':False}
proof['tests']['native-qwen-input']={'status':'PASS','evidence':'native-qwen-model-input.json','inferences':0,'actual_messages':0}
sources=list((ROOT/'runner').glob('*.py'))+list((ROOT/'runner').glob('*.ps1'))
sources += [ROOT/p for p in ('scripts/invoke-qwen-code.ps1','scripts/invoke-delegation.ps1','scripts/invoke-hermes.ps1','scripts/invoke-hermes-role.ps1','scripts/consultar-chatgpt.ps1','scripts/wait-chatgpt-child.ps1','tools/chatgpt-bridge.js','tools/chatgpt-ledger.js','tools/chatgpt-delivery.js','docs/F24-GATES.json','tests/test-phase24-attempt5-live.py','tests/f24_gates.py','tests/f24_attempt3_fixture.py','tests/windows_launcher_adapter.py','tests/finalize-live-test.ps1','config/system.yaml','config/security.yaml','config/VERSIONS.lock')]
sources += [ROOT/'tools/chatgpt-send-actuator.js',ROOT/env.get('F24_HARNESS','tests/test-phase24-attempt5-live.py')]
for p in sources:
 if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
history=json.loads((E/'history-before.json').read_text(encoding='utf-8'));assert all(sha(ROOT/p)==h for p,h in history['files'].items())
proof['sealed']=True;proof['source_hashes']={p.relative_to(ROOT).as_posix():sha(p) for p in sources};proof['historical_files_preserved']=len(history['files']);(E/'PREFLIGHT.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print('PREFLIGHT SEALED PASS; sources '+str(len(sources)))
