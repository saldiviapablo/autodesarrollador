"""Offline canary simulation against a complete archive of the frozen Hermes tree."""
import hashlib,json,pathlib,runpy,subprocess,uuid,zipfile
import yaml
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def smoke(candidate):
    security=runpy.run_path(str(candidate/'tools/path_security.py'))
    checks={'native_inside_path_allow':security['validate_within_dir'](candidate/'tools/x',candidate/'tools') is None,
            'native_escape_path_deny':bool(security['validate_within_dir'](candidate/'outside',candidate/'tools')),
            'native_traversal_detected':security['has_traversal_component']('../x'),
            'native_control_character_denied':security['has_unsafe_path_chars']('evil\nfile')}
    # Compile actual core entrypoints without starting processes or inference.
    for name in ['run_agent.py','tools/read_extract.py','tools/delegate_tool.py','hermes_cli/web_server.py','gateway/platforms/webhook.py']:
        try:compile((candidate/name).read_bytes(),str(candidate/name),'exec');checks[name]=True
        except (SyntaxError,OSError):checks[name]=False
    return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks}
def simulation():
    cfg=yaml.safe_load((ROOT/'config/system.yaml').read_text(encoding='utf-8-sig'))
    native=pathlib.Path(cfg['document_extraction']['native_source_dir']).resolve()
    commit=subprocess.check_output(['git','-C',str(native),'rev-parse','HEAD'],text=True).strip()
    if commit!=cfg['hermes']['commit'] or subprocess.check_output(['git','-C',str(native),'status','--porcelain'],text=True):raise ValueError('FROZEN_SOURCE_NOT_CLEAN')
    protected=[ROOT/'config/VERSIONS.lock',ROOT/'config/security.yaml',ROOT/'scripts/inference-lock.ps1',ROOT/'scripts/hermes-pre-tool-hook.py',native/'tools/path_security.py',native/'tools/read_extract.py',native/'tools/browser_tool.py',native/'install-stamp.json']
    before={str(p):sha(p) for p in protected}
    area=ROOT/'sandbox/canary-update';area.mkdir(exist_ok=True)
    backup=ROOT/'backups'/('controlled-update-'+uuid.uuid4().hex);backup.mkdir()
    archive=backup/'frozen-hermes.zip'
    subprocess.run(['git','-C',str(native),'archive','--format=zip','-o',str(archive),commit],check=True,timeout=60)
    manifest={'simulation':True,'trusted_origin':'installed official NousResearch/hermes-agent frozen Git checkout','frozen_commit':commit,'archive_sha256':sha(archive),'protected_hashes':before}
    originals=backup/'protected';originals.mkdir()
    for i,p in enumerate(protected):
        copy=originals/(str(i)+'-'+p.name);copy.write_bytes(p.read_bytes())
        if sha(copy)!=before[str(p)]:raise ValueError('BACKUP_VERIFICATION_FAILED')
    (backup/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    candidate=area/('candidate-'+uuid.uuid4().hex);candidate.mkdir()
    candidate.resolve().relative_to(area.resolve())
    pointer=area/'SIMULATED-ACTIVE.json';pointer_before=None
    try:
        with zipfile.ZipFile(archive) as z:
            if sum(i.file_size for i in z.infolist())>536870912:raise ValueError('ARCHIVE_SIZE_LIMIT')
            for i in z.infolist():
                (candidate/i.filename).resolve().relative_to(candidate.resolve())
                if (i.external_attr>>16)&0o170000==0o120000:raise ValueError('ARCHIVE_SYMLINK_DENIED')
            z.extractall(candidate)
        first=smoke(candidate)
        if first['status']!='PASS':raise ValueError('CANDIDATE_MANDATORY_SMOKE_FAILED')
        # Promotion is only a sandbox marker: live installation and VERSIONS.lock cannot change.
        frozen={'version':'0.21.6','commit':commit,'simulation':True}
        pointer.write_text(json.dumps(frozen))
        pointer_before=pointer.read_bytes();(backup/'SIMULATED-ACTIVE.json').write_bytes(pointer_before)
        pointer.write_text(json.dumps({'version':'0.21.6-simulated-candidate','candidate':candidate.name,'simulation':True}))
        promoted=json.loads(pointer.read_text())['version']=='0.21.6-simulated-candidate'
        # Inject a real policy regression into the candidate's native path guard.
        module=candidate/'tools/path_security.py'
        module.write_text(module.read_text(encoding='utf-8')+'\n# Canary regression injection\ndef validate_within_dir(path, root):\n    return None\n',encoding='utf-8')
        failed=smoke(candidate)
        if failed['status']=='PASS':raise ValueError('REGRESSION_NOT_DETECTED')
        pointer.write_bytes(pointer_before)
        rollback=pointer.read_bytes()==pointer_before
        after={str(p):sha(p) for p in protected}
        if before!=after or not rollback:raise ValueError('PRODUCTION_INTEGRITY_OR_ROLLBACK_FAILED')
        pointer.unlink()
        return {'status':'PASS','tests':{'T-7A-UPDATE-001':'PASS','T-7A-UPDATE-002':'PASS'},'candidate_smoke':first,'injected_regression_smoke':failed,'simulated_promotion_after_smoke':promoted,'automatic_rollback':rollback,'production_hashes_unchanged':True,'live_hermes_commit':commit,'live_version':'0.21.6','versions_lock_unchanged':True,'backup':str(backup),'archive_sha256':manifest['archive_sha256'],'new_dependencies':[],'actual_update_executed':False,'local_inferences':0}
    finally:
        if pointer.exists():
            if pointer_before is not None:pointer.write_bytes(pointer_before)
            pointer.unlink()
        # Recoverable cleanup: archive candidate tree; both targets are verified within workspace.
        candidate.resolve().relative_to(ROOT.resolve());target=backup/'tested-candidate';target.resolve().relative_to(ROOT.resolve())
        if candidate.exists():candidate.rename(target)
if __name__=='__main__':print(json.dumps(simulation(),indent=2))
