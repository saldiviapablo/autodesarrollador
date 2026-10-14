"""Consolidate F23 continuation and protected/historical integrity."""
import hashlib,json,pathlib,subprocess
import yaml
ROOT=pathlib.Path(__file__).resolve().parents[1];E=ROOT/'evidence/hermes-prompt-transport-20261014'
read=lambda path:json.loads(path.read_text(encoding='utf-8-sig'))
checks={}
for name in ('complex-transport.json','regression-smoke.json','f23-reviewer-continuation.json','resource-summary.json'):
    checks[name]=read(E/name)['status']=='PASS'
complex=read(E/'complex-transport.json')
checks['timeout']=complex['timeout_test']=='PASS'
checks['current_wrapper_tested']=complex['wrapper_sha256']==hashlib.sha256((ROOT/'scripts/invoke-hermes.ps1').read_bytes()).hexdigest()
before=read(E/'before-boundary.json');checks['before_boundary_reproduced']=before['status']=='PASS' and not before['integrity_before']
protected={}
for name in ('config/system.yaml','config/security.yaml','config/VERSIONS.lock','scripts/inference-lock.ps1','scripts/hermes-pre-tool-hook.py','scripts/invoke-hermes-role.ps1','scripts/invoke-qwen-code.ps1','scripts/invoke-delegation.ps1','scripts/canonical_path.py','scripts/security-guard.ps1','scripts/hermes-mcp-plugin-guard.ps1'):
    expected=subprocess.check_output(['git','show','cada0b2:'+name],cwd=ROOT)
    current=(ROOT/name).read_bytes()
    checks[name+'_unchanged']=expected.replace(b'\r\n',b'\n')==current.replace(b'\r\n',b'\n')
    protected[name]=hashlib.sha256(current).hexdigest()
for folder in ('evidence/phase-23','evidence/phase-23-attempt-2','evidence/phase-23-attempt-3','evidence/f23-human-reconciliation','evidence/phase-23-resume-20261014'):
    paths=subprocess.check_output(['git','ls-tree','-r','--name-only','cada0b2','--',folder],cwd=ROOT,text=True).splitlines()
    checks[folder+'_historical_unchanged']=bool(paths) and all(subprocess.check_output(['git','show','cada0b2:'+name],cwd=ROOT).replace(b'\r\n',b'\n')==(ROOT/name).read_bytes().replace(b'\r\n',b'\n') for name in paths)
cfg=yaml.safe_load((ROOT/'config/system.yaml').read_text(encoding='utf-8-sig'))
checks['frozen_model_parameters']=all(cfg['llama'][key]==value for key,value in {'alias':'qwen36','host':'127.0.0.1','port':8080,'ctx_size':65536,'parallel':1}.items())
for key,expected in [('executable','c741d245d827a0a3d3896f5f9b0039b3bb282dc9fc9840aa7cd7d072ddd86a39'),('model','671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7')]:
    with pathlib.Path(cfg['llama'][key]).open('rb') as file:actual=hashlib.file_digest(file,'sha256').hexdigest()
    checks['llama_'+key+'_sha256']=actual==expected;protected[key]=actual
native=pathlib.Path(cfg['hermes']['executable']).parents[1]/'hermes-agent'
head=subprocess.check_output(['git','-C',str(native),'rev-parse','HEAD'],text=True).strip()
checks['hermes_frozen_commit']=head==cfg['hermes']['commit']=='818c13be1dc4fd28987e1e881a9408224afd4535'
for role in ('supervisor','reviewer'):
    template=ROOT/('config/hermes-'+role+'/config.yaml')
    installed=pathlib.Path(cfg['hermes']['profile_dir']).parent/cfg['bot_roles'][role+'_profile']/'config.yaml'
    profile=yaml.safe_load(installed.read_text(encoding='utf-8-sig'))
    checks[role+'_readonly_profile']=installed.read_bytes()==template.read_bytes() and profile['platform_toolsets']['cli']==[] and profile['plugins']['enabled']==[] and profile['mcp_servers']=={} and not profile.get('hooks_auto_accept',False)
checks['completion_gate']=read(E/'completion-gate.json')['status']=='COMPLETED'
checks['job_ready_files_removed']=not list((ROOT/'runtime/hermes-jobs').glob('*.ready'))
result={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'protected_sha256':protected,'native_commit':head,'new_dependencies':[],'historical_fail_preserved':True}
(E/'fix-and-f23-gate.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result));raise SystemExit(0 if result['status']=='PASS' else 1)
