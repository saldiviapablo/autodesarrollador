import json,pathlib,re,yaml
ROOT=pathlib.Path(__file__).resolve().parents[1]
checks={}
readme=(ROOT/'00-README.md').read_text(encoding='utf-8-sig')
roadmap=(ROOT/'07-ROADMAP.md').read_text(encoding='utf-8-sig')
manifest=(ROOT/'MANIFEST.md').read_text(encoding='utf-8-sig')
status=(ROOT/'docs/IMPLEMENTATION-STATUS.md').read_text(encoding='utf-8-sig')
caps=(ROOT/'08-CAPACIDADES-NATIVAS-HERMES.md').read_text(encoding='utf-8-sig')
install=json.loads((ROOT/'config/INSTALLATION-STATE.json').read_text(encoding='utf-8-sig'))
checks['README_macro_pass']=bool(re.search(r'Macrofase 7A:.*— PASS',readme))
checks['ROADMAP_macro_pass']=bool(re.search(r'\*\*Macrofase 7A\*\*.*\| \*\*PASS\*\*',roadmap))
checks['MANIFEST_macro_pass']=bool(re.search(r'\*\*Macrofase 7A .*:\*\* \*\*PASS\*\*',manifest))
checks['IMPLEMENTATION_macro_pass']=bool(re.search(r'\| \*\*Macrofase 7A\*\*.*\| \*\*PASS\*\*',status))
checks['CAPABILITIES_macro_pass']='MACROFASE 7A = PASS' in caps
checks['installation_macro_pass']=install['macrophases']['7A']=='PASS'
checks['subphases_all_pass']=all(install['subphases_7a'][f'7A.{i}']=='PASS' for i in range(1,11))
checks['chatgpt_and_regression_pass']=install['chatgpt_idempotency']=='PASS' and install['regression_gate_7a']=='PASS'
checks['7b_and_8_pending']=install['macrophases']['7B']=='PENDING' and install['macrophases']['8']=='PENDING'
checks['no_stale_macro_progress']=not re.search(r'Macrofase 7A[^\n]*(?:IN_PROGRESS|PENDING)',readme+manifest)
checks['no_stale_pending_idempotency']='Pendiente para Macrofase 7A' not in roadmap and 'NO implementado ni probado todavía' not in caps
result={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks}
(ROOT/'evidence/regression-7a-final/document-coherence.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert all(checks.values())
