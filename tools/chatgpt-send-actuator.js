'use strict';
const {hash,normalize}=require('./chatgpt-ledger');
const {conversationId}=require('./chatgpt-delivery');
// Executed only in the approved top document. Inspection is read-only: no focus,
// insertion, DOM submit, or synthetic DOM keyboard/mouse event.
function inspectComposer(expectedText) {
  const norm=s=>s.trim().replace(/\r\n/g,'\n').replace(/\n\n+/g,'\n');
  const visible=el=>{if(el.isConnected===false)return false;for(let n=el;n;n=n.parentElement){const s=getComputedStyle(n);if(n.hidden||n.inert||n.getAttribute?.('aria-hidden')==='true'||s.visibility==='hidden'||s.visibility==='collapse'||s.display==='none')return false;}const r=el.getBoundingClientRect();return r.width>0&&r.height>0;};
  const text=el=>{const ps=Array.from(el.querySelectorAll('p'));return norm(ps.length?ps.map(p=>p.innerText).join('\n'):(el.value??el.innerText??''));};
  const allEditors=Array.from(document.querySelectorAll('[contenteditable="true"],textarea'));
  const editors=allEditors.filter(el=>visible(el)&&!el.disabled&&!el.readOnly&&!el.parentElement?.closest('[contenteditable="true"]'));
  const matches=editors.filter(el=>expectedText===undefined||text(el)===norm(expectedText));
  const prose=matches.length===1?matches[0]:null;
  const streaming=!!document.querySelector('button[data-testid*="stop"],button[aria-label*="Stop"],button[aria-label*="Detener"],.result-streaming');
  if(!prose)return {url:location.href,composer_found:false,composer_matches:matches.length,isStreaming:streaming,buttons:[]};
  let scope=prose.closest('form,[role="form"]'),scopeKind=scope?'form':null;
  if(!scope){
    let ancestor=prose.parentElement;
    for(let i=0;i<6&&ancestor&&ancestor!==document.body;i++,ancestor=ancestor.parentElement){
      if(ancestor.querySelectorAll('button,input[type="submit"]').length&&editors.filter(el=>ancestor.contains(el)).length===1){scope=ancestor;scopeKind='composer-container';break;}
    }
  }
  const buttons=scope?Array.from(scope.querySelectorAll('button,input[type="submit"]')).filter(button=>{
    // Native submit semantics take precedence; labels/test IDs only supplement
    // them inside the exact composer scope, never across the whole document.
    return button.type==='submit'||/send|enviar/i.test(button.getAttribute('aria-label')||'')||/^(send-button|composer-submit-button)$/.test(button.getAttribute('data-testid')||'');
  }).map(button=>{
    const r=button.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,hit=document.elementFromPoint(x,y);
    return {x,y,width:r.width,height:r.height,disabled:!!button.disabled||button.getAttribute('aria-disabled')==='true',visible:visible(button),hit:!!hit&&button.contains(hit),expectedSend:true,scope:scopeKind};
  }):[];
  return {url:location.href,composer_found:true,composer_matches:matches.length,composer_dom_index:allEditors.indexOf(prose),composer:text(prose),editable:prose.isContentEditable||prose.tagName==='TEXTAREA',focused:document.activeElement===prose||prose.contains(document.activeElement),scope_found:!!scope,scope_kind:scopeKind,isStreaming:streaming,buttons,sendAvailable:buttons.filter(b=>b.visible&&!b.disabled&&b.hit).length===1};
}
function selectActuator(record,observation,{pointerAvailable=true}={}) {
  const humanRetry=record?.delivery_state==='NOT_DELIVERED_CONFIRMED'&&record.human_retry_remaining===1&&record.send_attempts===1;
  if(!record||record.message_confirmed||(!humanRetry&&(record.send_attempts!==0||!['RESERVED','PREPARED'].includes(record.delivery_state)||record.history?.some(e=>e.to==='DELIVERY_INTENT'))))throw Error('ACTUATOR_PRIOR_INTENT_NO_SEND');
  if(conversationId(record.conversation_url)!==conversationId(observation.url))throw Error('ACTUATOR_CONVERSATION_MISMATCH');
  if(!observation.composer_found||observation.composer_matches!==1||!observation.editable||hash(normalize(observation.composer||''))!==record.prompt_sha256)throw Error('ACTUATOR_COMPOSER_HASH_MISMATCH');
  if(observation.isStreaming!==false)throw Error('ACTUATOR_STREAMING_DENIED');
  const candidates=observation.scope_found?(observation.buttons||[]).filter(b=>b.visible&&!b.disabled&&b.expectedSend&&b.hit&&b.width>0&&b.height>0&&Number.isFinite(b.x)&&Number.isFinite(b.y)):[];
  if(candidates.length===1&&pointerAvailable)return {method:'COMPOSER_SCOPED_SUBMIT',button:candidates[0]};
  if(humanRetry)throw Error('ACTUATOR_PRIOR_INTENT_NO_FALLBACK');
  if(observation.focused!==true)throw Error('ACTUATOR_ENTER_REQUIRES_FOCUS');
  return {method:'COMPOSER_ENTER_KEY'};
}
// A pointer readiness probe cannot submit: no button press/release is issued.
// Its acknowledgement timeout may choose the approved pre-intent keyboard
// fallback. Every other error remains fail-closed; deliver() never calls this.
async function probePointerMove(ws,button,dispatch) {
  try{
    await dispatch(ws,'Input.dispatchMouseEvent',{type:'mouseMoved',x:button.x,y:button.y,button:'none',buttons:0,pointerType:'mouse'});
    return true;
  }catch(error){
    if(error.message==='Timeout esperando respuesta CDP para Input.dispatchMouseEvent')return false;
    throw error;
  }
}
async function prepareSendActuator({readRecord,readPrepared,readConversation,baseline,probePointer,trace,sleep=ms=>new Promise(r=>setTimeout(r,ms))}) {
  let selected,pointerAvailable=true,pointerProbed=false;
  const checkBaseline=async()=>{const current=await readConversation();if(current.user!==baseline.user||current.assistant!==baseline.assistant||current.isStreaming)throw Error('BASELINE_CHANGED_NO_SEND');};
  for(let stable=0;stable<2;stable++){
    let prepared=await readPrepared();await checkBaseline();
    selected=selectActuator(readRecord(),prepared,{pointerAvailable});
    if(selected.button&&!pointerProbed){
      const fields={non_send_probe:'mouseMoved',phase:'prepare',send_attempts:readRecord().send_attempts,physical_actions:0};
      trace?.emit('POINTER_PROBE_START',fields);
      pointerAvailable=await probePointer(selected.button);pointerProbed=true;
      trace?.emit('POINTER_PROBE_END',{...fields,available:pointerAvailable});
      prepared=await readPrepared();await checkBaseline();
      selected=selectActuator(readRecord(),prepared,{pointerAvailable});
    }
    if(stable===0)await sleep(300);
  }
  return selected;
}
async function sendPhysicalEnter(ws,dispatch,trace) {
  trace?.emit('ENTER_KEYDOWN_START');
  await dispatch(ws,'Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13,text:'\r',unmodifiedText:'\r'});
  trace?.emit('ENTER_KEYDOWN_END');trace?.emit('ENTER_KEYUP_START');
  await dispatch(ws,'Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13});
  trace?.emit('ENTER_KEYUP_END');
}
module.exports={inspectComposer,selectActuator,sendPhysicalEnter,probePointerMove,prepareSendActuator};
