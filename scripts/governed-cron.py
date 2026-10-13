"""Native no-agent cron admission; only fixed hashed catalog jobs, isolated project home."""
import argparse,hashlib,json,os,pathlib,shutil,sys
from ruamel.yaml import YAML
import jsonschema
ROOT=pathlib.Path(__file__).resolve().parents[1]
yaml=YAML(typ='safe')
def prepare(project):
    p=pathlib.Path(project).absolute()
    for part in [p,*p.parents]:
        if part.exists() and (part.is_symlink() or part.is_junction()):raise ValueError('REPARSE_POINT_DENIED')
    p=p.resolve();p.relative_to(ROOT/'sandbox')
    auto=p/'.autopilot'
    if auto.is_junction() or auto.is_symlink():raise ValueError('REPARSE_POINT_DENIED')
    contract=yaml.load((auto/'RUN-CONTRACT.yaml').read_text(encoding='utf-8-sig'))
    jsonschema.validate(contract,json.loads((ROOT/'schemas/run-contract.schema.json').read_text(encoding='utf-8-sig')))
    if not contract['authorized'] or pathlib.Path(contract['project_root']).resolve()!=p or 'run_test' not in contract['allowed_actions']:raise ValueError('CONTRACT_DENIED')
    home=auto/'hermes-cron'
    for f in (home,home/'scripts'):
        if f.is_symlink() or f.is_junction():raise ValueError('REPARSE_POINT_DENIED')
    home.mkdir(exist_ok=True);(home/'scripts').mkdir(exist_ok=True)
    (home/'config.yaml').write_bytes((ROOT/'config/hermes-reviewer/config.yaml').read_bytes())
    os.environ.update(HERMES_HOME=str(home),HERMES_DISABLE_LAZY_INSTALLS='1',HERMES_CRON_SCRIPT_TIMEOUT='5',PYTHONDONTWRITEBYTECODE='1')
    cfg=yaml.load((ROOT/'config/system.yaml').read_text(encoding='utf-8-sig'))
    sys.path.insert(0,cfg['document_extraction']['native_source_dir'])
    return p,home
def operation(action,project,catalog_id=None,job_id=None):
    p,home=prepare(project)
    from tools.cronjob_tools import cronjob
    from cron.jobs import get_job,list_jobs
    from cron.scheduler import run_job
    catalog=json.loads((ROOT/'config/cron-catalog.json').read_text(encoding='utf-8-sig'))
    registry=home/'admitted-jobs.json';owned=json.loads(registry.read_text()) if registry.exists() else {}
    if action=='create':
        entry=catalog.get(catalog_id)
        if not entry or not entry.get('no_agent'):raise ValueError('CATALOG_DENIED')
        script=ROOT/entry['script'];script.resolve().relative_to(ROOT/'scripts/jobs')
        if hashlib.sha256(script.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('SCRIPT_HASH_DENIED')
        target=home/'scripts'/script.name
        if target.is_symlink() or target.is_junction():raise ValueError('REPARSE_POINT_DENIED')
        shutil.copyfile(script,target)
        result=json.loads(cronjob(action='create',name='da-'+catalog_id,schedule='24h',repeat=1,deliver='local',script=script.name,no_agent=True,workdir=str(p)))
        if not result.get('success'):raise ValueError(str(result))
        job_id=result['job']['job_id'];owned[job_id]=catalog_id
    elif action=='list':
        result={'success':True,'jobs':[j for j in list_jobs(include_disabled=True) if j['id'] in owned]}
    else:
        if job_id not in owned:raise ValueError('UNOWNED_JOB_DENIED')
        job=get_job(job_id);entry=catalog[owned[job_id]]
        expected=pathlib.Path(entry['script']).name
        if not job or not job.get('no_agent') or job.get('script')!=expected or pathlib.Path(job['workdir']).resolve()!=p:raise ValueError('JOB_POLICY_DENIED')
        script=home/'scripts'/expected
        if script.is_symlink() or hashlib.sha256(script.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('SCRIPT_HASH_DENIED')
        if action=='run':
            ok,doc,response,error=run_job(job)
            result={'success':ok,'output':response,'error':error,'local_inferences':0}
        else:
            result=json.loads(cronjob(action=action,job_id=job_id))
            if action=='remove' and result.get('success'):owned.pop(job_id)
    registry.write_text(json.dumps(owned,indent=2)+'\n')
    return result
def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['create','list','pause','resume','remove','run']);ap.add_argument('--project',required=True);ap.add_argument('--catalog-id');ap.add_argument('--job-id');a=ap.parse_args()
    print(json.dumps(operation(a.action,a.project,a.catalog_id,a.job_id),ensure_ascii=False))
if __name__=='__main__':
    sys.dont_write_bytecode=True
    sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
    try:main()
    except Exception as e:print(json.dumps({'success':False,'decision':'DENY','reason':str(e)}));sys.exit(1)
