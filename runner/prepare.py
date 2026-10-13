"""Read-only admission followed by the existing initializer; no inference or approval.

All destinations are admitted together. Revalidation narrows, but cannot eliminate,
filesystem TOCTOU without handle-pinned writes by the existing initializer.
"""
import argparse,base64,datetime,json,os,pathlib,subprocess,sys,yaml,jsonschema
import contract

ROOT=contract.ROOT
DESTINATIONS=['QWEN.md','.autopilot','.autopilot/logs','.autopilot/evidence',
    '.autopilot/checkpoints','.autopilot/reports','.autopilot/contract.tmp.json',
    '.autopilot/RUN-CONTRACT.yaml','.autopilot/RUN-CONTRACT.prepare.tmp.yaml',
    '.autopilot/RUN-PLAN.json','.autopilot/RUN-PLAN.prepare.tmp.json',
    '.autopilot/STATE.json','.autopilot/STATE.previous.json','.autopilot/STATE.tmp.json',
    '.autopilot/STATE.md','.autopilot/EVENTS.jsonl','.autopilot/HEARTBEAT.json','.autopilot/LOCK.json']

def admission(request):
    p=contract.project_path(request['project'],allow_missing=True,workspace=request.get('workspace') or None)
    paths=[contract.check_path(p/name) for name in DESTINATIONS]
    for path in paths:path.relative_to(p)
    if (p/'QWEN.md').exists() or (p/'.autopilot').exists():raise ValueError('EXISTING_PREPARE_ARTIFACTS_PRESERVED')
    plan_path=contract.check_path(request['plan'])
    plan=json.loads(plan_path.read_text(encoding='utf-8-sig'))
    criteria=request['criteria'];objective=request['objective']
    draft={'schema_version':'1.0','run_id':'run-pre-admission','project_id':p.name,
        'project_root':str(p),'objective':objective,'acceptance_criteria':criteria,
        'autonomy_mode':'unattended','authorized':False,'authorized_at':None,
        'created_at':datetime.datetime.now().astimezone().isoformat(),'time_budget_minutes':120,
        'allowed_actions':['edit_file','run_test','git_commit_local'],
        'forbidden_actions':['git_push','delete_root','modify_runner_guardrails'],
        'test_commands':[],'build_commands':[],'security_policy_reference':'config/security.yaml'}
    jsonschema.validate(draft,json.loads((ROOT/'schemas/run-contract.schema.json').read_text(encoding='utf-8-sig')))
    contract.validate_plan(p,plan,criteria)
    inputs=[plan_path,ROOT/'config/security.yaml',ROOT/'schemas/run-contract.schema.json',
        ROOT/'schemas/runner-plan.schema.json',ROOT/'schemas/autopilot-state.schema.json',
        ROOT/'templates/QWEN.md.template',ROOT/'scripts/init-autopilot-project.ps1',
        ROOT/'scripts/state-manager.ps1',ROOT/'scripts/windows-process-job.ps1',ROOT/'runner/contract.py',ROOT/'runner/prepare.py',ROOT/'runner/prepare-apply.ps1']
    hashes={str(f):contract.sha(contract.check_path(f)) for f in inputs}
    parents={str(f):(f.stat().st_dev,f.stat().st_ino) for f in [p,*p.parents] if f.exists()}
    return {'project':str(p),'root_existed':p.exists(),'destinations':[str(f) for f in paths],'input_hashes':hashes,'parents':parents,'plan':plan}

def identity(path):
    st=path.lstat()
    return (st.st_dev,st.st_ino,contract.sha(path) if path.is_file() else None)

def cleanup(info):
    """No recursive deletion. Unknown entries are preserved; reparse changes stop cleanup."""
    p=contract.project_path(info['project'],allow_missing=True)
    candidates=[pathlib.Path(s) for s in info['destinations']]
    for path in candidates:contract.check_path(path).relative_to(p)
    owned={path:identity(path) for path in candidates if path.exists()}
    removed=[];preserved=[]
    for path in sorted(owned,key=lambda f:len(f.parts),reverse=True):
        try:
            contract.check_path(path).relative_to(p)
            if identity(path)!=owned[path]:raise ValueError('CHANGED_ARTIFACT_PRESERVED')
            if path.is_dir():path.rmdir()
            else:path.unlink()
            removed.append(str(path.relative_to(p)))
        except Exception as e:preserved.append({'path':str(path),'reason':str(e)})
    if not info['root_existed'] and p.exists():
        try:p.rmdir();removed.append('.')
        except OSError as e:preserved.append({'path':str(p),'reason':str(e)})
    return {'removed':removed,'preserved':preserved,'status':'PASS' if not preserved else 'INCOMPLETE'}

def atomic(path,text):
    temp=path.with_name(path.stem+'.prepare.tmp'+path.suffix)
    with temp.open('x',encoding='utf-8',newline='\n') as f:
        f.write(text);f.flush();os.fsync(f.fileno())
    os.replace(temp,path)

def execute(request, *, initialize=None):
    phase='PREPARE_PRE_ADMISSION';info=None;started=False
    try:
        info=admission(request)
        # Read-only second pass: parent identities and all inputs must still agree.
        if admission(request)!=info:raise ValueError('PREPARE_ADMISSION_CHANGED')
        payload=base64.b64encode(json.dumps({'request':request,'binding':info},ensure_ascii=False).encode()).decode()
        if initialize is None:
            result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-File',str(ROOT/'runner/prepare-apply.ps1'),'-EncodedRequest',payload],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
        else:result=initialize(payload)
        # Child revalidates before touching the initializer and emits an APPLY marker.
        started='PREPARE_APPLY_STARTED' in result.stdout
        if started:phase='PREPARE_APPLY'
        if result.returncode:
            if not started and 'PREPARE_ADMISSION_CHANGED' in result.stdout:raise ValueError('PREPARE_ADMISSION_CHANGED')
            raise ValueError('INITIALIZER_FAILED')
        if not started:raise ValueError('APPLY_MARKER_MISSING')
        p=pathlib.Path(info['project']);auto=p/'.autopilot'
        atomic(auto/'RUN-PLAN.json',json.dumps(info['plan'],ensure_ascii=False,indent=2)+'\n')
        path=auto/'RUN-CONTRACT.yaml';draft=yaml.safe_load(path.read_text(encoding='utf-8-sig'))
        draft['authorized']=False;draft['authorized_at']=None
        atomic(path,yaml.safe_dump(draft,sort_keys=False,allow_unicode=True))
        final=contract.inspect(p)
        return {'status':'PASS','action':'Prepare','phase':phase,'project':str(p),
            'run_id':final['contract']['run_id'],'approval_digest':final['digest'],
            'prepare_write_count':sum(pathlib.Path(s).exists() for s in info['destinations']),
            'pre_admission':'PASS','revalidation':'PASS','cleanup':'NO_AUXILIARY_PROCESSES'}
    except Exception as e:
        # A timeout can interrupt the initializer after its first write.
        if isinstance(e,subprocess.TimeoutExpired):started=True;phase='PREPARE_APPLY'
        recovery=None
        if started and info:
            try:recovery=cleanup(info)
            except Exception as failure:recovery={'status':'INCOMPLETE','reason':str(failure)}
        reason='INVALID_PREPARE_INPUT' if isinstance(e,jsonschema.ValidationError) else ('PREPARE_TIMEOUT' if isinstance(e,subprocess.TimeoutExpired) else str(e))
        return {'status':'FAIL' if started else 'DENY','phase':phase,'reason':reason,
            'prepare_write_count':None if started else 0,'cleanup':recovery or 'NO_WRITES'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--request',required=True);ap.add_argument('--validate-only',action='store_true');a=ap.parse_args()
    payload=json.loads(base64.b64decode(a.request).decode('utf-8'))
    if a.validate_only:
        info=admission(payload['request'])
        # JSON roundtrip turns identity tuples into lists.
        if json.loads(json.dumps(info))!=payload['binding']:raise ValueError('PREPARE_ADMISSION_CHANGED')
        print(json.dumps({'status':'PASS','phase':'PREPARE_PRE_ADMISSION','prepare_write_count':0}));return
    result=execute(payload);print(json.dumps(result,ensure_ascii=False));sys.exit(0 if result['status']=='PASS' else 2)

if __name__=='__main__':
    try:main()
    except Exception as e:print(json.dumps({'status':'DENY','phase':'PREPARE_PRE_ADMISSION','reason':str(e),'prepare_write_count':0}));sys.exit(2)
