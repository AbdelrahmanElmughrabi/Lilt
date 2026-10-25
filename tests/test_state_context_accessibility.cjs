/** Finite S01-S05/C01 built-UI metadata regressions. Disposable API/media only.
 * Use existing PLAYWRIGHT_MODULE/Edge; R11_ASSETS and R11_EVIDENCE_DIR select inputs.
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
  const context = await browser.newContext({viewport: {width, height: 900}, colorScheme: 'light'});
  const page = await context.newPage(); page.setDefaultTimeout(5000);
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
    assert.deepEqual(foreign, [], 'Only exact local fixture assets are allowed');
  });
  await page.addInitScript(() => {
    const documents = [
      {id: 'doc-a', title: 'Alpha manuscript', markdown: 'Identical body text.', words: 3, created: 1},
      {id: 'doc-b', title: 'Beta manuscript', markdown: 'Identical body text.', words: 3, created: 2},
    ];
    const settings = {palette: 'violilt', theme: 'light', voice: 'af_heart', speed: 1, include_code: false,
      heading_pause: 0.6, paragraph_pause: 0.3, performance_mode: 'balanced', cpu_threads: 0,
      processing_device: 'cpu', gpu_device: -1, buffer_mode: 'balanced', auto_listen: false,
      warm_start: false, model_release: 'idle', cache_enabled: true, cache_limit_mb: 256};
    const job = (id, title, state) => ({id, title, state, document_id: 'doc-a', voice: 'af_heart', speed: 1,
      words: 3, preview: false, completed: state === 'completed' ? 2 : 1, total: 2, duration: 10,
      available_duration: 0, position: 0, message: '', created: 1, can_resume: true});
    const jobs = [job('saved-a', 'Alpha recording', 'completed'), job('saved-b', 'Beta recording', 'completed'),
      job('unfinished-a', 'Alpha unfinished', 'cancelled'), job('unfinished-b', 'Beta unfinished', 'cancelled')];
    const controls = window.stateFixture = {documents, jobs, settings, opens: [], settingsWrites: [], saves: [],
      playCalls: 0, pauseCalls: 0, exports: 0, removals: 0, continues: 0, closeMessages: []};
    HTMLMediaElement.prototype.play = function () { controls.playCalls++; return Promise.resolve(); };
    HTMLMediaElement.prototype.pause = function () { controls.pauseCalls++; };
    window.chrome ||= {};
    window.chrome.webview = {postMessage: message => controls.closeMessages.push(message)};
    window.pywebview = {api: {
      get_state: async () => ({documents: structuredClone(documents), jobs, active: null, settings, welcome_version: 1,
        model: {state: 'ready', percent: 100, message: 'Fixture only', voices: ['af_heart', 'bf_emma']},
        storage: 'Synthetic fixture', performance: null, cache: {count: 0, bytes: 0, limit_mb: 256}}),
      get_document: async id => { controls.opens.push(id); return structuredClone(documents.find(doc => doc.id === id)); },
      save_document: async (id, markdown) => {
        controls.saves.push({id, markdown}); const doc = documents.find(doc => doc.id === id);
        doc.markdown = markdown; return structuredClone(doc);
      },
      prepare_document: async text => ({title: 'Synthetic preview', text, words: 3,
        chunks: [{text, pause: 0.3, block: 0}], omissions: {code_blocks: 0, metadata: 0}}),
      save_settings: async value => { controls.settingsWrites.push(structuredClone(value)); Object.assign(settings, value); return value; },
      save_position: async () => true,
      export_recording: async () => { controls.exports++; return null; },
      remove_recording: async () => { controls.removals++; },
      resume_job: async id => { controls.continues++; return jobs.find(item => item.id === id); },
      open_microsoft_privacy: async () => true,
      generate: async () => { throw new Error('Real generation is outside this fixture'); },
    }};
  });
  await page.goto(origin);
  await page.waitForFunction(() => window.stateFixture.closeMessages.some(message => message.type === 'violilt:close-ready'));
  await page.clock.install(); await page.clock.pauseAt(new Date());
  await page.evaluate(() => { window.stateFixture.playCalls = 0; window.stateFixture.pauseCalls = 0; });
  page.axSession = await context.newCDPSession(page);
  await page.axSession.send('Accessibility.enable');
  return page;
}
async function ax(page, selector) {
  const {root} = await page.axSession.send('DOM.getDocument');
  const {nodeId} = await page.axSession.send('DOM.querySelector', {nodeId: root.nodeId, selector});
  assert(nodeId, `Required DOM target is missing: ${selector}`);
  const {nodes} = await page.axSession.send('Accessibility.getPartialAXTree', {nodeId, fetchRelatives: false});
  assert(nodes.length, `Required AX observation is missing: ${selector}`);
  const node = nodes[0];
  return {role: node.role?.value, name: node.name?.value, ignored: node.ignored,
    properties: Object.fromEntries((node.properties || []).map(property => [property.name, property.value?.value]))};
}
async function press(page, locator) { await locator.focus(); await page.keyboard.press('Enter'); }
async function openDocument(page, index = 0) {
  await press(page, page.locator('.document-list button').nth(index));
  await page.locator('.reading-article').waitFor();
  await page.waitForFunction(id => window.stateFixture.opens.at(-1) === id, index === 0 ? 'doc-a' : 'doc-b');
}
async function choices(page, selector) {
  const buttons = page.locator(selector + ' > button');
  const values = [];
  for (let i = 0; i < await buttons.count(); i++) values.push(await ax(page, `${selector} > button:nth-of-type(${i + 1})`));
  assert(values.length, 'Choice set must be present');
  return {buttons: values, pressedCount: await page.locator(selector).getByRole('button', {pressed: true}).count()};
}
function expectPressed(snapshot, selected) {
  assert.equal(snapshot.pressedCount, 1, 'Exactly one accessible pressed choice is required');
  assert.deepEqual(snapshot.buttons.map(button => String(button.properties.pressed)),
    snapshot.buttons.map((_button, index) => String(index === selected)));
}
async function record(name, data) {
  if (evidence) fs.writeFileSync(path.join(evidence, name + '.json'), JSON.stringify(data, null, 2));
}

test('S01 current shelf document follows actual opens despite identical text', async t => {
  const page = await fixture(t);
  const snapshots = [];
  for (let index = 0; index < 2; index++) {
    await openDocument(page, index);
    assert.equal((await page.locator('.reading-article').innerText()).trim(), 'Identical body text.');
    snapshots.push({current: await page.locator('.document-list button').evaluateAll(buttons => buttons.map(button => button.getAttribute('aria-current'))),
      openedButton: await ax(page, `.document-list > button:nth-of-type(${index + 1})`)});
  }
  await press(page, page.getByRole('button', {name: 'Home', exact: true}));
  const away = await page.locator('.document-list button').evaluateAll(buttons => buttons.map(button => button.getAttribute('aria-current')));
  const opens = await page.evaluate(() => window.stateFixture.opens);
  await record('S01', {snapshots, away, opens});
  assert.deepEqual(opens, ['doc-a', 'doc-b']);
  assert.deepEqual(snapshots.map(snapshot => snapshot.openedButton.role), ['button', 'button']);
  assert.match(snapshots[0].openedButton.name, /Alpha manuscript/); assert.match(snapshots[1].openedButton.name, /Beta manuscript/);
  assert.deepEqual(snapshots.map(snapshot => snapshot.current), [['true', null], [null, 'true']]);
  assert.deepEqual(away, [null, null], 'No studio document is current while Home is shown');
});
test('S02 narrow shelf expanded state follows visibility and Escape focus return', async t => {
  const page = await fixture(t, 1000);
  const toggle = page.getByRole('button', {name: 'Toggle shelf', exact: true});
  const snapshots = [{ax: await ax(page, '.shelf-toggle'), visible: await page.locator('.sidebar').isVisible()}];
  await toggle.focus(); await page.keyboard.press('Space');
  await page.locator('.sidebar').waitFor({state: 'visible'});
  snapshots.push({ax: await ax(page, '.shelf-toggle'), visible: await page.locator('.sidebar').isVisible()});
  await page.locator('.document-list button').first().focus(); await page.keyboard.press('Escape');
  await page.locator('.sidebar').waitFor({state: 'hidden'});
  snapshots.push({ax: await ax(page, '.shelf-toggle'), visible: await page.locator('.sidebar').isVisible()});
  const restored = await toggle.evaluate(el => el === window.document.activeElement);
  await record('S02', {snapshots, restored});
  assert.deepEqual(snapshots.map(snapshot => snapshot.visible), [false, true, false]); assert.equal(restored, true);
  assert.deepEqual(snapshots.map(snapshot => String(snapshot.ax.properties.expanded)), ['false', 'true', 'false']);
});
test('S03 document view pressed state follows each real view', async t => {
  const page = await fixture(t); await openDocument(page);
  const snapshots = [];
  for (const [index, target] of ['.reading-article', '.markdown-editor', '.spoken-text'].entries()) {
    await press(page, page.locator('.document-tabs > button').nth(index));
    await page.locator(target).waitFor({state: 'visible'});
    snapshots.push(await choices(page, '.document-tabs'));
  }
  const saves = await page.evaluate(() => window.stateFixture.saves);
  await record('S03', {snapshots, saves}); assert.deepEqual(saves, []);
  snapshots.forEach(expectPressed);
});
test('S04 chosen processing preset synchronizes both views with one settings call per activation', async t => {
  const page = await fixture(t); await openDocument(page);
  const initial = await choices(page, '.compact-presets');
  await press(page, page.locator('.compact-presets > button').nth(0));
  await page.waitForFunction(() => window.stateFixture.settingsWrites.length === 1);
  const compactQuiet = await choices(page, '.compact-presets');
  await press(page, page.getByRole('button', {name: 'Settings', exact: true}));
  const settingsQuiet = await choices(page, '.performance-presets');
  await press(page, page.locator('.performance-presets > button').nth(3));
  await page.waitForFunction(() => window.stateFixture.settingsWrites.length === 2);
  const settingsCustom = await choices(page, '.performance-presets');
  const threadsEnabled = await page.getByRole('combobox', {name: 'CPU threads', exact: true}).isEnabled();
  await press(page, page.getByRole('button', {name: 'Reading room', exact: true}));
  const compactCustom = await choices(page, '.compact-presets');
  const writes = await page.evaluate(() => window.stateFixture.settingsWrites.map(value => value.performance_mode));
  await record('S04', {initial, compactQuiet, settingsQuiet, settingsCustom, compactCustom, threadsEnabled, writes});
  assert.deepEqual(writes, ['quiet', 'custom']); assert.equal(threadsEnabled, true);
  expectPressed(initial, 1); expectPressed(compactQuiet, 0); expectPressed(settingsQuiet, 0);
  expectPressed(settingsCustom, 3); expectPressed(compactCustom, 3);
});
test('S05 explicit light and system remain distinguishable when effective colors match', async t => {
  const page = await fixture(t); await press(page, page.getByRole('button', {name: 'Settings', exact: true}));
  const colors = () => page.locator('.app-shell').evaluate(el => ({dark: el.classList.contains('dark'),
    paper: getComputedStyle(el).getPropertyValue('--paper'), ink: getComputedStyle(el).getPropertyValue('--ink')}));
  const initial = {choices: await choices(page, '.theme-choices'), colors: await colors()};
  await press(page, page.locator('.theme-choices > button').nth(2));
  await page.waitForFunction(() => window.stateFixture.settingsWrites.length === 1);
  const system = {choices: await choices(page, '.theme-choices'), colors: await colors()};
  await press(page, page.locator('.theme-choices > button').nth(0));
  await page.waitForFunction(() => window.stateFixture.settingsWrites.length === 2);
  const explicit = {choices: await choices(page, '.theme-choices'), colors: await colors()};
  const writes = await page.evaluate(() => window.stateFixture.settingsWrites.map(value => value.theme));
  await record('S05', {initial, system, explicit, writes});
  assert(initial.colors.paper.trim() && initial.colors.ink.trim(), 'Required effective color observations are present');
  assert.deepEqual(initial.colors, system.colors); assert.equal(system.colors.dark, false);
  assert.deepEqual(writes, ['system', 'light']); expectPressed(initial.choices, 0);
  expectPressed(system.choices, 2); expectPressed(explicit.choices, 0);
});
async function tabTo(page, target) {
  for (let steps = 1; steps <= 20; steps++) {
    await page.keyboard.press('Tab');
    if (await target.evaluate(el => el === window.document.activeElement)) return steps;
  }
  assert.fail('Required existing context container was not reached by real Tab');
}
for (const type of ['saved', 'unfinished', 'library']) test(`C01-${type} existing context targets expose title-correct groups and preserve actions`, async t => {
  const page = await fixture(t);
  let selector, titles;
  if (type === 'library') {
    await press(page, page.getByRole('button', {name: 'Your recordings', exact: false}));
    selector = '.recording-card'; titles = ['Alpha recording', 'Beta recording'];
    await page.getByRole('textbox', {name: 'Search recordings', exact: true}).focus();
  } else if (type === 'saved') {
    selector = '.saved-reading'; titles = ['Alpha recording', 'Beta recording'];
    await page.getByRole('button', {name: 'View all', exact: true}).focus();
  } else {
    selector = '.unfinished-row'; titles = ['Alpha unfinished', 'Beta unfinished'];
    await page.getByRole('button', {name: 'Export Beta recording as WAV', exact: true}).focus();
  }
  const snapshots = [];
  for (const [index, title] of titles.entries()) {
    const row = page.locator(selector).nth(index);
    const steps = await tabTo(page, row);
    const identity = await ax(page, `${selector}:nth-of-type(${index + 1})`);
    const namedGroups = await page.getByRole('group', {name: `Recording: ${title}`, exact: true}).count();
    const childButtons = type === 'saved' ? [`Play ${title}`, `Export ${title} as WAV`] :
      type === 'unfinished' ? ['Continue'] : ['Listen', 'Export WAV', 'Remove recording'];
    for (const name of childButtons) assert.equal(await row.getByRole('button', {name, exact: true}).count(), 1, `Separate child button remains: ${name}`);
    await page.keyboard.press('Shift+F10');
    const menu = page.getByRole('menu', {name: `Actions for ${title}`, exact: true}); await menu.waitFor();
    await page.keyboard.press('Escape'); await menu.waitFor({state: 'hidden'});
    const restored = await row.evaluate(el => el === window.document.activeElement);
    snapshots.push({title, steps, identity, namedGroups, childButtons, restored});
    assert.equal(restored, true);
  }
  const effects = await page.evaluate(() => ({play: window.stateFixture.playCalls, pause: window.stateFixture.pauseCalls,
    exports: window.stateFixture.exports, removals: window.stateFixture.removals, continues: window.stateFixture.continues}));
  await record(`C01-${type}`, {snapshots, effects});
  assert.deepEqual(effects, {play: 0, pause: 0, exports: 0, removals: 0, continues: 0});
  for (const snapshot of snapshots) {
    assert.equal(snapshot.identity.role, 'group'); assert.equal(snapshot.identity.name, `Recording: ${snapshot.title}`);
    assert.equal(snapshot.namedGroups, 1);
  }
});
