"""Capture installed Hermes query + model request before network/inference.

Temporary wrapper copies instrument the native read/HTTP boundary only. Source,
profiles, old sandbox and all historical evidence remain read-only.
"""
from pathlib import Path
import base64,hashlib,json,os,subprocess,uuid,shutil
R=Path(__file__).resolve().parents[1]
E=Path(os.environ.get('OVERNIGHT_REVIEWER_E',R/'evidence/overnight-reviewer-20261015'))
wrapped_mode=os.environ.get('REVIEWER_AUDIT_WRAPPED')=='1'
D=E/('input-audit-wrapped' if wrapped_mode else 'input-audit');D.mkdir(exist_ok=True)
case=R/'runtime'/('reviewer-input-'+uuid.uuid4().hex);case.mkdir()
q=lambda value:"'"+str(value).replace("'","''")+"'"
probe=case/'probe.py'
probe.write_text('''import sys,os,json,hashlib,pathlib
out=pathlib.Path(os.environ['DA_REVIEWER_AUDIT_OUTPUT'])
def capture(frame,event,arg):
 if event=='return' and frame.f_code.co_name=='_read_query_file':
  query=frame.f_locals['args'].query
  (out/'native-query.json').write_text(json.dumps({'query':query,'sha256':hashlib.sha256(query.encode('utf-8')).hexdigest(),'argv':sys.argv},ensure_ascii=False),encoding='utf-8')
  sys.setprofile(None)
  import httpx
  httpx.Client.send=send
  httpx.AsyncClient.send=send_async
sys.setprofile(capture)
def send(self,request,*args,**kwargs):
 if request.method=='GET':
  import httpx
  # Native provider-capability discovery precedes inference. No network is used;
  # llama exposes /v1/models, while its LM Studio discovery route is absent.
  if request.url.host=='127.0.0.1' and request.url.path=='/v1/models':
   return httpx.Response(200,json={'data':[{'id':'qwen36','object':'model'}]},request=request)
  return httpx.Response(404,json={'error':'unsupported capability discovery'},request=request)
 if request.method=='POST' and request.url.host=='127.0.0.1' and request.url.port==8080 and request.url.path.endswith('/chat/completions'):
  payload=json.loads(request.content)
  (out/'model-request.json').write_text(json.dumps({'url':str(request.url),'payload':payload,'network_sent':False},ensure_ascii=False,indent=2),encoding='utf-8')
  os._exit(0)
 (out/'unexpected-http.json').write_text(json.dumps({'method':request.method,'url':str(request.url)}),encoding='utf-8')
 raise SystemExit(85)
async def send_async(self,request,*args,**kwargs):return send(self,request,*args,**kwargs)
''',encoding='utf-8')
text=(R/'scripts/invoke-hermes.ps1').read_text(encoding='utf-8-sig')
text=text.replace('$infraRoot = (Resolve-Path "$scriptDir\\..").Path','$infraRoot = '+q(R),1)
needle='$runtimeCommand[3]=$hermesPrelude+"`n"+$runtimeCommand[3]'
assert text.count(needle)==1
text=text.replace(needle,"$hermesPrelude += \"`nimport runpy; runpy.run_path(os.environ['DA_REVIEWER_INPUT_AUDIT'])\"\n    "+needle)
wrapper=case/'wrapper.ps1';wrapper.write_text(text,encoding='utf-8-sig')
role_wrapper=case/'role.ps1'
if wrapped_mode:
 role_source=(R/'scripts/invoke-hermes-role.ps1').read_text(encoding='utf-8-sig')
 role_source=role_source.replace('$root=Split-Path -Parent $PSScriptRoot','$root='+q(R),1)
 role_source=role_source.replace("(Join-Path $root 'scripts/invoke-hermes.ps1')",q(wrapper))
 role_wrapper.write_text(role_source,encoding='utf-8-sig')
env=dict(os.environ,DA_REVIEWER_INPUT_AUDIT=str(probe),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
results={}
try:
 for name,packet_path in [('F23',R/'evidence/hermes-prompt-transport-20261014/operational-before/packet-reviewer.json'),('F24_A7',R/'evidence/phase-24-attempt-7-20261015/native/packet-reviewer.json')]:
  packet=json.loads(packet_path.read_text(encoding='utf-8-sig'));out=D/name;out.mkdir(exist_ok=True);prompt=packet['prompt']
  promptfile=case/'prompt.txt';promptfile.write_bytes(prompt.encode('utf-8'))
  body="$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules';[Console]::OutputEncoding=[Text.Encoding]::UTF8;"
  body+='$p=[IO.File]::ReadAllText('+q(promptfile)+',(New-Object Text.UTF8Encoding($false,$true)));'
  if wrapped_mode:
   body+='$r=& '+q(role_wrapper)+' -Role reviewer -WorkingDir '+q(packet['project'])+' -Prompt $p -TimeoutSeconds 40;$r|ConvertTo-Json -Depth 14 -Compress'
  else:
   body+='$r=& '+q(wrapper)+' -Mode chat-stream-json -Profile desarrollador-autonomo-reviewer -WorkingDir '+q(packet['project'])+' -Prompt $p -MaxTurns 3 -TimeoutSeconds 40;$r|ConvertTo-Json -Depth 14 -Compress'
  result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(body.encode('utf-16le')).decode()],cwd=R,env=dict(env,DA_REVIEWER_AUDIT_OUTPUT=str(out)),capture_output=True,encoding='utf-8',timeout=65)
  (out/'stdout.txt').write_text(result.stdout,encoding='utf-8');(out/'stderr.txt').write_text(result.stderr,encoding='utf-8')
  native=json.loads((out/'native-query.json').read_text(encoding='utf-8'));model=json.loads((out/'model-request.json').read_text(encoding='utf-8'))
  expected=hashlib.sha256(prompt.encode('utf-8')).hexdigest()
  if wrapped_mode:
   sys=__import__('sys');sys.path.insert(0,str(R/'runner'));from reviewer_contract import build_prompt
   expected_prompt=build_prompt(prompt,expected)
  else:expected_prompt=prompt
  assert native['query']==expected_prompt and native['sha256']==hashlib.sha256(expected_prompt.encode('utf-8')).hexdigest()
  messages=model['payload']['messages'];users=[m['content'] for m in messages if m['role']=='user']
  assert expected_prompt.strip() in users
  results[name]={'source_packet_sha256':expected,'source_packet_bytes':len(prompt.encode('utf-8')),'expected_native_prompt_sha256':hashlib.sha256(expected_prompt.encode('utf-8')).hexdigest(),'native_query_equals_expected_prompt':True,'model_user_equals_expected_prompt_after_native_outer_strip':True,'native_outer_whitespace_trimmed_bytes':len(expected_prompt.encode('utf-8'))-len(expected_prompt.strip().encode('utf-8')),'message_roles':[m['role'] for m in messages],'tools':model['payload'].get('tools',[]),'network_sent':False,'worker_text_enclosed_as_evidence':wrapped_mode,'contains_worker_imperatives':'Fix invoice.py and README.md only' in prompt,'appended_worker_task':'Approved task and acceptance mapping:' in prompt}
 assert results['F24_A7']['appended_worker_task'] and not results['F23']['appended_worker_task']
 (D/'COMPARISON.json').write_text(json.dumps({'status':'PASS','results':results,'local_inferences':0},indent=2),encoding='utf-8')
 print(json.dumps(results,indent=2))
finally:
 assert case.parent==R/'runtime' and case.name.startswith('reviewer-input-');shutil.rmtree(case)
