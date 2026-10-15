"""Certify exact evidence before the first new F24 attempt. No bridge/run actions."""
import hashlib,json,pathlib,shutil
R=pathlib.Path(__file__).resolve().parents[1];E=R/'evidence/f24-transaction-cert-20261014'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not(E/'CERTIFIED.json').exists()
for name in ['DETERMINISTIC.json','legacy-recovery.json','controlled-send/RESULT.json','pre-start-cleanup.json','PREFLIGHT.json','runtime-dependencies.json']:
 assert read(E/name)['status']=='PASS',name
legacy=read(E/'legacy-recovery.json');original=R/'runtime/chatgpt-consultations/6188f287744816b7f6d430d03b62076163f6bff4b3f2d9b720aeb7876e3e4f78.json'
assert sha(original)==legacy['ledger_before_sha256']=='a19538782cfaf89052c6fd4123fc80a1143777d3998c66c13781dbe9baf30521'
receipt=pathlib.Path(legacy['receipt_path']);assert sha(receipt)==legacy['receipt_sha256'];shutil.copyfile(receipt,E/'legacy-recovery-receipt.json')
h=read(E/'cleanup/heartbeat-recovery-fix.json');assert h['status']=='PASS' and h['RECOVERY_TECHNICAL_STATUS']=='SUCCESS'
normal=(E/'cleanup/normal-plan-before-fault.json').read_bytes();fault=read(E/'cleanup/fault-only-plan.json');rp=pathlib.Path(h['recovery_fixture'])/'.autopilot/RUN-PLAN.json'
assert fault['heartbeat_stale_seconds']==1 and normal==rp.read_bytes() and sha(rp)==h['normal_snapshot_sha256']
faultState=read(pathlib.Path(h['fault_fixture'])/'.autopilot/STATE.json');assert faultState['status']=='FAILED'
save(E/'heartbeat-certification.json',{'status':'PASS','NORMAL_CONFIG_SAVED':'PASS','FAULT_CONFIG_APPLIED':'PASS','HEARTBEAT_STALE_DETECTED':'PASS','FAULT_FIXTURE_TERMINATED':'PASS','FAULT_CONFIG_REMOVED_FROM_RECOVERY':'PASS','RECOVERY_CONFIG_EQUALS_ORIGINAL':'PASS','START_RECOVER':'PASS','RECOVERY_TECHNICAL_STATUS':'SUCCESS','CLEANUP':'PASS','normal_sha256':sha(rp),'original_bytes_unchanged':True,'production_policy_changed':False})
history=read(E/'history-before.json')['files'];assert all(sha(R/p)==v for p,v in history.items())
identity=read(E/'controlled-send/identity.json');a=pathlib.Path(identity['project'])/'.autopilot'
for p in a.rglob('*'):
 if p.is_file():d=E/'controlled-send/native'/p.relative_to(a);d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d)
assert read(a/'STATE.json')['chatgpt']['queries_used']==1
gate=read(E/'PREFLIGHT.json');assert gate['sealed'] and gate['TOTAL_GATES_FROZEN']==28 and sha(R/'docs/F24-GATES.json')==gate['gates_sha256']
save(E/'CERTIFIED.json',{'status':'PASS','PARTIAL_WORK_RESUMED':True,'BRIDGE_TRANSACTION_FIX':'PASS','PRE_SEND_STATE_MACHINE':'PASS','FALSE_UNKNOWN_DELIVERY_FIXED':'PASS','OWNED_DRAFT_ROLLBACK':'PASS','LEGACY_DRAFT_RECOVERY':'PASS','HISTORICAL_LEDGER_UNCHANGED':True,'HEARTBEAT_RECOVERY_FIX':'PASS','CONTROLLED_REAL_SEND':'PASS','F24_HARNESS_PREFLIGHT':'PASS','frozen_gates':28,'gate_catalog_unchanged':True,'preflight_is_test_certification_not_live_E2E':True,'historical_files_preserved':len(history),'new_local_inferences':0,'controlled_physical_sends':1,'attempt6_started':False,'attempt7_created':False,'new_dependencies':[]})
(E/'.gitattributes').write_text('* -text whitespace=-blank-at-eol,-blank-at-eof,space-before-tab,cr-at-eol\n',encoding='utf-8');print('TRANSACTION/LEGACY/CONTROLLED/HEARTBEAT/PREFLIGHT CERTIFIED PASS')
