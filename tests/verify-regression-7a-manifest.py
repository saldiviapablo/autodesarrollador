"""Exhaustive mandatory evidence and current component integrity, without rerunning approved suites."""
import hashlib,json,pathlib,subprocess,sys,yaml
ROOT=pathlib.Path(__file__).resolve().parents[1]
E=ROOT/'evidence/regression-7a-final';E.mkdir(exist_ok=True)
cfg=yaml.safe_load((ROOT/'config/system.yaml').read_text(encoding='utf-8-sig'))
security=yaml.safe_load((ROOT/'config/security.yaml').read_text(encoding='utf-8-sig'))
versions=yaml.safe_load((ROOT/'config/VERSIONS.lock').read_text(encoding='utf-8-sig'))
checks={};phases={}
def load(name):return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def require(name,value):checks[name]=bool(value)
for phase in range(1,11):
    if phase in (1,2,3,4):name=f'evidence/phase-7a{phase}/phase-7a{phase}-summary.json'
    elif phase==5:name='evidence/phase-7a5/SUMMARY.json'
    else:name=f'evidence/phase-7a{phase}/tests.json'
    data=load(name);tests=data.get('tests',data.get('data',{}).get('tests',{}))
    passed=(data.get('status')=='PASS' or data.get('all_passed') is True) and bool(tests) and all(v=='PASS' for v in tests.values())
    require(f'7A.{phase}_mandatory_evidence',passed)
    phases[f'7A.{phase}']={'status':'PASS' if passed else 'FAIL','evidence':name,'tests':tests}
required={'7A.1':['T-7A-MEM-001','T-7A-MEM-002','T-7A-SKILL-001','T-7A-SKILL-002','T-7A-HIERARCHY-001','T-7A-HOOK-001'],
          '7A.2':['T-7A-MCP-001','T-7A-MCP-002','T-7A-MCP-003','T-7A-MCP-004','T-7A-MCP-005','T-7A-PLUGIN-001','T-7A-PLUGIN-002'],
          '7A.3':[f'T-7A-DOC-{i:03}' for i in range(1,6)],'7A.4':[f'T-7A-BROWSER-{i:03}' for i in range(1,6)],
          '7A.5':['T-7A-BOT-001','T-7A-BOT-002','T-7A-SUBAGENT-001'],'7A.6':[f'T-7A-WT-{i:03}' for i in range(1,4)],
          '7A.7':['T-7A-CRON-001','T-7A-CRON-002'],'7A.8':[f'T-7A-DASH-{i:03}' for i in range(1,4)],
          '7A.9':['T-7A-GATEWAY-001','T-7A-GATEWAY-002'],'7A.10':['T-7A-UPDATE-001','T-7A-UPDATE-002']}
for phase,ids in required.items():require(phase+'_all_required_test_ids',all(phases[phase]['tests'].get(i)=='PASS' for i in ids))
for phase in range(3,11):
    evidence=f'evidence/phase-7a{phase}/regression-smoke.json'
    require(f'7A.{phase}_prior_smoke',load(evidence)['status']=='PASS')
for n in ('real-tests','deterministic','budget','budget-race','state-schema','regression-smoke'):
    require('idempotency_'+n,load('evidence/chatgpt-idempotency/'+n+'.json')['status']=='PASS')
binding=load('evidence/chatgpt-idempotency/real-source-hashes.json')
for name,value in binding['hashes'].items():require('current_real_smoke_binding_'+name,sha(ROOT/name)==value)
for name in ('wrapper-final-utf8','wrapper-final-cleanup'):
    require(name,load('evidence/chatgpt-idempotency/'+name+'.json')['Status']=='SUCCESS')
for name in ('config/security.yaml','scripts/inference-lock.ps1','scripts/hermes-pre-tool-hook.py','scripts/security-guard.ps1','scripts/hermes-memory-guard.ps1','scripts/hermes-mcp-plugin-guard.ps1','scripts/progress-guard.ps1','schemas/run-contract.schema.json'):
    original=subprocess.check_output(['git','show','8502d79:'+name],cwd=ROOT)
    require('frozen_'+name,original.replace(b'\r\n',b'\n')==(ROOT/name).read_bytes().replace(b'\r\n',b'\n'))
hook=security['hooks']['pre_tool_call'];require('approved_hook_sha256',sha(ROOT/hook['path'])==hook['sha256'])
mcp=security['mcp']['servers']['da_local_sandbox'];require('approved_mcp_sha256',sha(ROOT/mcp['script_path'])==mcp['sha256'])
plugin=security['plugins']['approved_plugins']['desarrollador-autonomo-health']
for location in (ROOT/plugin['repo_dir'],pathlib.Path(plugin['profile_dir'])):
    require('plugin_entry_'+str(location),sha(location/plugin['entrypoint'])==plugin['sha256'])
    require('plugin_manifest_'+str(location),sha(location/'plugin.yaml')==plugin['manifest_sha256'])
native=pathlib.Path(cfg['document_extraction']['native_source_dir'])
require('native_read_extract_hash',sha(native/'tools/read_extract.py')==cfg['document_extraction']['native_read_extract_sha256'])
require('native_file_tools_hash',sha(native/'tools/file_tools.py')==cfg['document_extraction']['native_file_tools_sha256'])
require('native_browser_hash',sha(native/'tools/browser_tool.py')==cfg['native_browser']['native_module_sha256'])
require('hermes_frozen_head',subprocess.check_output(['git','-C',str(native),'rev-parse','HEAD'],text=True).strip()==cfg['hermes']['commit'])
require('hermes_checkout_clean',not subprocess.check_output(['git','-C',str(native),'status','--porcelain'],text=True).strip())
require('hermes_productive_version',load(str(native/'install-stamp.json'))['baseVersion']=='0.21.6')
require('llama_alias_host_context_parallel',cfg['llama']['alias']=='qwen36' and cfg['llama']['host']=='127.0.0.1' and cfg['llama']['port']==8080 and cfg['llama']['ctx_size']==65536 and cfg['llama']['parallel']==1)
require('frozen_versions_lock_since_canary',not subprocess.check_output(['git','diff','597431b','--','config/VERSIONS.lock'],cwd=ROOT,text=True))
install=load('config/INSTALLATION-STATE.json')
require('installation_subphases_all_pass',all(install['subphases_7a'][f'7A.{i}']=='PASS' for i in range(1,11)))
require('macros_1_6_still_pass',all(install['macrophases'][str(i)]=='PASS' for i in range(1,7)))
require('7b_8_not_started',install['macrophases']['7B']=='PENDING' and install['macrophases']['8']=='PENDING')
require('no_native_update_executed',load('evidence/phase-7a10/tests.json')['actual_update_executed'] is False)
report={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'subphases':phases,'mandatory_test_count':sum(len(ids) for ids in required.values()),'approved_subphase_suites_repeated':False}
(E/'mandatory-integrity.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':len(checks),'failed':[n for n,v in checks.items() if not v],'mandatory_test_count':report['mandatory_test_count']}));assert all(checks.values()),report
