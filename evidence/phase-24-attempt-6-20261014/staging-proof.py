import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[2];E=pathlib.Path(__file__).resolve().parent
manifest=json.loads((E/'capture-manifest.json').read_text(encoding='utf-8'))['copies'];bad=[]
for source,record in manifest.items():
 path=E.relative_to(R).as_posix()+'/'+record['copy']
 r=subprocess.run(['git','show',':'+path],cwd=R,capture_output=True)
 if r.returncode or hashlib.sha256(r.stdout).hexdigest()!=record['sha256']:bad.append(path)
(E/'staging-integrity.json').write_text(json.dumps({'status':'PASS' if not bad else 'FAIL','native_copies':len(manifest),'mismatches':bad},indent=2)+'\n',encoding='utf-8')
assert not bad,bad
print('STAGED RAW COPY PROOF PASS '+str(len(manifest)))
