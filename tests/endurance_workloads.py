"""Immutable task generators. Worker alone implements module.py and README.md."""
import hashlib,json
CASES=[
('csv-ledger','Normalize CSV ledger rows and aggregate exact decimal amounts',
'''Implement parse_ledger(text) accepting a CSV string with exact header date,category,amount. Return a list of dicts with ISO calendar-valid YYYY-MM-DD date (reject noncanonical formats), nonempty stripped category and amount string quantized to two decimal digits with Decimal(str(x)) ROUND_HALF_UP. Preserve row order and Unicode. Reject malformed headers/row widths/invalid dates/nonfinite or malformed amounts with ValueError. Blank input is invalid; header alone returns []. Implement totals(rows) over parse_ledger output, aggregating by category with Decimal, returning a dict inserted in lexicographic category order and values as two-decimal strings. Negative amounts are allowed. Implement CLI: python module.py reads CSV from stdin; print JSON {"rows":...,"totals":...} ensure_ascii=False; invalid input -> exit2 and concise stderr without traceback. Document API, CLI, validation, exact Decimal rounding, Unicode and official reference.''',
'''import unittest,subprocess,sys,json
from module import parse_ledger,totals
class Acceptance(unittest.TestCase):
 def test_rows_unicode_and_rounding(self):
  r=parse_ledger('date,category,amount\\n2024-02-29, Café ,1.005\\n2024-03-01,"Comida, casa",-2.675\\n')
  self.assertEqual(r,[{'date':'2024-02-29','category':'Café','amount':'1.01'},{'date':'2024-03-01','category':'Comida, casa','amount':'-2.68'}])
 def test_aggregate(self):
  self.assertEqual(totals(parse_ledger('date,category,amount\\n2024-01-01,Z,0.10\\n2024-01-01,A,0.20\\n2024-01-02,Z,0.20\\n')),{'A':'0.20','Z':'0.30'})
  self.assertEqual(list(totals([{'date':'2024-01-01','category':'Z','amount':'1.00'},{'date':'2024-01-01','category':'A','amount':'1.00'}])),['A','Z'])
 def test_header_only(self):self.assertEqual(parse_ledger('date,category,amount\\n'),[])
 def test_invalid(self):
  for s in ['', 'wrong,header\\n', 'date,category,amount\\n2023-02-29,X,1\\n','date,category,amount\\n2024-1-01,X,1\\n','date,category,amount\\n2024-01-01,,1\\n','date,category,amount\\n2024-01-01,X,NaN\\n','date,category,amount\\n2024-01-01,X,Infinity\\n','date,category,amount\\n2024-01-01,X,bad\\n','date,category,amount\\n2024-01-01,X\\n','date,category,amount\\n2024-01-01,X,1,extra\\n']:
   with self.subTest(s=s):
    with self.assertRaises(ValueError):parse_ledger(s)
 def test_cli(self):
  p=subprocess.run([sys.executable,'module.py'],input='date,category,amount\\n2024-01-01,Ñ,1.005\\n',text=True,capture_output=True);self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout)['totals'],{'Ñ':'1.01'})
  p=subprocess.run([sys.executable,'module.py'],input='bad',text=True,capture_output=True);self.assertEqual(p.returncode,2);self.assertNotIn('Traceback',p.stderr)
'''),
('intervals','Merge integer time intervals and compute gaps and peak concurrency',
'''Implement merge_intervals(intervals) where intervals is a list of integer pairs 0<=start<end (bool is not an integer here). Reject all other values with ValueError. Return sorted merged tuples, merging overlaps and touching intervals; do not mutate input. Implement gaps(intervals,start,end): require integer non-bool 0<=start<end and every interval inside that window; return sorted uncovered tuples. Implement peak_load(intervals): maximum concurrent half-open intervals, touching endpoints do not overlap; empty ->0. CLI python module.py reads JSON {"intervals":[...],"start":int,"end":int} stdin and outputs JSON with merged,gaps,peak keys. Invalid -> exit2 concise stderr. Document half-open/touching semantics and examples. Python stdlib only.''',
'''import unittest,subprocess,sys,json,copy
from module import merge_intervals,gaps,peak_load
class Acceptance(unittest.TestCase):
 def test_merge(self):
  x=[[5,8],[1,3],[3,5],[10,12]];b=copy.deepcopy(x);self.assertEqual(merge_intervals(x),[(1,8),(10,12)]);self.assertEqual(x,b);self.assertEqual(merge_intervals([]),[])
 def test_gaps(self):
  self.assertEqual(gaps([[2,4],[4,6],[8,9]],0,10),[(0,2),(6,8),(9,10)]);self.assertEqual(gaps([],0,3),[(0,3)]);self.assertEqual(gaps([[0,3]],0,3),[])
 def test_peak(self):
  self.assertEqual(peak_load([[0,2],[2,4]]),1);self.assertEqual(peak_load([[0,4],[1,3],[2,5]]),3);self.assertEqual(peak_load([]),0)
 def test_exhaustive(self):
  for n in range(1,18):
   iv=[[i%7,(i%7)+1+i%3] for i in range(n)];expected=max(sum(a<=t<b for a,b in iv) for t in range(10));self.assertEqual(peak_load(iv),expected)
 def test_invalid(self):
  for bad in [None,[[0,0]],[[-1,2]],[[2,1]],[[True,3]],[[0,1.2]],[[0,1,2]],['bad']]:
   for fn in [merge_intervals,peak_load]:
    with self.subTest(bad=bad,fn=fn):
     with self.assertRaises(ValueError):fn(bad)
  for iv,a,b in [([[0,4]],1,5),([],True,2),([],0,0),([[1,5]],0,4)]:
   with self.assertRaises(ValueError):gaps(iv,a,b)
 def test_cli(self):
  p=subprocess.run([sys.executable,'module.py'],input=json.dumps({'intervals':[[1,3],[3,5]],'start':0,'end':6}),text=True,capture_output=True);self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout),{'merged':[[1,5]],'gaps':[[0,1],[5,6]],'peak':1})
  p=subprocess.run([sys.executable,'module.py'],input='bad',text=True,capture_output=True);self.assertEqual(p.returncode,2);self.assertNotIn('Traceback',p.stderr)
'''),
('catalog','Validate a portable file catalog and report duplicates without filesystem access',
'''Implement catalog(entries): entries is a list of dicts with exactly path,size,sha256. path must be a nonempty portable POSIX relative path, no backslash, colon, leading slash, empty component, . or .. component, NUL/newline. Unicode allowed. size must be integer >=0, bool forbidden. sha256 must be exactly64 lowercase hex characters. Reject malformed entries and duplicate paths with ValueError. Return new list of dicts sorted by path; never mutate input or access filesystem. Implement duplicate_groups(entries) using validated catalog: return lists of paths having same (size,sha256), each group sorted, only groups of >=2, groups sorted lexicographically. CLI reads JSON array stdin; outputs JSON {"catalog":...,"duplicates":...} ensure_ascii=False; invalid ->exit2 concise stderr. Document contract, Unicode, examples, no filesystem I/O.''',
'''import unittest,subprocess,sys,json,copy
from module import catalog,duplicate_groups
def entry(p,s=1,h='a'*64):return {'path':p,'size':s,'sha256':h}
class Acceptance(unittest.TestCase):
 def test_sort_unicode(self):
  x=[entry('ñ/b.txt'),entry('a.txt')];b=copy.deepcopy(x);self.assertEqual(catalog(x),[entry('a.txt'),entry('ñ/b.txt')]);self.assertEqual(x,b);self.assertEqual(catalog([]),[])
 def test_duplicates(self):self.assertEqual(duplicate_groups([entry('z'),entry('a'),entry('b',2),entry('c',2),entry('unique',3)]),[['a','z'],['b','c']])
 def test_invalid_paths(self):
  for p in ['', '/x','../x','a/../b','./a','a//b','a/','C:x','a\\\\b','a\\x00b','a\\nb']:
   with self.subTest(path=p):
    with self.assertRaises(ValueError):catalog([entry(p)])
 def test_invalid_records(self):
  for x in [None,[None],[{}],[entry('x',True)],[entry('x',-1)],[entry('x',1.5)],[entry('x',1,'A'*64)],[entry('x',1,'a'*63)],[entry('x'),entry('x')],[dict(entry('x'),extra=1)]]:
   with self.subTest(x=x):
    with self.assertRaises(ValueError):catalog(x)
 def test_same_hash_different_size_not_duplicate(self):self.assertEqual(duplicate_groups([entry('a',1),entry('b',2)]),[])
 def test_cli(self):
  p=subprocess.run([sys.executable,'module.py'],input=json.dumps([entry('ñ')]),text=True,capture_output=True);self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout),{'catalog':[entry('ñ')],'duplicates':[]})
  p=subprocess.run([sys.executable,'module.py'],input='bad',text=True,capture_output=True);self.assertEqual(p.returncode,2);self.assertNotIn('Traceback',p.stderr)
''')]
def fixture(index):
 name,objective,task,body=CASES[index%len(CASES)]
 tests=body+'''\n def test_documentation(self):
  from pathlib import Path
  text=Path('README.md').read_text(encoding='utf-8');self.assertGreater(len(text),250);self.assertIn('module.py',text);self.assertIn('ValueError',text);self.assertIn('2',text)
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Acceptance))
 if result.wasSuccessful():print('ENDURANCE_TEST_PASS')
 raise SystemExit(0 if result.wasSuccessful() else 1)
'''
 # Vary real acceptance inputs rather than adding a self-referential identity test.
 k=index+7
 varied={'csv-ledger':"\n def test_stage_specific_amount(self):\n  self.assertEqual(totals(parse_ledger('date,category,amount\\n2024-01-01,Task,"+str(k)+".125\\n')),{'Task':'"+str(k)+".13'})\n",
 'intervals':"\n def test_stage_specific_window(self):\n  self.assertEqual(gaps([["+str(k)+","+str(k+2)+"]],"+str(k-1)+","+str(k+3)+"),[("+str(k-1)+","+str(k)+"),("+str(k+2)+","+str(k+3)+")])\n",
 'catalog':"\n def test_stage_specific_names(self):\n  self.assertEqual(duplicate_groups([entry('"+str(k)+"/ñ'),entry('"+str(k)+"/a')]),[['"+str(k)+"/a','"+str(k)+"/ñ']])\n"}[name]
 tests=tests.replace('class Acceptance(unittest.TestCase):','class Acceptance(unittest.TestCase):'+varied)
 stub='"""Incomplete '+name+' utility. Worker must implement approved API."""\n'
 names={'csv-ledger':['parse_ledger','totals'],'intervals':['merge_intervals','gaps','peak_load'],'catalog':['catalog','duplicate_groups']}[name]
 stub+='\n'.join('def '+n+'(*args,**kwargs):\n raise NotImplementedError("incomplete baseline")\n' for n in names)
 build='import ast,pathlib\nast.parse(pathlib.Path("module.py").read_text(encoding="utf-8"))\nprint("ENDURANCE_BUILD_PASS")\n'
 return {'name':name,'objective':objective,'task':task+' Modify module.py and README.md only. Never edit tests/build/.autopilot. Run python test_module.py and python build.py.','files':{'module.py':stub,'README.md':'# '+name+'\n\nDocumentation incomplete.\n','test_module.py':tests,'build.py':build,'.gitignore':'.autopilot/\n__pycache__/\n'}}
