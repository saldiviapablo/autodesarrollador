import importlib.util,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('f',ROOT/'tests/runner-fixtures.py');f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
p=f.project('prestart-cleanup-final');assert (p/'.autopilot/LOCK.json').exists()
r=f.powershell('runner/launch.ps1','-ProjectRoot',p,'-Unattended');assert r.returncode==2,r.stderr
report=json.loads((p/'.autopilot/reports/runner-result.json').read_text(encoding='utf-8-sig'))
assert report['status']=='BLOCKED_REQUIRES_HUMAN' and report['technical_status']=='NOT_STARTED' and report['cleanup']['run_lock_removed']
assert not(p/'.autopilot/LOCK.json').exists() and not(p/'.autopilot/PROCESSES.json').exists()
assert (p/'.autopilot/reports/BLOCKED.md').exists() and list((p/'.autopilot/checkpoints').iterdir())
result={'status':'PASS','initializer_metadata_retired_under_physical_mutex':True,'no_worker_started':True,'blocked_checkpoint_report_and_cleanup':'PASS','project':str(p)}
(ROOT/'evidence/regression-7b-final/prestart-block.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
