const {chromium}=require(process.env.FOLIO_PLAYWRIGHT);const assert=require('assert'),fs=require('fs');
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(fn,limit=60000){const deadline=Date.now()+limit;while(Date.now()<deadline){const value=await fn();if(value)return value;await delay(200);}throw Error('Timed out');}
(async()=>{
  const browser=await until(async()=>{try{return await chromium.connectOverCDP('http://127.0.0.1:9223');}catch{return null;}});
  const page=await until(()=>browser.contexts()[0].pages().find(p=>p.url().startsWith('http://127.0.0.1')));
  await page.waitForSelector('.generate-button',{timeout:60000});
  const state=()=>page.evaluate(()=>window.pywebview.api.get_state());
  assert(!(await state()).performance.gpu_ready);
  await page.getByRole('button',{name:'Listen to a sample'}).click();
  const job=await until(async()=>{const s=await state();const j=s.jobs.find(j=>j.preview);if(j?.state==='failed')throw Error(j.message);return j?.state==='completed'?j:null;});
  assert(job.engine.provider==='CPUExecutionProvider');assert(job.duration>1);
  fs.writeFileSync('artifacts/cpu-only.json',JSON.stringify({success:true,gpuDisabled:true,job},null,2));
  console.log(JSON.stringify({success:true,gpuDisabled:true,cpuThreads:job.engine.threads,audioSeconds:job.duration}));
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
