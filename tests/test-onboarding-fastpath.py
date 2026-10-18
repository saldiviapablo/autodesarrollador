"""Portable regression for host-owned React/Vite onboarding and worker test delegation."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'runner')]
import onboarding_fastpath as host
import onboarding_planner as planner
import write_scope

OBJECTIVE = (
    "Crear una landing editorial premium React TypeScript Vite Tailwind "
    "con cinco avances de IA de 2026. Investigar fuentes oficiales actuales "
    "y conservarlas en docs/research.md. Ejecutar npm run build. "
    "El Worker debe poder crear componentes y probar el resultado."
)


class HostCompiledOnboarding(unittest.TestCase):
    def make(self, project):
        return host.compile_proposal(OBJECTIVE,project)

    def test_recognizes_explicit_stack_and_legacy_fallback(self):
        self.assertTrue(host.supports(OBJECTIVE))
        self.assertFalse(host.supports("Genera script de Python para CSV"))

    def test_real_project_objective_no_speculative_ui_assertions(self):
        with tempfile.TemporaryDirectory() as d:
            value=self.make(d)
            plan=value['plan']
            self.assertEqual(planner.validate(value),value)
            self.assertEqual(value['overview']['chatgpt_policy'],'disabled')
            self.assertEqual(plan['tests'][0]['argv'],['npm','run','test'])
            self.assertEqual(plan['tests'][1]['argv'],['node','__autonomy_verify.cjs'])
            self.assertNotIn('AI /2026',repr(value['seed_files']))
            self.assertNotIn('chapter-',repr(value['seed_files']))
            self.assertEqual(plan['builds'][0]['argv'],['npm','run','build'])
            self.assertIn('docs/research.md',[a['path'] for a in plan['artifacts']])
            self.assertEqual(plan['research']['max_results'],10)
            self.assertIn('governed_https',value['overview']['web_policy'])
            self.assertEqual(set(value['seed_files']),{plan['immutable_files'][0]['path']})
            for name,source in value['seed_files'].items():
                self.assertEqual(
                    hashlib.sha256(source.encode('utf-8')).hexdigest(),
                    plan['immutable_files'][0]['sha256'])
            for f in ('tests/page.test.cjs','src/App.tsx','docs/research.md',
                      'dist/index.html','package.json','tailwind.config.ts'):
                self.assertTrue(write_scope.allowed_change(f,plan),f)
            for f in ('.git/config','.autopilot/STATE.json','QWEN.md',
                      '__autonomy_verify.cjs','config/security.yaml'):
                self.assertFalse(write_scope.allowed_change(f,plan),f)

    def test_reusing_existing_immutable_host_verifier(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'__autonomy_verify.cjs').write_text(host.VERIFIER_SOURCE,encoding='utf-8')
            value=self.make(d)
            self.assertEqual(value['seed_files'],{})
            self.assertEqual(value['plan']['immutable_files'][0]['path'],'__autonomy_verify.cjs')

    def test_verifier_collision_generates_separate_path(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'__autonomy_verify.cjs').write_text('USER DATA',encoding='utf-8')
            value=self.make(d)
            self.assertTrue(value['plan']['immutable_files'][0]['path'].startswith('__autonomy_verify_'))
            self.assertEqual(len(value['seed_files']),1)

    def test_no_unrequested_research_for_plain_react_project(self):
        with tempfile.TemporaryDirectory() as d:
            value=host.compile_proposal('Crear interfaz React Vite local y hacer npm run build',d)
            self.assertNotIn('research',value['plan'])
            self.assertEqual(value['overview']['web_policy'],'none')

    def run_verifier(self,d):
        script='__autonomy_verify.cjs'
        (Path(d)/script).write_text(host.VERIFIER_SOURCE,encoding='utf-8')
        return subprocess.run(['node',script],cwd=d,text=True,capture_output=True,timeout=10)

    def test_host_verifier_rejects_fake_and_missing_tests(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'package.json').write_text(json.dumps({'scripts':{'test':'echo test passed'}}))
            self.assertNotEqual(self.run_verifier(d).returncode,0)
            (root/'package.json').write_text(json.dumps({'scripts':{'test':'node --test tests/page.test.cjs'}}))
            self.assertNotEqual(self.run_verifier(d).returncode,0)
            (root/'tests').mkdir()
            (root/'tests/page.test.cjs').write_text("console.log('pass')",encoding='utf-8')
            self.assertNotEqual(self.run_verifier(d).returncode,0)

    def test_host_verifier_accepts_substantive_test_source(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'package.json').write_text(json.dumps({'scripts':{'test':'node --test tests/page.test.cjs'}}))
            (root/'tests').mkdir()
            (root/'tests/page.test.cjs').write_text(
                "const assert = require('node:assert/strict');\n"
                "const { test } = require('node:test');\n"
                "test('real structural condition', () => { assert.equal(2 + 2, 4); });\n",
                encoding='utf-8')
            result=self.run_verifier(d)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('AUTONOMY_TESTS_PRESENT',result.stdout)


if __name__=='__main__':
    unittest.main(verbosity=2)
