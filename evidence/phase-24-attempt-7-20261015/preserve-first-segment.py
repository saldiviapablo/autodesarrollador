"""Read-only archive observer; never controls Runner, inference, browser or state."""
from pathlib import Path
import hashlib,json,time
R=Path(__file__).resolve().parents[2];E=R/'evidence/phase-24-attempt-7-20261015'
P=Path(json.loads((E/'fixture.json').read_text())['project']);A=P/'.autopilot'
def read(p):
 try:return json.loads(p.read_text(encoding='utf-8-sig'))
 except (OSError,ValueError):return {}
deadline=time.monotonic()+2700
while time.monotonic()<deadline:
 checks=read(A/'evidence/checks.json')
 if all(checks.get(group) and all(item['status']=='PASS' for item in checks[group]) for group in ['tests','builds']):
  target=E/'pre-recovery-native';target.mkdir(exist_ok=False);files={}
  for folder in ['logs','evidence']:
   for p in (A/folder).rglob('*'):
    if p.is_file():
     q=target/p.relative_to(A);q.parent.mkdir(parents=True,exist_ok=True);data=p.read_bytes();q.write_bytes(data);files[p.relative_to(A).as_posix()]=hashlib.sha256(data).hexdigest()
  for name in ['STATE.json','EVENTS.jsonl','PROCESSES.json']:
   p=A/name;q=target/name;data=p.read_bytes();q.write_bytes(data);files[name]=hashlib.sha256(data).hexdigest()
  (target/'MANIFEST.json').write_text(json.dumps({'source':str(A),'at_unix':time.time(),'sha256':files,'read_only_observer':True},indent=2),encoding='utf-8')
  print('FIRST_SEGMENT_ARCHIVED '+str(len(files)),flush=True);break
 if (E/'SUMMARY.json').exists():print('FIRST_SEGMENT_NOT_REACHED',flush=True);break
 time.sleep(.2)
