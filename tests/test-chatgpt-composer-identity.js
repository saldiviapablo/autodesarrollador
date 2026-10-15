'use strict';
const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),{spawnSync}=require('node:child_process');
const {composerBindings}=require('../tools/chatgpt-composer');const {conversationBindings}=require('../tools/chatgpt-conversation');
const {inspectComposer}=require('../tools/chatgpt-send-actuator');const {prepareComposerText}=require('../tools/chatgpt-composer-prepare');
function page({marker='data',code=true,codeSpoof=false,hiddenOld=false,duplicate=false,onlyCode=false,generic=false,unknownExtra=false,dirty=false}={}){
 let selected;const rect={x:0,y:0,width:200,height:30},doc={};
 function node(text='',attrs={},classes=[]){return {innerText:text,attrs,classNames:classes,parentElement:null,isConnected:true,isContentEditable:true,tagName:'DIV',id:attrs.id||'',style:{display:'block',visibility:'visible'},getAttribute(n){return this.attrs[n]??null;},hasAttribute(n){return Object.hasOwn(this.attrs,n);},getBoundingClientRect(){return this.style.display==='none'?{...rect,width:0}:rect;},getClientRects(){return [this.getBoundingClientRect()];},contains(n){for(;n;n=n.parentElement)if(n===this)return true;return false;},querySelectorAll(){return [];},focus(){doc.activeElement=this;},dispatchEvent(){},matches(s){return s==='[contenteditable="true"]'?this.isContentEditable:s==='[data-message-author-role]'?this.hasAttribute('data-message-author-role'):s==='article[data-turn]'?this.tagName==='ARTICLE'&&this.hasAttribute('data-turn'):s==='[class*="DilResponseRoot"]'?this.classNames.some(v=>v.includes('DilResponseRoot')):s.startsWith('.')?this.classNames.includes(s.slice(1)):false;},closest(selector){for(let n=this;n;n=n.parentElement)if(selector.split(',').some(s=>n.matches(s.trim())))return n;return null;}};}
 const assistant=node('response',{ 'data-message-author-role':'assistant'});assistant.isContentEditable=false;
 const user=node('question',{'data-message-author-role':'user'});user.isContentEditable=false;
 const cm=node('print("assistant code ñ")',codeSpoof?{id:'prompt-textarea','data-composer-markdown':''}:{},['cm-content']);cm.parentElement=assistant;
 const attrs=generic?{}:marker==='data'?{'data-composer-markdown':''}:marker==='id'?{id:'prompt-textarea'}:{'data-testid':'prompt-textarea'};
 const composer=node(dirty?'owned text ñ':'',attrs,['ProseMirror']);
 const old=node('retained',{id:'prompt-textarea'});old.style.display='none';
 const editors=[...(hiddenOld?[old]:[]),...(code?[cm]:[]),...(onlyCode?[]:[composer]),...(duplicate?[node('other',{id:'prompt-textarea'})]:[]),...(unknownExtra?[node('unrelated widget')]:[])];
 doc.querySelectorAll=s=>s==='[contenteditable="true"],textarea'?editors:s==='[data-message-author-role="user"]'?[user]:s==='[data-message-author-role="assistant"]'?[assistant]:[];
 doc.querySelector=()=>null;doc.elementFromPoint=()=>null;doc.createRange=()=>({selectNodeContents(n){selected=n;}});doc.execCommand=(cmd,_,text)=>{assert.equal(cmd,'insertText');assert.equal(selected,composer);selected.innerText=text;return true;};doc.activeElement=composer;
 const ctx=vm.createContext({document:doc,window:{getSelection:()=>({removeAllRanges(){},addRange(){}})},Event:class{},location:{href:'https://chatgpt.com/c/identity-test'},getComputedStyle:n=>n.style,module:{exports:{}},console});
 const evaluate=s=>vm.runInContext(s,ctx);const snapshot=()=>evaluate(`(()=>{${conversationBindings()}return readConversationSnapshot();})()`);const inspect=()=>evaluate(`(()=>{${composerBindings()}return (${inspectComposer.toString()})();})()`);const prepare=()=>evaluate(`(()=>{${composerBindings()}return (${prepareComposerText.toString()})('Canario áéíóú ñ',${inspectComposer.toString()});})()`);
 return {doc,editors,composer,cm,snapshot,inspect,prepare,evaluate,ctx};
}
const checks={};const a=page();assert.equal(a.editors.length,2);assert.equal(a.snapshot().composer_empty,true);assert.equal(a.inspect().composer_matches,1);assert.equal(a.inspect().composer,'');checks.code_editor_not_composer='PASS';
const old=spawnSync('git',['show','596c8b0:tools/chatgpt-conversation.js'],{encoding:'utf8',windowsHide:true});assert.equal(old.status,0);vm.runInContext(old.stdout,a.ctx);assert.equal(a.ctx.module.exports.readConversationSnapshot().composer_empty,false);checks.actual_legacy_a10_reader_reproduced='PASS';
for(const marker of ['data','id','testid']){const p=page({marker});assert.equal(p.snapshot().composer_empty,true);assert.equal(p.inspect().composer_matches,1);checks['positive_marker_'+marker]='PASS';}
for(const options of [{onlyCode:true},{generic:true,code:false},{generic:true,code:false,unknownExtra:true}]){const p=page(options);assert.equal(p.inspect().composer_found,false);assert.equal(p.snapshot().composer_empty,false);}checks.unidentified_or_missing_composer_deny='PASS';
const dup=page({duplicate:true});assert.equal(dup.inspect().composer_found,false);assert.equal(dup.inspect().composer_matches,2);assert.equal(dup.snapshot().composer_empty,false);assert.throws(dup.prepare,/NOT_UNIQUE/);checks.two_identified_composers_deny='PASS';
const spoof=page({codeSpoof:true});assert.equal(spoof.inspect().composer_matches,1);assert.equal(spoof.inspect().composer,'');checks.positive_marker_inside_message_still_excluded='PASS';
const hidden=page({hiddenOld:true});assert.equal(hidden.snapshot().composer_empty,true);assert.equal(hidden.inspect().composer_matches,1);checks.hidden_retained_composer_filtered='PASS';
const extra=page({unknownExtra:true});assert.equal(extra.inspect().composer_matches,1);checks.unrelated_widget_ignored_when_real_composer_identified='PASS';
const dirty=page({dirty:true});assert.equal(dirty.snapshot().composer_empty,false);assert.equal(dirty.inspect().composer,'owned text ñ');assert.throws(dirty.prepare,/PREEXISTING/);checks.nonempty_real_composer_never_ignored='PASS';
const prep=page();const before=prep.cm.innerText;assert.equal(prep.prepare().success,true);assert.equal(prep.composer.innerText,'Canario áéíóú ñ');assert.equal(prep.cm.innerText,before);checks.prepare_never_edits_assistant_code='PASS';
assert.equal(prep.snapshot().user,1);assert.equal(prep.snapshot().assistant,1);checks.turn_counter_unchanged='PASS';
console.log(JSON.stringify({status:'PASS',checks,real_sends:0,browser_access:false,ledger_access:false},null,2));
