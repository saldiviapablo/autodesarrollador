"""Single desktop entry, native Windows folder/file pickers, no extra packages.

The UI proposes and displays; canonical Prepare, approval and Runner decide.
There is deliberately no auto-approve or test-only approval switch.
"""
import argparse
import ctypes
from ctypes import wintypes
import datetime
import json
import os
from pathlib import Path
import subprocess
import threading
import time
import tkinter as tk
from tkinter import filedialog, ttk
import urllib.request
import uuid

import project_onboarding as data

R=data.ROOT
PY=str(Path(os.__file__).parents[1]/'python.exe')
if not Path(PY).exists(): PY='C:/Python314/python.exe'
ENV=dict(os.environ,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',PSModulePath='C:/Windows/System32/WindowsPowerShell/v1.0/Modules')
K=ctypes.WinDLL('kernel32',use_last_error=True)
K.CreateMutexW.argtypes=[ctypes.c_void_p,wintypes.BOOL,wintypes.LPCWSTR];K.CreateMutexW.restype=wintypes.HANDLE
K.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];K.OpenProcess.restype=wintypes.HANDLE
K.GetProcessTimes.argtypes=[wintypes.HANDLE,*([ctypes.POINTER(wintypes.FILETIME)]*4)]
K.CloseHandle.argtypes=[wintypes.HANDLE]
K.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
K.ReleaseMutex.argtypes=[wintypes.HANDLE]


def birth(pid):
    handle=K.OpenProcess(0x1000,False,int(pid))
    if not handle: return None
    try:
        times=[wintypes.FILETIME() for _ in range(4)]
        if not K.GetProcessTimes(handle,*[ctypes.byref(x) for x in times]): return None
        return (times[0].dwHighDateTime<<32)+times[0].dwLowDateTime+504911232000000000
    finally: K.CloseHandle(handle)


class Mutex:
    def __init__(self,name):
        self.handle=K.CreateMutexW(None,False,name)
        if not self.handle: raise OSError('MUTEX_CREATE_FAILED')
        self.held=K.WaitForSingleObject(self.handle,0) in (0,0x80)
        if not self.held:
            K.CloseHandle(self.handle);self.handle=None
            raise ValueError('Ya hay otra ejecución o ventana activa. Usá esa ventana o el iniciador Detener.')
    def close(self):
        if self.handle:
            if self.held: K.ReleaseMutex(self.handle)
            K.CloseHandle(self.handle);self.handle=None


def ps(script,*args):
    return ['powershell.exe','-NoProfile','-NonInteractive','-File',str(R/script),*map(str,args)]


def spawn(argv,payload=None):
    child=subprocess.Popen(argv,cwd=R,env=ENV,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                           creationflags=subprocess.CREATE_NO_WINDOW)
    box={}
    def communicate():
        out,err=child.communicate(None if payload is None else json.dumps(payload,ensure_ascii=False).encode('utf-8'))
        box.update(stdout=out.decode('utf-8-sig',errors='strict'),stderr=err.decode('utf-8-sig',errors='replace'))
    thread=threading.Thread(target=communicate,daemon=True);thread.start()
    return child,box,thread


def run_json(argv,payload=None,timeout=30):
    child,box,thread=spawn(argv,payload)
    thread.join(timeout)
    if thread.is_alive():
        child.kill();thread.join(10)
        raise ValueError('TRANSPORT_TIMEOUT')
    if child.returncode:
        raise ValueError(data.secret.sanitize_text(box.get('stdout','')+' '+box.get('stderr',''))[0])
    return json.loads(box['stdout'])


def active_stop(project=None):
    pointer=R/'runtime/project-launcher/active.json'
    active=data.read(pointer) if pointer.exists() else None
    if project is None:
        if not active or birth(active['pid'])!=active['start_ticks']:
            raise ValueError('No hay un Runner activo iniciado desde esta ventana. No se modificó ningún proyecto.')
        project=active['project']
    info=data.inspect(project)
    if not info['prepared'] or not info['lock']:
        raise ValueError('No hay un Runner activo con ownership registrado.')
    lock=info['lock'];pid=lock['owner_pid'];ticks=birth(pid)
    if ticks is None: raise ValueError('El owner del lock ya no existe. Metadata conservada.')
    if active and active['project']==str(data.project(project)):
        if active['run_id']!=info['run_id'] or active['pid']!=pid or active['start_ticks']!=ticks:
            raise ValueError('OWNERSHIP_MISMATCH_NO_STOP')
    else:
        # Without the launcher pointer, use the native PROCESS_STARTED/run record
        # only via the owner's exact birth persisted in PROCESSES.json.
        raise ValueError('No se encontró la identidad exacta del Runner de este iniciador. Usá runner/stop.ps1 para una ejecución iniciada por otra vía.')
    return run_json(ps('runner/stop.ps1','-ProjectRoot',str(project)))


def plan_review_text(bound):
    p=bound['proposal']['plan']
    text=(f"PROYECTO: {bound['project']}\nOBJETIVO:\n{bound['objective']}\n\n"
          "AUTONOMÍA: unattended, dentro de este proyecto.\nGIT: local / NO PUSH.\n"
          f"WEB: {p.get('research','Sin investigación programada')}\n"
          f"CHATGPT: {p.get('consultation','Sin consulta programada')}\n"
          "ACCIONES PERMITIDAS: editar archivos autorizados, ejecutar tests y commits locales.\n"
          "ACCIONES PROHIBIDAS: push, borrar la raíz, modificar infraestructura o guardrails, escribir fuera del proyecto, producción y despliegue.\n"
          f"TIMEOUTS: Prepare canónico fija un máximo de 120 min; este plan lo limita a {p.get('global_timeout_seconds',7200)} s. Fase: {p.get('phase_timeout_seconds',180)} s.\n"
          f"BUDGETS: ciclos {p.get('max_cycles','global')}; reinicios por rol {p.get('restart_budget','global')}; siempre limitados por configuración global.\n"
          "COMPLETION: objetivo + criterios + tests + build + artefactos + diff permitido + pendientes vacíos + STATE + Reviewer independiente.\n\n"
          "El Worker todavía no está autorizado. Si aprobás, Prepare generará el contrato y se comprobará que coincide con este plan antes de iniciar.\n\n"
          "PLAN COMPLETO:\n"+json.dumps(p,indent=2,ensure_ascii=False))
    for pin in p.get('immutable_files',[]):
        content=bound['proposal']['seed_files'].get(pin['path'])
        if content is None:content=(Path(bound['project'])/pin['path']).read_text(encoding='utf-8-sig')
        text+='\n\nPRUEBA INMUTABLE: '+pin['path']+'\n'+content
    if 'QWEN.md' in bound['project_snapshot']:
        text+='\n\nQWEN.md existente: se conserva íntegro, con respaldo y SHA-256; la guía generada por Prepare queda en evidence.'
    return text+'\n\n¿INICIAR ESTE PROYECTO? Esta aprobación vale una sola vez para el plan y las políticas mostradas.'


class App:
    def __init__(self):
        self.root=tk.Tk();self.root.title('Desarrollador Autónomo');self.root.geometry('920x690');self.root.minsize(680,480)
        self.root.state('zoomed')
        self.root.option_add('*Font','{Segoe UI} 11')
        self.frame=ttk.Frame(self.root,padding=16);self.frame.pack(fill='both',expand=True)
        self.text=tk.Text(self.frame,wrap='word',undo=True);scroll=ttk.Scrollbar(self.frame,command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.text.pack(fill='both',expand=True)
        self.buttons=ttk.Frame(self.root,padding=12);self.buttons.pack(fill='x')
        self.choice=tk.StringVar();self.project=None;self.session=R/'runtime/project-launcher/sessions'/uuid.uuid4().hex
        self.active=None;self.stop_requested=False;self.closed=False;self.health='Sin respuesta'
        self.root.protocol('WM_DELETE_WINDOW',self.cancel)
    def event(self,kind,details=None):
        self.session.mkdir(parents=True,exist_ok=True)
        line=json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'type':kind,'project':str(self.project) if self.project else None,'details':details},ensure_ascii=False)
        line=data.secret.sanitize_text(line)[0]
        with (self.session/'EVENTS.jsonl').open('a',encoding='utf-8') as f:f.write(line+'\n')
    def show(self,title,text,choices,editable=False):
        self.root.title('Desarrollador Autónomo - '+title)
        self.text.configure(state='normal');self.text.delete('1.0','end');self.text.insert('1.0',text)
        self.text.configure(state='normal' if editable else 'disabled')
        for child in self.buttons.winfo_children():child.destroy()
        for label,value in choices:
            ttk.Button(self.buttons,text=label,command=lambda v=value:self.choice.set(v)).pack(side='right',padx=5)
        self.root.deiconify();self.root.update_idletasks()
        if editable:self.text.focus_set()
    def wait_choice(self):
        self.choice.set('');self.root.wait_variable(self.choice);return self.choice.get()
    def cancel(self):
        if self.active:
            child=self.active['child']
            if self.active['kind']=='run':
                if not self.stop_requested:
                    try:active_stop(self.project);self.stop_requested=True;self.event('STOP_REQUESTED')
                    except Exception as e:self.event('STOP_FAILED',str(e))
            elif self.active['kind']=='prepare':
                self.active['cancel_after']=True # finish atomic admission/initializer before leaving
            else:
                child.kill();self.active['cancel_after']=True
        else:self.choice.set('cancel')
    def message(self,title,text):
        self.show(title,text,[('Cerrar','close')]);self.wait_choice()
    def objective(self):
        value=''
        while True:
            self.show('Objetivo — pegá texto o abrí un brief UTF-8',value,
                      [('Cancelar','cancel'),('Continuar','next'),('Abrir .md o .txt','file')],True)
            self.text.tag_add('sel','1.0','end')
            choice=self.wait_choice();value=self.text.get('1.0','end-1c')
            if choice=='cancel':return None
            if choice=='file':
                path=filedialog.askopenfilename(parent=self.root,title='Elegí el objetivo UTF-8',filetypes=[('Brief Markdown o texto','*.md *.txt')])
                if path:
                    value=data.main({'action':'brief','path':path})['text'];self.event('BRIEF_IMPORTED',{'extension':Path(path).suffix,'sha256':hashlib_sha(value)})
                continue
            if choice=='next':
                if not value.strip():continue
                return data.safe_text(value)
    def approve_plan(self,bound):
        self.show('Revisar y aprobar',plan_review_text(bound),[('No, cancelar','cancel'),('Sí, iniciar este proyecto','approve')])
        return self.wait_choice()=='approve'
    def approval(self,info):
        c,p=info['contract'],info['plan']
        text=(f"PROYECTO: {info['project']}\nRUN ID: {c['run_id']}\n\nOBJETIVO:\n{c['objective']}\n\n"
              f"AUTONOMÍA: {c['autonomy_mode']}\nGIT: local / NO PUSH\n"
              f"WEB: {p.get('research', 'Sin investigación programada')}\nCHATGPT: {p.get('consultation', 'Sin consulta programada; no se enviará una desde este plan')}\n\n"
              f"ACCIONES PERMITIDAS: {', '.join(c['allowed_actions'])}, dentro del proyecto.\n"
              f"ACCIONES PROHIBIDAS: {', '.join(c['forbidden_actions'])}; escribir fuera del proyecto, modificar infraestructura o credenciales, publicar o desplegar.\n"
              f"TIMEOUTS: contrato {c['time_budget_minutes']} min; plan {p.get('global_timeout_seconds','límite del contrato')} s; fase {p.get('phase_timeout_seconds',180)} s.\n"
              f"BUDGETS: ciclos {p.get('max_cycles','global')}; reinicios por rol {p.get('restart_budget','global')}. Siempre limitados por la política global.\n"
              "COMPLETION: criterios + tests + build + artefactos + diff permitido + pendientes vacíos + STATE + Reviewer independiente.\n\n"
              f"CRITERIOS:\n"+'\n'.join(c['acceptance_criteria'])+"\n\nPLAN COMPLETO:\n"+json.dumps(p,indent=2,ensure_ascii=False))
        for pin in p.get('immutable_files',[]):
            text+='\n\nPRUEBA INMUTABLE: '+pin['path']+'\n'+(Path(info['project'])/pin['path']).read_text(encoding='utf-8-sig')
        text+='\n\n¿INICIAR ESTE PROYECTO? La aprobación queda ligada a este contrato y plan.'
        self.show('Revisar y aprobar',text,[('No, cancelar','cancel'),('Sí, iniciar este proyecto','approve')])
        return self.wait_choice()=='approve'
    def progress_text(self,started):
        a=self.project/'.autopilot'
        try:
            s=data.read(a/'STATE.json');events=(a/'EVENTS.jsonl').read_text(encoding='utf-8-sig').splitlines();last=json.loads(events[-1])
            restarts=data.read(a/'RESTARTS.json') if (a/'RESTARTS.json').exists() else {}
            return (f"PROJECT: {self.project}\nRUN ID: {s['run_id']}\nSTATUS: {s['status']}\nCURRENT PHASE: {s['current_phase']}\n"
                    f"CURRENT TASK: {s['current_task']}\nLAST EVENT: {last['type']}\nELAPSED: {int(time.monotonic()-started)} s en esta apertura\n"
                    f"RESTARTS: {restarts}\nMODEL HEALTH: {self.health}\n\nEl Runner conserva el reloj original al continuar.\n"
                    "Para detener: DETENER-DESARROLLADOR-AUTONOMO.bat.\nCerrar esta ventana también solicita parada segura.")
        except (OSError,ValueError,KeyError):return f'PROJECT: {self.project}\nSTATUS: STARTING\nEl Runner está comprobando la admisión.'
    def wait_process(self,argv,payload,title,timeout,kind):
        child,box,thread=spawn(argv,payload);started=time.monotonic()
        self.active={'child':child,'kind':kind,'cancel_after':False}
        self.stop_requested=False
        if kind=='run':
            info=data.inspect(self.project)
            pointer={'project':str(self.project),'run_id':info['run_id'],'pid':child.pid,'start_ticks':birth(child.pid),'session':str(self.session)}
            path=R/'runtime/project-launcher/active.json';path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(pointer),encoding='utf-8');self.event('RUNNER_STARTED',pointer)
        self.show(title,'Preparando…',[])
        def health():
            try:
                with urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=1) as response:
                    self.health='READY' if json.load(response).get('status')=='ok' else 'No disponible'
            except Exception:self.health='Sin respuesta'
        def tick():
            if not thread.is_alive():self.choice.set('done');return
            if time.monotonic()-started>timeout:
                if kind=='run':
                    if not self.stop_requested:
                        active_stop(self.project);self.stop_requested=True
                else:child.kill()
            if kind=='run':
                threading.Thread(target=health,daemon=True).start();text=self.progress_text(started)
            else:text=f'{title}\n\nPROJECT: {self.project}\nTiempo: {int(time.monotonic()-started)} s\n\nEl Worker todavía no está autorizado.\nHermes prepara el plan en solo lectura; Prepare valida y genera el contrato.'
            self.text.configure(state='normal');self.text.delete('1.0','end');self.text.insert('1.0',text);self.text.configure(state='disabled')
            self.root.after(1500,tick)
        self.root.after(100,tick);self.wait_choice()
        cancelled=self.active['cancel_after'];self.active=None
        self.event('CHILD_EXIT',{'kind':kind,'pid':child.pid,'exit_code':child.returncode,'stdout':box.get('stdout',''),'stderr':box.get('stderr','')})
        if cancelled:raise ValueError('Preparación cancelada; no se aprobó ni inició el Worker.')
        if child.returncode and kind!='run':raise ValueError(box.get('stdout','')+' '+box.get('stderr',''))
        return box
    def launch(self,project):
        if not project:
            self.show('Elegir proyecto','Elegí la carpeta del proyecto en el selector de Windows.',[])
            project=filedialog.askdirectory(parent=self.root,title='Elegí la carpeta del proyecto',mustexist=True)
            if not project:return
        info=data.inspect(project);self.project=Path(info['project']);self.event('PROJECT_SELECTED',{'prepared':info['prepared']})
        fresh=not info['prepared'];recover=False
        if info['prepared']:
            s=info['state'];choices=[('Cancelar','cancel')]
            if s['status'] in data.TERMINAL|{'INITIALIZED','READY'}:choices.append(('Nuevo objetivo','new'))
            if info['can_continue']:choices.append(('Continuar proyecto','continue'))
            self.show('Proyecto preparado',f"PROYECTO: {self.project}\nÚLTIMO RUN: {s['run_id']}\nESTADO: {s['status']}\nÚLTIMA TAREA: {s['current_task']}\nÚLTIMO CHECKPOINT: {s['checkpoint']['last_id']}\nPENDIENTES: {s['pending_tasks']}\nTIEMPO RESTANTE: {int(info['remaining_seconds'])} s\n\nContinuar conserva reloj y contadores.\nNuevo objetivo archiva la preparación anterior íntegra.",choices)
            choice=self.wait_choice()
            if choice=='cancel':return
            fresh=choice=='new';recover=not fresh and s['status']!='INITIALIZED'
        if fresh:
            objective=self.objective()
            if objective is None:self.event('OBJECTIVE_CANCELLED');return
            bound=data.cached_draft(self.project,objective)
            if bound is None:
                planned=self.wait_process(ps('runner/plan-objective.ps1'),{'project':str(self.project),'objective':objective},'Hermes prepara el plan de solo lectura',390,'plan')
                bound=json.loads(planned['stdout'])
                data.cache_draft(bound)
            else:self.event('VALIDATED_UNAPPROVED_DRAFT_REUSED',{'binding':bound['binding']})
            if bound['status']!='PASS':raise ValueError('PLAN_DENIED')
            if not self.approve_plan(bound):
                self.event('APPROVAL_DENIED',{'binding':bound['binding'],'project_writes':0});return
            bound.update(action='approve_plan',decision='APPROVE',method='HUMAN_PLAN_REVIEW')
            approval=run_json(ps('scripts/project-launcher-action.ps1'),bound)
            self.event('HUMAN_APPROVAL',{'binding':bound['binding'],'approval_id':approval['approval_id']})
            bound['approval_id']=approval['approval_id']
            bound.update(action='prepare',new_objective=info['prepared'])
            self.wait_process(ps('scripts/project-launcher-action.ps1'),bound,'Prepare y preflight canónicos',160,'prepare')
        info=data.contract.inspect(self.project)
        validated=subprocess.run([PY,'-B',str(R/'runner/contract.py'),'validate','--project',str(self.project)],capture_output=True,env=ENV,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
        if validated.returncode:
            if fresh:raise ValueError('GENERATED_CONTRACT_NOT_AUTHORIZED_BY_REVIEWED_PLAN_STOP')
            if not self.approval(info):self.event('APPROVAL_DENIED',{'run_id':info['contract']['run_id']});return
            run_json([PY,'-B',str(R/'runner/contract.py'),'approve','--project',str(self.project),'--digest',info['digest']])
            self.event('HUMAN_APPROVAL',{'run_id':info['contract']['run_id'],'digest':info['digest']})
        argv=ps('runner/run.ps1','-ProjectRoot',str(self.project),'-Action','Start')
        if recover:argv+=['-Recover']
        finished=self.wait_process(argv,None,'Ejecución',28860,'run')
        state=data.read(self.project/'.autopilot/STATE.json')
        self.event('RUNNER_FINISHED',{'status':state['status']})
        self.message('Resultado: '+state['status'],f"PROJECT: {self.project}\nRUN ID: {state['run_id']}\nSTATUS: {state['status']}\n\nREPORTES:\n{self.project/'.autopilot/reports'}\n\n{finished['stdout']}")
    def close(self):self.root.destroy()


def hashlib_sha(text):
    return data.hashlib.sha256(text.encode('utf-8')).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',default='');parser.add_argument('--stop',action='store_true');a=parser.parse_args()
    app=App();mutex=None
    try:
        if a.stop:
            result=active_stop(a.project or None)
            app.message('Parada solicitada',f"RUN: {result['run_id']}\nEl Runner guardará checkpoint, estado y reporte, y cerrará sus procesos.")
        else:
            mutex=Mutex('Local\\DesarrolladorAutonomo_ProjectLauncher')
            app.launch(a.project)
    except Exception as exc:
        error=data.secret.sanitize_text(str(exc))[0];app.event('BLOCKED',error)
        app.message('Inicio bloqueado','BLOCKED_REQUIRES_HUMAN\n\n'+error+'\n\nNo se inicia trabajo sin un contrato válido y aprobado.')
    finally:
        if mutex:mutex.close()
        app.close()


if __name__=='__main__':main()
