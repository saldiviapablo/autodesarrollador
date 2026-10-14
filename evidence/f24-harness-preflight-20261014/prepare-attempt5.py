"""Prepare a new harness source only; this does not create/start a live run."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
s=(root/'tests/test-phase24-attempt4-live.py').read_text(encoding='utf-8-sig')
s=s.replace('attempt 4','attempt 5').replace('Attempt 4','Attempt 5').replace('ATTEMPT_4','ATTEMPT_5').replace('ATTEMPT 4','ATTEMPT 5').replace('attempt4','attempt5').replace('attempt-4','attempt-5').replace('f24-a4','f24-a5').replace("'attempt': 4","'attempt': 5")
s=s.replace("ROOT / 'evidence/f24-frontiers-20261014/historical-preservation-before.json'","ROOT / 'evidence/f24-harness-preflight-20261014/history-before.json'")
s=s.replace("'sandbox/f24-attempt3-f79dd822')","'sandbox/f24-attempt3-f79dd822','sandbox/f24-attempt4-2fbcc7d8')")
s=s.replace('WEB-CONSUMED.json','WEB-CONTEXT-DELIVERED.json').replace('WEB_RESULT_READ','WEB_CONTEXT_DELIVERED').replace('WEB_NOT_CONSUMED','WEB_CONTEXT_NOT_DELIVERED').replace('web_consumed','web_context_delivered').replace('web-consumed-before-crash','web-context-before-crash')
s=s.replace('import base64','import yaml\nfrom f24_gates import catalog, evaluate as evaluate_frozen_gates\nimport base64',1)
s=s.replace('watcher = threading.Thread',"preflight=read(ROOT/'evidence/f24-harness-preflight-20261014/PREFLIGHT.json')\nif not preflight or preflight.get('status')!='PASS':raise RuntimeError('F24_HARNESS_PREFLIGHT_REQUIRED')\nif sha(ROOT/'docs/F24-GATES.json')!=preflight['gates_sha256']:raise RuntimeError('FROZEN_GATES_CHANGED')\nsave('FROZEN-GATES.json',catalog())\nwatcher = threading.Thread",1)
needle="    git('add', '--', 'QWEN.md')"
assert s.count(needle)==1
s=s.replace(needle,"    # New, still-unapproved contract/state reflect the stricter normal plan limits.\n    cp=auto/'RUN-CONTRACT.yaml';contract=yaml.safe_load(cp.read_text(encoding='utf-8-sig'));contract['time_budget_minutes']=45;cp.write_text(yaml.safe_dump(contract,sort_keys=False,allow_unicode=True),encoding='utf-8')\n    state=read(auto/'STATE.json');state['max_cycles']=5;(auto/'STATE.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')\n    ps('. '+q(ROOT/'scripts/state-manager.ps1')+';$state=Get-Content -LiteralPath '+q(auto/'STATE.json')+' -Raw -Encoding UTF8|ConvertFrom-Json; $null=Write-AtomicState -StateObj $state -AutopilotDir '+q(auto)+' -ValidateTransition $false; @{status=\"PASS\"}')\n"+needle,1)
s=s.replace("            assert injection, 'MANDATORY_TEST_FAILED: NATIVE_WORKER_CRASH_GATE_NOT_REACHED'","            if not injection:\n                native_failure=(read(auto/'reports/runner-result.json') or {}).get('reason','NATIVE_WORKER_CRASH_GATE_NOT_REACHED')\n                raise RuntimeError('MANDATORY_TEST_FAILED: '+native_failure+'; controlled crash gate not reached')",1)
needle="report = read(auto / 'reports/runner-result.json') or {}\nresult ="
assert s.count(needle)==1
s=s.replace(needle,"if not failure:\n    try:\n        frozen=evaluate_frozen_gates(project,E,checks,injection,resource_failure);save('FROZEN-GATE-RESULT.json',frozen)\n        if frozen['status']!='PASS':failure='MANDATORY_TEST_FAILED: FROZEN_GATE_'+','.join(k for k,v in frozen['gates'].items() if not v)\n    except Exception as exc:failure='MANDATORY_TEST_FAILED: FROZEN_GATE_EVALUATION '+str(exc)\n"+needle,1)
assert not (root/'tests/test-phase24-attempt5-live.py').exists(),'Never overwrite a prepared harness; this is a one-time source creation record'
(root/'tests/test-phase24-attempt5-live.py').write_text(s,encoding='utf-8')
print('Fresh ATTEMPT5 harness source prepared; no run or consultation created.')
