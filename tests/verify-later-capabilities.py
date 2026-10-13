import hashlib,json,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
checks={}
for name in ['scripts/invoke-hermes-role.ps1','scripts/invoke-hermes.ps1','scripts/governed-worktree.py']:
    baseline=subprocess.check_output(['git','show','8b2b175:'+name],cwd=ROOT)
    checks[name+'_unchanged']=baseline.replace(b'\r\n',b'\n')==(ROOT/name).read_bytes().replace(b'\r\n',b'\n')
project=ROOT/'sandbox/phase7a6-worktrees'
checks['worktree_registry_empty']=json.loads((project/'.autopilot/worktrees.json').read_text())=={}
listing=subprocess.check_output(['git','-C',str(project),'worktree','list','--porcelain'],text=True)
checks['worktree_only_parent']=listing.count('worktree ')==1
checks['worktree_directory_removed']=not(project/'.autopilot-worktrees/task-001').exists()
checks['role_gate_pass']=json.loads((ROOT/'evidence/phase-7a5/deterministic-gate.json').read_text())['status']=='PASS'
result={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks}
(ROOT/sys.argv[1]).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert all(checks.values())
