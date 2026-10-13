"""Owned sandbox factories; fake mode is explicitly labelled, never claims native inference."""
import hashlib,json,pathlib,subprocess,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]
def powershell(script,*args,timeout=30):
    return subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-File',str(ROOT/script),*map(str,args)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
def project(name,backend='probe',delay=0,phase_timeout=15,global_timeout=90):
    p=ROOT/'sandbox'/('7b-'+name+'-'+uuid.uuid4().hex[:8]);p.mkdir()
    r=powershell('scripts/init-autopilot-project.ps1','-ProjectPath',p,'-Objective','Implement correct addition with verified tests','-AcceptanceCriteria','addition verified')
    assert r.returncode==0,r.stderr
    (p/'calculator.py').write_text('def add(a,b):\n    return a+b\n' if backend=='probe' else 'def add(a,b):\n    return a-b\n')
    test=p/'test_calculator.py';test.write_text('from calculator import add\nassert add(2,3)==5\nassert add(-1,3)==2\nprint("RUNNER_TEST_PASS")\n')
    (p/'.gitignore').write_text('.autopilot/\n__pycache__/\n')
    subprocess.run(['git','-C',str(p),'init','-q'],check=True);subprocess.run(['git','-C',str(p),'config','user.name','DA Sandbox'],check=True);subprocess.run(['git','-C',str(p),'config','user.email','sandbox@example.invalid'],check=True)
    subprocess.run(['git','-C',str(p),'add','--','.gitignore','calculator.py','test_calculator.py','QWEN.md'],check=True);subprocess.run(['git','-C',str(p),'commit','-q','-m','sandbox baseline'],check=True)
    plan={'schema_version':'1.0','task':'Change calculator.py add to return a+b; run python test_calculator.py. Never edit tests or .autopilot.','backend':backend,'allowed_files':['calculator.py'],'tests':[{'id':'unit','argv':['python','test_calculator.py'],'marker':'RUNNER_TEST_PASS'}],'builds':[],'no_build_reason':'Python fixture has no separate compilation step','criteria':[{'criterion':'addition verified','test_id':'unit'}],'artifacts':[{'path':'calculator.py','min_bytes':10}],'immutable_files':[{'path':'test_calculator.py','sha256':hashlib.sha256(test.read_bytes()).hexdigest()}],'phase_timeout_seconds':phase_timeout,'global_timeout_seconds':global_timeout,'probe_delay_seconds':delay}
    (p/'.autopilot/RUN-PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
    return p
def admission(p,action='inspect',digest=None):
    args=['C:/Python314/python.exe',str(ROOT/'runner/contract.py'),action,'--project',str(p)]
    if digest:args+=['--digest',digest]
    r=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',timeout=20);return r,json.loads(r.stdout)
def approve(p):
    r,data=admission(p);assert r.returncode==0,data
    r,data=admission(p,'approve',data['digest']);assert r.returncode==0,data
    return data
def start(p,timeout=180):return powershell('runner/run.ps1','-ProjectRoot',p,'-Action','Start',timeout=timeout)
