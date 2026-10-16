"""Compact planner guards: deterministic fixtures, never a Worker or GUI."""
import ast,copy,hashlib,json,os,pathlib,sys,unittest,uuid
from unittest.mock import patch
R=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'scripts'),str(R/'tests')]
import project_onboarding as data
import onboarding_planner as compact
import onboarding_hermes as native
from onboarding_long_fixture import objective

node=next(n for n in ast.parse((R/'tests/test-project-onboarding.py').read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='proposal')
ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),'fixture','exec'),ns)
BASE=R/'sandbox'/('compact-planner-'+uuid.uuid4().hex[:8]);BASE.mkdir()

def proposal():
    value=ns['proposal']()
    value['overview']={'objective_summary':'Suma Python validada sin modificar tests','tasks':['Implementar suma y documentación'],
        'research_requirements':[],'web_policy':'none','chatgpt_policy':'disabled','git_policy':'local_only_no_push',
        'restrictions':['Sólo el sandbox aprobado'],'completion_policy':compact.COMPLETION}
    return value

class Compact(unittest.TestCase):
    def setUp(self):self.p=BASE/self._testMethodName;self.p.mkdir();self.v=proposal()
    def test_compact_roundtrip(self):self.assertEqual(compact.decode(json.dumps(self.v)),self.v)
    def test_long_utf8_fixture(self):
        text=objective();self.assertGreater(len(text.encode()),17520);self.assertLessEqual(len(text.encode()),18000);self.assertIn('€',text);self.assertGreater(text.count('\n'),100)
    def test_raw_byte_cap(self):
        with self.assertRaisesRegex(ValueError,'PLAN_SIZE'):compact.decode('界'*6000)
    def test_duplicate_key_denied(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):compact.decode('{"plan":{},"plan":{}}')
    def test_nan_denied(self):
        with self.assertRaisesRegex(ValueError,'NONSTANDARD'):compact.decode('{"x":NaN}')
    def test_live_overview_required(self):
        del self.v['overview']
        with self.assertRaisesRegex(ValueError,'ENVELOPE'):compact.decode(json.dumps(self.v))
    def test_summary_cannot_repeat_brief(self):
        self.v['overview']['objective_summary']='x'*361
        with self.assertRaisesRegex(ValueError,'SUMMARY'):compact.validate(self.v)
    def test_seed_byte_cap(self):
        self.v['seed_files']={'test.py':'x'*8193}
        with self.assertRaisesRegex(ValueError,'SEED_SIZE'):compact.validate(self.v)
    def test_criteria_count_cap(self):
        self.v['plan']['criteria']*=17
        with self.assertRaisesRegex(ValueError,'CRITERIA'):compact.validate(self.v)
    def test_task_count_cap(self):
        self.v['overview']['tasks']=['a']*9
        with self.assertRaisesRegex(ValueError,'LIST_BOUND'):compact.validate(self.v)
    def test_no_push_policy_fixed(self):
        self.v['overview']['git_policy']='push'
        with self.assertRaisesRegex(ValueError,'POLICY'):compact.validate(self.v)
    def test_web_policy_matches_plan(self):
        self.v['overview']['web_policy']='governed_https'
        with self.assertRaisesRegex(ValueError,'WEB_POLICY'):compact.validate(self.v)
    def test_loopback_research_denied(self):
        self.v['plan']['research']={'url':'https://127.0.0.1/private'};self.v['overview']['web_policy']='governed_https'
        with self.assertRaisesRegex(ValueError,'PUBLIC_HTTPS'):compact.validate(self.v)
    def test_governed_research_retained(self):
        self.v['plan']['research']={'url':'https://developer.mozilla.org/en-US/docs/Web/Accessibility'};self.v['overview']['web_policy']='governed_https';self.v['overview']['research_requirements']=['Revisar accesibilidad MDN']
        bound=data.bind_proposal(self.p,'Implementar suma con investigación oficial',self.v);self.assertEqual(bound['proposal']['plan']['research'],self.v['plan']['research'])
    def test_worker_budget_not_increased(self):
        self.v['plan']['phase_timeout_seconds']=301
        with self.assertRaisesRegex(ValueError,'BUDGET_NOT_ADMITTED'):data.bind_proposal(self.p,'Implementar suma',self.v)
    def test_original_only_once_in_context_and_no_writes(self):
        text=objective();context=data.main({'action':'planner_context','project':str(self.p),'objective':text})
        payload=json.loads(context['prompt'].rsplit('\n',1)[1]);self.assertEqual(payload['objective'],text)
        self.assertEqual(context['objective_sha256'],hashlib.sha256(text.encode()).hexdigest());self.assertEqual(list(self.p.iterdir()),[])
        self.assertEqual(pathlib.Path(context['source_path']).read_bytes(),text.encode('utf-8'))
    def test_fixed_policies_are_derived_not_generated(self):
        for key in ('web_policy','chatgpt_policy','git_policy','completion_policy'):del self.v['overview'][key]
        self.v['plan']['research']={'url':'https://developer.mozilla.org/en-US/docs/Web/Accessibility'}
        result=compact.decode(json.dumps(self.v))
        self.assertEqual(result['overview']['web_policy'],'governed_https');self.assertEqual(result['overview']['git_policy'],'local_only_no_push')
    def test_unique_explicit_research_source_lowered(self):
        for key in ('web_policy','chatgpt_policy','git_policy','completion_policy'):del self.v['overview'][key]
        self.v['overview']['research_requirements']=['Consultar documentación oficial']
        result=compact.decode(json.dumps(self.v),'Investigar https://developer.mozilla.org/en-US/docs/Web/Accessibility antes de implementar')
        self.assertEqual(result['plan']['research']['url'],'https://developer.mozilla.org/en-US/docs/Web/Accessibility');self.assertEqual(result['overview']['web_policy'],'governed_https')
    def test_ambiguous_research_not_guessed(self):
        for key in ('web_policy','chatgpt_policy','git_policy','completion_policy'):del self.v['overview'][key]
        self.v['overview']['research_requirements']=['Investigar']
        with self.assertRaisesRegex(ValueError,'AMBIGUOUS'):compact.decode(json.dumps(self.v),'https://example.com https://other.example.com')
    def test_no_prepare_before_approval(self):
        bound=data.bind_proposal(self.p,'Implementar suma',self.v)
        with patch.dict(os.environ,{'DA_LAUNCHER_MUTEX_HELD':'1'}):
            with self.assertRaisesRegex(ValueError,'HUMAN_PLAN_APPROVAL_REQUIRED'):data.prepare_project(bound)
        self.assertEqual(list(self.p.iterdir()),[])
    def test_new_policy_and_normalizer_are_bound(self):
        hashes=data.policy_hashes();self.assertIn('config/onboarding-planner.json',hashes);self.assertIn('scripts/onboarding_planner.py',hashes)
    def test_seed_must_be_source_string(self):
        self.v['seed_files']={'test.js':{'not':'source'}}
        with self.assertRaisesRegex(ValueError,'SEED_SOURCE'):compact.validate(self.v)
    def test_yaml_literal_source_quotes_preserved(self):
        source='const re = /href="#[^"]*"/g;\nconst x = "UTF-8 ñ €";\n'
        self.v['seed_files']={'test.js':source}
        encoded=compact.yaml.safe_dump(self.v,allow_unicode=True)
        self.assertEqual(compact.decode(encoded)['seed_files']['test.js'],source)
    def test_yaml_duplicate_denied(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):compact.decode('plan: {}\nplan: {}')
    def test_yaml_alias_denied(self):
        with self.assertRaisesRegex(ValueError,'ALIAS'):compact.decode('plan: &a {}\nseed_files: *a')
    def test_yaml_custom_tag_denied(self):
        with self.assertRaises(compact.yaml.YAMLError):compact.decode('plan: !!python/object:builtins.object {}')
    def test_multiple_yaml_documents_denied(self):
        with self.assertRaises(compact.yaml.YAMLError):compact.decode('plan: {}\n---\nplan: {}')
    def native_request(self):return {'base_url':'http://127.0.0.1:8080/v1','model':'qwen36','project':str(self.p),'policy':compact.policy(),'disabled_toolsets':['terminal','file','web'],'prompt':'Synthetic no-op unit fixture'}
    def fake(self,tools=None,response=None):
        class Fake:
            last=None
            def __init__(self,**kw):
                Fake.last=self;self.kw=kw;self.tools=tools or [];self._fallback_chain=[];self.model=kw['model'];self.base_url=kw['base_url'];self.closed=False;self.called=False
            def run_conversation(self,prompt):self.called=True;return response or {'completed':True,'final_response':'{}','messages':[],'api_calls':1}
            def close(self):self.closed=True
        return Fake
    def test_native_request_caps_and_schema(self):
        cls=self.fake();native.run(self.native_request(),cls);kw=cls.last.kw
        self.assertEqual(kw['max_tokens'],4096);self.assertEqual(kw['max_iterations'],1);self.assertEqual(kw['fallback_model'],[])
        self.assertEqual(kw['request_overrides']['response_format']['type'],'json_schema');self.assertFalse(kw['request_overrides']['extra_body']['chat_template_kwargs']['enable_thinking']);self.assertTrue(cls.last.closed)
    def test_native_loaded_tools_denied_before_inference(self):
        cls=self.fake(tools=['terminal'])
        with self.assertRaisesRegex(ValueError,'READONLY'):native.run(self.native_request(),cls)
        self.assertFalse(cls.last.called);self.assertTrue(cls.last.closed)
    def test_native_tool_call_denied(self):
        cls=self.fake(response={'completed':True,'final_response':'{}','messages':[{'tool_calls':[{'name':'file'}]}]})
        with self.assertRaisesRegex(ValueError,'TOOL_CALL'):native.run(self.native_request(),cls)
    def test_native_wrong_route_denied(self):
        request=self.native_request();request['base_url']='https://example.invalid';cls=self.fake()
        with self.assertRaisesRegex(ValueError,'LOCAL_ROUTE'):native.run(request,cls)
        self.assertIsNone(cls.last)
    def test_native_incomplete_denied(self):
        cls=self.fake(response={'completed':False})
        with self.assertRaisesRegex(ValueError,'INCOMPLETE'):native.run(self.native_request(),cls)
    def test_native_oversize_denied(self):
        cls=self.fake(response={'completed':True,'final_response':'x'*16385})
        with self.assertRaisesRegex(ValueError,'PLAN_SIZE'):native.run(self.native_request(),cls)
    def test_actual_supervisor_profile_remains_readonly(self):
        runtime=data.main({'action':'planner_runtime'});self.assertEqual(runtime['status'],'PASS');self.assertIn('file',runtime['disabled_toolsets'])
    def test_seed_hash_is_computed_by_host(self):
        bound=data.bind_proposal(self.p,'Implementar suma',self.v);pin=bound['proposal']['plan']['immutable_files'][0]
        self.assertEqual(pin['sha256'],hashlib.sha256(self.v['seed_files'][pin['path']].encode()).hexdigest())
    def test_single_json_fence_supported(self):self.assertEqual(compact.decode('```json\n'+json.dumps(self.v)+'\n```'),self.v)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Compact))
    out=pathlib.Path(os.environ['COMPACT_PLANNER_E']);out.mkdir(parents=True,exist_ok=False)
    report={'status':'PASS' if result.wasSuccessful() else 'FAIL','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'sandbox':str(BASE),'inferences':0,'worker_starts':0,'gui_actions':0}
    (out/'RESULT.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report));raise SystemExit(0 if result.wasSuccessful() else 1)
