import importlib.util,json,pathlib,socket,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
spec=importlib.util.spec_from_file_location('governed_cron',ROOT/'scripts/governed-cron.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
project=ROOT/'sandbox/phase7a7-cron';e=ROOT/'evidence/phase-7a7';e.mkdir(exist_ok=True)
p,home=m.prepare(project)
import run_agent
def no_agent(*a,**k):raise AssertionError('NO_AGENT_JOB_CONSTRUCTED_LLM')
run_agent.AIAgent=no_agent
old_connect=socket.socket.connect
def deny_network(self,address):raise AssertionError('NO_AGENT_JOB_REQUESTED_NETWORK')
socket.socket.connect=deny_network
from cron.jobs import list_jobs
job_id=None
lock_before=(ROOT/'runtime/locks/inference-owner.json').read_bytes()
report={}
try:
    created=m.operation('create',project,'health_snapshot');assert created['success'],created
    job_id=created['job']['job_id']
    listed=m.operation('list',project);assert any(j['id']==job_id for j in listed['jobs'])
    paused=m.operation('pause',project,job_id=job_id);assert paused['success'],paused
    resumed=m.operation('resume',project,job_id=job_id);assert resumed['success'],resumed
    ran=m.operation('run',project,job_id=job_id);assert ran['success'] and 'HEALTH_SNAPSHOT' in ran['output'],ran
    denied={}
    for name in ('unknown_job','git push --force','../evil.py'):
        try:m.operation('create',project,name);raise AssertionError('Unauthorized job admitted')
        except ValueError as err:denied[name]=str(err)
    original=(home/'scripts/health-snapshot.py').read_bytes()
    (home/'scripts/health-snapshot.py').write_text('print("tampered")')
    try:
        try:m.operation('run',project,job_id=job_id);raise AssertionError('Tampered job ran')
        except ValueError as err:denied['tampered_script']=str(err)
    finally:(home/'scripts/health-snapshot.py').write_bytes(original)
    # Exercise native deadline/descendant cleanup using an unscheduled private fixture.
    import os
    from cron.scheduler_script import _run_job_script
    fixture=home/'scripts/timeout-fixture.py'
    fixture.write_text('import os,time,pathlib\npathlib.Path("timeout-pid.txt").write_text(str(os.getpid()))\ntime.sleep(30)\n')
    os.environ['HERMES_CRON_SCRIPT_TIMEOUT']='1'
    ok,output=_run_job_script('timeout-fixture.py',workdir=str(project))
    assert not ok and 'timed out' in output,output
    import psutil
    pid=int((project/'timeout-pid.txt').read_text());assert not psutil.pid_exists(pid),pid
    fixture.unlink();(project/'timeout-pid.txt').unlink()
    removed=m.operation('remove',project,job_id=job_id);assert removed['success'],removed;job_id=None
    assert not list_jobs(include_disabled=True)
    assert (ROOT/'runtime/locks/inference-owner.json').read_bytes()==lock_before
    report={'status':'PASS','tests':{'T-7A-CRON-001':'PASS','T-7A-CRON-002':'PASS','T-7A-CRON-003_TIMEOUT':'PASS'},'native_create_list_pause_resume_remove':True,'native_no_agent_run':ran,'denied':denied,'timeout':output,'timeout_pid_stopped':True,'remaining_jobs':0,'timers_started':0,'llm_constructor_tripwire':True,'network_tripwire':True,'inference_lock_unchanged':True,'local_inferences':0}
finally:
    socket.socket.connect=old_connect
    if job_id:m.operation('remove',project,job_id=job_id)
    (e/'tests.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
if report:
    (e/'security.json').write_text(json.dumps({'status':'PASS','denied':report['denied'],'cleanup_jobs':0,'timeout_pid_stopped':True},indent=2)+'\n')
print(json.dumps(report));assert report.get('status')=='PASS'
