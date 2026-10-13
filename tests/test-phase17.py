import importlib.util,json,pathlib,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fixtures',ROOT/'tests/runner-fixtures.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
e=ROOT/'evidence/phase-17';e.mkdir(parents=True,exist_ok=True);results={}
p=f.project('admission');denied=f.start(p,30);assert denied.returncode and 'APPROVAL_REQUIRED' in denied.stdout,denied.stdout
f.approve(p);r=f.start(p,90);(e/'probe.stdout.txt').write_text(r.stdout);(e/'probe.stderr.txt').write_text(r.stderr)
result=json.loads((p/'.autopilot/reports/runner-result.json').read_text(encoding='utf-8-sig'));assert result['technical_status']=='SUCCESS',result
assert result['status']=='STALLED' and result['reason']=='COMPLETION_GATE_NOT_INSTALLED'
assert not(p/'.autopilot/LOCK.json').exists();assert (p/'.autopilot/WATCHDOG.json').exists()
results['T-RUN-001']='PASS';results['T-RUN-005']='PASS';results['T-RUN-008']='PASS'
p_timeout=f.project('timeout',delay=10,phase_timeout=20,global_timeout=2);f.approve(p_timeout);r=f.start(p_timeout,40)
timeout=json.loads((p_timeout/'.autopilot/reports/runner-result.json').read_text(encoding='utf-8-sig'));assert timeout['status']=='FAILED' and timeout['reason']=='GLOBAL_TIMEOUT',timeout
results['T-RUN-006']='PASS';results['T-RUN-007']='PASS'
data={'status':'PARTIAL','tests':results,'probe_label':'lifecycle only; no fake native inference claim','approval_without_receipt':'DENY','completion_gate_not_installed':'STALLED','projects':[str(p),str(p_timeout)],'native_and_cron_tests':'PENDING'}
(e/'lifecycle.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data))
