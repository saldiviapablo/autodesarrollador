"""Isolated deterministic regression; no local inference. Existing phase suites unchanged."""
import argparse,json,pathlib,subprocess,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1];e=ROOT/'evidence/regression-7b-final';e.mkdir(exist_ok=True)
ap=argparse.ArgumentParser();ap.add_argument('--checks',nargs='+',choices=['state','security','checkpoint','lock'],default=['state','security','checkpoint']);a=ap.parse_args()
definitions={'state':('test-fase10-state.ps1','RESULTADO FINAL DE FASE 10: [PASS]'),'security':('test-fase15-security.ps1','RESULTADO FINAL DE FASE 15: [PASS]'),'checkpoint':('test-checkpoint-integrity.ps1','PASS'),'lock':('test-inference-lock.ps1','PASS')}
result_path=e/'deterministic-smoke.json';results=json.loads(result_path.read_text())['checks'] if result_path.exists() else {}
def psquote(value):return "'"+str(value).replace("'","''")+"'"
for name in a.checks:
    script,marker=definitions[name];sandbox=(ROOT/'sandbox'/('7b-regression-'+name+'-'+uuid.uuid4().hex[:8])).absolute()
    assert sandbox.is_relative_to(ROOT/'sandbox') and not sandbox.exists()
    command="$env:PSModulePath=Join-Path $PSHOME 'Modules'; & "+psquote(ROOT/'tests'/script)
    if name!='lock':command+=' -SandboxDir '+psquote(sandbox)
    if name in ('state','security','lock'):command+=' -EvidenceDir '+psquote(e/name)
    r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
    (e/(name+'.stdout.txt')).write_text('\n'.join(v.rstrip() for v in r.stdout.splitlines())+'\n',encoding='utf-8');(e/(name+'.stderr.txt')).write_text('\n'.join(v.rstrip() for v in r.stderr.splitlines())+'\n',encoding='utf-8')
    results[name]={'status':'PASS' if r.returncode==0 and marker in r.stdout else 'FAIL','exit_code':r.returncode,'marker':marker}
    assert results[name]['status']=='PASS',(name,r.stdout,r.stderr)
result={'status':'PASS','checks':results,'local_inferences':0,'prior_evidence_rewritten':False};result_path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
