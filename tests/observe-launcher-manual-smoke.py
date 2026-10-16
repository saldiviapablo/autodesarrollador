"""Observe one human GUI run from files/PIDs; stop through the production API.

Never selects a folder, types, clicks, approves or sends a consultant message.
"""
import argparse,datetime,json,os,pathlib,subprocess,sys,time
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import project_launcher_ui as ui
import project_onboarding as data

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',required=True);parser.add_argument('--evidence',required=True);a=parser.parse_args()
    p=data.project(a.project);p.relative_to(R/'sandbox');assert p.name.startswith('launcher-live-'),'DISPOSABLE_LAUNCHER_SANDBOX_ONLY'
    E=pathlib.Path(a.evidence).resolve()
    assert E.is_relative_to(R/'evidence') or (E.parent==R/'runtime/project-launcher' and E.name.startswith('manual-observer-')),'OWNED_OBSERVER_OUTPUT_REQUIRED'
    E.mkdir(exist_ok=False)
    start=time.monotonic();run_start=None;run_id=None;supervisor=False;node=None;stop=None
    state_path=p/'.autopilot/STATE.json';event_path=p/'.autopilot/EVENTS.jsonl'
    before=data.snapshot(p)
    result={'kind':'GUI_TEST_OBSERVER_NOT_RUNNER_STATE','status':'WAITING_FOR_HUMAN_GUI','project':str(p),'observer_pid':os.getpid(),'observer_birth_ticks':ui.birth(os.getpid()),
            'gui_control_actions':0,'approval_actions':0,'human_wait_limit_seconds':1800,'native_smoke_limit_seconds':240,
            'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    def save(name,value):
        (E/name).write_text(data.secret.sanitize_text(json.dumps(value,ensure_ascii=False,indent=2))[0],encoding='utf-8')
    save('STATE.json',result)
    try:
        while time.monotonic()-start<1800:
            try:
                s=data.read(state_path)
                events=[json.loads(line) for line in event_path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
            except (OSError,ValueError):time.sleep(1);continue
            if not any(e['type']=='RUN_STARTED' for e in events):time.sleep(1);continue
            if run_start is None:
                run_start=time.monotonic();run_id=s['run_id'];grant=data.read(p/'.autopilot/evidence/ONBOARDING-APPROVAL.json')
                assert grant['method']=='HUMAN_PLAN_REVIEW' and grant['decision']=='APPROVE'
                result.update(status='OBSERVING_NATIVE_RUN',run_id=run_id,human_approval=grant)
                save('STATE.json',result)
            assert s['run_id']==run_id,'RUN_CHANGED_NO_AUTOMATIC_CONTINUATION'
            supervisor=any(e['type']=='PROCESS_EXITED' and e['payload'].get('name')=='supervisor' and e['payload'].get('exit_code')==0 for e in events)
            workers=[e['payload'] for e in events if e['type']=='PROCESS_STARTED' and e['payload'].get('name')=='worker']
            if supervisor and workers:
                record=workers[-1]
                if ui.birth(record['pid'])==record['start_ticks']:
                    # A bounded read-only CIM snapshot proves the actual Qwen
                    # CLI descendant exists, beyond merely starting agent-step.
                    code="Get-CimInstance Win32_Process | Where-Object {$_.Name -in @('node.exe','powershell.exe')} | Select-Object ProcessId,ParentProcessId,CommandLine | ConvertTo-Json -Depth 3 -Compress"
                    raw=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',code],capture_output=True,env=ui.ENV,timeout=10)
                    rows=json.loads(raw.stdout.decode('utf-8-sig'));rows=rows if isinstance(rows,list) else [rows]
                    parents={int(x['ProcessId']):int(x['ParentProcessId']) for x in rows}
                    for row in rows:
                        if 'cli-entry.js' not in (row.get('CommandLine') or ''):continue
                        parent=int(row['ProcessId']);seen=set()
                        while parent in parents and parent not in seen:
                            seen.add(parent);parent=parents[parent]
                            if parent==record['pid']:node={'pid':row['ProcessId'],'start_ticks':ui.birth(row['ProcessId']),'worker_record':record};break
                        if node:break
            if node or time.monotonic()-run_start>240:
                stop=ui.active_stop(p);save('STOP.json',stop);break
            if s['status'] in data.TERMINAL:raise ValueError('RUN_TERMINATED_BEFORE_SMOKE_STOP:'+s['status'])
            time.sleep(1)
        if run_start is None:raise ValueError('HUMAN_GUI_NOT_STARTED_WITHIN_OBSERVER_WINDOW')
        if stop is None:raise ValueError('NO_CONTROLLED_STOP_RECEIPT')
        deadline=time.monotonic()+90
        while time.monotonic()<deadline:
            try:
                s=data.read(state_path);report=data.read(p/'.autopilot/reports/runner-result.json')
                if s['status'] in data.TERMINAL and not (p/'.autopilot/LOCK.json').exists():break
            except (OSError,ValueError):pass
            time.sleep(1)
        report=data.read(p/'.autopilot/reports/runner-result.json');cleanup=report['cleanup']
        survivors=[x for x in report['processes'] if ui.birth(x['pid'])==x['start_ticks']]
        checks={'supervisor_success':supervisor,'actual_qwen_cli_started':bool(node),'controlled_stop':stop['status']=='STOP_REQUESTED',
                'terminal_abort':s['status']==report['status']=='ABORTED','reason_stop_requested':report['reason']=='STOP_REQUESTED',
                'no_lock':not(p/'.autopilot/LOCK.json').exists(),'inference_free':cleanup.get('inference_mutex')=='FREE',
                'run_mutex_released':cleanup.get('run_mutex_released') is True,'no_owned_survivors':not survivors and not cleanup['owned_survivors'],
                'checkpoint_present':bool(list((p/'.autopilot/checkpoints').iterdir()))}
        result.update(status='PASS' if all(checks.values()) else 'FAIL',checks=checks,qwen=node,run_duration_seconds=report['duration_seconds'],cleanup=cleanup)
        save('RUNNER-RESULT.json',report)
    except Exception as exc:result.update(status='FAIL',reason=str(exc))
    result.update(finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),initial_project_snapshot=before)
    save('RESULT.json',result);save('STATE.json',result)
    print(json.dumps({'status':result['status'],'evidence':str(E),'reason':result.get('reason')},ensure_ascii=False),flush=True)
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
