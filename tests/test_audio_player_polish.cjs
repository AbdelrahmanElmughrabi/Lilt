/** Built UI only: synthetic API, HTML media, AudioContext and clock; no speech. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const {test, before, after} = require('node:test');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assets = path.resolve(process.env.PLAYER_ASSETS || 'frontend/dist');
const evidence = process.env.PLAYER_EVIDENCE_DIR;
const captureOnly = process.env.PLAYER_CAPTURE_ONLY === '1';
let browser, server, origin;
before(async () => {
  assert(fs.existsSync(path.join(assets, 'index.html')));
  if (evidence) fs.mkdirSync(evidence, {recursive:true});
  server = http.createServer((_req,res) => res.writeHead(404).end());
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  origin = `http://127.0.0.1:${server.address().port}`;
  try { browser = await chromium.launch({headless:true, executablePath:process.env.BROWSER_EXECUTABLE || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'}); }
  catch (error) { await new Promise(resolve=>server.close(resolve)); server=null; throw error; }
});
after(async()=>{if(browser) await browser.close(); if(server) await new Promise(resolve=>server.close(resolve));});
async function fixture(t, options={}) {
  const context = await browser.newContext({viewport:{width:1440,height:960},...options.context});
  const page=await context.newPage(); page.setDefaultTimeout(6000);
  const errors=[],foreign=[];
  page.on('pageerror',error=>errors.push(error.message));
  await context.route('**/*',route=>{
    const url=new URL(route.request().url());
    if(url.origin!==origin){foreign.push(url.href);return route.abort();}
    if(url.pathname.startsWith('/media/')) return route.fulfill({status:200,body:Buffer.from([1,2,3,4]),contentType:'audio/wav'});
    const file=path.resolve(assets,'.'+(url.pathname==='/'?'/index.html':url.pathname));
    if(!file.startsWith(assets+path.sep)) return route.fulfill({status:403,body:''});
    try {return route.fulfill({status:200,body:fs.readFileSync(file),contentType:({'.html':'text/html','.js':'text/javascript','.css':'text/css','.png':'image/png'})[path.extname(file)]||'application/octet-stream'});}
    catch{return route.fulfill({status:404,body:''});}
  });
  t.after(async()=>{await context.close();assert.deepEqual(errors,[]);assert.deepEqual(foreign,[]);});
  await page.addInitScript(options=>{
    const settings={palette:options.palette||'violilt',theme:options.theme||'light',voice:'af_heart',speed:1,include_code:false,heading_pause:.6,paragraph_pause:.3,performance_mode:'balanced',cpu_threads:0,processing_device:'cpu',gpu_device:-1,buffer_mode:'balanced',auto_listen:false,warm_start:false,model_release:'idle',cache_enabled:true,cache_limit_mb:256};
    const document={id:'reading',title:'A quiet chapter',markdown:'# A quiet chapter\n\nA small synthetic reading, with room to listen.',created:1};
    const job={id:'recording',document_id:'reading',title:options.long?'A very long chapter title — '+ 'the quiet art of listening to every word '.repeat(6):'The quiet art of listening',voice:'af_heart',speed:1,words:40,preview:false,state:options.mode==='stream'?'generating':'completed',completed:1,total:8,duration:options.long?10842:120,available_duration:12,position:options.long?4205:20,message:'',created:1,unread_count:2};
    if(options.mode==='stream'){job.duration=0;job.position=0;}
    const c=window.playerFixture={settings,document,job,jobs:options.mode==='empty'||options.mode==='preview'?[]:[job],reads:0,saves:[],exports:[],plays:0,pauses:0,rates:[],volumes:[],starts:[],stops:0,time:0,failPlay:false,gain:null,stream:{id:job.id,state:'generating',sections:[{index:0,start:0,duration:12,pause:0}],available:12,total:8,running:true,complete:false,throughput:2}};
    const media=new WeakMap(); const data=el=>{if(!media.has(el))media.set(el,{paused:true,time:0,rate:1,volume:.8});return media.get(el);};
    Object.defineProperties(HTMLMediaElement.prototype,{
      paused:{get(){return data(this).paused;}},currentTime:{get(){return data(this).time;},set(v){data(this).time=v;}},
      duration:{get(){return c.job.duration;}},readyState:{get(){return 0;}},
      playbackRate:{get(){return data(this).rate;},set(v){data(this).rate=v;c.rates.push(v);}},
      volume:{get(){return data(this).volume;},set(v){data(this).volume=v;c.volumes.push(v);}},
    });
    HTMLMediaElement.prototype.load=function(){};
    HTMLMediaElement.prototype.play=function(){c.plays++;if(c.failPlay)return Promise.reject(new Error('Synthetic playback failure'));data(this).paused=false;this.dispatchEvent(new Event('play'));return Promise.resolve();};
    HTMLMediaElement.prototype.pause=function(){c.pauses++;if(!data(this).paused){data(this).paused=true;this.dispatchEvent(new Event('pause'));}};
    // Prevent the native decoder from consuming deliberately synthetic media bytes.
    HTMLMediaElement.prototype.addEventListener = new Proxy(HTMLMediaElement.prototype.addEventListener,{apply(target,self,args){if(args[0]==='error')return;return Reflect.apply(target,self,args);}});
    window.AudioContext=class {
      constructor(){this.state='running';this.destination={};}
      get currentTime(){return c.time;}
      resume(){this.state='running';return Promise.resolve();}
      createGain(){c.gain={value:.8};return {gain:c.gain,connect(){},disconnect(){}};}
      createBufferSource(){return {playbackRate:{value:1},connect(){},disconnect(){},start(at,offset){c.starts.push({at,offset});},stop(){c.stops++;},onended:null};}
      decodeAudioData(){return Promise.resolve({duration:12});}
    };
    window.chrome||={};window.chrome.webview={postMessage(){}};
    window.pywebview={api:{
      get_state:async()=>{c.reads++;return structuredClone({documents:[document],jobs:c.jobs,active:c.job.state==='generating'?c.job:null,settings,welcome_version:1,model:{state:'ready',percent:100,message:'Fixture only',voices:['af_heart','bf_emma']},storage:'Synthetic fixture',cache:{count:0,bytes:0,limit_mb:256},performance:null});},
      get_document:async()=>structuredClone(document),prepare_document:async text=>({title:document.title,text,words:40,chunks:[{text,pause:.3,block:0}],omissions:{code_blocks:0,metadata:0}}),
      save_document:async(_id,text)=>({...document,markdown:text}),save_settings:async value=>Object.assign(settings,value),
      save_position:async(id,position)=>{c.saves.push({id,position});return true;},get_stream:async()=>structuredClone(c.stream),
      export_recording:async id=>{c.exports.push(id);return 'Synthetic export';},
      preview_voice:async()=>{c.job={...job,id:'preview',preview:true,title:'Heart voice sample',state:'completed',position:0,duration:8,available_duration:8,unread_count:0};c.jobs=[c.job];return c.job;},
      generate:async()=>{throw Error('Real generation is forbidden in this fixture');},
    }};
  },options);
  await page.clock.install({time:new Date('2030-01-01T00:00:00Z')});
  await page.clock.pauseAt(new Date('2030-01-01T00:00:01Z'));
  await page.goto(origin);await page.locator('.home-page').waitFor();
  if(options.mode!=='empty'&&options.mode!=='preview') {
    await page.waitForFunction(()=>!document.querySelector('.play-button').disabled);
    if(options.mode!=='stream') await page.locator('audio').evaluate(el=>el.dispatchEvent(new Event('loadedmetadata')));
  }
  return page;
}
async function poll(page){const reads=await page.evaluate(()=>window.playerFixture.reads);await page.clock.runFor(1000);await page.waitForFunction(n=>window.playerFixture.reads>n,reads);}
async function surface(page,name){
  if(name==='home'){if(!await page.locator('.brand').isVisible())await page.getByRole('button',{name:'Toggle shelf',exact:true}).click();await page.locator('.brand').click();await page.locator('.home-page').waitFor();}
  if(name==='settings'){if(await page.locator('.sidebar-settings').isVisible())await page.locator('.sidebar-settings').click();else{await page.getByRole('button',{name:'Toggle shelf',exact:true}).click();await page.locator('.sidebar-settings').click();}await page.locator('.settings-page').waitFor();}
  if(name==='reading'){if(!await page.locator('.document-list button').first().isVisible())await page.getByRole('button',{name:'Toggle shelf',exact:true}).click();await page.locator('.document-list button').first().click();await page.locator('.reading-article').waitFor();}
  await page.clock.runFor(200);
}
async function record(page,name){
  const layout=await page.locator('.player-bar').evaluate(el=>{
    const r=el.getBoundingClientRect();const meta=el.querySelector('.track-details').getBoundingClientRect();const toast=document.querySelector('.toast')?.getBoundingClientRect();return {height:r.height,top:r.top,bottom:r.bottom,viewport:innerHeight,horizontal:document.documentElement.scrollWidth>innerWidth,metadataVisible:meta.width>0&&meta.height>0,toastAbove:!toast||toast.bottom<=r.top,
      controls:[...el.querySelectorAll('button,input')].map(x=>{const b=x.getBoundingClientRect();const s=getComputedStyle(x);return {label:x.getAttribute('aria-label')||x.title,width:b.width,height:b.height,visible:s.display!=='none'&&b.width>0&&b.height>0,inFooter:b.top>=r.top&&b.bottom<=r.bottom+1&&b.left>=r.left&&b.right<=r.right+1};})};
  });
  if(evidence){fs.writeFileSync(path.join(evidence,name+'.json'),JSON.stringify(layout,null,2));await page.screenshot({path:path.join(evidence,name+'.png'),animations:'disabled'});}
  return layout;
}
test('visual matrix keeps player controls reachable across surfaces palettes and sizes',async t=>{
  for(const palette of ['violilt','classic'])for(const theme of ['light','dark']){
    const page=await fixture(t,{palette,theme,long:true});
    for(const [label,width,height] of [['desktop',1440,960],['minimum',1024,720],['narrow',700,620],['short',1024,520],['compact',480,640]]){
      await page.setViewportSize({width,height});
      for(const name of ['home','reading','settings']){
        await surface(page,name);const key=`${palette}-${theme}-${label}-${name}`;const result=await record(page,key);
        if(!captureOnly){assert(!result.horizontal,key);assert(result.bottom<=height+1,key);assert(result.metadataVisible,key);assert(result.toastAbove,key);assert(result.controls.every(c=>c.visible&&c.inFooter),key);assert.equal(await page.locator('.track-details strong').getAttribute('title'),await page.evaluate(()=>window.playerFixture.job.title));}
      }
    }
  }
});
test('saved audio activates once and retains seek clamps rate volume export and position calls',{skip:captureOnly},async t=>{
  const page=await fixture(t);const play=page.locator('.play-button'),seek=page.getByRole('slider',{name:'Seek audio',exact:true});
  await play.focus();await page.keyboard.press('Space');assert.equal(await page.evaluate(()=>window.playerFixture.plays),1);assert.equal(await play.getAttribute('aria-label'),'Pause');
  await page.keyboard.press('Enter');assert.equal(await page.evaluate(()=>window.playerFixture.pauses),2); // one initial selection pause, one activation
  await page.locator('audio').evaluate(el=>{el.currentTime=6;el.dispatchEvent(new Event('timeupdate'));});
  let count=await page.evaluate(()=>window.playerFixture.saves.length);await page.getByRole('button',{name:'Back 10 seconds',exact:true}).click();
  assert.deepEqual(await page.evaluate(()=>window.playerFixture.saves.slice(-1)),[{id:'recording',position:0}]);assert.equal(await page.evaluate(()=>window.playerFixture.saves.length),count+1);
  await page.locator('audio').evaluate(el=>{el.currentTime=117;el.dispatchEvent(new Event('timeupdate'));});
  count=await page.evaluate(()=>window.playerFixture.saves.length);await page.getByRole('button',{name:'Forward 10 seconds',exact:true}).click();assert.equal(await seek.inputValue(),'120');assert.equal(await page.evaluate(()=>window.playerFixture.saves.length),count+1);
  await seek.focus();await page.keyboard.press('Home');await page.keyboard.press('ArrowRight');assert.equal(await seek.inputValue(),'0.1');assert.match(await seek.getAttribute('aria-valuetext'),/total/);
  const rates=[];for(let i=0;i<6;i++){await page.locator('.playback-rate').click();rates.push(await page.locator('.playback-rate').innerText());}
  assert.deepEqual(await page.evaluate(()=>window.playerFixture.rates.slice(-6)),[1.25,1.5,1.75,2,.75,1]);
  const volume=page.getByRole('slider',{name:'Volume',exact:true});await volume.focus();await page.keyboard.press('Home');await page.keyboard.press('ArrowRight');assert.equal(await volume.inputValue(),'0.05');assert.equal(await page.evaluate(()=>window.playerFixture.volumes.at(-1)),.05);assert.equal(await volume.getAttribute('aria-valuetext'),'5 percent');
  await page.getByRole('button',{name:'Export recording',exact:true}).click();assert.deepEqual(await page.evaluate(()=>window.playerFixture.exports),['recording']);
  await page.locator('audio').evaluate(el=>{el.currentTime=37;el.dispatchEvent(new Event('timeupdate'));});assert.equal(await page.evaluate(()=>window.playerFixture.saves.at(-1).position),37);
  await page.locator('audio').evaluate(el=>el.dispatchEvent(new Event('ended')));assert.equal(await play.getAttribute('aria-label'),'Play');await record(page,'saved-ended');
});
test('stream availability buffering pause resume and completion use actual existing states',{skip:captureOnly},async t=>{
  const page=await fixture(t,{mode:'stream'});const play=page.locator('.play-button');
  assert.match(await page.locator('.player-duration').innerText(),/Available/);assert(await page.locator('.export-button').isDisabled());
  await play.click();await page.clock.runFor(100);assert.equal(await play.getAttribute('aria-label'),'Pause');await record(page,'stream-playing');
  // Exhaust decoded audio while the producer is still running.
  await page.evaluate(()=>window.playerFixture.time=12.1);await page.clock.runFor(100);assert.match(await page.locator('.player-track').innerText(),/Buffering/);assert.equal(await play.getAttribute('aria-label'),'Pause');await record(page,'stream-buffering');
  const saves=await page.evaluate(()=>window.playerFixture.saves.length);
  await play.click();assert.equal(await play.getAttribute('aria-label'),'Play');assert.equal(await page.evaluate(()=>window.playerFixture.saves.length),saves+1);assert.doesNotMatch(await page.locator('.player-track').innerText(),/Buffering/);await record(page,'stream-paused');
  await play.click();assert.equal(await play.getAttribute('aria-label'),'Pause');
  await page.evaluate(()=>{const c=window.playerFixture;c.stream.sections.push({index:1,start:12,duration:12,pause:0});c.stream.available=24;c.job.available_duration=24;});await poll(page);await page.clock.runFor(100);assert.doesNotMatch(await page.locator('.player-track').innerText(),/Buffering/);assert.match(await page.locator('.player-duration').innerText(),/0:24/);await record(page,'stream-resumed');
  // A stream seek retains both existing persistence routes: the explicit seek
  // save plus the >=5-second state callback save when that threshold is crossed.
  for(const [name,expected,writes] of [['Forward 10 seconds',22,2],['Forward 10 seconds',24,1],['Back 10 seconds',14,2]]) {
    const count=await page.evaluate(()=>window.playerFixture.saves.length);
    await page.getByRole('button',{name,exact:true}).click();
    assert.equal(await page.evaluate(()=>window.playerFixture.saves.at(-1).position),expected);
    assert.equal(await page.evaluate(()=>window.playerFixture.saves.length),count+writes);
    assert.deepEqual(await page.evaluate(n=>window.playerFixture.saves.slice(n),count),Array.from({length:writes},()=>({id:'recording',position:expected})));
  }
  await page.locator('.playback-rate').click();assert.equal(await page.locator('.playback-rate').getAttribute('aria-label'),'Playback speed, 1.25 times');
  const volume=page.getByRole('slider',{name:'Volume',exact:true});await volume.focus();await page.keyboard.press('Home');await page.keyboard.press('ArrowRight');assert.equal(await page.evaluate(()=>window.playerFixture.gain.value),.05);
  const seek=page.getByRole('slider',{name:'Seek audio',exact:true});await seek.focus();await page.keyboard.press('End');assert.equal(await seek.inputValue(),'24');assert.match(await seek.getAttribute('aria-valuetext'),/available/);assert.equal(await page.evaluate(()=>window.playerFixture.saves.at(-1).position),24);
  await page.evaluate(()=>{const c=window.playerFixture;c.job.state='completed';c.job.duration=24;c.stream.complete=true;c.stream.running=false;c.stream.state='completed';});await poll(page);assert(await page.locator('.export-button').isEnabled());assert.match(await page.locator('.player-duration').innerText(),/Total/);assert((await record(page,'stream-completed')).toastAbove);
  await page.setViewportSize({width:480,height:640});assert((await record(page,'stream-completed-compact')).toastAbove);
});
test('empty preview and playback failure stay truthful without accidental generation',{skip:captureOnly},async t=>{
  const empty=await fixture(t,{mode:'empty'});assert(await empty.locator('.play-button').isDisabled());assert(await empty.locator('.export-button').isDisabled());await record(empty,'empty');
  const page=await fixture(t,{mode:'preview'});await surface(page,'reading');await page.getByRole('button',{name:/Listen to a sample/}).click();await page.clock.runFor(200);await page.waitForFunction(()=>window.playerFixture.plays===1);assert.match(await page.locator('.player-track').innerText(),/Voice preview/);assert.match(await page.locator('.player-duration').innerText(),/0:08/);await record(page,'voice-preview');
  await page.locator('.play-button').click();await page.evaluate(()=>window.playerFixture.failPlay=true);await page.locator('.play-button').click();assert.match(await page.locator('.error-banner').innerText(),/Synthetic playback failure/);assert.equal(await page.locator('.play-button').getAttribute('aria-label'),'Play');await record(page,'playback-error');
});
test('enlarged text reduced motion and real range keyboard focus retain controls',{skip:captureOnly},async t=>{
  for(const palette of ['violilt','classic'])for(const theme of ['light','dark']){
    const page=await fixture(t,{palette,theme,long:true,context:{reducedMotion:'reduce',viewport:{width:1024,height:720}}});
    await page.evaluate(()=>{const sizes=[...document.querySelectorAll('.player-bar button,.player-bar span,.player-bar strong,.player-bar small')].map(el=>[el,parseFloat(getComputedStyle(el).fontSize)]);for(const [el,size] of sizes)el.style.fontSize=`${size*2}px`;});
    await surface(page,'settings');const layout=await record(page,`enlarged-${palette}-${theme}`);assert(layout.controls.every(c=>c.visible&&c.inFooter));
    const seek=page.getByRole('slider',{name:'Seek audio',exact:true});await page.locator('.player-buttons button').last().focus();await page.keyboard.press('Tab');assert(await seek.evaluate(el=>el===document.activeElement&&el.matches(':focus-visible')&&getComputedStyle(el).outlineStyle!=='none'));
    await page.keyboard.press('Home');await page.keyboard.press('ArrowRight');assert.equal(await seek.inputValue(),'0.1');
    const motion=await page.locator('.play-button').evaluate(el=>({transition:getComputedStyle(el).transitionDuration,animation:getComputedStyle(el).animationDuration}));assert(parseFloat(motion.transition)<=.001);assert(parseFloat(motion.animation)<=.001);
    await record(page,`enlarged-focus-${palette}-${theme}`);
  }
});
test('compact footer leaves reading generation and final Settings controls scroll reachable',{skip:captureOnly},async t=>{
  const page=await fixture(t,{long:true});
  for(const [width,height] of [[1024,720],[1024,520],[700,620],[480,640]]){
    await page.setViewportSize({width,height});await surface(page,'reading');
    const create=page.getByRole('button',{name:'Create your audio',exact:true});
    await create.focus();
    const reachable=await create.evaluate(el=>{const b=el.getBoundingClientRect();return b.top>=document.querySelector('.topbar').getBoundingClientRect().bottom&&b.bottom<=document.querySelector('.player-bar').getBoundingClientRect().top+1;});
    assert(reachable,`Reading action ${width}x${height}`);await record(page,`reading-action-${width}x${height}`);
    await surface(page,'settings');
    const last=page.locator('.settings-page button').last();await last.focus();
    assert(await last.evaluate(el=>{const b=el.getBoundingClientRect();return b.top>=0&&b.bottom<=document.querySelector('.player-bar').getBoundingClientRect().top+1;}),`Settings end ${width}x${height}`);
    await record(page,`settings-end-${width}x${height}`);
  }
});
