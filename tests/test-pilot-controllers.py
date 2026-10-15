"""Fixture/control tests only: zero native runs, inference or human approvals."""
from pathlib import Path
import ast,importlib.util,json,sys,threading,unittest,uuid
from unittest.mock import patch,Mock
BASE=Path(__file__).resolve().parent
def load(name,filename):
 spec=importlib.util.spec_from_file_location(name,BASE/filename);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
pilot=load('pilot_control_unit','pilot-controller.py');night=load('night_control_unit','night-pilot-controller.py');work=load('pilot_workload_unit','pilot_workload.py');nw=load('night_workload_unit','night-pilot-workload.py')
R=pilot.R
class Controls(unittest.TestCase):
 def test_pilot_f26_missing_denies_before_creation(self):
  with patch.object(pilot,'READ',return_value={'validation_8':{'f26':'NOT_RUN'}}),patch.object(pilot,'Pilot') as ctor:
   with self.assertRaises(AssertionError):pilot.main()
   ctor.assert_not_called()
 def test_night_f27_not_approved_denies_before_creation(self):
  v={'validation_8':{'f25':'PASS','4h':'PASS','f26':'PASS','f27':'BLOCKED_REQUIRES_HUMAN'}}
  with patch.object(night,'READ',return_value=v),patch.object(night,'Night') as ctor:
   with self.assertRaises(AssertionError):night.main()
   ctor.assert_not_called()
 def attempt(self,receipt):
  path=R/'evidence/unit-only-human-review-fixture.json';v={'validation_8':dict.fromkeys(['f25','4h','f26','f27'],'PASS')};v['validation_8']['f27_human_review_receipt']=str(path)
  def read(p):
   if Path(p).name=='INSTALLATION-STATE.json':return v
   if Path(p)==path:return receipt
   return {'status':'PASS'}
  with patch.object(night,'READ',side_effect=read),patch.object(night,'Night') as ctor,patch.object(night.subprocess,'check_output',return_value=''):
   with self.assertRaises(AssertionError):night.main()
   ctor.assert_not_called()
 def test_no_actual_human_method_denied(self):self.attempt({'method':'AUTOMATIC','decision':'ACCEPTED','human_confirmation_reference':'synthetic-unit'})
 def test_human_rejection_denied(self):self.attempt({'method':'HUMAN_FINAL_REVIEW','decision':'REJECTED','human_confirmation_reference':'synthetic-unit'})
 def test_missing_human_reference_denied(self):self.attempt({'method':'HUMAN_FINAL_REVIEW','decision':'ACCEPTED'})
 def test_review_project_outside_dedicated_sandbox_denied(self):
  with patch.object(night,'READ',return_value={'project':str(R/'logs'),'reviewed_files':{}}),patch.object(night.Stage,'__init__',return_value=None) as ctor:
   with self.assertRaisesRegex(AssertionError,'ONLY_DEDICATED_LOCAL_PILOT_ALLOWED'):night.Night('unit-receipt')
   ctor.assert_not_called()
 def test_incomplete_human_file_binding_denied(self):
  p=R/'sandbox'/('pilot-binding-unit-'+uuid.uuid4().hex[:8]);p.mkdir()
  with patch.object(night,'READ',return_value={'project':str(p),'reviewed_files':{}}),patch.object(night.Stage,'__init__',return_value=None) as ctor:
   with self.assertRaisesRegex(AssertionError,'INCOMPLETE_HUMAN_REVIEW_BINDING'):night.Night('unit-receipt')
   ctor.assert_not_called()
 def test_human_binding_requires_completed_native_state(self):
  p=R/'sandbox'/('pilot-binding-unit-'+uuid.uuid4().hex[:8]);p.mkdir();names=['module.py','README.md','test_module.py','build.py','sample-records.json','artifact-report.json','REPORT.md']
  for n in names:(p/n).write_text('labelled unit bytes only',encoding='utf-8')
  review={'project':str(p),'reviewed_files':dict.fromkeys(names,'unit-hash'),'native_run_id':'run-unit-fixture'}
  def read(path):return {'status':'RUNNING','run_id':'run-unit-fixture'} if Path(path).name=='STATE.json' else review
  with patch.object(night,'READ',side_effect=read),patch.object(night.Stage,'__init__',return_value=None) as ctor:
   with self.assertRaisesRegex(AssertionError,'HUMAN_REVIEW_NOT_BOUND_TO_COMPLETED_PILOT'):night.Night('unit-receipt')
   ctor.assert_not_called()
 def test_pilot_fixture_complete_before_start(self):
  v=work.pilot_fixture();tree=ast.parse(v['files']['test_module.py']);tests=[n.name for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
  self.assertEqual(len(tests),17)
  for name in ['test_half_up_bug','test_seconds_boundaries','test_invalid_seconds','test_cli_fail_closed','test_markdown_unicode_escape']:self.assertIn(name,tests)
  for name,source in v['files'].items():
   if name.endswith('.py'):ast.parse(source,filename=name)
  values=[n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)];self.assertIn('a\nb',values);self.assertIn('a\x00b',values);self.assertIn('ñ\\|a',values)
  self.assertIn("round(float(value)",v['files']['module.py']);self.assertIn('raise NotImplementedError',v['files']['module.py'])
 def test_existing_pilot_mutation_invalidates_human_review(self):
  case=R/'logs/overnight'/('pilot-review-unit-'+uuid.uuid4().hex[:8]);case.mkdir();(case/'module.py').write_text('unit fixture, not an implementation\n',encoding='utf-8')
  obj=object.__new__(night.Night);obj.origin=case;obj.review={'method':'HUMAN_FINAL_REVIEW','decision':'ACCEPTED','reviewed_files':{'module.py':'0'*64}}
  with self.assertRaisesRegex(AssertionError,'HUMAN_REVIEWED_PILOT_CHANGED'):obj.fixture(0)
 def readonly(self,mutate):
  case=R/'logs/overnight'/('pilot-readonly-unit-'+uuid.uuid4().hex[:8]);p=case/'project';p.mkdir(parents=True);a=p/'.autopilot';a.mkdir();(p/'README.md').write_text('original unit fixture',encoding='utf-8');(p/'artifact-report.json').write_text('{}',encoding='utf-8')
  obj=object.__new__(pilot.Pilot);obj.active=None;obj.tasks=[];obj.E=case/'evidence';seen=threading.Event()
  def git(*args):seen.set();return 'unit-head'
  obj.git=git
  def task(self,index):
   self.active=p;(a/'PROCESSES.json').write_text(json.dumps({'processes':[{'name':'reviewer','pid':12345}]}),encoding='utf-8');self.tasks=[{'project':str(p)}]
   assert seen.wait(3),'UNIT_OBSERVER_DID_NOT_REACH_SNAPSHOT'
   if mutate:(p/'artifact-report.json').write_text('{"forbidden_edit":true}',encoding='utf-8')
   self.active=None
  with patch.object(pilot.Stage,'run_task',task):obj.run_task(1)
  return json.loads((obj.E/'tasks/002/reviewer-full-target.json').read_text())
 def test_full_target_readonly_positive(self):self.assertEqual(self.readonly(False)['status'],'PASS')
 def test_artifact_edit_detected_by_readonly_observer(self):
  with self.assertRaisesRegex(AssertionError,'FULL_PILOT_REVIEWER_READONLY_NOT_PROVEN'):self.readonly(True)
 def test_legitimate_worker_correction_before_final_reviewer(self):
  case=R/'logs/overnight'/('pilot-readonly-retry-unit-'+uuid.uuid4().hex[:8]);p=case/'project';p.mkdir(parents=True);a=p/'.autopilot';a.mkdir();(p/'artifact-report.json').write_text('before legitimate correction',encoding='utf-8')
  obj=object.__new__(pilot.Pilot);obj.active=None;obj.tasks=[];obj.E=case/'evidence';first=threading.Event();second=threading.Event();calls=[]
  def git(*args):
   calls.append(True);(first if len(calls)==1 else second).set();return 'unit-head'
  obj.git=git
  def task(self,index):
   self.active=p;(a/'PROCESSES.json').write_text(json.dumps({'processes':[{'name':'reviewer','pid':10001}]}));assert first.wait(3)
   # The Worker, outside the first Reviewer, legitimately corrects its report.
   (p/'artifact-report.json').write_text('after legitimate correction',encoding='utf-8');(a/'PROCESSES.json').write_text(json.dumps({'processes':[{'name':'reviewer','pid':10002}]}));assert second.wait(3)
   self.tasks=[{'project':str(p)}];self.active=None
  with patch.object(pilot.Stage,'run_task',task):obj.run_task(1)
  proof=json.loads((obj.E/'tasks/002/reviewer-full-target.json').read_text());self.assertEqual(proof['status'],'PASS');self.assertEqual(len(proof['before']),2)
 def test_night_uses_actual_predecessor_bytes(self):
  p=R/'logs/overnight'/('pilot-chain-unit-'+uuid.uuid4().hex[:8]);p.mkdir();(p/'module.py').write_text('# labelled unit bytes, not completed pilot\n',encoding='utf-8');(p/'README.md').write_text('unit docs',encoding='utf-8');(p/'artifact-report.json').write_text(json.dumps({'records':[]}),encoding='utf-8');v=nw.night_fixture(0,p,p)
  self.assertEqual(v['files']['module.py'],(p/'module.py').read_text());self.assertIn('previous-report.json',v['immutable_files']);self.assertIn('PILOT-MEMORY.json',v['immutable_files']);self.assertIn('comparison-report.json',v['artifacts'])
  memory=json.loads(v['files']['PILOT-MEMORY.json']);self.assertEqual(memory['previous_report_sha256'],pilot.sha(p/'artifact-report.json'))
  tests=ast.parse(v['files']['test_module.py']);self.assertEqual(len([n for n in ast.walk(tests) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]),23);ast.parse(v['files']['build.py'])
if __name__=='__main__':unittest.main(verbosity=2)
