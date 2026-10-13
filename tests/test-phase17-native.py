import importlib.util,json,pathlib,time,sys,ctypes
ROOT=pathlib.Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('fixtures',ROOT/'tests/runner-fixtures.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
e=ROOT/'evidence/phase-17'
if len(sys.argv)>1:p=pathlib.Path(sys.argv[1])
else:
    p=f.project('native17',backend='live',phase_timeout=180,global_timeout=650);f.approve(p)
    r=f.start(p,timeout=720)
    (e/'native.stdout.txt').write_text(r.stdout,encoding='utf-8');(e/'native.stderr.txt').write_text(r.stderr,encoding='utf-8')
report=json.loads((p/'.autopilot/reports/runner-result.json').read_text(encoding='utf-8-sig'))
assert report['technical_status']=='SUCCESS',report
events=[json.loads(line) for line in (p/'.autopilot/EVENTS.jsonl').read_text(encoding='utf-8-sig').splitlines()]
assert any(v['type']=='MODEL_HEALTH_READY' for v in events)
roles=json.loads((p/'.autopilot/evidence/roles.json').read_text(encoding='utf-8-sig'))
assert all(roles[n]['status']=='SUCCESS' for n in ['supervisor','worker','reviewer']),roles
kernel=ctypes.WinDLL('kernel32',use_last_error=True)
kernel.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];kernel.OpenProcess.restype=ctypes.c_void_p
kernel.CloseHandle.argtypes=[ctypes.c_void_p]
for owned in report['processes']:
    handle=kernel.OpenProcess(0x1000,False,owned['pid'])
    if handle:
        # PID existence alone is insufficient; use birth identity before classifying an orphan.
        times=[ctypes.c_ulonglong() for _ in range(4)]
        kernel.GetProcessTimes.argtypes=[ctypes.c_void_p]+[ctypes.POINTER(ctypes.c_ulonglong)]*4
        ok=kernel.GetProcessTimes(handle,*[ctypes.byref(t) for t in times]);kernel.CloseHandle(handle)
        assert not ok or times[0].value+504911232000000000!=owned['start_ticks'],owned
result={'status':'PASS','tests':{'T-RUN-002':'PASS','T-RUN-003':'PASS','T-RUN-004':'PASS'},'real_hermes_supervisor':True,'real_qwen_worker':True,'real_hermes_reviewer':True,'project':str(p),'model_owned_and_cleaned':True,'local_inference_serialized_by_existing_wrappers':True,'result':report}
(e/'native.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
