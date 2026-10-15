"""Unit fixtures only: no actual phase, waiver, human review or model execution."""
from pathlib import Path
import copy,json,uuid,unittest
from unittest.mock import patch
import final_roadmap_gate as gate

R=Path(__file__).resolve().parents[1]
class RevisedGate(unittest.TestCase):
 def setUp(self):
  self.root=R/'logs/overnight'/('revised-gate-unit-'+uuid.uuid4().hex);self.e=self.root/'evidence/four';self.e.mkdir(parents=True);(self.root/'sandbox').mkdir()
  self.summary={'status':'PASS','stage_id':'unit-only-4h','duration_seconds':14781.0,'tasks':[{}]*26,'gates':{'labelled_unit':True},'cleanup':True,'integrity':True}
  self.put(self.e/'SUMMARY.json',self.summary);self.put(self.e/'INDEPENDENT-CLOSURE.json',{'status':'PASS','unit_fixture_only':True})
  self.waiver={'method':'EXPLICIT_USER_OBJECTIVE_REVISION','user_instruction':'UNIT FIXTURE, not a user authorization','F28_ORIGINAL_6_8H':'WAIVED_BY_USER','F28_NOT_EXECUTED':True,'F28_REPLACED_BY':gate.REPLACEMENT,'accepted_4h_stage_id':'unit-only-4h','accepted_4h_summary_sha256':gate.sha(self.e/'SUMMARY.json'),'accepted_4h_duration_seconds':14781.0,'accepted_4h_completed_tasks':26,'unit_fixture_only':True}
  self.path=self.root/'evidence/unit-waiver.json';self.put(self.path,self.waiver)
  self.install={'validation_8':{'f28':'WAIVED_BY_USER','4h':'PASS','4h_evidence':'evidence/four','f28_waiver_evidence':'evidence/unit-waiver.json','f28_waiver_sha256':gate.sha(self.path)},'phases_8':{'28':'WAIVED_BY_USER'},'F28_ORIGINAL_6_8H':'WAIVED_BY_USER','F28_NOT_EXECUTED':True,'F28_REPLACED_BY':gate.REPLACEMENT}
 def put(self,p,value):p.write_text(json.dumps(value),encoding='utf-8')
 def save_waiver(self):self.put(self.path,self.waiver);self.install['validation_8']['f28_waiver_sha256']=gate.sha(self.path)
 def deny(self,pattern):
  with self.assertRaisesRegex(AssertionError,pattern):gate.verify_final_waiver(self.install,self.root)
 def test_explicit_bound_replacement_unit_only(self):
  result=gate.verify_final_waiver(self.install,self.root);self.assertTrue(result['F28_NOT_EXECUTED']);self.assertTrue(result['original_F28_not_marked_PASS'])
 def test_original_f28_cannot_be_pass(self):self.install['phases_8']['28']='PASS';self.deny('F28_MUST_BE_WAIVED_NEVER_PASS')
 def test_missing_replacement_denied(self):del self.install['F28_REPLACED_BY'];self.deny('EXPLICIT_REVISED_ROADMAP_REQUIRED')
 def test_automatic_waiver_denied(self):self.waiver['method']='AUTOMATIC';self.save_waiver();self.deny('DIRECT_USER_WAIVER_REQUIRED')
 def test_missing_user_instruction_denied(self):del self.waiver['user_instruction'];self.save_waiver();self.deny('DIRECT_USER_WAIVER_REQUIRED')
 def test_changed_receipt_hash_denied(self):self.path.write_text('{}');self.deny('WAIVER_EVIDENCE_HASH_CHANGED')
 def test_changed_accepted_four_hour_hash_denied(self):self.waiver['accepted_4h_summary_sha256']='0'*64;self.save_waiver();self.deny('USER_WAIVER_NOT_BOUND_TO_ACCEPTED_4H')
 def test_short_duration_denied(self):self.summary['duration_seconds']=14399;self.put(self.e/'SUMMARY.json',self.summary);self.deny('ACTUAL_CERTIFIED_FOUR_HOURS_REQUIRED')
 def test_failed_four_hour_gate_denied(self):self.summary['gates']['labelled_unit']=False;self.put(self.e/'SUMMARY.json',self.summary);self.deny('ACTUAL_CERTIFIED_FOUR_HOURS_REQUIRED')
 def test_any_created_f28_denied(self):(self.root/'evidence/endurance-f28-unit-only').mkdir();self.deny('F28_ALREADY_CREATED_OR_EXECUTED')
 def test_night_entry_forbidden_before_any_constructor(self):
  import importlib.util
  spec=importlib.util.spec_from_file_location('night_waiver_unit',R/'tests/night-pilot-controller.py');night=importlib.util.module_from_spec(spec);spec.loader.exec_module(night)
  with patch.object(night,'READ',return_value=self.install),patch.object(night,'Night') as constructor:
   with self.assertRaisesRegex(AssertionError,'F28_FORBIDDEN_BY_EXPLICIT_USER_REVISION'):night.main()
   constructor.assert_not_called()
if __name__=='__main__':unittest.main(verbosity=2)
