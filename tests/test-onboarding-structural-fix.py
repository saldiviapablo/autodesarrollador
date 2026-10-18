"""Deterministic tests for the structural onboarding fix. No model, GUI or Worker."""
import copy
import json
import pathlib
import sys
import subprocess
import unittest

import jsonschema

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'runner')]

import onboarding_planner as planner
import onboarding_hermes as native
import write_scope


def base_value():
    return {
        'plan':{
            'schema_version':'1.0',
            'backend':'live',
            'task':planner.HOST_TASK,
            'allowed_files':['package.json','index.html','README.md'],
            'write_scope':['src/**','public/**','vite.config.*','tsconfig*.json'],
            'tests':[{'id':'acceptance','argv':['node','test_acceptance.js'],'marker':'ACCEPTANCE_PASS','timeout_seconds':60}],
            'builds':[{'id':'build','argv':['npm','run','build'],'marker':'build','timeout_seconds':60}],
            'criteria':[{'criterion':'La landing renderiza cinco capítulos y navegación accesible.','test_id':'acceptance'}],
            'artifacts':[{'path':'index.html','min_bytes':1}],
            'immutable_files':[{'path':'test_acceptance.js','sha256':'0'*64}],
            'phase_timeout_seconds':300,
            'global_timeout_seconds':2700,
            'max_cycles':5,
            'restart_budget':2,
        },
        'seed_files':{'test_acceptance.js':'console.log("ACCEPTANCE_PASS")\n'},
        'overview':{
            'objective_summary':'Landing React/Vite local y verificable.',
            'tasks':['Implementar la landing y verificarla localmente.'],
            'research_requirements':[],
            'restrictions':['Sin deploy ni push.'],
            'web_policy':'none',
            'chatgpt_policy':'disabled',
            'git_policy':'local_only_no_push',
            'completion_policy':planner.COMPLETION,
        },
    }


class StructuralOnboarding(unittest.TestCase):
    def test_contract_single_source_schema_accepts_same_value_as_validate(self):
        value=base_value()
        jsonschema.Draft7Validator(planner.planner_schema()).validate(value)
        self.assertEqual(planner.validate(copy.deepcopy(value)),value)

    def test_task_is_host_owned_and_bounded(self):
        value=base_value();value['plan']['task']='x'*5000
        result=planner.decode(json.dumps(value),'Crear landing local con npm run build')
        self.assertEqual(result['plan']['task'],planner.HOST_TASK)
        self.assertLessEqual(len(result['plan']['task']),600)

    def test_explicit_build_is_preserved(self):
        value=base_value();value['plan'].pop('builds');value['plan']['no_build_reason']='placeholder'
        result=planner.decode(json.dumps(value),'Ejecutar npm run build antes de cerrar')
        self.assertIn(['npm','run','build'],[item['argv'] for item in result['plan']['builds']])
        self.assertNotIn('no_build_reason',result['plan'])

    def test_open_research_becomes_query_not_ambiguous(self):
        value=base_value()
        value['overview']['research_requirements']=['Investigar cinco avances de IA de 2026 en múltiples fuentes oficiales.']
        result=planner.decode(json.dumps(value),'Investigar noticias actuales y verificar varias fuentes; npm run build')
        self.assertIn('query',result['plan']['research'])
        self.assertNotIn('url',result['plan']['research'])
        self.assertEqual(result['overview']['web_policy'],'governed_https')

    def test_single_explicit_url_can_lower_to_url(self):
        value=base_value()
        value['overview']['research_requirements']=['Consultar documentación oficial.']
        result=planner.decode(json.dumps(value),'Consultar https://developer.mozilla.org/en-US/docs/Web/Accessibility')
        self.assertEqual(result['plan']['research']['url'],'https://developer.mozilla.org/en-US/docs/Web/Accessibility')

    def test_research_url_and_query_are_mutually_exclusive(self):
        value=base_value()
        value['plan']['research']={'url':'https://example.com','query':'example'}
        value['overview']['web_policy']='governed_https'
        with self.assertRaises(ValueError):
            planner.validate(value)

    def test_greenfield_write_scope(self):
        plan=base_value()['plan']
        write_scope.validate_plan_scope(plan)
        self.assertTrue(write_scope.allowed_change('src/App.tsx',plan))
        self.assertTrue(write_scope.allowed_change('vite.config.ts',plan))
        self.assertFalse(write_scope.allowed_change('.autopilot/STATE.json',plan))
        self.assertFalse(write_scope.allowed_change('QWEN.md',plan))
        self.assertFalse(write_scope.allowed_change('test_acceptance.js',plan))

    def test_broad_or_reserved_write_scope_denied(self):
        for pattern in ('*','**','*/**','../src/**','.autopilot/**','runner/**'):
            with self.subTest(pattern=pattern):
                with self.assertRaises(ValueError):
                    write_scope.validate_pattern(pattern)

    def test_real_runpy_bootstrap_can_import_shared_planner(self):
        code="import runpy; runpy.run_path(r'scripts/onboarding_hermes.py', run_name='bootstrap_test')"
        result=subprocess.run([sys.executable,'-I','-c',code],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)

    def test_native_uses_exact_shared_schema(self):
        captured={}
        class Fake:
            def __init__(self,**kw):
                self.tools=[];self._fallback_chain=[];self.model=kw['model'];self.base_url=kw['base_url']
                captured['schema']=kw['request_overrides']['response_format']['json_schema']['schema']
            def run_conversation(self,prompt):
                return {'completed':True,'final_response':json.dumps(base_value()),'messages':[]}
            def close(self):pass
        request={
            'base_url':'http://127.0.0.1:8080/v1',
            'model':'qwen36',
            'policy':planner.policy(),
            'disabled_toolsets':['terminal','file','web'],
            'project':str(ROOT),
            'prompt':'fixture',
        }
        native.run(request,Fake)
        self.assertEqual(captured['schema'],planner.planner_schema())


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(StructuralOnboarding))
    raise SystemExit(0 if result.wasSuccessful() else 1)
