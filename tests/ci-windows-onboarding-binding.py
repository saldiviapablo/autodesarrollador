"""Windows-hosted contract/binding smoke with realistic malformed planner output.

No real Hermes, Worker, network research, approval, or project implementation.
"""
import importlib.util
import json
import pathlib
import sys
import uuid

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import onboarding_planner as planner
import project_onboarding as adapter

spec=importlib.util.spec_from_file_location('base_fixture',ROOT/'tests/test-onboarding-structural-fix.py')
fixture=importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)

p=ROOT/'sandbox'/('ci-binding-'+uuid.uuid4().hex[:8])
p.mkdir(parents=True)
value=fixture.base_value()
value['plan']['tests'][0]['argv']=['npm']
value['plan']['builds'][0]['argv']=['npm']
value['overview']['research_requirements']=['Investigar cinco avances de IA de 2026 en fuentes oficiales y reputadas.']
brief=('Crear landing React TypeScript Vite Tailwind Motion para localhost; '
       'investigación abierta multifuente de IA durante 2026; '
       'npm run build; responsive, accesibilidad y tests.\n'
       + 'Diseño editorial premium y sin deploy; sin push.\n'*80)
compiled=planner.decode(json.dumps(value),brief)
assert compiled['plan']['tests'][0]['argv']==['node','test_acceptance.js']
assert compiled['plan']['builds'][0]['argv']==['npm','run','build']
assert compiled['plan']['research']['query']
bound=adapter.bind_proposal(str(p),brief,compiled)
assert bound['status']=='PASS'
assert bound['proposal']['plan']['tests'][0]['argv']==['node','test_acceptance.js']
adapter.validate_binding(bound)
assert list(p.iterdir())==[], 'onboarding preflight made a project write'
print('SIMULATED_BINDING_PASS; WITHOUT_APPROVAL; WORKER_STARTS=0; WEB_FETCHES=0')
p.rmdir()
