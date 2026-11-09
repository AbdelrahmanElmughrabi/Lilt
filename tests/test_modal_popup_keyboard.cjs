/** Focused built-UI regressions. Existing Playwright/Edge, fake API/media only.
 * R11_ASSETS selects preserved/current build; R11_EVIDENCE_DIR is a fresh folder.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const {test, before, after} = require('node:test');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assets = path.resolve(process.env.R11_ASSETS || path.join(__dirname, '../frontend/dist'));
const evidence = process.env.R11_EVIDENCE_DIR;
let browser, server, origin;
before(async () => {
  assert(fs.existsSync(path.join(assets, 'index.html')), 'Built frontend is required');
  if (evidence) fs.mkdirSync(evidence, {recursive: true});
  server = http.createServer((_request, response) => response.writeHead(404).end());
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  origin = `http://127.0.0.1:${server.address().port}`;
  try {
    browser = await chromium.launch({headless: true, executablePath: process.env.BROWSER_EXECUTABLE ||
      'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
  } catch (error) {
    await new Promise(resolve => server.close(resolve)); server = null; throw error;
  }
});
after(async () => {
  if (browser) await browser.close();
  if (server) await new Promise(resolve => server.close(resolve));
});

async function fixture(t, width = 1280) {
  const context = await browser.newContext({viewport: {width, height: 900}});
  const page = await context.newPage();
  page.setDefaultTimeout(5000);
  const errors = [], foreign = [];
  page.on('pageerror', error => errors.push(error.message));
  await context.route('**/*', route => {
    const url = new URL(route.request().url());
    if (url.origin !== origin) { foreign.push(url.href); return route.abort(); }
    if (url.pathname.startsWith('/media/')) return route.fulfill({status: 204, body: ''});
    const file = path.resolve(assets, '.' + (url.pathname === '/' ? '/index.html' : url.pathname));
    if (!file.startsWith(assets + path.sep)) return route.fulfill({status: 403, body: ''});
    try {
      return route.fulfill({status: 200, body: fs.readFileSync(file), contentType:
        ({'.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png'})[path.extname(file)] || 'application/octet-stream'});
    } catch { return route.fulfill({status: 404, body: ''}); }
  });
  t.after(async () => {
    await context.close();
    assert.deepEqual(errors, [], 'Page errors cannot pass');
    assert.deepEqual(foreign, [], 'Only exact local fixture assets are permitted');
  });
  await page.addInitScript(() => {
    const document = {id: 'reading', title: 'Synthetic reading', markdown: 'Original fixture text.', created: 1};
    const settings = {palette: 'violilt', theme: 'light', voice: 'af_heart', speed: 1, include_code: false,
      heading_pause: 0.6, paragraph_pause: 0.3, performance_mode: 'balanced', cpu_threads: 0,
      processing_device: 'cpu', gpu_device: -1, buffer_mode: 'balanced', auto_listen: false,
      warm_start: false, model_release: 'idle', cache_enabled: true, cache_limit_mb: 256};
    const job = {id: 'recording', document_id: 'reading', title: 'Synthetic recording', voice: 'af_heart',
      speed: 1, words: 3, preview: false, state: 'completed', completed: 1, total: 1,
      duration: 10, position: 0, message: '', created: 1};
    const controls = window.popupFixture = {document, settings, saves: [], settingsWrites: [], imports: 0,
      playCalls: 0, pauseCalls: 0, removals: 0, closeMessages: [], holdSave: false, handoffs: 0};
    HTMLMediaElement.prototype.play = function () { controls.playCalls++; return Promise.resolve(); };
    HTMLMediaElement.prototype.pause = function () { controls.pauseCalls++; };
    window.chrome ||= {};
    window.chrome.webview = {postMessage: message => controls.closeMessages.push(message)};
    window.pywebview = {api: {
      get_state: async () => ({documents: [structuredClone(document)], jobs: [job], active: null, settings, welcome_version: 1,
        model: {state: 'ready', percent: 100, message: 'Fixture only', voices: ['af_heart', 'bf_emma']},
        storage: 'Synthetic fixture', performance: null, cache: {count: 0, bytes: 0, limit_mb: 256}}),
      get_document: async () => structuredClone(document),
      save_document: async (_id, markdown) => {
        controls.saves.push(markdown);
        if (controls.holdSave) await new Promise(resolve => controls.releaseSave = resolve);
        document.markdown = markdown; return structuredClone(document);
      },
      prepare_document: async text => ({title: document.title, text, words: 3,
        chunks: [{text, pause: 0.3, block: 0}], omissions: {code_blocks: 0, metadata: 0}}),
      save_settings: async value => { controls.settingsWrites.push(value); Object.assign(settings, value); return value; },
      save_position: async () => true,
      import_document: async () => { controls.imports++; return null; },
      remove_document: async () => { controls.removals++; },
      open_microsoft_privacy: async () => true,
      generate: async () => { throw new Error('Real generation is outside this fixture'); },
    }};
  });
  await page.goto(origin);
  if (width <= 1090) await page.getByRole('button', {name: 'Toggle shelf', exact: true}).click();
  await reading(page).click();
  await page.locator('.reading-article').waitFor();
  await page.waitForFunction(() => window.document.querySelector('.play-button')?.disabled === false);
  await page.clock.install(); await page.clock.pauseAt(new Date());
  await page.evaluate(() => { window.popupFixture.playCalls = 0; window.popupFixture.pauseCalls = 0; });
  return page;
}
const reading = page => page.locator('.document-list button').filter({hasText: 'Synthetic reading'});
const editor = page => page.getByRole('textbox', {name: 'Markdown editor', exact: true});
async function edit(page, text = 'Dirty isolated fixture text.') {
  await page.getByRole('button', {name: 'Edit', exact: true}).click();
  await editor(page).fill(text);
  assert.deepEqual(await page.evaluate(() => window.popupFixture.saves), []);
}
async function openModal(page, kind) {
  if (kind === 'About') await page.getByRole('button', {name: 'About Violilt', exact: true}).click();
  else {
    await reading(page).focus(); await page.keyboard.press('Shift+F10');
    await page.getByRole('menuitem', {name: 'Delete…', exact: true}).click();
  }
  const dialog = page.getByRole('dialog', {name: kind === 'About' ? 'A little less rushing. A little more listening.' : 'Remove this reading?', exact: true});
  await dialog.waitFor(); assert.equal(await dialog.evaluate(el => el.open), true);
  return dialog;
}
async function voice(page) {
  await page.locator('.voice-selector').focus(); await page.keyboard.press('Enter');
  await page.locator('.voice-menu').waitFor(); await page.keyboard.press('Tab');
  assert.equal(await page.locator('.voice-menu').evaluate(el => el.contains(window.document.activeElement)), true);
}
async function shelf(page) {
  await page.getByRole('button', {name: 'Toggle shelf', exact: true}).click();
  await reading(page).focus();
  assert.equal(await page.locator('.sidebar').evaluate(el => el.classList.contains('opened') && el.contains(window.document.activeElement)), true);
}
async function observe(page, name, extra = {}) {
  const focus = await page.evaluate(() => ({tag: window.document.activeElement?.tagName,
    className: window.document.activeElement?.className, menuOpen: !!window.document.querySelector('.voice-menu'),
    shelfDisplay: getComputedStyle(window.document.querySelector('.sidebar')).display,
    shelfOpened: window.document.querySelector('.sidebar').classList.contains('opened'),
    saves: window.popupFixture.saves, imports: window.popupFixture.imports,
    playCalls: window.popupFixture.playCalls, pauseCalls: window.popupFixture.pauseCalls}));
  if (evidence) fs.writeFileSync(path.join(evidence, name + '.json'), JSON.stringify({...focus, ...extra}, null, 2));
  return focus;
}

for (const kind of ['About', 'removal']) {
  test(`modal ${kind} Ctrl+S is isolated from permitted autosave`, async t => {
    const page = await fixture(t); await edit(page);
    const dialog = await openModal(page, kind);
    await page.keyboard.press('Control+s');
    const immediate = await observe(page, `save-${kind}-before-timer`);
    assert.deepEqual(immediate.saves, [], 'Manual shortcut cannot be attributed to scheduled autosave');
    await page.clock.runFor(1000);
    await page.waitForFunction(() => window.popupFixture.document.markdown === 'Dirty isolated fixture text.');
    assert.deepEqual(await page.evaluate(() => window.popupFixture.saves), ['Dirty isolated fixture text.']);
    assert.equal(await dialog.evaluate(el => el.open), true, 'Ordinary autosave remains allowed during a modal');
  });
  test(`modal ${kind} Ctrl+O cannot import behind the dialog`, async t => {
    const page = await fixture(t); const dialog = await openModal(page, kind);
    await page.keyboard.press('Control+o');
    const observed = await observe(page, `import-${kind}`);
    assert.equal(observed.imports, 0); assert.equal(await dialog.evaluate(el => el.open), true);
  });
  test(`modal ${kind} neutral Space preserves native Escape and button activation`, async t => {
    const page = await fixture(t); let dialog = await openModal(page, kind);
    // Deliberately exercise a native-dialog root target; this is synthetic focus,
    // not a claim that a particular browser's Tab sequence reaches the root.
    await dialog.evaluate(el => el.focus());
    assert.equal(await dialog.evaluate(el => el === window.document.activeElement), true, 'Required neutral focus observation');
    await page.keyboard.press('Space');
    const observed = await observe(page, `space-${kind}`, {focusSetup: 'synthetic native-dialog root'});
    assert.equal(observed.playCalls, 0); assert.equal(observed.pauseCalls, 0);
    await page.keyboard.press('Escape'); await dialog.waitFor({state: 'hidden'});
    dialog = await openModal(page, kind);
    await dialog.getByRole('button', {name: 'Close', exact: true}).focus();
    await page.keyboard.press('Space'); await dialog.waitFor({state: 'hidden'});
    assert.equal(await page.evaluate(() => window.popupFixture.removals), 0);
    assert.equal(await page.evaluate(() => window.popupFixture.playCalls), 0);
  });
}
test('voice Escape restores the trigger after option removal', async t => {
  const page = await fixture(t); await voice(page); await page.keyboard.press('Escape');
  await page.locator('.voice-menu').waitFor({state: 'hidden'});
  await observe(page, 'voice-escape');
  assert.equal(await page.locator('.voice-selector').evaluate(el => el === window.document.activeElement), true);
});
test('voice Enter selection saves once and restores the trigger', async t => {
  const page = await fixture(t); await voice(page); await page.keyboard.press('Tab');
  assert.equal(await page.locator('.voice-menu button').nth(1).evaluate(el => el === window.document.activeElement), true);
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => window.popupFixture.settings.voice === 'bf_emma');
  await observe(page, 'voice-selection');
  assert.equal(await page.locator('.voice-selector').evaluate(el => el === window.document.activeElement), true);
  assert.equal(await page.evaluate(() => window.popupFixture.settingsWrites.length), 1);
});
test('narrow shelf Escape restores its visible toggle', async t => {
  const page = await fixture(t, 1000); await shelf(page); await page.keyboard.press('Escape');
  await page.waitForFunction(() => getComputedStyle(window.document.querySelector('.sidebar')).display === 'none');
  await observe(page, 'narrow-shelf');
  assert.equal(await page.locator('.shelf-toggle').evaluate(el => el === window.document.activeElement), true);
});
for (const popup of ['voice', 'shelf']) {
  test(`${popup} dismissal preserves unrelated focus already reached`, async t => {
    const page = await fixture(t, popup === 'shelf' ? 1000 : 1280);
    await (popup === 'voice' ? voice(page) : shelf(page));
    await page.locator('.play-button').focus(); await page.keyboard.press('Escape');
    await observe(page, `${popup}-unrelated-before`);
    assert.equal(await page.locator('.play-button').evaluate(el => el === window.document.activeElement), true);
  });
  test(`${popup} dismissal rechecks an intentional focus handoff before tick settles`, async t => {
    const page = await fixture(t, popup === 'shelf' ? 1000 : 1280);
    await (popup === 'voice' ? voice(page) : shelf(page));
    await page.evaluate(() => window.addEventListener('keydown', event => {
      if (event.key === 'Escape') { window.popupFixture.handoffs++; window.document.querySelector('.play-button').focus(); }
    }, {once: true}));
    await page.keyboard.press('Escape');
    await observe(page, `${popup}-unrelated-during`);
    assert.equal(await page.evaluate(() => window.popupFixture.handoffs), 1);
    assert.equal(await page.locator('.play-button').evaluate(el => el === window.document.activeElement), true);
  });
}
test('new native close request owns focus while popup dismissal settles', async t => {
  const page = await fixture(t); await edit(page); await voice(page);
  await page.evaluate(() => {
    window.popupFixture.holdSave = true;
    window.addEventListener('keydown', event => {
      if (event.key === 'Escape') {
        // The injected close request is a separate native action. Do not also
        // apply this same key's default cancel action to the newly opened dialog.
        event.preventDefault();
        window.dispatchEvent(new CustomEvent('violilt:close-request', {detail: {id: 'focusClose'}}));
      }
    }, {once: true});
  });
  await page.keyboard.press('Escape');
  const dialog = page.getByRole('dialog', {name: 'Save before closing', exact: true});
  await dialog.waitFor();
  assert.equal(await dialog.evaluate(el => el.contains(window.document.activeElement)), true);
  await page.waitForFunction(() => typeof window.popupFixture.releaseSave === 'function');
  assert.equal(await page.evaluate(() => window.popupFixture.closeMessages.some(m => m.id === 'focusClose' && m.saved)), false);
  await observe(page, 'native-close-handoff', {dialogOwnsFocus: await dialog.evaluate(el => el.contains(window.document.activeElement))});
  await page.keyboard.press('Escape'); await dialog.waitFor({state: 'hidden'});
  await page.evaluate(() => { window.popupFixture.holdSave = false; window.popupFixture.releaseSave(); });
  await page.waitForFunction(() => window.popupFixture.document.markdown === 'Dirty isolated fixture text.');
  assert.deepEqual(await page.evaluate(() => window.popupFixture.closeMessages.filter(m => m.id === 'focusClose')),
    [{type: 'violilt:close-response', id: 'focusClose', saved: false}]);
});
test('wide shelf remains visible and retains its focused control', async t => {
  const page = await fixture(t, 1000); await shelf(page); await page.setViewportSize({width: 1280, height: 900});
  await reading(page).focus(); await page.keyboard.press('Escape');
  assert.equal(await page.locator('.sidebar').evaluate(el => getComputedStyle(el).display !== 'none'), true);
  assert.equal(await reading(page).evaluate(el => el === window.document.activeElement), true);
});
test('ordinary save import and background playback shortcuts remain available', async t => {
  const page = await fixture(t); await edit(page, 'Manual positive control.');
  await page.keyboard.press('Control+s');
  await page.waitForFunction(() => window.popupFixture.document.markdown === 'Manual positive control.');
  assert.deepEqual(await page.evaluate(() => window.popupFixture.saves), ['Manual positive control.']);
  await page.keyboard.press('Control+o'); await page.waitForFunction(() => window.popupFixture.imports === 1);
  await page.locator('.play-button').focus(); await page.locator('.play-button').evaluate(el => el.blur());
  assert.equal(await page.evaluate(() => window.document.activeElement === window.document.body), true);
  await page.keyboard.press('Space'); assert.equal(await page.evaluate(() => window.popupFixture.playCalls), 1);
});
test('file menu retains its shortcut suppression and Escape anchor restoration', async t => {
  const page = await fixture(t); await edit(page);
  await reading(page).focus(); await page.keyboard.press('Shift+F10');
  await page.getByRole('menu').waitFor();
  await page.keyboard.press('Control+s'); await page.keyboard.press('Control+o');
  assert.deepEqual(await page.evaluate(() => ({saves: window.popupFixture.saves, imports: window.popupFixture.imports})), {saves: [], imports: 0});
  await page.keyboard.press('Escape'); await page.getByRole('menu').waitFor({state: 'hidden'});
  assert.equal(await reading(page).evaluate(el => el === window.document.activeElement), true);
});
test('DocumentFind keeps input Space and Escape trigger restoration', async t => {
  const page = await fixture(t); await page.keyboard.press('Control+f');
  const input = page.getByRole('textbox', {name: 'Find in document', exact: true});
  await input.waitFor(); assert.equal(await input.evaluate(el => el === window.document.activeElement), true);
  await input.fill('Original'); await page.keyboard.press('Space'); assert.equal(await input.inputValue(), 'Original ');
  await page.keyboard.press('Escape'); await input.waitFor({state: 'hidden'});
  assert.equal(await page.locator('.find-trigger').evaluate(el => el === window.document.activeElement), true);
  assert.equal(await page.evaluate(() => window.popupFixture.playCalls), 0);
});
