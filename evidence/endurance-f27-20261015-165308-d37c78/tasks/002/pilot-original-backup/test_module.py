import copy,json,subprocess,sys,unittest
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
