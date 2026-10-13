"""Outbound-only notification lane, contract-derived data, loopback sandbox target."""
import asyncio,json,pathlib,re,sys,urllib.parse
from ruamel.yaml import YAML
import jsonschema
ROOT=pathlib.Path(__file__).resolve().parents[1]
async def notify(project,target):
    p=pathlib.Path(project).absolute()
    for part in [p,*p.parents]:
        if part.exists() and (part.is_symlink() or part.is_junction()):raise ValueError('REPARSE_POINT_DENIED')
    p=p.resolve();p.relative_to(ROOT/'sandbox')
    for part in (p/'.autopilot',p/'.autopilot/RUN-CONTRACT.yaml',p/'.autopilot/STATE.json'):
        if part.is_symlink() or part.is_junction():raise ValueError('REPARSE_POINT_DENIED')
    contract=YAML(typ='safe').load((p/'.autopilot/RUN-CONTRACT.yaml').read_text(encoding='utf-8-sig'))
    jsonschema.validate(contract,json.loads((ROOT/'schemas/run-contract.schema.json').read_text(encoding='utf-8-sig')))
    state=json.loads((p/'.autopilot/STATE.json').read_text(encoding='utf-8-sig'))
    if not contract['authorized'] or pathlib.Path(contract['project_root']).resolve()!=p or state['run_id']!=contract['run_id']:raise ValueError('CONTRACT_DENIED')
    url=urllib.parse.urlparse(target)
    if url.scheme!='http' or url.hostname!='127.0.0.1' or url.username or url.password or url.fragment or not url.port:raise ValueError('SANDBOX_DESTINATION_DENIED')
    events={'COMPLETED':'RUN COMPLETED','FAILED':'RUN FAILED','BLOCKED_REQUIRES_HUMAN':'BLOCKED_REQUIRES_HUMAN','STALLED':'STALLED'}
    if state['status'] not in events or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',state['run_id']):raise ValueError('EVENT_NOT_ADMITTED')
    payload={'schema_version':'1.0','event':events[state['status']],'run_id':state['run_id'],'status':state['status'],'trust':'DETERMINISTIC_STATE','local_inferences':0}
    import aiohttp
    # Existing Hermes gateway HTTP transport; automatic redirects are never followed.
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
        async with session.post(target,json=payload,allow_redirects=False) as response:
            if response.status!=200:raise ValueError('NOTIFICATION_REJECTED_'+str(response.status))
            await response.read()
    return {'status':'PASS','payload':payload,'destination':target,'incoming_commands_enabled':False}
if __name__=='__main__':
    try:print(json.dumps(asyncio.run(notify(sys.argv[1],sys.argv[2]))))
    except Exception as e:print(json.dumps({'status':'DENY','reason':str(e)}));sys.exit(1)
