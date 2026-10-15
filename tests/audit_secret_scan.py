"""Use the existing sanitizer; ignore only proven JSON formatting-only changes."""
from pathlib import Path
import argparse,base64,json,sys
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tests'))
from endurance_controller import ps,q
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
 hits=[];format_only=[]
 for item in changed['changed']:
  path=Path(item['path']).resolve(strict=True);assert path.is_relative_to(root)
  original=path.read_text(encoding='utf-8-sig',errors='replace');safe=base64.b64decode(item['sanitized_b64']).decode('utf-8')
  # Preserve physical CR/LF through both reads; read_text universal-newline
  # conversion is immaterial to strict JSON semantics, not to raw evidence.
  (format_only if formatting_only(original,safe) else hits).append(str(path.relative_to(root)))
 return {'status':'PASS' if not hits else 'FAIL','new_redaction_files':hits,'json_format_only_files':format_only,'policy':'Existing Sanitize-StringContent unchanged; strict JSON/JSONL values equal or DENY; duplicate keys/nonstandard constants DENY','raw_evidence_rewritten':False}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('evidence');args=parser.parse_args();result=scan_evidence(args.evidence);print(json.dumps(result,ensure_ascii=False));raise SystemExit(0 if result['status']=='PASS' else 1)
