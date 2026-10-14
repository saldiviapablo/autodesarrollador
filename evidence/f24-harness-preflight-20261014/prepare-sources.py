"""Repoint regression outputs to new evidence, never historical directories."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[2];p=root/'tests'
f=p/'test-windows-launcher-adapter.py';dest=root/'backups/f24-web-gate-20261014/tests'/f.name;shutil.copy2(f,dest)
updates={
 'test-recovery-continuation.py':("E=ROOT/'evidence/f24-frontiers-20261014/recovery';E.mkdir(exist_ok=True)","E=pathlib.Path(os.environ.get('F24_PREFLIGHT_E',str(ROOT/'evidence/f24-frontiers-20261014')))/'recovery';E.mkdir(parents=True,exist_ok=True)"),
 'test-hermes-prompt-transport.py':("E = ROOT / 'evidence/hermes-prompt-transport-20261014'","E = pathlib.Path(os.environ.get('F24_PREFLIGHT_E',str(ROOT/'evidence/hermes-prompt-transport-20261014')))/'reviewer-transport'"),
 'test-phase20.py':("e=ROOT/'evidence/phase-20';e.mkdir(exist_ok=True)","e=pathlib.Path(os.environ.get('F24_PREFLIGHT_E',str(ROOT/'evidence/phase-20')))/'completion';e.mkdir(parents=True,exist_ok=True)"),
 'test-phase22.py':("e=ROOT/'evidence/phase-22';e.mkdir(exist_ok=True)","e=pathlib.Path(os.environ.get('F24_PREFLIGHT_E',str(ROOT/'evidence/phase-22')))/'cleanup';e.mkdir(parents=True,exist_ok=True)"),
 'test-windows-launcher-adapter.py':("E=ROOT/'evidence/f24-launcher-adapter-fix-20261014';E.mkdir(exist_ok=True)","E=pathlib.Path(os.environ.get('F24_PREFLIGHT_E',str(ROOT/'evidence/f24-launcher-adapter-fix-20261014')))/'launcher';E.mkdir(parents=True,exist_ok=True)")}
for name,(a,b) in updates.items():
 f=p/name;s=f.read_text(encoding='utf-8-sig');assert s.count(a)==1,(name,a);s=s.replace(a,b)
 if name not in ('test-hermes-prompt-transport.py','test-windows-launcher-adapter.py'):s='import os\n'+s
 if name=='test-hermes-prompt-transport.py':s=s.replace('E.mkdir(exist_ok=True)','E.mkdir(parents=True,exist_ok=True)',1)
 f.write_text(s,encoding='utf-8')
f=p/'smoke-f24-frontiers.ps1';s=f.read_text(encoding='utf-8-sig');needle="$e=Join-Path $root 'evidence/f24-frontiers-20261014/regression'";assert s.count(needle)==1;s=s.replace(needle,needle+";if($env:F24_PREFLIGHT_E){$e=Join-Path $env:F24_PREFLIGHT_E 'regression'}",1);f.write_text(s,encoding='utf-8')
print('Regression outputs isolated; no historical evidence overwritten.')
