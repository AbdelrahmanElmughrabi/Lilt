/** Controlled loopback resource checks; no personal browser profile or real audio. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const [origin, foreign, id, output] = process.argv.slice(2);
const result = {success: false, checks: [], browser: {}, limits: ['Synthetic tone, not speech generation.', 'Source HTTP server, not installed MSIX.', 'Known-ID raw local access remains possible.']};
let browser;
const raw = (route, headers = {}, method = 'GET') => new Promise((resolve, reject) => {
  const request = http.request(origin, {path: route, headers, method}, response => {
    const data = []; response.on('data', chunk => data.push(chunk));
    response.on('end', () => resolve({status: response.statusCode, headers: response.headers, body: Buffer.concat(data)}));
  }); request.on('error', reject); request.end();
});
(async () => {
  const media = `/media/${id}.wav`;
  const audio = await raw(media);
  assert.equal(audio.status, 200); assert.equal(audio.body.subarray(0, 4).toString(), 'RIFF');
  assert.equal(audio.headers['access-control-allow-origin'], undefined);
  assert.equal(audio.headers['cross-origin-resource-policy'], 'same-origin');
  assert.equal(audio.headers['x-frame-options'], 'DENY');
  assert.equal((await raw(media, {}, 'HEAD')).headers['content-length'], String(audio.body.length));
  const range = await raw(media, {Range: 'bytes=0-3'});
  assert.equal(range.status, 206); assert.equal(range.body.toString(), 'RIFF');
  assert.equal((await raw(`/media/${id}/section-000000.wav`)).status, 200);
  assert.equal((await raw(`/media/${id}/section-000001.wav`)).status, 404);
  assert.equal((await raw('/media/' + '0'.repeat(32) + '.wav')).status, 404);
  assert.equal((await raw('/', {Host: 'foreign.invalid'})).status, 403);
  assert.equal((await raw('/%2e%2e/library.sqlite3')).status, 403);
  assert.equal((await raw('/', {}, 'POST')).status, 501);
  result.checks.push('Raw known-ID GET, HEAD, Range and published section work; unknown/unpublished/Host/traversal/POST reject.');
  browser = await chromium.launch({headless: true, executablePath: process.env.BROWSER_EXECUTABLE || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
  const local = await browser.newPage(); await local.goto(origin);
  result.browser.local = await local.evaluate(async media => {
    const response = await fetch(media); const bytes = await response.arrayBuffer();
    const audio = new Audio(media); audio.muted = true; await audio.play();
    await new Promise(resolve => setTimeout(resolve, 200)); const time = audio.currentTime; audio.pause();
    return {status: response.status, bytes: bytes.byteLength, playback_advanced: time > 0};
  }, media);
  assert.equal(result.browser.local.status, 200); assert(result.browser.local.playback_advanced);
  const outside = await browser.newPage(); await outside.goto(foreign);
  result.browser.foreign = await outside.evaluate(async url => {
    let readable = false;
    try { readable = (await (await fetch(url)).arrayBuffer()).byteLength > 0; } catch {}
    const media = await new Promise(resolve => {
      const audio = new Audio(url); audio.muted = true;
      const timer = setTimeout(() => {audio.pause(); resolve({timeout: true});}, 4000);
      audio.onloadedmetadata = () => {clearTimeout(timer); resolve({loaded: true});};
      audio.onerror = () => {clearTimeout(timer); resolve({blocked: true, code: audio.error?.code});};
      audio.load();
    });
    return {readable, media};
  }, origin + media);
  assert.equal(result.browser.foreign.readable, false);
  assert.equal(result.browser.foreign.media.blocked, true);
  const denied = [];
  outside.on('requestfailed', request => denied.push({url: request.url(), failure: request.failure()?.errorText}));
  await outside.evaluate(url => {const frame = document.createElement('iframe'); frame.src = url; document.body.append(frame);}, origin);
  await outside.waitForTimeout(700);
  result.browser.frame_failures = denied;
  assert(denied.some(item => item.url.startsWith(origin) && /BLOCKED|ABORTED/.test(item.failure || '')), 'Framing was not observed blocked.');
  result.checks.push('App-origin fetch/playback work; controlled foreign fetch, valid audio embedding and framing are blocked.');
  result.success = true;
})().catch(error => {result.error = error.stack; process.exitCode = 1;}).finally(async () => {
  if (browser) await browser.close();
  fs.writeFileSync(output, JSON.stringify(result, null, 2)); console.log(JSON.stringify(result));
});
