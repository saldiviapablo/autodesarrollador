"""Real6h F28 on actual copies of the human-reviewed F27 pilot, not utility stubs.

Does not execute before an explicit final human review receipt, F26 and2h/4h.
All implementation changes belong to Qwen through native Runner. Preserves the
previous actual report as immutable memory in each new pilot workspace.
"""
from pathlib import Path
import importlib.util,json,subprocess,sys
R=Path(__file__).resolve().parents[2]
if not(R/'AGENTS.md').exists():R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tests'))
from endurance_controller import Stage,READ,write,sha
def module(name,filename):
 spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
Pilot=module('pilot_controller','pilot-controller.py').Pilot
night_fixture=module('night_workload','night-pilot-workload.py').night_fixture
class Night(Pilot):
 def __init__(self,receipt_path):
  self.review=READ(receipt_path);self.review_path=Path(receipt_path);self.origin=Path(self.review['project']);self.previous=self.origin;self.chain=[]
  physical=self.origin.resolve(strict=True);assert physical.is_relative_to((R/'sandbox').resolve()),'ONLY_DEDICATED_LOCAL_PILOT_ALLOWED'
  required={'module.py','README.md','test_module.py','build.py','sample-records.json','artifact-report.json','REPORT.md'};assert required.issubset(self.review['reviewed_files']),'INCOMPLETE_HUMAN_REVIEW_BINDING'
  assert all((self.origin/n).resolve(strict=True).is_relative_to(physical) for n in self.review['reviewed_files']),'REVIEW_FILE_OUTSIDE_APPROVED_PILOT'
  state=READ(self.origin/'.autopilot/STATE.json');assert state['status']=='COMPLETED' and state['run_id']==self.review['native_run_id'],'HUMAN_REVIEW_NOT_BOUND_TO_COMPLETED_PILOT'
  Stage.__init__(self,'F28');self.model_out=None;self.model_err=None
 def _persist_locked(self):
  Stage._persist_locked(self)
  v=READ(self.E/'STATE.json');v.update(pilot_origin=str(self.origin),actual_human_review_receipt=str(self.review_path),pilot_chain=self.chain);write(self.E/'STATE.json',v)
  if self.admitted:write(R/'runtime/overnight/endurance-active.json',v)
 def guard(self):Stage.guard(self)
 def fixture(self,index):
  if index==0:
   assert self.review['method']=='HUMAN_FINAL_REVIEW' and self.review['decision']=='ACCEPTED'
   assert all(sha(self.origin/n)==h for n,h in self.review['reviewed_files'].items()),'HUMAN_REVIEWED_PILOT_CHANGED'
  else:
   assert READ(self.previous/'.autopilot/STATE.json')['status']=='COMPLETED'
   assert sha(self.previous/'artifact-report.json')==self.chain[-1]['report_after_sha256'],'PREVIOUS_ACTUAL_REPORT_CHANGED'
   assert sha(self.previous/'module.py')==self.chain[-1]['module_after_sha256'],'PREVIOUS_ACTUAL_IMPLEMENTATION_CHANGED'
  return night_fixture(index,self.previous,self.origin)
 def run_task(self,index):
  before=self.previous;before_module=sha(before/'module.py');before_report=sha(before/'artifact-report.json')
  Pilot.run_task(self,index)
  t=self.tasks[-1];p=Path(t['project']);a=p/'.autopilot';memory=READ(p/'PILOT-MEMORY.json')
  assert memory['previous_project']==str(before) and memory['previous_report_sha256']==before_report and memory['previous_module_sha256']==before_module
  assert sha(p/'previous-report.json')==before_report
  first=READ(self.E/'tasks'/str(index+1).zfill(3)/'fixture.json');assert first['files']['module.py']==(before/'module.py').read_text(encoding='utf-8'),'CLONE_NOT_ACTUAL_PREDECESSOR'
  link={'index':index+1,'origin':str(self.origin),'predecessor':str(before),'project':str(p),'run_id':t['run_id'],'module_before_sha256':before_module,'report_before_sha256':before_report,'module_after_sha256':sha(p/'module.py'),'report_after_sha256':sha(p/'artifact-report.json'),'comparison_after_sha256':sha(p/'comparison-report.json'),'memory_sha256':sha(p/'PILOT-MEMORY.json'),'predecessor_unchanged':sha(before/'module.py')==before_module and sha(before/'artifact-report.json')==before_report}
  assert link['predecessor_unchanged'];self.chain.append(link);write(self.E/'PILOT-CHAIN.json',self.chain);t.update(actual_pilot_origin=str(self.origin),actual_pilot_predecessor=str(before),pilot_memory_verified=True);write(self.E/'tasks'/str(index+1).zfill(3)/'RESULT.json',t);self.previous=p;self.persist()
 def run_night(self):
  result=Stage.run(self);s=READ(self.E/'SUMMARY.json')
  checks={'human_review_real':self.review['method']=='HUMAN_FINAL_REVIEW' and self.review['decision']=='ACCEPTED','all_tasks_actual_pilot_clones':len(self.chain)==len(self.tasks) and len(self.chain)>=3,'previous_report_memory_every_task':all(t.get('pilot_memory_verified') is True for t in self.tasks),'origin_unchanged':all(sha(self.origin/n)==h for n,h in self.review['reviewed_files'].items()),'chain_reports_unchanged':all(sha(Path(t['project'])/'artifact-report.json')==t['report_after_sha256'] and sha(Path(t['project'])/'module.py')==t['module_after_sha256'] for t in self.chain),'actual6to8h':21600<=s['duration_seconds']<=28800}
  write(self.E/'PILOT-GATE.json',{'status':'PASS' if result==0 and all(checks.values()) else 'FAIL','checks':checks,'review_receipt_sha256':sha(self.review_path),'origin':str(self.origin)})
  if result==0 and not all(checks.values()):
   # Preserve the shared stage's original result separately. The effective F28
   # result must include the pilot-specific gate, never only a duration PASS.
   write(self.E/'SHARED-STAGE-RESULT.json',s);s.update(status='FAIL',failure='PILOT_SPECIFIC_GATE_FAILED');write(self.E/'SUMMARY.json',s);self.terminal='FAIL';self.persist();return 1
  return result
def main():
 install=READ(R/'config/INSTALLATION-STATE.json');v=install['validation_8']
 assert not install.get('F28_NOT_EXECUTED') and v.get('f28')!='WAIVED_BY_USER','F28_FORBIDDEN_BY_EXPLICIT_USER_REVISION'
 assert v.get('f25')==v.get('4h')==v.get('f26')==v.get('f27')=='PASS','ALL_PRIOR_GATES_REQUIRED'
 receipt=Path(v['f27_human_review_receipt']);assert receipt.resolve().is_relative_to(R/'evidence');review=READ(receipt);assert review['method']=='HUMAN_FINAL_REVIEW' and review['decision']=='ACCEPTED' and review.get('human_confirmation_reference'),'ACTUAL_FINAL_HUMAN_REVIEW_REQUIRED'
 assert not subprocess.check_output(['git','status','--porcelain=v1'],cwd=R,text=True).strip(),'CLEAN_GIT_REQUIRED'
 assert READ(R/'runtime/overnight/endurance-active.json')['status']!='RUNNING'
 raise SystemExit(Night(receipt).run_night())
if __name__=='__main__':main()
