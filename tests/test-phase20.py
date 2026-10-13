import copy,importlib.util,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('fixtures',ROOT/'tests/runner-fixtures.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
spec=importlib.util.spec_from_file_location('completion',ROOT/'runner/completion.py');gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
p=f.project('gate20',backend='live');f.approve(p)
# This is labelled unit data for the gate, never proof of a live agent invocation.
(p/'calculator.py').write_text('def add(a,b):\n    return a+b\n')
state_path=p/'.autopilot/STATE.json';state=json.loads(state_path.read_text(encoding='utf-8-sig'));state['tests']['status']='PASS';state['pending_tasks']=[];state['completed_tasks']=[state['objective']];state['git']['head']=subprocess.check_output(['git','-C',str(p),'rev-parse','--short','HEAD'],text=True).strip();state_path.write_text(json.dumps(state))
checks={'run_id':state['run_id'],'tests':[{'id':'unit','status':'PASS','exit_code':0,'marker_present':True}],'builds':[],'linters':[]}
check_path=p/'.autopilot/evidence/checks.json';check_path.write_text(json.dumps(checks))
roles={r:{'status':'SUCCESS','text':'{"decision":"ACCEPTED"}'} for r in ('supervisor','worker','reviewer')};role_path=p/'.autopilot/evidence/roles.json';role_path.write_text(json.dumps(roles))
assert gate.evaluate(p)['status']=='COMPLETED'
plan_path=p/'.autopilot/RUN-PLAN.json';plan=json.loads(plan_path.read_text());original_plan=copy.deepcopy(plan)
cases={}
def expect(name):
    result=gate.evaluate(p);assert result['status']=='FAILED',(name,result);cases[name]=result['failed']
plan['builds']=[{'id':'build','argv':['python','test_calculator.py'],'marker':'BUILD'}];plan_path.write_text(json.dumps(plan));expect('missing_build_evidence');plan_path.write_text(json.dumps(original_plan))
plan['builds']=[];plan['linters']=[{'id':'lint','argv':['python','test_calculator.py'],'marker':'LINT'}];plan_path.write_text(json.dumps(plan));expect('missing_linter_evidence');plan_path.write_text(json.dumps(original_plan))
roles['reviewer']['text']='DONE';role_path.write_text(json.dumps(roles));expect('agent_done_insufficient');roles['reviewer']['text']='{"decision":"ACCEPTED"}';role_path.write_text(json.dumps(roles))
checks['tests'][0]['status']='FAIL';check_path.write_text(json.dumps(checks));expect('mandatory_test_fail');checks['tests'][0]['status']='PASS'
checks['tests'][0]['marker_present']=False;check_path.write_text(json.dumps(checks));expect('exit_zero_no_marker');checks['tests'][0]['marker_present']=True;check_path.write_text(json.dumps(checks))
state['pending_tasks']=['critical'];state_path.write_text(json.dumps(state));expect('pending_critical');state['pending_tasks']=[];state_path.write_text(json.dumps(state))
(p/'unexpected.txt').write_text('not approved');expect('spurious_diff');(p/'unexpected.txt').unlink()
original=(p/'calculator.py').read_bytes();(p/'calculator.py').unlink();expect('artifact_missing');(p/'calculator.py').write_bytes(original)
state['acceptance_criteria']=['unmapped'];state_path.write_text(json.dumps(state));expect('criterion_unmapped');state['acceptance_criteria']=['addition verified'];state_path.write_text(json.dumps(state))
checks['run_id']='other-run';check_path.write_text(json.dumps(checks));expect('stale_evidence');checks['run_id']=state['run_id'];check_path.write_text(json.dumps(checks))
pin=p/'test_calculator.py';original=pin.read_bytes();pin.write_text('print("fake")');expect('immutable_test_changed');pin.write_bytes(original)
state['failure']['repeated_count']=1;state_path.write_text(json.dumps(state));expect('unresolved_failure');state['failure']['repeated_count']=0;state_path.write_text(json.dumps(state))
assert gate.evaluate(p)['status']=='COMPLETED'
e=ROOT/'evidence/phase-20';e.mkdir(exist_ok=True);result={'status':'PASS','tests':{f'T-COMP-{i:03}':'PASS' for i in range(1,10)},'false_positive_cases':cases,'positive_case':'PASS','unit_fixture_only':True,'project':str(p)};(e/'tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
