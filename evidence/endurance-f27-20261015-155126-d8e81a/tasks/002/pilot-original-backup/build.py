import ast,json,pathlib,subprocess,sys
ast.parse(pathlib.Path('module.py').read_text(encoding='utf-8'))
data=pathlib.Path('sample-records.json').read_text(encoding='utf-8')
for args,name in [([], 'artifact-report.json'),(['--markdown'],'REPORT.md')]:
 p=subprocess.run([sys.executable,'module.py',*args],input=data,text=True,capture_output=True)
 assert p.returncode==0,p.stderr
 if not args:json.loads(p.stdout)
 pathlib.Path(name).write_text(p.stdout,encoding='utf-8')
print('ENDURANCE_BUILD_PASS')
