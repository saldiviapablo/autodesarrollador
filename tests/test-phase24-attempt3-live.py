"""Fresh F24 attempt 3 through the native launcher and unchanged Runner.

Run with the existing Hermes Python (psutil). This harness controls only its new
sandbox and owned processes; target implementation changes belong to Qwen Code.
No previous run, approval, deadline, ledger, or evidence is reused as execution.
"""

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
E = ROOT / 'evidence/phase-24-attempt-3-20261014'
E.mkdir(exist_ok=True)
PRESERVATION = E / 'attempt-2-preservation-before.json'
case = ROOT / 'sandbox' / ('f24-attempt3-' + uuid.uuid4().hex[:8])
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
    manifest = read(PRESERVATION)
    if not manifest or manifest.get('run_id') != 'run-20261014-020920' or not manifest.get('files'):
        raise RuntimeError('SECURITY_REGRESSION: ATTEMPT_2_PRESERVATION_MANIFEST_REQUIRED')
    bad = []
    for relative, expected in manifest['files'].items():
        path = ROOT / relative
        if not path.is_file() or sha(path) != expected:
            bad.append(relative)
    old_sandbox = ROOT / 'sandbox/f24-live-8ec4f51b'
    old_names = {name for name in manifest['files'] if name.startswith('sandbox/f24-live-8ec4f51b/')}
    current_names = {path.relative_to(ROOT).as_posix() for path in old_sandbox.rglob('*') if path.is_file() or path.is_symlink()}
    added = sorted(current_names - old_names)
    bad.extend(added)
    return {'status': 'PASS' if not bad else 'FAIL', 'files_checked': len(manifest['files']), 'mismatches': bad,
            'added_old_sandbox_files': added,
            'closed_classification': manifest['closed_classification'], 'old_state_written': False}


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


watcher = threading.Thread(target=monitor, daemon=True)
watcher.start()
try:
    preserved = verify_preserved()
    save('attempt-2-preservation-preflight.json', preserved)
    assert preserved['status'] == 'PASS', 'SECURITY_REGRESSION: ATTEMPT_2_CHANGED_BEFORE_START'
    if (E / 'fixture.json').exists():
        raise RuntimeError('BLOCKED_REQUIRES_HUMAN: ATTEMPT_3_ALREADY_PREPARED_DO_NOT_RESTART_HARNESS')
    project.mkdir(parents=True)
    save('fixture.json', {'attempt': 3, 'project': str(project), 'case': str(case),
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
                 ('commit', '-q', '-m', 'F24 attempt 3 immutable failing acceptance baseline')):
        git(*args)
    initial = subprocess.run([PYTHON, 'test_invoice.py'], cwd=project, capture_output=True, encoding='utf-8', timeout=30)
    (E / 'initial-test.txt').write_text(initial.stdout + initial.stderr, encoding='utf-8')
    checks['initial_test_fail'] = initial.returncode != 0 and 'Ran 13 tests' in initial.stderr
    assert checks['initial_test_fail'], 'MANDATORY_TEST_FAILED: ALL_INITIAL_ACCEPTANCE_TESTS_REQUIRED'
    plan = make_plan(project)
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
    git('add', '--', 'QWEN.md')
    git('commit', '-q', '-m', 'F24 attempt 3 generated project control baseline')
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
    consultation = 'f24-a3-' + run_id + '-' + uuid.uuid4().hex[:8]
    save('consultation.json', {'consultation_id': consultation, 'run_id': run_id,
                              'source': 'Fresh F24 attempt 3, no prior consultation ID reused'})
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
                raise RuntimeError('GLOBAL_TIMEOUT: ordinary 2700-second attempt 3 window exhausted')
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
            if phase == 1 and not checks.get('web') and any(item['name'] == 'supervisor' for item in records.get('processes', [])):
                web = ps('& ' + q(ROOT / 'scripts/web-research.ps1') +
                         ' -Url https://docs.python.org/3/library/decimal.html -OutputPath ' + q(auto / 'evidence/WEB.json'))
                save('web.json', web)
                checks['web'] = bool(web['Success'])
                assert checks['web'], 'MANDATORY_TEST_FAILED: REAL_OFFICIAL_WEB'
                progress('REAL_WEB_PASS')
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
                    save('checks-before-crash.json', actual)
                    save('events-before-crash.json', read_events())
                    ps('$null=& ' + q(ROOT / 'scripts/create-autopilot-checkpoint.ps1') + ' -ProjectPath ' + q(project) +
                       ' -CheckpointId ' + q('chk-f24-a3-before-crash-' + uuid.uuid4().hex[:8]) +
                       ' -Reason ' + q('Attempt 3 real native tests/build PASS before controlled owned parent crash') + ';@{status="PASS"}')
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
            assert injection, 'MANDATORY_TEST_FAILED: NATIVE_WORKER_CRASH_GATE_NOT_REACHED'
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline and not (auto / 'reports/watchdog-failure.json').exists():
                health_guard()
                time.sleep(.25)
            watchdog = read(auto / 'reports/watchdog-failure.json')
            save('watchdog.json', watchdog)
            checks['watchdog_checkpoint'] = bool(watchdog and watchdog['reason'] == 'PARENT_PROCESS_LOST' and list((auto / 'checkpoints').glob('*')))
            assert checks['watchdog_checkpoint'], 'MANDATORY_TEST_FAILED: WATCHDOG_CHECKPOINT'
            progress('WATCHDOG_PASS')
            session = ps('& ' + q(ROOT / 'scripts/consultar-chatgpt.ps1') + ' -Action check-session -ConsultationId ' +
                         q(consultation) + ' -TimeoutSeconds 25')
            save('chatgpt-session.json', session)
            if session.get('Status') != 'SUCCESS' or not session.get('ResultObj', {}).get('session_ready'):
                raise RuntimeError('BLOCKED_REQUIRES_HUMAN: dedicated ChatGPT session not ready')
            chat = ps('& ' + q(ROOT / 'scripts/consultar-chatgpt.ps1') + ' -Question ' + q(
                'Consulta F24 ATTEMPT 3: explica brevemente largest remainder para distribuir 0.05 entre tres pesos iguales, '
                'desempate por índice, amount >= 0, weights >= 0 con suma positiva y peso cero permitido. '
                'Distingue ROUND_HALF_UP del total y floor de cuotas. Incluye áéíóú ñ.') +
                ' -ConsultationId ' + q(consultation) + ' -StatePath ' + q(auto / 'STATE.json') +
                ' -TimeoutSeconds 60 -OutputPath ' + q(auto / 'evidence/CHATGPT.json'), 95)
            save('chatgpt.json', chat)
            ledger_path = ROOT / 'runtime/chatgpt-consultations' / (hashlib.sha256(consultation.encode('utf-8')).hexdigest() + '.json')
            ledger = read(ledger_path) or {}
            save('chatgpt-ledger-final.json', ledger)
            if (chat.get('Status') == 'UNKNOWN_DELIVERY' or
                    (ledger.get('send_attempts', 0) >= 1 and ledger.get('delivery_state') != 'COMPLETED')):
                raise RuntimeError('BLOCKED_REQUIRES_HUMAN: attempt 3 UNKNOWN_DELIVERY; NO RESEND')
            result = chat.get('ResultObj', {})
            checks['chatgpt_real'] = chat.get('Status') == 'SUCCESS' and result.get('message_sent') and result.get('response_received')
            checks['chatgpt_turn_deltas'] = (result.get('user_turns_after') == result.get('user_turns_before', -2) + 1 and
                                            result.get('assistant_turns_after') == result.get('assistant_turns_before', -2) + 1)
            checks['chatgpt_composer_empty'] = result.get('composer_cleared') is True
            checks['chatgpt_single_physical_send'] = result.get('physical_send_count') == 1
            checks['chatgpt_utf8'] = result.get('source_text_equals_dom_text') is True and 'áéíóú ñ' in result.get('source_text', '')
            parsed = urlparse(result.get('url', ''))
            checks['chatgpt_domain'] = parsed.scheme == 'https' and parsed.hostname == 'chatgpt.com'
            checks['chatgpt_ledger_completed'] = ledger.get('delivery_state') == 'COMPLETED' and ledger.get('send_attempts') == 1
            checks['chatgpt_baseline_persisted'] = (ledger.get('user_turns_before') == result.get('user_turns_before') and
                ledger.get('assistant_turns_before') == result.get('assistant_turns_before') and bool(ledger.get('conversation_url')))
            history = ledger.get('history', [])
            baseline_positions = [index for index, event in enumerate(history) if event.get('from') == 'RESERVED' and
                                  event.get('to') == 'RESERVED' and event.get('send_attempts') == 0]
            intent_positions = [index for index, event in enumerate(history) if event.get('to') == 'DELIVERY_INTENT' and
                                event.get('send_attempts') == 1]
            checks['chatgpt_baseline_before_intent'] = bool(baseline_positions and intent_positions and
                baseline_positions[0] < intent_positions[0] and
                dt.datetime.fromisoformat(history[baseline_positions[0]]['at'].replace('Z', '+00:00')) <=
                dt.datetime.fromisoformat(history[intent_positions[0]]['at'].replace('Z', '+00:00')))
            session_url = session.get('ResultObj', {}).get('url', '')
            session_conversation = urlparse(session_url).path.removeprefix('/c/') if '/c/' in urlparse(session_url).path else None
            conversation_id = parsed.path.removeprefix('/c/') if parsed.path.startswith('/c/') else None
            checks['chatgpt_conversation_persisted'] = bool(conversation_id and ledger.get('conversation_url') == result.get('url'))
            if session_conversation:
                checks['chatgpt_reused_conversation_unchanged'] = session_conversation == conversation_id
            save('chatgpt-baseline-proof.json', {'consultation_id': consultation, 'run_id': run_id,
                'conversation_id': conversation_id, 'conversation_url': ledger.get('conversation_url'),
                'session_url_before_attempt': session_url, 'baseline_user_turns': ledger.get('user_turns_before'),
                'baseline_assistant_turns': ledger.get('assistant_turns_before'), 'baseline_history_positions': baseline_positions,
                'delivery_intent_history_positions': intent_positions, 'ledger_sha256': sha(ledger_path),
                'baseline_before_intent': checks['chatgpt_baseline_before_intent']})
            (E / 'chatgpt-response.txt').write_text(chat.get('Response', ''), encoding='utf-8')
            assert all(checks[name] for name in checks if name.startswith('chatgpt_')), 'MANDATORY_TEST_FAILED: CHATGPT_CONFIRMATION'
            ledger_before = ledger_path.read_bytes()
            state_before = (auto / 'STATE.json').read_bytes()
            retry = ps('& ' + q(ROOT / 'scripts/consultar-chatgpt.ps1') + ' -ConsultationId ' + q(consultation) +
                       ' -StatePath ' + q(auto / 'STATE.json') + ' -TimeoutSeconds 15')
            checks['chatgpt_idempotency'] = (retry.get('Status') == 'ALREADY_SENT' and ledger_path.read_bytes() == ledger_before and
                                            (auto / 'STATE.json').read_bytes() == state_before)
            save('chatgpt-logical-retry.json', {'result': retry, 'additional_physical_sends': 0 if checks['chatgpt_idempotency'] else None,
                                             'ledger_unchanged': ledger_path.read_bytes() == ledger_before,
                                             'budget_state_unchanged': (auto / 'STATE.json').read_bytes() == state_before})
            assert checks['chatgpt_idempotency'], 'SECURITY_REGRESSION: CHATGPT_RETRY'
            progress('CHATGPT_COMPLETED', consultation_id=consultation, logical_retry='ALREADY_SENT', additional_physical_sends=0)
            recovery_started = time.time()
        else:
            report = read(auto / 'reports/runner-result.json') or {}
            gate = read(auto / 'evidence/completion-gate.json') or {}
            roles = read(auto / 'evidence/roles.json') or {}
            save('native-result.json', {'report': report, 'gate': gate, 'roles': roles})
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
            failure = 'BLOCKED_REQUIRES_HUMAN: attempt 3 UNKNOWN_DELIVERY after bridge interruption; NO RESEND; ' + failure
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

report = read(auto / 'reports/runner-result.json') or {}
result = {'status': 'FAIL' if failure or survivors or not all(checks.values()) else 'PASS', 'failure': failure,
          'attempt': 3, 'run_id': run_id, 'checks': checks, 'project': str(project), 'consultation_id': consultation,
          'duration_seconds': report.get('duration_seconds'), 'total_harness_elapsed_seconds': time.monotonic() - start,
          'setup_seconds': clock_started - harness_started_wall if clock_started else None,
          'global_timeout_seconds': GLOBAL_SECONDS, 'RAM_min_available_mib': min((row['ram_available_bytes'] for row in samples), default=0) / 1024**2,
          'pagefile_max_used_gib': max((row['pagefile']['used'] for row in samples), default=0) / 1024**3,
          'VRAM_max_mib': max((int(row['memory_mib'].split(',')[0]) for row in gpu if row['memory_mib']), default=None),
          'new_dependencies': [], 'no_push': True, 'F25_started': False}
save('SUMMARY.json', result)
print(json.dumps(result, ensure_ascii=False), flush=True)
raise SystemExit(0 if result['status'] == 'PASS' else 1)
