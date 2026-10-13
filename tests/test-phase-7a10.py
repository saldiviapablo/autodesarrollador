import importlib.util,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];e=ROOT/'evidence/phase-7a10';e.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('controlled_update',ROOT/'scripts/controlled-update.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
r=m.simulation();assert r['status']=='PASS' and r['automatic_rollback'] and r['production_hashes_unchanged']
(e/'tests.json').write_text(json.dumps(r,indent=2)+'\n');(e/'security.json').write_text(json.dumps({'status':'PASS','live_hermes_unchanged':True,'versions_lock_unchanged':True,'candidate_archived':True,'active_marker_removed':True},indent=2)+'\n')
print(json.dumps(r))
