import importlib.util,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('f',ROOT/'tests/runner-fixtures.py');f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
e=ROOT/'evidence/phase-21';e.mkdir(exist_ok=True)
p=f.project('report21-unit');r=f.powershell('tests/test-phase21-report.ps1','-ProjectRoot',p);assert r.returncode==0,r.stderr
unit=json.loads(r.stdout);cases={}
for name,kwargs in [('timeout',{'delay':30,'global_timeout':2}),('stalled',{}),('gate_denied_probe',{})]:
    p=f.project('report21-'+name,**kwargs)
    if name=='stalled':
        path=p/'.autopilot/STATE.json';state=json.loads(path.read_text(encoding='utf-8-sig'));state['progress']['no_progress_cycles']=3;path.write_text(json.dumps(state))
    f.approve(p);r=f.start(p,60);report=json.loads((p/'.autopilot/reports/runner-result.json').read_text(encoding='utf-8-sig'))
    expected='STALLED' if name=='stalled' else 'FAILED';assert report['status']==expected,(report,r.stderr)
    assert (p/'.autopilot/reports/FINAL.md').exists() and not (p/'.autopilot/LOCK.json').exists()
    cases[name]={'status':'PASS','terminal':expected,'project':str(p),'reason':report['reason']}
p=f.project('report21-unapproved');r=f.powershell('runner/launch.ps1','-ProjectRoot',p,'-Unattended');assert r.returncode==2,r.stderr
assert (p/'.autopilot/reports/BLOCKED.md').exists() and list((p/'.autopilot/checkpoints').iterdir())
result={'status':'PASS','unit':unit,'actual_lifecycle_cases':cases,'unattended_no_prompt_report_checkpoint':'PASS','dependencies_added':[]}
(e/'tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
