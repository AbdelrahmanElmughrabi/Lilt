/**
 * Built-frontend regressions with a disposable in-memory desktop API.
 * Build frontend first. Uses existing Playwright/Edge; no app/test installation.
 * Set PLAYWRIGHT_MODULE to an existing Playwright module and optionally
 * BROWSER_EXECUTABLE to an existing Chromium/Edge executable, then run:
 * node --test tests/test_editor_save.cjs
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const {test, before, after} = require('node:test');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const assets = path.resolve(__dirname, '../frontend/dist');
const contentTypes = {'.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png'};
let browser, server, origin;

before(async () => {
  assert(fs.existsSync(path.join(assets, 'index.html')), 'Build frontend before running browser regressions.');
  server = http.createServer((request, response) => {
    const requested = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
    const file = path.resolve(assets, '.' + (requested === '/' ? '/index.html' : requested));
    if (!file.startsWith(assets + path.sep)) return response.writeHead(403).end();
    try {
      response.writeHead(200, {'Content-Type': contentTypes[path.extname(file)] || 'application/octet-stream'});
      response.end(fs.readFileSync(file));
    } catch { response.writeHead(404).end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  origin = `http://127.0.0.1:${server.address().port}`;
  browser = await chromium.launch({headless: true, executablePath: process.env.BROWSER_EXECUTABLE ||
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
});

after(async () => {
  if (browser) await browser.close();
  if (server) await new Promise(resolve => server.close(resolve));
});

async function fixture(t) {
  const page = await browser.newPage({viewport: {width: 1280, height: 900}});
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  t.after(async () => { await page.close(); assert.deepEqual(errors, [], 'Unexpected browser errors'); });
  await page.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
  await page.addInitScript(() => {
    const documents = [
      {id: 'doc-a', title: 'Disposable reading', markdown: 'Original reading.', created: 1},
      {id: 'doc-b', title: 'Other reading', markdown: 'Other document.', created: 2},
    ];
    const settings = {palette: 'violilt', theme: 'light', voice: 'af_heart', speed: 1, include_code: false,
      heading_pause: 0.6, paragraph_pause: 0.3, performance_mode: 'balanced', cpu_threads: 0,
      processing_device: 'auto', gpu_device: -1, buffer_mode: 'balanced', auto_listen: false,
      warm_start: false, model_release: 'idle', cache_enabled: true, cache_limit_mb: 256};
    const controls = window.saveFixture = {documents, events: [], saves: [], preparations: [], generated: [],
      holdSave: false, holdReview: false, failSave: false, failState: false, holdState: false, closeMessages: []};
    window.chrome ||= {};
    window.chrome.webview = {postMessage: message => controls.closeMessages.push(message)};
    const prepared = text => ({title: 'Disposable reading', text, words: text.split(/\s+/).filter(Boolean).length,
      chunks: [{text, pause: 0.3, block: 0}], omissions: {code_blocks: 0, metadata: 0}, unread_count: 0});
    window.pywebview = {api: {
      get_state: async () => {
        if (controls.failState) throw new Error('Disposable refresh failure; document storage is healthy.');
        if (controls.holdState) await new Promise(resolve => controls.releaseState = resolve);
        return {documents: structuredClone(documents), jobs: [], active: null,
        model: {state: 'ready', percent: 100, message: 'Fixture only', voices: ['af_heart']},
        settings, storage: 'Disposable fixture', performance: null, cache: controls.cache || {count: 0, bytes: 0, limit_mb: 256}};
      },
      get_document: async id => structuredClone(documents.find(doc => doc.id === id)),
      save_document: async (id, markdown) => {
        controls.events.push(['save-start', id, markdown]);
        controls.saves.push({id, markdown});
        if (controls.holdSave) await new Promise(resolve => controls.releaseSave = resolve);
        if (controls.failSave) throw new Error('Disposable save failure; retry.');
        const doc = documents.find(doc => doc.id === id);
        doc.markdown = markdown;
        controls.events.push(['save-finish', id, markdown]);
        return structuredClone(doc);
      },
      prepare_document: async text => {
        controls.preparations.push(text);
        if (controls.holdReview) {
          controls.holdReview = false;
          await new Promise(resolve => controls.releaseReview = resolve);
        }
        controls.events.push(['review', text]);
        return prepared(text);
      },
      save_settings: async value => value,
      generate: async (id, markdown) => {
        controls.generated.push({id, markdown});
        controls.events.push(['generate', id, markdown]);
        throw new Error('Generation captured by disposable fixture.');
      },
      save_position: async () => true,
    }};
  });
  await page.goto(origin);
  await page.locator('.document-list button').filter({hasText: 'Disposable reading'}).click();
  await page.locator('.reading-article').waitFor();
  await page.getByRole('button', {name: 'Edit', exact: true}).click();
  await page.clock.install();
  await page.clock.pauseAt(new Date());
  return page;
}

const editor = page => page.getByRole('textbox', {name: 'Markdown editor', exact: true});
const state = page => page.evaluate(() => ({documents: window.saveFixture.documents, saves: window.saveFixture.saves,
  preparations: window.saveFixture.preparations, generated: window.saveFixture.generated, events: window.saveFixture.events}));
async function spoken(page) {
  await page.getByRole('button', {name: 'Spoken', exact: true}).click();
  return page.locator('.spoken-text').innerText();
}
async function settle(page, condition) {
  await page.waitForFunction(condition);
}

test('Ctrl+S saves and refreshes Spoken before the pending autosave fires', async t => {
  const page = await fixture(t);
  await editor(page).fill('Manual save must be spoken.');
  await page.keyboard.press('Control+s');
  await settle(page, () => window.saveFixture.documents[0].markdown === 'Manual save must be spoken.');
  assert.equal(await spoken(page), 'Manual save must be spoken.');
  await page.clock.runFor(6000);
  assert.equal((await state(page)).saves.length, 1, 'Manual save cancels both pending timers');
});

test('idle autosave waits one second after the last edit and refreshes Spoken', async t => {
  const page = await fixture(t);
  await editor(page).fill('First draft.');
  await page.clock.runFor(900);
  assert.equal((await state(page)).saves.length, 0);
  await editor(page).fill('Latest idle draft.');
  await page.clock.runFor(999);
  assert.equal((await state(page)).saves.length, 0);
  await page.clock.runFor(1);
  await settle(page, () => window.saveFixture.documents[0].markdown === 'Latest idle draft.');
  assert.equal(await spoken(page), 'Latest idle draft.');
});

test('continuous typing saves at five seconds even without an idle gap', async t => {
  const page = await fixture(t);
  for (let index = 0; index < 10; index++) {
    await editor(page).fill(`Continuous draft ${index}.`);
    await page.clock.runFor(500);
  }
  await settle(page, () => window.saveFixture.saves.length >= 1);
  assert.equal((await state(page)).documents[0].markdown, 'Continuous draft 9.');
  await editor(page).fill('The final idle draft.');
  await page.clock.runFor(1000);
  await settle(page, () => window.saveFixture.documents[0].markdown === 'The final idle draft.');
  assert.equal(await spoken(page), 'The final idle draft.');
});

test('Saved is not shown while the backend write is pending', async t => {
  const page = await fixture(t);
  await page.evaluate(() => window.saveFixture.holdSave = true);
  await editor(page).fill('Pending write.');
  await page.keyboard.press('Control+s');
  await settle(page, () => typeof window.saveFixture.releaseSave === 'function');
  assert.match(await page.locator('.reading-meta').innerText(), /Saving changes/);
  await page.evaluate(() => {window.saveFixture.holdSave = false; window.saveFixture.releaseSave();});
  await settle(page, () => window.saveFixture.documents[0].markdown === 'Pending write.');
  assert.equal(await spoken(page), 'Pending write.');
  assert.match(await page.locator('.reading-meta').innerText(), /Saved to your shelf/);
});

test('edits made during a pending write remain intact and are saved in order', async t => {
  const page = await fixture(t);
  await page.evaluate(() => window.saveFixture.holdSave = true);
  await editor(page).fill('Earlier snapshot.');
  await page.keyboard.press('Control+s');
  await settle(page, () => typeof window.saveFixture.releaseSave === 'function');
  await editor(page).fill('Newer snapshot.');
  await page.keyboard.press('Control+s');
  await page.evaluate(() => {window.saveFixture.holdSave = false; window.saveFixture.releaseSave();});
  await settle(page, () => window.saveFixture.documents[0].markdown === 'Newer snapshot.');
  assert.equal(await editor(page).inputValue(), 'Newer snapshot.');
  assert.equal(await spoken(page), 'Newer snapshot.');
  assert.deepEqual((await state(page)).saves.map(save => save.markdown), ['Earlier snapshot.', 'Newer snapshot.']);
});

test('a late preparation result cannot replace text prepared after a newer edit', async t => {
  const page = await fixture(t);
  await page.evaluate(() => window.saveFixture.holdReview = true);
  await editor(page).fill('An outdated preview.');
  await page.clock.runFor(1000);
  await settle(page, () => typeof window.saveFixture.releaseReview === 'function');
  await editor(page).fill('Newest preview.');
  await page.keyboard.press('Control+s');
  await settle(page, () => window.saveFixture.documents[0].markdown === 'Newest preview.');
  await page.evaluate(() => window.saveFixture.releaseReview());
  assert.equal(await spoken(page), 'Newest preview.');
});

test('a failed save keeps the edit and a successful Ctrl+S retry updates Spoken', async t => {
  const page = await fixture(t);
  await page.evaluate(() => window.saveFixture.failSave = true);
  await editor(page).fill('An edit worth keeping.');
  await page.keyboard.press('Control+s');
  await page.getByRole('alert').filter({hasText: 'Disposable save failure'}).waitFor();
  assert.equal((await state(page)).documents[0].markdown, 'Original reading.');
  assert.equal(await editor(page).inputValue(), 'An edit worth keeping.');
  await page.evaluate(() => window.saveFixture.failSave = false);
  await page.keyboard.press('Control+s');
  await settle(page, () => window.saveFixture.documents[0].markdown === 'An edit worth keeping.');
  assert.equal(await spoken(page), 'An edit worth keeping.');
  assert.equal(await page.getByRole('alert').count(), 0);
});

test('document navigation persists pending edits before opening another reading', async t => {
  const page = await fixture(t);
  await editor(page).fill('Saved before navigation.');
  await page.locator('.document-list button').filter({hasText: 'Other reading'}).click();
  await page.locator('.reading-article').filter({hasText: 'Other document.'}).waitFor();
  assert.equal((await state(page)).documents[0].markdown, 'Saved before navigation.');
  await page.locator('.document-list button').filter({hasText: 'Disposable reading'}).click();
  assert.equal(await spoken(page), 'Saved before navigation.');
});

test('Generate waits for pending saves and receives the latest edited text', async t => {
  const page = await fixture(t);
  await page.evaluate(() => window.saveFixture.holdSave = true);
  await editor(page).fill('Latest generation input.');
  await page.keyboard.press('Control+s');
  await settle(page, () => typeof window.saveFixture.releaseSave === 'function');
  await page.locator('.generate-button').click();
  assert.equal((await state(page)).generated.length, 0);
  await page.evaluate(() => {window.saveFixture.holdSave = false; window.saveFixture.releaseSave();});
  await settle(page, () => window.saveFixture.generated.length === 1);
  const result = await state(page);
  assert.deepEqual(result.generated, [{id: 'doc-a', markdown: 'Latest generation input.'}]);
  assert(result.events.findIndex(event => event[0] === 'save-finish') < result.events.findIndex(event => event[0] === 'generate'));
});

async function requestClose(page, id = 'close123') {
  await page.evaluate(id => window.dispatchEvent(new CustomEvent('violilt:close-request', {detail: {id}})), id);
}
const closeReplies = page => page.evaluate(() => window.saveFixture.closeMessages.filter(message => message.type === 'violilt:close-response'));
const closed = page => settle(page, () => window.saveFixture.closeMessages.some(message => message.type === 'violilt:close-response' && message.saved));

test('failed refresh after durable save reports separately and close does not repeat the write', async t => {
  const page = await fixture(t);
  await page.evaluate(() => window.saveFixture.failState = true);
  await editor(page).fill('Durable despite failed refresh.');
  await page.keyboard.press('Control+s');
  await page.getByRole('alert').filter({hasText: 'Disposable refresh failure'}).waitFor();
  assert.equal((await state(page)).documents[0].markdown, 'Durable despite failed refresh.');
  await requestClose(page);
  await closed(page);
  assert.equal((await state(page)).saves.length, 1);
});

test('held refresh after durable save cannot hold close approval', async t => {
  const page = await fixture(t);
  await page.evaluate(() => window.saveFixture.holdState = true);
  await editor(page).fill('Durable despite held refresh.');
  await page.keyboard.press('Control+s');
  await settle(page, () => typeof window.saveFixture.releaseState === 'function');
  await requestClose(page);
  await closed(page);
  assert.equal((await state(page)).documents[0].markdown, 'Durable despite held refresh.');
  assert.equal((await state(page)).saves.length, 1);
  await page.evaluate(() => { window.saveFixture.holdState = false; window.saveFixture.releaseState(); });
});

test('unavailable cache shows its status instead of a successful zero-count scan and recovers', async t => {
  const page = await fixture(t);
  await page.evaluate(() => window.saveFixture.cache = {available: false, count: null, bytes: null, limit_mb: 256,
    message: 'Reusable audio could not be accessed. Readings can continue; your recordings are kept.'});
  await page.clock.runFor(900);
  await page.getByRole('button', {name: 'Settings', exact: true}).click();
  const card = page.locator('.performance-card');
  await card.getByRole('status').filter({hasText: 'Reusable audio could not be accessed'}).waitFor();
  assert.equal(await card.getByText('0 passages', {exact: false}).count(), 0);
  assert.equal(await card.getByRole('button', {name: 'Clear reusable audio'}).isDisabled(), true);
  await page.evaluate(() => window.saveFixture.cache = {available: true, count: 2, bytes: 1048576, limit_mb: 256, message: ''});
  await page.clock.runFor(900);
  await card.getByText('2 passages · 1.0 MB.', {exact: false}).waitFor();
  assert.equal(await card.getByRole('button', {name: 'Clear reusable audio'}).isDisabled(), false);
});

test('normal close saves the latest edit before its autosave timer and does not wait for Spoken preparation', async t => {
  const page = await fixture(t);
  await editor(page).fill('Saved by normal close.');
  await page.evaluate(() => window.saveFixture.holdReview = true);
  await requestClose(page);
  await closed(page);
  assert.equal((await state(page)).documents[0].markdown, 'Saved by normal close.');
  assert.equal((await state(page)).saves.length, 1);
  assert.deepEqual(await closeReplies(page), [{type: 'violilt:close-response', id: 'close123', saved: true}]);
});

test('normal close drains an in-flight save and the newer dirty snapshot in order', async t => {
  const page = await fixture(t);
  await page.evaluate(() => window.saveFixture.holdSave = true);
  await editor(page).fill('Earlier close snapshot.');
  await page.keyboard.press('Control+s');
  await settle(page, () => typeof window.saveFixture.releaseSave === 'function');
  await editor(page).fill('Latest close snapshot.');
  await requestClose(page);
  await page.getByRole('dialog', {name: 'Save before closing'}).waitFor();
  assert.deepEqual(await closeReplies(page), []);
  await page.evaluate(() => {window.saveFixture.holdSave = false; window.saveFixture.releaseSave();});
  await closed(page);
  assert.equal((await state(page)).documents[0].markdown, 'Latest close snapshot.');
  assert.deepEqual((await state(page)).saves.map(save => save.markdown), ['Earlier close snapshot.', 'Latest close snapshot.']);
});

test('failed normal-close save retains the editor and offers a successful retry', async t => {
  const page = await fixture(t);
  await page.evaluate(() => window.saveFixture.failSave = true);
  await editor(page).fill('Keep this failed-close edit.');
  await requestClose(page);
  await page.getByRole('dialog').getByRole('alert').filter({hasText: 'Disposable save failure'}).waitFor();
  assert.deepEqual(await closeReplies(page), []);
  assert.equal((await state(page)).documents[0].markdown, 'Original reading.');
  assert.equal(await editor(page).inputValue(), 'Keep this failed-close edit.');
  await page.evaluate(() => window.saveFixture.failSave = false);
  await page.getByRole('button', {name: 'Retry save and close', exact: true}).click();
  await closed(page);
  assert.equal((await state(page)).documents[0].markdown, 'Keep this failed-close edit.');
});

test('keeping editing cancels close approval even when its pending save later succeeds', async t => {
  const page = await fixture(t);
  await page.evaluate(() => window.saveFixture.holdSave = true);
  await editor(page).fill('Slow close save.');
  await requestClose(page);
  await settle(page, () => typeof window.saveFixture.releaseSave === 'function');
  await page.getByRole('button', {name: 'Keep editing', exact: true}).click();
  assert.deepEqual(await closeReplies(page), [{type: 'violilt:close-response', id: 'close123', saved: false}]);
  await editor(page).fill('Edit after cancelling close.');
  await page.evaluate(() => {window.saveFixture.holdSave = false; window.saveFixture.releaseSave();});
  await page.keyboard.press('Control+s');
  await settle(page, () => window.saveFixture.documents[0].markdown === 'Edit after cancelling close.');
  assert.equal((await closeReplies(page)).some(message => message.saved), false);
  await requestClose(page, 'close456');
  await closed(page);
  assert.equal((await closeReplies(page)).at(-1).id, 'close456');
});

test('a close save timeout stays recoverable and a late completion cannot close after cancellation', async t => {
  const page = await fixture(t);
  await page.evaluate(() => window.saveFixture.holdSave = true);
  await editor(page).fill('Timeout close edit.');
  await requestClose(page);
  await settle(page, () => typeof window.saveFixture.releaseSave === 'function');
  await page.clock.runFor(10000);
  await page.getByRole('dialog').getByRole('alert').filter({hasText: 'taking longer'}).waitFor();
  assert.deepEqual(await closeReplies(page), []);
  await page.keyboard.press('Escape');
  await page.getByRole('dialog').waitFor({state: 'hidden'});
  await page.evaluate(() => {window.saveFixture.holdSave = false; window.saveFixture.releaseSave();});
  await settle(page, () => window.saveFixture.documents[0].markdown === 'Timeout close edit.');
  assert.deepEqual(await closeReplies(page), [{type: 'violilt:close-response', id: 'close123', saved: false}]);
});

test('repeated close requests and save shortcuts cannot duplicate or bypass the close transaction', async t => {
  const page = await fixture(t);
  await page.evaluate(() => window.saveFixture.holdSave = true);
  await editor(page).fill('One close write.');
  await requestClose(page);
  await settle(page, () => typeof window.saveFixture.releaseSave === 'function');
  await requestClose(page);
  await page.keyboard.press('Control+s');
  await page.keyboard.press('Control+o');
  assert.equal((await state(page)).saves.length, 1);
  await page.evaluate(() => {window.saveFixture.holdSave = false; window.saveFixture.releaseSave();});
  await closed(page);
  assert.equal((await closeReplies(page)).length, 1);
});
