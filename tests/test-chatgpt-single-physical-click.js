'use strict';
const assert = require('assert/strict');
const fs = require('fs');
const { sendSinglePhysicalClick } = require('../tools/chatgpt-bridge');

(async () => {
  const button = {visible:true, disabled:false, expectedSend:true, x:120, y:240};
  const checks = {};
  const calls = [];
  await sendSinglePhysicalClick(null, button, async (_, method, params) => calls.push({method,params}));
  assert.deepEqual(calls, [
    {method:'Input.dispatchMouseEvent',params:{type:'mousePressed',x:120,y:240,button:'left',clickCount:1}},
    {method:'Input.dispatchMouseEvent',params:{type:'mouseReleased',x:120,y:240,button:'left',clickCount:1}},
  ]);
  checks.one_physical_press_release_pair = 'PASS';
  for (const invalid of [null, {...button,visible:false}, {...button,disabled:true},
                         {...button,expectedSend:false}, {...button,x:NaN}, {...button,y:Infinity}]) {
    let dispatched = 0;
    await assert.rejects(sendSinglePhysicalClick(null, invalid, async () => dispatched++), /SEND_BUTTON_UNAVAILABLE/);
    assert.equal(dispatched, 0);
  }
  checks.invalid_target_no_input = 'PASS';
  for (const errorAt of [1,2]) {
    let dispatched = 0;
    await assert.rejects(sendSinglePhysicalClick(null, button, async () => {
      if (++dispatched === errorAt) throw new Error('transport ambiguous');
    }), /transport ambiguous/);
    assert.equal(dispatched, errorAt);
  }
  checks.transport_error_no_retry_or_fallback = 'PASS';
  const source = fs.readFileSync(require.resolve('../tools/chatgpt-bridge'), 'utf8');
  assert(!source.includes('sendBtn.click()'));
  assert(!source.includes('form.requestSubmit()'));
  assert(!source.includes("new KeyboardEvent('keydown'"));
  const intent = source.indexOf("ledger.update(consultationId, { delivery_state: 'DELIVERY_INTENT'");
  const click = source.indexOf('await sendSinglePhysicalClick(ws, physicalButton);');
  assert(intent > 0 && click > intent);
  checks.intent_persisted_before_only_send_path = 'PASS';
  console.log(JSON.stringify({status:'PASS',checks,browser_access:false,physical_sends:0},null,2));
})().catch(err => {console.error(err);process.exitCode=1;});
