import unittest,subprocess,sys,json,copy
from module import merge_intervals,gaps,peak_load
class Acceptance(unittest.TestCase):
 def test_stage_specific_window(self):
  self.assertEqual(gaps([[20,22]],19,23),[(19,20),(22,23)])

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

 def test_documentation(self):
  from pathlib import Path
  text=Path('README.md').read_text(encoding='utf-8');self.assertGreater(len(text),250);self.assertIn('module.py',text);self.assertIn('ValueError',text);self.assertIn('2',text)
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Acceptance))
 if result.wasSuccessful():print('ENDURANCE_TEST_PASS')
 raise SystemExit(0 if result.wasSuccessful() else 1)
