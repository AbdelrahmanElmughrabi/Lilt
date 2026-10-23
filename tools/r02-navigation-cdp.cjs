/** Observe canceled navigation through CDP without closing/reloading the native app. */
const fs = require('node:fs');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const [port, foreign, output, expectedInput, expectedMarker] = process.argv.slice(2);
const result = {success: false};
async function bounded(operation) {
  let timer;
  try { return await Promise.race([operation, new Promise((_, reject) => {timer = setTimeout(() => reject(Error('CDP probe timeout')), 4000);})]); }
  finally {clearTimeout(timer);}
}
async function record(name, operation) {
  try { result[name] = {value: await bounded(operation)}; }
  catch (error) { result[name] = {error: error.message}; }
}
(async () => {
  if (!expectedInput || !expectedMarker) throw Error('Expected app URL and document marker are required');
  const expected = new URL(expectedInput).href;
  if (new URL(expected).protocol !== 'http:' || new URL(expected).hostname !== '127.0.0.1') throw Error('Expected a loopback app URL');
  result.expected_url = expected;
  result.expected_marker = expectedMarker;
  const browser = await bounded(chromium.connectOverCDP(`http://127.0.0.1:${port}`));
  const page = browser.contexts().flatMap(context => context.pages()).find(page => page.url() === expected);
  if (!page) throw Error('Expected native app target missing');
  const cdp = await bounded(page.context().newCDPSession(page));
  result.before_url = page.url();
  await record('before_body', page.locator('body').innerText({timeout: 3000}).then(text => text.slice(0, 120)));
  await record('assignment', page.evaluate(url => {window.location.href = url; return true;}, foreign + 'navigation-cdp'));
  await record('body_after', page.locator('body').innerText({timeout: 3000}).then(text => text.slice(0, 120)));
  await record('direct_runtime_after', cdp.send('Runtime.evaluate', {expression: 'JSON.stringify({body:!!document.body,marker:window.__r02Marker,url:location.href})', returnByValue: true}));
  result.after_url = page.url();
  for (const name of ['before_body', 'assignment', 'body_after', 'direct_runtime_after']) {
    if (!result[name] || 'error' in result[name]) throw Error(`Required observation failed: ${name}`);
  }
  for (const name of ['before_body', 'body_after']) {
    if (typeof result[name].value !== 'string' || !result[name].value.trim()) throw Error(`Missing body text: ${name}`);
  }
  if (result.assignment.value !== true) throw Error('Navigation assignment was not observed');
  if (result.before_url !== expected || result.after_url !== expected) throw Error('Native app URL changed');
  const raw = result.direct_runtime_after.value;
  if (!raw || 'exceptionDetails' in raw || raw.result?.type !== 'string') throw Error('Invalid CDP runtime result');
  const runtime = JSON.parse(raw.result.value);
  if (!runtime || runtime.body !== true || runtime.marker !== expectedMarker || runtime.url !== expected) {
    throw Error('Native document identity was not preserved');
  }
  result.runtime_after = runtime;
  result.success = true;
})().catch(error => {result.error = error.stack;}).finally(() => {
  fs.writeFileSync(output, JSON.stringify(result, null, 2)); console.log(JSON.stringify(result));
  // Disconnect this test process; Browser.close could close the owned native
  // WebView before the Python probe can independently inspect its real state.
  process.exit(result.success ? 0 : 1);
});
