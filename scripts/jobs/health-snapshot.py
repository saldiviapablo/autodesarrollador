"""Offline, bounded no-agent job: emits project state, never mutates it."""
import json,pathlib
p=pathlib.Path.cwd()/'.autopilot/STATE.json'
state=json.loads(p.read_text(encoding='utf-8-sig'))
print(json.dumps({'event':'HEALTH_SNAPSHOT','run_id':state['run_id'],'status':state['status'],'local_inferences':0}))
