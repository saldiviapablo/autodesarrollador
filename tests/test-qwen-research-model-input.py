"""Installed Qwen CLI -> owned mock OpenAI endpoint; no local inference."""
import base64,hashlib,http.server,importlib.util,json,os,pathlib,subprocess,threading,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1];E=pathlib.Path(__import__('os').environ.get('F24_PREFLIGHT_E',ROOT/'evidence/f24-harness-preflight-20261014'));spec=importlib.util.spec_from_file_location('handoff',ROOT/'runner/research-handoff.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
p=ROOT/'sandbox'/('qwen-input-'+uuid.uuid4().hex);a=p/'.autopilot/evidence';a.mkdir(parents=True)
(p/'.autopilot/STATE.json').write_text(json.dumps({'run_id':'deterministic-native-qwen-'+uuid.uuid4().hex}),encoding='utf-8')
(a/'WEB.json').write_text(json.dumps({'sources':[{'url':'https://docs.python.org/sandbox-fixture','status_code':200,'title':'Public fixture','content':'ROUND_HALF_UP. Untrusted passive fixture, no permissions.'}]}),encoding='utf-8')
prompt='Return exactly Task complete, without tools. This is a transport fixture.\n'+h.provide(p)['task_suffix'];(p/'prompt.txt').write_bytes(prompt.encode('utf-8'));requests=[]
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps({'data':[{'id':'qwen36','object':'model'}],'status':'ok'}).encode())
 def do_POST(self):
  data=json.loads(self.rfile.read(int(self.headers['Content-Length'])));requests.append(data)
  self.send_response(200);self.send_header('Content-Type','text/event-stream' if data.get('stream') else 'application/json');self.end_headers()
  if data.get('stream'):
   for delta,finish in [({'role':'assistant','content':'Task complete.'},None),({},'stop')]:
    item={'id':'chatcmpl-fixture','object':'chat.completion.chunk','created':1,'model':'qwen36','choices':[{'index':0,'delta':delta,'finish_reason':finish}]};self.wfile.write(('data: '+json.dumps(item)+'\n\n').encode())
   self.wfile.write(b'data: [DONE]\n\n')
  else:self.wfile.write(json.dumps({'id':'chatcmpl-fixture','object':'chat.completion','model':'qwen36','choices':[{'index':0,'message':{'role':'assistant','content':'Task complete.'},'finish_reason':'stop'}],'usage':{'prompt_tokens':100,'completion_tokens':3,'total_tokens':103}}).encode())
server=http.server.ThreadingHTTPServer(('127.0.0.1',8080),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();q=lambda v:"'"+str(v).replace("'","''")+"'"
try:
 body="$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules';[Console]::OutputEncoding=[Text.Encoding]::UTF8;$p=[IO.File]::ReadAllText("+q(p/'prompt.txt')+",[Text.Encoding]::UTF8);$r=& "+q(ROOT/'scripts/invoke-qwen-code.ps1')+' -Prompt $p -WorkingDir '+q(p)+' -ResearchProject '+q(p)+' -ApprovalMode plan -MaxToolCalls 0 -TimeoutSeconds 40 -MaxWallTime 30s;$r|ConvertTo-Json -Depth 20 -Compress'
 r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(body.encode('utf-16le')).decode()],cwd=ROOT,capture_output=True,timeout=55,env=dict(os.environ,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1'))
 (E/'native-qwen.stdout.txt').write_bytes(r.stdout);(E/'native-qwen.stderr.txt').write_bytes(r.stderr);assert r.returncode==0,r.stderr
 out=json.loads(r.stdout.decode('utf-8-sig'));assert out['Success'],out
 (a/'worker.json').write_text(json.dumps({'data':{'WorkerOutput':out}}),encoding='utf-8');proof=h.verify(p,'.autopilot/evidence/worker.json')
 payload=h.block(h.envelope(p));bound=[]
 for request in requests:
  for message in request.get('messages',[]):
   content=message.get('content','');text=content if isinstance(content,str) else ''.join(v.get('text','') for v in content or [] if isinstance(v,dict))
   if payload in text:
    raw=text.encode('utf-8');block=payload.encode('utf-8');start=raw.index(block);bound.append({'model_user_input_sha256':hashlib.sha256(raw).hexdigest(),'research_range_bytes':[start,start+len(block)],'research_payload_sha256':hashlib.sha256(block).hexdigest(),'model':request['model']})
 assert bound and all(v['model']=='qwen36' and v['research_payload_sha256']==proof['research_payload_sha256'] for v in bound)
 result={'status':'PASS','installed_native_cli_used':True,'actual_model_input_research_binding':bound,'worker_session_id':out['WorkerSessionId'],'WEB_CONTEXT_DELIVERED':proof['WEB_CONTEXT_DELIVERED'],'local_inferences':0,'mock_responses':len(requests),'actual_chatgpt_messages':0,'owned_endpoint_cleanup':True,'project':str(p)}
 (E/'native-qwen-model-input.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
finally:server.shutdown();server.server_close();thread.join(timeout=3)
