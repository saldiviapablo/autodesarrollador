"""Final closure admission negatives; never create a report, run or approval."""
from pathlib import Path
import copy,importlib.util,sys,unittest
from unittest.mock import patch
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('final_close_entry_unit',R/'tests/close-final-validation.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class ClosureEntry(unittest.TestCase):
 def install(self):return {'phases_8':{**dict.fromkeys(map(str,range(23,28)),'PASS'),'28':'WAIVED_BY_USER'},'validation_8':{**dict.fromkeys(['f25','4h','f26','f27'],'PASS'),'f28':'WAIVED_BY_USER'},'F28_NOT_EXECUTED':True,'unit_fixture_only':True}
 def test_complete_status_header_only(self):module.require_completed_phases(self.install())
 def test_f27_human_pending_denied(self):
  v=self.install();v['validation_8']['f27']='TECHNICAL_PASS_AWAITING_HUMAN_REVIEW'
  with self.assertRaisesRegex(AssertionError,'ALL_REMAINING_PHASES_MUST_ACTUALLY_PASS'):module.require_completed_phases(v)
 def test_phase_index_pending_denied(self):
  v=self.install();v['phases_8']['27']='PENDING_HUMAN_FINAL_REVIEW'
  with self.assertRaisesRegex(AssertionError,'ALL_REMAINING_PHASES_MUST_ACTUALLY_PASS'):module.require_completed_phases(v)
 def test_f26_missing_denied(self):
  v=self.install();v['validation_8']['f26']='NOT_RUN'
  with self.assertRaisesRegex(AssertionError,'ALL_REMAINING_PHASES_MUST_ACTUALLY_PASS'):module.require_completed_phases(v)
 def test_prior_f24_failure_denied(self):
  v=self.install();v['phases_8']['24']='FAIL'
  with self.assertRaisesRegex(AssertionError,'ALL_REMAINING_PHASES_MUST_ACTUALLY_PASS'):module.require_completed_phases(v)
 def test_f28_pass_denied(self):
  v=self.install();v['validation_8']['f28']='PASS'
  with self.assertRaisesRegex(AssertionError,'F28_WAIVED_NEVER_PASS_REQUIRED'):module.require_completed_phases(v)
 def test_f28_executed_denied(self):
  v=self.install();v['F28_NOT_EXECUTED']=False
  with self.assertRaisesRegex(AssertionError,'F28_WAIVED_NEVER_PASS_REQUIRED'):module.require_completed_phases(v)
 def test_pending_human_cannot_write_or_commit(self):
  v=self.install();v['validation_8']['f27']='PENDING_HUMAN_FINAL_REVIEW'
  with patch.object(module,'READ',return_value=v),patch.object(sys,'argv',['close-final-validation.py','--evidence','NONEXISTENT_UNIT_ONLY','--commit']),patch.object(module,'write') as write,patch.object(module.subprocess,'run') as run:
   with self.assertRaisesRegex(AssertionError,'ALL_REMAINING_PHASES_MUST_ACTUALLY_PASS'):module.main()
   write.assert_not_called();run.assert_not_called()
if __name__=='__main__':unittest.main(verbosity=2)
