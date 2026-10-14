"""Show the old PS5 native-command boundary losing prompt quotes, without inference."""
import base64, hashlib, json, pathlib, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
E=ROOT/'evidence/hermes-prompt-transport-20261014'
prompt=json.loads((E/'complex-transport.json').read_text(encoding='utf-8'))['results'][0]['native']['query']
path=ROOT/'runtime/hermes-before-prompt.txt';path.write_bytes(prompt.encode('utf-8'))
q=lambda value:"'"+str(value).replace("'","''")+"'"
try:
    body="[Console]::OutputEncoding=[Text.Encoding]::UTF8;$p=[IO.File]::ReadAllText("+q(path)+");$argsList=@('-p','desarrollador-autonomo-reviewer','chat','-q',$p,'--oneshot','-Q','--format','stream-json'); & 'C:\\Users\\Pc\\AppData\\Local\\hermes\\bin\\hermes.exe' --print-runtime-command -- @argsList"
    r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(body.encode('utf-16le')).decode()],capture_output=True,encoding='utf-8',timeout=20)
    argv=json.loads(r.stdout.lstrip('\ufeff'))
    index=argv.index('-q');received=argv[index+1]
    result={'status':'PASS','boundary':'PowerShell 5 native invocation of --print-runtime-command -- @argList','original_sha256':hashlib.sha256(prompt.encode('utf-8')).hexdigest(),'received_argument_sha256':hashlib.sha256(received.encode('utf-8')).hexdigest(),'integrity_before':received==prompt,'received_argument_count':len(argv),'received_argv':argv,'local_inferences':0}
    assert not result['integrity_before'], 'Old boundary unexpectedly preserved the complex prompt'
    (E/'before-boundary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='received_argv'}))
finally:path.unlink()
