"""One actual read-only Hermes plan. No GUI, Prepare, approval, Worker or send."""
import argparse,datetime,json,os,pathlib,subprocess,sys,time
R=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
import project_onboarding as data

def main():
    a=argparse.ArgumentParser();a.add_argument('--project',required=True);a.add_argument('--brief',required=True);a.add_argument('--evidence',required=True);args=a.parse_args()
    p=data.project(args.project);assert p.is_relative_to(R/'sandbox'),'SANDBOX_ONLY'
    E=data.contract.check_path(args.evidence);E.relative_to(R/'evidence');E.mkdir(parents=True,exist_ok=False)
    objective=data.main({'action':'brief','path':args.brief})['text'];before=data.snapshot(p)
    env=dict(os.environ,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',PSModulePath='C:/Windows/System32/WindowsPowerShell/v1.0/Modules')
    start=time.monotonic()
    child=subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-File',str(R/'runner/plan-objective.ps1')],cwd=R,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (E/'PROCESS.json').write_text(json.dumps({'pid':child.pid,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kind':'READ_ONLY_PREFLIGHT_NOT_RUNNER_START','project':str(p),'timeout_seconds':390},indent=2),encoding='utf-8')
    try:out,err=child.communicate(json.dumps({'project':str(p),'objective':objective},ensure_ascii=False).encode('utf-8'),timeout=390)
    except subprocess.TimeoutExpired:
        child.kill();out,err=child.communicate(timeout=15)
    out=out.decode('utf-8-sig',errors='replace');err=err.decode('utf-8-sig',errors='replace')
    (E/'stdout.json').write_text(data.secret.sanitize_text(out)[0],encoding='utf-8')
    (E/'stderr.txt').write_text(data.secret.sanitize_text(err)[0],encoding='utf-8')
    result={'status':'FAIL','exit_code':child.returncode,'duration_seconds':time.monotonic()-start,'project_unchanged':before==data.snapshot(p),'worker_starts':0,'approval_actions':0,'bridge_actions':0}
    try:
        bound=json.loads(out)
        assert child.returncode==0 and bound['status']=='PASS',bound
        data.validate_binding(bound)
        assert bound['planner']['readonly'] is True and bound['planner']['tools']==0
        assert bound['planner']['hook']=='PASS' and bound['planner']['project_snapshot_unchanged'] is True
        assert result['project_unchanged'] and not (p/'.autopilot').exists()
        result.update(status='PASS',planner=bound['planner'],binding=bound['binding'])
        # Cache is a scoped, unapproved draft. It is reusable only after a fresh
        # snapshot and complete policy binding validation, never an approval.
        data.cache_draft(bound)
    except Exception as exc:result['reason']=data.secret.sanitize_text(str(exc))[0]
    (E/'RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(result,evidence=str(E)),ensure_ascii=False),flush=True)
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
