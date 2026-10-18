"""Realistic no-model replay of the defective React/Vite approval proposal.

This tests the source-language mismatch and the build/output/research
contract compiler without launching Hermes, Worker or web fetching.
"""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import onboarding_planner as planner
sys.path.insert(0,str(ROOT/'runner'))
import write_scope

spec=importlib.util.spec_from_file_location('existing_fixture',ROOT/'tests/test-onboarding-structural-fix.py')
fixture=importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
OBJECTIVE='Crear landing premium React TypeScript Vite Tailwind; investigar avances IA 2026 en docs/research.md; npm run build.'

class PlanQuality(unittest.TestCase):
    def setUp(self):
        self.value=fixture.base_value()
        self.value['overview']['research_requirements']=['Investigación multifuente IA 2026']
        self.value['plan']['research']={
            'query':'Los 5 avances más importantes de Inteligencia Artificial en 2026 hasta la fecha',
            'domains':['nature.com','arxiv.org','techcrunch.com','google.org']
        }
        self.value['overview']['web_policy']='governed_https'
        self.value['plan']['builds'][0]['marker']='BUILD_PASS'
        self.value['plan']['write_scope']=['src/**','public/**']
        self.value['plan']['artifacts']=[{'path':'src/App.tsx','min_bytes':1}]

    def compile(self):
        return planner.decode(json.dumps(self.value),OBJECTIVE)

    def test_real_approval_mismatched_acceptance_marker_denied(self):
        self.value['plan']['tests'][0]['argv']=['node','build_check.js']
        self.value['plan']['tests'][0]['marker']='ACCEPTANCE_PASS'
        self.value['seed_files']={
            'build_check.js':"const {execSync}=require('child_process'); execSync('npm run build'); console.log('BUILD_PASS');"
        }
        self.value['plan']['immutable_files']=[{'path':'build_check.js','sha256':'0'*64}]
        with self.assertRaisesRegex(ValueError,'PLANNER_TEST_MARKER_MISSING:acceptance'):
            self.compile()

    def test_build_only_test_cannot_prove_unrelated_criteria(self):
        self.value['plan']['tests'][0]['argv']=['node','build_check.js']
        self.value['plan']['tests'][0]['marker']='ACCEPTANCE_PASS'
        self.value['seed_files']={
            'build_check.js':"const {execSync}=require('child_process'); execSync('npm run build'); console.log('ACCEPTANCE_PASS');"
        }
        self.value['plan']['immutable_files']=[{'path':'build_check.js','sha256':'0'*64}]
        with self.assertRaisesRegex(ValueError,'PLANNER_BUILD_ONLY_ACCEPTANCE:acceptance'):
            self.compile()

    def test_substantive_seeded_js_acceptance_does_not_trigger_false_rejection(self):
        self.value['plan']['tests'][0]['argv']=['node','test_acceptance.js']
        self.value['plan']['tests'][0]['marker']='ACCEPTANCE_PASS'
        self.value['seed_files']={
            'test_acceptance.js':"const assert=require('node:assert/strict'); const fs=require('fs'); const s=fs.readFileSync('src/App.tsx','utf8'); assert(s.includes('01')); console.log('ACCEPTANCE_PASS');"
        }
        self.value['plan']['immutable_files']=[{'path':'test_acceptance.js','sha256':'0'*64}]
        self.assertEqual(self.compile()['plan']['tests'][0]['argv'],['node','test_acceptance.js'])

    def test_failing_real_world_node_in_py_rejected(self):
        self.value['plan']['tests'][0]['argv']=['python','test_acceptance.py']
        self.value['seed_files']={'test_acceptance.py':'''node -e "const fs = require('fs'); console.log('ACCEPTANCE_PASS')"'''}
        self.value['plan']['immutable_files']=[{'path':'test_acceptance.py','sha256':'0'*64}]
        with self.assertRaisesRegex(ValueError,'PLANNER_IMMUTABLE_PYTHON_SYNTAX_INVALID'):
            self.compile()

    def test_normal_py_source_is_accepted(self):
        self.value['plan']['tests'][0]['argv']=['python','test_acceptance.py']
        self.value['seed_files']={'test_acceptance.py':"assert True\nprint('ACCEPTANCE_PASS')\n"}
        self.value['plan']['immutable_files']=[{'path':'test_acceptance.py','sha256':'0'*64}]
        # This test confirms syntax only; content quality still requires human
        # review and independent Reviewer. A trivial test is not proof of UX.
        out=self.compile()
        self.assertEqual(out['plan']['tests'][0]['argv'],['python','test_acceptance.py'])

    def test_react_vite_generated_outputs_allowed(self):
        plan=self.compile()['plan']
        for path in ('docs/research.md','dist/index.html','src/App.tsx','src/components/Hero.tsx','package-lock.json','.gitignore'):
            with self.subTest(path=path):self.assertTrue(write_scope.allowed_change(path,plan),path)
        for path in ('.git/config','.autopilot/STATE.json','QWEN.md','test_acceptance.js'):
            with self.subTest(path=path):self.assertFalse(write_scope.allowed_change(path,plan),path)
        self.assertIn('docs/research.md',[item['path'] for item in plan['artifacts']])

    def test_build_marker_is_real_npm_echo(self):
        plan=self.compile()['plan']
        self.assertEqual(plan['builds'][0]['argv'],['npm','run','build'])
        self.assertEqual(plan['builds'][0]['marker'],'build')

    def test_research_is_truly_open(self):
        plan=self.compile()['plan']
        self.assertIn('query',plan['research'])
        self.assertNotIn('domains',plan['research'])

    def test_no_change_to_model_owned_original(self):
        before=copy.deepcopy(self.value)
        self.compile()
        self.assertEqual(before,self.value)

if __name__=='__main__':
    unittest.main(verbosity=2)
