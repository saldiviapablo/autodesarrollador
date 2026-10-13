"""Strict runner admission and one approval binding contract, plan and frozen policy."""
import argparse,hashlib,json,pathlib,sys,datetime,yaml,jsonschema
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check_path(p):
    p=pathlib.Path(p).absolute()
    for part in [p,*p.parents]:
        if part.exists() and (part.is_symlink() or part.is_junction()):raise ValueError('REPARSE_POINT_DENIED')
    return p.resolve()
def inspect(project):
    p=check_path(project)
    if p==ROOT or p==pathlib.Path(p.anchor) or str(p).startswith('\\\\') or not p.is_dir():raise ValueError('PROJECT_ROOT_DENIED')
    auto=check_path(p/'.autopilot');contract_path=check_path(auto/'RUN-CONTRACT.yaml');plan_path=check_path(auto/'RUN-PLAN.json')
    contract=yaml.safe_load(contract_path.read_text(encoding='utf-8-sig'))
    jsonschema.validate(contract,json.loads((ROOT/'schemas/run-contract.schema.json').read_text(encoding='utf-8-sig')))
    if pathlib.Path(contract['project_root']).resolve()!=p:raise ValueError('CONTRACT_PROJECT_MISMATCH')
    plan=json.loads(plan_path.read_text(encoding='utf-8-sig'))
    jsonschema.validate(plan,json.loads((ROOT/'schemas/runner-plan.schema.json').read_text()))
    if plan.get('backend','live')=='probe' and not p.is_relative_to(ROOT/'sandbox'):raise ValueError('PROBE_ONLY_IN_SANDBOX')
    for name in plan['allowed_files']+[a['path'] for a in plan['artifacts']]+[a['path'] for a in plan.get('immutable_files',[])]:
        relative=pathlib.Path(name)
        if relative.is_absolute() or '..' in relative.parts or name.startswith(('.autopilot','runner/','config/security')):raise ValueError('PLAN_PATH_DENIED')
        check_path(p/relative).relative_to(p)
    if set(c['criterion'] for c in plan['criteria'])!=set(contract['acceptance_criteria']):raise ValueError('CRITERIA_NOT_FULLY_MAPPED')
    commands=plan['tests']+plan.get('builds',[])+plan.get('linters',[])
    ids=[c['id'] for c in commands]
    if len(set(ids))!=len(ids) or not plan['tests']:raise ValueError('TESTS_REQUIRED_OR_DUPLICATE_ID')
    if any(c['test_id'] not in ids for c in plan['criteria']):raise ValueError('CRITERION_CHECK_MISSING')
    frozen=[ROOT/'config/system.yaml',ROOT/'config/security.yaml',ROOT/'config/VERSIONS.lock',ROOT/'scripts/inference-lock.ps1',ROOT/'scripts/hermes-pre-tool-hook.py',ROOT/'schemas/runner-plan.schema.json']
    frozen+=sorted(f for f in (ROOT/'runner').iterdir() if f.suffix in ('.ps1','.py'))
    hashes={str(contract_path):sha(contract_path),str(plan_path):sha(plan_path),**{str(f):sha(f) for f in frozen}}
    digest=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
    receipt=ROOT/'runtime/run-approvals'/(hashlib.sha256(str(p).casefold().encode()).hexdigest()+'-'+contract['run_id']+'.json')
    return {'project':str(p),'auto':str(auto),'contract':contract,'plan':plan,'hashes':hashes,'digest':digest,'receipt_path':str(receipt)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['inspect','approve','validate']);ap.add_argument('--project',required=True);ap.add_argument('--digest');a=ap.parse_args();info=inspect(a.project)
    receipt=check_path(info['receipt_path'])
    if a.action=='approve':
        if a.digest!=info['digest']:raise ValueError('EXPLICIT_APPROVAL_DIGEST_REQUIRED')
        if not info['contract']['authorized']:
            contract_path=pathlib.Path(info['auto'])/'RUN-CONTRACT.yaml'
            data=info['contract'];data['authorized']=True;data['authorized_at']=datetime.datetime.now().astimezone().isoformat()
            contract_path.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True),encoding='utf-8')
            info=inspect(a.project)
        receipt.parent.mkdir(parents=True,exist_ok=True)
        with receipt.open('x',encoding='utf-8') as f:json.dump({'digest':info['digest'],'run_id':info['contract']['run_id'],'approved_at':datetime.datetime.now().astimezone().isoformat()},f)
    elif a.action=='validate':
        if not info['contract']['authorized'] or not receipt.exists() or json.loads(receipt.read_text())['digest']!=info['digest']:raise ValueError('APPROVAL_REQUIRED_OR_CHANGED')
    print(json.dumps({'status':'PASS',**info},ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except Exception as e:print(json.dumps({'status':'DENY','reason':str(e)}));sys.exit(2)
