"""View/controller tests without a desktop, cursor, inference or real approval.

Human choices are simulated only in unit fixtures; these tests never Start.
"""
import contextlib,copy,datetime,importlib.util,json,os,pathlib,sys,tempfile,unittest,uuid
from unittest.mock import Mock,patch
R=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
import project_onboarding as data
import project_launcher_ui as ui
spec=importlib.util.spec_from_file_location('onboard_fixture',R/'tests/test-project-onboarding.py')
# Load fixture definitions without executing its module-level output creation.
import ast
tree=ast.parse((R/'tests/test-project-onboarding.py').read_text(encoding='utf-8'))
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='proposal')
fixture_namespace={};exec(compile(ast.Module(body=[node],type_ignores=[]),'fixture-proposal','exec'),fixture_namespace)
proposal=fixture_namespace['proposal']
BASE=R/'sandbox'/('launcher-flow-'+uuid.uuid4().hex[:8]);BASE.mkdir()

@contextlib.contextmanager
def mutation_scope():
    with patch.dict(os.environ,{'DA_LAUNCHER_MUTEX_HELD':'1'}):yield

class Flow(unittest.TestCase):
    def setUp(self):
        self.p=BASE/self._testMethodName;self.p.mkdir()
        self.bound=data.bind_proposal(self.p,'Implement addition with deterministic acceptance',proposal())
    def app(self):
        a=object.__new__(ui.App);a.root=object();a.project=None;a.show=Mock();a.event=Mock();a.objective=Mock(return_value=None);a.wait_choice=Mock(return_value='cancel');return a
    def grant(self,bound=None):
        b=bound or self.bound
        with mutation_scope():return data.approve_plan(dict(b,decision='APPROVE',method='HUMAN_PLAN_REVIEW'))
    def test_prepare_without_prior_approval_zero_writes(self):
        with mutation_scope(),patch.object(data.prepare,'execute') as call:
            with self.assertRaisesRegex(ValueError,'HUMAN_PLAN_APPROVAL_REQUIRED'):data.prepare_project(self.bound)
            call.assert_not_called()
        self.assertEqual(list(self.p.iterdir()),[])
    def test_no_implicit_approval_decision(self):
        with mutation_scope():
            with self.assertRaisesRegex(ValueError,'EXPLICIT_HUMAN_PLAN_REVIEW_REQUIRED'):data.approve_plan(self.bound)
        self.assertEqual(list(self.p.iterdir()),[])
    def test_grant_bound_and_consumed_once(self):
        grant=self.grant();b=dict(self.bound,approval_id=grant['approval_id'])
        self.assertEqual(data.consume_plan_approval(b)['binding'],b['binding'])
        with self.assertRaises(FileExistsError):data.consume_plan_approval(b)
        self.assertEqual(list(self.p.iterdir()),[])
    def test_cross_project_approval_denied(self):
        grant=self.grant();p=BASE/(self._testMethodName+'-B');p.mkdir()
        b=data.bind_proposal(p,self.bound['objective'],proposal());b['approval_id']=grant['approval_id']
        with self.assertRaisesRegex(ValueError,'HUMAN_APPROVAL_BINDING_MISMATCH'):data.consume_plan_approval(b)
    def test_policy_changed_requires_new_review(self):
        changed=dict(data.policy_hashes(),unapproved='changed')
        with patch.object(data,'policy_hashes',return_value=changed):
            with self.assertRaisesRegex(ValueError,'PREPARATION_POLICY_CHANGED'):data.validate_binding(self.bound)
    def test_plan_changed_denied(self):
        b=copy.deepcopy(self.bound);b['proposal']['plan']['task']='An unreviewed replacement task'
        with self.assertRaisesRegex(ValueError,'PROPOSAL_BINDING_CHANGED'):data.validate_binding(b)
    def test_budget_increase_denied(self):
        for key,value in [('global_timeout_seconds',2701),('phase_timeout_seconds',301),('max_cycles',6),('restart_budget',3)]:
            v=proposal();v['plan'][key]=value
            with self.assertRaisesRegex(ValueError,'ONBOARDING_BUDGET_NOT_ADMITTED'):data.bind_proposal(self.p,'Implement addition',v)
    def test_system_directories_denied_readonly(self):
        for name in ('SystemRoot','ProgramFiles','LOCALAPPDATA'):
            value=os.environ.get(name)
            if value:
                with self.assertRaisesRegex(ValueError,'SYSTEM_DIRECTORY_NOT_A_MANAGED_PROJECT'):data.project(value)
    def test_noargs_calls_native_picker_boundary(self):
        app=self.app()
        with patch.object(ui.filedialog,'askdirectory',return_value=str(self.p)) as select:
            app.launch('');select.assert_called_once();self.assertTrue(select.call_args.kwargs['mustexist'])
        app.objective.assert_called_once();self.assertEqual(list(self.p.iterdir()),[])
    def test_argument_skips_picker(self):
        app=self.app()
        with patch.object(ui.filedialog,'askdirectory') as select:app.launch(str(self.p));select.assert_not_called()
        app.objective.assert_called_once();self.assertEqual(list(self.p.iterdir()),[])
    def test_picker_cancel_zero_project_writes(self):
        app=self.app()
        with patch.object(ui.filedialog,'askdirectory',return_value=''),patch.object(data,'inspect') as inspect:
            app.launch('');inspect.assert_not_called()
        app.objective.assert_not_called();self.assertEqual(list(self.p.iterdir()),[])
    def test_human_deny_no_prepare(self):
        app=self.app();self.assertFalse(app.approve_plan(self.bound));app.wait_choice.assert_called_once()
        self.assertEqual(list(self.p.iterdir()),[])
    def test_one_positive_view_choice(self):
        app=self.app();app.wait_choice.return_value='approve';self.assertTrue(app.approve_plan(self.bound));app.wait_choice.assert_called_once()
        self.assertEqual(list(self.p.iterdir()),[]) # view is not the approver/service
    def test_full_plan_review_contains_acceptance_source(self):
        text=ui.plan_review_text(self.bound)
        for value in ['OBJETIVO','TIMEOUTS','BUDGETS','GIT','WEB','CHATGPT','COMPLETION','test_acceptance.py','assert add(-2, 3) == 1']:
            self.assertIn(value,text)
    def test_existing_summary_cancel_no_new_objective(self):
        app=self.app();info={'prepared':True,'project':str(self.p),'can_continue':True,'remaining_seconds':120,
            'state':{'run_id':'run-existing','status':'STALLED','current_task':'pending task','checkpoint':{'last_id':'checkpoint-1'},'pending_tasks':['pending task']}}
        with patch.object(data,'inspect',return_value=info):app.launch(str(self.p))
        app.objective.assert_not_called();self.assertIn('checkpoint-1',app.show.call_args.args[1]);self.assertEqual(list(self.p.iterdir()),[])
    def test_interrupted_run_cannot_be_archived(self):
        with self.assertRaisesRegex(ValueError,'INTERRUPTED_RUN_REQUIRES_RECOVERY'):data.archive(self.p,{'prepared':True,'state':{'status':'RUNNING'}})
        self.assertFalse((self.p/'.autopilot-history').exists())
    def test_draft_cache_isolated_and_never_approval(self):
        data.cache_draft(self.bound);self.assertEqual(data.cached_draft(self.p,self.bound['objective'])['binding'],self.bound['binding'])
        self.assertIsNone(data.cached_draft(self.p,self.bound['objective']+' different'))
        p=BASE/(self._testMethodName+'-B');p.mkdir();self.assertIsNone(data.cached_draft(p,self.bound['objective']))
        (self.p/'user-change.txt').write_text('new input');self.assertIsNone(data.cached_draft(self.p,self.bound['objective']))
        self.assertFalse((self.p/'.autopilot').exists())
    def test_stop_pid_reuse_denied(self):
        testroot=self.p/'transport';pointer=testroot/'runtime/project-launcher/active.json';pointer.parent.mkdir(parents=True)
        pointer.write_text(json.dumps({'project':str(self.p),'pid':123,'start_ticks':1,'run_id':'run-native'}))
        with patch.object(ui,'R',testroot),patch.object(ui,'birth',return_value=2),patch.object(ui,'run_json') as send:
            with self.assertRaises(ValueError):ui.active_stop()
            send.assert_not_called()
    def test_error_stays_until_close_choice(self):
        app=self.app();app.message('Error de prueba','Visible error');app.show.assert_called_once_with('Error de prueba','Visible error',[('Cerrar','close')]);app.wait_choice.assert_called_once()

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Flow))
    report={'status':'PASS' if result.wasSuccessful() else 'FAIL','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'scope':'headless view/controller and approval integration; human decisions mocked only; no Start/inference/GUI actions','sandbox':str(BASE),'details':[str(x[1]) for x in result.failures+result.errors]}
    out=pathlib.Path(os.environ['LAUNCHER_FLOW_E']);out.mkdir(parents=True,exist_ok=False);(out/'RESULT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report));raise SystemExit(0 if result.wasSuccessful() else 1)
