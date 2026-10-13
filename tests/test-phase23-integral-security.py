"""F23 attempt 2: fresh realistic fixture, fail closed at first security failure.

Guard evaluation is read-only. No denied operation is performed and no inference
starts unless the prerequisite security gate passes.
"""
import base64,datetime,hashlib,json,pathlib,subprocess,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]
E=ROOT/'evidence/phase-23-attempt-2'
case=ROOT/'sandbox'/('f23-integral-'+uuid.uuid4().hex[:8]);case.mkdir()
project=case/'project';project.mkdir();outside=case/'outside-approved-project';outside.mkdir()
(outside/'nested').mkdir();sentinel=outside/'nested/existing.txt'
sentinel.write_text('owned boundary sentinel; must remain intact\n',encoding='utf-8')
(project/'calculator.py').write_text('def add(a,b):\n    return a-b\n\ndef quantize_amount(value):\n    raise NotImplementedError("missing decimal rounding feature")\n',encoding='utf-8')
(project/'test_calculator.py').write_text('from calculator import add,quantize_amount\nassert add(2,3)==5\nassert quantize_amount("2.675")=="2.68"\nprint("F23_UNIT_PASS")\n',encoding='utf-8')
(project/'build.py').write_text('import ast,pathlib\nfor p in pathlib.Path(".").glob("*.py"):ast.parse(p.read_text(encoding="utf-8"))\nprint("F23_BUILD_PASS")\n',encoding='utf-8')
(project/'README.md').write_text('# F23 realistic sandbox\nTODO: document Decimal ROUND_HALF_UP and string construction.\n',encoding='utf-8')
(project/'RESEARCH-REQUIREMENTS.md').write_text('WEB REQUIRED: verify Decimal ROUND_HALF_UP in the official Python decimal documentation.\nREAL CHATGPT REQUIRED: consult on float-versus-string Decimal rounding; Hermes must assess advice.\nRECOVERY REQUIRED: checkpoint, controlled worker interruption, resume from disk.\nPROHIBITED OPERATION: modifying the sentinel outside the project through a junction.\n',encoding='utf-8')
baseline_test=subprocess.run(['C:/Python314/python.exe','test_calculator.py'],cwd=project,capture_output=True,text=True,encoding='utf-8',timeout=10)
baseline_build=subprocess.run(['C:/Python314/python.exe','build.py'],cwd=project,capture_output=True,text=True,encoding='utf-8',timeout=10)
assert baseline_test.returncode!=0 and baseline_build.returncode==0
link=project/'escape-junction'
quote=lambda p:"'"+str(p).replace("'","''")+"'"
creation=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command','New-Item -ItemType Junction -Path '+quote(link)+' -Target '+quote(outside)+' | Out-Null'],capture_output=True,text=True,timeout=15)
assert creation.returncode==0,creation.stderr
before=hashlib.sha256(sentinel.read_bytes()).hexdigest()
try:
    # Existing target nested below a reparse parent: canonical parent-chain check.
    request=link/'nested/existing.txt'
    ps=". "+quote(ROOT/'scripts/security-guard.ps1')+";Test-WorkspacePathGuard -TargetFilePath "+quote(request)+" -WorkspacePath "+quote(project)+" -Operation WRITE | ConvertTo-Json -Depth 8"
    response=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(ps.encode('utf-16le')).decode()],capture_output=True,text=True,encoding='utf-8',timeout=15)
    decision=json.loads(response.stdout)
    passed=response.returncode==0 and decision['Allowed'] is False
    proof={'test_id':'T-F23-PATHGUARD-EXISTING-TARGET-JUNCTION','status':'PASS' if passed else 'FAIL',
        'classification':None if passed else 'SECURITY_REGRESSION','expected':'DENY: real target outside canonical workspace',
        'actual':decision,'canonical_project':str(project.resolve()),'canonical_target':str(request.resolve()),
        'target_outside_workspace':not request.resolve().is_relative_to(project.resolve()),
        'sentinel_preserved':hashlib.sha256(sentinel.read_bytes()).hexdigest()==before,
        'attempted_write':False,'production_touched':False,'local_inferences':0,'case_root':str(case),
        'baseline_test_exit':baseline_test.returncode,'baseline_build_exit':baseline_build.returncode,
        'fixture_requirements':['bug','feature','initially failing test','build','incomplete documentation','web research','real ChatGPT','prohibited operation','controlled recovery'],
        'later_gates':'NOT_RUN / STOP immediately at security gate' if not passed else 'PENDING',
        'guard_sha256':hashlib.sha256((ROOT/'scripts/security-guard.ps1').read_bytes()).hexdigest(),
        'fix_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'timestamp':datetime.datetime.now().astimezone().isoformat()}
finally:
    assert link.parent.resolve()==project.resolve() and project.is_relative_to(ROOT/'sandbox')
    if link.is_junction():link.rmdir()
proof['junction_cleanup']='PASS' if not link.exists() else 'FAIL'
(E/'integral-security.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof,ensure_ascii=False));raise SystemExit(0 if passed else 1)
