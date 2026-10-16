"""Directed post-v1 regression only: no GUI, Qwen inference or prior E2E phase.

Uses the certified owned-job test wrapper and relocates historical test outputs.
"""
import argparse,base64,datetime,json,os,pathlib,subprocess,sys,time
R=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
import project_launcher_ui as ui
PY='C:/Python314/python.exe'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--evidence',required=True);args=parser.parse_args()
    E=pathlib.Path(args.evidence).resolve();E.relative_to(R/'evidence');E.mkdir(exist_ok=False)
    birth=ui.birth(os.getpid());before={p.resolve() for p in (R/'sandbox').iterdir() if p.is_dir()}
    env=dict(ui.ENV,F24_PREFLIGHT_E=str(E/'deterministic'),LAUNCHER_FLOW_E=str(E/'flow'))
    results={}
    def run(name,argv,timeout=180):
        payload=base64.b64encode(json.dumps({'evidence':str(E),'name':name,'argv':list(map(str,argv)),
            'timeout':timeout,'controller_pid':os.getpid(),'controller_birth_ticks':birth}).encode()).decode()
        start=time.monotonic()
        p=subprocess.run(ui.ps('tests/run-owned-audit-gate.ps1','-PayloadBase64',payload),cwd=R,env=env,capture_output=True,timeout=timeout+60)
        (E/(name+'.wrapper.stdout.txt')).write_bytes(p.stdout);(E/(name+'.wrapper.stderr.txt')).write_bytes(p.stderr)
        receipt=json.loads((E/(name+'.process.json')).read_text(encoding='utf-8-sig'))
        results[name]={'status':'PASS' if p.returncode==0 and receipt['status']=='PASS' and receipt['owned_job_closed'] and receipt['owned_process_exited'] else 'FAIL',
                       'duration_seconds':time.monotonic()-start,'process':receipt}
        (E/'PROGRESS.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        print(json.dumps({name:results[name]['status']}),flush=True)
        if results[name]['status']!='PASS':raise ValueError(name+' failed; inspect preserved raw outputs')
    def relocated(name,directory=None,timeout=180):
        argv=[PY,'-B',R/'tests/relocate-audit-test.py','--test',name,'--output',E/('relocated-'+name)]
        if directory:argv+=['--directory',directory]
        run(name,argv,timeout)
    # Wait once for any owned preflight to finish; never contend with inference.
    mutex=ui.K.CreateMutexW(None,False,'Local\\DesarrolladorAutonomo_RunMutex')
    code=ui.K.WaitForSingleObject(mutex,300000)
    if code not in (0,0x80):raise ValueError('ACTIVE_RUN_NOT_INTERRUPTED_REGRESSION_NOT_STARTED')
    ui.K.ReleaseMutex(mutex);ui.K.CloseHandle(mutex)
    try:
        run('launcher-flow',[PY,'-B',R/'tests/test-project-launcher-flow.py'])
        run('canonical-prepare-one-affected-case',[PY,'-B',R/'tests/test-project-onboarding.py','Checks.test_canonical_prepare_isolation_history'])
        relocated('test-phase23-prepare-boundary.py','evidence/phase-23-attempt-3',90)
        relocated('test-phase18-controls.py','evidence/phase-18',150)
        run('completion-gate',[PY,'-B',R/'tests/test-phase20.py'],90)
        run('cleanup-and-recovery',[PY,'-B',R/'tests/test-phase22.py'],180)
        run('inference-lock',ui.ps('tests/test-inference-lock.ps1','-EvidenceDir',E/'lock','-LogFile',E/'lock.log.txt'),180)
        run('batch-argument-transport',[PY,'-B',R/'tests/test-windows-launcher-adapter.py'],60)
        run('domain-lock',['node.exe',R/'tests/test-chatgpt-domain-lock.js'],60)
    finally:
        # Only fresh, explicitly labelled fixture roots emitted by these suites.
        candidates=[]
        for name in ['completion-gate.stdout.txt','test-phase18-controls.py.stdout.txt','cleanup-and-recovery.stdout.txt']:
            f=E/name
            if not f.exists():continue
            for line in f.read_text(encoding='utf-8-sig',errors='replace').splitlines():
                try:entry=json.loads(line)
                except ValueError:continue
                def collect(v):
                    if isinstance(v,dict):
                        for k,x in v.items():
                            if k=='project' and isinstance(x,str):candidates.append(pathlib.Path(x))
                            elif k=='projects' and isinstance(x,list):candidates.extend(pathlib.Path(y) for y in x if isinstance(y,str))
                            else:collect(x)
                    elif isinstance(v,list):
                        for x in v:collect(x)
                collect(entry)
        cleaned=[]
        for project in sorted(set(candidates)):
            p=project.resolve();p.relative_to(R/'sandbox')
            if p in before:raise ValueError('HISTORICAL_FIXTURE_CLEANUP_DENIED')
            lock=p/'.autopilot/LOCK.json'
            if not lock.exists():continue
            state=json.loads((p/'.autopilot/STATE.json').read_text(encoding='utf-8-sig'))
            assert p.name.startswith('7b-') and state['objective']=='Implement correct addition with verified tests'
            quote=lambda x:"'"+str(x).replace("'","''")+"'"
            script=("$env:PSModulePath=Join-Path $PSHOME 'Modules';. "+quote(R/'runner/core.ps1')+";. "+quote(R/'runner/cleanup.ps1')+
                ";$a="+quote(p/'.autopilot')+";$s=Get-Content -LiteralPath (Join-Path $a 'STATE.json') -Raw -Encoding UTF8|ConvertFrom-Json;"+
                "$l=Get-Content -LiteralPath (Join-Path $a 'LOCK.json') -Raw -Encoding UTF8|ConvertFrom-Json;"+
                "if($l.run_id -ne $s.run_id -or @(Get-RunnerSurvivors $a).Count){throw 'FIXTURE_OWNERSHIP_INVALID'};"+
                "$owner=Get-Process -Id $l.owner_pid -ErrorAction SilentlyContinue;if($owner -and $owner.StartTime.ToUniversalTime() -le ([datetimeoffset]$l.started_at).UtcDateTime.AddSeconds(1)){throw 'INITIALIZER_STILL_ALIVE'};"+
                "$s.status='ABORTED';$s.current_task='Terminal directed-test fixture cleanup';$null=Write-AtomicState -StateObj $s -AutopilotDir $a;"+
                "$null=Update-AutopilotHeartbeat -AutopilotDir $a -RunId $s.run_id -ProcessId $PID -Status 'ABORTED' -CurrentTask 'fixture cleanup';Remove-RunnerOwnedLock $a $s.run_id $l.owner_pid;'FIXTURE_CLEANUP_PASS'")
            r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(script.encode('utf-16le')).decode()],cwd=R,env=env,capture_output=True,timeout=40)
            assert r.returncode==0,r.stderr.decode(errors='replace');cleaned.append(str(p))
        (E/'FIXTURE-CLEANUP.json').write_text(json.dumps({'status':'PASS','roots':cleaned,'historical_roots_touched':False},indent=2),encoding='utf-8')
    report={'status':'PASS' if results and all(v['status']=='PASS' for v in results.values()) else 'FAIL','suites':results,
            'inferences':0,'gui_control_actions':0,'prior_E2E_phases_repeated':[],'pushes':0}
    (E/'RESULT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'status':report['status'],'evidence':str(E),'suites':len(results)}),flush=True)
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
