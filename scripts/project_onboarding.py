"""Launcher data adapter. Contracts are made exclusively by canonical Prepare.

Mutating actions are called under the production RunMutex by launcher-action.ps1.
No agent calls, command execution from briefs, approval or Runner start live here.
"""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import re
import onboarding_planner as compact_planner
import onboarding_fastpath

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runner'))
import contract
import prepare
import write_scope

spec = importlib.util.spec_from_file_location('onboarding_secret', ROOT / 'scripts/hermes-pre-tool-hook.py')
secret = importlib.util.module_from_spec(spec)
spec.loader.exec_module(secret)
TERMINAL = {'COMPLETED', 'FAILED', 'ABORTED', 'STALLED', 'BLOCKED_REQUIRES_HUMAN', 'STOPPED'}
EXCLUDES = {'.git', '.autopilot', '.autopilot-history', 'node_modules', '.venv', 'venv', '__pycache__'}
MUTATION_CONTEXT={}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def safe_text(text):
    if not isinstance(text, str) or not text.strip() or '\x00' in text:
        raise ValueError('EMPTY_OR_INVALID_TEXT')
    if len(text.encode('utf-8', errors='strict')) > 200000:
        raise ValueError('BRIEF_TOO_LARGE_200KB')
    if secret.sanitize_text(text)[0] != text:
        raise ValueError('SECRET_DETECTED_REMOVE_SECRETS_BEFORE_CONTINUING')
    return text


def project(value):
    p = contract.project_path(value)
    for name in ('SystemRoot','WINDIR','ProgramFiles','ProgramFiles(x86)','ProgramData','LOCALAPPDATA','APPDATA'):
        value=os.environ.get(name)
        if value and p.is_relative_to(contract.check_path(value)):
            raise ValueError('SYSTEM_DIRECTORY_NOT_A_MANAGED_PROJECT')
    # Do not admit the infrastructure, one of its parents, or its implementation
    # directories as a managed project. Only disposable sandboxes are internal.
    if ROOT.is_relative_to(p) or (p.is_relative_to(ROOT) and not p.is_relative_to(ROOT / 'sandbox')):
        raise ValueError('INFRASTRUCTURE_PROJECT_OVERLAP_DENIED')
    if p == ROOT / 'sandbox':
        raise ValueError('SANDBOX_CONTAINER_IS_NOT_A_PROJECT')
    policy = contract.yaml.safe_load((ROOT / 'config/security.yaml').read_text(encoding='utf-8-sig'))
    if any(contract.check_path(v).is_relative_to(p) for v in policy['protected_paths']):
        raise ValueError('PROTECTED_DESCENDANT_DENIED')
    for name in prepare.DESTINATIONS + ['.git', '.gitignore', '.autopilot-history']:
        contract.check_path(p / name).relative_to(p)
    return p


def files(p):
    found = []
    for current, dirs, names in os.walk(p, followlinks=False):
        dirs[:] = sorted(n for n in dirs if n not in EXCLUDES)
        for n in dirs + names:
            contract.check_path(Path(current) / n).relative_to(p)
        for n in sorted(names):
            path = Path(current) / n
            if path.stat().st_size > 2_000_000:
                raise ValueError('PROJECT_FILE_TOO_LARGE_FOR_PREFLIGHT:' + str(path.relative_to(p)))
            found.append(path)
            if len(found) > 3000:
                raise ValueError('PROJECT_INVENTORY_LIMIT_REQUIRES_SCOPED_PREFLIGHT')
    return found


def git(p, *args, check=True):
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0')
    r = subprocess.run(['git', '-C', str(p), '-c', 'core.quotepath=false', *args], capture_output=True,
                       text=True, encoding='utf-8', errors='strict', timeout=30, env=env)
    if check and r.returncode:
        raise ValueError('GIT_OPERATION_FAILED:' + args[0])
    return r


def git_root(p):
    r = git(p, 'rev-parse', '--show-toplevel', check=False)
    if r.returncode:
        return None
    root = contract.check_path(r.stdout.strip())
    if root != p:
        # An empty test sandbox may inherit the infrastructure Git. It gets a
        # separate repository; any other parent repo is preserved and denied.
        if root == ROOT and p.is_relative_to(ROOT / 'sandbox'):
            return None
        raise ValueError('PARENT_GIT_REPOSITORY_DENIED')
    if not (p / '.git').is_dir():
        raise ValueError('GIT_WORKTREE_REQUIRES_EXISTING_GOVERNED_WORKTREE_FLOW')
    contract.check_path(p / '.git')
    return root


def snapshot(p):
    return {str(f.relative_to(p)).replace('\\', '/'): contract.sha(f) for f in files(p)}


def policy_hashes():
    """Bind the human plan review to the actual preparer, policies and launch code."""
    paths=list((ROOT/'runner').glob('*.py'))+list((ROOT/'runner').glob('*.ps1'))
    paths += [ROOT/n for n in ['config/system.yaml','config/security.yaml','config/VERSIONS.lock',
        'config/onboarding-planner.json','scripts/onboarding_planner.py','scripts/onboarding_fastpath.py','scripts/onboarding_hermes.py','scripts/onboarding-hermes.ps1','scripts/onboarding-repair.ps1',
        'schemas/run-contract.schema.json','schemas/runner-plan.schema.json','schemas/autopilot-state.schema.json',
        'scripts/init-autopilot-project.ps1','scripts/state-manager.ps1','scripts/canonical_path.py',
        'scripts/security-guard.ps1','scripts/inference-lock.ps1','scripts/hermes-pre-tool-hook.py',
        'scripts/invoke-hermes-role.ps1','scripts/invoke-hermes.ps1','scripts/invoke-qwen-code.ps1',
        'scripts/invoke-delegation.ps1','scripts/project_onboarding.py','scripts/project_launcher_ui.py',
        'scripts/project-launcher-action.ps1','scripts/project-launcher-common.ps1','templates/QWEN.md.template']]
    return {str(p.relative_to(ROOT)).replace('\\','/'):contract.sha(contract.check_path(p)) for p in sorted(set(paths))}


def validate_binding(request):
    p=project(request['project'])
    validate_proposal(p,request['objective'],request['proposal'])
    scope={k:request[k] for k in ('project','objective','proposal','project_snapshot','policy_hashes')}
    if str(p)!=request['project'] or digest(scope)!=request['binding']:
        raise ValueError('PROPOSAL_BINDING_CHANGED')
    if policy_hashes()!=request['policy_hashes']:
        raise ValueError('PREPARATION_POLICY_CHANGED_REVIEW_AGAIN')
    if snapshot(p)!=request['project_snapshot']:
        raise ValueError('PROJECT_CHANGED_SINCE_PREFLIGHT')
    return p


def approve_plan(request):
    """Persist an explicit human decision. This action never starts any process."""
    if os.environ.get('DA_LAUNCHER_MUTEX_HELD')!='1': raise ValueError('RUN_MUTEX_REQUIRED')
    validate_binding(request)
    if request.get('decision')!='APPROVE' or request.get('method')!='HUMAN_PLAN_REVIEW':
        raise ValueError('EXPLICIT_HUMAN_PLAN_REVIEW_REQUIRED')
    approval_id=uuid.uuid4().hex
    directory=contract.check_path(ROOT/'runtime/project-launcher/plan-approvals')
    directory.mkdir(parents=True,exist_ok=True)
    receipt={'approval_id':approval_id,'binding':request['binding'],'project':request['project'],
             'decision':'APPROVE','method':'HUMAN_PLAN_REVIEW','approved_at':datetime.datetime.now().astimezone().isoformat()}
    with (directory/(approval_id+'.json')).open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False)
    return {'status':'PASS',**receipt}


def consume_plan_approval(request):
    approval_id=request.get('approval_id','')
    if not re.fullmatch('[a-f0-9]{32}',approval_id): raise ValueError('HUMAN_PLAN_APPROVAL_REQUIRED')
    directory=contract.check_path(ROOT/'runtime/project-launcher/plan-approvals')
    receipt=read(contract.check_path(directory/(approval_id+'.json')))
    if (receipt['binding']!=request['binding'] or receipt['project']!=request['project']
            or receipt['decision']!='APPROVE' or receipt['method']!='HUMAN_PLAN_REVIEW'):
        raise ValueError('HUMAN_APPROVAL_BINDING_MISMATCH')
    with (directory/(approval_id+'.consumed.json')).open('x',encoding='utf-8') as f:
        json.dump({'binding':request['binding'],'consumed_at':datetime.datetime.now().astimezone().isoformat()},f)
    return receipt


def inspect(value):
    p = project(value)
    own_git = git_root(p)
    result = {'status': 'PASS', 'project': str(p), 'prepared': False, 'git': bool(own_git)}
    cp = p / '.autopilot/RUN-CONTRACT.yaml'
    if cp.exists():
        info = contract.inspect(p)
        state = read(p / '.autopilot/STATE.json')
        contract.jsonschema.validate(state, read(ROOT / 'schemas/autopilot-state.schema.json'))
        if state['run_id'] != info['contract']['run_id']:
            raise ValueError('STATE_RUN_ID_MISMATCH')
        clock_path = ROOT / 'runtime/run-clocks' / Path(info['receipt_path']).name
        clock = read(clock_path) if clock_path.exists() else None
        cfg = contract.yaml.safe_load((ROOT / 'config/system.yaml').read_text(encoding='utf-8-sig'))
        limit = min(info['contract']['time_budget_minutes'] * 60, cfg['runner']['global_timeout_minutes'] * 60,
                    info['plan'].get('global_timeout_seconds', 28800))
        elapsed = 0
        if clock:
            if clock['run_id'] != state['run_id']:
                raise ValueError('RUN_CLOCK_ID_MISMATCH')
            elapsed = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(clock['started_at'])).total_seconds()
            if elapsed < 0:
                raise ValueError('INVALID_RUN_CLOCK')
        result.update(prepared=True, run_id=state['run_id'], state=state, admission=info,
                      elapsed_seconds=elapsed, remaining_seconds=max(0, limit-elapsed),
                      can_continue=state['status'] != 'COMPLETED' and elapsed < limit,
                      clock=clock, restarts=read(p / '.autopilot/RESTARTS.json') if (p / '.autopilot/RESTARTS.json').exists() else {},
                      lock=read(p / '.autopilot/LOCK.json') if (p / '.autopilot/LOCK.json').exists() else None)
    elif (p / '.autopilot').exists():
        raise ValueError('INCOMPLETE_PREPARATION_PRESERVED_REQUIRES_INSPECTION')
    return result


def validate_proposal(p, objective, proposal):
    safe_text(objective)
    if set(proposal) not in ({'plan', 'seed_files'},{'plan','seed_files','overview'}):
        raise ValueError('INVALID_PLANNER_ENVELOPE')
    if 'overview' in proposal:compact_planner.validate(proposal)
    plan = proposal['plan']
    if plan.get('backend', 'live') != 'live' or plan.get('sandbox_crash_boundary') or plan.get('consultation'):
        raise ValueError('NEW_PROJECT_PLAN_REQUIRES_LIVE_NO_IMPLICIT_CONSULTATION')
    criteria = [c['criterion'] for c in plan['criteria']]
    contract.validate_plan(p, plan, criteria)
    for name,cap in [('global_timeout_seconds',2700),('phase_timeout_seconds',300),('max_cycles',5),('restart_budget',2)]:
        if name not in plan or plan[name]>cap:
            raise ValueError('ONBOARDING_BUDGET_NOT_ADMITTED:'+name)
    safe_text(json.dumps(proposal, ensure_ascii=False))
    if not plan.get('builds') and not plan.get('no_build_reason'):
        raise ValueError('BUILD_OR_EXPLICIT_NO_BUILD_REASON_REQUIRED')
    seeds = proposal['seed_files']
    if not isinstance(seeds, dict):
        raise ValueError('SEED_FILES_OBJECT_REQUIRED')
    pins = {x['path']: x['sha256'] for x in plan.get('immutable_files', [])}
    for name, content in seeds.items():
        path = contract.check_path(p / name)
        path.relative_to(p)
        if name not in pins or name in plan['allowed_files'] or path.exists():
            raise ValueError('ONLY_NEW_IMMUTABLE_ACCEPTANCE_FILES_MAY_BE_SEEDED')
        if hashlib.sha256(content.encode('utf-8')).hexdigest() != pins[name]:
            raise ValueError('SEED_HASH_MISMATCH')
    for name, expected in pins.items():
        if name in plan['allowed_files']:
            raise ValueError('IMMUTABLE_FILE_IN_WORKER_ALLOWLIST')
        if name not in seeds and contract.sha(contract.check_path(p / name)) != expected:
            raise ValueError('EXISTING_ACCEPTANCE_HASH_MISMATCH')
    if not pins:
        raise ValueError('INDEPENDENT_IMMUTABLE_ACCEPTANCE_REQUIRED')
    for name in plan['allowed_files'] + list(seeds):
        if Path(name).parts[0].casefold() in {'.git', '.autopilot-history'} or name == 'QWEN.md':
            raise ValueError('METADATA_NOT_WORKER_OUTPUT')
    for command in plan['tests'] + plan.get('builds', []) + plan.get('linters', []):
        if command['argv'][0] not in compact_planner.ONBOARDING_EXECUTABLES:
            raise ValueError('CHECK_EXECUTABLE_NOT_ADMITTED')
    return criteria


def bind_proposal(value, objective, proposal):
    p = project(value)
    # Hashes are calculated deterministically, never trusted from the model.
    proposal = json.loads(json.dumps(proposal))
    seeds = proposal['seed_files']
    pins = {v['path']: v for v in proposal['plan'].get('immutable_files', [])}
    for name, content in seeds.items():
        pins[name] = {'path': name, 'sha256': hashlib.sha256(content.encode('utf-8')).hexdigest()}
    proposal['plan']['immutable_files'] = list(pins.values())
    validate_proposal(p, objective, proposal)
    scope={'proposal':proposal,'project':str(p),'objective':objective,'project_snapshot':snapshot(p),'policy_hashes':policy_hashes()}
    return {'status':'PASS',**scope,'binding':digest(scope)}


def draft_path(p,objective):
    project_key=hashlib.sha256(str(p).casefold().encode()).hexdigest()
    objective_key=hashlib.sha256(objective.encode('utf-8')).hexdigest()
    return contract.check_path(ROOT/'runtime/project-launcher/drafts'/project_key/(objective_key+'.json'))


def cache_draft(bound):
    p=validate_binding(bound)
    path=draft_path(p,bound['objective']);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(uuid.uuid4().hex+'.tmp')
    with temporary.open('x',encoding='utf-8') as f:json.dump(bound,f,ensure_ascii=False,indent=2)
    os.replace(temporary,path)
    return {'status':'PASS','path':str(path),'approved':False}


def cached_draft(value,objective):
    p=project(value);safe_text(objective);path=draft_path(p,objective)
    if not path.exists():return None
    try:
        bound=read(path);validate_binding(bound)
        if bound['project']!=str(p) or bound['objective']!=objective:return None
        return bound
    except (OSError,ValueError,KeyError,TypeError):return None


def archive(p, info):
    """Move only exact, verified operational paths, never delete run history."""
    if not info['prepared']:
        return None
    if info['state']['status'] not in TERMINAL | {'INITIALIZED', 'READY'}:
        raise ValueError('INTERRUPTED_RUN_REQUIRES_RECOVERY_BEFORE_NEW_OBJECTIVE')
    destination = contract.check_path(p / '.autopilot-history' / info['run_id'])
    destination.relative_to(p / '.autopilot-history')
    if destination.exists():
        raise ValueError('HISTORY_DESTINATION_EXISTS')
    manifest = {}
    auto = p / '.autopilot'
    for current, dirs, names in os.walk(auto, followlinks=False):
        for name in dirs + names:
            contract.check_path(Path(current) / name).relative_to(auto)
        for name in names:
            path = Path(current) / name
            manifest[str(path.relative_to(p)).replace('\\', '/')] = contract.sha(path)
    if (p / 'QWEN.md').exists():
        manifest['QWEN.md'] = contract.sha(p / 'QWEN.md')
    destination.mkdir(parents=True)
    (destination / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    for name in ['.autopilot', 'QWEN.md']:
        source = contract.check_path(p / name)
        if source.exists():
            source.rename(destination / name)
    if any(contract.sha(destination / name) != expected for name, expected in manifest.items()):
        raise ValueError('HISTORY_VERIFICATION_FAILED_STOP')
    return str(destination)


def prepare_project(request):
    if os.environ.get('DA_LAUNCHER_MUTEX_HELD') != '1':
        raise ValueError('RUN_MUTEX_REQUIRED')
    p = project(request['project'])
    info = inspect(p)
    proposal = request['proposal']
    criteria = validate_proposal(p, request['objective'], proposal)
    validate_binding(request)
    if info['prepared'] and not request.get('new_objective'):
        raise ValueError('EXISTING_RUN_PRESERVED')
    imported_qwen=None
    if not info['prepared'] and (p/'QWEN.md').exists():
        safe_text((p/'QWEN.md').read_text(encoding='utf-8-sig'))
        imported_qwen={'sha256':contract.sha(p/'QWEN.md')}
    if info['git'] and git(p, 'diff', '--cached', '--name-only').stdout.strip():
        raise ValueError('STAGED_USER_CHANGES_PRESERVED')
    # Before any write, inspect every file and secret in a prospective new repo.
    baseline = files(p)
    if not info['git']:
        for f in baseline:
            if f.suffix.lower() in {'.key', '.pem', '.token', '.secret'} or f.name.startswith('.env'):
                raise ValueError('SENSITIVE_BASELINE_FILE_DENIED')
            try:
                safe_text(f.read_text(encoding='utf-8-sig')) if f.stat().st_size else None
            except UnicodeError:
                raise ValueError('NON_TEXT_BASELINE_REQUIRES_EXISTING_GIT') from None
    approval=consume_plan_approval(request)
    history = archive(p, info)
    if imported_qwen is not None:
        imported=contract.check_path(p/'.autopilot-history'/('import-'+uuid.uuid4().hex))
        imported.mkdir(parents=True)
        (p/'QWEN.md').rename(imported/'QWEN.md')
        (imported/'MANIFEST.json').write_text(json.dumps({'QWEN.md':imported_qwen['sha256']},indent=2),encoding='utf-8')
        imported_qwen['directory']=str(imported)
    operation = ROOT / 'runtime/project-launcher' / uuid.uuid4().hex
    contract.check_path(operation)
    operation.mkdir(parents=True)
    source = operation / 'plan.json'
    source.write_text(json.dumps(proposal['plan'], ensure_ascii=False), encoding='utf-8')
    result = prepare.execute({'project': str(p), 'objective': request['objective'], 'criteria': criteria, 'plan': str(source)})
    if result['status'] != 'PASS':
        if imported_qwen is not None and not (p/'QWEN.md').exists():
            with (p/'QWEN.md').open('xb') as f:f.write((Path(imported_qwen['directory'])/'QWEN.md').read_bytes())
        # Old bytes remain in the archive; do not overwrite a partial Prepare.
        return dict(result, history=history)
    MUTATION_CONTEXT.update(preparation_applied=True,project=str(p),run_id=result['run_id'])
    if imported_qwen is not None:
        # Preserve both the canonical generated guide and the user's existing
        # guide. Never overwrite either; the Worker sees the unchanged original.
        (p/'QWEN.md').rename(p/'.autopilot/evidence/PREPARE-QWEN.md')
        with (p/'QWEN.md').open('xb') as f:f.write((Path(imported_qwen['directory'])/'QWEN.md').read_bytes())
        if contract.sha(p/'QWEN.md')!=imported_qwen['sha256']:raise ValueError('IMPORTED_QWEN_INTEGRITY_FAILED')
    for name, content in proposal['seed_files'].items():
        path = contract.check_path(p / name)
        path.relative_to(p)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8', newline='') as stream:
            stream.write(content)
    auto = p / '.autopilot'
    final=contract.inspect(p)
    actual=final['contract']
    if (final['plan']!=proposal['plan'] or actual['objective']!=request['objective'] or actual['acceptance_criteria']!=criteria
            or actual['autonomy_mode']!='unattended' or actual['time_budget_minutes']!=120
            or actual['allowed_actions']!=['edit_file','run_test','git_commit_local']
            or actual['forbidden_actions']!=['git_push','delete_root','modify_runner_guardrails']
            or actual['authorized']):
        raise ValueError('GENERATED_CONTRACT_DIFFERS_FROM_HUMAN_REVIEW')
    (auto/'evidence/ONBOARDING-APPROVAL.json').write_text(json.dumps(approval,ensure_ascii=False,indent=2),encoding='utf-8')
    if 'overview' in proposal:
        (auto/'evidence/ONBOARDING-OVERVIEW.json').write_text(json.dumps(proposal['overview'],ensure_ascii=False,indent=2),encoding='utf-8')
        (auto/'evidence/ONBOARDING-OBJECTIVE.md').write_bytes(request['objective'].encode('utf-8'))
    (auto / 'evidence/ONBOARDING.json').write_text(json.dumps({'binding': request['binding'], 'history': history,
        'source': 'CANONICAL_PREPARE', 'approval': 'HUMAN_PLAN_REVIEW_RECORDED', 'imported_qwen':imported_qwen,'objective_sha256': hashlib.sha256(request['objective'].encode()).hexdigest()}, indent=2), encoding='utf-8')
    return dict(result, history=history, operation=str(operation), git_initialization_required=not info['git'],approval_id=approval['approval_id'])


def initialize_git(value):
    if os.environ.get('DA_LAUNCHER_MUTEX_HELD') != '1':
        raise ValueError('RUN_MUTEX_REQUIRED')
    p = project(value)
    own = git_root(p)
    if own and git(p, 'diff', '--cached', '--name-only').stdout.strip():
        raise ValueError('STAGED_USER_CHANGES_PRESERVED')
    if not own:
        git(p, 'init', '-q')
        git(p, 'config', 'user.name', 'Desarrollador Autonomo')
        git(p, 'config', 'user.email', 'local@desarrollador-autonomo.invalid')
    # Local exclusions only; never change an existing project's ignore rules.
    exclude = contract.check_path(p / '.git/info/exclude')
    exclude.parent.mkdir(exist_ok=True)
    original = exclude.read_text(encoding='utf-8') if exclude.exists() else ''
    additions = [n for n in ['/.autopilot/', '/.autopilot-history/', '/.qwen/', '__pycache__/', '*.pyc'] if n not in original.splitlines()]
    if additions:
        with exclude.open('a', encoding='utf-8') as f:
            f.write('\n' + '\n'.join(additions) + '\n')
    plan = read(p / '.autopilot/RUN-PLAN.json')
    names = ['QWEN.md'] + [x['path'] for x in plan.get('immutable_files', [])]
    if not own:
        names = [str(f.relative_to(p)) for f in files(p)]
    for name in names:
        f = contract.check_path(p / name)
        f.relative_to(p)
        if f.is_file():
            content = f.read_text(encoding='utf-8-sig')
            if content.strip(): safe_text(content)
    git(p, 'add', '--', *names)
    if git(p, 'diff', '--cached', '--name-only').stdout.strip():
        git(p, 'commit', '-q', '-m', 'chore: prepare project baseline')
    if git(p, 'rev-parse', '--verify', 'HEAD', check=False).returncode:
        raise ValueError('GIT_BASELINE_REQUIRED')
    return {'status': 'PASS', 'git_head': git(p, 'rev-parse', 'HEAD').stdout.strip()}


def main(r):
    action = r['action']
    if action == 'planner_audit':
        p=project(r['project']);value=r['result'];safe_text(json.dumps(value,ensure_ascii=False))
        directory=contract.check_path(ROOT/'runtime/project-launcher/planner-results');directory.mkdir(parents=True,exist_ok=True)
        path=directory/(uuid.uuid4().hex+'.json')
        path.write_text(json.dumps({'project':str(p),'native_result':value},ensure_ascii=False,indent=2),encoding='utf-8')
        return {'status':'PASS','path':str(path)}
    if action == 'planner_runtime':
        cfg=contract.yaml.safe_load((ROOT/'config/system.yaml').read_text(encoding='utf-8-sig'))
        home=contract.check_path(Path(cfg['hermes']['profile_dir']).parent/cfg['bot_roles']['supervisor_profile'])
        profile=home/'config.yaml';approved=ROOT/'config/hermes-supervisor/config.yaml'
        if contract.sha(profile)!=contract.sha(approved):raise ValueError('ROLE_PROFILE_INTEGRITY_MISMATCH')
        v=contract.yaml.safe_load(profile.read_text(encoding='utf-8-sig'))
        if v['platform_toolsets']['cli'] or v['plugins']['enabled'] or v['mcp_servers'] or v['hooks_auto_accept']:
            raise ValueError('ROLE_READONLY_POLICY_MISMATCH')
        return {'status':'PASS','profile_home':str(home),'disabled_toolsets':v['agent']['disabled_toolsets'],'profile_sha256':contract.sha(profile)}
    if action == 'inspect': return inspect(r['project'])
    if action == 'planner_context':
        p = project(r['project'])
        objective = safe_text(r['objective'])
        source_dir=contract.check_path(ROOT/'runtime/project-launcher/planner-sources'/hashlib.sha256(str(p).casefold().encode()).hexdigest())
        source_dir.mkdir(parents=True,exist_ok=True)
        source_hash=hashlib.sha256(objective.encode('utf-8')).hexdigest();source_path=source_dir/(source_hash+'.md')
        if source_path.exists():
            if source_path.read_bytes()!=objective.encode('utf-8'):raise ValueError('PLANNER_ORIGINAL_SOURCE_HASH_MISMATCH')
        else:
            with source_path.open('xb') as f:f.write(objective.encode('utf-8'))
        context = []
        remaining = 45000
        for f in files(p):
            name = str(f.relative_to(p)).replace('\\', '/')
            if f.name.startswith('.env') or f.suffix.lower() in {'.pem', '.key', '.token', '.secret'}:
                continue
            try: content = f.read_text(encoding='utf-8-sig')
            except UnicodeError: continue
            clean = secret.sanitize_text(content)[0]
            if remaining > 0:
                context.append({'path': name, 'sha256': contract.sha(f), 'content': clean[:min(8000, remaining)]})
                remaining -= len(context[-1]['content'])
        # The complete local schema is still validated by contract.validate_plan.
        # Give the model only the relevant shape, rather than every unrelated
        # bridge/crash/probe option, to keep a cold-start preflight bounded.
        shape={'plan':{'schema_version':'1.0','backend':'live','task':'approved task',
            'allowed_files':['product.py','README.md'],
            'write_scope':['src/**'],
            'tests':[{'id':'acceptance','argv':['python','test_acceptance.py'],'marker':'ACCEPTANCE_PASS','timeout_seconds':60}],
            'builds':[{'id':'build','argv':['python','build_check.py'],'marker':'BUILD_PASS','timeout_seconds':60}],
            'criteria':[{'criterion':'specific acceptance criterion','test_id':'acceptance'}],
            'artifacts':[{'path':'product.py','min_bytes':1}],
            'immutable_files':[{'path':'test_acceptance.py','sha256':'0'*64},{'path':'build_check.py','sha256':'0'*64}],
            'phase_timeout_seconds':300,'global_timeout_seconds':2700,'max_cycles':5,'restart_budget':2},
            'seed_files':{'test_acceptance.py':'acceptance test source','build_check.py':'build verifier source'}}
        prompt=compact_planner.prompt(shape,objective,context)
        return {'status':'PASS','prompt':prompt,'snapshot':snapshot(p),'read_only':True,'planner_policy':compact_planner.policy(),
                'planner_schema':compact_planner.planner_schema(),'source_path':str(source_path),
                'objective_sha256':hashlib.sha256(objective.encode('utf-8')).hexdigest(),'objective_utf8_bytes':len(objective.encode('utf-8'))}
    if action == 'brief':
        f = contract.check_path(r['path'])
        if f.suffix.lower() not in {'.md', '.txt'} or f.stat().st_size > 200000:
            raise ValueError('BRIEF_MD_TXT_UTF8_MAX_200KB_REQUIRED')
        return {'status': 'PASS', 'text': safe_text(f.read_bytes().decode('utf-8-sig', errors='strict'))}
    if action == 'fast_proposal':
        p=project(r['project'])
        objective=safe_text(r['objective'])
        if not onboarding_fastpath.supports(objective):
            return {'status':'UNSUPPORTED'}
        proposed=onboarding_fastpath.compile_proposal(objective,p)
        return {'status':'PASS','bound':bind_proposal(str(p),objective,proposed)}
    if action == 'proposal': return bind_proposal(r['project'], r['objective'], r['proposal'])
    if action == 'planner_proposal': return bind_proposal(r['project'],r['objective'],compact_planner.decode(r['text'],r['objective']))
    if action == 'approve_plan': return approve_plan(r)
    if action == 'cache_draft': return cache_draft(r)
    if action == 'prepare': return prepare_project(r)
    if action == 'git': return initialize_git(r['project'])
    raise ValueError('UNKNOWN_ACTION')


if __name__ == '__main__':
    try:
        print(json.dumps(main(json.loads(sys.stdin.buffer.read().decode('utf-8-sig'))), ensure_ascii=False))
    except Exception as exc:
        message = secret.sanitize_text(str(exc))[0]
        print(json.dumps({'status': 'DENY', 'reason': message,**MUTATION_CONTEXT}, ensure_ascii=False))
        sys.exit(2)
