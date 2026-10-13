"""Real Prepare boundary cases and reusable negative filesystem assertion."""
import base64,hashlib,json,os,pathlib,subprocess,sys,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runner'))
import prepare,contract
E=ROOT/'evidence/phase-23-attempt-2';E.mkdir(exist_ok=True)
case=ROOT/'sandbox'/('prepare-admission-'+uuid.uuid4().hex[:8]);case.mkdir()
plan=case/'plan.json'
plan.write_text(json.dumps({'schema_version':'1.0','task':'Verify the harmless fixture','backend':'probe',
    'allowed_files':['app.py'],'tests':[{'id':'unit','argv':['python','test_app.py'],'marker':'UNIT_PASS'}],
    'no_build_reason':'Admission fixture','criteria':[{'criterion':'addition verified','test_id':'unit'}],
    'artifacts':[{'path':'app.py'}]}),encoding='utf-8')
results={};checks={};junctions=[]

def snapshot(root):
    rows={}
    for current,dirs,files in os.walk(root,followlinks=False):
        for name in dirs[:]:
            p=pathlib.Path(current)/name
            rows[str(p.relative_to(root))]='REPARSE' if p.is_symlink() or p.is_junction() else 'DIR'
            if p.is_symlink() or p.is_junction():dirs.remove(name)
        for name in files:
            p=pathlib.Path(current)/name
            rows[str(p.relative_to(root))]='LINK' if p.is_symlink() else hashlib.sha256(p.read_bytes()).hexdigest()
    return rows

def negative_assertion(before,after,response,exit_code):
    return exit_code!=0 and response['status']=='DENY' and response['phase']=='PREPARE_PRE_ADMISSION' and response['prepare_write_count']==0 and before==after

def invoke(p,*,workspace=None,source=plan,allowed=False):
    argv=['powershell.exe','-NoProfile','-NonInteractive','-File',str(ROOT/'runner/run.ps1'),'-ProjectRoot',str(p),'-Action','Prepare','-Objective','Verify admission boundary','-AcceptanceCriteria','addition verified','-PlanPath',str(source)]
    if workspace:argv+=['-WorkspaceRoot',str(workspace)]
    before=snapshot(case)
    r=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=100)
    response=json.loads(r.stdout)
    success=(r.returncode==0 and response['status']=='PASS') if allowed else negative_assertion(before,snapshot(case),response,r.returncode)
    return {'status':'PASS' if success else 'FAIL','response':response,'exit_code':r.returncode,'stderr':r.stderr}

def junction(path,target):
    quote=lambda s:"'"+str(s).replace("'","''")+"'"
    r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command','New-Item -ItemType Junction -Path '+quote(path)+' -Target '+quote(target)+' | Out-Null'],capture_output=True,text=True,timeout=15)
    assert r.returncode==0,r.stderr;junctions.append(path)

try:
    normal=case/'normal';normal.mkdir();(normal/'sentinel.txt').write_text('preserve',encoding='utf-8')
    results['A_NORMAL']=invoke(normal,allowed=True)
    target=case/'target';target.mkdir();(target/'sentinel.txt').write_text('preserve',encoding='utf-8')
    link=case/'root-junction';junction(link,target);results['B_ROOT_JUNCTION']=invoke(link)
    child=target/'child';child.mkdir();results['C_PARENT_JUNCTION']=invoke(link/'child')
    redirected=case/'redirected';redirected.mkdir();junction(redirected/'.autopilot',target);results['D_DESTINATION_JUNCTION']=invoke(redirected)
    results['E_TRAVERSAL']=invoke(str(case/'child'/'..'/'traversal'))
    workspace=case/'approved-scope';workspace.mkdir();results['F_OUTSIDE_DECLARED_SCOPE']=invoke(case/'outside',workspace=workspace)
    symbolic=case/'symbolic'
    try:os.symlink(target,symbolic,target_is_directory=True)
    except OSError as e:results['G_SYMLINK']={'status':'UNAVAILABLE','reason':str(e)}
    else:
        try:results['G_SYMLINK']=invoke(symbolic)
        finally:symbolic.unlink()
    unicode=case/'proyecto válido ñ 漢字';unicode.mkdir();results['H_UNICODE_SPACES']=invoke(unicode,allowed=True)
    badplan=case/'bad-plan.json';badplan.write_text('{}',encoding='utf-8')
    results['INVALID_PLAN']=invoke(case/'invalid-input',source=badplan)
    results['EXISTING_PRESERVED']=invoke(normal)
    # A filesystem change between validation and Apply must be rejected again.
    race=case/'race';race.mkdir();request={'project':str(race),'objective':'Verify race boundary','criteria':['addition verified'],'plan':str(plan)}
    original=prepare.admission(request);race.rmdir();junction(race,target)
    before=snapshot(case)
    response=prepare.execute(request)
    checks['TOCTOU_REVALIDATION_ZERO_WRITE']=negative_assertion(before,snapshot(case),response,2)
    # Controlled initializer failure: stop, remove only declared attempt artifacts,
    # preserve existing project files and an unknown file created during Apply.
    failed=case/'apply-failure';failed.mkdir();(failed/'sentinel.txt').write_text('preserve',encoding='utf-8')
    def inject_failure(encoded):
        (failed/'.autopilot').mkdir();(failed/'.autopilot/STATE.tmp.json').write_text('partial',encoding='utf-8')
        (failed/'user-concurrent.txt').write_text('preserve',encoding='utf-8')
        return subprocess.CompletedProcess([],2,'PREPARE_APPLY_STARTED\ncontrolled failure','')
    response=prepare.execute({**request,'project':str(failed)},initialize=inject_failure)
    checks['APPLY_FAILURE_FAIL_SAFE']=response['status']=='FAIL' and response['cleanup']['status']=='PASS' and not(failed/'.autopilot').exists() and (failed/'sentinel.txt').read_text(encoding='utf-8')=='preserve' and (failed/'user-concurrent.txt').exists()
    checks['DRAFT_CONTRACT_AND_STATE']=contract.inspect(normal)['contract']['authorized'] is False and json.loads((normal/'.autopilot/STATE.json').read_text(encoding='utf-8-sig'))['status']=='INITIALIZED'
    checks['NORMAL_USER_FILE_PRESERVED']=(normal/'sentinel.txt').read_text(encoding='utf-8')=='preserve'
    checks['NO_TEMP_ARTIFACTS']=not list(normal.rglob('*.tmp.*'))
    # Real atomic STATE write using the unchanged State Manager.
    ps=". '"+str(ROOT/'scripts/state-manager.ps1').replace("'","''")+"';$auto='"+str(normal/'.autopilot').replace("'","''")+"';$state=Get-Content -LiteralPath (Join-Path $auto 'STATE.json') -Raw -Encoding UTF8|ConvertFrom-Json;$null=Write-AtomicState -StateObj $state -AutopilotDir $auto -ValidateTransition $false"
    env=os.environ.copy();env['PSModulePath']=r'C:\Windows\System32\WindowsPowerShell\v1.0\Modules'
    r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(ps.encode('utf-16le')).decode()],capture_output=True,text=True,encoding='utf-8',env=env,timeout=30)
    checks['ATOMIC_STATE_WRITE']=r.returncode==0 and (normal/'.autopilot/STATE.previous.json').exists() and not(normal/'.autopilot/STATE.tmp.json').exists()
    # Holding the actual run mutex must deny Prepare before any write.
    probe=case/'mutex-project'
    ps=r"$m=New-Object Threading.Mutex($false,'Local\DesarrolladorAutonomo_RunMutex');$held=$m.WaitOne(0);try {& powershell.exe -NoProfile -NonInteractive -File '"+str(ROOT/'runner/run.ps1')+"' -ProjectRoot '"+str(probe)+"' -Action Prepare -Objective 'Verify mutex admission' -AcceptanceCriteria 'addition verified' -PlanPath '"+str(plan)+"'} finally {if($held){$m.ReleaseMutex()};$m.Dispose()}"
    before=snapshot(case)
    r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(ps.encode('utf-16le')).decode()],capture_output=True,text=True,encoding='utf-8',timeout=15)
    response=json.loads(r.stdout)
    checks['RUN_MUTEX_ZERO_WRITE']=response['reason']=='RUN_ALREADY_ACTIVE' and response['prepare_write_count']==0 and snapshot(case)==before
    # Release only this harness's initialization metadata under the real mutex.
    for prepared in (normal,unicode):
        lock=prepared/'.autopilot/LOCK.json'
        ps=r"$m=New-Object Threading.Mutex($false,'Local\DesarrolladorAutonomo_RunMutex');$held=$m.WaitOne(0);try {if(-not $held){throw 'RUN_ACTIVE'};$path='"+str(lock)+"';$meta=Get-Content -LiteralPath $path -Raw -Encoding UTF8|ConvertFrom-Json;if(Get-Process -Id $meta.owner_pid -ErrorAction SilentlyContinue){throw 'OWNER_ALIVE'};Remove-Item -LiteralPath $path} finally {if($held){$m.ReleaseMutex()};$m.Dispose()}"
        r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(ps.encode('utf-16le')).decode()],capture_output=True,text=True,encoding='utf-8',timeout=15)
        checks['OWNED_INITIALIZATION_LOCK_CLEANUP_'+prepared.name]=r.returncode==0 and not lock.exists()
finally:
    for link in reversed(junctions):
        assert link.is_relative_to(case) and case.is_relative_to(ROOT/'sandbox')
        if link.is_junction():link.rmdir()
report={'status':'PASS' if all(r['status'] in ('PASS','UNAVAILABLE') for r in results.values()) and all(checks.values()) else 'FAIL','cases':results,'smoke':checks,'case_root':str(case),'local_inferences':0,'launcher_prepare':'NOT_APPLICABLE: launcher has no Prepare action','cleanup':'Owned reparse entries removed; fixtures preserved as evidence'}
(E/'prepare-admission.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False));assert report['status']=='PASS'
