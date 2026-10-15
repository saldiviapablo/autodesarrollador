import unittest,subprocess,sys,json,copy
from module import catalog,duplicate_groups
def entry(p,s=1,h='a'*64):return {'path':p,'size':s,'sha256':h}
class Acceptance(unittest.TestCase):
 def test_stage_specific_names(self):
  self.assertEqual(duplicate_groups([entry('30/ñ'),entry('30/a')]),[['30/a','30/ñ']])

 def test_sort_unicode(self):
  x=[entry('ñ/b.txt'),entry('a.txt')];b=copy.deepcopy(x);self.assertEqual(catalog(x),[entry('a.txt'),entry('ñ/b.txt')]);self.assertEqual(x,b);self.assertEqual(catalog([]),[])
 def test_duplicates(self):self.assertEqual(duplicate_groups([entry('z'),entry('a'),entry('b',2),entry('c',2),entry('unique',3)]),[['a','z'],['b','c']])
 def test_invalid_paths(self):
  for p in ['', '/x','../x','a/../b','./a','a//b','a/','C:x','a\\b','a\x00b','a\nb']:
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

 def test_documentation(self):
  from pathlib import Path
  text=Path('README.md').read_text(encoding='utf-8');self.assertGreater(len(text),250);self.assertIn('module.py',text);self.assertIn('ValueError',text);self.assertIn('2',text)
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Acceptance))
 if result.wasSuccessful():print('ENDURANCE_TEST_PASS')
 raise SystemExit(0 if result.wasSuccessful() else 1)
