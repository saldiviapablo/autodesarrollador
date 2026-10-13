import asyncio,hashlib,importlib.util,json,os,pathlib,secrets,socket,sys
from ruamel.yaml import YAML
from aiohttp import web,ClientSession
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
cfg=YAML(typ='safe').load((ROOT/'config/system.yaml').read_text(encoding='utf-8-sig'));sys.path.insert(0,cfg['document_extraction']['native_source_dir'])
project=ROOT/'sandbox/phase7a9-gateway';e=ROOT/'evidence/phase-7a9';e.mkdir(exist_ok=True)
os.environ['HERMES_HOME']=str(project/'.autopilot/hermes-gateway');os.environ['HERMES_DISABLE_LAZY_INSTALLS']='1'
from gateway.config import PlatformConfig
from gateway.platforms.webhook import WebhookAdapter
spec=importlib.util.spec_from_file_location('gateway_notify',ROOT/'scripts/gateway-notify.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
async def main():
    received=[];secret=secrets.token_urlsafe(40);adapter=WebhookAdapter(PlatformConfig(enabled=True,extra={'host':'127.0.0.1','secret':secret}))
    async def outbound(request):
        received.append(await request.json());return web.json_response({'accepted':True})
    async def incoming(request):
        body,error=await adapter._read_authenticated_body(request,'sandbox',{'secret':secret})
        if error is not None:return web.json_response({'trust':'UNTRUSTED','decision':'DENY','reason':'INVALID_SIGNATURE'},status=401)
        return web.json_response({'trust':'UNTRUSTED','decision':'DENY','reason':'OUTBOUND_ONLY'},status=403)
    async def stalled(request):
        await asyncio.sleep(5);return web.Response()
    app=web.Application();app.router.add_post('/notify',outbound);app.router.add_post('/incoming',incoming);app.router.add_post('/stalled',stalled)
    runner=web.AppRunner(app);await runner.setup();site=web.TCPSite(runner,'127.0.0.1',0);await site.start();port=site._server.sockets[0].getsockname()[1]
    baseline=(ROOT/'runtime/locks/inference-owner.json').read_bytes()
    protected=hashlib.sha256((ROOT/'config/security.yaml').read_bytes()).hexdigest()
    results={}
    try:
        results['outbound']=await module.notify(project,f'http://127.0.0.1:{port}/notify')
        assert len(received)==1 and received[0]['event']=='RUN COMPLETED'
        async with ClientSession() as session:
            async with session.post(f'http://127.0.0.1:{port}/incoming',json={'command':'git push --force','status':'COMPLETED'}) as response:
                assert response.status==401;results['incoming_unsigned']=await response.json()
        for target in [f'http://localhost:{port}/notify','https://evil.test/',f'http://127.0.0.1@evil.test:{port}/notify']:
            try:await module.notify(project,target);raise AssertionError('External target accepted')
            except ValueError:pass
        try:await module.notify(project,f'http://127.0.0.1:{port}/stalled');raise AssertionError('Deadline failed')
        except TimeoutError:results['timeout']='PASS'
        assert baseline==(ROOT/'runtime/locks/inference-owner.json').read_bytes()
        assert protected==hashlib.sha256((ROOT/'config/security.yaml').read_bytes()).hexdigest()
    finally:await adapter.disconnect();await runner.cleanup()
    with socket.socket() as s:assert s.connect_ex(('127.0.0.1',port))!=0
    report={'status':'PASS','tests':{'T-7A-GATEWAY-001':'PASS','T-7A-GATEWAY-002':'PASS','TIMEOUT_CLEANUP':'PASS'},'results':results,'received_notifications':len(received),'native_inbound_hmac_validation':True,'local_mock_transport':'aiohttp already used by native gateway','outbound_only':True,'cleanup_listener_closed':True,'local_inferences':0,'protected_hash_unchanged':True}
    (e/'tests.json').write_text(json.dumps(report,indent=2)+'\n');(e/'security.json').write_text(json.dumps({'status':'PASS','incoming_unsigned':'DENY_UNTRUSTED','external_targets':'DENY','cleanup':'PASS'},indent=2)+'\n');print(json.dumps(report))
asyncio.run(main())
