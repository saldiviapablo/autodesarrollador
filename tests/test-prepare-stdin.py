"""Large canonical Prepare transport, read-only validation and fixed argv."""
import ast,base64,json,os,pathlib,subprocess,sys,unittest,uuid
from unittest.mock import patch
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'runner'))
import prepare
BASE=R/'sandbox'/('prepare-stdin-'+uuid.uuid4().hex[:8]);BASE.mkdir()
tree=ast.parse((R/'tests/test-project-onboarding.py').read_text(encoding='utf-8'));node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='proposal');ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),'fixture','exec'),ns)

class Transport(unittest.TestCase):
    def setUp(self):
        self.p=BASE/self._testMethodName;self.p.mkdir();v=ns['proposal']();path=BASE/(self._testMethodName+'.json');path.write_text(json.dumps(v['plan']),encoding='utf-8')
        self.request={'project':str(self.p),'objective':'Objetivo largo á ñ € con saltos\n'*1800,'criteria':[x['criterion'] for x in v['plan']['criteria']],'plan':str(path)}
    def encoded(self):return base64.b64encode(json.dumps({'request':self.request,'binding':prepare.admission(self.request)},ensure_ascii=False).encode()).decode()
    def test_apply_argv_does_not_contain_large_payload(self):
        with patch.object(prepare.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'','')) as call:
            result=prepare.execute(self.request)
        self.assertEqual(result['reason'],'APPLY_MARKER_MISSING');argv=call.call_args.args[0]
        self.assertIn('-ReadRequestFromStdin',argv);self.assertLess(len(subprocess.list2cmdline(argv)),1000);self.assertGreater(len(call.call_args.kwargs['input']),32767);self.assertEqual(list(self.p.iterdir()),[])
    def test_long_validate_stdin_zero_writes(self):
        p=subprocess.run([sys.executable,'-B',str(R/'runner/prepare.py'),'--request-stdin','--validate-only'],input=self.encoded().encode(),capture_output=True,timeout=20)
        self.assertEqual(p.returncode,0,p.stdout);self.assertEqual(json.loads(p.stdout)['prepare_write_count'],0);self.assertEqual(list(self.p.iterdir()),[])
    def test_changed_binding_stdin_denied_zero_writes(self):
        payload=json.loads(base64.b64decode(self.encoded()));payload['binding']['root_existed']=False
        encoded=base64.b64encode(json.dumps(payload).encode())
        p=subprocess.run([sys.executable,'-B',str(R/'runner/prepare.py'),'--request-stdin','--validate-only'],input=encoded,capture_output=True,timeout=20)
        self.assertNotEqual(p.returncode,0);self.assertIn('PREPARE_ADMISSION_CHANGED',p.stdout.decode());self.assertEqual(list(self.p.iterdir()),[])
    def test_powershell_utf8_bom_stdin_preserved(self):
        p=subprocess.run([sys.executable,'-B',str(R/'runner/prepare.py'),'--request-stdin','--validate-only'],input=b'\xef\xbb\xbf'+self.encoded().encode()+b'\r\n',capture_output=True,timeout=20)
        self.assertEqual(p.returncode,0,p.stdout);self.assertEqual(list(self.p.iterdir()),[])

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Transport));e=pathlib.Path(os.environ['PREPARE_STDIN_E']);e.mkdir(exist_ok=False)
    report={'status':'PASS' if result.wasSuccessful() else 'FAIL','tests':result.testsRun,'sandbox':str(BASE),'inferences':0,'worker_starts':0,'gui_actions':0};(e/'RESULT.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report));raise SystemExit(0 if result.wasSuccessful() else 1)
