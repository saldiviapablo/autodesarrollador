"""Focused post-v1 launcher tests. No inference, bridge send or prior phase run."""
import copy, hashlib, importlib.util, json, os, pathlib, subprocess, sys, time, unittest, uuid
R=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
import project_onboarding as o
E=R/'evidence'/('launcher-multi-project-'+time.strftime('%Y%m%d-%H%M%S'))
E.mkdir()
BASE=R/'sandbox'/('launcher-cert-'+uuid.uuid4().hex[:8]);BASE.mkdir()
RESULTS={}

def make(name):
    p=BASE/name;p.mkdir();return p

def proposal():
    text='from module import add\nassert add(2, 3) == 5\nassert add(-2, 3) == 1\nprint("ADDITION_PASS")\n'
    return {'seed_files':{'test_acceptance.py':text},'plan':{'schema_version':'1.0','backend':'live',
        'task':'Implement add(a,b) in module.py; return their sum. Never modify immutable acceptance tests.',
        'allowed_files':['module.py','README.md'],'tests':[{'id':'unit','argv':['python','test_acceptance.py'],'marker':'ADDITION_PASS'}],
        'builds':[],'no_build_reason':'Small Python test fixture; no deployment artifact',
        'criteria':[{'criterion':'add returns the sum including negative arguments','test_id':'unit'}],
        'artifacts':[{'path':'module.py'}],'immutable_files':[],
        'phase_timeout_seconds':300,'global_timeout_seconds':2700,'max_cycles':5,'restart_budget':2}}

def action(payload):
    env=dict(os.environ,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',PSModulePath='C:/Windows/System32/WindowsPowerShell/v1.0/Modules')
    r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-File',str(R/'scripts/project-launcher-action.ps1')],
        input=json.dumps(payload,ensure_ascii=False),capture_output=True,text=True,encoding='utf-8',timeout=180,env=env)
    if r.returncode: raise AssertionError(r.stdout+'\n'+r.stderr)
    return json.loads(r.stdout)

def approve_fixture(bound):
    # Synthetic human decision for the non-inference integration fixture only.
    # This is not evidence that a real person approved a live Worker run.
    request=dict(bound,action='approve_plan',decision='APPROVE',method='HUMAN_PLAN_REVIEW')
    grant=action(request)
    return dict(bound,approval_id=grant['approval_id'])

class Checks(unittest.TestCase):
    def setUp(self): self.p=make(self._testMethodName)
    def tearDown(self): RESULTS[self._testMethodName]='EXECUTED'
    def test_empty_new_project(self): self.assertFalse(o.inspect(self.p)['prepared']);self.assertEqual(list(self.p.iterdir()),[])
    def test_nonexistent_path_denied(self):
        with self.assertRaises(ValueError): o.project(self.p/'missing')
        self.assertEqual(list(self.p.iterdir()),[])
    def test_relative_path_denied(self):
        with self.assertRaises(ValueError): o.project('sandbox')
    def test_infrastructure_denied(self):
        for p in [R,R.parent,R/'scripts',R/'tools',R/'config',R/'runner',R/'sandbox']:
            with self.assertRaises(ValueError): o.project(p)
    def test_reparse_denied(self):
        target=make('junction-target');link=self.p/'link'
        quoted=lambda x:"'"+str(x).replace("'","''")+"'"
        r=subprocess.run(['powershell.exe','-NoProfile','-Command','New-Item -ItemType Junction -Path '+quoted(link)+' -Value '+quoted(target)+' | Out-Null'],capture_output=True)
        self.assertEqual(r.returncode,0,r.stderr)
        try:
            with self.assertRaises(ValueError): o.project(link)
            self.assertEqual(list(target.iterdir()),[])
        finally: link.rmdir() # exact owned junction only; not its target
    def test_unicode_spaces(self):
        p=make('Proyecto áéíóú ñ € ° espacios');self.assertEqual(o.project(p),p)
    def test_multiline_long_utf8(self):
        text=('¿Áéíóú ñ € ° "comillas"?\nsegunda línea\r\n'*800)
        self.assertEqual(o.safe_text(text),text)
    def test_md_txt_exact_utf8(self):
        text='áéíóú ñ ¿? € ° "comillas"\r\nlinea 2\n'
        for suffix in ['.md','.txt','.MD']:
            p=self.p/('brief'+suffix);p.write_bytes(text.encode('utf-8'))
            self.assertEqual(o.main({'action':'brief','path':str(p)})['text'],text)
    def test_invalid_utf8_denied(self):
        p=self.p/'brief.txt';p.write_bytes(b'bad\xff')
        with self.assertRaises(UnicodeError):o.main({'action':'brief','path':str(p)})
    def test_wrong_brief_extension_denied(self):
        p=self.p/'brief.exe';p.write_text('not a brief')
        with self.assertRaises(ValueError):o.main({'action':'brief','path':str(p)})
    def test_secret_not_persisted(self):
        value='secret'+'=synthetic_onboarding_value'
        with self.assertRaises(ValueError):o.safe_text(value)
        self.assertEqual(list(self.p.iterdir()),[])
    def test_missing_mapping_denied_before_write(self):
        v=proposal();v['plan']['criteria'][0]['test_id']='nonexistent'
        with self.assertRaises(ValueError):o.bind_proposal(self.p,'Implement addition',v)
        self.assertEqual(list(self.p.iterdir()),[])
    def test_outside_seed_denied(self):
        v=proposal();v['seed_files']['../escape.py']='bad'
        with self.assertRaises(ValueError):o.bind_proposal(self.p,'Implement addition',v)
        self.assertFalse((BASE/'escape.py').exists())
    def test_immutable_not_worker_output(self):
        v=proposal();v['plan']['allowed_files'].append('test_acceptance.py')
        with self.assertRaises(ValueError):o.bind_proposal(self.p,'Implement addition',v)
    def test_no_test_overwrite(self):
        (self.p/'test_acceptance.py').write_text('ORIGINAL')
        with self.assertRaises(ValueError):o.bind_proposal(self.p,'Implement addition',proposal())
        self.assertEqual((self.p/'test_acceptance.py').read_text(),'ORIGINAL')
    def test_no_implicit_bridge_or_probe(self):
        for key,value in [('backend','probe'),('consultation',{'id':'not-authorized'}),('sandbox_crash_boundary',True)]:
            v=proposal();v['plan'][key]=value
            with self.assertRaises(ValueError):o.bind_proposal(self.p,'Implement addition',v)
    def test_no_unmapped_seed(self):
        v=proposal();v['seed_files']['module.py']='def add(a,b): return 0'
        with self.assertRaises(ValueError):o.bind_proposal(self.p,'Implement addition',v)
    def test_canonical_prepare_isolation_history(self):
        p=self.p;other=make('Proyecto B independiente')
        bound=o.bind_proposal(p,'Implement addition á ñ € °',proposal());bound.update(action='prepare',new_objective=False)
        self.assertEqual(list(p.iterdir()),[]) # proposal/cancel path has no writes
        bound=approve_fixture(bound)
        result=action(bound);self.assertEqual(result['status'],'PASS')
        first=o.inspect(p);self.assertTrue(first['prepared']);self.assertTrue(first['admission']['contract']['authorized'])
        self.assertFalse((p/'.autopilot/LOCK.json').exists());self.assertTrue(pathlib.Path(first['admission']['receipt_path']).exists())
        self.assertTrue((p/'QWEN.md').exists());self.assertTrue((p/'.git').is_dir())
        for name in ['STATE.json','STATE.md','EVENTS.jsonl','RUN-CONTRACT.yaml','RUN-PLAN.json','HEARTBEAT.json','logs','reports','evidence','checkpoints']:
            self.assertTrue((p/'.autopilot'/name).exists(),name)
        before={str(f.relative_to(p)):o.contract.sha(f) for f in (p/'.autopilot').rglob('*') if f.is_file()}
        second=o.bind_proposal(other,'Implement independent addition',proposal());second.update(action='prepare',new_objective=False)
        action(approve_fixture(second))
        self.assertEqual(before,{str(f.relative_to(p)):o.contract.sha(f) for f in (p/'.autopilot').rglob('*') if f.is_file()})
        self.assertNotEqual(first['admission']['receipt_path'],o.inspect(other)['admission']['receipt_path'])
        # New objective keeps every byte of the prior operational history.
        v=proposal();v['seed_files']={};v['plan']['immutable_files']=first['admission']['plan']['immutable_files']
        b=o.bind_proposal(p,'Document the already approved addition behavior',v);b.update(action='prepare',new_objective=True)
        result=action(approve_fixture(b));history=pathlib.Path(result['history'])
        self.assertNotEqual(first['run_id'],o.inspect(p)['run_id'])
        for name,sha in before.items():self.assertEqual(o.contract.sha(history/name),sha)
        self.assertEqual(list(other.glob('.autopilot-history/*')),[])
        (E/'CANONICAL-PREPARE.json').write_text(json.dumps({'status':'PASS','projects':[str(p),str(other)],'previous_run':first['run_id'],'new_run':o.inspect(p)['run_id'],'history':str(history),'old_operational_files_unchanged':len(before)},indent=2),encoding='utf-8')
    def test_changed_project_denied(self):
        b=o.bind_proposal(self.p,'Implement addition',proposal());b.update(action='prepare')
        (self.p/'new.txt').write_text('user change')
        os.environ['DA_LAUNCHER_MUTEX_HELD']='1'
        try:
            with self.assertRaisesRegex(ValueError,'PROJECT_CHANGED'):o.prepare_project(b)
        finally:os.environ.pop('DA_LAUNCHER_MUTEX_HELD')
        self.assertFalse((self.p/'.autopilot').exists())
    def test_prepare_mutex_required(self):
        b=o.bind_proposal(self.p,'Implement addition',proposal())
        with self.assertRaisesRegex(ValueError,'RUN_MUTEX_REQUIRED'):o.prepare_project(b)

if __name__=='__main__':
    suite=(unittest.defaultTestLoader.loadTestsFromNames(sys.argv[1:],module=sys.modules[__name__])
           if len(sys.argv)>1 else unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    out={'status':'PASS' if result.wasSuccessful() else 'FAIL','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'sandbox':str(BASE),'scope':'deterministic data/Prepare tests only; native UI and live start/stop certified separately'}
    (E/'DETERMINISTIC.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(dict(out,evidence=str(E))))
    sys.exit(0 if result.wasSuccessful() else 1)
