import hashlib,json,pathlib,time,yaml
ROOT=pathlib.Path(__file__).resolve().parents[1]
cfg=yaml.safe_load((ROOT/'config/system.yaml').read_text(encoding='utf-8-sig'));locked=yaml.safe_load((ROOT/'config/VERSIONS.lock').read_text(encoding='utf-8-sig'))
model=pathlib.Path(cfg['llama']['model']);start=time.monotonic()
with model.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
expected=locked['inference']['qwen_model']['blob_sha256']
result={'status':'PASS' if actual==expected else 'FAIL','model_path':str(model),'size_bytes':model.stat().st_size,'expected_sha256':expected,'actual_sha256':actual,'duration_seconds':round(time.monotonic()-start,2),'llama_executable_sha256':hashlib.sha256(pathlib.Path(cfg['llama']['executable']).read_bytes()).hexdigest(),'no_files_modified':True}
(ROOT/'evidence/regression-7a-final/model-hash.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert actual==expected
