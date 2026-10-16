"""Consume a real sandbox planner result; certify Prepare without ever Start.

Approval is simulated ONLY for this disposable integration fixture, never a
human decision for a live Worker or for the user's Landing Page project.
"""
import argparse,datetime,hashlib,json,os,pathlib,shutil,subprocess,sys,time
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import project_onboarding as data
import project_launcher_ui as ui
import onboarding_planner as compact

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--receipt',required=True);parser.add_argument('--evidence',required=True);parser.add_argument('--bound');args=parser.parse_args()
    receipt=data.read(args.receipt);p=data.project(receipt['project']);p.relative_to(R/'sandbox')
    assert p.name.startswith('onboarding-long-UX '),'DISPOSABLE_LONG_FIXTURE_ONLY'
    e=data.contract.check_path(args.evidence);e.relative_to(R/'evidence');e.mkdir(exist_ok=False)
    live=data.contract.check_path(receipt['evidence']);live.relative_to(R/'evidence')
    bound_path=data.contract.check_path(args.bound) if args.bound else live/'stdout.json';bound_path.relative_to(R/'evidence')
    bound=data.read(bound_path);assert bound['status']=='PASS' and data.read(live/'RESULT.json')['status']=='PASS'
    data.validate_binding(bound);original=pathlib.Path(receipt['brief']).read_bytes();text=original.decode('utf-8')
    checks={};policy=compact.policy();plan=bound['proposal']['plan'];started=time.monotonic()
    def save(name,value):(e/name).write_text(data.secret.sanitize_text(json.dumps(value,ensure_ascii=False,indent=2))[0],encoding='utf-8')
    def service(payload):
        result=subprocess.run(ui.ps('scripts/project-launcher-action.ps1'),input=json.dumps(payload,ensure_ascii=False).encode('utf-8'),capture_output=True,env=ui.ENV,timeout=160)
        return result,json.loads(result.stdout.decode('utf-8-sig'))
    checks['LONG_OBJECTIVE']=17520<=len(original)<=19000 and text.count('\n')>100 and all(x in text for x in ['UX/UI','€','Stack','Investigación web','Criterios'])
    checks['PLANNER_WITHIN_BUDGET']=bound['planner']['duration']<=policy['timeout_seconds'] and bound['planner']['policy']==policy
    checks['STRUCTURED_PLAN']=compact.validate(bound['proposal'])==bound['proposal'] and bool(bound['proposal']['overview']['research_requirements']) and bool(plan.get('research'))
    checks['PLAN_SIZE_BOUNDED']=bound['planner']['plan_utf8_bytes']<=policy['max_plan_bytes']
    checks['ORIGINAL_OBJECTIVE_PRESERVED']=bound['objective'].encode('utf-8')==original and bound['planner']['objective_sha256']==hashlib.sha256(original).hexdigest()
    checks['ORIGINAL_SOURCE_BEFORE_APPROVAL']=pathlib.Path(bound['planner']['source_path']).read_bytes()==original
    checks['REVIEW_VIEW_COMPLETE']=text in ui.plan_review_text(bound) and bound['proposal']['overview']['objective_summary'] in ui.plan_review_text(bound)
    before=data.snapshot(p);r,denied=service(dict(bound,action='prepare',new_objective=False))
    save('BEFORE-APPROVAL-DENY.json',denied)
    checks['NO_WORKER_BEFORE_APPROVAL']=(r.returncode!=0 and 'HUMAN_PLAN_APPROVAL_REQUIRED' in denied['reason'] and data.snapshot(p)==before=={} and not(p/'.autopilot').exists())
    assert all(checks.values()),checks
    # Test-only approval drives the normal service/RunMutex/Prepare path. This
    # script has no Start call and never claims a human reviewed this fixture.
    r,grant=service(dict(bound,action='approve_plan',decision='APPROVE',method='HUMAN_PLAN_REVIEW'))
    assert r.returncode==0,grant
    r,prepared=service(dict(bound,action='prepare',approval_id=grant['approval_id'],new_objective=False));save('PREPARE.json',prepared)
    assert r.returncode==0,prepared
    actual=data.contract.inspect(p);state=data.read(p/'.autopilot/STATE.json')
    checks['PREPARE']=prepared['status']=='PASS' and actual['plan']==plan and actual['contract']['objective'].encode()==original and actual['contract']['authorized']
    checks['ORIGINAL_OBJECTIVE_PRESERVED'] &= (p/'.autopilot/evidence/ONBOARDING-OBJECTIVE.md').read_bytes()==original
    checks['TESTS_IMMUTABLE']=all(data.contract.sha(p/pin['path'])==pin['sha256'] for pin in plan['immutable_files'])
    checks['NO_RUNNER_OR_WORKER_STARTED']=state['status']=='INITIALIZED' and not(p/'.autopilot/PROCESSES.json').exists()
    for name in ('Local\\DesarrolladorAutonomo_RunMutex','DesarrolladorAutonomo_InferenceMutex'):
        lock=ui.Mutex(name);lock.close()
    checks['CLEANUP']=not(p/'.autopilot/LOCK.json').exists() and ui.birth(bound['planner']['model_pid'])!=bound['planner']['model_start_ticks']
    shutil.copy2(receipt['brief'],e/'SYNTHETIC-OBJECTIVE.md')
    save('OVERVIEW.json',bound['proposal']['overview']);save('RUN-PLAN.json',actual['plan'])
    report={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'project':str(p),'objective_utf8_bytes':len(original),
        'objective_sha256':hashlib.sha256(original).hexdigest(),'plan_utf8_bytes':bound['planner']['plan_utf8_bytes'],'planner_duration_seconds':bound['planner']['duration'],
        'prepare_certification_seconds':time.monotonic()-started,'planner_policy':policy,'approval_source':'SYNTHETIC_DISPOSABLE_INTEGRATION_FIXTURE_ONLY',
        'worker_starts':0,'runner_starts':0,'gui_actions':0,'inferences_in_this_prepare_certificate':0,'real_user_project_used':False}
    save('RESULT.json',report);print(json.dumps(report,ensure_ascii=False),flush=True)
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
