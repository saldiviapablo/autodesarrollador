"""Normal minimal admission only. No test campaign, model calls, or sends."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
R=Path(__file__).resolve().parents[2];E=R/'evidence/phase-24-attempt-10-20261015'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
save=lambda n,v:(E/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
assert subprocess.check_output(['git','status','--porcelain=v1'],cwd=R,text=True).strip()==''
E.mkdir(exist_ok=False)
old=read(R/'evidence/overnight-reviewer-20261015/history-before.json')['files']
# Post-run authorized composer source fix is not historical evidence.
old={n:h for n,h in old.items() if n not in ['tools/chatgpt-send-actuator.js','tools/chatgpt-pre-send.js']}
assert all(sha(R/f)==h for f,h in old.items())
paths={R/f for f in old}
for folder in ['evidence','sandbox/f24-attempt7-86dd900d','sandbox/f24-attempt8-bd7004d5','sandbox/f24-attempt9-2c28c8f9','runtime/chatgpt-consultations','runtime/run-clocks','runtime/run-approvals']:
 paths.update(p for p in (R/folder).rglob('*') if p.is_file() and E not in p.parents)
# Configuration changes only at authorized closure; history preserves actual
# sandboxes, ledgers, clocks and all previous evidence, not future status views.
paths={p for p in paths if p.relative_to(R).as_posix() not in ['config/INSTALLATION-STATE.json']}
save('history-before.json',{'files':{p.relative_to(R).as_posix():sha(p) for p in sorted(paths)}})
protected=read(R/'evidence/phase-24-attempt-5-20261014/protected-final.json')['hashes'];actual={}
for name,expected in protected.items():
 print(json.dumps({'admission_protected':Path(name).name}),flush=True)
 actual[name]=sha(Path(name));assert actual[name]==expected,name
save('protected-before.json',{'status':'PASS','hashes':actual})
import yaml
cfg=yaml.safe_load((R/'config/system.yaml').read_text(encoding='utf-8-sig'))
assert [cfg['llama'][k] for k in ['alias','host','port','ctx_size','parallel']]==['qwen36','127.0.0.1',8080,65536,1]
assert cfg['hermes']['version']=='0.21.6'
gates=read(R/'docs/F24-GATES.json');assert gates['total_gates']==28
assert sha(R/'docs/F24-GATES.json')=='690949c59fbf278f1863a35f4b27b07f3ab3b99960420c939a628625fc526953'
env=dict(os.environ,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
for args in [['powershell.exe','-NoProfile','-NonInteractive','-File',str(R/'logs/f24-attempt10/admission.ps1')],['node',str(R/'logs/f24-attempt10/browser-admission.js')]]:
 p=subprocess.run(args,cwd=R,capture_output=True,encoding='utf-8',timeout=20,env=env)
 print(p.stdout,flush=True);assert p.returncode==0,p.stderr
hp=cfg['document_extraction']['native_python']
code="import psutil,json;print(json.dumps({'ram_available_bytes':psutil.virtual_memory().available,'ram_total_bytes':psutil.virtual_memory().total,'pagefile':psutil.swap_memory()._asdict()}))"
resources=json.loads(subprocess.check_output([hp,'-c',code],encoding='utf-8',env=env))
resources['gpu']=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,memory.total','--format=csv,noheader,nounits'],encoding='utf-8',timeout=5).strip()
assert resources['ram_available_bytes']>Path(cfg['llama']['model']).stat().st_size,'INSUFFICIENT_AVAILABLE_RAM_FOR_APPROVED_MODEL'
save('admission-resources.json',resources)
# Bind the current committed infrastructure, including the new isolated harness.
tracked=subprocess.check_output(['git','ls-files','runner','scripts','tools','tests','schemas','config'],cwd=R,text=True).splitlines()
sources={f:sha(R/f) for f in tracked if (R/f).is_file()}
sources['docs/F24-GATES.json']=sha(R/'docs/F24-GATES.json')
save('ADMISSION.json',{'status':'PASS','sealed':True,'mode':'MINIMAL_NORMAL_ADMISSION_NO_RECERTIFICATION_CAMPAIGN','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'gates_sha256':sha(R/'docs/F24-GATES.json'),'total_gates':28,'source_hashes':sources,'checks':{'git_clean_before_admission':True,'protected_hashes':True,'mutex_ports':'admission-locks-ports.json','profile_domain_single_tab':'admission-browser.json','resources':'admission-resources.json','approved_model_configuration':True,'certified_counter_and_live_fresh_chat':'80dd12c / f897e14','reviewer_fix_certification':'1796a93 / evidence/overnight-reviewer-20261015/CERTIFIED.json','composer_fix_certification':'a3edd3b / evidence/chatgpt-active-composer-20261015/CERTIFIED.json','pointer_preintent_certification':'652db9d / evidence/chatgpt-pointer-preintent-20261015/CERTIFIED.json'},'tests_rerun':False,'budgets':{'global_timeout_seconds':2700,'phase_timeout_seconds':300,'restart_budget':2,'max_cycles':5}})
(E/'.gitattributes').write_text('* -text whitespace=-blank-at-eol,-blank-at-eof,space-before-tab,cr-at-eol\n',encoding='utf-8')
for name in ['prepare-admission.py','admission.ps1','browser-admission.js']:
 (E/name).write_bytes((R/'logs/f24-attempt10'/name).read_bytes())
print(json.dumps({'ADMISSION':'PASS','RAM_available_GiB':resources['ram_available_bytes']/1024**3,'frozen_gates':28,'source_files_bound':len(sources)}),flush=True)
