'use strict';
// Executed in the guarded top document. The production readonly inspector is
// passed explicitly so preparation and verification select the SAME editor.
// This function prepares text only; it has no submit, key or ledger operations.
function prepareComposerText(text, inspect) {
  const before=inspect();
  if(!before.composer_found||before.composer_matches!==1||!before.editable||before.isStreaming!==false)throw Error('PREPARE_COMPOSER_NOT_UNIQUE_OR_EDITABLE');
  if(before.composer!=='')throw Error('PREEXISTING_COMPOSER_NO_WRITE');
  const editors=Array.from(document.querySelectorAll('[contenteditable="true"],textarea'));
  const prose=editors[before.composer_dom_index];
  if(!prose)throw Error('PREPARE_COMPOSER_CHANGED');
  prose.focus();
  if(document.activeElement!==prose&&!prose.contains(document.activeElement))throw Error('PREPARE_FOCUS_FAILED');
  if(prose.tagName==='TEXTAREA'){
    prose.setSelectionRange(0,prose.value.length);
  }else{
    const range=document.createRange();range.selectNodeContents(prose);
    const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);
  }
  if(!document.execCommand('insertText',false,text))throw Error('PREPARE_INSERT_FAILED');
  prose.dispatchEvent(new Event('input',{bubbles:true}));
  const after=inspect(text);
  if(!after.composer_found||after.composer_matches!==1||after.composer_dom_index!==before.composer_dom_index)throw Error('CHATGPT_ENCODING_MISMATCH_NO_UNCHECKED_CLEAR');
  return {success:true,domText:after.composer,rawInnerText:prose.value??prose.innerText??'',composer_dom_index:after.composer_dom_index};
}
module.exports={prepareComposerText};
