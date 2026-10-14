"""A–H deterministic tests. Fake batch only, no native Runner or inference."""
import hashlib,json,os,pathlib,tempfile
from windows_launcher_adapter import launch_batch

ROOT=pathlib.Path(__file__).resolve().parents[1]
E=pathlib.Path(os.environ.get('F24_PREFLIGHT_E',str(ROOT/'evidence/f24-launcher-adapter-fix-20261014')))/'launcher';E.mkdir(parents=True,exist_ok=True)
# A requires a path without spaces; the infrastructure root contains spaces.
# Create exclusively new, uniquely named files in the user's existing temp area.
case=pathlib.Path(tempfile.mkdtemp(prefix='da-launcher-')).resolve()
created=[];checks={};results=[]
try:
    capture=case/'capture.py';counter=case/'invocations.jsonl'
    capture.write_text('''import json,os,pathlib,sys
sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
args=sys.argv[1:]
with pathlib.Path(os.environ['DA_LAUNCHER_COUNTER']).open('a',encoding='utf-8') as file:file.write(json.dumps({'args':args,'pid':os.getpid()},ensure_ascii=False)+'\\n')
print(json.dumps({'args':args},ensure_ascii=False))
print('STDERR áéíóú ñ € °',file=sys.stderr)
raise SystemExit(int(os.environ.get('DA_LAUNCHER_EXIT','0')))
''',encoding='utf-8');created += [capture,counter]
    for filename in ('launcher.bat','launcher with spaces.bat'):
        path=case/filename
        path.write_bytes(b'@echo off\r\n"C:\\Python314\\python.exe" "%~dp0capture.py" %*\r\nexit /b %errorlevel%\r\n');created.append(path)
    env=dict(os.environ,DA_LAUNCHER_COUNTER=str(counter),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
    tests=[('A',case/'launcher.bat',['simple'],0),('B',case/'launcher with spaces.bat',['simple'],0),('C',case/'launcher.bat',[str(case/'project with spaces')],0),('D',case/'launcher with spaces.bat',['áéíóú ñ ¿? € °','second argument'],0),('E',case/'launcher.bat',['first','','third'],0),('G',case/'launcher.bat',['exit-code'],37)]
    assert ' ' not in str(case/'launcher.bat')
    for name,launcher,args,exit_code in tests:
        previous=len(counter.read_text(encoding='utf-8').splitlines()) if counter.exists() else 0
        proc=launch_batch(launcher,args,env=dict(env,DA_LAUNCHER_EXIT=str(exit_code)))
        out,err=proc.communicate(timeout=15)
        actual=json.loads(out)['args'];count=len(counter.read_text(encoding='utf-8').splitlines())
        checks[name]=actual==args and proc.returncode==exit_code and count==previous+1
        checks[name+'_exactly_once']=count==previous+1
        results.append({'case':name,'expected':args,'actual':actual,'exit_code':proc.returncode,'stdout':out,'stderr':err,'execution_count_delta':count-previous})
        assert checks[name],results[-1]
    before=counter.read_bytes();denied=[]
    for value in ('x & echo INJECTED','x | echo INJECTED','> injected.txt','< input','%COMSPEC%','!VARIABLE!','x^&echo INJECTED','" & echo INJECTED','x\r\necho INJECTED','x\x00tail','$(echo malicious)'):
        try:launch_batch(case/'launcher.bat',[value],env=env)
        except ValueError:denied.append(value)
        else:raise AssertionError('UNSAFE_ARGUMENT_WAS_NOT_DENIED')
    checks['F']=counter.read_bytes()==before and not(case/'injected.txt').exists()
    checks['H']=all('STDERR áéíóú ñ € °' in result['stderr'] and json.loads(result['stdout'])['args']==result['expected'] for result in results)
    checks['historical_diagnosis']=json.loads((ROOT/'evidence/phase-24-20261014/launcher-adapter-diagnosis.json').read_text(encoding='utf-8'))['status']=='PASS'
    result={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'results':results,'dangerous_arguments_denied':denied,'new_dependencies':[],'native_runner_starts':0,'local_inferences':0,'external_write_reason':'Required case A needs a no-spaces path; infrastructure root contains spaces. New isolated temp files only, no existing files modified.','temporary_directory':str(case),'adapter_sha256':hashlib.sha256((ROOT/'tests/windows_launcher_adapter.py').read_bytes()).hexdigest()}
finally:
    # Remove only the exact task-created files, no recursive or cross-shell deletion.
    for path in created:
        assert path.parent==case and case.name.startswith('da-launcher-')
        if path.exists():path.unlink()
    case.rmdir()
result['cleanup']='PASS'
(E/'adapter-A-H.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':checks,'cleanup':result['cleanup']}))
