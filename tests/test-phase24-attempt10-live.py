"""Fresh F24 attempt 10 through the native launcher and approved Runner.

Run with the existing Hermes Python (psutil). This harness controls only its new
sandbox and owned processes; target implementation changes belong to Qwen Code.
No previous run, approval, deadline, ledger, or evidence is reused as execution.
"""

from f24_gates import catalog, evaluate as evaluate_frozen_gates
import base64
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import threading
import time
import uuid
from urllib.parse import urlparse

import psutil

from f24_attempt3_fixture import (
    BUILD_TEST, CRITERION, INITIAL_INVOICE, INITIAL_README, UNIT_TEST, make_plan,
)
from windows_launcher_adapter import launch_batch

ROOT = pathlib.Path(__file__).resolve().parents[1]
E = ROOT / 'evidence/phase-24-attempt-10-20261015'
E.mkdir(exist_ok=True)
PRESERVATION = E / 'history-before.json'
case = ROOT / 'sandbox' / ('f24-attempt10-' + uuid.uuid4().hex[:8])
project = case / 'project'
auto = project / '.autopilot'
PYTHON = 'C:/Python314/python.exe'
GLOBAL_SECONDS = 2700
q = lambda value: "'" + str(value).replace("'", "''") + "'"
start = time.monotonic()
harness_started_wall = time.time()
checks, samples, gpu, seen, run_parents = {}, [], [], {}, {}
runner = None
failure = None
consultation = None
run_id = None
clock_path = None
clock_before = None
clock_started = None
injection = None
reviewer_snapshot = None
reviewer_snapshots = []
reviewer_seen_keys = set()
last_sample = last_gpu = 0
resource_failure = None
monitor_stop = threading.Event()


def read(path):
    try:
        return json.loads(path.read_text(encoding='utf-8-sig'))
    except (ValueError, OSError):
        return None


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    (E / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def progress(stage, **details):
    print(json.dumps({'stage': stage, 'elapsed_seconds': round(time.monotonic() - start, 2), **details}, ensure_ascii=False), flush=True)


def verify_preserved():
    manifest=read(PRESERVATION)
    if not manifest or not manifest.get('files'):raise RuntimeError('HISTORICAL_MANIFEST_REQUIRED')
    bad=[relative for relative,expected in manifest['files'].items() if not(ROOT/relative).is_file() or sha(ROOT/relative)!=expected]
    for tree in ('sandbox/f24-live-8ec4f51b','sandbox/f24-attempt3-f79dd822','sandbox/f24-attempt4-2fbcc7d8'):
        expected={name for name in manifest['files'] if name.startswith(tree+'/')}
        actual={f.relative_to(ROOT).as_posix() for f in (ROOT/tree).rglob('*') if f.is_file()}
        bad.extend(sorted(actual-expected))
    return {'status':'PASS' if not bad else 'FAIL','files_checked':len(manifest['files']),'mismatches':bad,'classification':'ATTEMPT2 FAIL/GLOBAL_TIMEOUT; ATTEMPT3 HISTORICAL FAIL/BLOCKED_REQUIRES_HUMAN'}


def ps(body, timeout=90):
    code = ("$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules';"
            "$env:PYTHONUTF8='1';$env:PYTHONDONTWRITEBYTECODE='1';"
            "[Console]::OutputEncoding=[Text.Encoding]::UTF8;$r=& {" + body +
            "};Write-Output 'F24_JSON';$r|ConvertTo-Json -Depth 30 -Compress")
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand',
                             base64.b64encode(code.encode('utf-16le')).decode()],
                            capture_output=True, encoding='utf-8', timeout=timeout)
    if result.returncode:
        raise RuntimeError('MANDATORY_TEST_FAILED: adapter ' + result.stderr[-1500:] + result.stdout[-500:])
    health_guard()
    try:
        return json.loads(result.stdout.rsplit('F24_JSON', 1)[1].strip())
    except (IndexError, ValueError) as exc:
        raise RuntimeError('MANDATORY_TEST_FAILED: PS_JSON_OUTPUT ' + result.stdout[-1500:]) from exc


def git(*args):
    return subprocess.run(['git', '-C', str(project), *args], check=True, capture_output=True,
                          encoding='utf-8', timeout=30).stdout.strip()


def stop_owned_parents():
    for pid, birth in list(run_parents.items()):
        try:
            parent = psutil.Process(pid)
            if abs(parent.create_time() - birth) < .01:
                parent.kill()
        except psutil.NoSuchProcess:
            pass


def sample_resources():
    global last_sample, last_gpu
    now = time.monotonic()
    if now - last_sample < 5:
        return
    records = read(auto / 'PROCESSES.json') or {}
    memory = psutil.virtual_memory()
    rss = 0
    for item in records.get('processes', []):
        try:
            proc = psutil.Process(item['pid'])
            birth = proc.create_time()
            if abs(birth - (item['start_ticks'] / 1e7 - 62135596800)) > .01:
                continue
            seen[(proc.pid, birth)] = {'pid': proc.pid, 'birth': birth, 'role': item['name']}
            if item['name'] == 'llama':
                rss = proc.memory_info().rss
            for child in proc.children(recursive=True):
                try:
                    child_birth = child.create_time()
                    seen[(child.pid, child_birth)] = {'pid': child.pid, 'birth': child_birth, 'role': item['name']}
                except psutil.NoSuchProcess:
                    pass
        except psutil.NoSuchProcess:
            pass
    samples.append({'elapsed_seconds': now - start, 'ram_total_bytes': memory.total,
                    'ram_available_bytes': memory.available, 'llama_working_set_bytes': rss,
                    'pagefile': psutil.swap_memory()._asdict(), 'processes': len(psutil.pids())})
    last_sample = now
    if now - last_gpu > 15:
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'],
                                capture_output=True, text=True, timeout=5)
        if result.returncode:
            raise RuntimeError('MANDATORY_TEST_FAILED: GPU_RESOURCE_MEASUREMENT')
        gpu.append({'elapsed_seconds': now - start, 'memory_mib': result.stdout.strip()})
        last_gpu = now
    save('resources-live.json', {'samples': samples, 'gpu': gpu})
    if len(samples) >= 3 and all(row['ram_available_bytes'] < 150 * 1024**2 for row in samples[-3:]):
        raise RuntimeError('CRITICAL_RESOURCE_DEGRADATION: sustained RAM below 150 MiB')


def monitor():
    global resource_failure
    while not monitor_stop.is_set():
        try:
            sample_resources()
        except Exception as exc:
            resource_failure = str(exc)
            stop_owned_parents()
            return
        monitor_stop.wait(.25)


def health_guard():
    if resource_failure:
        raise RuntimeError(resource_failure)


def file_snapshot():
    return {name: sha(project / name) for name in ('invoice.py', 'README.md', 'test_invoice.py', 'build.py', 'QWEN.md')}


def read_events():
    path = auto / 'EVENTS.jsonl'
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def observe_clock():
    global clock_before, clock_started
    if clock_path and clock_path.exists() and clock_before is None:
        clock_before = clock_path.read_bytes()
        value = read(clock_path)
        if value['run_id'] != run_id:
            raise RuntimeError('SECURITY_REGRESSION: NEW_RUN_CLOCK_ID_MISMATCH')
        clock_started = dt.datetime.fromisoformat(value['started_at']).timestamp()
        save('native-clock-initial.json', {'clock_path': str(clock_path), 'value': value, 'sha256': sha(clock_path)})
        progress('NATIVE_CLOCK_STARTED', run_id=run_id, global_timeout_seconds=GLOBAL_SECONDS)


preflight=read(E/'ADMISSION.json')
if not preflight or preflight.get('status')!='PASS':raise RuntimeError('MINIMAL_ADMISSION_REQUIRED')
if not preflight.get('sealed') or any(sha(ROOT/path)!=digest for path,digest in preflight.get('source_hashes',{}).items()):raise RuntimeError('PREFLIGHT_SOURCES_CHANGED_OR_UNSEALED')
if sha(ROOT/'docs/F24-GATES.json')!=preflight['gates_sha256']:raise RuntimeError('FROZEN_GATES_CHANGED')
assert not subprocess.check_output(['git','status','--porcelain=v1'],cwd=ROOT,text=True).strip(), 'GIT_NOT_CLEAN_BEFORE_START'
save('FROZEN-GATES.json',catalog())
watcher = threading.Thread(target=monitor, daemon=True)
watcher.start()
try:
    preserved = verify_preserved()
    save('attempt-2-preservation-preflight.json', preserved)
    assert preserved['status'] == 'PASS', 'SECURITY_REGRESSION: ATTEMPT_2_CHANGED_BEFORE_START'
    if (E / 'fixture.json').exists():
        raise RuntimeError('BLOCKED_REQUIRES_HUMAN: ATTEMPT_10_ALREADY_PREPARED_DO_NOT_RESTART_HARNESS')
    project.mkdir(parents=True)
    save('fixture.json', {'attempt': 10, 'project': str(project), 'case': str(case),
                         'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                         'global_timeout_seconds': GLOBAL_SECONDS, 'setup_duration_included_in_resources': True,
                         'target_code_editor': 'Qwen Code Worker only'})
    for name, content in (('invoice.py', INITIAL_INVOICE), ('README.md', INITIAL_README),
                          ('test_invoice.py', UNIT_TEST), ('build.py', BUILD_TEST),
                          ('.gitignore', '.autopilot/\n__pycache__/\n')):
        (project / name).write_text(content, encoding='utf-8')
    for args in (('init', '-q'), ('config', 'user.name', 'DA F24 Sandbox'),
                 ('config', 'user.email', 'sandbox@example.invalid'),
                 ('add', '--', '.gitignore', 'invoice.py', 'README.md', 'test_invoice.py', 'build.py'),
                 ('commit', '-q', '-m', 'F24 attempt 10 immutable failing acceptance baseline')):
        git(*args)
    initial = subprocess.run([PYTHON, 'test_invoice.py'], cwd=project, capture_output=True, encoding='utf-8', timeout=30)
    (E / 'initial-test.txt').write_text(initial.stdout + initial.stderr, encoding='utf-8')
    checks['initial_test_fail'] = initial.returncode != 0 and 'Ran 13 tests' in initial.stderr
    assert checks['initial_test_fail'], 'MANDATORY_TEST_FAILED: ALL_INITIAL_ACCEPTANCE_TESTS_REQUIRED'
    plan = make_plan(project)
    consultation='f24-a10-'+uuid.uuid4().hex
    plan['task']=plan['task'].replace('then read .autopilot/evidence/WEB.json for official research.','then use the official research delivered inline by Runner; do not glob for it.')
    plan['research']={'url':'https://docs.python.org/3/library/decimal.html','diagnose_before_fetch':True}
    plan['consultation']={'id':consultation,'question':'Consulta F24 ATTEMPT 10: resume largest remainder, empates por índice, amount >= 0, weights >= 0 y suma positiva. Explica ROUND_HALF_UP. Responde breve e incluye áéíóú ñ.','response_timeout_seconds':60,'after_recovery':True,'new_conversation':True}
    plan['sandbox_crash_boundary']=True
    plan_path = case / 'plan.json'
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    save('immutable-tests-before-start.json', {'status': 'PASS', 'tests': plan['immutable_files'],
          'unit_test_methods': 13, 'required_examples': ['zero weight allowed', 'negative amount denied',
          'negative weight denied', 'all zero weights denied', 'single weight allowed'], 'initial_exit_code': initial.returncode})
    progress('IMMUTABLE_ACCEPTANCE_READY', tests=13)
    prepared = ps('& ' + q(ROOT / 'runner/run.ps1') + ' -Action Prepare -ProjectRoot ' + q(project) +
                  ' -Objective ' + q('Implement precise invoice arithmetic and cent-conserving allocation in isolated sandbox') +
                  ' -AcceptanceCriteria ' + q(CRITERION) + ' -PlanPath ' + q(plan_path) + ' | ConvertFrom-Json')
    save('prepare.json', prepared)
    checks['prepare'] = prepared['status'] == 'PASS'
    assert checks['prepare'], 'MANDATORY_TEST_FAILED: PREPARE'
    # New, still-unapproved contract/state reflect the stricter normal plan limits.
    cp=auto/'RUN-CONTRACT.yaml'
    subprocess.run([PYTHON,'-c',"import pathlib,sys,yaml;p=pathlib.Path(sys.argv[1]);c=yaml.safe_load(p.read_text(encoding='utf-8-sig'));c['time_budget_minutes']=45;p.write_text(yaml.safe_dump(c,sort_keys=False,allow_unicode=True),encoding='utf-8')",str(cp)],check=True,capture_output=True,timeout=15)
    state=read(auto/'STATE.json');state['max_cycles']=5;(auto/'STATE.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    ps('. '+q(ROOT/'scripts/state-manager.ps1')+';$state=Get-Content -LiteralPath '+q(auto/'STATE.json')+' -Raw -Encoding UTF8|ConvertFrom-Json; $null=Write-AtomicState -StateObj $state -AutopilotDir '+q(auto)+' -ValidateTransition $false; @{status="PASS"}')
    git('add', '--', 'QWEN.md')
    git('commit', '-q', '-m', 'F24 attempt 10 generated project control baseline')
    save('generated-control-baseline.json', {'sha256': sha(project / 'QWEN.md'), 'file': 'QWEN.md',
                                            'source': 'Prepare initializer before single approval'})
    preflight = ps('& ' + q(ROOT / 'runner/run.ps1') + ' -Action Preflight -ProjectRoot ' + q(project) + ' | ConvertFrom-Json')
    save('preflight.json', preflight)
    checks['preflight'] = preflight['status'] == 'PASS'
    assert checks['preflight'], 'MANDATORY_TEST_FAILED: PREFLIGHT'
    info = json.loads(subprocess.check_output([PYTHON, str(ROOT / 'runner/contract.py'), 'inspect', '--project', str(project)], encoding='utf-8'))
    run_id = info['contract']['run_id']
    assert run_id != 'run-20261014-020920', 'SECURITY_REGRESSION: OLD_RUN_REUSED'
    assert info['plan']['global_timeout_seconds'] == GLOBAL_SECONDS
    approval = subprocess.run([PYTHON, str(ROOT / 'runner/contract.py'), 'approve', '--project', str(project),
                               '--digest', info['digest']], capture_output=True, encoding='utf-8', check=True)
    approval_info = json.loads(approval.stdout)
    save('approval.json', approval_info)
    checks['single_approval'] = True
    clock_path = ROOT / 'runtime/run-clocks' / pathlib.Path(approval_info['receipt_path']).name
    assert consultation == plan['consultation']['id']
    save('consultation.json', {'consultation_id': consultation, 'run_id': run_id,
                              'source': 'Fresh F24 attempt 10, no prior consultation ID reused'})
    progress('PREPARED_APPROVED', run_id=run_id, project=str(project))
    for phase in (1, 2):
        out = (E / ('runner-' + str(phase) + '.stdout.txt')).open('w', encoding='utf-8')
        err = (E / ('runner-' + str(phase) + '.stderr.txt')).open('w', encoding='utf-8')
        if phase == 1:
            runner = launch_batch(ROOT / 'INICIAR-DESARROLLADOR-AUTONOMO.bat', [str(project)], stdout=out, stderr=err)
            checks['real_launcher_started'] = True
        else:
            assert clock_before and clock_path.read_bytes() == clock_before, 'SECURITY_REGRESSION: CLOCK_CHANGED_BEFORE_RECOVERY'
            runner = subprocess.Popen(['powershell.exe', '-NoProfile', '-NonInteractive', '-File', str(ROOT / 'runner/run.ps1'),
                                       '-ProjectRoot', str(project), '-Action', 'Start', '-Recover'], stdout=out, stderr=err)
        run_parents[runner.pid] = psutil.Process(runner.pid).create_time()
        progress('LAUNCHER_STARTED' if phase == 1 else 'NATIVE_RECOVERY_STARTED', pid=runner.pid)
        fallback_deadline = time.monotonic() + GLOBAL_SECONDS
        last_status = None
        while runner.poll() is None:
            observe_clock()
            if (clock_started and time.time() > clock_started + GLOBAL_SECONDS + 5) or time.monotonic() > fallback_deadline:
                raise RuntimeError('GLOBAL_TIMEOUT: ordinary 2700-second attempt 10 window exhausted')
            records = read(auto / 'PROCESSES.json') or {}
            try:
                parent = psutil.Process(records['runner_pid'])
                if parent.pid == runner.pid or any(ancestor.pid == runner.pid for ancestor in parent.parents()):
                    run_parents[parent.pid] = parent.create_time()
            except (KeyError, psutil.NoSuchProcess):
                pass
            state = read(auto / 'STATE.json') or {}
            status = (state.get('status'), state.get('current_task'))
            if status != last_status:
                progress('NATIVE_STATE', pass_number=phase, status=status[0], task=status[1])
                last_status = status
            if phase == 1 and injection is None:
                actual = read(auto / 'evidence/checks.json')
                if actual and all(actual.get(group) and all(item['status'] == 'PASS' for item in actual[group]) for group in ('tests', 'builds')):
                    parent = psutil.Process(records['runner_pid'])
                    birth = parent.create_time()
                    if run_parents.get(parent.pid) != birth:
                        raise RuntimeError('SECURITY_REGRESSION: UNOWNED_CRASH_TARGET')
                    parent.suspend()
                    before_crash_state = read(auto / 'STATE.json')
                    if before_crash_state.get('status') == 'COMPLETED':
                        parent.resume()
                        raise RuntimeError('MANDATORY_TEST_FAILED: RUN_COMPLETED_BEFORE_CONTROLLED_CRASH')
                    consumed=read(auto/'evidence/WEB-CONTEXT-DELIVERED.json') or {}
                    assert consumed.get('WEB_CONTEXT_DELIVERED') is True,'MANDATORY_TEST_FAILED: WEB_CONTEXT_NOT_DELIVERED'
                    checks['web']=True;checks['web_context_delivered']=True
                    save('web-context-before-crash.json',consumed)
                    save('checks-before-crash.json', actual)
                    save('events-before-crash.json', read_events())
                    ps('$null=& ' + q(ROOT / 'scripts/create-autopilot-checkpoint.ps1') + ' -ProjectPath ' + q(project) +
                       ' -CheckpointId ' + q('chk-f24-a10-before-crash-' + uuid.uuid4().hex[:8]) +
                       ' -Reason ' + q('Attempt 10 real native tests/build PASS before controlled owned parent crash') + ';@{status="PASS"}')
                    injection = {'runner_pid': parent.pid, 'runner_birth': birth, 'state': before_crash_state,
                                 'action': 'one controlled owned Runner parent crash after native checks PASS and immutable checkpoint'}
                    save('injection.json', injection)
                    parent.kill()
                    checks['native_tests_pass_before_crash'] = True
                    progress('CONTROLLED_PARENT_CRASH', runner_pid=parent.pid)
            if phase == 2:
                for item in records.get('processes', []):
                    key = (item['pid'], item['start_ticks'])
                    if (item['name'] == 'reviewer' and item['start_ticks'] / 1e7 - 62135596800 > recovery_started
                            and key not in reviewer_seen_keys):
                        reviewer_snapshot = file_snapshot()
                        reviewer_snapshots.append({'hashes': reviewer_snapshot, 'process': item})
                        reviewer_seen_keys.add(key)
                        save('readonly-reviewer-before.json', {'iterations': reviewer_snapshots})
                        progress('INDEPENDENT_REVIEWER_STARTED', pid=item['pid'], iteration=len(reviewer_snapshots))
            health_guard()
            time.sleep(.1)
        runner.wait(timeout=15)
        out.close()
        err.close()
        observe_clock()
        if phase == 1:
            if not injection:
                native_failure=(read(auto/'reports/runner-result.json') or {}).get('reason','NATIVE_WORKER_CRASH_GATE_NOT_REACHED')
                raise RuntimeError('MANDATORY_TEST_FAILED: '+native_failure+'; controlled crash gate not reached')
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline and not (auto / 'reports/watchdog-failure.json').exists():
                health_guard()
                time.sleep(.25)
            watchdog = read(auto / 'reports/watchdog-failure.json')
            save('watchdog.json', watchdog)
            checks['watchdog_checkpoint'] = bool(watchdog and watchdog['reason'] == 'PARENT_PROCESS_LOST' and list((auto / 'checkpoints').glob('*')))
            assert checks['watchdog_checkpoint'], 'MANDATORY_TEST_FAILED: WATCHDOG_CHECKPOINT'
            progress('WATCHDOG_PASS')
            # Mandatory continuation happens before the real managed consultation.
            recovery_started = time.time()
        else:
            report = read(auto / 'reports/runner-result.json') or {}
            gate = read(auto / 'evidence/completion-gate.json') or {}
            roles = read(auto / 'evidence/roles.json') or {}
            save('native-result.json', {'report': report, 'gate': gate, 'roles': roles})
            chat=read(auto/'evidence/CHATGPT.json') or {}
            retry=read(auto/'evidence/CHATGPT-RETRY.json') or {}
            save('chatgpt.json',chat);save('chatgpt-logical-retry.json',retry)
            ledger_path=ROOT/'runtime/chatgpt-consultations'/(hashlib.sha256(consultation.encode()).hexdigest()+'.json')
            ledger=read(ledger_path) or {};save('chatgpt-ledger-final.json',ledger)
            if report.get('status')=='BLOCKED_REQUIRES_HUMAN' or (ledger.get('send_attempts',0)>0 and ledger.get('delivery_state')!='COMPLETED'):
                raise RuntimeError('BLOCKED_REQUIRES_HUMAN: '+str(report.get('reason'))+'; NO RESEND')
            checks['chatgpt_real']=chat.get('status')=='SUCCESS' and chat.get('message_sent') and chat.get('response_received') and chat.get('composer_cleared')
            checks['chatgpt_utf8']=chat.get('source_text_equals_dom_text') is True and chat.get('utf8_valid') is True
            checks['chatgpt_idempotency']=retry.get('status')=='ALREADY_SENT' and retry.get('additional_physical_sends')==0 and retry.get('ledger_unchanged') is True and retry.get('budget_unchanged') is True

            checks['runner_completed'] = runner.returncode == 0 and report.get('status') == 'COMPLETED'
            checks['completion_gate'] = gate.get('status') == 'COMPLETED' and bool(gate.get('checks')) and all(gate['checks'].values())
            checks['independent_reviewer_accepted'] = gate.get('checks', {}).get('independent_reviewer_accepted') is True
            checks['reviewer_readonly'] = reviewer_snapshot is not None and reviewer_snapshot == file_snapshot()
            save('readonly-reviewer-after.json', {'hashes': file_snapshot(), 'unchanged': checks['reviewer_readonly']})
            cleanup = report.get('cleanup', {})
            checks['native_cleanup'] = not cleanup.get('owned_survivors', ['UNKNOWN']) and not cleanup.get('errors', ['UNKNOWN']) and not (auto / 'LOCK.json').exists()
            checks['disk_recovery'] = any(event['type'] == 'RUN_RECOVERED_FROM_DISK' for event in read_events())
            checks['clock_preserved_across_recovery'] = clock_before is not None and clock_path.read_bytes() == clock_before
            checks['duration_normal_budget'] = 0 < report.get('duration_seconds', 0) <= GLOBAL_SECONDS
            checks['immutable_tests_preserved'] = all(sha(project / pin['path']) == pin['sha256'] for pin in plan['immutable_files'])
            checks['native_state_terminal'] = (read(auto / 'STATE.json') or {}).get('status') == 'COMPLETED'
            assert all(checks.values()), 'MANDATORY_TEST_FAILED: ' + ','.join(name for name, value in checks.items() if not value)
            progress('NATIVE_COMPLETED', run_id=run_id, duration_seconds=report.get('duration_seconds'))
except Exception as exc:
    failure = str(exc)
    if consultation:
        pending_path = ROOT / 'runtime/chatgpt-consultations' / (hashlib.sha256(consultation.encode('utf-8')).hexdigest() + '.json')
        pending = read(pending_path) or {}
        if pending.get('send_attempts', 0) >= 1 and pending.get('delivery_state') != 'COMPLETED':
            save('chatgpt-ambiguous-stop.json', {'consultation_id': consultation, 'ledger': pending,
                 'original_error': failure, 'no_resend': True, 'ledger_modified_by_harness': False})
            if pending.get('delivery_state')=='SENT_CONFIRMED':
                failure='BLOCKED_REQUIRES_HUMAN: SENT_CONFIRMED / RESPONSE_PENDING retained; NO RESEND; '+failure
            else:
                failure = 'BLOCKED_REQUIRES_HUMAN: attempt 10 delivery unresolved after bridge interruption; NO RESEND; ' + failure
    progress('STOP', reason=failure)
finally:
    stop_owned_parents()
    if runner and runner.poll() is None:
        runner.kill()
        runner.wait(timeout=15)
    deadline = time.monotonic() + 45
    survivors = []
    while time.monotonic() < deadline:
        survivors = []
        for (pid, birth), record in list(seen.items()):
            try:
                if abs(psutil.Process(pid).create_time() - birth) < .01:
                    survivors.append(record)
            except psutil.NoSuchProcess:
                pass
        if not survivors:
            break
        time.sleep(.25)
    monitor_stop.set()
    watcher.join(timeout=10)
    if (auto / 'STATE.json').exists():
        duration = time.time() - clock_started if clock_started else time.monotonic() - start
        args = ['powershell.exe', '-NoProfile', '-NonInteractive', '-File', str(ROOT / 'tests/finalize-live-test.ps1'),
                '-ProjectRoot', str(project), '-EvidenceRoot', str(E), '-Duration', str(duration)]
        if failure:
            args += ['-Failure', failure]
        cleanup = subprocess.run(args, capture_output=True, encoding='utf-8', timeout=60)
        (E / 'cleanup.stdout.txt').write_text(cleanup.stdout, encoding='utf-8')
        (E / 'cleanup.stderr.txt').write_text(cleanup.stderr, encoding='utf-8')
        checks['final_cleanup'] = cleanup.returncode == 0 and (read(E / 'cleanup-final.json') or {}).get('status') == 'PASS'
        if not checks['final_cleanup']:
            failure = (failure or '') + '; MANDATORY_TEST_FAILED: FINAL_CLEANUP'
    save('resources-live.json', {'samples': samples, 'gpu': gpu})
    save('cleanup-identities.json', {'owned_processes': list(seen.values()), 'survivors': survivors, 'external_browser_preserved': True})
    try:
        preserved_after = verify_preserved()
        save('attempt-2-preservation-after.json', preserved_after)
        checks['attempt_2_preserved'] = preserved_after['status'] == 'PASS'
        if not checks['attempt_2_preserved']:
            failure = (failure or '') + '; SECURITY_REGRESSION: ATTEMPT_2_CHANGED'
    except Exception as exc:
        failure = (failure or '') + '; ' + str(exc)

if not failure:
    try:
        frozen=evaluate_frozen_gates(project,E,checks,injection,resource_failure);save('FROZEN-GATE-RESULT.json',frozen)
        if frozen['status']!='PASS':failure='MANDATORY_TEST_FAILED: FROZEN_GATE_'+','.join(k for k,v in frozen['gates'].items() if not v)
    except Exception as exc:failure='MANDATORY_TEST_FAILED: FROZEN_GATE_EVALUATION '+str(exc)
report = read(auto / 'reports/runner-result.json') or {}
result = {'status': 'FAIL' if failure or survivors or not all(checks.values()) else 'PASS', 'failure': failure,
          'attempt': 10, 'run_id': run_id, 'checks': checks, 'project': str(project), 'consultation_id': consultation,
          'duration_seconds': report.get('duration_seconds'), 'total_harness_elapsed_seconds': time.monotonic() - start,
          'setup_seconds': clock_started - harness_started_wall if clock_started else None,
          'global_timeout_seconds': GLOBAL_SECONDS, 'RAM_min_available_mib': min((row['ram_available_bytes'] for row in samples), default=0) / 1024**2,
          'pagefile_max_used_gib': max((row['pagefile']['used'] for row in samples), default=0) / 1024**3,
          'VRAM_max_mib': max((int(row['memory_mib'].split(',')[0]) for row in gpu if row['memory_mib']), default=None),
          'new_dependencies': [], 'no_push': True, 'F25_started': False}
save('SUMMARY.json', result)
print(json.dumps(result, ensure_ascii=False), flush=True)
raise SystemExit(0 if result['status'] == 'PASS' else 1)
