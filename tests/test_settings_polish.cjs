/** Settings presentation/interaction checks. Exact local built assets and disposable APIs only.
 * SETTINGS_ASSETS / SETTINGS_EVIDENCE_DIR select preserved inputs and fresh output.
 * SETTINGS_CAPTURE_ONLY=1 records the same visual matrix against the entry candidate.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const {test, before, after} = require('node:test');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assets = path.resolve(process.env.SETTINGS_ASSETS || path.join(__dirname, '../frontend/dist'));
const evidence = process.env.SETTINGS_EVIDENCE_DIR;
const captureOnly = process.env.SETTINGS_CAPTURE_ONLY === '1';
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
  const context = await browser.newContext({viewport:options.viewport || {width:1440,height:1000},
    colorScheme:'light', reducedMotion:options.reducedMotion || 'no-preference'});
  const page = await context.newPage(); page.setDefaultTimeout(6000);
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
  t.after(async () => { await context.close(); assert.deepEqual(errors, []); assert.deepEqual(external, []); });
  await page.addInitScript(options => {
    const doc = {id:'reading',title:'Synthetic reading',markdown:'# A quiet page\n\nWords for listening.',created:1};
    const defaults = {palette:options.palette || 'violilt',theme:options.theme || 'light',voice:'af_heart',speed:1,include_code:false,
      heading_pause:.6,paragraph_pause:.3,performance_mode:'balanced',cpu_threads:0,processing_device:'cpu',gpu_device:-1,
      buffer_mode:'balanced',auto_listen:false,warm_start:false,model_release:'idle',cache_enabled:true,cache_limit_mb:256};
    const settings = {...defaults, ...JSON.parse(sessionStorage.getItem('settings-fixture') || '{}')};
    const configuration = {provider:'CPUExecutionProvider',label:'CPU',threads:4,device_id:-1};
    const c = window.settingsFixture = {settings,writes:[],calls:[],reads:0,fail:'',pending:'',settle:null,
      model:{state:'ready',percent:100,message:'Ready.',voices:['af_heart'],download_bytes:120575669},
      performance:{configuration,logical_processors:8,physical_cores:4,adapters:[{id:0,name:'Synthetic NVIDIA adapter',memory_mb:4096}],
        gpu_ready:true,gpu_message:'Optional GPU runtime and model ready.',cpu_percent:0,gpu_percent:null,
        memory:{state:'idle',message:''},warmup:{state:'ready',message:'Voices are ready.'},
        benchmark:{state:'idle',completed:0,total:0,message:'',results:[]},recommendation:null},
      cache:{count:3,bytes:1572864,limit_mb:256,available:true}};
    async function action(name) {
      c.calls.push(name);
      if (c.fail === name) throw new Error(`Synthetic ${name} failure`);
      if (c.pending === name) await new Promise(resolve => c.settle = resolve);
      if (name === 'warm') { c.performance.warmup={state:'ready',message:'Voices are ready.'}; c.performance.memory={state:'idle',message:''}; }
      if (name === 'release') { c.performance.warmup={state:'idle',message:'Voice memory released. It reloads for your next reading.'}; c.performance.memory={state:'unloaded',message:''}; }
      if (name === 'clear') { c.cache.count=0; c.cache.bytes=0; }
      if (name === 'test') c.performance.benchmark={state:'running',completed:1,total:4,message:'Measuring CPU · 2 threads',results:[]};
      if (name === 'stop') c.performance.benchmark={state:'cancelled',completed:1,total:4,message:'Speed test stopped.',results:[]};
      return true;
    }
    HTMLMediaElement.prototype.play = function () { throw new Error('Audio is outside this fixture'); };
    HTMLMediaElement.prototype.pause = function () {};
    window.chrome ||= {}; window.chrome.webview = {postMessage:() => {}};
    window.pywebview = {api:{
      get_state:async () => { c.reads++; return {documents:[doc],jobs:[],active:c.active || null,settings,model:structuredClone(c.model),welcome_version:1,
        storage:'C:\\Disposable fixture\\Library with a deliberately long storage folder name\\Violilt',
        performance:structuredClone(c.performance),cache:structuredClone(c.cache)}; },
      get_document:async () => structuredClone(doc),save_document:async (_id,text) => ({...doc,markdown:text}),
      save_settings:async value => { c.writes.push(value); Object.assign(settings,value); sessionStorage.setItem('settings-fixture',JSON.stringify(settings)); return settings; },
      prepare_document:async text => ({title:doc.title,text,words:8,chunks:[],omissions:{code_blocks:0,metadata:0}}),
      warm_engine:() => action('warm'),release_engine:() => action('release'),clear_cache:() => action('clear'),
      start_benchmark:() => action('test'),stop_benchmark:() => action('stop'),
      import_model:async () => null,save_position:async () => true,
      generate:async () => { throw new Error('Inference is outside this fixture'); },
    }};
  }, options);
  await page.goto(origin); await page.locator('.home-page').waitFor();
  await openSettings(page);
  return page;
}
async function openSettings(page) {
  if (!await page.getByRole('button',{name:'Settings',exact:true}).isVisible()) await page.getByRole('button',{name:'Toggle shelf',exact:true}).click();
  await page.getByRole('button',{name:'Settings',exact:true}).click(); await page.locator('.settings-page').waitFor();
}
async function observe(page, name) { if (evidence) await page.screenshot({path:path.join(evidence,name+'.png'),animations:'disabled'}); }
async function record(name, data) { if (evidence) fs.writeFileSync(path.join(evidence,name+'.json'),JSON.stringify(data,null,2)); }
async function poll(page) {
  const reads=await page.evaluate(()=>window.settingsFixture.reads);
  await page.waitForFunction(previous=>window.settingsFixture.reads>previous,reads);
}

test('visual matrix: both palettes, desktop and narrow/short Settings and unchanged reading controls', async t => {
  const observations = [];
  for (const palette of ['violilt','classic']) for (const theme of ['light','dark']) for (const narrow of [false,true]) {
    const key = `${palette}-${theme}-${narrow?'small':'desktop'}`;
    const page = await fixture(t,{palette,theme,viewport:narrow?{width:640,height:480}:{width:1440,height:1000}});
    await observe(page,key+'-top');
    await page.getByRole('combobox',{name:'Release voice model',exact:true}).scrollIntoViewIfNeeded();
    await observe(page,key+'-memory');
    await page.locator('.cache-controls').evaluate(el=>el.scrollIntoView({block:'center'}));
    await observe(page,key+'-cache');
    await page.locator('.theme-choices').evaluate(el=>el.scrollIntoView({block:'center'}));
    await observe(page,key+'-appearance');
    await page.locator('.settings-page').evaluate(el=>el.scrollTop=el.scrollHeight);
    await observe(page,key+'-end');
    const layout = await page.locator('.settings-page').evaluate(el=>({horizontal:el.scrollWidth>el.clientWidth+1,
      endVisible:el.scrollHeight-el.scrollTop-el.clientHeight<=1,headings:[...el.querySelectorAll('h2,h3')].map(h=>h.textContent),
      clippedControls:[...el.querySelectorAll('button,select,input')].filter(control=>{
        const rect=control.getBoundingClientRect(),main=el.getBoundingClientRect(); return rect.left<main.left || rect.right>main.right+1;
      }).map(control=>control.textContent || control.getAttribute('aria-label'))}));
    const footer = await page.locator('.player-bar').evaluate(el=>({bottom:el.getBoundingClientRect().bottom,height:el.getBoundingClientRect().height,viewport:innerHeight}));
    if (!captureOnly) { assert(!layout.horizontal,key); assert.deepEqual(layout.clippedControls,[],key); assert(layout.endVisible); assert(footer.bottom<=footer.viewport+1); }
    if (!narrow) {
      await page.locator('.document-list button').click(); await page.locator('.reading-article').waitFor();
      await observe(page,key+'-reading');
      layout.reading = await page.locator('.reading-options .toggle-row').evaluate(el=>({label:getComputedStyle(el).fontSize,
        helper:getComputedStyle(el.querySelector('small')).fontSize,track:getComputedStyle(el.querySelector('.toggle-track')).width,
        focus:getComputedStyle(el.querySelector('input')).outlineStyle}));
    }
    observations.push({key,layout,footer});
  }
  await record('visual-matrix',observations);
});

test('all Settings controls retain writes, device choices and saved values on reopen', {skip:captureOnly}, async t => {
  const page=await fixture(t);
  await page.locator('.performance-presets > button').nth(3).click();
  for (const [name,value] of [['CPU threads','3'],['Processing device','gpu'],['Graphics card','0'],['Listening buffer','smooth'],['Release voice model','keep'],['Cache limit','512']])
    await page.getByRole('combobox',{name,exact:true}).selectOption(value);
  for (const text of ['Listen as audio arrives','Prepare voices when Violilt opens','Reuse unchanged passages'])
    await page.locator('.toggle-row').filter({hasText:text}).locator('input').press('Space');
  await page.locator('.palette-choices > button').nth(1).click(); await page.locator('.theme-choices > button').nth(1).click();
  const saved=await page.evaluate(()=>window.settingsFixture.settings);
  assert.deepEqual({mode:saved.performance_mode,threads:saved.cpu_threads,device:saved.processing_device,gpu:saved.gpu_device,
    buffer:saved.buffer_mode,release:saved.model_release,limit:saved.cache_limit_mb,listen:saved.auto_listen,warm:saved.warm_start,
    cache:saved.cache_enabled,palette:saved.palette,theme:saved.theme},
    {mode:'custom',threads:3,device:'gpu',gpu:0,buffer:'smooth',release:'keep',limit:512,listen:true,warm:true,cache:false,palette:'classic',theme:'dark'});
  assert.equal(await page.evaluate(()=>window.settingsFixture.writes.length),12);
  await page.reload(); await page.locator('.home-page').waitFor(); await openSettings(page);
  assert.equal(await page.getByRole('combobox',{name:'Graphics card',exact:true}).inputValue(),'0');
  assert.equal(await page.getByRole('combobox',{name:'CPU threads',exact:true}).inputValue(),'3');
  assert(await page.locator('.theme-choices > button').nth(1).getAttribute('aria-pressed')==='true');
  await page.locator('.theme-choices > button').nth(2).click();
  await page.emulateMedia({colorScheme:'dark'}); await page.waitForFunction(()=>document.querySelector('.app-shell').classList.contains('dark'));
  await page.emulateMedia({colorScheme:'light'}); await page.waitForFunction(()=>!document.querySelector('.app-shell').classList.contains('dark'));
  await page.getByRole('combobox',{name:'Processing device',exact:true}).selectOption('cpu');
  await page.locator('.document-list button').click(); await page.locator('.reading-article').waitFor();
  assert.equal(await page.locator('.compact-presets > button[aria-pressed="true"]').innerText(),'Custom');
  await record('saved-controls',{saved});
});

test('truthful preparation, release, benchmark and cache outcomes preserve actions and focus', {skip:captureOnly}, async t => {
  const page=await fixture(t);
  const prepare=page.getByRole('button',{name:'Prepare voice now',exact:true});
  const release=()=>page.getByRole('button',{name:/^(Release memory now|Releasing…)$/});
  await page.evaluate(()=>{ const c=window.settingsFixture; c.pending='warm'; c.performance.warmup={state:'loading',message:'Preparing CPU voices…'}; c.performance.memory={state:'busy',message:''}; });
  await poll(page);
  assert(await page.getByRole('button',{name:'Preparing…',exact:true}).isDisabled()); assert(await release().isDisabled());
  assert.match(await page.locator('.memory-status').innerText(),/Preparing CPU voices/); await observe(page,'state-preparing');
  await page.evaluate(()=>{const c=window.settingsFixture; c.performance.warmup={state:'failed',message:'Synthetic preparation failure'}; c.performance.memory={state:'unloaded',message:''};});
  await poll(page); assert.match(await page.locator('.memory-status').innerText(),/preparation failure/);
  await prepare.click(); await page.waitForFunction(()=>window.settingsFixture.settle!==null);
  assert(!await page.locator('.toast').count());
  await page.evaluate(()=>{const c=window.settingsFixture;c.pending='';c.settle();c.settle=null;}); await poll(page);
  assert.match(await page.locator('.memory-status').innerText(),/idle/);
  assert.equal(await page.getByText('Voices are ready.',{exact:true}).count(),0,'Stale warmup success must not duplicate memory status');
  await page.evaluate(()=>{window.settingsFixture.fail='release';});
  await release().click(); assert.match(await page.locator('.error-banner').innerText(),/release failure/);
  assert.equal(await page.locator('.toast').count(),0);
  await page.evaluate(()=>{window.settingsFixture.performance.memory={state:'releasing',message:'The voice process has not stopped yet. Try releasing memory again.'};});
  await poll(page); assert.match(await page.locator('.memory-status').innerText(),/has not stopped yet/);
  assert(await release().isDisabled()); await observe(page,'state-release-error');
  await page.evaluate(()=>{const c=window.settingsFixture;c.fail='';c.performance.memory={state:'idle',message:''};}); await poll(page);
  await page.evaluate(()=>{const c=window.settingsFixture;c.pending='release';});
  await release().focus(); await page.keyboard.press('Enter'); await page.waitForFunction(()=>window.settingsFixture.settle!==null);
  await page.evaluate(()=>{window.settingsFixture.performance.memory={state:'releasing',message:''};}); await poll(page);
  assert(await release().isDisabled()); assert.equal(await page.locator('.toast').count(),0); await observe(page,'state-releasing');
  // Native disabled buttons cease to be focus targets. A reader can continue
  // through enabled controls; completion must not steal that subsequent focus.
  await page.getByRole('combobox',{name:'Release voice model',exact:true}).focus(); await page.keyboard.press('Tab');
  const focusAnchor=page.locator('.reusable-card input');
  assert(await focusAnchor.evaluate(el=>el===document.activeElement));
  await page.evaluate(()=>{const c=window.settingsFixture;c.pending='';c.settle();c.settle=null;}); await poll(page);
  assert.match(await page.locator('.memory-status').innerText(),/released/);
  assert.match(await page.locator('.toast').innerText(),/Voice memory released/);
  assert(await focusAnchor.evaluate(el=>el===document.activeElement),'Completion must not move subsequent focus');
  await page.locator('.toast').waitFor({state:'hidden'});
  await page.evaluate(()=>{window.settingsFixture.fail='clear';});
  await page.getByRole('button',{name:'Clear reusable audio',exact:true}).click();
  assert.match(await page.locator('.error-banner').innerText(),/clear failure/); assert.equal(await page.locator('.toast').count(),0);
  await page.evaluate(()=>{window.settingsFixture.fail='';});
  await page.getByRole('button',{name:'Clear reusable audio',exact:true}).click();
  assert(await page.getByRole('button',{name:'Clear reusable audio',exact:true}).isDisabled());
  assert.match(await page.locator('.toast').innerText(),/recordings are kept/);
  await page.evaluate(()=>{window.settingsFixture.cache={available:false,count:0,bytes:0,limit_mb:256,message:'Synthetic cache unavailable. Recordings are kept.'};}); await poll(page);
  assert(await page.getByRole('status').filter({hasText:'Synthetic cache unavailable'}).isVisible()); await observe(page,'state-cache-unavailable');
  await page.getByRole('button',{name:'Run speed test',exact:true}).click();
  assert(await page.getByRole('button',{name:'Stop test',exact:true}).isEnabled());
  assert.match(await page.locator('.speed-test').innerText(),/Measuring CPU/); assert(await prepare.isDisabled());
  await observe(page,'state-benchmark'); await page.getByRole('button',{name:'Stop test',exact:true}).click();
  assert(await page.getByText('Speed test stopped.',{exact:true}).isVisible());
  await page.evaluate(()=>{window.settingsFixture.performance.benchmark={state:'failed',completed:1,total:4,message:'Synthetic speed test failure',results:[{label:'CPU · 2 threads',error:'Unavailable'}]};}); await poll(page);
  assert(await page.getByText('Synthetic speed test failure',{exact:true}).isVisible()); await observe(page,'state-benchmark-error');
  await page.evaluate(()=>{window.settingsFixture.active={id:'active',title:'Synthetic generation',state:'generating',completed:0,total:2,engine:{label:'CPU',threads:4}};window.settingsFixture.performance.memory={state:'busy',message:'Voice process in use'};}); await poll(page);
  assert(await prepare.isDisabled()); assert(await release().isDisabled()); assert(await page.getByRole('button',{name:'Run speed test',exact:true}).isDisabled());
  assert(await page.getByText('Changes apply to your next reading or continuation.',{exact:true}).isVisible()); await observe(page,'state-busy');
  await record('actions',await page.evaluate(()=>window.settingsFixture.calls));
});

test('scaled text, reduced motion and real keyboard traversal keep Settings actions reachable', {skip:captureOnly}, async t => {
  for (const palette of ['violilt','classic']) for (const theme of ['light','dark']) {
    const page=await fixture(t,{palette,theme,viewport:{width:640,height:480},reducedMotion:'reduce'});
    // Browser text-only scaling proxy; native Windows display scaling is a separate check.
    await page.evaluate(()=>{
      const text=[...document.querySelectorAll('.settings-page :is(p,small,label,button,select,code,span,strong,h1,h2,h3)')];
      const sizes=text.map(el=>parseFloat(getComputedStyle(el).fontSize)*2);
      text.forEach((el,index)=>el.style.setProperty('font-size',sizes[index]+'px','important'));
    });
    await page.locator('.settings-page .existing-files').focus();
    const visited=[];
    for (let step=0;step<60;step++) {
      await page.keyboard.press('Tab');
      const focus=await page.evaluate(()=>{const el=document.activeElement,style=getComputedStyle(el),rect=el.getBoundingClientRect();
        const indicator=el.matches('.toggle-row input')?getComputedStyle(el.nextElementSibling):style;
        return {name:el.getAttribute('aria-label') || el.textContent,settings:!!el.closest('.settings-page'),keyboard:el.matches(':focus-visible'),
          outline:indicator.outlineStyle,width:parseFloat(indicator.outlineWidth),left:rect.left,right:rect.right,top:rect.top,bottom:rect.bottom,
          transition:style.transitionDuration,animation:style.animationName};});
      if (!focus.settings) break;
      visited.push(focus); assert(focus.keyboard); assert.notEqual(focus.outline,'none'); assert(focus.width>=2);
      assert(focus.left>=0 && focus.right<=640); assert(focus.top>=0 && focus.bottom<=480);
      assert.equal(focus.transition,'0s'); assert.equal(focus.animation,'none');
    }
    assert(visited.some(f=>f.name==='Microsoft services & privacy'),'Tab must reach final help action');
    assert(!(await page.locator('.settings-page').evaluate(el=>el.scrollWidth>el.clientWidth+1)));
    await observe(page,`scaled-focus-${palette}-${theme}`); await record(`focus-${palette}-${theme}`,visited);
  }
});
