'use strict';
const assert = require('node:assert/strict');
const vm = require('node:vm');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const bridge = path.resolve(__dirname, '../tools/chatgpt-bridge.js');
const { validateDomain, guardPageExpression } = require(bridge);

const cases = [
  ['https://chatgpt.com/', true],
  ['https://chatgpt.com/c/preflight?x=1#part', true],
  ['https://openai.com/', false],
  ['https://www.openai.com/', false],
  ['https://foo.chatgpt.com/', false],
  ['https://chatgpt.com.evil.test/', false],
  ['https://chatgpt.com@evil.test/', false],
  ['http://chatgpt.com/', false],
  ['URL invalida', false],
  ['about:blank', false],
  ['', false],
  ['https://chatgpt.com./', false],
  ['https://user:password@chatgpt.com/', false],
];
const results = [];
for (const [url, allowed] of cases) {
  assert.equal(validateDomain(url), allowed, url);
  const page = { window: { location: { href: url } }, URL, acted: false };
  if (allowed) {
    assert.equal(vm.runInNewContext(guardPageExpression('(acted = true)'), page, { timeout: 1000 }), true);
    assert.equal(page.acted, true);
  } else {
    assert.throws(() => vm.runInNewContext(guardPageExpression('(acted = true)'), page, { timeout: 1000 }));
    assert.equal(page.acted, false, 'Blocked URL must never execute the DOM action');
    const cli = spawnSync(process.execPath, [bridge, '--url', url, '--mock-response', 'must-not-run'], {
      timeout: 5000, encoding: 'utf8', windowsHide: true,
    });
    assert.equal(cli.error, undefined);
    assert.equal(cli.status, 2);
    assert.equal(JSON.parse(cli.stdout).status, 'DOMAIN_BLOCKED');
  }
  results.push({ url, expected: allowed ? 'ALLOW' : 'DENY', status: 'PASS' });
}
console.log(JSON.stringify({ test_id: 'PREFLIGHT-DOMAIN-NODE', status: 'PASS', cases: results }, null, 2));
