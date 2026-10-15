"""Use the existing sanitizer; ignore only proven JSON formatting-only changes."""
from pathlib import Path
import argparse,base64,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tests'))
from endurance_controller import ps,q

RAW_CANARY='security/secret-redaction.md'
SAFE_CANARY='security/secret-redaction.sanitized.md'
def published_fixture_text(text):
 # These literal synthetic canaries already occur in the approved test source.
 # They must still never be included in the evidence Git export.
 text=text.replace('TEST_SECRET_DO_NOT_LEAK_12345','[REDACTED]').replace('sk-live998877665544332211','[REDACTED]')
 return '\n'.join(line.rstrip() for line in text.lstrip('\ufeff').splitlines()).strip()+'\n'

def prepare_evidence_export(root):
 root=Path(root).resolve(strict=True);assert root.is_relative_to((R/'evidence').resolve())
 raw=root/RAW_CANARY
 if not raw.exists():return []
 assert raw.resolve().is_relative_to(root),'RAW_FIXTURE_SCOPE_DENIED'
 # Whole-file equivalence to the already-redacted approved historical fixture
 # prevents an arbitrary secret/file from being excluded as a synthetic test.
 approved=subprocess.check_output(['git','show','6e0a507:evidence/phase-23-attempt-3/security-smoke/secret-redaction.md'],cwd=R).decode('utf-8-sig')
 safe=published_fixture_text(raw.read_text(encoding='utf-8-sig'))
 assert safe==published_fixture_text(approved),'UNEXPECTED_PRIVATE_FIXTURE_CONTENT'
 (root/SAFE_CANARY).write_text(safe,encoding='utf-8')
 ignore=root/'.gitignore';expected='/'+RAW_CANARY+'\n'
 assert not ignore.exists() or ignore.read_text(encoding='utf-8')==expected,'UNEXPECTED_EVIDENCE_IGNORE'
 ignore.write_text(expected,encoding='utf-8')
 receipt={'raw_path':RAW_CANARY,'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'export_path':SAFE_CANARY,'export_sha256':hashlib.sha256((root/SAFE_CANARY).read_bytes()).hexdigest(),'reference':'6e0a507:evidence/phase-23-attempt-3/security-smoke/secret-redaction.md','raw_preserved_locally':True,'raw_excluded_from_git':True}
 (root/'PRIVATE-FIXTURE-EXPORT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
 return [RAW_CANARY]

def private_fixture_exclusions(root):
 receipt=root/'PRIVATE-FIXTURE-EXPORT.json'
 if not receipt.exists():return set()
 record=json.loads(receipt.read_text(encoding='utf-8'));raw=root/RAW_CANARY;safe=root/SAFE_CANARY
 assert record['raw_path']==RAW_CANARY and record['export_path']==SAFE_CANARY
 assert hashlib.sha256(raw.read_bytes()).hexdigest()==record['raw_sha256'] and hashlib.sha256(safe.read_bytes()).hexdigest()==record['export_sha256'],'PRIVATE_FIXTURE_HASH_CHANGED'
 assert safe.read_text(encoding='utf-8')==published_fixture_text(raw.read_text(encoding='utf-8-sig')),'PRIVATE_FIXTURE_EXPORT_CHANGED'
 assert (root/'.gitignore').read_text(encoding='utf-8')=='/'+RAW_CANARY+'\n'
 assert not subprocess.check_output(['git','ls-files','--',raw.relative_to(R).as_posix()],cwd=R,text=True).strip(),'PRIVATE_FIXTURE_MUST_NOT_BE_TRACKED'
 approved=subprocess.check_output(['git','show','6e0a507:evidence/phase-23-attempt-3/security-smoke/secret-redaction.md'],cwd=R).decode('utf-8-sig')
 assert safe.read_text(encoding='utf-8')==published_fixture_text(approved),'UNEXPECTED_PRIVATE_FIXTURE_CONTENT'
 return {RAW_CANARY}

def stage_evidence(root):
 root=Path(root).resolve(strict=True);excluded=private_fixture_exclusions(root)
 files=[str(p.relative_to(R)) for p in root.rglob('*') if p.is_file() and p.relative_to(root).as_posix() not in excluded]
 for start in range(0,len(files),35):subprocess.run(['git','add','-f','--',*files[start:start+35]],cwd=R,check=True)
 return excluded
def unique(pairs):
 out={}
 for key,value in pairs:
  if key in out:raise ValueError('DUPLICATE_JSON_KEY_DENIED')
  out[key]=value
 return out
def canonical(text):
 def bad(value):raise ValueError('NONSTANDARD_JSON_CONSTANT_DENIED')
 value=json.loads(text,object_pairs_hook=unique,parse_constant=bad)
 return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)
def formatting_only(before,after):
 if before==after:return True
 try:return canonical(before)==canonical(after)
 except (ValueError,TypeError):
  a=before.splitlines();b=after.splitlines()
  if len(a)!=len(b):return False
  try:return all(x==y or canonical(x)==canonical(y) for x,y in zip(a,b))
  except (ValueError,TypeError):return False
def scan_evidence(root):
 root=Path(root).resolve(strict=True);assert root.is_dir() and root.is_relative_to((R/'evidence').resolve()),'EVIDENCE_SCAN_SCOPE_REQUIRED'
 # No input secret is passed on a command line or printed. The sanitizer's
 # changed output is transferred privately to this process for strict parsing.
 changed=ps('. '+q(R/'scripts/state-manager.ps1')+';. '+q(R/'scripts/security-guard.ps1')+';$rows=@();foreach($f in @(Get-ChildItem -LiteralPath '+q(root)+' -Recurse -File)){$g=Test-WorkspacePathGuard -TargetFilePath $f.FullName -WorkspacePath '+q(root)+' -Operation READ;if(-not $g.Allowed){throw "SCAN_FILE_SCOPE_DENIED"};$raw=[IO.File]::ReadAllText($f.FullName);$safe=Sanitize-StringContent $raw;if($safe -cne $raw){$rows+=@{path=$f.FullName;sanitized_b64=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($safe))}}};@{changed=$rows}',timeout=180)
 hits=[];format_only=[];private=private_fixture_exclusions(root)
 for item in changed['changed']:
  path=Path(item['path']).resolve(strict=True);assert path.is_relative_to(root)
  if path.relative_to(root).as_posix() in private:continue
  original=path.read_text(encoding='utf-8-sig',errors='replace');safe=base64.b64decode(item['sanitized_b64']).decode('utf-8')
  # Preserve physical CR/LF through both reads; read_text universal-newline
  # conversion is immaterial to strict JSON semantics, not to raw evidence.
  (format_only if formatting_only(original,safe) else hits).append(str(path.relative_to(root)))
 return {'status':'PASS' if not hits else 'FAIL','scope':'Git evidence export; proven synthetic fixture original preserved locally and excluded' if private else 'Entire evidence directory','private_raw_fixture_paths':sorted(private),'new_redaction_files':hits,'json_format_only_files':format_only,'policy':'Existing Sanitize-StringContent unchanged; strict JSON/JSONL values equal or DENY; duplicate keys/nonstandard constants DENY','raw_evidence_rewritten':False}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('evidence');args=parser.parse_args();result=scan_evidence(args.evidence);print(json.dumps(result,ensure_ascii=False));raise SystemExit(0 if result['status']=='PASS' else 1)
