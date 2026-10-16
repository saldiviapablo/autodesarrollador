"""Final read-only integrity/ownership audit for the post-v1 launcher change."""
import datetime,hashlib,json,pathlib,socket,subprocess,sys,time
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import project_launcher_ui as ui
import project_onboarding as data
E=R/'evidence'/('launcher-integrity-'+time.strftime('%Y%m%d-%H%M%S'));E.mkdir()
checks={};details={};start=time.monotonic()
def sha(path):
    h=hashlib.sha256()
    with pathlib.Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
lease=ui.Mutex('Local\\DesarrolladorAutonomo_RunMutex')
try:
    inference=ui.Mutex('DesarrolladorAutonomo_InferenceMutex');inference.close();checks['physical_inference_mutex_free']=True
    frozen=['config/system.yaml','config/security.yaml','config/VERSIONS.lock','runner/run.ps1','runner/core.ps1','runner/prepare.py','runner/prepare-apply.ps1','runner/contract.py','runner/cleanup.ps1','runner/completion.py','runner/watchdog-monitor.ps1','scripts/inference-lock.ps1','scripts/hermes-pre-tool-hook.py','scripts/security-guard.ps1','scripts/invoke-hermes.ps1','scripts/invoke-hermes-role.ps1','scripts/invoke-qwen-code.ps1','scripts/invoke-delegation.ps1','tools']
    diff=subprocess.run(['git','diff','--exit-code','--',*frozen],cwd=R,capture_output=True,timeout=30)
    checks['frozen_runtime_and_guards_unchanged']=diff.returncode==0
    cfg=data.contract.yaml.safe_load((R/'config/system.yaml').read_text(encoding='utf-8-sig'))
    protected={cfg['llama']['executable']:'c741d245d827a0a3d3896f5f9b0039b3bb282dc9fc9840aa7cd7d072ddd86a39',
        cfg['llama']['model']:'671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7',
        str(R/'scripts/hermes-pre-tool-hook.py'):'49a28be99803169841c82b99e48573d966fe26e5a348228417cc94ad46a7573c',
        str(R/'scripts/mcp-sandbox-server.py'):'ab4c23e4c68dde352c63fbac9bef53dbdb747a411d52fb949d996413b20807c3',
        str(R/'config/plugins/desarrollador-autonomo-health/__init__.py'):'88516ba97a93fdc30a4eda9dfa72f3316d8e586ea2f664c5827ac10885de011e',
        str(pathlib.Path(cfg['hermes']['profile_dir'])/'plugins/desarrollador-autonomo-health/__init__.py'):'88516ba97a93fdc30a4eda9dfa72f3316d8e586ea2f664c5827ac10885de011e'}
    details['protected']={p:{'expected':expected,'actual':sha(p)} for p,expected in protected.items()}
    checks['six_protected_components']=all(v['actual']==v['expected'] for v in details['protected'].values())
    original=data.read(R/'evidence/final-global-audit-20261015-184713/HISTORICAL-MANIFEST.json')
    changed=[n for n,expected in original.items() if sha(R/n)!=expected]
    checks['v1_historical_evidence_unchanged']=not changed;details['historical_files']=len(original);details['historical_changes']=changed
    checks['frozen_model_configuration']=(cfg['llama']['alias'],cfg['llama']['host'],cfg['llama']['ctx_size'],cfg['llama']['parallel'])==('qwen36','127.0.0.1',65536,1)
    checks['ports_free']=True
    for port in [8080,9119]:
        with socket.socket() as sock:
            sock.settimeout(.5)
            if sock.connect_ex(('127.0.0.1',port))==0:checks['ports_free']=False
    survivors=[]
    for f in (R/'evidence/launcher-directed-20261015-224046').glob('*.process.json'):
        owner=data.read(f)['owned_identity']
        if ui.birth(owner['pid'])==owner['start_ticks']:survivors.append(owner)
    checks['directed_test_processes_exited']=not survivors;details['survivors']=survivors
    installation=data.read(R/'config/INSTALLATION-STATE.json')['validation_8']
    f24=data.read(R/'evidence/phase-24-attempt-11-20261015/SUMMARY.json')
    checks['v1_phases_still_pass']=(f24['status']=='PASS' and installation['f24_completion_gate']=='COMPLETED'
        and installation['f24_integrity']=='PASS' and all(installation.get(k)=='PASS' for k in ['f25','4h','f26','f27']))
finally:lease.close()
checks['physical_run_mutex_released']=True
report={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'details':details,'duration_seconds':time.monotonic()-start,
        'gui_control_actions':0,'inferences':0,'new_dependencies':[],'final_manual_smoke':'PENDING'}
(E/'RESULT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':checks,'evidence':str(E),'duration_seconds':report['duration_seconds']},ensure_ascii=False),flush=True)
raise SystemExit(0 if report['status']=='PASS' else 1)
