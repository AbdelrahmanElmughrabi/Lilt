const {chromium} = require(process.env.LILT_PLAYWRIGHT || 'playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(fn, timeout = 60000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) { const value = await fn(); if (value) return value; await delay(150); }
  throw Error('Timed out waiting for desktop state');
}
function contrast(a, b) {
  const luminance = color => {
    const channels = color.match(/[\d.]+/g).slice(0,3).map(Number).map(n => n / 255).map(n => n <= .04045 ? n/12.92 : ((n+.055)/1.055)**2.4);
    return .2126*channels[0]+.7152*channels[1]+.0722*channels[2];
  };
  const x=luminance(a), y=luminance(b); return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);
}
(async () => {
  const browser = await until(async () => { try {return await chromium.connectOverCDP('http://127.0.0.1:9223');} catch {return null;} });
  const page = await until(() => browser.contexts().flatMap(c => c.pages()).find(p => p.url().startsWith('http://127.0.0.1:')));
  const errors=[]; page.on('pageerror', error => errors.push(error.message));
  const apiState=()=>page.evaluate(()=>window.pywebview.api.get_state());
  await page.getByRole('heading',{name:'Find your rhythm.'}).waitFor({timeout:60000});
  assert.equal(await page.title(),'Lilt');
  assert.equal(await page.getByText('Interface preview',{exact:true}).count(),0);
  const initial=await apiState();
  const sample=page.getByRole('button',{name:/^The art of paying attention/}).first();
  if (await sample.count()) await sample.click();
  fs.mkdirSync('artifacts/lilt-branding',{recursive:true});
  const variants=[];
  const report={title:await page.title(),initialDocuments:initial.documents.length,initialRecordings:initial.jobs.filter(j=>!j.preview).length,storage:initial.storage,variants};
  try {
    await page.getByRole('button',{name:'Settings',exact:true}).click();
    const group=page.getByRole('group',{name:'Theme palette'});
    for (const palette of ['lilt','classic']) {
      await group.getByRole('button',{name:palette==='lilt'?/^Lilt/:/^Classic/}).click();
      for (const appearance of ['light','dark']) {
        await page.getByRole('button',{name:appearance==='light'?/^Daylight/:/^After hours/}).click();
        await until(async()=>{ const s=await apiState();return s.settings.palette===palette&&s.settings.theme===appearance; });
        await delay(220); // Wait for the existing color transition before sampling contrast.
        const styles=await page.evaluate(()=>{
          const shell=document.querySelector('.app-shell');const css=getComputedStyle(shell);
          const button=getComputedStyle(document.querySelector('.primary-button'));
          return {palette:shell.dataset.palette,dark:shell.classList.contains('dark'),background:css.getPropertyValue('--paper').trim(),accent:css.getPropertyValue('--accent').trim(),buttonColor:button.color,buttonBackground:button.backgroundColor};
        });
        assert.equal(styles.palette,palette);assert.equal(styles.dark,appearance==='dark');
        assert(contrast(styles.buttonColor,styles.buttonBackground)>=4.5,`Primary button contrast: ${palette} ${appearance}`);
        await page.getByRole('button',{name:'Reading room',exact:true}).click();
        await page.screenshot({path:`artifacts/lilt-branding/${palette}-${appearance}.png`,animations:'disabled'});
        assert(!/folio/i.test(await page.locator('body').innerText()));
        variants.push({palette,appearance,...styles,buttonContrast:contrast(styles.buttonColor,styles.buttonBackground)});
        await page.getByRole('button',{name:'Settings',exact:true}).click();
      }
    }
    await group.getByRole('button',{name:/^Lilt/}).click();
    await page.getByRole('button',{name:/^Follow your device/}).click();
    for (const colorScheme of ['dark','light']) {
      await page.emulateMedia({colorScheme});
      await until(async()=>await page.locator('.app-shell').evaluate((el,dark)=>el.classList.contains('dark')===dark,colorScheme==='dark'));
    }
    report.systemAppearance=true;
    await page.getByRole('button',{name:/^After hours/}).click();
    await until(async()=>(await apiState()).settings.theme==='dark');
    await page.reload();
    await page.getByRole('heading',{name:'Find your rhythm.'}).waitFor({timeout:15000});
    assert.equal(await page.locator('.app-shell').getAttribute('data-palette'),'lilt');
    assert(await page.locator('.app-shell').evaluate(el=>el.classList.contains('dark')));
    report.reloadPersistence=true;
    await page.getByRole('button',{name:'Settings',exact:true}).click();
    await page.getByRole('button',{name:/^Daylight/}).click();
    await page.getByRole('group',{name:'Theme palette'}).scrollIntoViewIfNeeded();
    await page.screenshot({path:'artifacts/lilt-branding/settings.png',animations:'disabled'});
    await page.getByRole('button',{name:'Reading room',exact:true}).click();
    const session=await page.context().newCDPSession(page);
    await session.send('Emulation.setDeviceMetricsOverride',{width:1024,height:681,deviceScaleFactor:1,mobile:false});
    const box=await page.getByRole('button',{name:'Create your audio',exact:false}).boundingBox();
    const metrics=await page.evaluate(()=>({width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth}));
    assert(metrics.scrollWidth<=metrics.width);assert(box&&box.y+box.height<=metrics.height-80);
    report.minimumWindow=metrics;
    await page.screenshot({path:'artifacts/lilt-branding/minimum-window.png',animations:'disabled'});
    await session.send('Emulation.clearDeviceMetricsOverride');await session.detach();
    await page.getByTitle('About Lilt').click();
    assert.equal(await page.locator('.about-brand').getAttribute('alt'),'Lilt');
    await page.screenshot({path:'artifacts/lilt-branding/about.png',animations:'disabled'});
    await page.getByTitle('Close',{exact:true}).click();
    await until(async()=>(await apiState()).performance.warmup.state!=='loading');
    await page.getByRole('button',{name:'Listen to a sample',exact:false}).click();
    const preview=await until(async()=>{
      const s=await apiState(); const job=s.jobs.find(j=>j.preview);
      if (job?.state==='failed') throw Error(job.message);
      return job?.state==='completed'?job:null;
    },90000);
    assert(preview.duration>1);
    await until(async()=>(await page.getByLabel('Seek audio').inputValue())>.2);
    await page.getByTitle('Pause',{exact:true}).click();
    const paused=Number(await page.getByLabel('Seek audio').inputValue());
    await delay(350);
    assert(Math.abs(Number(await page.getByLabel('Seek audio').inputValue())-paused)<.1);
    await page.getByTitle('Forward 10 seconds',{exact:true}).click();
    const position=Number(await page.getByLabel('Seek audio').inputValue());
    assert(position>=Math.min(paused+9.5,preview.duration-.5));
    report.speech={provider:preview.engine.provider,audioSeconds:preview.duration,position,pauseStable:true};
    await page.screenshot({path:'artifacts/lilt-branding/playback.png',animations:'disabled'});
    await page.evaluate(id=>window.pywebview.api.remove_recording(id,true),preview.id);
    assert.equal((await apiState()).documents.length,initial.documents.length);
    assert.equal((await apiState()).jobs.filter(j=>!j.preview).length,initial.jobs.filter(j=>!j.preview).length);
    report.existingLibraryRetained=true;
    assert.deepEqual(errors,[]);
    report.pageErrors=errors;report.success=true;
    fs.writeFileSync('artifacts/lilt-branding/native-check.json',JSON.stringify(report,null,2));
    console.log(JSON.stringify(report));
  } finally {
    await page.evaluate(settings=>window.pywebview.api.save_settings(settings),initial.settings);
    await page.emulateMedia({colorScheme:null});
    await browser.close();
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
