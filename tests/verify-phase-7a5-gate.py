"""Admission, persisted role evidence and frozen control integrity checks."""
import hashlib, json, pathlib, subprocess, yaml
ROOT=pathlib.Path(__file__).resolve().parents[1]
cfg=yaml.safe_load((ROOT/'config/system.yaml').read_text(encoding='utf-8-sig'))
evidence=ROOT/'evidence/phase-7a5'
checks={}
for role in ('supervisor','reviewer','researcher'):
    live=pathlib.Path(cfg['hermes']['profile_dir']).parent/cfg['bot_roles'][role+'_profile']/'config.yaml'
    template=ROOT/'config'/('hermes-'+role)/'config.yaml'
    data=yaml.safe_load(live.read_text(encoding='utf-8-sig'))
    checks[role+'_profile_integrity']=live.read_bytes()==template.read_bytes()
    checks[role+'_no_tools']=data['platform_toolsets']['cli']==[] and data['mcp_servers']=={} and data['plugins']['enabled']==[]
    checks[role+'_no_hook_auto_accept']=not data.get('hooks_auto_accept',False)
for name in ('T-7A-BOT-001','T-7A-BOT-002','T-7A-BOT-003','T-7A-SUBAGENT-001'):
    checks[name]=json.loads((evidence/(name+'.json')).read_text(encoding='utf-8-sig'))['status']=='PASS'
for name in ('config/security.yaml','scripts/inference-lock.ps1','scripts/hermes-pre-tool-hook.py'):
    historical=subprocess.check_output(['git','show','8502d79:'+name],cwd=ROOT)
    checks[name+'_unchanged']=historical.replace(b'\r\n',b'\n')==(ROOT/name).read_bytes().replace(b'\r\n',b'\n')
checks['subagent_capability_redacted']=json.loads((evidence/'T-7A-SUBAGENT-001.json').read_text(encoding='utf-8-sig'))['native_child_result']['handle']['capability']=='[REDACTED]'
result={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'new_dependencies':[]}
(evidence/'deterministic-gate.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result));assert all(checks.values()),checks
