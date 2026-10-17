"""Saved-output build mapping: no models, commands, GUI or real project writes."""
import argparse,copy,hashlib,importlib.util,json,os,pathlib,sys,unittest
from unittest.mock import patch
import jsonschema

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import onboarding_planner as planner
import onboarding_hermes as native
import project_onboarding as data

class Build(unittest.TestCase):
    def setUp(self):
        self.value=copy.deepcopy(SAVED)
        self.project=compact.BASE/self._testMethodName;self.project.mkdir()
    def decode(self,objective='Ejecutar npm run build'):
        return planner.decode(json.dumps(self.value,ensure_ascii=False),objective)
    def test_real_failure_reproduced(self):
        with self.assertRaisesRegex(ValueError,'BUILD_OR_EXPLICIT_NO_BUILD_REASON_REQUIRED'):
            data.bind_proposal(self.project,'Objetivo sin comando de build',self.decode(''))
    def test_real_output_with_saved_explicit_brief(self):
        self.assertIn('npm run build',OBJECTIVE)
        result=self.decode(OBJECTIVE);bound=data.bind_proposal(self.project,OBJECTIVE,result)
        self.assertIn(['npm','run','build'],[c['argv'] for c in bound['proposal']['plan']['builds']])
        self.assertNotIn('no_build_reason',result['plan'])
        self.assertEqual(list(self.project.iterdir()),[])
        self.assertEqual(result['seed_files'],self.value['seed_files'])
        for field in ('tests','criteria','artifacts','allowed_files','global_timeout_seconds','restart_budget'):
            self.assertEqual(result['plan'][field],self.value['plan'][field])
    def test_no_build_exemption_invented(self):
        result=self.decode('Proyecto sin build explícito')
        self.assertNotIn('builds',result['plan']);self.assertNotIn('no_build_reason',result['plan'])
        with self.assertRaisesRegex(ValueError,'BUILD_OR_EXPLICIT_NO_BUILD_REASON_REQUIRED'):
            data.bind_proposal(self.project,'Proyecto sin build explícito',result)
    def test_existing_build_preserved_and_no_duplicate(self):
        command={'id':'compile','argv':['npm','run','build'],'marker':'compiled','timeout_seconds':90}
        self.value['plan']['builds']=[command]
        self.assertEqual(self.decode()['plan']['builds'],[command])
    def test_other_build_not_substitute_for_explicit_command(self):
        command={'id':'verify','argv':['node','verify.js'],'marker':'VERIFY_PASS','timeout_seconds':30}
        self.value['plan']['builds']=[command]
        result=self.decode()['plan']['builds'];self.assertEqual(result[0],command)
        self.assertEqual(result[1]['argv'],['npm','run','build'])
    def test_normalization_idempotent(self):
        result=self.decode();self.assertEqual(planner.decode(json.dumps(result),'npm run build'),result)
    def test_wrong_script_not_mapped(self):
        for text in ('npm run builder','npm run build:other','npm run build.js','pnpm run build'):
            with self.subTest(text=text):self.assertNotIn('builds',self.decode(text)['plan'])
    def test_explicit_build_overrides_exemption(self):
        self.value['plan']['no_build_reason']='Static files need no build'
        result=self.decode();self.assertNotIn('no_build_reason',result['plan']);self.assertTrue(result['plan']['builds'])
    def test_explicit_no_build_reason_retained_without_command(self):
        self.value['plan']['no_build_reason']='Static HTML served directly without bundling'
        result=self.decode('HTML estático');data.bind_proposal(self.project,'HTML estático',result)
        self.assertEqual(result['plan']['no_build_reason'],self.value['plan']['no_build_reason'])
    def test_command_id_collision_avoided(self):
        self.value['plan']['tests'][0]['id']='npm-build'
        self.value['plan']['criteria']=[dict(c,test_id='npm-build') for c in self.value['plan']['criteria']]
        result=self.decode();data.bind_proposal(self.project,'npm run build',result)
        self.assertEqual(result['plan']['builds'][0]['id'],'npm-build-explicit')
    def test_no_worker_or_prepare_before_approval(self):
        bound=data.bind_proposal(self.project,'npm run build',self.decode())
        with patch.dict(os.environ,{'DA_LAUNCHER_MUTEX_HELD':'1'}):
            with self.assertRaisesRegex(ValueError,'HUMAN_PLAN_APPROVAL_REQUIRED'):data.prepare_project(bound)
        self.assertEqual(list(self.project.iterdir()),[])
    def test_generation_schema_and_compiler_split_build_responsibility(self):
        fake=compact.Compact().fake()
        native.run({'model':'qwen36','base_url':'http://127.0.0.1:8080/v1','policy':planner.policy(),
                    'disabled_toolsets':['all'],'project':str(self.project),'prompt':'mock only'},fake)
        schema=fake.last.kw['request_overrides']['response_format']['json_schema']['schema']
        validator=jsonschema.Draft7Validator(schema);jsonschema.Draft7Validator.check_schema(schema)
        validator.validate(self.value)
        fixed=self.decode(OBJECTIVE)
        validator.validate(fixed)
        self.assertIn(['npm','run','build'],[c['argv'] for c in fixed['plan']['builds']])
        self.assertFalse(schema['properties']['plan']['additionalProperties'])
        missing=copy.deepcopy(self.value)
        with self.assertRaisesRegex(ValueError,'BUILD_OR_EXPLICIT_NO_BUILD_REASON_REQUIRED'):
            data.bind_proposal(self.project,'Sin build explícito',planner.decode(json.dumps(missing),'Sin build explícito'))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for option in ('fixture','objective','evidence'):parser.add_argument('--'+option,required=True)
    args=parser.parse_args();source=pathlib.Path(args.fixture);brief=pathlib.Path(args.objective)
    raw=source.read_bytes();original=brief.read_bytes()
    SAVED=json.loads(json.loads(raw.decode('utf-8-sig'))['native_result']['text']);OBJECTIVE=original.decode('utf-8-sig')
    spec=importlib.util.spec_from_file_location('compact_tests',ROOT/'tests/test-onboarding-compact.py')
    compact=importlib.util.module_from_spec(spec);spec.loader.exec_module(compact)
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Build),
                             unittest.defaultTestLoader.loadTestsFromTestCase(compact.Compact)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    unchanged=source.read_bytes()==raw and brief.read_bytes()==original
    status='PASS' if result.wasSuccessful() and unchanged else 'FAIL'
    report={'status':status,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            **{gate:status for gate in ('REAL_FAILURE_FIXTURE','EXPLICIT_BUILD_PRESERVED','BUILD_GATE_STRICT','NO_WORKER_BEFORE_APPROVAL')},
            'fixture':str(source),'fixture_sha256':hashlib.sha256(raw).hexdigest(),
            'objective_source':str(brief),'objective_sha256':hashlib.sha256(original).hexdigest(),
            'original_files_unchanged':unchanged,'inferences':0,'worker_starts':0,'gui_actions':0,
            'sandbox':str(compact.BASE),'note':'Saved output replayed in disposable sandbox with preserved full brief containing explicit build; no real project execution.'}
    out=pathlib.Path(args.evidence);out.mkdir(parents=True,exist_ok=False)
    (out/'RESULT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report));raise SystemExit(0 if status=='PASS' else 1)
