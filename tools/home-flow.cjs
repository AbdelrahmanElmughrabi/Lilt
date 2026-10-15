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
    for (const scenario of (process.argv.length > 2 ? process.argv.slice(2) : ['normal', 'late-bridge', 'stalled-state', 'missing-bridge', 'empty-library', 'file-actions', 'drop-files'])) {
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
        window.__state = state;
        window.chrome ||= {};
        window.chrome.webview = {postMessage: ([name, params, id]) => {
          window.__calls[name] = (window.__calls[name] || 0) + 1;
          if (name === 'get_state' && window.__stall) return;
          const args = JSON.parse(params);
          if (window.__fail === name) {
            queueMicrotask(() => window.pywebview._returnValuesCallbacks[name][id]({isError: true, value: JSON.stringify({message: 'Test file action failed.', name: 'ValueError', stack: ''})}));
            return;
          }
          let result;
          switch (name) {
            case 'get_state': result = state; break;
            case 'get_document': result = docs.find(doc => doc.id === args[0]); result.opened = Date.now() / 1000; state.documents.sort((a, b) => b.opened - a.opened); break;
            case 'prepare_document': result = {title: 'Reading', text: args[0], words: 10, chunks: [], omissions: {code_blocks: 0, metadata: 0}}; break;
            case 'save_document': { const doc = docs.find(doc => doc.id === args[0]); doc.markdown = args[1]; result = doc; break; }
            case 'save_position': job.position = args[1]; result = true; break;
            case 'save_settings': state.settings = args[0]; result = args[0]; break;
            case 'remove_document': state.documents = state.documents.filter(doc => doc.id !== args[0]); result = true; break;
            case 'remove_recording': state.jobs = state.jobs.filter(job => job.id !== args[0]); result = true; break;
            case 'reveal_document': window.__revealed = args[0]; result = true; break;
            case 'reveal_recording': window.__revealed = args[0]; result = true; break;
            case 'import_document': result = null; break;
            case 'export_recording': result = 'C:/test/export.wav'; break;
            case 'new_document': result = {id: 'new', title: 'Untitled reading', markdown: '# Untitled reading', created: Date.now() / 1000}; state.documents.unshift(result); break;
            default: result = true;
          }
          queueMicrotask(() => window.pywebview._returnValuesCallbacks[name][id]({value: JSON.stringify(result)}));
        }};
        window.chrome.webview.postMessageWithAdditionalObjects = async (message, files) => {
          window.__dropCalls = (window.__dropCalls || 0) + 1;
          const result = {documents: [], errors: []};
          for (const file of files) {
            if (!/\.(md|markdown)$/i.test(file.name)) { result.errors.push({name: file.name, message: 'Choose a Markdown (.md or .markdown) file.'}); continue; }
            const markdown = await file.text();
            const doc = {id: 'drop-' + crypto.randomUUID(), title: markdown.match(/^#\s+(.+)$/m)?.[1] || file.name, markdown, created: Date.now() / 1000, source: 'C:/test/' + file.name};
            result.documents.push(doc); docs.push(doc);
          }
          state.documents = [...docs];
          window.pywebview._returnValuesCallbacks.import_dropped_documents[message.id]({value: JSON.stringify(result)});
        };
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
        // Existing entries expose the same menu without opening the reading.
        const menu = page.getByRole('menu');
        await page.locator('.recent-reading').last().click({button: 'right'});
        assert.equal(await menu.getByRole('menuitem').count(), 2);
        assert.equal(await page.locator('.studio-layout').count(), 0);
        await menu.getByRole('menuitem', {name: 'Show in File Explorer'}).click();
        assert.equal(await page.evaluate(() => window.__revealed), 'first', JSON.stringify({errors, banner: await page.locator('.error-banner').allTextContents(), calls: await page.evaluate(() => window.__calls)}));
        await page.locator('.recent-reading').first().focus();
        await page.keyboard.press('Shift+F10');
        assert(await menu.getByRole('menuitem', {name: 'Show in File Explorer'}).isDisabled());
        await page.keyboard.press('Escape');
        assert.equal(await menu.count(), 0);
        assert(await page.locator('.recent-reading').first().evaluate(el => el === document.activeElement));
        for (const selector of ['.saved-reading', '.listen-card']) {
          await page.locator(selector).click({button: 'right'});
          await menu.getByRole('menuitem', {name: 'Show in File Explorer'}).click();
          assert.equal(await page.evaluate(() => window.__revealed), '0123456789abcdef0123456789abcdef');
        }
        await page.locator('.document-list > button').first().click({button: 'right'});
        await page.getByRole('heading', {name: 'Bring your words.'}).click();
        assert.equal(await menu.count(), 0);
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
        // Removing a different document keeps the current editor and selection.
        const editor = page.getByLabel('Markdown editor');
        const before = await editor.inputValue();
        await page.locator('.document-list > button').filter({hasText: 'A slower kind of morning'}).click({button: 'right'});
        await menu.getByRole('menuitem', {name: 'Delete…'}).click();
        await page.getByRole('dialog').filter({hasText: 'Remove this reading?'}).getByRole('button', {name: 'Remove', exact: true}).click();
        await page.waitForFunction(() => document.querySelectorAll('.document-list > button').length === 2);
        assert.equal(await editor.inputValue(), before);
        // Canceling from a card must preserve the recording.
        await page.getByRole('button', {name: 'Your recordings'}).click();
        await page.locator('.recording-card').click({button: 'right'});
        await menu.getByRole('menuitem', {name: 'Delete…'}).click();
        await page.getByRole('button', {name: 'Keep it', exact: true}).click();
        assert.equal(await page.locator('.recording-card').count(), 1);
        // Delete the selected recording and release its player.
        await page.locator('.recording-card').click({button: 'right'});
        await menu.getByRole('menuitem', {name: 'Delete…'}).click();
        await page.getByRole('dialog').filter({hasText: 'Remove this recording?'}).getByRole('button', {name: 'Remove', exact: true}).click();
        await page.waitForFunction(() => document.querySelectorAll('.recording-card').length === 0);
        assert(await page.getByTitle('Export recording', {exact: true}).isDisabled());
        // Remove the open document and then the final remaining document.
        await page.getByRole('button', {name: 'Reading room', exact: true}).click();
        for (let remaining = 1; remaining >= 0; remaining--) {
          await page.locator('.document-list > button.chosen').click({button: 'right'});
          await menu.getByRole('menuitem', {name: 'Delete…'}).click();
          await page.getByRole('dialog').filter({hasText: 'Remove this reading?'}).getByRole('button', {name: 'Remove', exact: true}).click();
          await page.waitForFunction(count => document.querySelectorAll('.document-list > button').length === count, remaining);
        }
        assert.equal(await page.locator('.document-list > button').count(), 0);
      }
      if (scenario === 'file-actions') {
        const menu = page.getByRole('menu');
        await page.evaluate(() => {
          window.__state.jobs.push({...window.__state.jobs[0], id: 'unfinished', title: 'Unfinished test', state: 'cancelled'});
        });
        await page.locator('.unfinished-row').waitFor();
        await page.locator('.unfinished-row').click({button: 'right'});
        await menu.getByRole('menuitem', {name: 'Show in File Explorer'}).click();
        assert.equal(await page.evaluate(() => window.__revealed), 'unfinished');
        await page.locator('.unfinished-row').click({button: 'right'});
        await menu.getByRole('menuitem', {name: 'Delete…'}).click();
        await page.getByRole('dialog').getByRole('button', {name: 'Remove', exact: true}).click();
        await page.waitForFunction(() => !document.querySelector('.unfinished-row'));
        await page.evaluate(() => { window.__fail = 'reveal_document'; });
        await page.locator('.recent-reading').last().click({button: 'right'});
        await menu.getByRole('menuitem', {name: 'Show in File Explorer'}).click();
        await page.getByRole('alert').filter({hasText: 'Test file action failed.'}).waitFor();
        await page.evaluate(() => { window.__fail = 'remove_recording'; });
        await page.locator('.saved-reading').click({button: 'right'});
        await menu.getByRole('menuitem', {name: 'Delete…'}).click();
        await page.getByRole('dialog').getByRole('button', {name: 'Remove', exact: true}).click();
        await page.getByRole('alert').filter({hasText: 'Test file action failed.'}).waitFor();
        assert.equal(await page.locator('.saved-reading').count(), 1);
        assert(!(await page.getByTitle('Export recording', {exact: true}).isDisabled()));
        await page.getByRole('button', {name: 'Keep it', exact: true}).click();
        await page.evaluate(() => { window.__fail = ''; window.__state.jobs[0].state = 'generating'; });
        await page.getByRole('button', {name: 'Your recordings'}).click();
        await page.locator('.recording-card .spin').waitFor();
        await page.locator('.recording-card').click({button: 'right'});
        assert(await menu.getByRole('menuitem', {name: 'Delete…'}).isDisabled());
        await page.keyboard.press('Escape');
        // Menus clamp to the viewport and follow the active palette.
        await page.setViewportSize({width: 1024, height: 720});
        await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
        await page.locator('.recording-card').evaluate(el => el.dispatchEvent(new MouseEvent('contextmenu', {clientX: 1020, clientY: 716, bubbles: true, cancelable: true})));
        await page.waitForFunction(() => {
          const r = document.querySelector('[role=menu]')?.getBoundingClientRect();
          return r && r.left > 0 && r.top > 0 && r.right <= innerWidth && r.bottom <= innerHeight;
        });
        fs.mkdirSync(path.join(root, 'artifacts'), {recursive: true});
        await menu.waitFor();
        await page.screenshot({path: path.join(root, 'artifacts/file-context-menu-light.png')});
        assert.equal(await menu.count(), 1);
        await page.keyboard.press('Escape');
        await page.setViewportSize({width: 1440, height: 960});
        await page.getByRole('button', {name: 'Settings', exact: true}).click();
        await page.getByRole('button', {name: /After hours/}).click();
        await page.getByRole('button', {name: 'Home', exact: true}).click();
        await page.locator('.app-shell.dark').waitFor();
        await page.locator('.recent-reading').last().click({button: 'right'});
        await menu.waitFor();
        await page.screenshot({path: path.join(root, 'artifacts/file-context-menu-dark.png')});
        assert.equal(await menu.count(), 1);
        await page.setViewportSize({width: 1100, height: 760});
        await page.waitForFunction(() => !document.querySelector('[role=menu]'));
      }
      if (scenario === 'drop-files') {
        const overlay = page.locator('.file-drop-overlay');
        async function drag(type, files = [{name: 'new.md', text: '# Dropped reading'}], selector = '.app-shell') {
          return page.evaluate(({type, files, selector}) => {
            const transfer = new DataTransfer();
            for (const file of files) transfer.items.add(new File([file.text], file.name, {type: 'text/markdown'}));
            return document.querySelector(selector).dispatchEvent(new DragEvent(type, {dataTransfer: transfer, bubbles: true, cancelable: true}));
          }, {type, files, selector});
        }
        // Ordinary editor/text drags do not trigger the file affordance.
        await page.evaluate(() => { const d = new DataTransfer(); d.setData('text/plain', 'hello'); window.dispatchEvent(new DragEvent('dragenter', {dataTransfer: d})); });
        assert(!(await overlay.isVisible()));
        for (const palette of ['lilt', 'classic']) {
          for (const appearance of ['light', 'dark']) {
            await page.getByRole('button', {name: 'Settings', exact: true}).click();
            await page.getByRole('group', {name: 'Theme palette'}).getByRole('button', {name: palette === 'lilt' ? /Lilt/ : /Classic/}).click();
            await page.getByRole('button', {name: appearance === 'light' ? /Daylight/ : /After hours/}).click();
            await drag('dragenter');
            await overlay.waitFor({state: 'visible'});
            await page.waitForFunction(() => getComputedStyle(document.querySelector('.file-drop-overlay')).opacity === '1');
            const colors = await overlay.evaluate(el => ({ink: getComputedStyle(el).color, inherited: getComputedStyle(document.querySelector('.app-shell')).color}));
            assert.equal(colors.ink, colors.inherited);
            const accent = await page.locator('.file-drop-overlay h2 em').evaluate(el => ({actual: getComputedStyle(el).color, expected: getComputedStyle(el).getPropertyValue('--accent').trim()}));
            assert.equal(accent.actual, await page.evaluate(color => { const el = document.createElement('span'); el.style.color = color; document.body.append(el); const normalized = getComputedStyle(el).color; el.remove(); return normalized; }, accent.expected));
            assert(await overlay.evaluate(el => el.matches(':popover-open')));
            fs.mkdirSync(path.join(root, 'artifacts'), {recursive: true});
            await page.screenshot({path: path.join(root, `artifacts/drop-${palette}-${appearance}.png`)});
            await drag('dragleave');
            assert(!(await overlay.isVisible()));
          }
        }
        await page.emulateMedia({reducedMotion: 'reduce'});
        await drag('dragenter');
        assert.equal(await page.locator('.paper-front').evaluate(el => getComputedStyle(el).animationName), 'none');
        await drag('dragleave');
        await page.getByRole('button', {name: 'Home', exact: true}).click();
        // One native-style batch adds both readings; invalid files get a clear error.
        const batch = [{name: 'one.md', text: '# One dropped reading'}, {name: 'two.markdown', text: '# Two dropped readings'}, {name: 'photo.png', text: 'image'}];
        assert.equal(await drag('drop', batch, '.home-page'), false);
        await page.locator('.studio-layout').waitFor();
        await page.waitForFunction(() => document.querySelectorAll('.document-list > button').length === 4);
        assert(await page.locator('.reading-article').innerText().then(text => text.includes('One dropped reading')));
        assert((await page.getByRole('alert').innerText()).includes('photo.png'));
        assert.equal(await page.evaluate(() => window.__dropCalls), 1);
        // Files dropped on the editor import as readings and preserve its pending save.
        await page.getByRole('button', {name: 'Edit', exact: true}).click();
        await page.getByLabel('Markdown editor').fill('# Keep my edits');
        await drag('drop', [{name: 'three.md', text: '# Third dropped reading'}], '.markdown-editor');
        await page.waitForFunction(() => document.querySelectorAll('.document-list > button').length === 5);
        assert.equal(await page.evaluate(() => window.__calls.save_document), 1);
        assert(await page.evaluate(() => window.__state.documents.some(doc => doc.markdown === '# Keep my edits')));
        await drag('dragenter', undefined, '.sidebar');
        await page.evaluate(() => window.dispatchEvent(new Event('blur')));
        assert(!(await overlay.isVisible()));
        const url = page.url();
        await drag('drop', [{name: 'unsupported.wav', text: 'audio'}]);
        await page.getByRole('alert').filter({hasText: 'unsupported.wav'}).waitFor();
        assert.equal(page.url(), url);
        assert.equal(await page.locator('.document-list > button').count(), 5);
      }
      assert.deepEqual(errors, [], scenario + ' page errors');
      reports.push({scenario, success: true});
      await page.close();
    }
    console.log(JSON.stringify(reports));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; }).finally(() => server.close());
