"""Frozen native dashboard behind a loopback, contract-bound administrative gate."""
import argparse,hashlib,json,os,pathlib,sys,time,urllib.parse
from ruamel.yaml import YAML
import jsonschema
ROOT=pathlib.Path(__file__).resolve().parents[1];yaml=YAML(typ='safe')
SAFE_API=frozenset(['/api/status','/api/config','/api/config/defaults','/api/config/schema','/api/mcp/servers','/api/memory','/api/cron/jobs','/api/skills','/api/dashboard/themes','/api/dashboard/font','/api/dashboard/plugins','/api/auth/status','/api/da/state','/api/sessions','/api/profiles','/api/profiles/active'])
def main():
    if os.environ.get('DA_DASHBOARD_JOB_READY'):
        ready=pathlib.Path(os.environ['DA_DASHBOARD_JOB_READY'])
        ready.write_text(str(os.getpid()))
        assigned=ready.with_suffix('.assigned');deadline=time.monotonic()+10
        while not assigned.exists() and time.monotonic()<deadline:time.sleep(.01)
        if not assigned.exists() or assigned.read_text()!=str(os.getpid()):raise ValueError('JOB_NOT_ASSIGNED')
    ap=argparse.ArgumentParser();ap.add_argument('--project',required=True);ap.add_argument('--host');ap.add_argument('--port',type=int);a=ap.parse_args()
    cfg=yaml.load((ROOT/'config/system.yaml').read_text(encoding='utf-8-sig'));settings=cfg['native_dashboard']
    host=a.host or settings['host'];port=a.port or settings['port']
    if host!='127.0.0.1':raise ValueError('NON_LOOPBACK_DENIED')
    project=pathlib.Path(a.project).absolute()
    for p in [project,*project.parents]:
        if p.exists() and (p.is_symlink() or p.is_junction()):raise ValueError('REPARSE_POINT_DENIED')
    project=project.resolve();project.relative_to(ROOT/'sandbox')
    auto=project/'.autopilot';home=auto/'hermes-dashboard'
    for p in (auto,auto/'RUN-CONTRACT.yaml',home):
        if p.is_symlink() or p.is_junction():raise ValueError('REPARSE_POINT_DENIED')
    def contract_ok():
        c=yaml.load((auto/'RUN-CONTRACT.yaml').read_text(encoding='utf-8-sig'))
        jsonschema.validate(c,json.loads((ROOT/'schemas/run-contract.schema.json').read_text(encoding='utf-8-sig')))
        return c['authorized'] and pathlib.Path(c['project_root']).resolve()==project
    if not contract_ok():raise ValueError('CONTRACT_DENIED')
    home.mkdir(exist_ok=True)
    (home/'config.yaml').write_bytes((ROOT/'config/hermes-reviewer/config.yaml').read_bytes())
    # No background agents, desktop cron ticker, or auto-update during this governed surface.
    for name in list(os.environ):
        if name.startswith(('HERMES_DESKTOP','HERMES_DASHBOARD','HERMES_SERVE','HERMES_WEB')):os.environ.pop(name,None)
    os.environ.update(HERMES_HOME=str(home),HERMES_DISABLE_LAZY_INSTALLS='1',PYTHONDONTWRITEBYTECODE='1')
    sys.path.insert(0,cfg['document_extraction']['native_source_dir'])
    from hermes_cli import web_server as native
    from fastapi.responses import JSONResponse
    native.app.state.bind_host=host;native.app.state.auth_required=False
    class Governance:
        def __init__(self,app):self.app=app
        async def __call__(self,scope,receive,send):
            if scope['type']=='websocket':
                await send({'type':'websocket.close','code':1008});return
            if scope['type']!='http':return await self.app(scope,receive,send)
            path=scope['path'];method=scope['method']
            query=urllib.parse.parse_qs(scope.get('query_string',b'').decode('utf-8','replace'))
            try:valid=contract_ok()
            except Exception:valid=False
            reason=None
            if not valid:reason='CONTRACT_DENIED'
            elif method not in ('GET','HEAD'):reason='ADMIN_MUTATION_LOCKED_DURING_RUN'
            elif any(k in query for k in ('home','path','cwd')) or ('profile' in query and query['profile']!=['default']):reason='PROFILE_OR_PATH_OVERRIDE_DENIED'
            elif path.startswith('/api/') and path not in SAFE_API:reason='ENDPOINT_NOT_ADMITTED'
            elif not path.startswith('/api/') and not (path in ('/','/config','/memory','/cron','/skills','/mcp','/dashboard','/favicon.ico') or path.startswith(('/assets/','/fonts/','/fonts-terminal/'))):reason='ENDPOINT_NOT_ADMITTED'
            if reason:return await JSONResponse({'decision':'DENY','reason':reason},status_code=403)(scope,receive,send)
            return await self.app(scope,receive,send)
    @native.app.get('/api/da/state')
    async def state():
        return json.loads((auto/'STATE.json').read_text(encoding='utf-8-sig'))
    # Native SPA catch-all is already registered; the explicit state route precedes it.
    native.app.router.routes.insert(0,native.app.router.routes.pop())
    native.app.add_middleware(Governance)
    import uvicorn
    uvicorn.run(native.app,host=host,port=port,log_level='warning',access_log=False,timeout_graceful_shutdown=3)
if __name__=='__main__':
    sys.dont_write_bytecode=True
    sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
    try:main()
    except Exception as e:print(json.dumps({'status':'DENY','reason':str(e)}));sys.exit(1)
