// Headless UI checks with the production CSP, actual pywebview JS and fixtures.
// Native IPC is verified separately by native-startup-check.py.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium } = require(process.env.LILT_PLAYWRIGHT || 'playwright');
const root = path.resolve(__dirname, '..');
const assets = path.join(root, 'frontend/dist');
const methods = [...fs.readFileSync(path.join(root, 'backend/bridge.py'), 'utf8').matchAll(/^    def ([a-z]\w*)\(/gm)].map(match => ({func: match[1], params: []}));
const base = fs.readFileSync(path.join(root, '.venv/Lib/site-packages/webview/js/api.js'), 'utf8').replaceAll('%(platform)s', 'edgechromium');
const bridge = base + '\n' + fs.readFileSync(path.join(root, 'assets/desktop-api.js'), 'utf8') + '\nwindow.pywebview._createApi(' + JSON.stringify(methods) + ');window.dispatchEvent(new CustomEvent("pywebviewready"));';
const wave = Buffer.alloc(44 + 24000 * 2 * 12);
wave.write('RIFF'); wave.writeUInt32LE(wave.length - 8, 4); wave.write('WAVEfmt ', 8); wave.writeUInt32LE(16, 16); wave.writeUInt16LE(1, 20); wave.writeUInt16LE(1, 22); wave.writeUInt32LE(24000, 24); wave.writeUInt32LE(48000, 28); wave.writeUInt16LE(2, 32); wave.writeUInt16LE(16, 34); wave.write('data', 36); wave.writeUInt32LE(wave.length - 44, 40);
const server = http.createServer((request, response) => {
  const route = new URL(request.url, 'http://localhost').pathname;
  if (route === '/__bridge.js') { response.setHeader('Content-Type', 'text/javascript'); response.end(bridge); return; }
  if (route.startsWith('/media/')) { response.setHeader('Content-Type', 'audio/wav'); response.end(wave); return; }
  const file = path.resolve(assets, route === '/' ? 'index.html' : '.' + route);
  if (!file.startsWith(assets + path.sep) || !fs.existsSync(file)) { response.writeHead(404); response.end(); return; }
  response.setHeader('Content-Type', file.endsWith('.js') ? 'text/javascript' : file.endsWith('.css') ? 'text/css' : file.endsWith('.png') ? 'image/png' : 'text/html');
  response.end(fs.readFileSync(file));
});

(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const url = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch({channel: 'msedge', headless: true, args: ['--disable-gpu']});
  const reports = [];
  try {
    for (const scenario of ['normal', 'late-bridge', 'stalled-state', 'missing-bridge', 'empty-library']) {
      const page = await browser.newPage({viewport: {width: 1440, height: 960}});
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.addInitScript(scenario => {
        window.__stall = scenario === 'stalled-state';
        window.__calls = {};
        window.pywebview = {api: {}}; // An empty object must not count as ready.
        const docs = [{id: 'first', title: 'The art of paying attention', markdown: '# The art of paying attention\n\nA quiet thought.', created: 1, opened: 10, words: 120, source: 'C:/notes/attention.md'}, {id: 'second', title: 'A slower kind of morning', markdown: '# A slower kind of morning\n\nYour next sentence is waiting.', created: 2, opened: 20, words: 230}];
        const job = {id: '0123456789abcdef0123456789abcdef', document_id: 'first', title: docs[0].title, voice: 'af_heart', speed: 1, words: 120, preview: false, state: 'completed', completed: 1, total: 1, duration: 12, available_duration: 12, position: 3, created: 1, message: 'Ready'};
        const state = {documents: scenario === 'empty-library' ? [] : docs, jobs: scenario === 'empty-library' ? [] : [job], active: null, model: {state: 'ready', percent: 100, message: 'Ready', voices: ['af_heart']}, settings: {palette: 'lilt', theme: 'light'}, storage: 'C:/test/Lilt', performance: null, cache: {count: 0, bytes: 0, limit_mb: 256}};
        window.chrome ||= {};
        window.chrome.webview = {postMessage: ([name, params, id]) => {
          window.__calls[name] = (window.__calls[name] || 0) + 1;
          if (name === 'get_state' && window.__stall) return;
          const args = JSON.parse(params);
          let result;
          switch (name) {
            case 'get_state': result = state; break;
            case 'get_document': result = docs.find(doc => doc.id === args[0]); result.opened = Date.now() / 1000; state.documents.sort((a, b) => b.opened - a.opened); break;
            case 'prepare_document': result = {title: 'Reading', text: args[0], words: 10, chunks: [], omissions: {code_blocks: 0, metadata: 0}}; break;
            case 'save_position': job.position = args[1]; result = true; break;
            case 'save_settings': state.settings = args[0]; result = args[0]; break;
            case 'import_document': result = null; break;
            case 'export_recording': result = 'C:/test/export.wav'; break;
            case 'new_document': result = {id: 'new', title: 'Untitled reading', markdown: '# Untitled reading', created: Date.now() / 1000}; state.documents.unshift(result); break;
            default: result = true;
          }
          queueMicrotask(() => window.pywebview._returnValuesCallbacks[name][id]({value: JSON.stringify(result)}));
        }};
        if (scenario !== 'missing-bridge') setTimeout(() => { const script = document.createElement('script'); script.src = '/__bridge.js'; document.head.append(script); }, scenario === 'late-bridge' ? 4500 : 200);
      }, scenario);
      await page.goto(url);
      if (['stalled-state', 'missing-bridge'].includes(scenario)) {
        await page.getByRole('button', {name: 'Retry connection'}).waitFor({timeout: 25000});
        assert.equal(await page.locator('.home-page').count(), 0);
        assert.equal(await page.locator('.preview-label').count(), 0);
        await page.evaluate(() => {
          window.__stall = false;
          if (typeof window.pywebview.api.get_state !== 'function') { const script = document.createElement('script'); script.src = '/__bridge.js'; document.head.append(script); }
        });
        await page.getByRole('button', {name: 'Retry connection'}).click();
      }
      await page.locator('.home-page').waitFor({timeout: 25000});
      assert.equal(await page.locator('.preview-label').count(), 0);
      assert.equal(await page.locator('.recent-reading').count(), scenario === 'empty-library' ? 0 : 2);
      assert.equal(await page.locator('.saved-reading').count(), scenario === 'empty-library' ? 0 : 1);
      if (scenario === 'normal') {
        await page.getByRole('button', {name: 'Continue listening', exact: true}).click();
        await page.waitForFunction(() => !document.querySelector('audio').paused && document.querySelector('audio').currentTime > 3.2);
        await page.getByTitle('Pause', {exact: true}).click();
        await page.getByRole('button', {name: /Export .* as WAV/}).click();
        assert.equal(await page.evaluate(() => window.__calls.export_recording), 1);
        await page.locator('.recent-reading').last().click();
        await page.locator('.studio-layout').waitFor();
        await page.getByRole('button', {name: 'Home', exact: true}).click();
        assert.match(await page.locator('.recent-reading').first().innerText(), /paying attention/);
        fs.mkdirSync(path.join(root, 'artifacts'), {recursive: true});
        await page.screenshot({path: path.join(root, 'artifacts/home-light.png')});
        await page.setViewportSize({width: 1024, height: 681});
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        assert(await page.getByRole('button', {name: 'Continue listening', exact: true}).isVisible());
        await page.screenshot({path: path.join(root, 'artifacts/home-small.png')});
        await page.setViewportSize({width: 1440, height: 960});
        await page.getByRole('button', {name: 'Settings', exact: true}).click();
        await page.getByRole('button', {name: /After hours/}).click();
        await page.getByRole('button', {name: 'Home', exact: true}).click();
        await page.locator('.app-shell.dark').waitFor();
        await page.screenshot({path: path.join(root, 'artifacts/home-dark.png')});
        await page.getByRole('button', {name: 'New reading', exact: true}).click();
        await page.getByLabel('Markdown editor').waitFor();
      }
      assert.deepEqual(errors, [], scenario + ' page errors');
      reports.push({scenario, success: true});
      await page.close();
    }
    console.log(JSON.stringify(reports));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; }).finally(() => server.close());
