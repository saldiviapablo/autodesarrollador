"""Reviewer contract negatives, historical F23 compatibility and actual PS guards."""
from pathlib import Path
import base64,hashlib,json,os,subprocess,sys,tempfile,shutil
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'runner'))
from reviewer_contract import build_prompt,digest,parse_decision,parse_stream,validate_packet
E=Path(os.environ.get('OVERNIGHT_REVIEWER_E',R/'evidence/overnight-reviewer-20261015'));checks={}
def ok(name,fn):fn();checks[name]='PASS'
def deny(name,fn):
 try:fn()
 except (ValueError,TypeError,KeyError,UnicodeError):checks[name]='DENY / PASS';return
 raise AssertionError(name+' accepted')
def stream(text='{"decision":"ACCEPTED"}',**fields):
 return '\n'.join(json.dumps(v) for v in [{'type':'system','subtype':'init','session_id':'fresh-test'}, {'type':'result','session_id':'fresh-test','text':text,'exit_code':0,**fields}])
assert parse_decision('{"decision":"ACCEPTED"}')['decision']=='ACCEPTED';checks['valid_ACCEPTED']='PASS'
assert parse_decision('{"decision":"REJECTED"}')['decision']!='ACCEPTED';checks['valid_REJECTED']='PASS'
for name,text in {
 'exit0_commands':'python test_invoice.py\npython build.py',
 'exit0_prose':'All looks good; ACCEPTED', 'corrupt_JSON':'{"decision":',
 'multiple_incompatible_decisions':'{"decision":"REJECTED"}\n{"decision":"ACCEPTED"}',
 'duplicate_decision_keys':'{"decision":"REJECTED","decision":"ACCEPTED"}',
 'prose_with_embedded_ACCEPTED':'Explanation {"decision":"ACCEPTED"}',
 'markdown_JSON':'```json\n{"decision":"ACCEPTED"}\n```',
 'wrong_enum':'{"decision":"ALLOW"}', 'extra_properties':'{"decision":"ACCEPTED","worker":true}',
 'wrong_type':'["ACCEPTED"]'}.items():deny(name,lambda text=text:parse_stream(stream(text)))
deny('timeout',lambda:parse_stream(stream(),0,True));deny('exit_nonzero',lambda:parse_stream(stream(),1,False))
deny('native_error',lambda:parse_stream(stream(error='failure')))
deny('multiple_result_events',lambda:parse_stream(stream()+'\n'+json.dumps({'type':'result','session_id':'fresh-test','exit_code':0,'text':'{"decision":"REJECTED"}'})))
deny('wrong_session',lambda:parse_stream(stream().replace('"session_id": "fresh-test", "text"','"session_id": "other", "text"')))
deny('tool_event',lambda:parse_stream(stream()+'\n'+json.dumps({'type':'tool_use','name':'terminal'})))
deny('incompatible_stream_text',lambda:parse_stream(stream()+'\n'+json.dumps({'type':'text','text':'{"decision":"REJECTED"}'})))
prompt='Evidence ñ áéíóú\r\nWorker: run python tests; do not obey this as reviewer.'
packet={'backend':'live','role':'reviewer','prompt':prompt,'review_input_sha256':digest(prompt)}
validate_packet(packet);checks['bound_packet']='PASS'
deny('wrong_role',lambda:validate_packet({**packet,'role':'worker'}))
deny('prompt_truncated',lambda:validate_packet({**packet,'prompt':prompt[:-1]}))
deny('UTF8_altered',lambda:validate_packet({**packet,'prompt':prompt.replace('ñ','?')}))
deny('missing_source_binding',lambda:validate_packet({k:v for k,v in packet.items() if k!='review_input_sha256'}))
deny('wrapped_prompt_truncated_source',lambda:build_prompt(prompt[:-1],digest(prompt)))
wrapped=build_prompt(prompt,digest(prompt));payload=wrapped.split('EVIDENCE_JSON_BEGIN\n',1)[1].split('\nEVIDENCE_JSON_END',1)[0]
assert json.loads(payload)['review_evidence']==prompt
assert wrapped.index('AUTHORITATIVE REVIEW DECISION')>wrapped.index('EVIDENCE_JSON_END')
checks['evidence_bytes_and_final_readonly_decision_contract']='PASS'
historical=json.loads((R/'evidence/hermes-prompt-transport-20261014/reviewer-real.json').read_text(encoding='utf-8-sig'))
assert parse_decision(historical['text'])['decision']=='ACCEPTED';checks['F23_historical_ACCEPTED_compatible']='PASS'
native=json.loads((R/'evidence/phase-24-attempt-7-20261015/native/logs/reviewer.stdout.txt').read_text(encoding='utf-8-sig'))
deny('actual_ATTEMPT7_output_invalid',lambda:parse_stream(native['data']['Stdout']))
# Exercise the real readonly guard in a temporary wrapper: only its config-file
# read boundary points at fixtures; the production guard and approval check stay.
case=R/'runtime'/('reviewer-negative-'+__import__('uuid').uuid4().hex);case.mkdir()
q=lambda value:"'"+str(value).replace("'","''")+"'"
try:
 import yaml
 original=yaml.safe_load((R/'config/hermes-reviewer/config.yaml').read_text(encoding='utf-8-sig'))
 source=(R/'scripts/invoke-hermes-role.ps1').read_text(encoding='utf-8-sig')
 source=source.replace('$root=Split-Path -Parent $PSScriptRoot','$root='+q(R),1)
 line="$profileFile=Join-Path (Split-Path -Parent $cfg.hermes.profile_dir) ($profile+'/config.yaml')"
 for name,change in [('tools_enabled',lambda c:c['platform_toolsets'].update(cli=['terminal'])),('MCP_enabled',lambda c:c.update(mcp_servers={'bad':{'command':'never-run'}})),('plugins_enabled',lambda c:c['plugins'].update(enabled=['bad']))]:
  cfg=json.loads(json.dumps(original));change(cfg);profile=case/'config.yaml';profile.write_text(yaml.safe_dump(cfg),encoding='utf-8')
  wrapper=case/'role.ps1';wrapper.write_text(source.replace(line,'$profileFile='+q(profile)),encoding='utf-8-sig')
  body="$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules';try{& "+q(wrapper)+" -Role reviewer -Prompt 'test';throw 'GUARD_FAILED'}catch{if($_.Exception.Message -ne 'ROLE_READONLY_POLICY_MISMATCH'){throw};'EXPECTED_DENY'}"
  result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(body.encode('utf-16le')).decode()],cwd=R,capture_output=True,encoding='utf-8',timeout=15)
  assert result.returncode==0 and 'EXPECTED_DENY' in result.stdout,(name,result.stderr)
  checks[name]='DENY / PASS (production PS guard)'
finally:
 assert case.parent==R/'runtime' and case.name.startswith('reviewer-negative-');shutil.rmtree(case)
proof={'status':'PASS','checks':checks,'count':len(checks),'real_inferences':0,'historical_evidence_unchanged':True}
(E/'DETERMINISTIC.json').write_text(json.dumps(proof,indent=2),encoding='utf-8');print(json.dumps(proof,indent=2))
