"""Close an actual successful revised final audit. Never run a phase or infer."""
from pathlib import Path
import argparse,datetime,hashlib,json,shutil,subprocess,sys
import psutil
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tests'))
from endurance_controller import READ,write,sha,ps,q
from audit_secret_scan import prepare_evidence_export,scan_evidence,stage_evidence
from final_roadmap_gate import verify_final_waiver

def require_completed_phases(install):
 v=install['validation_8']
 assert all(install.get('phases_8',{}).get(str(n))=='PASS' for n in range(23,28)) and all(v.get(n)=='PASS' for n in ['f25','4h','f26','f27']),'ALL_REMAINING_PHASES_MUST_ACTUALLY_PASS'
 assert v.get('f28')==install['phases_8'].get('28')=='WAIVED_BY_USER' and install.get('F28_NOT_EXECUTED') is True,'F28_WAIVED_NEVER_PASS_REQUIRED'

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--evidence',required=True);ap.add_argument('--commit',action='store_true');a=ap.parse_args()
 install=READ(R/'config/INSTALLATION-STATE.json');require_completed_phases(install);revision=verify_final_waiver(install,R);v=install['validation_8']
 E=Path(a.evidence).resolve(strict=True);assert E.is_relative_to((R/'evidence').resolve()) and E.name.startswith('final-global-audit-')
 s=READ(E/'SUMMARY.json');checks=READ(E/'AUDIT-CHECKS.json');assert s['status']=='PASS' and not s['failure'] and len(s['tests'])>=54 and {'pilot-controller-controls','revised-final-waiver-controls','final-closure-entry-controls'}.issubset(s['tests']) and all(x['status']=='PASS' for x in s['tests'].values()) and all(checks.values()),'ACTUAL_COMPLETE_FINAL_REGRESSION_REQUIRED'
 assert READ(E/'REVISED-ROADMAP-GATE.json')==revision
 assert checks['F27-human-final-review'] and checks['F27-complete-human-file-binding'] and checks['F28-explicit-user-waiver-no-execution']
 sources=READ(E/'SOURCE-MANIFEST.json');history=READ(E/'HISTORICAL-MANIFEST.json');assert all(sha(R/n)==h for n,h in sources.items()),'FINAL_AUDIT_SOURCE_CHANGED';assert all(sha(R/n)==h for n,h in history.items()),'FINAL_HISTORY_CHANGED'
 for name,item in s['tests'].items():
  receipt=READ(E/(name+'.process.json'));assert receipt==item['process'] and receipt['status']=='PASS' and receipt['exit_code']==0 and receipt['owned_job_closed'] and receipt['owned_process_exited'] and receipt['stream_cleanup']
  ident=receipt['owned_identity']
  try:p=psutil.Process(ident['pid']);assert abs(p.create_time()-(ident['start_ticks']/1e7-62135596800))>.01,'FINAL_TEST_PROCESS_SURVIVES'
  except psutil.NoSuchProcess:pass
 for p in E.rglob('ADAPTER.json'):
  ad=READ(p);assert ad['assertions_unchanged'] and not ad['dry_run'] and sha(ad['source'])==ad['source_sha256']
 protected=READ(R/'evidence/phase-24-attempt-5-20261014/protected-final.json')['hashes'];assert all(sha(n)==h for n,h in protected.items())
 review=READ(R/v['f27_human_review_receipt']);P=Path(review['project']);assert review['method']=='HUMAN_FINAL_REVIEW' and review['decision']=='ACCEPTED' and review.get('human_confirmation_reference')
 assert all(sha(P/n)==h for n,h in review['reviewed_files'].items()) and READ(P/'.autopilot/STATE.json')['run_id']==review['native_run_id'] and READ(P/'.autopilot/STATE.json')['status']=='COMPLETED'
 tasks=[];summaries={}
 for key in ['f25','4h']:
  summaries[key]=READ(R/v[key+'_evidence']/'SUMMARY.json');tasks.extend(summaries[key]['tasks'])
 tasks.append({'project':str(P)})
 survivors=[];locks=[]
 for task in tasks:
  auto=Path(task['project'])/'.autopilot'
  if(auto/'LOCK.json').exists():locks.append(str(auto))
  assert READ(auto/'STATE.json')['status']=='COMPLETED'
  for item in READ(auto/'PROCESSES.json').get('processes',[]):
   try:
    p=psutil.Process(item['pid'])
    if abs(p.create_time()-(item['start_ticks']/1e7-62135596800))<.01:survivors.append(item)
   except psutil.NoSuchProcess:pass
 live=ps('. '+q(R/'runner/core.ps1')+';. '+q(R/'runner/cleanup.ps1')+';@{inference=(Test-RunnerInferenceReleased);ports=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object {$_.LocalPort -in @(8080,9119)}|Select-Object LocalPort,OwningProcess)}')
 assert not survivors and not locks and live['inference']=='FREE' and not live['ports'];assert not READ(R/'runtime/overnight/audit-active.json')['status']=='RUNNING';assert READ(R/'runtime/overnight/endurance-active.json')['status']!='RUNNING' and READ(R/'runtime/overnight/pilot-active.json')['status']!='RUNNING'
 f24=READ(R/'evidence/phase-24-attempt-11-20261015/FINAL.json');f27=READ(R/v['f27_evidence']/'INDEPENDENT-TECHNICAL-CLOSURE.json');state=READ(R/'runtime/overnight/STATE.json');assert len(state['new_failures'])==len(state['fixes']) and state['last_failure']['resolved'] is True,'UNRESOLVED_OVERNIGHT_DEFECT';resource_sets=[summaries[n]['resources'] for n in ['f25','4h']]+[f27['resources']]
 resources={'RAM_MIN_MIB':min([x['RAM_min_available_mib'] for x in resource_sets]+[f24['RAM_MIN_MIB']]),'PAGEFILE_MAX_GIB':max([x['pagefile_max_used_gib'] for x in resource_sets]+[f24['PAGEFILE_MAX_GIB']]),'VRAM_MAX_MIB':max([x['VRAM_max_mib'] for x in resource_sets]+[f24['VRAM_MAX_MIB']]),'LLAMA_MAX_WORKING_SET_MIB':max([x['llama_max_working_set_mib'] for x in resource_sets]+[f24['LLAMA_MAX_WORKING_SET_MIB']]),'scope':'Actual accepted F24/F25/4H/F27 measurements; original samples retained, no synthetic duration'}
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();result={'PROJECT_STATUS':'COMPLETE','scope':'REVISED_ROADMAP_EXPLICIT_USER_F28_WAIVER','F24':'PASS','F25':'PASS','4H':'PASS','F26':'PASS','F27':'PASS','F28_ORIGINAL_6_8H':'WAIVED_BY_USER','F28_NOT_EXECUTED':True,'F28_REPLACED_BY':install['F28_REPLACED_BY'],'GLOBAL_REGRESSION':'PASS','FINAL_AUDIT':'PASS','CLEANUP':'PASS','INTEGRITY':'PASS','F25_REAL_DURATION_SECONDS':summaries['f25']['duration_seconds'],'FOUR_HOUR_REAL_DURATION_SECONDS':summaries['4h']['duration_seconds'],'F27_NATIVE_DURATION_SECONDS':f27['native_task_duration_seconds'],'F28_REAL_DURATION_SECONDS':None,'TOTAL_NEW_FAILURES_FOUND':len(state['new_failures']),'TOTAL_FAILURES_FIXED':len(state['fixes']),'failure_count_scope':'Unique verified causes in overnight registry, separate from expected negative cases and bounded native role incidents','RUNNER':'PASS','WATCHDOG':'PASS','SUPERVISOR':'PASS','WORKER':'PASS','REVIEWER':'PASS','COMPLETION_GATE':'PASS','CHATGPT':'PASS_FROM_ACTUAL_F24_F25_4H_IDEMPOTENT_CONSULTATIONS_NO_NEW_SEND','RECOVERY':'PASS','RESOURCES':resources,'remaining_gate_exemptions':['Original F28 real6–8h explicitly waived; longest accepted continuous run14781.278687s/26tasks'],'PUSH_PERFORMED':False,'at':stamp}
 shutil.copyfile(__file__,E/'CLOSURE-SCRIPT.py.txt');write(E/'INDEPENDENT-FINAL-CLOSURE.json',{'status':'PASS','source_files':len(sources),'historical_files':len(history),'protected_components':len(protected),'regression_suites':len(s['tests']),'audit_checks':len(checks),'cleanup':live,'survivors':survivors,'locks':locks,'revised_roadmap':revision,'no_native_or_ledger_mutation':True,'closure_script_sha256':sha(E/'CLOSURE-SCRIPT.py.txt')});write(E/'PROJECT-RESULT.json',result)
 prepare_evidence_export(E);scan=scan_evidence(E);write(E/'SECRET-SCAN.json',scan);assert scan['status']=='PASS'
 B=R/'backups'/('final-close-'+E.name);B.mkdir(exist_ok=False);names=['00-README.md','07-ROADMAP.md','MANIFEST.md','docs/IMPLEMENTATION-STATUS.md','config/INSTALLATION-STATE.json','docs/OVERNIGHT-RESUME.md']
 for n in names:
  dest=B/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/n,dest)
 if (R/'docs/PROJECT-FINAL-REPORT.md').exists():shutil.copyfile(R/'docs/PROJECT-FINAL-REPORT.md',B/'PROJECT-FINAL-REPORT.previous.md')
 report='docs/PROJECT-FINAL-REPORT.md';(R/report).write_text('# Proyecto completo bajo roadmap revisado\n\nLa exención humana de F28 no se presenta como una prueba PASS de6–8h. Todos los demás gates finales están aprobados, incluida la revisión humana real del piloto.\n\n```json\n'+json.dumps(result,ensure_ascii=False,indent=2)+'\n```\n\nEvidence: '+E.relative_to(R).as_posix()+'/. Full original sources/raw process streams/manifests/adapters, source/history/protected hashes and independent closure remain auditable. Actual hardware minima/maxima and native timeout/restart history are preserved; accepted4H had two ordinary Completion Gate corrections, and F27 consumed2 normal Worker restarts before completion. No F24/F25/4H/F26 E2E or duration test was repeated for final closure. Final validation is a separate current-system regression, with no local inference or ChatGPT send. No dependency/software/driver/policy update, production action or push. Historical FAILs and unknown/no-resend consultations remain unchanged.\n',encoding='utf-8')
 import re
 for n in names[:4]:
  p=R/n;t=p.read_text(encoding='utf-8-sig')
  if n=='00-README.md':t=re.sub(r'^Macrofase 8:.*$','Macrofase 8:  PASS bajo roadmap revisado; F23–F27/4H/regresión/auditoría final PASS; F28 WAIVED_BY_USER / NOT_EXECUTED',t,count=1,flags=re.M)
  if n=='07-ROADMAP.md':t=re.sub(r'^\| \*\*Macrofase 8\*\*.*$','| **Macrofase 8** | Validación Final revisada | F23–F27/4H/regresión/auditoría PASS; F28 WAIVED_BY_USER / NOT_EXECUTED | **PASS bajo roadmap revisado** |',t,count=1,flags=re.M)
  if n=='MANIFEST.md':t=re.sub(r'^- \*\*Macrofase 8 \(Validación Final.*$','- **Macrofase 8 (Validación Final): PASS bajo roadmap revisado**; F23–F27/4H/regresión/auditoría PASS; F28 **WAIVED_BY_USER / NOT_EXECUTED**',t,count=1,flags=re.M)
  if n=='docs/IMPLEMENTATION-STATUS.md':t=re.sub(r'^\| \*\*Macrofase 8\*\*.*$','| **Macrofase 8** | Validación Final revisada | **PASS bajo roadmap revisado** | '+report+'; F28 WAIVED_BY_USER / NOT_EXECUTED |',t,count=1,flags=re.M)
  p.write_text(t.rstrip()+'\n\n## Cierre final bajo roadmap revisado — '+stamp+'\n\nPROJECT_STATUS=COMPLETE; todos los gates restantes PASS; F28 original WAIVED_BY_USER/NOT_EXECUTED, nunca PASS. '+report+'\n',encoding='utf-8')
 install.update(project_status='COMPLETE',project_status_scope=result['scope'],final_report=report);install['macrophases']['8']='PASS';install['validation_8'].update(status='PASS',final_audit='PASS',regression_gate_final='PASS',final_evidence=E.relative_to(R).as_posix(),final_cleanup='PASS',final_integrity='PASS');install['updated_at']=stamp;write(R/'config/INSTALLATION-STATE.json',install)
 state.update(status='COMPLETED',last_completed='PROJECT COMPLETE UNDER REVISED ROADMAP',active_phase='COMPLETE',active_run=None,active_task=None,current_native_project=None,controller_pid=None,tool_session_id=None,next_action='STOP. Never execute waived F28. No push.',project_status='COMPLETE',updated_at=stamp);write(R/'runtime/overnight/STATE.json',state);write(R/'runtime/overnight/checkpoints/PROJECT-COMPLETE.json',state)
 blocked=R/'runtime/overnight/BLOCKED.md'
 if blocked.exists():
  shutil.copyfile(blocked,E/'PRIOR-BLOCKED-NOTICE.md');blocked.write_text(blocked.read_text(encoding='utf-8').rstrip()+'\n\nRESOLVED: actual human final review and revised final regression/audit PASS; PROJECT COMPLETE at '+stamp+'\n',encoding='utf-8')
 with (R/'runtime/overnight/EVENTS.jsonl').open('a',encoding='utf-8') as h:h.write(json.dumps({'event':'PROJECT_COMPLETE_UNDER_REVISED_ROADMAP','at':stamp,'evidence':str(E),'F28':'WAIVED_BY_USER_NOT_EXECUTED'})+'\n')
 (R/'docs/OVERNIGHT-RESUME.md').write_text('# Project complete — revised roadmap\n\n```json\n'+json.dumps(state,ensure_ascii=False,indent=2)+'\n```\n\nSTOP. All remaining authorized gates PASS. Original F28 WAIVED_BY_USER / NOT_EXECUTED, not PASS. '+report+'\n',encoding='utf-8')
 if a.commit:
  subprocess.run(['git','add','--',*names,report],cwd=R,check=True);excluded=stage_evidence(E);subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
  for p in E.rglob('*'):
   if p.is_file() and p.relative_to(E).as_posix() not in excluded:assert hashlib.sha256(subprocess.check_output(['git','show',':'+p.relative_to(R).as_posix()],cwd=R)).hexdigest()==sha(p)
  subprocess.run(['git','commit','-q','-m','docs: close revised roadmap project after final audit and regression'],cwd=R,check=True);assert not subprocess.check_output(['git','status','--porcelain=v1'],cwd=R,text=True).strip()
 print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
