import importlib.util,json,pathlib,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('fixtures',ROOT/'tests/runner-fixtures.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
p=f.project('recover17');f.approve(p);first=f.start(p);assert (p/'.autopilot/reports/runner-result.json').exists()
(p/'.autopilot/STATE.json').write_text('{corrupt')
recovered=f.powershell('runner/run.ps1','-ProjectRoot',p,'-Action','Start','-Recover',timeout=80)
state=json.loads((p/'.autopilot/STATE.json').read_text(encoding='utf-8-sig'));assert state['status']=='STALLED',recovered.stderr
events=(p/'.autopilot/EVENTS.jsonl').read_text(encoding='utf-8-sig');assert 'RUN_RECOVERED_FROM_DISK' in events
external=subprocess.Popen(['C:/Python314/python.exe','-m','http.server','8080','--bind','127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    time.sleep(.4);assert external.poll() is None
    target=f.project('external17',backend='live',phase_timeout=5,global_timeout=15);f.approve(target);denied=f.start(target,40)
    result=json.loads((target/'.autopilot/reports/runner-result.json').read_text(encoding='utf-8-sig'))
    assert result['status']=='BLOCKED_REQUIRES_HUMAN' and result['reason']=='EXTERNAL_MODEL_NOT_COMPATIBLE',result
    assert external.poll() is None,'Runner killed a preexisting external process'
finally:external.terminate();external.wait(timeout=10)
report={'status':'PASS','recover_corrupted_state_from_disk':True,'unknown_listener_denied':True,'external_process_preserved':True,'projects':[str(p),str(target)]}
(ROOT/'evidence/phase-17/recovery-external.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
