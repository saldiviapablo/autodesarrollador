"""Resource and process audit for the bounded F23 reviewer continuation."""
import json, pathlib, subprocess, time
import psutil
ROOT=pathlib.Path(__file__).resolve().parents[1]
E=ROOT/'evidence/hermes-prompt-transport-20261014'
samples=[];gpu=[];owned={};reason=None;started=time.monotonic()
with (E/'maintenance.stdout.txt').open('w',encoding='utf-8') as out, (E/'maintenance.stderr.txt').open('w',encoding='utf-8') as err:
    process=subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-File',str(ROOT/'tests/resume-phase23-reviewer.ps1')],stdout=out,stderr=err)
    parent=psutil.Process(process.pid);birth=parent.create_time()
    try:
        while process.poll() is None:
            children=parent.children(recursive=True)
            for child in children:
                try:owned[(child.pid,child.create_time())]=child
                except psutil.NoSuchProcess:pass
            memory=psutil.virtual_memory();sample={'elapsed_seconds':time.monotonic()-started,'ram_available_bytes':memory.available,'ram_total_bytes':memory.total,'pagefile':psutil.swap_memory()._asdict(),'llama_working_set_bytes':0}
            for child in children:
                try:
                    if child.name()=='llama-server.exe':sample['llama_working_set_bytes']=child.memory_info().rss
                except psutil.NoSuchProcess:pass
            samples.append(sample)
            r=subprocess.run(['nvidia-smi','--query-gpu=memory.used,memory.total','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5)
            gpu.append({'elapsed_seconds':sample['elapsed_seconds'],'memory_mib':r.stdout.strip()})
            (E/'resources-live.json').write_text(json.dumps({'samples':samples,'gpu':gpu},indent=2)+'\n',encoding='utf-8')
            if len(samples)>=3 and all(s['ram_available_bytes']<150*1024**2 for s in samples[-3:]):
                reason='CRITICAL_RESOURCE_DEGRADATION: 3 consecutive 5s samples below 150 MiB';break
            if time.monotonic()-started>660:reason='MANDATORY_TEST_FAILED: MAINTENANCE_TIMEOUT';break
            time.sleep(5)
    finally:
        if process.poll() is None:
            # Abort only the verified task-owned parent; its kernel job closes descendants.
            if parent.create_time()==birth:parent.kill()
        process.wait(timeout=15)
        time.sleep(1)
survivors=[]
for (pid,birth),child in owned.items():
    try:
        if child.is_running() and child.create_time()==birth:survivors.append({'pid':pid,'birth':birth,'name':child.name()})
    except psutil.NoSuchProcess:pass
result={'status':'PASS' if process.returncode==0 and not reason and not survivors else 'FAIL','reason':reason,'exit_code':process.returncode,'duration_seconds':time.monotonic()-started,'owned_survivors':survivors,'ram_min_available_mib':min(s['ram_available_bytes'] for s in samples)/1024**2,'pagefile_max_used_gib':max(s['pagefile']['used'] for s in samples)/1024**3,'vram_max_mib':max(int(g['memory_mib'].split(',')[0]) for g in gpu if g['memory_mib'])}
(E/'resource-summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result));raise SystemExit(0 if result['status']=='PASS' else 1)
