/** Execute the real helper with controlled CDP transport; no browser/network. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {test} = require('node:test');

const helper = path.resolve(process.env.R02_CDP_HELPER || path.join(__dirname, '../tools/r02-navigation-cdp.cjs'));
const source = fs.readFileSync(helper, 'utf8');
const expected = 'http://127.0.0.1:4321/';
const foreign = 'http://127.0.0.1:4322/';
const marker = 'a'.repeat(32);
const outcomes = [];
if (process.env.R02_CDP_TEST_RESULTS) process.on('exit', () => {
  fs.writeFileSync(process.env.R02_CDP_TEST_RESULTS, JSON.stringify({helper,
    helper_sha256: require('node:crypto').createHash('sha256').update(source).digest('hex'), outcomes}, null, 2));
});

async function execute(scenario) {
  let bodyReads = 0, assigned = false, closed = false, result;
  const assignments = [];
  const failAll = scenario === 'all-observations-fail';
  const runtime = {body: true, marker, url: expected};
  if (scenario === 'runtime-missing-marker') delete runtime.marker;
  if (scenario === 'runtime-wrong-marker') runtime.marker = 'b'.repeat(32);
  if (scenario === 'runtime-wrong-url') runtime.url = foreign;
  if (scenario === 'runtime-no-body') runtime.body = false;
  const response = {result: {type: 'string', value: JSON.stringify(runtime)}};
  if (scenario === 'runtime-invalid-json') response.result.value = '{not JSON';
  if (scenario === 'runtime-exception') response.exceptionDetails = {text: 'Synthetic runtime exception'};
  const cdp = {send: async () => {
    if (failAll || scenario === 'runtime-error') throw Error('Synthetic runtime transport failure');
    return response;
  }};
  const context = {newCDPSession: async () => cdp};
  const page = {
    url: () => scenario === 'changed-page-url' && assigned ? foreign + 'navigation-cdp' : expected,
    context: () => context,
    locator: selector => {
      assert.equal(selector, 'body');
      const before = ++bodyReads === 1;
      return {innerText: async () => {
        if (failAll || scenario === (before ? 'before-body-error' : 'after-body-error')) throw Error('Synthetic body observation failure');
        if (!before && scenario === 'after-body-timeout') return new Promise(() => {});
        if (scenario === (before ? 'empty-before-body' : 'empty-after-body')) return '   ';
        return 'Synthetic native application body';
      }};
    },
    evaluate: async (_operation, url) => {
      assignments.push(url);
      assigned = true;
      if (failAll || scenario === 'assignment-error') throw Error('Synthetic assignment failure');
      return scenario !== 'assignment-false';
    },
  };
  const decoy = {...page, url: () => 'http://127.0.0.1:4999/'};
  const browser = {
    contexts: () => [{pages: () => scenario === 'missing-expected-target' ? [decoy] :
      scenario === 'decoy-first' ? [decoy, page] : [page]}],
    close: async () => {closed = true;},
  };
  const chromium = {connectOverCDP: async () => {
    if (scenario === 'connection-error') throw Error('Synthetic CDP connection failure');
    return browser;
  }};
  const timers = new Set();
  return new Promise((resolve, reject) => {
    const cleanup = () => {for (const timer of timers) clearTimeout(timer);};
    const watchdog = setTimeout(() => {cleanup(); reject(Error('Helper did not report an exit within 6.5 seconds'));}, 6500);
    try {
      vm.runInNewContext(source, {
        URL, console: {log() {}},
        require: name => {
          if (name === 'node:fs') return {writeFileSync: (_output, value) => {result = JSON.parse(value);}};
          if (name === 'fixture-playwright') return {chromium};
          throw Error('Unexpected helper import: ' + name);
        },
        setTimeout: (callback, delay) => {const timer = setTimeout(callback, delay); timers.add(timer); return timer;},
        clearTimeout: timer => {clearTimeout(timer); timers.delete(timer);},
        process: {
          argv: ['node', helper, '9222', foreign, 'virtual-results.json', expected,
            scenario === 'missing-expected-marker' ? '' : marker],
          env: {PLAYWRIGHT_MODULE: 'fixture-playwright'},
          exit: code => {
            clearTimeout(watchdog); cleanup();
            const outcome = {scenario, code, result, browser_closed: closed, assignments};
            outcomes.push(outcome); resolve(outcome);
          },
        },
      }, {filename: helper, timeout: 1000});
    } catch (error) {
      clearTimeout(watchdog); cleanup(); reject(error);
    }
  });
}

test('valid observations pass and preserve the owned native browser', async () => {
  const outcome = await execute('valid');
  assert.equal(outcome.code, 0);
  assert.equal(outcome.result.success, true);
  assert.equal(outcome.result.before_url, expected);
  assert.equal(outcome.result.after_url, expected);
  assert.equal(outcome.browser_closed, false);
  assert.deepEqual(outcome.assignments, [foreign + 'navigation-cdp']);
});

test('select the expected application when another loopback page is listed first', async () => {
  const outcome = await execute('decoy-first');
  assert.equal(outcome.code, 0);
  assert.equal(outcome.result.success, true);
  assert.equal(outcome.result.before_url, expected);
  assert.equal(outcome.browser_closed, false);
});

for (const scenario of ['all-observations-fail', 'before-body-error', 'assignment-error',
  'after-body-error', 'runtime-error', 'runtime-exception', 'runtime-invalid-json',
  'runtime-missing-marker', 'runtime-wrong-marker', 'runtime-wrong-url', 'runtime-no-body',
  'empty-before-body', 'empty-after-body', 'assignment-false', 'changed-page-url',
  'missing-expected-target', 'missing-expected-marker', 'connection-error', 'after-body-timeout']) {
  test('reject ' + scenario + ' without closing the native browser', async () => {
    const outcome = await execute(scenario);
    assert.notEqual(outcome.code, 0);
    assert.equal(outcome.result.success, false);
    assert.equal(outcome.browser_closed, false);
    if (scenario === 'all-observations-fail') {
      for (const name of ['before_body', 'assignment', 'body_after', 'direct_runtime_after']) {
        assert.equal(typeof outcome.result[name].error, 'string');
      }
    }
    if (scenario === 'after-body-timeout') assert.match(outcome.result.body_after.error, /timeout/i);
  });
}
