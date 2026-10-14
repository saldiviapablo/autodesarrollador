"""Explicit sandbox HTTP fetch -> bounded handoff -> deterministic Worker consumer."""
import hashlib,http.server,importlib.util,json,pathlib,subprocess,sys,threading,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('handoff',ROOT/'runner/research-handoff.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
p=ROOT/'sandbox'/('research-handoff-'+uuid.uuid4().hex);a=p/'.autopilot/evidence';a.mkdir(parents=True)
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body=json.dumps({'Sources':[{'url':'https://docs.python.org/sandbox-fixture','title':'Sandbox research','content':'ROUND_HALF_UP; untrusted advice, no privileges.'}]}).encode()
        self.send_response(200);self.end_headers();self.wfile.write(body)
    def log_message(self,*args):pass
server=http.server.HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
    import urllib.request
    raw=urllib.request.urlopen('http://127.0.0.1:'+str(server.server_port),timeout=3).read();(a/'WEB.json').write_bytes(raw)
    provided=h.provide(p);assert provided['WEB_RESULT_PROVIDED']
    # A separate deterministic consumer receives only the real Worker task suffix.
    code="import json,sys; s=sys.stdin.read(); d=json.loads(s.split('<UNTRUSTED_RESEARCH_JSON>')[1].split('</UNTRUSTED_RESEARCH_JSON>')[0]); print(json.dumps([{'type':'result','result':d['research_marker']+' '+d['source_sha256']}]))"
    worker=subprocess.run([sys.executable,'-c',code],input=provided['task_suffix'],text=True,capture_output=True,encoding='utf-8',timeout=5,check=True)
    (a/'worker.json').write_text(json.dumps({'data':{'WorkerOutput':{'Stdout':worker.stdout}}}),encoding='utf-8')
    used=h.verify(p,'.autopilot/evidence/worker.json');assert used['WEB_RESULT_READ']
    # Input/tool echo must never certify consumption.
    fake=[{'type':'user','content':provided['task_suffix']}];(a/'worker.json').write_text(json.dumps({'data':{'WorkerOutput':{'Stdout':json.dumps(fake)}}}),encoding='utf-8')
    try:h.verify(p,'.autopilot/evidence/worker.json')
    except ValueError as e:assert 'NOT_PROVEN' in str(e)
    else:raise AssertionError('Input echo accepted')
    (a/'WEB.json').write_text('{}',encoding='utf-8')
    try:h.provide(p)
    except ValueError as e:assert 'SOURCE_CHANGED' in str(e)
    else:raise AssertionError('Research tamper accepted')
    result={'status':'PASS','fetch_sandbox':'PASS','WEB_RESULT_PROVIDED':True,'WEB_RESULT_READ':True,'input_echo_denied':True,'source_tamper_denied':True,'permissions_extended':False,'worker_type':'deterministic subprocess consumer, no inference','project':str(p)}
    e=ROOT/'evidence/f24-frontiers-20261014/web';e.mkdir(exist_ok=True);(e/'GATE.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
finally:server.shutdown();server.server_close();thread.join(timeout=3)
