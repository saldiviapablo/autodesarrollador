"""Dedicated disposable local pilot. Initial defects and immutable acceptance.

No personal repository/data, deployment, credentials or runtime edits. Only the
Qwen Worker may implement module.py and documentation after native approval.
"""
import json
TASK='''Implement a usable Python stdlib CLI for synthetic local execution reports.
Implement normalize(records), summarize(records), round_seconds(value), and CLI
python module.py. round_seconds uses the seconds validation/format below.
records is a JSON list. Each record must be a dict with EXACTLY id,status,seconds.
id: nonempty stripped string, no CR/LF/NUL, preserve Unicode; IDs must be unique
after stripping. status EXACTLY PASS,FAIL,BLOCKED,TIMEOUT. seconds: string,int or
float (bool forbidden), finite Decimal(str(value)) between0 and1000000000000
inclusive; reject out-of-range inputs before rounding. Quantize .01 with
ROUND_HALF_UP; reject invalid input with ValueError, not incidental exceptions.
Zero, including negative zero, must be formatted canonically as0.00.
normalize returns NEW dicts sorted by id, seconds formatted with two decimals;
input must remain unchanged. summarize returns {records:[normalized],counts:
{PASS:int,FAIL:int,BLOCKED:int,TIMEOUT:int},total_seconds:str,max_seconds:str},
with exact Decimal sums and max over normalized values; empty -> all0/0.00.
Implement markdown(summary): a Markdown report with a title, counts/total/max,
and rows sorted by id. Escape pipes in IDs so table cells remain well formed.
Use this stable layout: first line '# Execution report', then
'Total seconds: <total_seconds>' and 'Max seconds: <max_seconds>'. Include a
two-column Markdown table headed '| Status | Count |' with one row per status
in PASS,FAIL,BLOCKED,TIMEOUT order, then a three-column table headed
'| ID | Status | Seconds |' with the normalized records sorted by id.
Use ordinary Markdown separator rows and pipe-delimited data cells with spaces.
CLI reads stdin JSON list; default prints JSON summary ensure_ascii=False;
--markdown prints Markdown. Invalid input/unknown option -> exit2, concise stderr
without traceback, stdout empty. No network, filesystem reads, dependencies or
secrets required by the application itself. Document actual API/CLI, validation,
Unicode, Decimal rounding, exact examples and official Decimal reference.
README must explicitly say stdlib or standard library only. Do not invent
requirements.txt, downloads or installation commands for nonexistent files.
Fix the initial money/seconds rounding bug as well as missing report features.
Modify module.py and README.md only; build.py generates the approved reports.
Never edit immutable tests/build/input fixtures/control files. Run tests/build.
'''
INITIAL='''"""Incomplete execution-report utility; synthetic data only."""
def round_seconds(value):
    return format(round(float(value), 2), '.2f')

def normalize(records):
    raise NotImplementedError('missing validation and normalization')

def summarize(records):
    raise NotImplementedError('missing report aggregation')

def markdown(summary):
    raise NotImplementedError('missing report renderer')
'''
ACCEPTANCE=r'''import copy,json,subprocess,sys,unittest
from decimal import Decimal
import module as app
from pathlib import Path
class Acceptance(unittest.TestCase):
 def row(self,id='a',status='PASS',seconds='1.005'):return {'id':id,'status':status,'seconds':seconds}
 def test_half_up_bug(self):self.assertEqual(app.round_seconds('1.005'),'1.01');self.assertEqual(app.normalize([self.row()])[0]['seconds'],'1.01')
 def test_unicode_sort_copy(self):
  x=[self.row(' ñ ',seconds=2),self.row('a',seconds=.125)];before=copy.deepcopy(x)
  self.assertEqual(app.normalize(x),[self.row('a',seconds='0.13'),self.row('ñ',seconds='2.00')]);self.assertEqual(x,before)
 def test_counts_sum_max(self):
  x=[self.row('a','PASS','0.105'),self.row('b','FAIL','2.675'),self.row('c','BLOCKED',0),self.row('d','TIMEOUT','1.005')]
  s=app.summarize(x);self.assertEqual(s['counts'],{'PASS':1,'FAIL':1,'BLOCKED':1,'TIMEOUT':1});self.assertEqual(s['total_seconds'],'3.80');self.assertEqual(s['max_seconds'],'2.68');self.assertEqual(s['records'],app.normalize(x));self.assertEqual(set(s),{'records','counts','total_seconds','max_seconds'})
 def test_empty(self):self.assertEqual(app.summarize([]),{'records':[],'counts':{'PASS':0,'FAIL':0,'BLOCKED':0,'TIMEOUT':0},'total_seconds':'0.00','max_seconds':'0.00'})
 def test_seconds_boundaries(self):
  for value in [0,-0.0,'-0.00','0.00001']:self.assertEqual(app.round_seconds(value),'0.00')
  self.assertEqual(app.round_seconds('1000000000000'),'1000000000000.00')
 def test_invalid_container_and_shape(self):
  for bad in [None,{},'[]',(),[None],[{}],[[]],[dict(self.row(),extra=1)]]:
   for fn in [app.normalize,app.summarize]:
    with self.subTest(bad=bad,fn=fn):
     with self.assertRaises(ValueError):fn(bad)
 def test_invalid_ids(self):
  for id in ['', '  ',1,True,None,[],{},'a\nb','a\rb','a\x00b']:
   with self.subTest(id=id):
    with self.assertRaises(ValueError):app.normalize([self.row(id)])
  with self.assertRaises(ValueError):app.normalize([self.row('a'),self.row(' a ')])
 def test_invalid_status(self):
  for status in ['pass','SUCCESS','',None,True,1,[],{}]:
   with self.subTest(status=status):
    with self.assertRaises(ValueError):app.normalize([self.row(status=status)])
 def test_invalid_seconds(self):
  for seconds in [-1,'-.01','1000000000000.01','1e100','NaN','Infinity','-Infinity',float('nan'),float('inf'),None,True,{},[],(),b'1',Decimal('1'),'bad','']:
   with self.subTest(seconds=seconds):
    with self.assertRaises(ValueError):app.normalize([self.row(seconds=seconds)])
    with self.assertRaises(ValueError):app.round_seconds(seconds)
 def test_many_exact_decimals(self):
  x=[self.row(str(i),seconds='0.10') for i in range(100)];self.assertEqual(app.summarize(x)['total_seconds'],'10.00')
 def test_markdown_unicode_escape(self):
  s=app.markdown(app.summarize([self.row('ñ|a')]));self.assertIsInstance(s,str);self.assertIn('# ',s);self.assertIn('ñ\\|a',s);self.assertIn('1.01',s)
 def test_markdown_complete_counts_totals_sorted(self):
  summary=app.summarize([self.row('z','FAIL','2.675'),self.row('a','PASS','1.005')]);before=copy.deepcopy(summary);text=app.markdown(summary)
  self.assertEqual(summary,before);self.assertEqual(text.splitlines()[0],'# Execution report')
  for line in ['Total seconds: 3.69','Max seconds: 2.68','| Status | Count |','| PASS | 1 |','| FAIL | 1 |','| BLOCKED | 0 |','| TIMEOUT | 0 |','| ID | Status | Seconds |','| a | PASS | 1.01 |','| z | FAIL | 2.68 |']:self.assertIn(line,text)
  self.assertLess(text.index('| a |'),text.index('| z |'))
 def test_markdown_empty_report(self):
  text=app.markdown(app.summarize([]))
  for line in ['Total seconds: 0.00','Max seconds: 0.00','| ID | Status | Seconds |']:self.assertIn(line,text)
  for status in ['PASS','FAIL','BLOCKED','TIMEOUT']:self.assertIn('| '+status+' | 0 |',text)
 def test_json_cli(self):
  x=[self.row('ñ')];p=subprocess.run([sys.executable,'module.py'],input=json.dumps(x),text=True,capture_output=True);self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout),app.summarize(x));self.assertIn('ñ',p.stdout)
 def test_markdown_cli(self):
  x=[self.row('ñ')];p=subprocess.run([sys.executable,'module.py','--markdown'],input=json.dumps(x),text=True,capture_output=True);self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(p.stdout.strip(),app.markdown(app.summarize(x)).strip())
 def test_cli_fail_closed(self):
  for text,args in [('bad',[]),('{}',[]),('[{}]',[]),('[]',['--unknown'])]:
   p=subprocess.run([sys.executable,'module.py',*args],input=text,text=True,capture_output=True);self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,'');self.assertNotIn('Traceback',p.stderr);self.assertTrue(p.stderr.strip())
 def test_docs(self):
  t=Path('README.md').read_text(encoding='utf-8');self.assertGreater(len(t),500)
  for word in ['module.py','normalize','summarize','round_seconds','markdown','--markdown','ValueError','ROUND_HALF_UP','1.005','1.01','https://docs.python.org/3/library/decimal.html']:self.assertIn(word,t)
  self.assertRegex(t,'Unicode|UTF-8')
  self.assertRegex(t.lower(),'stdlib|standard library')
  self.assertNotIn('pip install -r requirements.txt',t.lower())
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Acceptance))
 if r.wasSuccessful():print('ENDURANCE_TEST_PASS')
 raise SystemExit(0 if r.wasSuccessful() else 1)
'''
# Raw source above deliberately escapes Python string literals. Normalize one
# layer so the generated tests contain actual newline/NUL validation operands.
ACCEPTANCE=ACCEPTANCE.replace("'a\\\\nb'","'a\\nb'").replace("'a\\\\rb'","'a\\rb'").replace("'a\\\\x00b'","'a\\x00b'").replace("'ñ\\\\\\\\|a'","'ñ\\\\|a'")
BUILD='''import ast,json,pathlib,subprocess,sys
ast.parse(pathlib.Path('module.py').read_text(encoding='utf-8'))
data=pathlib.Path('sample-records.json').read_text(encoding='utf-8')
for args,name in [([], 'artifact-report.json'),(['--markdown'],'REPORT.md')]:
 p=subprocess.run([sys.executable,'module.py',*args],input=data,text=True,capture_output=True)
 assert p.returncode==0,p.stderr
 if not args:json.loads(p.stdout)
 pathlib.Path(name).write_text(p.stdout,encoding='utf-8')
print('ENDURANCE_BUILD_PASS')
'''
def pilot_fixture():
 records=[{'id':'compilación ñ','status':'PASS','seconds':'2.675'},{'id':'prueba cero','status':'PASS','seconds':0},{'id':'recovery','status':'TIMEOUT','seconds':'10.005'},{'id':'revisión|local','status':'BLOCKED','seconds':'1.005'}]
 return {'name':'local-run-report-pilot','objective':'Deliver a usable noncritical synthetic run-report CLI with exact validated totals and Unicode Markdown/JSON outputs','task':TASK,'files':{'module.py':INITIAL,'README.md':'# Local run-report pilot\n\nDocumentation incomplete.\n','test_module.py':ACCEPTANCE,'build.py':BUILD,'sample-records.json':json.dumps(records,ensure_ascii=False,indent=2)+'\n','.gitignore':'.autopilot/\n__pycache__/\n'}}
