/**
 * Focused built-UI regressions using disposable API/media fixtures.
 * Build with tools/build_frontend.py. Set PLAYWRIGHT_MODULE to an existing
 * Playwright installation; optional R11_ASSETS and R11_EVIDENCE_DIR select
 * preserved assets and a fresh evidence directory. No native app or speech runs.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const {test, before, after} = require('node:test');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const assets = path.resolve(process.env.R11_ASSETS || path.join(__dirname, '../frontend/dist'));
const evidence = process.env.R11_EVIDENCE_DIR;
const types = {'.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png'};
let browser, server, origin;

before(async () => {
  assert(fs.existsSync(path.join(assets, 'index.html')), 'Built frontend is required');
  if (evidence) fs.mkdirSync(evidence, {recursive: true});
  server = http.createServer((request, response) => {
    const pathname = new URL(request.url, 'http://localhost').pathname;
    if (pathname.startsWith('/media/')) return response.writeHead(204).end();
    const file = path.resolve(assets, '.' + (pathname === '/' ? '/index.html' : pathname));
    if (!file.startsWith(assets + path.sep)) return response.writeHead(403).end();
    try {
      response.writeHead(200, {'Content-Type': types[path.extname(file)] || 'application/octet-stream'});
      response.end(fs.readFileSync(file));
    } catch { response.writeHead(404).end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  origin = `http://127.0.0.1:${server.address().port}`;
  try {
    browser = await chromium.launch({headless: true, executablePath: process.env.BROWSER_EXECUTABLE ||
      'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
  } catch (error) {
    await new Promise(resolve => server.close(resolve));
    server = null;
    throw error;
  }
});

after(async () => {
  if (browser) await browser.close();
  if (server) await new Promise(resolve => server.close(resolve));
});

async function fixture(t, palette = 'violilt', theme = 'light') {
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}});
  const page = await context.newPage();
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  t.after(async () => {
    await context.close();
    assert.deepEqual(errors, [], 'Unexpected browser errors');
  });
  await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
  await page.addInitScript(({palette, theme}) => {
    const settings = {palette, theme, voice: 'af_heart', speed: 1, include_code: false,
      heading_pause: 0.6, paragraph_pause: 0.3, performance_mode: 'balanced', cpu_threads: 0,
      processing_device: 'cpu', gpu_device: -1, buffer_mode: 'balanced', auto_listen: false,
      warm_start: false, model_release: 'idle', cache_enabled: true, cache_limit_mb: 256};
    const document = {id: 'reading', title: 'Synthetic reading', markdown: 'Fixture words.', created: 1};
    const job = {id: 'recording', document_id: document.id, title: 'Synthetic recording',
      voice: 'af_heart', speed: 1, words: 2, preview: false, state: 'completed',
      completed: 1, total: 1, duration: 10, position: 0, message: '', created: 1};
    const configuration = {provider: 'CPUExecutionProvider', label: 'CPU', threads: 2, device_id: -1};
    const controls = window.keyboardFixture = {playCalls: 0};
    // Observe dispatch without loading/playing audio or launching speech workers.
    HTMLMediaElement.prototype.play = function () { controls.playCalls++; return Promise.resolve(); };
    HTMLMediaElement.prototype.pause = function () {};
    window.chrome ||= {};
    window.chrome.webview = {postMessage: () => {}};
    window.pywebview = {api: {
      get_state: async () => ({documents: [document], jobs: [job],
        active: {...job, id: 'generating', state: 'generating', completed: 0, engine: configuration},
        settings, welcome_version: 1, model: {state: 'ready', percent: 100, message: 'Fixture only', voices: ['af_heart']},
        storage: 'Synthetic fixture', cache: {count: 0, bytes: 0, limit_mb: 256},
        performance: {configuration, cpu_percent: 20, gpu_percent: null, gpu_ready: false,
          logical_processors: 2, physical_cores: 2, adapters: [], gpu_message: '',
          memory: {state: 'busy', message: 'Fixture only'}, warmup: {state: 'idle', message: ''},
          benchmark: {state: 'idle', completed: 0, total: 0, message: '', results: []}, recommendation: null}}),
      get_document: async () => structuredClone(document),
      save_document: async (_id, text) => ({...document, markdown: text}),
      prepare_document: async text => ({title: document.title, text, words: 2,
        chunks: [{text, pause: 0.3, block: 0}], omissions: {code_blocks: 0, metadata: 0}}),
      save_settings: async value => Object.assign(settings, value),
      save_position: async () => true,
      generate: async () => { throw new Error('Real generation is outside this fixture'); },
    }};
  }, {palette, theme});
  await page.goto(origin);
  await page.locator('.document-list button').filter({hasText: 'Synthetic reading'}).click();
  await page.locator('.reading-article').waitFor();
  await page.locator('.hardware-usage summary').waitFor();
  await page.waitForFunction(() => window.document.querySelector('.play-button')?.disabled === false);
  // Prevent polling from altering the synthetic state during observations.
  await page.clock.install();
  await page.clock.pauseAt(new Date());
  return page;
}

async function record(page, name, observations) {
  if (!evidence) return;
  fs.writeFileSync(path.join(evidence, `${name}.json`), JSON.stringify(observations, null, 2));
  await page.screenshot({path: path.join(evidence, `${name}.png`)});
}

async function focusSummaryByTab(page) {
  await page.getByRole('button', {name: 'Stop generation', exact: true}).focus();
  await page.keyboard.press('Shift+Tab');
  assert.equal(await page.locator('.hardware-usage summary').evaluate(el => el === window.document.activeElement), true,
    'Native summary must be reachable by keyboard from the adjacent real control');
}

test('Space opens and closes native performance details without starting playback', async t => {
  const page = await fixture(t);
  await focusSummaryByTab(page);
  const details = page.locator('.hardware-usage');
  assert.equal(await details.evaluate(el => el.open), false);
  await page.keyboard.press('Space');
  const observations = await page.evaluate(() => ({open: window.document.querySelector('.hardware-usage').open,
    playCalls: window.keyboardFixture.playCalls}));
  await record(page, 'summary-space', observations);
  assert.deepEqual(observations, {open: true, playCalls: 0});
  await page.keyboard.press('Space');
  assert.equal(await details.evaluate(el => el.open), false);
  assert.equal(await page.evaluate(() => window.keyboardFixture.playCalls), 0);
});

test('Enter keeps native performance details activation', async t => {
  const page = await fixture(t);
  await focusSummaryByTab(page);
  await page.keyboard.press('Enter');
  assert.equal(await page.locator('.hardware-usage').evaluate(el => el.open), true);
  assert.equal(await page.evaluate(() => window.keyboardFixture.playCalls), 0);
});

test('background Space and the focused playback button each dispatch playback once', async t => {
  const page = await fixture(t);
  await page.locator('.play-button').focus();
  await page.keyboard.press('Space');
  assert.equal(await page.evaluate(() => window.keyboardFixture.playCalls), 1,
    'Native button activation must not also invoke the global shortcut');
  await page.locator('.play-button').evaluate(el => el.blur());
  assert.equal(await page.evaluate(() => window.document.activeElement === window.document.body), true);
  await page.keyboard.press('Space');
  assert.equal(await page.evaluate(() => window.keyboardFixture.playCalls), 2,
    'Ordinary global playback shortcut must remain available');
});

for (const palette of ['violilt', 'classic']) for (const theme of ['light', 'dark']) {
  test(`recording search has visible keyboard focus and accepts Space (${palette}/${theme})`, async t => {
    const page = await fixture(t, palette, theme);
    await page.getByRole('button', {name: 'Your recordings', exact: false}).click();
    const search = page.getByRole('textbox', {name: 'Search recordings', exact: true});
    await search.waitFor();
    await page.getByRole('button', {name: 'Import document', exact: false}).focus();
    await page.keyboard.press('Tab');
    const observations = await search.evaluate(el => {
      const style = getComputedStyle(el);
      return {focused: el === window.document.activeElement, keyboardFocus: el.matches(':focus-visible'),
        outlineStyle: style.outlineStyle, outlineWidth: parseFloat(style.outlineWidth), outlineColor: style.outlineColor};
    });
    await record(page, `search-${palette}-${theme}`, observations);
    assert.equal(observations.focused, true, 'Real Tab navigation must reach search');
    assert.equal(observations.keyboardFocus, true);
    assert.notEqual(observations.outlineStyle, 'none');
    assert(observations.outlineWidth >= 2, 'Keyboard focus needs an effective visible outline');
    assert.notEqual(observations.outlineColor, 'rgba(0, 0, 0, 0)');
    await search.fill('Synthetic');
    await page.keyboard.press('Space');
    assert.equal(await search.inputValue(), 'Synthetic ');
    assert.equal(await page.evaluate(() => window.keyboardFixture.playCalls), 0);
  });
}
