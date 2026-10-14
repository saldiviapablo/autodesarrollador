'use strict';
const fs = require('fs');
const { hash, normalize } = require('./chatgpt-ledger');
const now = () => Number(process.hrtime.bigint() / 1000n) / 1000;
function budgets(responseSeconds) {
  if (!Number.isInteger(responseSeconds) || responseSeconds < 1 || responseSeconds > 300) throw Error('INVALID_RESPONSE_BUDGET');
  const stages = {readiness:15000, prepare:15000, click:4000, confirmation:12000, response:responseSeconds*1000, finalize:4000};
  const internal_ms = Object.values(stages).reduce((a,b)=>a+b,0);
  return {stages, internal_ms, cleanup_margin_ms:5000, parent_ms:internal_ms+8000, cdp_ms:5000, click_event_ms:2000};
}
class Budget {
  constructor(seconds, clock=now) {this.spec=budgets(seconds);this.clock=clock;this.started=clock();this.internalEnd=this.started+this.spec.internal_ms;this.enter('readiness');}
  enter(stage) {this.stage=stage;this.stageEnd=Math.min(this.internalEnd,this.clock()+this.spec.stages[stage]);}
  remaining(cap=5000) {const left=Math.floor(Math.min(this.internalEnd,this.stageEnd)-this.clock());if(left<=0)throw Error('DEADLINE_'+this.stage.toUpperCase());return Math.min(cap,left);}
  expired() {return this.clock()>=Math.min(this.internalEnd,this.stageEnd);}
}
class Trace {
  constructor(filename, id, clock=now) {this.filename=filename;this.id=id;this.clock=clock;if(fs.existsSync(filename)&&fs.lstatSync(filename).isSymbolicLink())throw Error('TRACE_PATH_DENIED');}
  emit(event, fields={}) {
    const allowed=['prompt_sha256','conversation_id','user','assistant','streaming','composer_empty','confirmed','reason','phase','pid'];
    const safe=Object.fromEntries(Object.entries(fields).filter(([k,v])=>allowed.includes(k)&&['string','number','boolean'].includes(typeof v)));
    const row={event,consultation_id:this.id,at:new Date().toISOString(),mono_ms:this.clock(),...safe};
    const fd=fs.openSync(this.filename,'a',0o600);try{fs.writeSync(fd,JSON.stringify(row)+'\n');fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
  }
}
function conversationId(url) {
  const u=new URL(url);if(u.protocol!=='https:'||u.hostname!=='chatgpt.com'||u.username||u.password)throw Error('DOMAIN_BLOCKED');
  if(u.pathname==='/')return null;
  const m=/^\/c\/([A-Za-z0-9-]{1,120})\/?$/.exec(u.pathname);if(!m)throw Error('CONVERSATION_ID_INVALID');return m[1];
}
function sentProof(record, observation, newConversation=false) {
  try {
    const expected=conversationId(record.conversation_url), current=conversationId(observation.url);
    const identity=expected!==null?current===expected:newConversation&&current!==null&&record.user_turns_before===0&&record.assistant_turns_before===0;
    return identity&&observation.user===record.user_turns_before+1&&hash(normalize(observation.lastUserText||''))===record.prompt_sha256;
  } catch {return false;}
}
async function deliver({ledger,id,baseline,click,probe,budget,trace,sleep=ms=>new Promise(r=>setTimeout(r,ms)),newConversation=false}) {
  const record=ledger.read(id);
  budget.enter('click');
  ledger.update(id,{delivery_state:'DELIVERY_INTENT',send_attempts:record.send_attempts+1});
  trace.emit('DELIVERY_INTENT',{prompt_sha256:record.prompt_sha256});
  await click();
  budget.enter('confirmation');let observation,first=true,confirmed=false;
  while(!budget.expired()) {
    observation=await probe();
    const proof=sentProof(record,observation,newConversation);
    trace.emit(first?'FIRST_POST_CLICK_PROBE':'SEND_CONFIRMATION_PROBE',{user:observation.user,assistant:observation.assistant,streaming:!!observation.isStreaming,composer_empty:observation.composer_empty??(typeof observation.composer==='string'?!normalize(observation.composer):undefined),confirmed:proof});first=false;
    if(proof) {
      ledger.update(id,{delivery_state:'SENT_CONFIRMED',message_confirmed:true,user_turns_after:observation.user,conversation_url:observation.url,response_state:'PENDING'});
      trace.emit('SENT_CONFIRMED',{conversation_id:conversationId(observation.url),user:observation.user});confirmed=true;break;
    }
    await sleep(Math.min(300,budget.remaining(300)));
  }
  if(!confirmed){ledger.update(id,{delivery_state:'UNKNOWN_DELIVERY'});trace.emit('TIMEOUT',{phase:'confirmation'});return {status:'UNKNOWN_DELIVERY',no_resend:true};}
  budget.enter('response');trace.emit('RESPONSE_WAIT_START');let last='',stable=0;
  while(!budget.expired()) {
    observation=await probe();
    if(conversationId(observation.url)!==conversationId(ledger.read(id).conversation_url))throw Error('CONVERSATION_CHANGED_AFTER_SENT');
    if(observation.user===baseline.user+1&&observation.assistant===baseline.assistant+1&&!observation.isStreaming&&observation.lastAssistantText) {
      stable=last===observation.lastAssistantText?stable+1:1;last=observation.lastAssistantText;
      if(stable>=2) {
        ledger.update(id,{delivery_state:'COMPLETED',message_confirmed:true,assistant_turns_after:observation.assistant,response_sha256:hash(last),response_state:'CAPTURED'});
        trace.emit('RESPONSE_CAPTURED',{assistant:observation.assistant});return {status:'SUCCESS',response:last,observation};
      }
    }
    await sleep(Math.min(1200,budget.remaining(1200)));
  }
  trace.emit('TIMEOUT',{phase:'response'});return {status:'SENT_CONFIRMED',response_state:'PENDING',no_resend:true};
}
module.exports={budgets,Budget,Trace,conversationId,sentProof,deliver};
