/** Reading-room candidate checks: exact built assets, disposable APIs/media, no workers.
 * READING_ASSETS / READING_EVIDENCE_DIR select inputs/output. READING_CAPTURE_ONLY=1
 * records the identical visual fixture against preserved entry assets.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const {test, before, after} = require('node:test');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assets = path.resolve(process.env.READING_ASSETS || path.join(__dirname, '../frontend/dist'));
const evidence = process.env.READING_EVIDENCE_DIR;
const captureOnly = process.env.READING_CAPTURE_ONLY === '1';
let browser, server, origin;
before(async () => {
  assert(fs.existsSync(path.join(assets, 'index.html')));
  if (evidence) fs.mkdirSync(evidence, {recursive:true});
  server = http.createServer((_req,res) => res.writeHead(404).end());
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  origin = `http://127.0.0.1:${server.address().port}`;
  browser = await chromium.launch({headless:true, executablePath:process.env.BROWSER_EXECUTABLE ||
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
});
after(async () => { await browser?.close(); if (server) await new Promise(resolve => server.close(resolve)); });

async function fixture(t, options = {}) {
  const context = await browser.newContext({viewport:options.viewport || {width:1440,height:960},
    reducedMotion:options.reducedMotion || 'no-preference',colorScheme:'light'});
  const page = await context.newPage(); page.setDefaultTimeout(6000);
  const errors=[],foreign=[];
  page.on('pageerror',error => errors.push(error.message));
  await context.route('**/*',route => {
    const url = new URL(route.request().url());
    if (url.origin !== origin) { foreign.push(url.href); return route.abort(); }
    if (url.pathname.startsWith('/media/')) return route.fulfill({status:204,body:''});
    const file = path.resolve(assets,'.'+(url.pathname === '/'?'/index.html':url.pathname));
    if (!file.startsWith(assets+path.sep)) return route.fulfill({status:403,body:''});
    try { return route.fulfill({status:200,body:fs.readFileSync(file),contentType:
      ({'.html':'text/html','.js':'text/javascript','.css':'text/css','.png':'image/png'})[path.extname(file)] || 'application/octet-stream'}); }
    catch { return route.fulfill({status:404,body:''}); }
  });
  t.after(async () => { await context.close(); assert.deepEqual(errors,[]); assert.deepEqual(foreign,[]); });
  await page.addInitScript(options => {
    const doc={id:'reading',title:'The art of paying attention',created:1,
      markdown:options.empty?'':'# The art of paying attention\n\nA quiet moment can change the way we read. There is no need to hurry through a good page.\n\n## Make room for the words\n\nChoose a voice, settle into a comfortable pace, and let the words find their rhythm.\n\n> Take your time. The next chapter can wait.\n\nA few lines of code can stay on the page, or join the narration.\n\n```js\nconst pace = "unhurried";\n```'};
    const settings={palette:options.palette || 'violilt',theme:options.theme || 'light',voice:'af_heart',speed:1,
      include_code:false,heading_pause:.6,paragraph_pause:.3,performance_mode:'balanced',cpu_threads:0,
      processing_device:'cpu',gpu_device:-1,buffer_mode:'balanced',auto_listen:false,warm_start:false,
      model_release:'idle',cache_enabled:true,cache_limit_mb:256};
    const configuration={provider:'CPUExecutionProvider',label:'CPU',threads:4,device_id:-1};
    const c=window.readingFixture={doc,settings,writes:[],generated:[],samples:[],cancels:0,playCalls:0,reads:0,
      holdGenerate:false,releaseGenerate:null,active:null,jobs:[],
      model:{state:options.missing?'missing':'ready',percent:options.missing?0:100,message:'Disposable fixture',voices:['af_heart','bf_emma','bm_george','af_bella','af_sarah','am_michael','am_adam']}};
    const job={id:'recording',document_id:doc.id,title:doc.title,voice:'af_heart',speed:1,words:70,preview:false,
      state:'completed',completed:4,total:4,duration:42,position:0,message:'',created:1};
    if (options.recording) c.jobs=[job];
    c.makeActive=(state,extra={}) => c.active={...job,id:'active',state,completed:state==='preparing'?0:2,
      total:4,available_duration:state==='preparing'?0:18,engine:configuration,
      message:state==='preparing'?'Loading the voice for this reading.':'Working on the next section.',...extra};
    HTMLMediaElement.prototype.play=function(){c.playCalls++;return Promise.resolve();};
    HTMLMediaElement.prototype.pause=function(){};
    window.chrome ||= {}; window.chrome.webview={postMessage:()=>{}};
    window.pywebview={api:{
      get_state:async()=>{c.reads++;return {documents:[structuredClone(doc)],jobs:structuredClone(c.jobs),
        active:structuredClone(c.active),settings,welcome_version:1,model:structuredClone(c.model),storage:'Disposable fixture',
        cache:{count:0,bytes:0,limit_mb:256},performance:{configuration,cpu_percent:12,gpu_percent:null,
          logical_processors:8,physical_cores:4,adapters:[],gpu_ready:false,gpu_message:'',
          memory:{state:c.active?'busy':'idle',message:''},warmup:{state:'idle',message:''},
          benchmark:{state:'idle',completed:0,total:0,message:'',results:[]},recommendation:null}};},
      get_document:async()=>structuredClone(doc),save_document:async(_id,text)=>{doc.markdown=text;return structuredClone(doc);},
      prepare_document:async text=>({title:doc.title,text,words:text?70:0,chunks:text?[{text,pause:.3,block:0}]:[],
        omissions:{code_blocks:settings.include_code?0:1,metadata:0}}),
      save_settings:async value=>{c.writes.push(value);Object.assign(settings,value);return settings;},
      generate:async(id,markdown,value)=>{c.generated.push({id,markdown,value});
        if(c.holdGenerate)await new Promise(resolve=>c.releaseGenerate=resolve);
        throw new Error('Synthetic generation failure. Retry your reading.');},
      preview_voice:async(voice,speed)=>{c.samples.push({voice,speed});return true;},
      cancel_generation:async()=>{c.cancels++;c.active.state='cancelling';c.active.message='Stopping after the current section.';return true;},
      save_position:async()=>true,
    }};
  },options);
  await page.goto(origin); await page.locator('.home-page').waitFor();
  if ((options.viewport?.width || 1440)<=1090) await page.getByRole('button',{name:'Toggle shelf',exact:true}).click();
  await page.locator('.document-list button').filter({hasText:'The art of paying attention'}).click();
  await page.locator('.reading-article').waitFor({state:'attached'});
  return page;
}
async function capture(page,name) { if(evidence) await page.screenshot({path:path.join(evidence,name+'.png'),animations:'disabled'}); }
function record(name,value) { if(evidence)fs.writeFileSync(path.join(evidence,name+'.json'),JSON.stringify(value,null,2)); }
async function layout(page) {
  return page.evaluate(()=>{
    const geometry=selector=>{const el=document.querySelector(selector),r=el.getBoundingClientRect();
      return {x:r.x,y:r.y,width:r.width,height:r.height,scrollWidth:el.scrollWidth,clientWidth:el.clientWidth,
        scrollHeight:el.scrollHeight,clientHeight:el.clientHeight};};
    return {studio:geometry('.studio-layout'),panel:geometry('.voice-panel'),controls:geometry('.voice-controls'),
      player:geometry('.player-bar'),footer:geometry('.reading-footer'),
      tabs:[...document.querySelectorAll('.document-tabs button')].map(el=>({text:el.textContent,pressed:el.getAttribute('aria-pressed')}))};
  });
}
test('visual matrix: palettes, light/dark, desktop, supported minimum and narrow/short',async t=>{
  const observations=[];
  for(const palette of ['violilt','classic'])for(const theme of ['light','dark'])
    for(const [name,viewport]of [['desktop',{width:1440,height:960}],['minimum',{width:1024,height:720}],['small',{width:640,height:480}]]){
      const key=`${palette}-${theme}-${name}`,page=await fixture(t,{palette,theme,viewport});
      await capture(page,key+'-top');
      await page.locator('.compact-presets').scrollIntoViewIfNeeded();
      await capture(page,key+'-options');
      const observed=await layout(page); observations.push({key,...observed});
      if(!captureOnly){
        for(const area of ['studio','controls'])assert(observed[area].scrollWidth<=observed[area].clientWidth+1,key+' '+area);
        await page.locator('.generate-button').scrollIntoViewIfNeeded();
        const button=await page.locator('.generate-button').boundingBox();
        assert(button.x>=0 && button.x+button.width<=viewport.width+1,key);
        assert(button.y>=0 && button.y+button.height<=viewport.height+1,key);
        assert(observed.player.y+observed.player.height<=viewport.height+1,key);
        await capture(page,key+'-action');
      }
  }
  record('visual-matrix',observations);
});

test('controls save once without speech; sample and narration remain separate actions',{skip:captureOnly},async t=>{
  const page=await fixture(t);
  await page.locator('.voice-selector').click();await page.locator('.voice-menu button').nth(1).click();
  const speed=page.getByRole('slider',{name:'Narration speed',exact:true});await speed.focus();await speed.press('ArrowRight');await speed.press('Tab');
  await page.locator('.reading-options input').press('Space');
  await page.getByRole('combobox',{name:'Paragraph pause',exact:true}).selectOption('0.6');
  await page.locator('.compact-presets button').nth(0).press('Enter');
  await page.waitForFunction(()=>window.readingFixture.writes.length===5);
  assert.deepEqual(await page.evaluate(()=>({voice:window.readingFixture.settings.voice,speed:window.readingFixture.settings.speed,
    code:window.readingFixture.settings.include_code,pause:window.readingFixture.settings.paragraph_pause,mode:window.readingFixture.settings.performance_mode,
    generated:window.readingFixture.generated,samples:window.readingFixture.samples,plays:window.readingFixture.playCalls})),
    {voice:'bf_emma',speed:1.1,code:true,pause:.6,mode:'quiet',generated:[],samples:[],plays:0});
  await page.getByRole('button',{name:/Listen to a sample/}).press('Enter');
  await page.waitForFunction(()=>window.readingFixture.samples.length===1);
  assert.deepEqual(await page.evaluate(()=>window.readingFixture.samples),[{voice:'bf_emma',speed:1.1}]);
  assert.deepEqual(await page.evaluate(()=>window.readingFixture.generated),[]);
  await page.evaluate(()=>window.readingFixture.holdGenerate=true);
  await page.getByRole('button',{name:'Create your audio',exact:true}).press('Enter');
  await page.waitForFunction(()=>typeof window.readingFixture.releaseGenerate==='function');
  const preparing=page.getByRole('button',{name:'Preparing your reading…',exact:true});
  assert(await preparing.isDisabled());assert(await page.getByRole('button',{name:/Listen to a sample/}).isDisabled());
  await preparing.evaluate(el=>el.click());
  assert.equal(await page.evaluate(()=>window.readingFixture.generated.length),1);
  await capture(page,'state-starting');
  await page.evaluate(()=>window.readingFixture.releaseGenerate());
  await page.getByRole('alert').filter({hasText:'Synthetic generation failure'}).waitFor();
  assert(await page.getByRole('button',{name:'Create your audio',exact:true}).isEnabled());
  await capture(page,'state-error');
});

test('real state fields distinguish preparation, generation, saving, cancellation and warnings',{skip:captureOnly},async t=>{
  const page=await fixture(t,{viewport:{width:1024,height:720}});
  for(const [state,label]of [['preparing','Preparing your reading…'],['generating','Generating audio…'],['assembling','Saving recording…']]){
    await page.evaluate(state=>window.readingFixture.makeActive(state),state);
    await page.locator('.generation-progress').filter({hasText:label}).waitFor();
    assert(await page.getByRole('button',{name:'Stop generation',exact:true}).isEnabled());
    assert(await page.getByRole('button',{name:/Listen to a sample/}).isDisabled());
    if(state==='preparing')assert.equal(await page.locator('.ready-audio').count(),0);
    else {
      assert.match(await page.locator('.ready-audio').innerText(),/0:18 of audio ready/);
      assert.match(await page.locator('.ready-audio').innerText(),/Completed sections are available/);
    }
    await capture(page,'state-'+state);
  }
  await page.evaluate(()=>window.readingFixture.makeActive('generating',{unread_count:3,
    pronunciation_warnings:['Some words use fallback pronunciation. Review the saved warnings.'],throughput:2.3,first_audio_seconds:1.2,cache_hits:1}));
  await page.getByText('Some words use fallback pronunciation. Review the saved warnings.',{exact:true}).waitFor();
  assert.match(await page.locator('.generation-progress').innerText(),/3 symbols omitted/);
  const details=page.locator('.hardware-usage');await details.locator('summary').press('Space');
  assert(await details.evaluate(el=>el.open));assert.equal(await page.evaluate(()=>window.readingFixture.playCalls),0);
  await capture(page,'state-warning-details');
  await page.getByRole('button',{name:'Stop generation',exact:true}).press('Enter');
  await page.locator('.generation-progress').filter({hasText:'Stopping generation…'}).waitFor();
  assert(await page.getByRole('button',{name:'Stopping after this section…',exact:true}).isDisabled());
  assert.equal(await page.evaluate(()=>window.readingFixture.cancels),1);
  await page.locator('.generation-area').evaluate(el=>el.scrollTop=el.scrollHeight);
  await capture(page,'state-cancelling');
  await page.evaluate(()=>window.readingFixture.makeActive('generating',{preview:true}));
  await page.getByRole('button',{name:'Listen to a sample Generating…',exact:true}).waitFor();
  assert(await page.getByRole('button',{name:'Listen to a sample Generating…',exact:true}).isDisabled());
  await page.evaluate(()=>{window.readingFixture.active=null;});
  await page.getByRole('button',{name:'Create your audio',exact:true}).waitFor();
  assert.equal(await page.locator('.generation-progress').count(),0);
});

test('empty reading is disabled and missing model retains setup route',{skip:captureOnly},async t=>{
  const empty=await fixture(t,{empty:true});assert(await empty.getByRole('button',{name:'Create your audio',exact:true}).isDisabled());
  await capture(empty,'state-empty');
  const missing=await fixture(t,{missing:true});
  await capture(missing,'state-missing');
  await missing.getByRole('button',{name:'Set up & start listening',exact:true}).press('Enter');
  await missing.locator('.settings-page').waitFor();
  assert.deepEqual(await missing.evaluate(()=>window.readingFixture.generated),[]);
  await capture(missing,'missing-model-settings');
});

test('Settings shortcut and unchanged player remain usable from the reading room',{skip:captureOnly},async t=>{
  const page=await fixture(t,{recording:true});
  await page.locator('.play-button').waitFor({state:'visible'});assert(await page.locator('.play-button').isEnabled());
  await page.locator('.play-button').press('Space');assert.equal(await page.evaluate(()=>window.readingFixture.playCalls),1);
  await page.getByRole('button',{name:'Processing settings',exact:true}).click();
  await page.locator('.settings-page').waitFor();
  await page.locator('.performance-presets button').nth(3).press('Enter');
  await page.waitForFunction(()=>window.readingFixture.writes.length===1);
  await page.getByRole('button',{name:'Reading room',exact:true}).click();
  assert.equal(await page.locator('.compact-presets button').nth(3).getAttribute('aria-pressed'),'true');
  await page.locator('.play-button').press('Space');assert.equal(await page.evaluate(()=>window.readingFixture.playCalls),2);
  await capture(page,'settings-return-player');
  await page.evaluate(()=>window.readingFixture.makeActive('generating',{id:'recording'}));
  await page.locator('.ready-audio').filter({hasText:'Listen using the player below.'}).waitFor();
});

test('long voice popup remains keyboard reachable at minimum and narrow/short sizes',{skip:captureOnly},async t=>{
  for(const viewport of [{width:1024,height:720},{width:640,height:480}]){
    const page=await fixture(t,{viewport});await page.locator('.voice-selector').click();
    const last=page.locator('.voice-menu button').last();
    for(let step=0;step<7;step++)await page.keyboard.press('Tab');
    assert(await last.evaluate(el=>el===document.activeElement));
    const box=await last.boundingBox();assert(box.x>=0 && box.x+box.width<=viewport.width);
    assert(box.y>=0 && box.y+box.height<=viewport.height);
    await capture(page,`voice-popup-${viewport.width}`);
    await page.keyboard.press('Escape');await page.locator('.voice-menu').waitFor({state:'hidden'});
    assert(await page.locator('.voice-selector').evaluate(el=>el===document.activeElement));
    await page.locator('.voice-selector').press('Enter');
    for(let step=0;step<7;step++)await page.keyboard.press('Tab');
    await page.keyboard.press('Enter');await page.waitForFunction(()=>window.readingFixture.settings.voice==='am_adam');
    assert(await page.locator('.voice-selector').evaluate(el=>el===document.activeElement));
    assert.equal(await page.evaluate(()=>window.readingFixture.writes.length),1);
    assert.deepEqual(await page.evaluate(()=>({samples:window.readingFixture.samples,generated:window.readingFixture.generated,plays:window.readingFixture.playCalls})),
      {samples:[],generated:[],plays:0});
  }
});

test('enlarged text and reduced motion keep studio controls reachable by real Tab',{skip:captureOnly},async t=>{
  for(const palette of ['violilt','classic'])for(const theme of ['light','dark']){
    const page=await fixture(t,{palette,theme,viewport:{width:1024,height:720},reducedMotion:'reduce'});
    await page.evaluate(()=>{
      const nodes=[...document.querySelectorAll('.studio-layout :is(p,small,label,button,select,span,strong,h1,h2,h3)')];
      const sizes=nodes.map(el=>parseFloat(getComputedStyle(el).fontSize)*2);
      nodes.forEach((el,i)=>el.style.setProperty('font-size',sizes[i]+'px','important'));
    });
    await page.locator('.voice-selector').focus();const visited=[];
    for(let step=0;step<20;step++){
      await page.keyboard.press('Tab');
      const focus=await page.evaluate(()=>{
        const el=document.activeElement,r=el.getBoundingClientRect(),style=getComputedStyle(el);
        const indicator=el.matches('.toggle-row input')?getComputedStyle(el.nextElementSibling):style;
        return {name:el.getAttribute('aria-label') || el.textContent,panel:!!el.closest('.voice-panel'),
          keyboard:el.matches(':focus-visible'),outline:indicator.outlineStyle,width:parseFloat(indicator.outlineWidth),
          left:r.left,right:r.right,top:r.top,bottom:r.bottom,transition:style.transitionDuration,animation:style.animationName};
      });
      if(!focus.panel)break;visited.push(focus);
      assert(focus.keyboard);assert.notEqual(focus.outline,'none');assert(focus.width>=2);
      assert(focus.left>=0 && focus.right<=1025);assert(focus.top>=0 && focus.bottom<=721);
      assert.equal(focus.transition,'0s');assert.equal(focus.animation,'none');
    }
    assert(visited.some(f=>f.name.includes('Create your audio')),'Tab reaches the primary action');
    assert.equal(await page.evaluate(()=>window.readingFixture.generated.length),0);
    const observed=await layout(page);assert(observed.controls.scrollWidth<=observed.controls.clientWidth+1);
    await capture(page,`scaled-${palette}-${theme}`);record(`scaled-${palette}-${theme}`,{visited,layout:observed});
  }
});
