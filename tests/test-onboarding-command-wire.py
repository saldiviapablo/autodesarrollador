"""Adversarial deterministic replay of planner command wire anomalies.

No model, no network, no Worker. Exercises real decode() and strict schema.
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

spec=importlib.util.spec_from_file_location('structural_fixture',ROOT/'tests/test-onboarding-structural-fix.py')
fixture=importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)

OBJECTIVE='Crear una landing React con investigación multifuente y ejecutar npm run build.'


class CommandWire(unittest.TestCase):
    def setUp(self):
        self.value=fixture.base_value()

    def compile(self):
        return planner.decode(json.dumps(self.value),OBJECTIVE)

    def test_short_npm_test_resolves_unique_seed(self):
        self.value['plan']['tests'][0]['argv']=['npm']
        plan=self.compile()['plan']
        self.assertEqual(plan['tests'][0]['argv'],['node','test_acceptance.js'])

    def test_empty_array_resolves_unique_seed(self):
        self.value['plan']['tests'][0]['argv']=[]
        plan=self.compile()['plan']
        self.assertEqual(plan['tests'][0]['argv'],['node','test_acceptance.js'])

    def test_string_form_resolves(self):
        self.value['plan']['tests'][0]['argv']='node test_acceptance.js'
        self.assertEqual(self.compile()['plan']['tests'][0]['argv'],['node','test_acceptance.js'])

    def test_single_packed_string_resolves(self):
        self.value['plan']['tests'][0]['argv']=['node test_acceptance.js']
        self.assertEqual(self.compile()['plan']['tests'][0]['argv'],['node','test_acceptance.js'])

    def test_short_build_explicit_is_filled(self):
        self.value['plan']['builds'][0]['argv']=['npm']
        self.assertEqual(self.compile()['plan']['builds'][0]['argv'],['npm','run','build'])

    def test_single_packed_build_resolves(self):
        self.value['plan']['builds'][0]['argv']=['npm run build']
        self.assertEqual(self.compile()['plan']['builds'][0]['argv'],['npm','run','build'])

    def test_npx_normalization(self):
        self.value['plan']['tests'][0]['argv']=['npx','vitest','run']
        self.assertEqual(self.compile()['plan']['tests'][0]['argv'],['npm','exec','--','vitest','run'])

    def test_windows_alias(self):
        self.value['plan']['tests'][0]['argv']=['node.exe','test_acceptance.js']
        self.assertEqual(self.compile()['plan']['tests'][0]['argv'],['node','test_acceptance.js'])

    def test_ambiguous_seeds_fail_closed(self):
        self.value['plan']['tests'][0]['argv']=['npm']
        self.value['seed_files']['other_test.js']='console.log("OTHER")'
        with self.assertRaisesRegex(ValueError,'PLANNER_CHECK_COMMAND_AMBIGUOUS'):
            self.compile()

    def test_unknown_executable_denied(self):
        self.value['plan']['tests'][0]['argv']=['powershell','-File','test.ps1']
        with self.assertRaisesRegex(ValueError,'CHECK_EXECUTABLE_NOT_ADMITTED'):
            self.compile()

    def test_packed_shell_injection_denied(self):
        self.value['plan']['tests'][0]['argv']='node test_acceptance.js && echo UNAUTHORIZED'
        with self.assertRaisesRegex(ValueError,'PLANNER_CHECK_SHELL_OPERATOR_DENIED'):
            self.compile()

    def test_missing_no_matching_seed_denied(self):
        self.value['plan']['tests'][0]['argv']=[]
        self.value['seed_files']={}
        with self.assertRaisesRegex(ValueError,'PLANNER_CHECK_COMMAND_INCOMPLETE'):
            self.compile()

    def test_unrecognized_argv_type_denied(self):
        self.value['plan']['tests'][0]['argv']={'command':'node test_acceptance.js'}
        with self.assertRaisesRegex(ValueError,'PLANNER_CHECK_ARGV_INVALID'):
            self.compile()

    def test_non_string_argument_denied(self):
        self.value['plan']['tests'][0]['argv']=['node',5]
        with self.assertRaisesRegex(ValueError,'PLANNER_CHECK_ARGV_INVALID'):
            self.compile()

    def test_normalization_does_not_modify_input(self):
        before=copy.deepcopy(self.value)
        self.value['plan']['tests'][0]['argv']=['npm']
        before=copy.deepcopy(self.value)
        self.compile()
        self.assertEqual(before,self.value)

    def test_output_idempotent(self):
        self.value['plan']['tests'][0]['argv']=['npm']
        normalized=self.compile()
        again=planner.decode(json.dumps(normalized),OBJECTIVE)
        self.assertEqual(again,normalized)

    def test_large_brief_without_model(self):
        brief=OBJECTIVE+'\n'+'Diseño responsive y accesible.\n'*400
        normalized=planner.decode(json.dumps(self.value),brief)
        self.assertEqual(normalized['plan']['builds'][0]['argv'],['npm','run','build'])


if __name__=='__main__':
    unittest.main(verbosity=2)
