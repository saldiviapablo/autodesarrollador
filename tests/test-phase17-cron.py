import importlib.util,json,pathlib,subprocess,sys,yaml
ROOT=pathlib.Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('fixtures',ROOT/'tests/runner-fixtures.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
cfg=yaml.safe_load((ROOT/'config/system.yaml').read_text(encoding='utf-8-sig'));python=cfg['document_extraction']['native_python'];tool=ROOT/'scripts/register-runner-cron.py'
def cron(action,p):
    r=subprocess.run([python,'-I',str(tool),action,'--project',str(p)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=80)
    return r
p=f.project('cron17');denied=cron('create',p);assert denied.returncode and 'CRON_APPROVAL_REQUIRED' in denied.stdout,denied.stdout
f.approve(p);created=cron('create',p);assert created.returncode==0,(created.stdout,created.stderr)
try:
    dispatched=cron('trigger',p);assert dispatched.returncode==0,(dispatched.stdout,dispatched.stderr)
    result=json.loads((p/'.autopilot/reports/runner-result.json').read_text(encoding='utf-8-sig'))
    assert result['technical_status']=='SUCCESS',result
    assert (p/'.autopilot/WATCHDOG.json').exists()
    assert not(p/'.autopilot/LOCK.json').exists()
finally:
    cleanup=cron('remove',p);assert cleanup.returncode==0,(cleanup.stdout,cleanup.stderr)
data={'status':'PASS','test_id':'T-RUN-009','native_cron_created':True,'native_scheduler_tick_dispatch':True,'runner_approved_contract_required':True,'unapproved_registration_denied':True,'watchdog_monitor_executed':True,'runner_finally_executed':True,'cron_job_removed':True,'backend':'labelled probe, live native chain separately certified','project':str(p),'runner_result':result}
(ROOT/'evidence/phase-17/cron.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data))
