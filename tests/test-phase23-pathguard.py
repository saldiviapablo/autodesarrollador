"""Physical confinement A-J, READ/WRITE, bounded links and governed adapters."""
import base64,hashlib,json,os,pathlib,subprocess,sys,uuid
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'runner'))
import canonical_path,contract
E=ROOT/'evidence/phase-23-attempt-3';E.mkdir(exist_ok=True)
case=ROOT/'sandbox'/('pathguard-'+uuid.uuid4().hex[:8]);case.mkdir()
project=case/'project';project.mkdir();inside=project/'inside';inside.mkdir()
outside=case/'outside';outside.mkdir();(outside/'nested').mkdir()
for p in (inside/'normal.txt',outside/'existing.txt',outside/'nested/existing.txt'):
    p.write_text('owned pathguard sentinel\n',encoding='utf-8')
unicode=project/'válido ñ 漢字';unicode.mkdir();(unicode/'archivo con espacios.txt').write_text('UTF-8 ñ 漢字',encoding='utf-8')
quote=lambda s:"'"+str(s).replace("'","''")+"'"
links=[]
def junction(p,target):
    r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command','New-Item -ItemType Junction -Path '+quote(p)+' -Target '+quote(target)+' | Out-Null'],capture_output=True,text=True,timeout=15)
    assert r.returncode==0,r.stderr;links.append(p)
def snapshot(root):
    rows={}
    for current,dirs,files in os.walk(root,followlinks=False):
        for name in dirs[:]:
            p=pathlib.Path(current)/name;link=p.is_symlink() or p.is_junction()
            rows[str(p.relative_to(root))]='LINK' if link else 'DIR'
            if link:dirs.remove(name)
        for name in files:
            p=pathlib.Path(current)/name;rows[str(p.relative_to(root))]='LINK' if p.is_symlink() else hashlib.sha256(p.read_bytes()).hexdigest()
    return rows
checks={};results=[]
try:
    junction(project/'external',outside);junction(project/'internal',inside)
    junction(project/'second',outside);junction(project/'first',project/'second')
    junction(project/'windows',pathlib.Path('C:/Windows'))
    lookalike=case/'project-evil';lookalike.mkdir();(lookalike/'existing.txt').write_text('prefix sentinel',encoding='utf-8')
    cases=[('A',inside/'normal.txt',True),('B',project/'external/existing.txt',False),
        ('C',project/'external/new.txt',False),('D',project/'external/nested',False),
        ('E',project/'internal/normal.txt',True),('F',project/'first/existing.txt',False),
        ('G',str(project/'..'/'outside/existing.txt'),False),('H',outside/'existing.txt',False),
        ('I',unicode/'archivo con espacios.txt',True),('J',str(project/'external/existing.txt').upper(),False),
        ('PREFIX_LOOKALIKE',lookalike/'existing.txt',False),('MISSING_NORMAL',project/'new-directory/new.txt',True)]
    # Symlinks are supported by this Windows environment; exercise actual loops.
    os.symlink('loop-b',project/'loop-a',target_is_directory=True);links.append(project/'loop-a')
    os.symlink('loop-a',project/'loop-b',target_is_directory=True);links.append(project/'loop-b')
    os.symlink('missing-target',project/'dangling',target_is_directory=True);links.append(project/'dangling')
    cases+=[('CYCLE',project/'loop-a/file.txt',False),('DANGLING',project/'dangling/new.txt',False)]
    next_target=inside
    for index in range(canonical_path.MAX_REPARSE_HOPS+1):
        p=project/('hop-'+str(index));os.symlink(next_target,p,target_is_directory=True);links.append(p);next_target=p
    cases.append(('LINK_LIMIT',next_target/'normal.txt',False))
    requests=[{'id':name+'_'+operation,'target':str(p),'workspace':str(project),'operation':operation,'expected':allowed} for name,p,allowed in cases for operation in ('READ','WRITE')]
    requests.append({'id':'ROOT_DESTROY','target':str(project),'workspace':str(project),'operation':'DESTROY','expected':False})
    requests_path=case/'requests.json';requests_path.write_text(json.dumps(requests,ensure_ascii=False),encoding='utf-8')
    ps="$env:PSModulePath=Join-Path $PSHOME 'Modules';. "+quote(ROOT/'scripts/security-guard.ps1')+";$items=Get-Content -LiteralPath "+quote(requests_path)+" -Raw -Encoding UTF8|ConvertFrom-Json;foreach($item in $items){$decision=Test-WorkspacePathGuard -TargetFilePath $item.target -WorkspacePath $item.workspace -Operation $item.operation;@{id=$item.id;expected=$item.expected;decision=$decision}|ConvertTo-Json -Depth 12 -Compress}"
    before=snapshot(case)
    r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(ps.encode('utf-16le')).decode()],capture_output=True,text=True,encoding='utf-8',timeout=60)
    assert r.returncode==0,r.stderr
    results=[json.loads(line) for line in r.stdout.splitlines() if line.strip()]
    for result in results:
        checks[result['id']]=result['decision']['Allowed']==result['expected'] and result['decision']['writes_performed']==0
    checks['ZERO_SIDE_EFFECTS']=snapshot(case)==before
    checks['EXACT_ORIGINAL_REASON']=next(v for v in results if v['id']=='B_WRITE')['decision']['Reason']=='PATH_BOUNDARY_VIOLATION'
    # Runner and Prepare call the same resolver with their existing stricter policy.
    for name in ('external','internal','first'):
        try:contract.check_path(project/name/'existing.txt')
        except ValueError as e:checks['RUNNER_'+name]=str(e)=='REPARSE_POINT_DENIED'
        else:checks['RUNNER_'+name]=False
    try:contract.project_path(outside,workspace=project)
    except ValueError as e:checks['RUNNER_SCOPE']=str(e)=='PATH_BOUNDARY_VIOLATION'
    else:checks['RUNNER_SCOPE']=False
    with patch.object(canonical_path.os,'readlink',side_effect=OSError('controlled unreadable reparse')):
        try:canonical_path.resolve_path(project/'external/existing.txt')
        except canonical_path.PathDenied as e:checks['UNREADABLE_REPARSE_FAIL_CLOSED']=str(e)=='UNSUPPORTED_REPARSE_DENIED'
        else:checks['UNREADABLE_REPARSE_FAIL_CLOSED']=False
    # Approved server and plugin remain byte-identical; adapters use central admission.
    mcp=ROOT/'sandbox/phase7a2-mcp'/('pathguard-'+uuid.uuid4().hex[:8]);mcp.mkdir()
    (mcp/'normal.txt').write_text('governed read sentinel',encoding='utf-8');junction(mcp/'external',outside)
    wrapper=ROOT/'scripts/hermes-mcp-plugin-guard.ps1'
    def guarded(action,arguments,tool=None):
        payload=base64.b64encode(json.dumps(arguments).encode()).decode()
        ps="$env:PSModulePath=Join-Path $PSHOME 'Modules';$env:PYTHONUTF8='1';$env:PYTHONDONTWRITEBYTECODE='1';$argsJson=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('"+payload+"'));& "+quote(wrapper)+" -Action "+action+" -ArgumentsJson $argsJson"+(" -McpToolName "+tool if tool else '')
        r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(ps.encode('utf-16le')).decode()],capture_output=True,text=True,encoding='utf-8',timeout=40)
        assert r.returncode==0,r.stderr;return json.loads(r.stdout)
    adapters={}
    adapters['mcp_external']=guarded('InvokeMcpTool',{'relative_path':str(mcp/'external/existing.txt')},'da_read_sandbox')
    checks['MCP_EXTERNAL_DENY']=adapters['mcp_external'].get('decision')=='DENY'
    adapters['mcp_normal']=guarded('InvokeMcpTool',{'relative_path':str(mcp/'normal.txt')},'da_read_sandbox')
    checks['MCP_NORMAL_ALLOW']=adapters['mcp_normal'].get('decision')=='ALLOW' or (not adapters['mcp_normal'].get('is_error',True) and adapters['mcp_normal'].get('status')=='AVAILABLE')
    adapters['plugin_external']=guarded('InvokePluginTool',{'target_path':str(project/'windows/win.ini')})
    checks['PLUGIN_EXTERNAL_DENY']=adapters['plugin_external'].get('decision')=='DENY'
    adapters['plugin_normal']=guarded('InvokePluginTool',{'target_path':str(inside/'normal.txt')})
    checks['PLUGIN_NORMAL_ALLOW']=adapters['plugin_normal'].get('decision')=='ALLOW'
    adapters['plugin_integrity']=guarded('VerifyPluginIntegrity',{})
    checks['PLUGIN_SHA256']=adapters['plugin_integrity'].get('status')=='PASS'
finally:
    for link in reversed(links):
        assert link.is_relative_to(ROOT/'sandbox')
        if link.is_symlink():link.unlink()
        elif link.is_junction():link.rmdir()
proof={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'cases':results,'adapters':adapters,
    'policy_E':'Existing 04 policy permits physical target inside workspace; Runner/Prepare/MCP retain stricter all-reparse DENY',
    'before':json.loads((ROOT/'evidence/phase-23-attempt-2/integral-security.json').read_text(encoding='utf-8'))['actual'],
    'case_root':str(case),'cleanup':'Owned links removed nonrecursively; inert fixtures retained','local_inferences':0}
(E/'pathguard-A-J.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':proof['status'],'checks':checks,'adapters':adapters},ensure_ascii=False));assert proof['status']=='PASS'
