const {chromium}=require(process.env.LILT_PLAYWRIGHT);const fs=require('fs'),assert=require('assert');
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(fn,limit=90000){const deadline=Date.now()+limit;while(Date.now()<deadline){const v=await fn();if(v)return v;await delay(100);}throw Error('Timed out');}
(async()=>{
  const browser=await until(async()=>{try{return await chromium.connectOverCDP('http://127.0.0.1:9223');}catch{return null;}});const page=await until(()=>browser.contexts()[0].pages().find(p=>p.url().startsWith('http://127.0.0.1')));
  await page.reload();await page.getByRole('button',{name:'Reading room',exact:true}).first().click(); await page.waitForSelector('.generate-button');
  const state=()=>page.evaluate(()=>window.pywebview.api.get_state());
  if(process.argv[2]==='prepare'){
    await page.evaluate(async()=>{const api=window.pywebview.api;const s=await api.get_state();await api.save_settings({...s.settings,processing_device:'gpu',performance_mode:'balanced',cache_enabled:false,buffer_mode:'sooner',warm_start:true});const doc=await api.new_document();await api.save_document(doc.id,'# Across a fresh start\n\n'+Array.from({length:18},(_,i)=>`Part ${i+1}. A quiet thought is worth carrying into another day. We can stop this reading, close the application, and return to the same words without losing our place. The next sentence will be waiting when we are ready.`).join('\n\n'));});
    await page.reload();await page.getByRole('button',{name:'Reading room',exact:true}).first().click(); await page.waitForSelector('.generate-button');await page.getByRole('button',{name:/Across a fresh start/}).first().click();await page.getByRole('button',{name:'Create your audio',exact:true}).click();
    const active=await until(async()=>{const s=await state();return s.active?.completed>=2?s.active:null;});
    assert(active.completed<active.total);
    if(await page.getByTitle('Pause',{exact:true}).count())await page.getByTitle('Pause',{exact:true}).click();
    await page.getByLabel('Seek audio').fill('1');await delay(250);
    const folder='artifacts/performance-packaged/jobs/'+active.id;
    const firstMtime=fs.statSync(folder+'/section-000000.wav').mtimeMs;
    const manifest=await page.evaluate(id=>window.pywebview.api.get_stream(id),active.id);
    fs.writeFileSync('artifacts/restart-target.json',JSON.stringify({id:active.id,firstMtime,position:Number(await page.getByLabel('Seek audio').inputValue()),available:manifest.available}));
    console.log(JSON.stringify({prepared:true,id:active.id,completed:active.completed,total:active.total}));
    require('child_process').execFileSync('.venv/Scripts/python.exe',['-c',"import ctypes; window=ctypes.windll.user32.FindWindowW(None,'Lilt'); ctypes.windll.user32.PostMessageW(window,0x0010,0,0) if window else None"]);
  }else{
    const target=JSON.parse(fs.readFileSync('artifacts/restart-target.json','utf8'));const initial=await state();const job=initial.jobs.find(j=>j.id===target.id);
    assert(job.state==='interrupted',job.state);assert(job.available_duration>=target.available);
    await delay(600);assert(Math.abs(Number(await page.getByLabel('Seek audio').inputValue())-target.position)<.2);
    await until(async()=>['ready','failed'].includes((await state()).performance.warmup.state));assert((await state()).performance.warmup.state==='ready');
    await page.getByTitle('Play',{exact:true}).click();await delay(1300);await page.getByTitle('Pause',{exact:true}).click();assert(Number(await page.getByLabel('Seek audio').inputValue())>target.position+.8);
    await page.getByRole('button',{name:/Your recordings/}).click();await page.getByRole('button',{name:'Continue',exact:true}).first().click();
    const finished=await until(async()=>{const s=await state();const j=s.jobs.find(j=>j.id===target.id);assert(j.available_duration>=target.available,'Continuation unpublished existing audio');if(j.state==='failed')throw Error(j.message);return j.state==='completed'?j:null;});
    assert(fs.statSync('artifacts/performance-packaged/jobs/'+target.id+'/section-000000.wav').mtimeMs===target.firstMtime,'Restart regenerated a checkpoint');
    await page.evaluate(async()=>{const api=window.pywebview.api;const s=await api.get_state();await api.save_settings({...s.settings,warm_start:false,cache_enabled:true,processing_device:'auto',performance_mode:'balanced'});});
    await page.getByRole('button',{name:'Settings',exact:true}).click();await delay(1000);
    await page.locator('.settings-page').evaluate(el=>el.scrollTop=480);await delay(200);await page.screenshot({path:'artifacts/ui-performance-final.png'});
    fs.writeFileSync('artifacts/restart-flow.json',JSON.stringify({success:true,partialPosition:target.position,savedSections:job.completed,final:finished,startupWarmup:true,checkpointUnchanged:true},null,2));
    console.log(JSON.stringify({success:true,actualRestart:true,partialPlayback:true,startupWarmup:true,checkpointUnchanged:true}));
  }
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
