/** Built welcome/setup UX; fake desktop/model APIs, no downloads or inference. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const {test, before, after} = require('node:test');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assets = path.resolve(process.env.WELCOME_ASSETS || path.join(__dirname, '../frontend/dist'));
const evidence = process.env.WELCOME_EVIDENCE_DIR;
let browser, server, origin;
before(async () => {
  assert(fs.existsSync(path.join(assets, 'index.html')));
  if (evidence) fs.mkdirSync(evidence, {recursive:true});
  server = http.createServer((_req, res) => res.writeHead(404).end());
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  origin = `http://127.0.0.1:${server.address().port}`;
  browser = await chromium.launch({headless:true, executablePath:process.env.BROWSER_EXECUTABLE || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
});
after(async () => { await browser?.close(); if (server) await new Promise(resolve => server.close(resolve)); });
async function fixture(t, options = {}) {
  const context = await browser.newContext({viewport:options.viewport || {width:1280,height:960}});
  const page = await context.newPage(); page.setDefaultTimeout(7000);
  const errors = [], external = [];
  page.on('pageerror', e => errors.push(e.message));
  await context.route('**/*', route => {
    const url = new URL(route.request().url());
    if (url.origin !== origin) { external.push(url.href); return route.abort(); }
    if (url.pathname.startsWith('/media/')) return route.fulfill({status:204,body:''});
    const file = path.resolve(assets, '.' + (url.pathname === '/' ? '/index.html' : url.pathname));
    if (!file.startsWith(assets + path.sep)) return route.fulfill({status:403,body:''});
    try { return route.fulfill({status:200,contentType:({'.html':'text/html','.js':'text/javascript','.css':'text/css','.png':'image/png'})[path.extname(file)] || 'application/octet-stream',body:fs.readFileSync(file)}); }
    catch { return route.fulfill({status:404,body:''}); }
  });
  t.after(async () => { await context.close(); assert.deepEqual(errors, []); assert.deepEqual(external, [], 'No model download or external navigation is allowed'); });
  await page.addInitScript(options => {
    const doc = {id:'first',title:'Your first reading',markdown:'# Your first reading\n\nWords for listening.',created:1};
    const settings = {palette:options.palette || 'violilt',theme:options.theme || 'light',voice:'af_heart',speed:1,include_code:false,
      heading_pause:.6,paragraph_pause:.3,performance_mode:'balanced',cpu_threads:0,processing_device:'cpu',gpu_device:-1,
      buffer_mode:'balanced',auto_listen:false,warm_start:false,model_release:'idle',cache_enabled:true,cache_limit_mb:256};
    const c = window.welcomeFixture = {settings,model:{state:options.modelReady?'ready':'missing',percent:options.modelReady?100:0,
      message:options.modelReady?'Ready.':'Download voices to begin.',voices:options.modelReady?['af_heart']:[],download_bytes:120575669},
      setupCalls:0,importCalls:0,completionCalls:0,preferenceWrites:[],generationCalls:0,opened:[],failComplete:false,failDownload:false,
      importedReady:false,playCalls:0,documentImports:0};
    HTMLMediaElement.prototype.play = function () { c.playCalls++; return Promise.resolve(); };
    HTMLMediaElement.prototype.pause = function () {};
    window.chrome ||= {}; window.chrome.webview = {postMessage:() => {}};
    window.pywebview = {api:{
      get_state:async () => ({documents:[doc],jobs:[],active:null,settings,model:structuredClone(c.model),
        welcome_version:Number(sessionStorage.getItem('fixture-welcome') || options.seen || 0),storage:'Fixture library',
        performance:null,cache:{count:0,bytes:0,limit_mb:256}}),
      get_document:async () => structuredClone(doc),save_document:async (_id,text) => ({...doc,markdown:text}),
      save_settings:async value => { c.preferenceWrites.push(value); Object.assign(settings,value); return settings; },
      prepare_document:async text => ({title:doc.title,text,words:5,chunks:[],omissions:{code_blocks:0,metadata:0}}),
      complete_welcome:async () => { c.completionCalls++; if(c.failComplete) throw new Error('Fixture storage unavailable.'); sessionStorage.setItem('fixture-welcome','1'); return true; },
      setup_model:async () => { c.setupCalls++; if(c.failDownload) { c.model={...c.model,state:'error',message:'Fixture connection failed.'}; } else c.model={...c.model,state:'downloading',percent:23,message:'Downloading voices · 28 / 120 MB'}; return structuredClone(c.model); },
      import_model:async () => { c.importCalls++; if(!c.importedReady) return null; c.model={...c.model,state:'ready',percent:100,voices:['af_heart']}; return structuredClone(c.model); },
      import_document:async () => { c.documentImports++; return null; }, save_position:async () => true,
      generate:async () => { c.generationCalls++; throw new Error('Generation is outside this fixture'); },
      open_microsoft_privacy:async ref => { c.opened.push(ref); return true; },
    }};
  }, options);
  await page.goto(origin); await page.waitForFunction(() => document.querySelector('.app-shell'));
  await page.waitForFunction(() => document.querySelector('.loading-screen') === null);
  return page;
}
const welcome = page => page.getByRole('dialog',{name:'Welcome to Violilt.',exact:true});
async function observe(page, name) { if(evidence) await page.screenshot({path:path.join(evidence,name+'.png')}); }

test('welcome leads with the app, explains one-click model setup and remembers exploration', async t => {
  const page=await fixture(t); await welcome(page).waitFor();
  assert.equal(await page.locator('.microsoft-notice[open]').count(),0);
  assert(await welcome(page).getByRole('heading',{name:'Welcome to Violilt.'}).isVisible());
  assert(await welcome(page).getByRole('button',{name:'Download voices · 121 MB',exact:true}).isEnabled());
  const copy=await welcome(page).innerText();
  assert.match(copy,/No separate installer or account is needed/); assert.match(copy,/Microsoft Defender SmartScreen/);
  assert.match(copy,/Microsoft receives required diagnostic data from WebView2 and safety-check information/); assert.match(copy,/required diagnostic data/);
  assert.equal(await welcome(page).locator('details').evaluate(el=>el.open),false);
  await page.keyboard.press('Control+o'); await page.keyboard.press('Control+s');
  assert.deepEqual(await page.evaluate(()=>[window.welcomeFixture.setupCalls,window.welcomeFixture.documentImports,window.welcomeFixture.preferenceWrites.length]),[0,0,0]);
  await observe(page,'welcome-desktop');
  await welcome(page).getByRole('button',{name:'Explore for now',exact:true}).click();
  assert.equal(await page.locator('.welcome-dialog[open]').count(),0);
  assert.equal(await page.evaluate(()=>window.welcomeFixture.completionCalls),1);
  assert(await page.locator('.home-voice-setup').getByRole('button',{name:'Download voices · 121 MB',exact:true}).isVisible());
  await page.reload(); await page.waitForFunction(()=>document.querySelector('.loading-screen')===null);
  assert.equal(await page.locator('dialog[open]').count(),0);
  assert.equal(await page.evaluate(()=>window.welcomeFixture.setupCalls),0);
});

test('Escape dismisses welcome once without downloading or starting speech', async t => {
  const page=await fixture(t); await welcome(page).waitFor();
  await observe(page,'welcome-desktop-current');
  await page.keyboard.press('Escape');
  await page.waitForFunction(()=>!document.querySelector('.welcome-dialog[open]'));
  assert.deepEqual(await page.evaluate(()=>[window.welcomeFixture.completionCalls,window.welcomeFixture.setupCalls,window.welcomeFixture.generationCalls]),[1,0,0]);
  assert.equal(await page.getByRole('button',{name:'Violilt home',exact:true}).evaluate(el=>el===document.activeElement),true);
  await page.reload(); await page.waitForFunction(()=>document.querySelector('.loading-screen')===null);
  assert.equal(await page.locator('dialog[open]').count(),0);
});

test('explicit download shows progress, reaches ready and never starts speech automatically', async t => {
  const page=await fixture(t); await welcome(page).getByRole('button',{name:'Download voices · 121 MB',exact:true}).click();
  await welcome(page).getByRole('progressbar',{name:'Voice download'}).waitFor();
  assert.equal(await welcome(page).getByRole('progressbar').getAttribute('aria-valuenow'),'23');
  assert(await welcome(page).getByRole('button',{name:'Downloading voices…',exact:true}).isDisabled());
  assert.equal(await page.evaluate(()=>window.welcomeFixture.setupCalls),1);
  await page.evaluate(()=>{window.welcomeFixture.model={...window.welcomeFixture.model,state:'ready',percent:100,voices:['af_heart']};});
  await welcome(page).getByRole('button',{name:'Start reading',exact:true}).waitFor();
  await welcome(page).getByRole('button',{name:'Start reading',exact:true}).click();
  await page.locator('.reading-article').waitFor();
  assert.equal(await page.evaluate(()=>window.welcomeFixture.generationCalls),0);
});

test('failed model download has a visible retry and existing-file cancellation remains harmless', async t => {
  const page=await fixture(t);
  await welcome(page).getByRole('button',{name:'Use existing files',exact:true}).click();
  assert.equal(await page.evaluate(()=>window.welcomeFixture.importCalls),1);
  assert(await welcome(page).getByRole('button',{name:'Download voices · 121 MB',exact:true}).isEnabled());
  await page.evaluate(()=>window.welcomeFixture.failDownload=true);
  await welcome(page).getByRole('button',{name:'Download voices · 121 MB',exact:true}).click();
  await welcome(page).getByRole('alert').filter({hasText:'Fixture connection failed.'}).waitFor();
  await page.evaluate(()=>window.welcomeFixture.failDownload=false);
  await welcome(page).getByRole('button',{name:'Retry download',exact:true}).click();
  await welcome(page).getByRole('progressbar').waitFor();
  assert.equal(await page.evaluate(()=>window.welcomeFixture.setupCalls),2);
});

test('already available voices skip downloading and existing files can still be imported', async t => {
  const page=await fixture(t,{modelReady:true});
  assert.equal(await welcome(page).getByRole('button',{name:/Download voices/}).count(),0);
  await welcome(page).getByRole('button',{name:'Use existing files',exact:true}).click();
  assert.equal(await page.evaluate(()=>window.welcomeFixture.importCalls),1);
  await welcome(page).getByRole('button',{name:'Start reading',exact:true}).click();
  await page.locator('.reading-article').waitFor();
  assert.equal(await page.evaluate(()=>window.welcomeFixture.setupCalls),0);
});

test('unwritable welcome preference offers an honest session-only continuation', async t => {
  const page=await fixture(t); await page.evaluate(()=>window.welcomeFixture.failComplete=true);
  await welcome(page).getByRole('button',{name:'Explore for now',exact:true}).click();
  await welcome(page).getByRole('alert').filter({hasText:'Fixture storage unavailable.'}).waitFor();
  await welcome(page).getByRole('button',{name:'Continue for this session',exact:true}).click();
  assert.equal(await page.locator('.welcome-dialog[open]').count(),0);
  await page.reload(); await welcome(page).waitFor();
  assert.deepEqual(await page.evaluate(()=>window.welcomeFixture.preferenceWrites),[]);
});

test('guide and privacy can be reopened from Settings with no repeat completion write', async t => {
  const page=await fixture(t,{seen:1,modelReady:true});
  assert.equal(await page.locator('dialog[open]').count(),0);
  await page.getByRole('button',{name:'Settings',exact:true}).click();
  await page.getByRole('button',{name:'Welcome & quick guide',exact:true}).click();
  await welcome(page).locator('summary').click();
  assert.equal(await welcome(page).locator('details').evaluate(el=>el.open),true);
  await welcome(page).getByRole('link',{name:'Microsoft Privacy Statement',exact:true}).click();
  assert.deepEqual(await page.evaluate(()=>window.welcomeFixture.opened),['privacy-statement']);
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('dialog[open]').count(),0);
  assert.equal(await page.evaluate(()=>window.welcomeFixture.completionCalls),0);
  assert.equal(await page.getByRole('button',{name:'Welcome & quick guide',exact:true}).evaluate(el=>el===document.activeElement),true);
  assert(await page.getByRole('heading',{name:'Getting started & privacy',exact:true}).isVisible());
  await page.getByRole('button',{name:'Microsoft services & privacy',exact:true}).click();
  await page.getByRole('dialog',{name:'Microsoft services & privacy',exact:true}).waitFor();
});

for(const [palette,theme] of [['violilt','light'],['classic','dark']]) test(`small-window welcome remains usable with ${palette}/${theme}`,async t=>{
  const page=await fixture(t,{palette,theme,viewport:{width:640,height:480}});
  const dialog=welcome(page); await dialog.waitFor();
  await dialog.getByRole('button',{name:'Download voices · 121 MB',exact:true}).scrollIntoViewIfNeeded();
  const bounds=await dialog.evaluate(el=>({width:el.getBoundingClientRect().width,height:el.getBoundingClientRect().height,scroll:el.scrollHeight,client:el.clientHeight,horizontal:el.scrollWidth>el.clientWidth+1}));
  assert(bounds.width<=608 && bounds.height<=448); assert(!bounds.horizontal);
  await dialog.locator('summary').focus(); await page.keyboard.press('Space');
  assert.equal(await dialog.locator('details').evaluate(el=>el.open),true);
  await observe(page,`welcome-small-${palette}-${theme}`);
  await dialog.getByRole('button',{name:'Explore for now',exact:true}).click();
  assert.equal(await page.locator('.welcome-dialog[open]').count(),0);
});
