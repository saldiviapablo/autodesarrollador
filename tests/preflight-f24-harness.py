"""Deterministic pre-START adapters/gates; never runs a live E2E or ChatGPT send."""
import hashlib,json,os,pathlib,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1];E=pathlib.Path(os.environ.get('F24_PREFLIGHT_E',ROOT/'evidence/f24-harness-preflight-20261014'));E.mkdir(exist_ok=True)
env=dict(os.environ,F24_PREFLIGHT_E=str(E),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',PSModulePath='C:/Windows/System32/WindowsPowerShell/v1.0/Modules')
env['CHATGPT_TEST_EVIDENCE_DIR']=str(E/'chatgpt');(E/'chatgpt').mkdir(exist_ok=True)
bridge=ROOT/'tools/chatgpt-bridge.js';approved=subprocess.run(['git','show','HEAD:tools/chatgpt-bridge.js'],cwd=ROOT,capture_output=True,check=True).stdout
assert bridge.read_bytes()==approved,'APPROVED_BRIDGE_CHANGED'
(E/'chatgpt/integrity-before.json').write_text(json.dumps({'protected':{'tools/chatgpt-bridge.js':hashlib.sha256(approved).hexdigest()}}),encoding='utf-8')
tests=[('web',[sys.executable,'tests/test-research-handoff.py']),('delivery',['node','tests/test-chatgpt-delivery.js']),('domain',['node','tests/test-chatgpt-domain-lock.js']),('idempotency',['node','tests/test-chatgpt-idempotency.js']),('human',['node','tests/test-chatgpt-human-reconciliation.js']),('single-click',['node','tests/test-chatgpt-single-physical-click.js']),('child-cleanup',['powershell.exe','-NoProfile','-NonInteractive','-File','tests/test-chatgpt-child-cleanup.ps1']),('launcher',[sys.executable,'tests/test-windows-launcher-adapter.py']),('reviewer-transport',[sys.executable,'tests/test-hermes-prompt-transport.py']),('completion',[sys.executable,'tests/test-phase20.py']),('recovery',[sys.executable,'tests/test-recovery-continuation.py']),('cleanup',[sys.executable,'tests/test-phase22.py']),('syntax-lock',['powershell.exe','-NoProfile','-NonInteractive','-File','tests/smoke-f24-frontiers.ps1'])]
results={}
tests.insert(1,('send-actuator',['node','tests/test-chatgpt-send-actuator.js']))
tests.insert(1,('frozen-evaluator',[sys.executable,'tests/test-f24-frozen-evaluator.py']))
tests.insert(2,('budget-cache',['powershell.exe','-NoProfile','-NonInteractive','-File','tests/test-runner-budget-merge.ps1']))
tests.append(('native-qwen-input',[sys.executable,'tests/test-qwen-research-model-input.py']))
for name,argv in tests:
 print(json.dumps({'preflight':name,'status':'START'}),flush=True);start=time.monotonic()
 r=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,encoding='utf-8',timeout=500)
 (E/(name+'.stdout.txt')).write_text(r.stdout,encoding='utf-8');(E/(name+'.stderr.txt')).write_text(r.stderr,encoding='utf-8')
 results[name]={'status':'PASS' if r.returncode==0 else 'FAIL','exit_code':r.returncode,'duration_seconds':time.monotonic()-start}
 print(json.dumps({'preflight':name,**results[name]}),flush=True)
 if r.returncode:raise RuntimeError('F24_HARNESS_PREFLIGHT_FAILED: '+name+'; '+r.stderr[-2000:])
from f24_gates import catalog
gates=json.loads((ROOT/'docs/F24-GATES.json').read_text(encoding='utf-8-sig'))
assert gates==catalog() and len(gates['gates'])==28 and len({g['name'] for g in gates['gates']})==28
assert all(all(g.get(k) for k in ('pass_condition','evidence','producer','verification')) for g in gates['gates'])
history=json.loads((E/'history-before.json').read_text(encoding='utf-8'));bad=[p for p,h in history['files'].items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h];assert not bad,bad
result={'status':'PASS','WEB_GATE_FIX':'PASS','F24_HARNESS_PREFLIGHT':'PASS','TOTAL_GATES_FROZEN':28,'gates_sha256':hashlib.sha256((ROOT/'docs/F24-GATES.json').read_bytes()).hexdigest(),'tests':results,'historical_files_preserved':len(history['files']),'actual_messages_sent':0,'local_inferences':0,'attempt5_started':False}
(E/'PREFLIGHT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result),flush=True)
