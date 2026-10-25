/** Built UI with disposable API/opener/media fixtures. No native app or real links.
 * Set PLAYWRIGHT_MODULE, optionally R05_ASSETS/R05_EVIDENCE_DIR, then node --test.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const {test, before, after} = require('node:test');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assets = path.resolve(process.env.R05_ASSETS || path.join(__dirname, '../frontend/dist'));
const evidence = process.env.R05_EVIDENCE_DIR;
const links = {
  'privacy-statement': 'https://privacy.microsoft.com/privacystatement',
  smartscreen: 'https://learn.microsoft.com/en-us/legal/microsoft-edge/privacy#smartscreen',
};
let browser, server, origin;
before(async () => {
  assert(fs.existsSync(path.join(assets, 'index.html')), 'Built assets are required');
  if (evidence) fs.mkdirSync(evidence, {recursive: true});
  server = http.createServer((request, response) => {
    const pathname = new URL(request.url, 'http://localhost').pathname;
    if (pathname.startsWith('/media/')) return response.writeHead(204).end();
    const file = path.resolve(assets, '.' + (pathname === '/' ? '/index.html' : pathname));
    if (!file.startsWith(assets + path.sep)) return response.writeHead(403).end();
    try {
      response.writeHead(200, {'Content-Type': ({'.html':'text/html','.js':'text/javascript','.css':'text/css','.png':'image/png'})[path.extname(file)] || 'application/octet-stream'});
      response.end(fs.readFileSync(file));
    } catch { response.writeHead(404).end(); }
  });
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

async function fixture(t, options = {}) {
  const context = await browser.newContext({viewport: options.viewport || {width:1280,height:900}});
  const page = await context.newPage();
  page.setDefaultTimeout(5000);
  const errors = [], requests = [];
  page.on('pageerror', error => errors.push(error.message));
  await context.route('**/*', route => {
    const url = route.request().url();
    if (new URL(url).origin === origin) {
      // Serve exact local build bytes without a network response intermediary.
      const pathname = new URL(url).pathname;
      if (pathname.startsWith('/media/')) return route.fulfill({status:204,body:''});
      const file = path.resolve(assets, '.' + (pathname === '/' ? '/index.html' : pathname));
      if (!file.startsWith(assets + path.sep)) return route.fulfill({status:403,body:''});
      try {
        return route.fulfill({status:200,contentType:({'.html':'text/html','.js':'text/javascript','.css':'text/css','.png':'image/png'})[path.extname(file)] || 'application/octet-stream',body:fs.readFileSync(file)});
      } catch { return route.fulfill({status:404,body:''}); }
    }
    requests.push(url); return route.abort();
  });
  t.after(async () => {
    await context.close();
    assert.deepEqual(errors, [], 'Browser errors cannot count as success');
    assert.deepEqual(requests, [], 'Notice must not navigate/fetch external links');
  });
  await page.addInitScript(options => {
    const settings = options.existing ? {palette:'classic',theme:'dark',voice:'bf_emma',speed:1.25,
      auto_listen:false,processing_device:'cpu',cache_enabled:false} : {};
    const document = {id:'reading',title:'Synthetic reading',markdown:'Original fixture text.',created:1};
    const job = {id:'recording',title:'Synthetic recording',document_id:'reading',voice:'af_heart',speed:1,
      words:3,preview:false,state:'completed',completed:1,total:1,duration:10,position:0,message:'',created:1};
    const controls = window.noticeFixture = {settings, document, saves:[], settingsWrites:[], opened:[],
      closeMessages:[], playCalls:0, imports:0, failLink:false, falseLink:false, holdLink:false,
      holdSave:false, failSave:false, failState:!!options.failState};
    HTMLMediaElement.prototype.play = function () { controls.playCalls++; return Promise.resolve(); };
    HTMLMediaElement.prototype.pause = function () {};
    window.chrome ||= {};
    window.chrome.webview = {postMessage: message => controls.closeMessages.push(message)};
    window.pywebview = {api: {
      get_state: async () => {
        if (controls.failState) throw new Error('Synthetic connection failure.');
        return {documents:[document],jobs:[job],active:null,settings,storage:'Synthetic fixture',
          performance:null,cache:{count:0,bytes:0,limit_mb:256},welcome_version:1,
          model:{state:'ready',percent:100,message:'Fixture only',voices:['af_heart','bf_emma']}};
      },
      get_document: async () => structuredClone(document),
      save_document: async (_id, markdown) => {
        controls.saves.push(markdown);
        if (controls.holdSave) await new Promise(resolve => controls.releaseSave = resolve);
        if (controls.failSave) throw new Error('Synthetic save failure; retry.');
        document.markdown = markdown; return structuredClone(document);
      },
      prepare_document: async text => ({title:document.title,text,words:3,chunks:[{text,pause:0.3,block:0}],
        omissions:{code_blocks:0,metadata:0}}),
      save_settings: async value => { controls.settingsWrites.push(value); return value; },
      save_position: async () => true,
      import_document: async () => { controls.imports++; return null; },
      generate: async () => { throw new Error('Generation outside notice fixture'); },
      open_microsoft_privacy: async reference => {
        controls.opened.push(reference);
        if (controls.holdLink) await new Promise(resolve => controls.releaseLink = resolve);
        if (controls.failLink) throw new Error('Synthetic browser failure. Retry or copy the address.');
        return !controls.falseLink;
      },
    }};
  }, options);
  await page.goto(origin);
  await page.waitForFunction(() => window.noticeFixture && document.querySelector('.app-shell'));
  await reopen(page);
  return page;
}
const notice = page => page.getByRole('dialog', {name:'Microsoft services & privacy',exact:true});
async function observe(page, name, values) {
  if (!evidence) return;
  fs.writeFileSync(path.join(evidence, name + '.json'), JSON.stringify(values, null, 2));
  await page.screenshot({path:path.join(evidence,name+'.png')});
}
async function reopen(page) {
  if (!await page.locator('dialog[aria-labelledby="about-title"][open]').count()) {
    const trigger = page.getByRole('button',{name:'About Violilt',exact:true});
    const toggle = page.getByRole('button',{name:'Toggle shelf',exact:true});
    if (await toggle.isVisible() && await toggle.getAttribute('aria-expanded') === 'false') await toggle.click();
    await trigger.click();
  }
  await page.getByRole('button',{name:'Microsoft services & privacy',exact:true}).click();
  await notice(page).waitFor();
}
async function edit(page) {
  await notice(page).getByRole('button',{name:'Continue',exact:true}).click();
  if (await page.locator('dialog[aria-labelledby="about-title"][open]').count()) await page.keyboard.press('Escape');
  await page.locator('.document-list button').filter({hasText:'Synthetic reading'}).click();
  await page.getByRole('button',{name:'Edit',exact:true}).click();
  await page.clock.install(); await page.clock.pauseAt(new Date());
}

for (const existing of [false,true]) test(`notice remains available from About with ${existing ? 'existing' : 'initial'} settings`, async t => {
  const page = await fixture(t,{existing});
  await notice(page).waitFor();
  const copy = await notice(page).innerText();
  assert.match(copy,/Microsoft Defender SmartScreen/);
  assert.match(copy,/collects and sends your information to Microsoft/);
  assert.match(copy,/required diagnostic data/);
  assert.match(copy,/Windows controls optional diagnostic data/);
  assert.match(copy,/does not change diagnostic settings or give consent/);
  for (const [i,url] of Object.values(links).entries()) assert.equal(await notice(page).locator('a').nth(i).getAttribute('href'),url);
  assert.equal(await notice(page).evaluate(el => el.open),true);
  await observe(page,existing?'existing-launch':'initial-launch',{copy,settings:await page.evaluate(()=>window.noticeFixture.settings)});
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('.microsoft-notice').evaluate(el=>el.open),false);
  assert.deepEqual(await page.evaluate(()=>({writes:window.noticeFixture.settingsWrites,saves:window.noticeFixture.saves})),{writes:[],saves:[]});
  await page.reload();
  await page.waitForFunction(() => window.noticeFixture && document.querySelector('.app-shell'));
  assert.equal(await page.locator('dialog[open]').count(),0,'Returning users enter the app directly');
  await reopen(page);
  assert.equal(await notice(page).evaluate(el=>el.open),true,'The full notice remains accessible');
});

test('persistent About route restores focus through native Escape and link Tab order', async t => {
  const page = await fixture(t);
  await notice(page).waitFor();
  assert.equal(await notice(page).getByRole('button',{name:'Continue',exact:true}).evaluate(el=>el===document.activeElement),true);
  await page.keyboard.press('Control+o'); await page.keyboard.press('Control+s');
  assert.deepEqual(await page.evaluate(()=>({imports:window.noticeFixture.imports,saves:window.noticeFixture.saves,play:window.noticeFixture.playCalls})),{imports:0,saves:[],play:0});
  await page.keyboard.press('Space'); // Native Continue button activation.
  assert.equal(await page.locator('.microsoft-notice').evaluate(el=>el.open),false);
  await reopen(page);
  // Traverse within the native dialog; browser chrome can receive Tab at its end.
  await page.keyboard.press('Shift+Tab');
  assert.equal(await notice(page).locator('a').nth(1).evaluate(el=>el===document.activeElement),true);
  await page.keyboard.press('Shift+Tab');
  assert.equal(await notice(page).locator('a').first().evaluate(el=>el===document.activeElement),true);
  const focus = await notice(page).locator('a').first().evaluate(el=>({visible:el.matches(':focus-visible'),outline:getComputedStyle(el).outlineWidth}));
  assert.equal(focus.visible,true); assert(parseFloat(focus.outline)>=2);
  await page.keyboard.press('Tab');
  assert.equal(await notice(page).locator('a').nth(1).evaluate(el=>el===document.activeElement),true);
  await page.keyboard.press('Tab');
  assert.equal(await notice(page).getByRole('button',{name:'Continue',exact:true}).evaluate(el=>el===document.activeElement),true);
  await page.keyboard.press('Escape');
  assert.equal(await page.getByRole('button',{name:'Microsoft services & privacy',exact:true}).evaluate(el=>el===document.activeElement),true);
  assert.equal(await page.locator('.about-modal[open]').count(),1);
  await page.keyboard.press('Escape'); assert.equal(await page.locator('dialog[open]').count(),0);
  assert.equal(await page.getByRole('button',{name:'About Violilt',exact:true}).evaluate(el=>el===document.activeElement),true);
  assert.equal(await page.evaluate(()=>window.noticeFixture.playCalls),0);
  await observe(page,'keyboard-focus',focus);
});

test('two fixed links use fake opener with failure, false result and successful retry', async t => {
  const page = await fixture(t);
  await notice(page).waitFor();
  const url = page.url();
  await notice(page).locator('a').first().click();
  await notice(page).locator('a').nth(1).focus(); await page.keyboard.press('Enter');
  await page.evaluate(()=>window.noticeFixture.failLink=true);
  await notice(page).locator('a').first().click();
  await notice(page).getByRole('alert').waitFor(); assert.match(await notice(page).getByRole('alert').innerText(),/Synthetic browser failure/);
  await page.evaluate(()=>{window.noticeFixture.failLink=false;window.noticeFixture.falseLink=true;});
  await notice(page).locator('a').first().click();
  await page.waitForFunction(()=>document.querySelector('.notice-error')?.textContent.includes('browser could not be opened'));
  await page.evaluate(()=>window.noticeFixture.falseLink=false);
  await notice(page).locator('a').first().click();
  await page.waitForFunction(()=>!document.querySelector('.notice-error'));
  const opened=await page.evaluate(()=>window.noticeFixture.opened);
  assert.deepEqual(opened,['privacy-statement','smartscreen','privacy-statement','privacy-statement','privacy-statement']);
  assert.equal(page.url(),url); assert.equal(page.context().pages().length,1);
  await observe(page,'fixed-links',{url,opened});
});

test('notice remains usable during startup failure and service retry', async t => {
  const page=await fixture(t,{failState:true});
  await notice(page).waitFor();
  await notice(page).locator('a').first().click();
  await notice(page).getByRole('alert').waitFor();
  assert.match(await notice(page).getByRole('alert').innerText(),/desktop service is not connected/);
  await page.keyboard.press('Escape');
  if (await page.locator('dialog[aria-labelledby="about-title"][open]').count()) await page.keyboard.press('Escape');
  await page.evaluate(()=>window.noticeFixture.failState=false);
  await page.getByRole('button',{name:'Retry connection',exact:true}).click();
  await page.waitForFunction(()=>window.noticeFixture.closeMessages.some(m=>m.type==='violilt:close-ready'));
  await reopen(page); await notice(page).locator('a').first().click();
  await page.waitForFunction(()=>window.noticeFixture.opened.length===1);
  assert.equal(await notice(page).getByRole('alert').count(),0);
});

test('native close takes precedence over startup notice and Escape keeps editing', async t => {
  const page=await fixture(t);
  await notice(page).waitFor();
  await page.waitForFunction(()=>window.noticeFixture.closeMessages.some(m=>m.type==='violilt:close-ready'));
  await page.evaluate(()=>window.dispatchEvent(new CustomEvent('violilt:close-request',{detail:{id:'initialClose'}})));
  await page.getByRole('dialog',{name:'Save before closing',exact:true}).waitFor();
  assert.equal(await page.locator('.microsoft-notice').evaluate(el=>el.open),false);
  await page.waitForFunction(()=>window.noticeFixture.closeMessages.some(m=>m.id==='initialClose'&&m.saved===true));
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('dialog[open]').count(),0);
  await reopen(page); assert.equal(await notice(page).evaluate(el=>el.open),true);
});

test('notice during dirty edits does not save; close drains held write before approval', async t => {
  const page=await fixture(t); await edit(page);
  await page.getByRole('textbox',{name:'Markdown editor',exact:true}).fill('Latest unsaved fixture text.');
  await reopen(page);
  assert.deepEqual(await page.evaluate(()=>window.noticeFixture.saves),[],'Paused autosave isolates notice attribution');
  await page.evaluate(()=>{window.noticeFixture.holdSave=true;window.dispatchEvent(new CustomEvent('violilt:close-request',{detail:{id:'dirtyClose'}}));});
  await page.waitForFunction(()=>window.noticeFixture.saves.length===1);
  assert.equal(await page.locator('.microsoft-notice').evaluate(el=>el.open),false);
  assert.equal(await page.evaluate(()=>window.noticeFixture.closeMessages.some(m=>m.id==='dirtyClose'&&m.saved)),false);
  await page.evaluate(()=>window.noticeFixture.releaseSave());
  await page.waitForFunction(()=>window.noticeFixture.closeMessages.some(m=>m.id==='dirtyClose'&&m.saved===true));
  assert.equal(await page.evaluate(()=>window.noticeFixture.document.markdown),'Latest unsaved fixture text.');
  assert.deepEqual(await page.evaluate(()=>window.noticeFixture.saves),['Latest unsaved fixture text.']);
});

test('notice close interaction preserves failed save, Escape cancellation and explicit retry', async t => {
  const page=await fixture(t); await edit(page);
  await page.getByRole('textbox',{name:'Markdown editor',exact:true}).fill('Retained failed-save fixture text.');
  await reopen(page);
  await page.evaluate(()=>{window.noticeFixture.failSave=true;window.dispatchEvent(new CustomEvent('violilt:close-request',{detail:{id:'failedClose'}}));});
  await page.getByRole('dialog',{name:'Save before closing',exact:true}).getByRole('alert').waitFor();
  assert.equal(await page.evaluate(()=>window.noticeFixture.closeMessages.some(m=>m.saved===true)),false);
  await page.keyboard.press('Escape');
  assert.equal(await page.getByRole('textbox',{name:'Markdown editor',exact:true}).inputValue(),'Retained failed-save fixture text.');
  await page.evaluate(()=>{window.noticeFixture.failSave=false;window.dispatchEvent(new CustomEvent('violilt:close-request',{detail:{id:'retryClose'}}));});
  await page.waitForFunction(()=>window.noticeFixture.closeMessages.some(m=>m.id==='retryClose'&&m.saved===true));
  assert.deepEqual(await page.evaluate(()=>window.noticeFixture.saves),['Retained failed-save fixture text.','Retained failed-save fixture text.']);
});

test('notice remains within a small viewport with scrollable copy and visible Continue', async t => {
  const page=await fixture(t,{existing:true,viewport:{width:640,height:480}});
  await notice(page).waitFor();
  const box=await notice(page).boundingBox(); assert(box && box.x>=0 && box.y>=0 && box.x+box.width<=640 && box.y+box.height<=480);
  await notice(page).getByRole('button',{name:'Continue',exact:true}).scrollIntoViewIfNeeded();
  await observe(page,'small-viewport',{box,scroll:await notice(page).evaluate(el=>({height:el.clientHeight,total:el.scrollHeight}))});
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('.microsoft-notice[open]').count(),0);
  await page.keyboard.press('Escape'); assert.equal(await page.locator('dialog[open]').count(),0);
});
