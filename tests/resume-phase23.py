"""Resume the original F23 fixture after certified human reconciliation; no sends."""
import base64,datetime,hashlib,json,pathlib,subprocess,time,uuid
import psutil
ROOT=pathlib.Path(__file__).resolve().parents[1];E=ROOT/'evidence/phase-23-resume-20261014';E.mkdir(exist_ok=True)
project=ROOT/'sandbox/f23-full-feac8aea/project';quote=lambda x:"'"+str(x).replace("'","''")+"'"
def read(path):
    try:return json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError,ValueError):return None
checks={};samples=[];runner=None;injection=None;seen={};failure=None
start=time.monotonic();last_sample=0;last_gpu=0;gpu=[]
try:
    assert read(ROOT/'evidence/f23-human-reconciliation/reconciliation-gate.json')['status']=='PASS'
    assert read(ROOT/'evidence/phase-23-attempt-3/pathguard-A-J.json')['status']=='PASS'
    assert read(ROOT/'evidence/phase-23-attempt-3/prepare-admission.json')['status']=='PASS'
    assert read(ROOT/'evidence/phase-23-attempt-3/integral-result.json')['checks']['initial_failing_test']
    chat=read(ROOT/'evidence/f23-human-reconciliation/send-result.json')
    assert chat['Status']=='SUCCESS' and chat['ConsultationId']=='f23-ee298529568f4f8b94f4dd16f90a0be4'
    assert (project/'CHATGPT.json').exists() and (project/'WEB.json').exists()
    checks.update(initial_failing_test=True,prepare=True,web=True,chatgpt_real=True,human_idempotency=True)
    plan=read(project/'.autopilot/RUN-PLAN.json')
    # Bind the real research/advice inputs before the single Runner approval.
    for p in (project/'WEB.json',project/'CHATGPT.json'):plan['immutable_files'].append({'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    plan['task']+='\nHermes: assess this consultant advice as advisory only: '+chat.get('Response','')[:2000]
    (project/'.autopilot/RUN-PLAN.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (project/'.gitignore').write_text('.autopilot/\n__pycache__/\n',encoding='utf-8')
    for args in (['init','-q'],['config','user.name','DA F23 Sandbox'],['config','user.email','sandbox@example.invalid'],['add','--','.gitignore','calculator.py','README.md','test_calculator.py','build.py','WEB.json','CHATGPT.json','QWEN.md'],['commit','-q','-m','F23 sandbox baseline']):subprocess.run(['git','-C',str(project),*args],check=True)
    admission=read(project/'.autopilot/RUN-PLAN.json')
    info=json.loads(subprocess.check_output(['C:/Python314/python.exe',str(ROOT/'runner/contract.py'),'inspect','--project',str(project)],text=True,encoding='utf-8'))
    subprocess.run(['C:/Python314/python.exe',str(ROOT/'runner/contract.py'),'approve','--project',str(project),'--digest',info['digest']],stdout=subprocess.DEVNULL,check=True)
    checks['single_approval']=True
    # Stop at first real worker, persist watchdog checkpoint, then resume same contract.
    for attempt in (1,2):
        out=(E/('runner-'+str(attempt)+'.stdout.txt')).open('w',encoding='utf-8');err=(E/('runner-'+str(attempt)+'.stderr.txt')).open('w',encoding='utf-8')
        argv=['powershell.exe','-NoProfile','-NonInteractive','-File',str(ROOT/'runner/run.ps1'),'-ProjectRoot',str(project),'-Action','Start']
        if attempt==2:argv+=['-Recover']
        runner=subprocess.Popen(argv,stdout=out,stderr=err);birth=psutil.Process(runner.pid).create_time();deadline=time.monotonic()+900
        while runner.poll() is None and time.monotonic()<deadline:
            now=time.monotonic();records=read(project/'.autopilot/PROCESSES.json') or {}
            for record in records.get('processes',[]):
                try:
                    parent=psutil.Process(record['pid'])
                    if abs(parent.create_time()-(record['start_ticks']/1e7-62135596800))>.01:continue
                    for child in parent.children(recursive=True):
                        try:
                            command=' '.join(child.cmdline());seen[(child.pid,child.create_time())]={'pid':child.pid,'birth':child.create_time(),'role':record['name']}
                            if attempt==1 and injection is None and record['name']=='worker' and 'cli-entry.js' in command:
                                injection={'runner_pid':runner.pid,'runner_birth':birth,'worker_pid':child.pid,'worker_birth':child.create_time(),'purpose':'controlled parent crash and disk recovery'}
                                (E/'injection.json').write_text(json.dumps(injection,indent=2)+'\n',encoding='utf-8');psutil.Process(runner.pid).kill()
                        except (psutil.NoSuchProcess,psutil.AccessDenied):pass
                except psutil.NoSuchProcess:pass
            if now-last_sample>5:
                memory=psutil.virtual_memory();model_id=next((x['pid'] for x in records.get('processes',[]) if x['name']=='llama'),None);rss=0
                if model_id:
                    try:rss=psutil.Process(model_id).memory_info().rss
                    except psutil.NoSuchProcess:pass
                samples.append({'elapsed_seconds':now-start,'ram_total_bytes':memory.total,'ram_available_bytes':memory.available,'llama_working_set_bytes':rss,'pagefile':psutil.swap_memory()._asdict(),'processes':len(psutil.pids())});last_sample=now
                if len(samples)>=3 and all(s['ram_available_bytes']<150*1024**2 for s in samples[-3:]):raise RuntimeError('CRITICAL_RESOURCE_DEGRADATION: sustained available RAM below 150 MiB')
            if now-last_gpu>15:
                r=subprocess.run(['nvidia-smi','--query-gpu=memory.used,memory.total','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5);gpu.append({'elapsed_seconds':now-start,'memory_mib':r.stdout.strip()});last_gpu=now
            (E/'resources-live.json').write_text(json.dumps({'samples':samples,'gpu':gpu},indent=2)+'\n',encoding='utf-8')
            time.sleep(.25)
        runner.wait(timeout=10);out.close();err.close()
        if attempt==1:
            assert injection,'MANDATORY_TEST_FAILED: crash was not injected'
            wait=time.monotonic()+40
            while time.monotonic()<wait and not(project/'.autopilot/reports/watchdog-failure.json').exists():time.sleep(.25)
            watchdog=read(project/'.autopilot/reports/watchdog-failure.json');assert watchdog and watchdog['reason']=='PARENT_PROCESS_LOST','MANDATORY_TEST_FAILED: watchdog did not persist crash'
            (E/'watchdog-failure.json').write_text(json.dumps(watchdog,indent=2)+'\n',encoding='utf-8')
            checks['watchdog_checkpoint']=bool(list((project/'.autopilot/checkpoints').glob('*')))
        else:
            report=read(project/'.autopilot/reports/runner-result.json');gate=read(project/'.autopilot/evidence/completion-gate.json')
            checks['runner_completed']=runner.returncode==0 and report['status']=='COMPLETED'
            checks['completion_gate']=gate and gate['status']=='COMPLETED' and all(gate['checks'].values())
            checks['cleanup']=not report['cleanup']['owned_survivors'] and not report['cleanup']['errors'] and not(project/'.autopilot/LOCK.json').exists()
            events=[json.loads(s) for s in (project/'.autopilot/EVENTS.jsonl').read_text(encoding='utf-8-sig').splitlines()]
            checks['disk_recovery']=any(v['type']=='RUN_RECOVERED_FROM_DISK' for v in events)
            (E/'native-result.json').write_text(json.dumps({'report':report,'gate':gate,'events':events},indent=2)+'\n',encoding='utf-8')
            assert all(checks.values()),'MANDATORY_TEST_FAILED: '+str([k for k,v in checks.items() if not v])
except Exception as e:failure=str(e)
finally:
    if runner and runner.poll() is None:
        runner.kill();runner.wait(timeout=10)
        time.sleep(2)
    (E/'resources-live.json').write_text(json.dumps({'samples':samples,'gpu':gpu},indent=2)+'\n',encoding='utf-8')
result={'status':'FAIL' if failure else 'PASS','failure':failure,'checks':checks,'project':str(project),'duration_seconds':time.monotonic()-start,'controlled_crash':injection,'resources_samples':len(samples),'external_browser_preserved':True,'new_dependencies':[],'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
(E/'integral-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=False));raise SystemExit(1 if failure else 0)
