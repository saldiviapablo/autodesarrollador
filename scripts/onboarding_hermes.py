"""Native Hermes AIAgent adapter for this read-only preflight only.

Launched by the official installation bootstrap, under the existing process
job, profile/hook/plugin guards and cross-process inference lease.
"""
import contextlib,json,os,sys,time,uuid

def run(request,agent_class):
    if request['base_url']!='http://127.0.0.1:8080/v1' or request['model']!='qwen36':raise ValueError('PLANNER_LOCAL_ROUTE_REQUIRED')
    policy=request['policy'];session='onboarding-'+uuid.uuid4().hex
    strings=lambda n:{'type':'array','maxItems':n,'items':{'type':'string','maxLength':180}}
    view={'type':'object','properties':{'objective_summary':{'type':'string','minLength':1,'maxLength':360},
        'tasks':dict(strings(policy['max_tasks']),minItems=1),'research_requirements':strings(6),'restrictions':strings(8)},
        'required':['objective_summary','tasks','research_requirements','restrictions'],'additionalProperties':False}
    schema={'type':'object','properties':{'plan':{'type':'object'},'seed_files':{'type':'object','additionalProperties':{'type':'string'}},'overview':view},'required':['plan','seed_files','overview'],'additionalProperties':False}
    overrides={'response_format':{'type':'json_schema','json_schema':{'name':'onboarding_plan','strict':True,'schema':schema}},
               'extra_body':{'chat_template_kwargs':{'enable_thinking':False}}}
    start=time.monotonic()
    agent=agent_class(model=request['model'],provider='custom',requested_provider='custom',api_mode='chat_completions',
        base_url=request['base_url'],api_key='local-not-required',max_iterations=1,max_tokens=policy['max_output_tokens'],
        enabled_toolsets=[],disabled_toolsets=request['disabled_toolsets'],quiet_mode=True,verbose_logging=False,
        skip_memory=True,skip_context_files=True,skip_background_review=True,session_id=session,session_db=None,
        cwd=request['project'],run_budget_seconds=policy['timeout_seconds'],fallback_model=[],request_overrides=overrides)
    try:
        if agent.tools or getattr(agent,'_fallback_chain',[]):raise ValueError('READONLY_PLANNER_RUNTIME_MISMATCH')
        if agent.model!=request['model'] or agent.base_url.rstrip('/')!=request['base_url']:raise ValueError('PLANNER_RUNTIME_ROUTE_CHANGED')
        result=agent.run_conversation(request['prompt'])
        if not result.get('completed') or not result.get('final_response'):raise ValueError('PLANNER_NATIVE_RESPONSE_INCOMPLETE')
        if agent.tools or any(m.get('tool_calls') or m.get('function_call') or m.get('role') in ('tool','function') for m in result.get('messages',[])):
            raise ValueError('READONLY_PREFLIGHT_TOOL_CALL_DENIED')
        text=result['final_response']
        if len(text.encode('utf-8'))>policy['max_plan_bytes']:raise ValueError('PLANNER_PLAN_SIZE_EXCEEDED')
        return {'status':'PASS','session_id':session,'text':text,'duration':time.monotonic()-start,'tools':0,
                'api_calls':result.get('api_calls'),'input_tokens':getattr(agent,'session_input_tokens',None),
                'output_tokens':getattr(agent,'session_output_tokens',None),'request_limits':{'max_tokens':policy['max_output_tokens'],'response_format':'json_schema','enable_thinking':False}}
    finally:agent.close()

def main():
    sys.stdin.reconfigure(encoding='utf-8',errors='strict');sys.stdout.reconfigure(encoding='utf-8',errors='strict')
    request=json.load(sys.stdin);os.environ['HERMES_HOME']=request['profile_home'];os.environ['HERMES_PROFILE']='desarrollador-autonomo-supervisor'
    os.environ.pop('HERMES_ACCEPT_HOOKS',None);os.environ['HERMES_SINGLE_QUERY_SESSION']='1'
    os.chdir(request['project'])
    with contextlib.redirect_stdout(sys.stderr):
        from run_agent import AIAgent
        result=run(request,AIAgent)
    print(json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':
    try:main()
    except Exception as exc:print(json.dumps({'status':'DENY','reason':str(exc)}),flush=True);raise SystemExit(2)
