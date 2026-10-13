"""Git CLI isolation with contract admission, exact review binding and owned cleanup."""
import argparse, hashlib, json, pathlib, re, subprocess, sys, uuid, zipfile, yaml, jsonschema
ROOT=pathlib.Path(__file__).resolve().parents[1]
def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.STDOUT,timeout=30).decode('utf-8').strip()
def digest(value):return hashlib.sha256(value.encode()).hexdigest()
def admit(project):
    p=pathlib.Path(project).absolute()
    for part in [p,*p.parents]:
        if part.exists() and (part.is_symlink() or part.is_junction()):raise ValueError('REPARSE_POINT_DENIED')
    p=p.resolve();p.relative_to(ROOT/'sandbox')
    contract=p/'.autopilot/RUN-CONTRACT.yaml'
    for part in (contract,contract.parent):
        if part.is_symlink() or part.is_junction():raise ValueError('REPARSE_POINT_DENIED')
    c=yaml.safe_load(contract.read_text(encoding='utf-8-sig'))
    jsonschema.validate(c,json.loads((ROOT/'schemas/run-contract.schema.json').read_text(encoding='utf-8-sig')))
    if not c.get('authorized') or pathlib.Path(c['project_root']).resolve()!=p or 'git_commit_local' not in c['allowed_actions']:raise ValueError('CONTRACT_DENIED')
    if git(p,'rev-parse','--show-toplevel').replace('\\','/').casefold()!=str(p).replace('\\','/').casefold():raise ValueError('NOT_PROJECT_GIT_ROOT')
    return p
def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['create','inspect','integrate','remove']);ap.add_argument('--project',required=True);ap.add_argument('--task',default='task-001');ap.add_argument('--gate');a=ap.parse_args()
    p=admit(a.project)
    if not re.fullmatch(r'task-[a-zA-Z0-9-]{1,64}',a.task):raise ValueError('INVALID_TASK_ID')
    registry=p/'.autopilot/worktrees.json';records=json.loads(registry.read_text()) if registry.exists() else {}
    wt=p/'.autopilot-worktrees'/a.task;branch='agent/'+a.task
    if a.action=='create':
        if a.task in records or wt.exists():raise ValueError('ALREADY_OWNED')
        if git(p,'status','--porcelain','--untracked-files=no'):raise ValueError('PARENT_DIRTY')
        base=git(p,'rev-parse','HEAD');git(p,'worktree','add','-b',branch,str(wt),base)
        records[a.task]={'path':str(wt),'branch':branch,'base':base,'run_id':yaml.safe_load((p/'.autopilot/RUN-CONTRACT.yaml').read_text(encoding='utf-8-sig'))['run_id']}
    else:
        record=records.get(a.task)
        if not record or record['path']!=str(wt):raise ValueError('UNOWNED_WORKTREE')
        # Resolve every existing path before forced Git cleanup.
        for part in [wt,*wt.parents]:
            if part.exists() and (part.is_symlink() or part.is_junction()):raise ValueError('REPARSE_POINT_DENIED')
        wt.resolve().relative_to((p/'.autopilot-worktrees').resolve())
        if a.action=='integrate':
            gate=json.loads(pathlib.Path(a.gate).read_text(encoding='utf-8-sig')) if a.gate else {}
            head=git(wt,'rev-parse','HEAD');diff=git(p,'diff',record['base'],head,'--')
            changed=git(p,'diff','--name-only',record['base'],head).splitlines()
            if any(n.startswith(('.autopilot/','runner/','backups/')) or pathlib.PurePosixPath(n).name in ('security.yaml','RUN-CONTRACT.yaml','VERSIONS.lock') for n in changed):raise ValueError('PROTECTED_PATH_DENIED')
            if gate.get('decision')!='ACCEPTED' or gate.get('completion_gate')!='PASS' or gate.get('tests')!='PASS' or gate.get('reviewed_commit')!=head or gate.get('diff_sha256')!=digest(diff):raise ValueError('REVIEW_GATE_DENIED')
            if git(p,'rev-parse','HEAD')!=record['base'] or git(p,'status','--porcelain','--untracked-files=no') or git(wt,'status','--porcelain','--untracked-files=no'):raise ValueError('STALE_OR_DIRTY_REVIEW')
            git(p,'merge','--ff-only',head)
        elif a.action=='remove':
            # Preserve dirty contents before forced removal, including untracked data.
            if git(wt,'status','--porcelain'):
                files=[f for f in wt.rglob('*') if f.is_file() and f.name!='.git']
                if any(f.is_symlink() or f.is_junction() for f in wt.rglob('*')):raise ValueError('REPARSE_POINT_DENIED')
                if sum(f.stat().st_size for f in files)>52428800:raise ValueError('BACKUP_SIZE_LIMIT')
                archive=ROOT/'backups'/('worktree-'+uuid.uuid4().hex);archive.mkdir()
                with zipfile.ZipFile(archive/'dirty.zip','w',zipfile.ZIP_DEFLATED) as z:
                    for f in files:z.write(f,f.relative_to(wt))
                if not (archive/'dirty.zip').exists():raise ValueError('BACKUP_FAILED')
            git(p,'worktree','remove','--force',str(wt));git(p,'worktree','prune');records.pop(a.task)
    registry.write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','action':a.action,'path':str(wt),'records':records,'worktrees':git(p,'worktree','list','--porcelain')}))
if __name__=='__main__':
    try:main()
    except Exception as e:print(json.dumps({'status':'DENY','reason':str(e)}));sys.exit(1)
