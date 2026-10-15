"""Validate the user's explicit F28 waiver; never turn a waived gate into PASS."""
from pathlib import Path
import hashlib,json

REPLACEMENT='CERTIFIED_4H_ENDURANCE + F27_REAL_PILOT + FINAL_REGRESSION'
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verify_final_waiver(install,root):
 root=Path(root).resolve(strict=True);v=install['validation_8']
 assert v.get('f28')=='WAIVED_BY_USER' and install.get('phases_8',{}).get('28')=='WAIVED_BY_USER','F28_MUST_BE_WAIVED_NEVER_PASS'
 assert install.get('F28_ORIGINAL_6_8H')=='WAIVED_BY_USER' and install.get('F28_NOT_EXECUTED') is True and install.get('F28_REPLACED_BY')==REPLACEMENT,'EXPLICIT_REVISED_ROADMAP_REQUIRED'
 path=(root/v['f28_waiver_evidence']).resolve(strict=True)
 assert path.is_relative_to((root/'evidence').resolve()),'WAIVER_EVIDENCE_SCOPE_DENIED'
 assert sha(path)==v['f28_waiver_sha256'],'WAIVER_EVIDENCE_HASH_CHANGED'
 w=read(path)
 assert w.get('method')=='EXPLICIT_USER_OBJECTIVE_REVISION' and w.get('user_instruction'),'DIRECT_USER_WAIVER_REQUIRED'
 assert w.get('F28_ORIGINAL_6_8H')=='WAIVED_BY_USER' and w.get('F28_NOT_EXECUTED') is True and w.get('F28_REPLACED_BY')==REPLACEMENT,'WAIVER_RECEIPT_INCONSISTENT'
 e=(root/v['4h_evidence']).resolve(strict=True)
 assert e.is_relative_to((root/'evidence').resolve()),'FOUR_HOUR_EVIDENCE_SCOPE_DENIED'
 s=read(e/'SUMMARY.json');closure=read(e/'INDEPENDENT-CLOSURE.json')
 assert v.get('4h')=='PASS' and s['status']=='PASS' and s['duration_seconds']>=14400 and all(s['gates'].values()) and s['cleanup'] and s['integrity'] and closure['status']=='PASS','ACTUAL_CERTIFIED_FOUR_HOURS_REQUIRED'
 assert s['stage_id']==w['accepted_4h_stage_id'] and sha(e/'SUMMARY.json')==w['accepted_4h_summary_sha256'],'USER_WAIVER_NOT_BOUND_TO_ACCEPTED_4H'
 assert s['duration_seconds']==w['accepted_4h_duration_seconds'] and len(s['tasks'])==w['accepted_4h_completed_tasks']==26,'ACCEPTED_4H_DURATION_OR_TASKS_CHANGED'
 assert not list((root/'evidence').glob('endurance-f28-*')) and not list((root/'sandbox').glob('endurance-f28-*')),'F28_ALREADY_CREATED_OR_EXECUTED'
 active=root/'runtime/overnight/endurance-active.json'
 assert not active.exists() or read(active).get('stage')!='F28','F28_CONTROLLER_MUST_NOT_EXIST'
 return {'explicit_user_waiver':True,'original_F28_not_marked_PASS':True,'F28_NOT_EXECUTED':True,'accepted_real_4h_seconds':s['duration_seconds'],'accepted_real_4h_tasks':len(s['tasks']),'waiver_sha256':sha(path),'replacement':REPLACEMENT}
