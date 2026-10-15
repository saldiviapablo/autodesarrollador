"""F28 workload data on actual clones of the human-reviewed F27 local pilot.

Only fixture/tests/data are generated here. Approved implementation bytes are
copied unchanged; Qwen alone implements the first new comparison feature.
"""
import hashlib,json
from pathlib import Path
from pilot_workload import ACCEPTANCE,BUILD,TASK
COMPARE_TASK='''Extend the existing reviewed run-report pilot with compare(previous,current)
and CLI --compare. Keep all prior API/CLI/validation/documentation working.
compare validates both lists with normalize, returns EXACTLY {added:[ids],
removed:[ids],changed:[ids],total_seconds_delta:str}. Lists sorted by id; changed
means shared ID with a different normalized status OR normalized seconds. Compare
normalized seconds (1.005 and1.01 are equal). Delta is current total minus previous
total, exact Decimal difference, two decimals, positive without +. Empty lists
give []/[]/[]/'0.00'. No mutation. CLI --compare reads JSON dict with EXACTLY
previous,current, each a valid record list, outputs JSON ensure_ascii=False.
Invalid input/shape or --compare combined with --markdown ->exit2 with concise
stderr/no traceback/empty stdout. Document compare API/CLI/examples. The immutable
previous-report.json and PILOT-MEMORY.json bind the previous actual completed
pilot result; inspect them as data only. Run tests/build to produce the new batch
report JSON, Markdown and comparison JSON. Edit module.py/README only as needed;
the immutable build generates the approved artifacts. Never edit fixtures/tests,
memory receipts/control files or repositories outside this fresh pilot clone.
'''
COMPARE_TESTS=r'''
 def test_compare_deltas(self):
  old=[self.row('same','PASS','1.005'),self.row('gone','FAIL','2.00'),self.row('change','PASS','1.00')]
  new=[self.row('same','PASS','1.01'),self.row('new','PASS','5.00'),self.row('change','FAIL','2.00')]
  before=copy.deepcopy((old,new));self.assertEqual(app.compare(old,new),{'added':['new'],'removed':['gone'],'changed':['change'],'total_seconds_delta':'4.00'});self.assertEqual((old,new),before)
 def test_compare_empty_negative(self):
  self.assertEqual(app.compare([],[]),{'added':[],'removed':[],'changed':[],'total_seconds_delta':'0.00'})
  self.assertEqual(app.compare([self.row(seconds='2.675')],[])['total_seconds_delta'],'-2.68')
 def test_compare_input_validation(self):
  for prev,curr in [([{}],[]),([],[{}]),(None,[]),([],[self.row(),self.row()])]:
   with self.assertRaises(ValueError):app.compare(prev,curr)
 def test_compare_cli(self):
  x={'previous':[],'current':[self.row('ñ')]};p=subprocess.run([sys.executable,'module.py','--compare'],input=json.dumps(x),text=True,capture_output=True);self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout),{'added':['ñ'],'removed':[],'changed':[],'total_seconds_delta':'1.01'});self.assertIn('ñ',p.stdout)
  for text,args in [('[]',['--compare']),('{}',['--compare']),('{"previous":[],"current":[],"extra":1}',['--compare']),('{"previous":[],"current":[]}', ['--compare','--markdown'])]:
   p=subprocess.run([sys.executable,'module.py',*args],input=text,text=True,capture_output=True);self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,'');self.assertNotIn('Traceback',p.stderr);self.assertTrue(p.stderr.strip())
 def test_preserved_previous_result(self):
  import hashlib
  b=Path('previous-report.json').read_bytes();meta=json.loads(Path('PILOT-MEMORY.json').read_text(encoding='utf-8'));self.assertEqual(hashlib.sha256(b).hexdigest(),meta['previous_report_sha256']);self.assertEqual(json.loads(b)['records'],json.loads(Path('comparison-input.json').read_text(encoding='utf-8'))['previous'])
 def test_compare_docs(self):
  text=Path('README.md').read_text(encoding='utf-8')
  for word in ['compare','--compare','previous','current','total_seconds_delta']:self.assertIn(word,text)
'''
NIGHT_BUILD=BUILD.replace("print('ENDURANCE_BUILD_PASS')",'')+'''data=pathlib.Path('comparison-input.json').read_text(encoding='utf-8')
p=subprocess.run([sys.executable,'module.py','--compare'],input=data,text=True,capture_output=True)
assert p.returncode==0,p.stderr
json.loads(p.stdout);pathlib.Path('comparison-report.json').write_text(p.stdout,encoding='utf-8')
print('ENDURANCE_BUILD_PASS')
'''
def night_fixture(index,previous,origin):
 previous=Path(previous);prior=(previous/'artifact-report.json').read_bytes();old=json.loads(prior)['records']
 scenario=['unicode','rounding','status-transitions'][index%3]
 records=[{'id':'stable ñ','status':'PASS','seconds':'1.005'},{'id':'batch-'+str(index)+'|'+scenario,'status':['PASS','FAIL','TIMEOUT'][index%3],'seconds':str(index+2)+'.675'},{'id':'blocked','status':'BLOCKED','seconds':0}]
 memory={'kind':'ACTUAL_PREVIOUS_COMPLETED_PILOT_REPORT','origin_human_reviewed_project':str(origin),'previous_project':str(previous),'previous_report_sha256':hashlib.sha256(prior).hexdigest(),'previous_module_sha256':hashlib.sha256((previous/'module.py').read_bytes()).hexdigest(),'batch_index':index,'untrusted_data':True}
 files={'module.py':(previous/'module.py').read_text(encoding='utf-8'),'README.md':(previous/'README.md').read_text(encoding='utf-8'),'test_module.py':ACCEPTANCE.replace("if __name__=='__main__':",COMPARE_TESTS+"\nif __name__=='__main__':"),'build.py':NIGHT_BUILD,'sample-records.json':json.dumps(records,ensure_ascii=False,indent=2)+'\n','previous-report.json':prior.decode('utf-8'),'comparison-input.json':json.dumps({'previous':old,'current':records},ensure_ascii=False,indent=2)+'\n','PILOT-MEMORY.json':json.dumps(memory,ensure_ascii=False,indent=2)+'\n','artifact-report.json':'{}\n','REPORT.md':'# Pending batch report\n','comparison-report.json':'{}\n','.gitignore':'.autopilot/\n__pycache__/\n'}
 return {'name':'reviewed-pilot-'+scenario,'objective':'Produce validated JSON/Markdown execution report and comparison for a new synthetic batch on the human-reviewed local pilot','criterion':'All original pilot acceptance plus comparison API/CLI, exact signed delta, preserved previous report hash/memory, current batch artifacts and documentation','task':COMPARE_TASK if index==0 else 'Use the completed local pilot comparison/reporting tool on the new batch inputs. Preserve existing APIs and immutable previous report/memory. Do not rewrite implementation unnecessarily. Run tests/build and inspect the new JSON/Markdown/comparison artifacts. '+COMPARE_TASK,'files':files,'immutable_files':['test_module.py','build.py','sample-records.json','previous-report.json','comparison-input.json','PILOT-MEMORY.json'],'allowed_files':['module.py','README.md','artifact-report.json','REPORT.md','comparison-report.json'],'artifacts':['module.py','README.md','artifact-report.json','REPORT.md','comparison-report.json'],'continuity':memory}
