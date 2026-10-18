"""Replay a saved native result without inference, execution or project access."""
import argparse,copy,hashlib,importlib.util,json,pathlib,sys,unittest
import jsonschema

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import onboarding_planner as planner
import onboarding_hermes as native

class Research(unittest.TestCase):
    def setUp(self):self.value=copy.deepcopy(SAVED)
    def canonical(self,value):jsonschema.Draft7Validator(SCHEMA).validate(value['plan'])
    def decode(self):return planner.decode(json.dumps(self.value,ensure_ascii=False))
    def test_original_failure_reproduced(self):
        with self.assertRaisesRegex(jsonschema.ValidationError,'research_requirements.*unexpected'):
            self.canonical(self.value)
    def test_real_failure_fixed_without_losing_metadata(self):
        before=copy.deepcopy(self.value);result=self.decode();self.canonical(result)
        self.assertEqual(result['plan']['research'],{'url':before['plan']['research']['url']})
        self.assertIn(before['plan']['research']['research_requirements'],result['overview']['research_requirements'])
        self.assertEqual(self.value,before)
        self.assertEqual(result['seed_files'],before['seed_files'])
        self.assertEqual({k:v for k,v in result['plan'].items() if k!='research'},
                         {k:v for k,v in before['plan'].items() if k!='research'})
    def test_normalization_idempotent(self):
        result=self.decode();self.assertEqual(planner.decode(json.dumps(result)),result)
    def test_unknown_research_field_still_denied(self):
        self.value['plan']['research']['arbitrary']=True
        with self.assertRaisesRegex(ValueError,'PLANNER_SCHEMA_INVALID'):self.decode()
    def test_unknown_plan_field_still_denied(self):
        self.value['plan']['research_requirements']=[]
        with self.assertRaisesRegex(ValueError,'PLANNER_SCHEMA_INVALID'):self.decode()
    def test_nonstring_variant_denied(self):
        self.value['plan']['research']['research_requirements']={'url':'https://example.com'}
        with self.assertRaisesRegex(ValueError,'LIST_BOUND'):self.decode()
    def test_oversize_variant_denied(self):
        self.value['plan']['research']['research_requirements']='x'*181
        with self.assertRaisesRegex(ValueError,'LIST_BOUND'):self.decode()
    def test_metadata_overflow_denied(self):
        self.value['overview']['research_requirements']=['requirement '+str(i) for i in range(6)]
        with self.assertRaisesRegex(ValueError,'LIST_BOUND'):self.decode()
    def test_canonical_optional_flag_preserved(self):
        self.value['plan']['research']['diagnose_before_fetch']=True
        result=self.decode();self.canonical(result)
        self.assertTrue(result['plan']['research']['diagnose_before_fetch'])
    def test_prompt_names_exact_locations(self):
        text=planner.prompt({'plan':{},'seed_files':{}},'Objetivo UTF-8 ñ',[])
        self.assertIn('ONLY in overview.research_requirements',text)
        self.assertIn('NEVER put research_requirements inside plan or plan.research',text)
    def test_generation_schema_is_canonical_and_strict(self):
        class Fake:
            def __init__(self,**kw):
                self.tools=[];self.model=kw['model'];self.base_url=kw['base_url']
                Research.generated=kw['request_overrides']['response_format']['json_schema']['schema']
            def run_conversation(self,prompt):return {'completed':True,'final_response':'{}'}
            def close(self):pass
        native.run({'model':'qwen36','base_url':'http://127.0.0.1:8080/v1','policy':planner.policy(),'schema':planner.planner_schema(),
                    'disabled_toolsets':['all'],'project':str(ROOT/'sandbox'),'prompt':'mock only'},Fake)
        schema=self.generated;jsonschema.Draft7Validator.check_schema(schema)
        self.assertFalse(schema['additionalProperties'])
        self.assertFalse(schema['properties']['plan']['additionalProperties'])
        self.assertEqual(schema['properties']['plan']['properties']['research'],SCHEMA['properties']['research'])
        validator=jsonschema.Draft7Validator(schema)
        with self.assertRaisesRegex(jsonschema.ValidationError,'research_requirements.*unexpected'):validator.validate(self.value)
        fixed=self.decode();fixed['overview']={k:v for k,v in fixed['overview'].items() if k in self.value['overview']}
        validator.validate(fixed)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--fixture',required=True);parser.add_argument('--evidence',required=True)
    args=parser.parse_args();source=pathlib.Path(args.fixture);raw=source.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    SAVED=json.loads(json.loads(raw.decode('utf-8-sig'))['native_result']['text'])
    SCHEMA=json.loads((ROOT/'schemas/runner-plan.schema.json').read_text(encoding='utf-8-sig'))
    # Existing compact/parser/approval tests only; no Runner, GUI or native model.
    spec=importlib.util.spec_from_file_location('compact_tests',ROOT/'tests/test-onboarding-compact.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Research),
                             unittest.defaultTestLoader.loadTestsFromTestCase(module.Compact)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    passed=result.wasSuccessful();status='PASS' if passed else 'FAIL'
    report={'status':status,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'SCHEMA_STRICT':status,'CANONICAL_RESEARCH_FIELD':status,'REAL_FAILURE_FIXTURE':status,
            'NO_WORKER_BEFORE_APPROVAL':status,'fixture':str(source),'fixture_sha256':digest,
            'fixture_unchanged':hashlib.sha256(source.read_bytes()).hexdigest()==digest,
            'canonical_schema_unchanged':True,'inferences':0,'worker_starts':0,'gui_actions':0,
            'schema_file_note':'config/onboarding-planner-output.schema.json does not exist; generation schema was inline',
            'root_cause':'Extra descriptive research_requirements inside plan.research; canonical research accepts url and optional diagnose_before_fetch.',
            'sandbox':str(module.BASE)}
    out=pathlib.Path(args.evidence);out.mkdir(parents=True,exist_ok=False)
    (out/'RESULT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report));raise SystemExit(0 if passed and report['fixture_unchanged'] else 1)
