"""No inference. Check truthful duration gates and compile failing fixtures."""
from pathlib import Path
import ast,copy,json,subprocess,sys,unittest,uuid,concurrent.futures
from unittest.mock import patch
from endurance_controller import validate_stage,DURATIONS,R,write,ps
from endurance_workloads import fixture
class Policy(unittest.TestCase):
 def setUp(self):
  self.tasks=[{'status':'PASS','workload':n,'actual_recovery':i==0,'checkpoints':1,'clock_preserved':True,'reviewer_readonly':True} for i,n in enumerate(['csv','intervals','catalog'])]
  self.resource={'samples':1440,'max_sample_gap':5.5,'critical':False}
 def gate(self,**kwargs):
  args=dict(stage='F25',elapsed=7200,tasks=self.tasks,resource=self.resource,integrity=True,cleanup=True);args.update(kwargs);return validate_stage(**args)
 def test_valid_evidence_shape(self):self.assertTrue(all(self.gate().values()))
 def test_powershell_diagnostic_bytes_do_not_corrupt_json(self):
  completed=subprocess.CompletedProcess([],0,b'STAGE_JSON\n{"status":"PASS"}\n',b'legacy OEM diagnostic \xa2')
  with patch('endurance_controller.subprocess.run',return_value=completed):self.assertEqual(ps('component fixture'),{'status':'PASS'})
 def test_powershell_json_requires_utf8(self):
  completed=subprocess.CompletedProcess([],0,b'STAGE_JSON\n{"text":"\xa2"}',b'')
  with patch('endurance_controller.subprocess.run',return_value=completed):
   with self.assertRaises(UnicodeDecodeError):ps('component fixture')
 def test_partial_duration_never_pass(self):self.assertFalse(self.gate(elapsed=7199.99)['real_duration'])
 def test_real_4h_and_night_requirements(self):
  self.assertEqual(DURATIONS,{'F25':7200,'4H':14400,'F28':21600});self.assertFalse(self.gate(stage='4H',elapsed=14399)['real_duration']);self.assertFalse(self.gate(stage='F28',elapsed=28801)['night_upper_bound'])
 def test_monitor_gap(self):self.assertFalse(self.gate(resource={**self.resource,'max_sample_gap':31})['continuous_monitoring'])
 def test_missing_monitor(self):self.assertFalse(self.gate(resource={})['continuous_monitoring'])
 def test_too_few_samples(self):self.assertFalse(self.gate(resource={**self.resource,'samples':719})['continuous_monitoring'])
 def test_recovery_must_be_executed(self):
  t=copy.deepcopy(self.tasks);t[0]['actual_recovery']=False;self.assertFalse(self.gate(tasks=t)['actual_recovery'])
 def test_each_task_native_pass(self):
  t=copy.deepcopy(self.tasks);t[-1]['status']='FAIL';self.assertFalse(self.gate(tasks=t)['native_completion_every_task'])
 def test_several_varied_tasks(self):
  self.assertFalse(self.gate(tasks=self.tasks[:1])['several_tasks']);self.assertFalse(self.gate(tasks=[self.tasks[0]]*3)['varied_workloads'])
 def test_critical_resource(self):self.assertFalse(self.gate(resource={**self.resource,'critical':True})['no_sustained_critical_ram'])
 def test_integrity(self):self.assertFalse(self.gate(integrity=False)['integrity'])
 def test_cleanup(self):self.assertFalse(self.gate(cleanup=False)['cleanup'])
 def test_checkpoints_required(self):
  t=copy.deepcopy(self.tasks);t[1]['checkpoints']=0;self.assertFalse(self.gate(tasks=t)['checkpoints_each_task'])
 def test_native_clocks_required(self):
  t=copy.deepcopy(self.tasks);t[1]['clock_preserved']=False;self.assertFalse(self.gate(tasks=t)['native_clocks_preserved'])
 def test_readonly_reviewers_required(self):
  t=copy.deepcopy(self.tasks);t[1]['reviewer_readonly']=False;self.assertFalse(self.gate(tasks=t)['reviewers_readonly'])
 def test_concurrent_atomic_metadata_writes(self):
  d=R/'sandbox'/('endurance-write-cert-'+uuid.uuid4().hex[:8]);d.mkdir();p=d/'STATE.json'
  def one(i):write(p,{'sequence':i,'text':'áéíóú ñ'*100,'items':list(range(50))})
  with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(one,range(40)))
  v=json.loads(p.read_text(encoding='utf-8'));self.assertIn(v['sequence'],range(40));self.assertEqual(v['items'],list(range(50)));self.assertEqual(v['text'],'áéíóú ñ'*100);self.assertFalse(list(d.glob('*.writing')))
 def test_generated_acceptance_preexists_and_fails(self):
  d=R/'sandbox'/('endurance-fixture-cert-'+uuid.uuid4().hex[:8]);d.mkdir()
  outcomes=[]
  for index in range(6):
   v=fixture(index);p=d/str(index);p.mkdir()
   for n,text in v['files'].items():
    (p/n).write_text(text,encoding='utf-8')
    if n.endswith('.py'):ast.parse(text,filename=n)
   proc=subprocess.run(['C:/Python314/python.exe','test_module.py'],cwd=p,capture_output=True,encoding='utf-8',timeout=20)
   self.assertNotEqual(proc.returncode,0);self.assertNotIn('ENDURANCE_TEST_PASS',proc.stdout);self.assertIn('Ran ',proc.stderr)
   (p/'baseline.stdout.txt').write_text(proc.stdout,encoding='utf-8');(p/'baseline.stderr.txt').write_text(proc.stderr,encoding='utf-8');outcomes.append({'index':index,'workload':v['name'],'expected_initial_failure':True})
  (R/'logs/overnight/endurance-fixture-cert.json').write_text(json.dumps({'status':'PASS','directory':str(d),'fixtures':outcomes},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':unittest.main(verbosity=2)
