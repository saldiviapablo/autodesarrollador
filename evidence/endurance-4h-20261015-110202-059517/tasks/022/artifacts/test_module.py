import unittest,subprocess,sys,json
from module import parse_ledger,totals
class Acceptance(unittest.TestCase):
 def test_stage_specific_amount(self):
  self.assertEqual(totals(parse_ledger('date,category,amount\n2024-01-01,Task,28.125\n')),{'Task':'28.13'})

 def test_rows_unicode_and_rounding(self):
  r=parse_ledger('date,category,amount\n2024-02-29, Café ,1.005\n2024-03-01,"Comida, casa",-2.675\n')
  self.assertEqual(r,[{'date':'2024-02-29','category':'Café','amount':'1.01'},{'date':'2024-03-01','category':'Comida, casa','amount':'-2.68'}])
 def test_aggregate(self):
  self.assertEqual(totals(parse_ledger('date,category,amount\n2024-01-01,Z,0.10\n2024-01-01,A,0.20\n2024-01-02,Z,0.20\n')),{'A':'0.20','Z':'0.30'})
  self.assertEqual(list(totals([{'date':'2024-01-01','category':'Z','amount':'1.00'},{'date':'2024-01-01','category':'A','amount':'1.00'}])),['A','Z'])
 def test_header_only(self):self.assertEqual(parse_ledger('date,category,amount\n'),[])
 def test_invalid(self):
  for s in ['', 'wrong,header\n', 'date,category,amount\n2023-02-29,X,1\n','date,category,amount\n2024-1-01,X,1\n','date,category,amount\n2024-01-01,,1\n','date,category,amount\n2024-01-01,X,NaN\n','date,category,amount\n2024-01-01,X,Infinity\n','date,category,amount\n2024-01-01,X,bad\n','date,category,amount\n2024-01-01,X\n','date,category,amount\n2024-01-01,X,1,extra\n']:
   with self.subTest(s=s):
    with self.assertRaises(ValueError):parse_ledger(s)
 def test_cli(self):
  p=subprocess.run([sys.executable,'module.py'],input='date,category,amount\n2024-01-01,Ñ,1.005\n',text=True,capture_output=True);self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout)['totals'],{'Ñ':'1.01'})
  p=subprocess.run([sys.executable,'module.py'],input='bad',text=True,capture_output=True);self.assertEqual(p.returncode,2);self.assertNotIn('Traceback',p.stderr)

 def test_documentation(self):
  from pathlib import Path
  text=Path('README.md').read_text(encoding='utf-8');self.assertGreater(len(text),250);self.assertIn('module.py',text);self.assertIn('ValueError',text);self.assertIn('2',text)
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Acceptance))
 if result.wasSuccessful():print('ENDURANCE_TEST_PASS')
 raise SystemExit(0 if result.wasSuccessful() else 1)
