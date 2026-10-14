"""Deterministic multi-criterion completion; agent text and exit0 are insufficient."""
import argparse,hashlib,json,pathlib,re,subprocess,sys,jsonschema
ROOT=pathlib.Path(__file__).resolve().parents[1]
def evaluate(project):
    p=pathlib.Path(project).resolve();auto=p/'.autopilot'
    plan=json.loads((auto/'RUN-PLAN.json').read_text(encoding='utf-8-sig'))
    state=json.loads((auto/'STATE.json').read_text(encoding='utf-8-sig'))
    roles=json.loads((auto/'evidence/roles.json').read_text(encoding='utf-8-sig'))
    evidence=json.loads((auto/'evidence/checks.json').read_text(encoding='utf-8-sig'))
    checks={}
    try:jsonschema.validate(state,json.loads((ROOT/'schemas/autopilot-state.schema.json').read_text(encoding='utf-8-sig')));checks['state_schema_valid']=True
    except jsonschema.ValidationError:checks['state_schema_valid']=False
    checks['native_live_backend']=plan.get('backend','live')=='live'
    checks['roles_success']=all(roles.get(role,{}).get('status')=='SUCCESS' for role in ('supervisor','worker','reviewer'))
    text=roles.get('reviewer',{}).get('text','');match=re.search(r'\{.*\}',text,re.S)
    try:accepted=json.loads(match.group())['decision']=='ACCEPTED' if match else False
    except (KeyError,json.JSONDecodeError):accepted=False
    checks['independent_reviewer_accepted']=accepted
    checks['run_id_consistent']=evidence.get('run_id')==state['run_id']
    all_results={r['id']:r for group in ('tests','builds','linters') for r in evidence.get(group,[]) if r}
    for group in ('tests','builds','linters'):
        required=plan.get(group,[])
        checks[group+'_all_required']=all(all_results.get(c['id'],{}).get('status')=='PASS' and all_results[c['id']].get('exit_code')==0 and all_results[c['id']].get('marker_present') for c in required)
    if plan.get('research'):
        import importlib.util
        spec=importlib.util.spec_from_file_location('research_binding',ROOT/'runner/research-handoff.py');handoff=importlib.util.module_from_spec(spec);spec.loader.exec_module(handoff)
        try:checks['required_web_context_delivered']=handoff.validate(p,'.autopilot/logs/worker.stdout.txt')['WEB_CONTEXT_DELIVERED'] is True
        except (ValueError,KeyError,OSError,TypeError):checks['required_web_context_delivered']=False
    if plan.get('consultation'):
        path=auto/'evidence/CHATGPT.json';chat=json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {}
        checks['required_consultation_captured']=chat.get('status')=='SUCCESS' and chat.get('consultation_id')==plan['consultation']['id'] and chat.get('message_sent') is True and chat.get('response_received') is True and chat.get('composer_cleared') is True and chat.get('user_turns_after')==chat.get('user_turns_before',-2)+1 and chat.get('assistant_turns_after')==chat.get('assistant_turns_before',-2)+1
    if plan.get('consultation'):
        retry_path=auto/'evidence/CHATGPT-RETRY.json';retry=json.loads(retry_path.read_text(encoding='utf-8-sig')) if retry_path.exists() else {}
        checks['consultation_retry_no_resend']=retry.get('status')=='ALREADY_SENT' and retry.get('additional_physical_sends')==0 and retry.get('ledger_unchanged') is True and retry.get('budget_unchanged') is True
        checks['consultation_budget_persisted']=state['chatgpt']['queries_used']>=1
    checks['tests_exist']=bool(plan['tests'])
    checks['no_build_approved_or_passed']=bool(plan.get('builds')) or bool(plan.get('no_build_reason'))
    checks['criteria_all_mapped_and_passed']=set(c['criterion'] for c in plan['criteria'])==set(state['acceptance_criteria']) and all(all_results.get(c['test_id'],{}).get('status')=='PASS' for c in plan['criteria'])
    checks['pending_empty']=not state['pending_tasks']
    checks['failures_not_pending']=state['failure']['repeated_count']==0
    checks['state_tests_pass']=state['tests']['status']=='PASS'
    for pin in plan.get('immutable_files',[]):
        f=p/pin['path'];checks['immutable_'+pin['path']]=f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest()==pin['sha256']
    for artifact in plan['artifacts']:
        f=p/artifact['path'];checks['artifact_'+artifact['path']]=f.is_file() and not f.is_symlink() and f.stat().st_size>=artifact.get('min_bytes',1)
    # Review both tracked diff and untracked names, excluding operational .autopilot metadata.
    changed=subprocess.check_output(['git','-C',str(p),'diff','--name-only','HEAD'],text=True).splitlines()
    changed+=subprocess.check_output(['git','-C',str(p),'ls-files','--others','--exclude-standard'],text=True).splitlines()
    changed=[n for n in changed if not n.startswith('.autopilot/')]
    checks['diff_only_approved_files']=all(n in plan['allowed_files'] for n in changed)
    checks['relevant_diff_exists']=bool(changed)
    head=subprocess.check_output(['git','-C',str(p),'rev-parse','--short','HEAD'],text=True).strip()
    checks['state_git_head_consistent']=state['git']['head']==head
    result={'status':'COMPLETED' if all(checks.values()) else 'FAILED','checks':checks,'failed':[n for n,v in checks.items() if not v],'changed_files':changed,'run_id':state['run_id'],'source':'DETERMINISTIC_COMPLETION_GATE'}
    return result
if __name__=='__main__':
    try:print(json.dumps(evaluate(sys.argv[1]),ensure_ascii=False))
    except Exception as e:print(json.dumps({'status':'FAILED','reason':str(e),'source':'DETERMINISTIC_COMPLETION_GATE'}))
