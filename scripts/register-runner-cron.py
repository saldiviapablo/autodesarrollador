"""Explicit native Cron dispatcher; frozen one-shot approval remains mandatory in child Runner."""
import argparse,hashlib,json,os,pathlib,subprocess,sys
from ruamel.yaml import YAML
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['create','trigger','remove']);ap.add_argument('--project',required=True);a=ap.parse_args()
    p=pathlib.Path(a.project).resolve();home=p/'.autopilot/hermes-runner-cron'
    from_cfg=YAML(typ='safe').load((ROOT/'config/system.yaml').read_text(encoding='utf-8-sig'))
    sys.path.insert(0,from_cfg['document_extraction']['native_source_dir']);os.environ.update(HERMES_HOME=str(home),HERMES_DISABLE_LAZY_INSTALLS='1')
    from cron.jobs import create_job,trigger_job,remove_job,get_due_jobs
    from cron.scheduler import tick
    registry=home/'runner-job.json'
    if a.action=='create':
        admission=subprocess.run(['C:/Python314/python.exe',str(ROOT/'runner/contract.py'),'validate','--project',str(p)],capture_output=True,text=True,timeout=20)
        if admission.returncode:raise ValueError('CRON_APPROVAL_REQUIRED')
        for x in [home,home/'scripts']:
            if x.is_symlink() or x.is_junction():raise ValueError('CRON_REPARSE_DENIED')
            x.mkdir(parents=True,exist_ok=True)
        (home/'config.yaml').write_bytes((ROOT/'config/hermes-reviewer/config.yaml').read_bytes())
        command=['powershell.exe','-NoProfile','-NonInteractive','-File',str(ROOT/'runner/run.ps1'),'-ProjectRoot',str(p),'-Action','Start']
        shim=home/'scripts/dispatch-runner.py'
        shim.write_text('import subprocess,sys\nr=subprocess.run('+repr(command)+',capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=28800)\nprint(r.stdout)\nprint(r.stderr,file=sys.stderr)\nsys.exit(r.returncode)\n',encoding='utf-8')
        job=create_job(prompt=None,schedule='1m',name='da-approved-runner',no_agent=True,script=shim.name,workdir=str(p),repeat=1,deliver='local')
        registry.write_text(json.dumps({'job_id':job['id'],'shim_sha256':hashlib.sha256(shim.read_bytes()).hexdigest(),'project':str(p)},indent=2))
        print(json.dumps({'status':'PASS','job_id':job['id'],'no_agent_dispatcher':True}));return
    record=json.loads(registry.read_text());shim=home/'scripts/dispatch-runner.py'
    if record['project']!=str(p) or hashlib.sha256(shim.read_bytes()).hexdigest()!=record['shim_sha256']:raise ValueError('CRON_DISPATCHER_INTEGRITY_DENIED')
    if a.action=='trigger':
        trigger_job(record['job_id']);assert any(j['id']==record['job_id'] for j in get_due_jobs())
        fired=tick(verbose=False,sync=True);print(json.dumps({'status':'DISPATCHED','scheduler_tick':fired,'project':str(p)}))
    else:
        removed=remove_job(record['job_id']);registry.unlink();print(json.dumps({'status':'PASS','removed':bool(removed)}))
if __name__=='__main__':
    sys.dont_write_bytecode=True
    try:main()
    except Exception as e:print(json.dumps({'status':'DENY','reason':str(e)}));sys.exit(2)
