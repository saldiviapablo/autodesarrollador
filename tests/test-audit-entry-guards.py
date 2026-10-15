"""Entry guard unit checks only: no audit runs, native roles, browser or ledger."""
from pathlib import Path
import importlib.util,json,sys,unittest,uuid
from unittest.mock import patch
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('audit_entry_unit',BASE/'global-audit.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
R=module.R
class Guards(unittest.TestCase):
 def test_bridge_fixture_is_source_bound_and_fresh(self):
  case=R/'logs/overnight'/('audit-bridge-unit-'+uuid.uuid4().hex);case.mkdir()
  module.prepare_bridge_integrity_fixture(case)
  record=json.loads((case/'integrity-before.json').read_text(encoding='utf-8'))
  self.assertEqual(record['protected']['tools/chatgpt-bridge.js'],module.sha(R/'tools/chatgpt-bridge.js'))
  with self.assertRaisesRegex(AssertionError,'FRESH_BRIDGE_INTEGRITY_FIXTURE_REQUIRED'):module.prepare_bridge_integrity_fixture(case)
 def test_unapproved_bridge_cannot_seed_fixture(self):
  case=R/'logs/overnight'/('audit-bridge-unit-'+uuid.uuid4().hex);case.mkdir()
  with patch.object(module.subprocess,'check_output',return_value=b'unapproved unit bytes'):
   with self.assertRaisesRegex(AssertionError,'APPROVED_BRIDGE_CHANGED'):module.prepare_bridge_integrity_fixture(case)
  self.assertFalse((case/'integrity-before.json').exists())
 def deny(self,expected,*,f25='PASS',four='PASS',endurance='PASS',prior=False,dirty=False,final=False):
  case=R/'logs/overnight'/('audit-entry-unit-'+uuid.uuid4().hex);case.mkdir()
  if prior:
   p=case/'runtime/overnight/audit-active.json';p.parent.mkdir(parents=True);p.write_text('{"status":"RUNNING","unit_fixture_only":true}',encoding='utf-8')
  def read(path):
   if Path(path).name=='INSTALLATION-STATE.json':return {'validation_8':{'f25':f25,'4h':four,'f26':'PASS','f27':'PENDING','f28':'NOT_RUN'}}
   if Path(path).name=='endurance-active.json':return {'status':endurance}
   if Path(path).name=='audit-active.json':return {'status':'RUNNING'}
   raise AssertionError('UNEXPECTED_IO_BEFORE_ADMISSION:'+str(path))
  with patch.object(module,'R',case),patch.object(module,'READ',side_effect=read),patch.object(module.subprocess,'check_output',return_value=' M unit-dirty' if dirty else ''),patch.object(sys,'argv',['global-audit.py']+(['--final'] if final else [])):
   with self.assertRaisesRegex(AssertionError,expected):module.main()
  self.assertFalse((case/'evidence').exists(),'DENIED_ENTRY_CREATED_AUDIT_EVIDENCE')
 def test_actual_f25_required(self):self.deny('ACTUAL_2H_AND_4H_REQUIRED',f25='NOT_RUN')
 def test_actual_four_hours_required(self):self.deny('ACTUAL_2H_AND_4H_REQUIRED',four='RUNNING')
 def test_active_endurance_is_preserved(self):self.deny('NO_AUDIT_DURING_ACTIVE_STAGE',endurance='RUNNING')
 def test_existing_or_interrupted_audit_is_not_duplicated(self):self.deny('EXISTING_OR_INTERRUPTED_AUDIT_REQUIRES_DISK_RECONCILIATION_NO_DUPLICATE',prior=True)
 def test_dirty_git_denies_before_creation(self):self.deny('CLEAN_GIT_REQUIRED',dirty=True)
 def test_final_requires_actual_pilot_night(self):self.deny('ALL_ACTUAL_FINAL_PHASES_REQUIRED',final=True)
 def test_declared_owned_fixture_scope(self):
  p=R/'sandbox'/('f26-unit-'+uuid.uuid4().hex[:8]);self.assertTrue(module.owns_fixture_metadata(p/'.autopilot',{'objective':'labelled fixture'}, {p.resolve()}))
 def test_known_factory_and_prepare_scope(self):
  self.assertTrue(module.owns_fixture_metadata(R/'sandbox/7b-gate20-12abcdef/.autopilot',{'objective':'Implement correct addition with verified tests'},set()))
  self.assertTrue(module.owns_fixture_metadata(R/'sandbox/7b-prepare-12abcdef/.autopilot',{'objective':'Explicit prepare generates run id'},set()))
 def test_unrelated_new_project_metadata_preserved(self):
  for name in ['personal-project','7b-personal-12abcdef','f26-unregistered-12abcdef']:
   self.assertFalse(module.owns_fixture_metadata(R/'sandbox'/name/'.autopilot',{'objective':'Personal unrelated work'},set()))
  self.assertFalse(module.owns_fixture_metadata(R/'logs/7b-gate20-12abcdef/.autopilot',{'objective':'Implement correct addition with verified tests'},set()))
  self.assertFalse(module.owns_fixture_metadata(R/'sandbox',{},set()))
  self.assertFalse(module.owns_fixture_metadata(R/'sandbox/7b-gate20-12abcdef/other',{'objective':'Implement correct addition with verified tests'},set()))
 def test_sandbox_reuse_requires_this_audits_declared_initialized_root(self):
  case=R/'logs/overnight'/('audit-reuse-unit-'+uuid.uuid4().hex);(case/'sandbox').mkdir(parents=True);p=case/'sandbox/owned';p.mkdir();other=case/'sandbox/foreign';other.mkdir()
  with patch.object(module,'R',case):
   self.assertEqual(module.admit_sandbox_fixture(p,{p.resolve()},True),p.resolve())
   with self.assertRaisesRegex(AssertionError,'ONLY_THIS_AUDITS_INITIALIZED_FIXTURE_MAY_BE_REUSED'):module.admit_sandbox_fixture(other,{p.resolve()},True)
   with self.assertRaisesRegex(AssertionError,'FRESH_OWNED_SANDBOX_REQUIRED'):module.admit_sandbox_fixture(p,set())
   with self.assertRaisesRegex(AssertionError,'FRESH_OWNED_SANDBOX_REQUIRED'):module.admit_sandbox_fixture(case/'outside',set())
   self.assertEqual(module.admit_sandbox_fixture(case/'sandbox/fresh',set()),(case/'sandbox/fresh').resolve())
if __name__=='__main__':unittest.main(verbosity=2)
