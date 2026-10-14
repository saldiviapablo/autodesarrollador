"""Deterministic cmd.exe adapter check; never starts the actual Runner."""
import json,pathlib,subprocess,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]
E=ROOT/'evidence/phase-24-20261014'
case=ROOT/'runtime'/('launcher-boundary-'+uuid.uuid4().hex);case.mkdir()
launcher=case/'launcher with spaces.bat';argument=case/'project with spaces'
launcher.write_bytes(b'@echo off\r\necho ARGUMENT=%~1\r\necho LAUNCHER_BOUNDARY_PASS\r\nexit /b 0\r\n')
command='"'+str(launcher)+'" "'+str(argument)+'"'
try:
    before=subprocess.run(['cmd.exe','/d','/s','/c','"'+command+'"'],capture_output=True,text=True,timeout=10)
    after=subprocess.run('cmd.exe /d /s /c "'+command+'"',capture_output=True,text=True,timeout=10)
    assert before.returncode!=0 and after.returncode==0 and 'LAUNCHER_BOUNDARY_PASS' in after.stdout and str(argument) in after.stdout
    result={'status':'PASS','before_exit_code':before.returncode,'after_exit_code':after.returncode,'after_output':after.stdout,'paths_with_spaces':'PASS','scope':'test adapter only; actual F24 not retried','native_runner_starts':0,'local_inferences':0,'chatgpt_sends':0}
    (E/'launcher-adapter-diagnosis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
finally:
    launcher.unlink();case.rmdir()
