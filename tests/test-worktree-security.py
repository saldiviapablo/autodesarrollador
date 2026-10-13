import importlib.util,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
script=ROOT/'scripts/governed-worktree.py'
project=ROOT/'sandbox/phase7a6-worktrees'
cases=[('outside_workspace',['create','--project',str(ROOT.parent)]),('task_traversal',['create','--project',str(project),'--task','../escape']),('unowned_cleanup',['remove','--project',str(project),'--task','task-unowned'])]
results={}
for name,args in cases:
    p=subprocess.run(['C:/Python314/python.exe',str(script),*args],capture_output=True,text=True,timeout=40)
    data=json.loads(p.stdout);results[name]={'status':'PASS' if p.returncode and data['status']=='DENY' else 'FAIL','reason':data['reason']}
result={'status':'PASS' if all(v['status']=='PASS' for v in results.values()) else 'FAIL','cases':results}
(ROOT/'evidence/phase-7a6/security.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['status']=='PASS'
