import importlib.util,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('f',ROOT/'tests/runner-fixtures.py');f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
p=f.project('cleanup22-report-write-failure');folder=p/'.autopilot/reports';folder.rename(p/'.autopilot/reports.saved');folder.write_text('controlled obstruction');f.approve(p);r=f.start(p,45)
state=json.loads((p/'.autopilot/STATE.json').read_text(encoding='utf-8-sig'));assert state['status']=='FAILED'
matches=list((ROOT/'runtime/emergency-reports').glob(state['run_id']+'-*/runner-result.json'));assert len(matches)==1,matches
report=json.loads(matches[0].read_text(encoding='utf-8-sig'));assert report['status']=='FAILED' and report['reason'].startswith('FINAL_REPORT_WRITE_FAILED')
assert report['cleanup']['run_mutex_released'] and report['cleanup']['owned_survivors']==[] and not(p/'.autopilot/LOCK.json').exists()
result={'status':'PASS','report_directory_obstructed':True,'fallback_json_and_human':(matches[0].parent/'FINAL.md').exists(),'physical_cleanup_not_masked_by_report_failure':True,'project':str(p),'report':report}
(ROOT/'evidence/phase-22/report-failure.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'PASS','fallback':str(matches[0])}))
