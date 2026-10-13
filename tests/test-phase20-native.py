"""Actual live chain through the authoritative F20 gate; never a probe."""
import importlib.util,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('fixtures',ROOT/'tests/runner-fixtures.py');f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
p=f.project('completion20-native',backend='live',phase_timeout=180,global_timeout=650);f.approve(p)
r=f.start(p,720);e=ROOT/'evidence/phase-20'
(e/'native.stdout.txt').write_text(r.stdout,encoding='utf-8');(e/'native.stderr.txt').write_text(r.stderr,encoding='utf-8')
report=json.loads((p/'.autopilot/reports/runner-result.json').read_text(encoding='utf-8-sig'))
gate=json.loads((p/'.autopilot/evidence/completion-gate.json').read_text(encoding='utf-8-sig'))
assert r.returncode==0 and report['status']=='COMPLETED' and all(gate['checks'].values()),(report,r.stderr)
assert not (p/'.autopilot/LOCK.json').exists()
result={'status':'PASS','actual_native_chain':True,'gate':gate,'report':report,'project':str(p)}
(e/'native.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
