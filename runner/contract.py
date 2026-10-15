"""Strict runner admission and one approval binding contract, plan and frozen policy."""
import argparse,hashlib,json,pathlib,sys,datetime,yaml,jsonschema
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from canonical_path import resolve_path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check_path(p):
    return pathlib.Path(resolve_path(p,reject_reparse=True,reject_traversal=True)['physical'])

def project_path(project, *, allow_missing=False, workspace=None):
    if not pathlib.Path(project).is_absolute():raise ValueError('ABSOLUTE_PROJECT_ROOT_REQUIRED')
    p=check_path(project)
    if p==ROOT or p==pathlib.Path(p.anchor) or p.drive.startswith('\\\\'):raise ValueError('PROJECT_ROOT_DENIED')
    if workspace is not None and not p.is_relative_to(check_path(workspace)):raise ValueError('PATH_BOUNDARY_VIOLATION')
    policy=yaml.safe_load((ROOT/'config/security.yaml').read_text(encoding='utf-8-sig'))
    for protected in policy['protected_paths']:
        if p.is_relative_to(check_path(protected)):raise ValueError('PROTECTED_PROJECT_ROOT_DENIED')
    if not p.is_dir() and not (allow_missing and not p.exists() and p.parent.is_dir()):raise ValueError('PROJECT_ROOT_DENIED')
    return p

def validate_plan(p,plan,criteria):
    jsonschema.validate(plan,json.loads((ROOT/'schemas/runner-plan.schema.json').read_text(encoding='utf-8-sig')))
    if plan.get('backend','live')=='probe' and not p.is_relative_to(ROOT/'sandbox'):raise ValueError('PROBE_ONLY_IN_SANDBOX')
    if plan.get('sandbox_crash_boundary') and not p.is_relative_to(ROOT/'sandbox'):raise ValueError('CRASH_BOUNDARY_ONLY_IN_SANDBOX')
    for name in plan['allowed_files']+[a['path'] for a in plan['artifacts']]+[a['path'] for a in plan.get('immutable_files',[])]:
        relative=pathlib.Path(name)
        if relative.is_absolute() or relative.drive or '..' in relative.parts or name.startswith(('.autopilot','runner/','config/security')):raise ValueError('PLAN_PATH_DENIED')
        check_path(p/relative).relative_to(p)
    if set(c['criterion'] for c in plan['criteria'])!=set(criteria):raise ValueError('CRITERIA_NOT_FULLY_MAPPED')
    commands=plan['tests']+plan.get('builds',[])+plan.get('linters',[])
    ids=[c['id'] for c in commands]
    if len(set(ids))!=len(ids) or not plan['tests']:raise ValueError('TESTS_REQUIRED_OR_DUPLICATE_ID')
    if any(c['test_id'] not in ids for c in plan['criteria']):raise ValueError('CRITERION_CHECK_MISSING')
def inspect(project):
    p=project_path(project)
    auto=check_path(p/'.autopilot');contract_path=check_path(auto/'RUN-CONTRACT.yaml');plan_path=check_path(auto/'RUN-PLAN.json')
    contract=yaml.safe_load(contract_path.read_text(encoding='utf-8-sig'))
    jsonschema.validate(contract,json.loads((ROOT/'schemas/run-contract.schema.json').read_text(encoding='utf-8-sig')))
    if check_path(contract['project_root'])!=p:raise ValueError('CONTRACT_PROJECT_MISMATCH')
    plan=json.loads(plan_path.read_text(encoding='utf-8-sig'))
    validate_plan(p,plan,contract['acceptance_criteria'])
    frozen=[ROOT/'config/system.yaml',ROOT/'config/security.yaml',ROOT/'config/VERSIONS.lock',ROOT/'scripts/inference-lock.ps1',ROOT/'scripts/hermes-pre-tool-hook.py',ROOT/'schemas/runner-plan.schema.json']
    frozen+=[ROOT/'scripts/canonical_path.py',ROOT/'scripts/security-guard.ps1',ROOT/'scripts/hermes-mcp-plugin-guard.ps1']
    frozen+=[ROOT/'scripts/invoke-qwen-code.ps1',ROOT/'scripts/invoke-delegation.ps1',ROOT/'scripts/invoke-hermes-role.ps1',ROOT/'scripts/invoke-hermes.ps1']
    frozen+=[ROOT/'docs/F24-GATES.json',ROOT/'tests/f24_gates.py',ROOT/'tests/test-phase24-attempt5-live.py',ROOT/'tests/f24_attempt3_fixture.py',ROOT/'tests/windows_launcher_adapter.py',ROOT/'tests/finalize-live-test.ps1']
    frozen+=[ROOT/'tools/chatgpt-bridge.js',ROOT/'tools/chatgpt-ledger.js',ROOT/'tools/chatgpt-delivery.js',ROOT/'tools/chatgpt-send-actuator.js',ROOT/'tools/chatgpt-fresh-chat.js',ROOT/'scripts/consultar-chatgpt.ps1',ROOT/'scripts/wait-chatgpt-child.ps1',ROOT/'tests/test-phase24-attempt6-live.py']
    frozen+=[ROOT/'tools/chatgpt-pre-send.js']
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
