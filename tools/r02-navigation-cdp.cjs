/** Observe canceled navigation through CDP without closing/reloading the native app. */
const fs = require('node:fs');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const [port, foreign, output] = process.argv.slice(2);
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
  const browser = await chromium.connectOverCDP(`http://127.0.0.1:${port}`);
  const page = browser.contexts().flatMap(context => context.pages()).find(page => page.url().startsWith('http://127.0.0.1:'));
  if (!page) throw Error('Native app target missing');
  const cdp = await page.context().newCDPSession(page);
  result.before_url = page.url();
  await record('before_body', page.locator('body').innerText({timeout: 3000}).then(text => text.slice(0, 120)));
  await record('assignment', page.evaluate(url => {window.location.href = url; return true;}, foreign + 'navigation-cdp'));
  await record('body_after', page.locator('body').innerText({timeout: 3000}).then(text => text.slice(0, 120)));
  await record('direct_runtime_after', cdp.send('Runtime.evaluate', {expression: 'JSON.stringify({body:!!document.body,marker:window.__r02Marker,url:location.href})', returnByValue: true}));
  result.after_url = page.url();
  result.success = true;
})().catch(error => {result.error = error.stack;}).finally(() => {
  fs.writeFileSync(output, JSON.stringify(result, null, 2)); console.log(JSON.stringify(result));
  // Disconnect this test process; Browser.close could close the owned native
  // WebView before the Python probe can independently inspect its real state.
  process.exit(result.success ? 0 : 1);
});
