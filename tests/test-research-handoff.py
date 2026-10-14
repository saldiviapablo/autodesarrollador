"""A-J: actual wrapper/process argv dispatch, no inference or model echo gate."""
import base64,copy,hashlib,http.server,importlib.util,json,os,pathlib,subprocess,threading,uuid,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('handoff',ROOT/'runner/research-handoff.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
E=pathlib.Path(os.environ.get('F24_PREFLIGHT_E',str(ROOT/'evidence/f24-harness-preflight-20261014')))/'web';E.mkdir(parents=True,exist_ok=True)
p=ROOT/'sandbox'/('research-dispatch-'+uuid.uuid4().hex);a=p/'.autopilot/evidence';a.mkdir(parents=True)
(p/'.autopilot/STATE.json').write_text(json.dumps({'run_id':'deterministic-'+uuid.uuid4().hex}),encoding='utf-8')
class Handler(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
  body=b'Official sandbox research: ROUND_HALF_UP, no privileges.';self.send_response(200);self.end_headers();self.wfile.write(body)
 def log_message(self,*args):pass
server=http.server.HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();cases={}
q=lambda s:"'"+str(s).replace("'","''")+"'"
try:
 with urllib.request.urlopen('http://127.0.0.1:'+str(server.server_port),timeout=3) as response:
  source={'sources':[{'url':'https://docs.python.org/sandbox-fixture','status_code':response.status,'content':response.read().decode(),'title':'Sandbox research'}]}
 (a/'WEB.json').write_text(json.dumps(source),encoding='utf-8');original_web=(a/'WEB.json').read_bytes()
 provided=h.provide(p);env=h.envelope(p);original_env=(a/'WEB-HANDOFF.json').read_bytes()
 prompt='Task: "quoted" áéíóú ñ\nC:\\folder with spaces\\\n'+provided['task_suffix']+'\nDo the approved task.'
 prompt_file=p/'prompt.txt';prompt_file.write_bytes(prompt.encode('utf-8'))
 fake=p/'capture.cjs';fake.write_text("const c=require('crypto'),a=process.argv;const session=a[a.indexOf('--session-id')+1];console.log(JSON.stringify([{type:'system',subtype:'init',session_id:session,received_input_sha256:c.createHash('sha256').update(a.at(-1),'utf8').digest('hex')},{type:'result',session_id:session,result:'Task complete; no research echo.'}]));",encoding='utf-8')
 text=(ROOT/'scripts/invoke-qwen-code.ps1').read_text(encoding='utf-8-sig')
 text=text.replace('$infraRoot = (Resolve-Path "$scriptDir\\..").Path','$infraRoot = '+q(ROOT),1)
 needle='$cliEntry = "C:\\Users\\Pc\\AppData\\Roaming\\npm\\node_modules\\@qwen-code\\qwen-code\\cli-entry.js"'
 assert text.count(needle)==1;text=text.replace(needle,'$cliEntry = '+q(fake),1)
 wrapper=p/'wrapper.ps1';wrapper.write_text(text,encoding='utf-8-sig')
 body="$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules';[Console]::OutputEncoding=[Text.Encoding]::UTF8;$p=[IO.File]::ReadAllText("+q(prompt_file)+",[Text.Encoding]::UTF8);$r=& "+q(wrapper)+' -Prompt $p -WorkingDir '+q(p)+' -ResearchProject '+q(p)+' -TimeoutSeconds 20;$r|ConvertTo-Json -Depth 15 -Compress'
 run=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(body.encode('utf-16le')).decode()],capture_output=True,encoding='utf-8',timeout=40)
 assert run.returncode==0,run.stderr
 output=json.loads(run.stdout.lstrip('\ufeff'));assert output['Success'],output
 events=json.loads(output['Stdout']);assert events[0]['received_input_sha256']==hashlib.sha256(prompt.encode()).hexdigest()
 worker_file=a/'worker.json';worker={'data':{'WorkerOutput':output}};worker_file.write_text(json.dumps(worker),encoding='utf-8')
 proof=h.verify(p,'.autopilot/evidence/worker.json');assert proof['WEB_CONTEXT_DELIVERED'];cases['A_fetch_and_actual_input']='PASS';cases['F_no_model_echo_required']='PASS';cases['J_inline_no_read_file']='PASS'
 (E/'actual-wrapper-output.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
 (E/'dispatch-proof.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
 def deny(name,action):
  try:action()
  except (ValueError,KeyError,OSError):cases[name]='PASS'
  else:raise AssertionError('Unexpected ALLOW: '+name)
 def prepared(text):
  dispatch=str(uuid.uuid4());session=str(uuid.uuid4());ip,_=h.dispatch_paths(p,dispatch);ip.parent.mkdir();ip.write_text(text,encoding='utf-8');return h.prepare(p,dispatch,session)
 deny('B_missing_research',lambda:prepared('No research in actual input'))
 bad=copy.deepcopy(env);bad['source_sha256']='0'*64;(a/'WEB-HANDOFF.json').write_text(json.dumps(bad),encoding='utf-8');deny('C_wrong_research_sha',lambda:prepared(prompt));(a/'WEB-HANDOFF.json').write_bytes(original_env)
 (a/'WEB.json').write_bytes(original_web+b' ');deny('D_source_changed_before_dispatch',lambda:prepared(prompt));(a/'WEB.json').write_bytes(original_web)
 deny('E_truncated_input',lambda:prepared(prompt.replace(h.block(env),h.block(env)[:-10])))
 receipt_path=h.dispatch_paths(p,output['ResearchDispatchId'])[1];receipt=receipt_path.read_bytes();j=h.read(receipt_path);j['phase']='PREPARED';h.atomic(receipt_path,j);deny('G_worker_never_started',lambda:h.validate(p,'.autopilot/evidence/worker.json'));receipt_path.write_bytes(receipt)
 wrong=copy.deepcopy(worker);wrong['data']['WorkerOutput']['WorkerSessionId']=str(uuid.uuid4());worker_file.write_text(json.dumps(wrong),encoding='utf-8');deny('H_other_worker_session',lambda:h.validate(p,'.autopilot/evidence/worker.json'));worker_file.write_text(json.dumps(worker),encoding='utf-8')
 bad=copy.deepcopy(env);bad['mode']='file';(a/'WEB-HANDOFF.json').write_text(json.dumps(bad),encoding='utf-8');deny('I_file_mode_without_actual_access',lambda:prepared(prompt));(a/'WEB-HANDOFF.json').write_bytes(original_env)
 assert h.validate(p,'.autopilot/evidence/worker.json')['WEB_CONTEXT_DELIVERED']
 result={'status':'PASS','cases':cases,'total_cases':len(cases),'actual_process_boundary':'Production wrapper copy; only CLI target replaced with deterministic argv capture','inferences':0,'actual_input_utf8_sha_matches':True,'model_echo_required':False,'project':str(p),'no_permissions_added':True}
 (E/'GATE.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
finally:server.shutdown();server.server_close();thread.join(timeout=3)
