import json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
changed=subprocess.check_output(['git','diff','--name-only','8502d79'],cwd=ROOT,text=True).splitlines()
changed+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
python_files=sorted(n for n in set(changed) if n.endswith('.py') and (ROOT/n).exists())
for name in python_files:compile((ROOT/name).read_bytes(),str(ROOT/name),'exec')
js_files=['tools/chatgpt-bridge.js','tools/chatgpt-ledger.js','tests/test-chatgpt-idempotency.js']
for name in js_files:subprocess.run(['node','--check',str(ROOT/name)],check=True,capture_output=True,timeout=10)
ps_files=sorted(n for n in set(changed) if n.endswith('.ps1') and (ROOT/n).exists())
script=ROOT/'runtime/build-powershell-check.ps1'
script.write_text("$ErrorActionPreference='Stop'\n$files=Get-Content -LiteralPath $args[0] -Raw -Encoding UTF8|ConvertFrom-Json\nforeach($file in $files){$tokens=$null;$errors=$null;$null=[Management.Automation.Language.Parser]::ParseFile($file,[ref]$tokens,[ref]$errors);if($errors.Count -gt 0){throw ($errors|Out-String)}}\n'POWERSHELL_AST_PASS'\n",encoding='utf-8-sig')
manifest=ROOT/'runtime/build-powershell-files.json';manifest.write_text(json.dumps([str(ROOT/n) for n in ps_files]))
p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-File',str(script),str(manifest)],capture_output=True,text=True,timeout=20)
assert p.returncode==0,p.stderr
result={'status':'PASS','python_compiled':len(python_files),'node_syntax_checked':len(js_files),'powershell_5_1_ast_checked':len(ps_files),'files':python_files+js_files+ps_files,'generated_bytecode':False}
(ROOT/'evidence/regression-7a-final/build.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='files'}))
